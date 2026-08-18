/* Routing Client — the window's glass.
 *
 * WINDOW, NOT WIZARD (the same contract server.py keeps): nothing here decides a
 * lane or prices a token. Every number on the screen arrived on an
 * SSE event from routing_lab.py; this file renders it and animates the yard.
 *
 * The API it consumes (routing_client/server.py):
 *   GET  /api/status  -> {unlocks:{ex1,ex2,ex3,ex5}, gateway_alive, key_present,
 *                         key_source, sdk_available, lab_error, lab_hint,
 *                         repo_root, python}
 *   GET  /api/gpu     -> {available, utilization_pct, memory_used_mb}   (gateway mode only)
 *   GET  /api/gateway_stats -> {available, stats} | 503 {available:false, error}
 *   POST /api/query   -> SSE: route_decision {lane,model,why} · receipt (+counterfactual_saved)
 *                             · answer {text} · error {message}
 *
 * No frameworks, no build step, no node_modules. Paths are RELATIVE ("api/status",
 * never "/api/status") so the client survives being served under a JupyterLab
 * proxy prefix. And the launcher's iframe is sandboxed WITHOUT allow-forms, so
 * nothing here may depend on form submission — see wire().
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------- constants

  // /api/status re-executes the learner's lab file on every poll, so this is slow
  // on purpose. It also stops entirely while the tab is hidden (see startPolling).
  var POLL_MS = 5000;

  // /api/gpu is one short-lived subprocess, so the GPU badge can be a live reading
  // instead of a stale one. Same discipline as the status poll, plus a third gate:
  // it runs only while gateway mode is on (see syncGpuPolling).
  var GPU_POLL_MS = 2000;

  // Which exercise powers which strategy. `gateway` has no probe — Ex4's blank is a
  // TOML file, so server.py's gateway_alive stands in for it; `mock_demo` needs no
  // exercise filled at all (its router is the shim's mock — it still buys its answer
  // with the key, like every other strategy).
  var UNLOCK_OF = {
    strong_only: "ex1", efficient_only: "ex1",
    manual_classifier: "ex2", switchyard_stage: "ex3"
  };
  var EXERCISE_OF = { ex1: 1, ex2: 2, ex3: 3, ex5: 5 };

  var STRATEGIES = [
    { id: "strong_only",       sub: "every task at the frontier tier" },
    { id: "efficient_only",    sub: "every task on the open model" },
    { id: "manual_classifier", sub: "a cheap model picks the lane" },
    { id: "switchyard_stage",  sub: "the SDK reads the trajectory" },
    { id: "gateway",           sub: "routes.toml decides, out of process" },
    // MockRouter replaces the routing DECISION, not the answering call — mock_demo
    // needs NVIDIA_API_KEY like every other strategy. What it does not need is the SDK.
    { id: "mock_demo",         sub: "no SDK needed — deterministic demo router" }
  ];

  // First unlocked wins; the learner's own pick is sticky from then on. Routed
  // before flat-rate: the client defaults to the cheap lane, like the module argues.
  var AUTO_DEFAULTS = ["switchyard_stage", "manual_classifier", "efficient_only", "mock_demo"];

  // ---------------------------------------------------------------- tiny DOM

  function $(sel) { return document.querySelector(sel); }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); }

  function num(v) { var n = Number(v); return isFinite(n) ? n : 0; }

  function usd(v, digits) { return "$" + num(v).toFixed(digits == null ? 4 : digits); }

  function trunc(s, n) {
    s = String(s == null ? "" : s);
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  // ------------------------------------------------------------------ toasts

  function toast(message, kind) {
    var box = $("#toasts");
    var node = el("div", "toast" + (kind ? " " + kind : ""), String(message || "").trim() || "unknown error");
    node.addEventListener("click", function () { node.remove(); });
    box.appendChild(node);
    setTimeout(function () { node.remove(); }, kind === "error" ? 12000 : 7000);
  }

  // ------------------------------------------------------------------- state

  var state = {
    status: null,
    sig: "",            // last rendered status signature — kills 5s repaint flicker
    strategy: null,     // the learner's pick, once made
    cost: 0,            // session bill: Σ receipt.cost
    counterfactual: 0,  // Σ receipt.counterfactual_cost — the frontier-only price of the same session
    saved: 0,           // Σ receipt.counterfactual_saved (a frontier call contributes 0.0 by construction)
    lane: null,         // lane of the decision in flight, for the receipt that follows it
    busy: false         // a query in flight
  };

  // While a query is spending, Send goes quiet and the signal lamp names the
  // strategy carrying it. One truth, consulted everywhere.
  function syncBusy() {
    $("#send").disabled = state.busy;
    var lamp = $("#busy-live");
    if (state.busy) lamp.textContent = "routing via " + (state.strategy || "…") + " …";
    lamp.hidden = !state.busy;
  }

  // ------------------------------------------------------------- SSE reading

  // FastAPI answers a malformed body with a 422 JSON document, not a stream — so
  // the content type is checked BEFORE anything tries to parse frames out of it.
  function detailText(payload) {
    var d = payload && payload.detail;
    if (!d) return "";
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d.map(function (e) {
        return (e && e.loc ? e.loc.join(".") + ": " : "") + (e && e.msg ? e.msg : JSON.stringify(e));
      }).join("; ");
    }
    return JSON.stringify(d);
  }

  function dispatchFrame(frame, onEvent) {
    var name = "message", data = [];
    frame.split(/\r?\n/).forEach(function (line) {
      if (!line || line.charAt(0) === ":") return;       // blank line or SSE comment
      var i = line.indexOf(":");
      var field = i === -1 ? line : line.slice(0, i);
      var value = i === -1 ? "" : line.slice(i + 1);
      if (value.charAt(0) === " ") value = value.slice(1);
      if (field === "event") name = value;
      else if (field === "data") data.push(value);
    });
    if (!data.length) return;
    var payload;
    try { payload = JSON.parse(data.join("\n")); }
    catch (err) { payload = { message: data.join("\n") }; }
    onEvent(name, payload);
  }

  function stream(path, body, onEvent) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (res) {
      var ctype = (res.headers.get("content-type") || "").toLowerCase();
      if (ctype.indexOf("text/event-stream") === -1) {
        return res.text().then(function (raw) {
          var message = "";
          try { message = detailText(JSON.parse(raw)); } catch (err) { /* not JSON */ }
          throw new Error("HTTP " + res.status + " — " + (message || trunc(raw, 300) || "no body"));
        });
      }
      var reader = res.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";
      function pump() {
        return reader.read().then(function (chunk) {
          if (chunk.done) {
            buffer += decoder.decode();
            if (buffer.trim()) dispatchFrame(buffer, onEvent);   // last frame, no trailing blank line
            return;
          }
          buffer += decoder.decode(chunk.value, { stream: true });
          var frames = buffer.split(/\r?\n\r?\n/);
          buffer = frames.pop();                                  // the incomplete tail
          frames.forEach(function (frame) { dispatchFrame(frame, onEvent); });
          return pump();
        });
      }
      return pump();
    });
  }

  // -------------------------------------------------------------- the yard

  // yard.svg is its own document inside <object>, so its ids live in
  // contentDocument. If that is unavailable, the SVG is inlined into this document
  // instead and yardDoc becomes `document` — either way yEl() finds the ids.
  var yardDoc = null, cardRaf = 0;

  function yEl(id) { return yardDoc ? yardDoc.getElementById(id) : null; }

  function bindYard() {
    var obj = $("#yard");
    // Already inlined: the <object> is gone from the page, and re-deriving yardDoc
    // from it would drop the SVG that IS on the page (the object's load event can
    // still fire after inlineYard has replaced the node).
    if (!obj && $(".yard-inline svg")) return true;
    try { yardDoc = (obj && obj.contentDocument) || null; } catch (err) { yardDoc = null; }
    if (yardDoc && yardDoc.getElementById("card")) return true;
    yardDoc = null;
    return false;
  }

  function inlineYard() {
    var obj = $("#yard");
    if (!obj) return;
    fetch("yard.svg").then(function (r) { return r.text(); }).then(function (svg) {
      if (bindYard()) return;                       // it loaded while we were fetching
      var host = el("div", "yard-inline");
      host.innerHTML = svg;
      obj.parentNode.replaceChild(host, obj);
      yardDoc = document;
    }).catch(function () { /* the yard is decoration; the receipts still tell the story */ });
  }

  function setupYard() {
    var obj = $("#yard");
    if (!obj) return;
    if (bindYard()) return;
    obj.addEventListener("load", function () { bindYard(); });
    setTimeout(function () { if (!bindYard()) inlineYard(); }, 1500);
  }

  // Three lanes in the SVG, three lanes on the wire (server.py derives them from the
  // receipt's model id). The names match so nothing has to translate twice.
  var RAIL_OF = { efficient: "rail-efficient", capable: "rail-capable", local: "rail-gpu" };
  var LOCO_OF = { efficient: "loco-efficient", capable: "loco-capable", local: "loco-gpu" };
  var HOT_OF = { efficient: "y-hot-efficient", capable: "y-hot-capable", local: "y-hot-local" };

  // Which rail a decision actually drives down. `local` means the gateway named a
  // model neither constant covers — Ex4b's NIM, or an upstream rename — so it goes
  // to the GPU rail when that lane is on the page and to the efficient one when it
  // is not. The receipt shows the raw id either way, which is what keeps the
  // fallback honest: the yard is short a rail, not wrong about the model.
  function slotFor(lane) {
    if (lane === "capable") return "capable";
    if (lane === "local" && gpu.shown) return "local";
    return "efficient";
  }

  function railOf(lane) { return yEl(RAIL_OF[slotFor(lane)]); }

  function paintLanes(lane) {
    ["rail-in", "rail-efficient", "rail-capable", "rail-gpu"].forEach(function (id) {
      var rail = yEl(id);
      if (rail) rail.classList.remove("y-hot-efficient", "y-hot-capable", "y-hot-local");
    });
    ["loco-efficient", "loco-capable", "loco-gpu"].forEach(function (id) {
      var loco = yEl(id);
      if (loco) loco.classList.remove("y-lit");
    });
    if (!lane) return;
    var slot = slotFor(lane), hot = HOT_OF[slot];
    var railIn = yEl("rail-in"), branch = yEl(RAIL_OF[slot]);
    if (railIn) railIn.classList.add(hot);
    if (branch) branch.classList.add(hot);
    var loco = yEl(LOCO_OF[slot]);
    if (loco) loco.classList.add("y-lit");
  }

  function park(card, path, at) {
    var point = path.getPointAtLength(at * path.getTotalLength());
    card.setAttribute("transform", "translate(" + point.x.toFixed(2) + " " + point.y.toFixed(2) + ")");
  }

  function resetCard() {
    var card = yEl("card"), railIn = yEl("rail-in");
    if (!card || !railIn) return;
    cancelAnimationFrame(cardRaf);
    park(card, railIn, 0);
    card.setAttribute("opacity", "0.4");
    paintLanes(null);
    var why = yEl("dispatcher-why");
    if (why) why.textContent = "…";
  }

  // ~940ms total: onto the dispatcher, then down the decided branch.
  function runCard(lane) {
    var card = yEl("card"), railIn = yEl("rail-in"), branch = railOf(lane);
    if (!card || !railIn || !branch) return;
    card.setAttribute("opacity", "1");
    var legs = [{ path: railIn, ms: 320 }, { path: branch, ms: 620 }];
    var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (still) { park(card, branch, 1); return; }
    cancelAnimationFrame(cardRaf);
    var leg = 0;
    function drive() {
      var path = legs[leg].path, ms = legs[leg].ms, t0 = performance.now();
      function step(now) {
        var p = Math.min(1, (now - t0) / ms);
        var eased = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
        park(card, path, eased);
        if (p < 1) cardRaf = requestAnimationFrame(step);
        else if (++leg < legs.length) drive();
      }
      cardRaf = requestAnimationFrame(step);
    }
    drive();
  }

  function onDecision(d) {
    state.lane = LANE_WORDS[d.lane] ? d.lane : "efficient";
    var why = yEl("dispatcher-why");
    if (why) why.textContent = trunc(d.why || d.model || "", 26);
    paintLanes(state.lane);
    runCard(state.lane);
  }

  // ------------------------------------------------- the local lane (Ex4b)

  // The third locomotive is hidden until there is something true to say with it:
  // gateway mode on (a local NIM is a gateway target — off gateway mode a GPU
  // reading explains nothing on this page) AND /api/gpu reporting a GPU.
  var gpu = { shown: false, timer: 0, inFlight: false };

  function gatewayMode() { return state.strategy === "gateway"; }

  function showGpuLane(on) {
    var lane = yEl("lane-gpu");
    if (!lane || gpu.shown === on) return;      // yard not bound yet, or already there
    gpu.shown = on;
    lane.style.display = on ? "" : "none";
    // The lane is drawn below the 900x320 frame, so the drawing AND the box holding
    // it have to grow together — a taller viewBox alone just shrinks itself to fit.
    var svg = yEl("yard-svg"), host = $("#yard");
    if (svg) svg.setAttribute("viewBox", on ? "0 0 900 360" : "0 0 900 320");
    if (host) host.classList.toggle("with-gpu", on);          // null on the inline path
    if (!on && state.lane === "local") resetCard();           // no rail left to park on
  }

  function setGpu(g) {
    var available = !!(g && g.available);
    if (available) {
      var util = Number(g.utilization_pct);
      var reading = isFinite(util) ? util.toFixed(0) : "—";
      var badge = yEl("gpu-badge");
      if (badge) badge.textContent = reading + "% util";
      // memory.used reads [N/A] on unified-memory parts, so it rides in the hover
      // title: the badge is one live number and must never render a blank one.
      var title = yEl("gpu-title");
      if (title) {
        title.textContent = "nvidia-smi · " + reading + "% utilization · " +
          (g.memory_used_mb == null ? "memory used not reported by this driver"
                                    : g.memory_used_mb + " MiB used");
      }
    }
    showGpuLane(available && gatewayMode());
  }

  function pollGpu() {
    if (gpu.inFlight || document.visibilityState === "hidden") return;
    if (!gatewayMode()) { showGpuLane(false); return; }
    gpu.inFlight = true;
    fetch("api/gpu", { cache: "no-store" }).then(function (res) {
      return res.ok ? res.json() : { available: false };
    }).then(setGpu).catch(function () {
      showGpuLane(false);     // our own server is down; the status poll does the toast
    }).then(function () { gpu.inFlight = false; });
  }

  function syncGpuPolling() {
    clearInterval(gpu.timer);
    gpu.timer = 0;
    if (!gatewayMode()) { showGpuLane(false); return; }   // no lane, and nothing to poll
    if (document.visibilityState === "hidden") return;    // paused; the lane stays as it is
    pollGpu();
    gpu.timer = setInterval(pollGpu, GPU_POLL_MS);
  }

  // ------------------------------------------------ the gateway's own meter

  function count(v) { return Math.round(num(v)).toLocaleString(); }

  // One write, and only when the words actually changed: this line is polled every
  // POLL_MS and it is aria-live, so rebuilding identical text would have a screen
  // reader announce the same meter every five seconds.
  function paintStats(node, cls, head, rest) {
    if (!node.hidden && node.className === cls && node.textContent === head + rest) return;
    clear(node);
    node.className = cls;
    node.hidden = false;
    node.appendChild(el("b", null, head));
    node.appendChild(document.createTextNode(rest));
  }

  // Same three figures the lab's Exercise 4 prints. METER ON TOKENS, NEVER ON
  // CALLS: the gateway's
  // `tiers.*.calls` reads 0 for its default tier however much traffic it served (a
  // verified upstream quirk — docs/specs/switchyard-api-notes.md); token_pct is the
  // honest share.
  function statsBits(stats) {
    var classifier = stats.classifier || {};
    var overhead = stats.routing_overhead || {};
    var calls = num(classifier.total_requests);
    var tiers = stats.tiers || {};
    var names = Object.keys(tiers).sort();
    return {
      tax: count(calls) + (calls === 1 ? " judge call · " : " judge calls · ") +
           count((classifier.total_tokens || {}).total) + " tokens · " +
           count(overhead.avg_ms) + " ms added per request",
      split: names.map(function (name) {
        return name + " " + num(tiers[name].token_pct).toFixed(0) + "%";
      }).join(" / "),
      hasTiers: names.length > 0
    };
  }

  function renderGatewayStats(payload) {
    var node = $("#gateway-stats");
    var stats = payload && payload.available && payload.stats;
    if (!stats) {           // no gateway mode, no gateway, or no stats from it
      clear(node);
      node.className = "";
      node.hidden = true;
      return;
    }

    var bits = statsBits(stats);
    var tax = bits.tax;
    if (!bits.hasTiers) {
      // An unlabelled tier is not a missing datum: it is the router having failed to
      // decide, with every request served anyway. The lab's Ex4 print says the same.
      paintStats(node, "degraded", "⚠ the gateway reports no tier labels",
        " — requests are being served without a routing decision. Check the judge " +
        "target in routes.toml (both traps are commented there). Router tax so far: " +
        tax + ".");
      return;
    }
    paintStats(node, "", "the gateway's own meter",
      " · tokens by tier: " + bits.split + " · router tax: " + tax +
      " — spent server-side, which is why every receipt above reads $0.0000 of it.");
  }

  // One read at a time, on the gpu.inFlight discipline. This one earns the guard
  // twice over: the request re-executes the lab file server-side AND opens a socket
  // to the gateway, and /api/status's liveness probe only proves a TCP connect (0.3s)
  // while the read behind it may take 30 — so a gateway that accepts and then stalls
  // would otherwise stack a fresh request every POLL_MS, each holding a server worker,
  // with an older answer free to paint over a newer one.
  var statsInFlight = false;

  function refreshGatewayStats() {
    if (statsInFlight) return;
    if (!gatewayMode()) { renderGatewayStats(null); return; }
    statsInFlight = true;
    fetch("api/gateway_stats", { cache: "no-store" }).then(function (res) {
      return res.json();          // 503 carries {available:false, error} — same shape
    }).then(renderGatewayStats).catch(function () {
      renderGatewayStats(null);
    }).then(function () { statsInFlight = false; });
  }

  // Both gateway-only panels move together whenever the picked strategy does — but
  // only ONE of them fetches from here. The meter's single fetch site is
  // refreshStatus's own tick (below), so a status change that reaches both paths
  // cannot fire two reads: leaving gateway mode hides the line immediately, entering
  // it fills the line on the next status tick, and the numbers stay fresh after a
  // query because ask() ends in refreshStatus().
  function syncGatewayPanels() {
    syncGpuPolling();
    if (!gatewayMode()) renderGatewayStats(null);
  }

  // ---------------------------------------------------------------- receipts

  // Also the set of lanes this client knows: onDecision falls back to `efficient` for
  // anything else, rather than rendering a lane with no word for it.
  var LANE_WORDS = { efficient: "efficient · open", capable: "capable · frontier",
                     local: "local · your GPU" };

  function onReceipt(r) {
    var cost = num(r.cost);
    var counterfactual = num(r.counterfactual_cost);
    // server.py adds counterfactual_saved; fall back to the subtraction it does.
    var saved = ("counterfactual_saved" in r) ? num(r.counterfactual_saved) : counterfactual - cost;
    var lane = state.lane || "efficient";

    state.cost += cost;
    state.counterfactual += counterfactual;
    state.saved += saved;
    renderMeters();

    var li = el("li", "receipt " + lane);
    var top = el("div", "top");
    top.appendChild(el("span", "lane", LANE_WORDS[lane]));
    top.appendChild(el("span", "model", r.model || "(model unnamed)"));
    li.appendChild(top);
    li.appendChild(el("div", "why", r.why || ""));

    var bits = [usd(cost), num(r.latency).toFixed(1) + "s",
                num(r.input_tokens) + "→" + num(r.output_tokens) + " tok"];
    if (num(r.router_tax) > 0) bits.push("router tax " + usd(r.router_tax));
    var nums = el("div", "nums", bits.join(" · "));
    li.appendChild(nums);

    li.appendChild(el("div", "saved",
      "would-have-been " + usd(counterfactual) + " at the frontier tier · saved " + usd(saved)));

    var log = $("#receipt-log");
    log.insertBefore(li, log.firstChild);
    while (log.children.length > 50) log.removeChild(log.lastChild);
  }

  function renderMeters() {
    $("#bill").textContent = usd(state.cost);
    // The percentage is measured against what THIS session would have cost with
    // every call at the frontier tier — 0% until something has been spent.
    var pct = state.counterfactual > 0 ? (100 * state.saved / state.counterfactual) : 0;
    $("#saved").textContent = usd(state.saved) + " (" + pct.toFixed(0) + "%)";
  }

  function showReply(question, answer) {
    var box = $("#reply");
    box.hidden = false;
    box.querySelector(".reply-q").textContent = "› " + question;
    box.querySelector(".reply-a").textContent = answer == null ? "" : String(answer);
  }

  // ------------------------------------------------------------- the query

  // Returns true when a query was actually dispatched — the ask box only clears
  // itself on true, so a refused send (busy, no strategy) never eats typed text.
  function ask(text) {
    text = String(text || "").trim();
    if (!text) return false;
    if (state.busy) { toast("a query is already in flight — wait for it to land"); return false; }
    if (!state.strategy) { toast("pick a strategy first"); return false; }

    state.busy = true;
    state.lane = null;
    syncBusy();
    resetCard();

    var sawAnswer = false, sawError = false;
    stream("api/query", { text: text, strategy: state.strategy }, function (name, d) {
      if (name === "route_decision") onDecision(d);
      else if (name === "receipt") onReceipt(d);
      else if (name === "answer") { sawAnswer = true; showReply(text, d.text); }
      else if (name === "error") { sawError = true; toast(d.message, "error"); }
    }).then(function () {
      if (!sawAnswer && !sawError) {
        toast("stream ended unexpectedly — no answer and no error arrived. Check the terminal " +
              "running the client.", "error");
      }
    }).catch(function (err) {
      toast(err && err.message ? err.message : String(err), "error");
    }).then(function () {
      state.busy = false;
      syncBusy();
      refreshStatus();      // a query that filled in a blank may have unlocked something
    });
    return true;
  }

  // ---------------------------------------------------------------- status

  function unlocked(strategy, s) {
    if (!s) return false;
    if (strategy === "mock_demo") return true;
    if (strategy === "gateway") return !!s.gateway_alive;
    var key = UNLOCK_OF[strategy];
    return !!(s.unlocks && s.unlocks[key]);
  }

  function lockNote(strategy) {
    if (strategy === "gateway") {
      return "unlocks in Exercise 4 — start it with: bash scripts/serve_gateway.sh routes.toml";
    }
    var exercise = EXERCISE_OF[UNLOCK_OF[strategy]];
    return exercise ? "unlocks in Exercise " + exercise : "locked";
  }

  function renderStrategies(s) {
    var box = $("#strategies");
    clear(box);
    STRATEGIES.forEach(function (spec) {
      var open = unlocked(spec.id, s);
      var chip = el("button", "chip" + (open ? "" : " locked") + (state.strategy === spec.id ? " on" : ""));
      chip.type = "button";
      chip.disabled = !open;
      chip.setAttribute("aria-pressed", state.strategy === spec.id ? "true" : "false");
      chip.title = open ? spec.sub : lockNote(spec.id);
      chip.appendChild(el("span", "id", spec.id));
      chip.appendChild(el("span", "sub", open ? spec.sub : lockNote(spec.id)));
      chip.addEventListener("click", function () {
        state.strategy = spec.id;
        renderStatus(state.status);      // repaints from the same seam a poll uses
      });
      box.appendChild(chip);
    });
  }

  function renderOnline(s) {
    var systems = [
      ["Ex1 · the meter", !!(s.unlocks && s.unlocks.ex1)],
      ["Ex2 · the classifier", !!(s.unlocks && s.unlocks.ex2)],
      ["Ex3 · the stage router", !!(s.unlocks && s.unlocks.ex3)],
      ["Ex4 · the gateway", !!s.gateway_alive],
      ["Ex5 · the verdict", !!(s.unlocks && s.unlocks.ex5)]
    ];
    var on = systems.filter(function (row) { return row[1]; }).length;
    var strip = $("#online");
    strip.textContent = "systems online: " + on + "/5";
    strip.classList.toggle("all-on", on === 5);
    strip.title = systems.map(function (row) {
      return (row[1] ? "● " : "○ ") + row[0];
    }).join("\n");
  }

  function banner(kind, head, body, command, tail) {
    var node = el("div", "banner " + kind);
    node.appendChild(el("b", null, head));
    node.appendChild(document.createTextNode(" " + body));
    if (command) node.appendChild(el("pre", null, command));
    if (tail) node.appendChild(el("div", null, tail));
    return node;
  }

  // The server sends its own absolute repo root, and it shares a filesystem with the
  // learner's terminal: /project inside JupyterLab, the clone's path outside it.
  function repoRoot(s) { return (s && s.repo_root) || "/project"; }

  function renderBanners(s) {
    var box = $("#banners");
    clear(box);
    if (!s.key_present) {
      // The server already looked in BOTH places a key can live for a tile — its
      // own environment and <root>/secrets.env, which it re-reads on every poll —
      // so this banner means the key is genuinely nowhere, and the fix needs no
      // relaunch: the moment secrets.env has it, this banner takes itself down.
      box.appendChild(banner("bad",
        "NVIDIA_API_KEY is missing — not in the client's environment, and not in " +
        repoRoot(s) + "/secrets.env.",
        "Every live query will fail until it's set, mock_demo included (its router is a " +
        "mock; the call that answers is real). Save it with the Secrets Manager tile on " +
        "the JupyterLab launcher, or add this line to " + repoRoot(s) + "/secrets.env — " +
        "the client re-reads that file every few seconds, no relaunch needed:",
        "NVIDIA_API_KEY=nvapi-…",
        "The one exception is gateway: its answers are bought with the key exported in " +
        "the terminal running the gateway (Exercise 4's serve step)."));
    }
    if (s.lab_error) {
      box.appendChild(banner("warn",
        "routing_lab.py did not execute.",
        "Every system reads offline until it does — this is the file itself failing, not a " +
        "blank exercise:",
        s.lab_error,
        s.lab_hint || ""));
    }
    if (!s.sdk_available) {
      box.appendChild(banner("warn",
        "The Switchyard SDK is not importable from the client's interpreter.",
        "switchyard_stage answers through the MockRouter demo path instead — the query still " +
        "routes, but the decision is the mock's, not the SDK's. Install it, then relaunch " +
        "the tile — the SDK is bound once per server process, so a relaunch is what swaps " +
        "the mock out:",
        "bash scripts/install_switchyard.sh"));
    }
  }

  function renderStatus(s) {
    if (!s) return;
    state.status = s;
    if (state.strategy && !unlocked(state.strategy, s)) state.strategy = null;   // it re-locked
    if (!state.strategy) {
      for (var i = 0; i < AUTO_DEFAULTS.length; i++) {
        if (unlocked(AUTO_DEFAULTS[i], s)) { state.strategy = AUTO_DEFAULTS[i]; break; }
      }
    }
    renderOnline(s);
    // Repaint the chips/banners only when something actually moved: this runs every
    // POLL_MS, and rebuilding the header on every tick flickers and eats hover.
    var sig = JSON.stringify([s.unlocks, s.gateway_alive, s.key_present, s.sdk_available,
                              s.lab_error, s.lab_hint, s.repo_root, state.strategy]);
    if (sig === state.sig) return;
    state.sig = sig;
    renderStrategies(s);
    renderBanners(s);
    // Only when the pick actually moved: the GPU poll runs at 2s, and restarting its
    // interval on every 5s status tick would quietly stretch it.
    syncGatewayPanels();
  }

  var statusInFlight = false, statusDown = false;

  function refreshStatus() {
    if (statusInFlight || document.visibilityState === "hidden") return;
    statusInFlight = true;
    fetch("api/status", { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    }).then(function (s) {
      statusDown = false;
      renderStatus(s);
      // THE meter's one fetch site — after renderStatus, so a tick that just switched
      // the pick to gateway mode fills the line on that same tick.
      refreshGatewayStats();
    }).catch(function (err) {
      if (!statusDown) {
        statusDown = true;
        state.sig = "";     // force a full repaint when it comes back
        toast("the client's server stopped answering (" + (err.message || err) + "). " +
              "Relaunch the Routing Client tile.", "error");
      }
    }).then(function () { statusInFlight = false; });
  }

  // The status endpoint re-executes the lab file on every call, so it is polled
  // slowly and not at all while nobody is looking at it.
  var pollTimer = 0;

  function startPolling() {
    clearInterval(pollTimer);
    pollTimer = setInterval(refreshStatus, POLL_MS);
  }

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") clearInterval(pollTimer);
    else { refreshStatus(); startPolling(); }
    syncGpuPolling();       // stops the 2s GPU poll too, and restarts it on return
  });

  // ------------------------------------------------------------------- boot

  function wire() {
    var input = $("#q");

    // NEVER via form submission. The JupyterLab launcher renders this app in an
    // iframe sandboxed WITHOUT allow-forms (jupyter-app-launcher pins the token
    // list), and a sandboxed form does not submit: Enter and a type=submit button
    // do nothing, fire no event, and log only to a console the learner never sees.
    // Click and keydown are not form submission, so the box is driven from those;
    // the submit listener stays as a belt-and-braces fallback for any unsandboxed
    // context (it cannot double-fire — Enter is consumed by the keydown handler
    // before implicit submission, and the Send button is type=button).
    function submitQuery() {
      if (ask(input.value)) input.value = "";
      else if (!String(input.value || "").trim()) input.focus();
    }

    input.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" || event.isComposing) return;
      event.preventDefault();
      submitQuery();
    });
    $("#send").addEventListener("click", submitQuery);
    $("#ask").addEventListener("submit", function (event) {
      event.preventDefault();
      submitQuery();
    });

    Array.prototype.forEach.call(document.querySelectorAll("#chips .ex"), function (button) {
      button.addEventListener("click", function () { ask(button.textContent); });
    });
  }

  setupYard();
  wire();
  renderMeters();
  refreshStatus();
  startPolling();
})();
