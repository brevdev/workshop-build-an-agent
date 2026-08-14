/* Routing Client — the window's glass.
 *
 * WINDOW, NOT WIZARD (the same contract server.py keeps): nothing here decides a
 * lane, prices a token, or grades a race. Every number on the screen arrived on an
 * SSE event from routing_lab.py; this file renders it and animates the yard.
 *
 * The API it consumes (routing_client/server.py):
 *   GET  /api/status  -> {unlocks:{ex1,ex2,ex3,ex5}, gateway_alive, key_present,
 *                         sdk_available, lab_error, repo_root}
 *   GET  /api/gpu     -> {available, utilization_pct, memory_used_mb}   (gateway mode only)
 *   GET  /api/gateway_stats -> {available, stats} | 503 {available:false, error}
 *   POST /api/query   -> SSE: route_decision {lane,model,why} · receipt (+counterfactual_saved)
 *                             · answer {text} · error {message}
 *   POST /api/race    -> SSE: race_row {strategy,accuracy,cost,frontier_pct,router_tax_pct}
 *                             · race_receipt {receipt} · error {message}
 *
 * No frameworks, no build step, no node_modules. Paths are RELATIVE ("api/status",
 * never "/api/status") so the client survives being served under a JupyterLab
 * proxy prefix.
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

  // MIRRORS `RACE_STRATEGIES` in routing_client/server.py: run_suite answers the
  // 12-task workload under these four and raises on anything else. `gateway` and
  // `mock_demo` are /api/query strategies ONLY and must never appear as race chips.
  // A fifth strategy moves both lists in the same diff.
  var RACE_STRATEGIES = ["strong_only", "efficient_only", "manual_classifier", "switchyard_stage"];
  var TASKS_PER_SUITE = 12;

  // What one suite actually costs in LIVE calls — twelve tasks is not twelve calls.
  // Every suite adds one LLM-judge call (the single unverifiable task is graded by a
  // model, not a string check), and manual_classifier pays the router tax: a second
  // call per task before any work happens. 13 + 13 + 25 + 13 = 64 for all four.
  var SUITE_CALLS = { strong_only: TASKS_PER_SUITE + 1, efficient_only: TASKS_PER_SUITE + 1,
                      manual_classifier: TASKS_PER_SUITE * 2 + 1,
                      switchyard_stage: TASKS_PER_SUITE + 1 };
  function raceCalls(picks) {
    return picks.reduce(function (n, id) { return n + (SUITE_CALLS[id] || TASKS_PER_SUITE); }, 0);
  }

  // First unlocked wins; the learner's own pick is sticky from then on. Routed
  // before flat-rate: the client defaults to the cheap lane, like the module argues.
  var AUTO_DEFAULTS = ["switchyard_stage", "manual_classifier", "efficient_only", "mock_demo"];

  var SVG_NS = "http://www.w3.org/2000/svg";

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
    busy: false,
    racing: false,
    raceSel: {},
    raceRows: []
  };

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

  function renderGatewayStats(payload) {
    var node = $("#gateway-stats");
    var stats = payload && payload.available && payload.stats;
    if (!stats) {           // no gateway mode, no gateway, or no stats from it
      clear(node);
      node.className = "";
      node.hidden = true;
      return;
    }

    // Same three figures the lab's Exercise 4 prints, in the same order.
    var classifier = stats.classifier || {};
    var overhead = stats.routing_overhead || {};
    var calls = num(classifier.total_requests);
    var tax = count(calls) + (calls === 1 ? " judge call · " : " judge calls · ") +
              count((classifier.total_tokens || {}).total) + " tokens · " +
              count(overhead.avg_ms) + " ms added per request";

    // METER ON TOKENS, NEVER ON CALLS: the gateway's `tiers.*.calls` reads 0 for its
    // default tier however much traffic that tier served (a verified upstream quirk —
    // docs/specs/switchyard-api-notes.md). token_pct is the honest share.
    var tiers = stats.tiers || {};
    var names = Object.keys(tiers).sort();
    if (!names.length) {
      // An unlabelled tier is not a missing datum: it is the router having failed to
      // decide, with every request served anyway. The lab's Ex4 print says the same.
      paintStats(node, "degraded", "⚠ the gateway reports no tier labels",
        " — requests are being served without a routing decision. Check the judge " +
        "target in routes.toml (both traps are commented there). Router tax so far: " +
        tax + ".");
      return;
    }
    var split = names.map(function (name) {
      return name + " " + num(tiers[name].token_pct).toFixed(0) + "%";
    }).join(" / ");
    paintStats(node, "", "the gateway's own meter",
      " · tokens by tier: " + split + " · router tax: " + tax +
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

  function ask(text) {
    text = String(text || "").trim();
    if (!text) return;
    if (state.busy) { toast("a query is already in flight — wait for it to land"); return; }
    if (!state.strategy) { toast("pick a strategy first"); return; }

    state.busy = true;
    state.lane = null;
    $("#send").disabled = true;
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
      $("#send").disabled = false;
      refreshStatus();      // a query that filled in a blank may have unlocked something
    });
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
      box.appendChild(banner("bad",
        "NVIDIA_API_KEY is not set for this client.",
        "Every live query will fail until it is — except gateway, whose answer is bought " +
        "with the key exported in the terminal running the gateway. Set it in the terminal " +
        "that started the client — the server reads the key once, at startup — then " +
        "relaunch the tile:",
        "set -a; source " + repoRoot(s) + "/secrets.env; set +a",
        "mock_demo is not a way around this either: its router is a mock, but the call " +
        "that answers is a real one."));
    }
    if (s.lab_error) {
      box.appendChild(banner("warn",
        "routing_lab.py did not execute.",
        "Every system reads offline until it does — this is the file itself failing, not a " +
        "blank exercise:",
        s.lab_error));
    }
    if (!s.sdk_available) {
      box.appendChild(banner("warn",
        "The Switchyard SDK is not installed.",
        "switchyard_stage answers through the MockRouter demo path instead — the query still " +
        "routes, but the decision is the mock's, not the SDK's. Install it, then restart the " +
        "tile (the flag is read once at server startup):",
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
                              s.lab_error, s.repo_root, state.strategy]);
    if (sig === state.sig) return;
    state.sig = sig;
    renderStrategies(s);
    renderBanners(s);
    renderRaceChips();
    updateRaceControls();
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

  // ------------------------------------------------------------- race mode

  function renderRaceChips() {
    var box = $("#race-strats");
    clear(box);
    RACE_STRATEGIES.forEach(function (id) {
      var open = unlocked(id, state.status || {});
      if (!open) delete state.raceSel[id];
      var chip = el("button", "chip" + (open ? "" : " locked") + (state.raceSel[id] ? " on" : ""));
      chip.type = "button";
      chip.disabled = !open || state.racing;
      chip.title = open ? SUITE_CALLS[id] + " live model calls" : lockNote(id);
      chip.setAttribute("aria-pressed", state.raceSel[id] ? "true" : "false");
      chip.appendChild(el("span", "id", id));
      chip.appendChild(el("span", "sub", open ? SUITE_CALLS[id] + " live calls" : lockNote(id)));
      chip.addEventListener("click", function () {
        if (state.raceSel[id]) delete state.raceSel[id];
        else state.raceSel[id] = true;
        renderRaceChips();
        updateRaceControls();
      });
      box.appendChild(chip);
    });
  }

  function racePicks() {
    // canonical order, so the row the lab's verdict calls "routed" is the one the
    // learner would expect (server.py re-sorts too — this only keeps the UI honest).
    return RACE_STRATEGIES.filter(function (id) { return !!state.raceSel[id]; });
  }

  function updateRaceControls() {
    var btn = $("#run-race");
    var picks = racePicks();
    var ready = !!(state.status && state.status.unlocks && state.status.unlocks.ex5);
    if (state.racing) {
      btn.disabled = true;
      btn.textContent = "racing " + picks.length + " strategies — " +
                        raceCalls(picks) + " live calls, no cancel …";
      return;
    }
    btn.disabled = !ready || picks.length === 0;
    if (!ready) {
      btn.title = "unlocks in Exercise 5";
      btn.textContent = "Run the 12-task suite — unlocks in Exercise 5 (routing_verdict)";
    } else if (!picks.length) {
      btn.title = "";
      btn.textContent = "Run the 12-task suite — pick at least one strategy above";
    } else {
      btn.title = "";
      btn.textContent = "Run the 12-task suite × " + picks.length + " — ≈" +
                        raceCalls(picks) + " live model calls, several minutes, " +
                        "no cancel" + (picks.length === RACE_STRATEGIES.length ? " (all four)" : "");
    }
  }

  function addRaceRow(row) {
    var tr = el("tr", row.strategy === "strong_only" ? "baseline" : null);
    [row.strategy,
     num(row.accuracy) + "/12",
     usd(row.cost),
     num(row.frontier_pct).toFixed(0) + "%",
     num(row.router_tax_pct).toFixed(0) + "%"
    ].forEach(function (cell) { tr.appendChild(el("td", null, cell)); });
    $("#race-table").querySelector("tbody").appendChild(tr);
  }

  function setRaceReceipt(text, kind) {
    var node = $("#race-receipt");
    node.className = kind;
    node.textContent = text;
  }

  function renderRaceReceipt(receipt) {
    var text = String(receipt == null ? "" : receipt).trim();
    // "insufficient data" is what the lab's verdict returns when it has no
    // strong_only row to compare a routed one against — a state, never a verdict.
    if (!text || text === "insufficient data") {
      setRaceReceipt("not enough strategies finished for a verdict — the comparison needs " +
                     "strong_only plus one routed strategy (manual_classifier or switchyard_stage).",
                     "neutral");
      return;
    }
    setRaceReceipt("🧾 " + text, "verdict");
  }

  function runRace() {
    var picks = racePicks();
    if (!picks.length || state.racing) return;

    state.racing = true;
    state.raceRows = [];
    clear($("#race-table").querySelector("tbody"));
    setRaceReceipt("", "");
    drawPareto();
    renderRaceChips();
    updateRaceControls();

    var sawReceipt = false, sawError = false;
    stream("api/race", { strategies: picks }, function (name, d) {
      if (name === "race_row") {
        state.raceRows.push(d);
        addRaceRow(d);
        drawPareto();
      } else if (name === "race_receipt") {
        sawReceipt = true;
        renderRaceReceipt(d.receipt);
      } else if (name === "error") {
        sawError = true;
        toast(d.message, "error");
        if (!sawReceipt) setRaceReceipt(d.message, "bad");
      }
    }).then(function () {
      if (!sawReceipt && !sawError) {
        toast("the race stream ended without a verdict. Check the terminal running the client.", "error");
      }
    }).catch(function (err) {
      toast(err && err.message ? err.message : String(err), "error");
    }).then(function () {
      state.racing = false;
      renderRaceChips();
      updateRaceControls();
      refreshStatus();
    });
  }

  // ------------------------------------------------- the Pareto scatter (§4c)

  var PAD = { l: 58, r: 22, t: 22, b: 46 }, CHART = { w: 460, h: 260 };
  var INK = { dim: "#c6c6c6", mute: "#8f8f8f", axis: "#2a3441" };

  function svgEl(name, attrs, text) {
    var node = document.createElementNS(SVG_NS, name);
    for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) {
      node.setAttribute(k, attrs[k]);
    }
    if (text != null) node.textContent = text;
    return node;
  }

  function label(x, y, text, anchor, fill) {
    return svgEl("text", {
      x: x.toFixed(1), y: y.toFixed(1), "text-anchor": anchor || "middle",
      fill: fill || INK.mute, "font-size": "11", "font-family": "ui-monospace, Menlo, Consolas, monospace"
    }, text);
  }

  function niceMax(v) {
    if (!(v > 0)) return 0.01;
    var p = Math.pow(10, Math.floor(Math.log10(v)));
    var n = v / p;
    var step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
    return step * p;
  }

  function axisMoney(v) {
    if (v === 0) return "$0";
    return "$" + v.toFixed(v < 0.01 ? 4 : v < 0.1 ? 3 : 2);
  }

  function drawPareto() {
    var svg = $("#pareto");
    clear(svg);
    var x0 = PAD.l, x1 = CHART.w - PAD.r, yBase = CHART.h - PAD.b, yTop = PAD.t;
    var rows = state.raceRows;
    var costs = rows.map(function (r) { return num(r.cost); });
    var xMax = niceMax(Math.max.apply(null, costs.concat([0])) * 1.1);
    var X = function (c) { return x0 + (num(c) / xMax) * (x1 - x0); };
    var Y = function (a) { return yBase - (Math.max(0, Math.min(12, num(a))) / 12) * (yBase - yTop); };

    // two recessive axis lines, no gridlines
    svg.appendChild(svgEl("line", { x1: x0, y1: yBase, x2: x1, y2: yBase, stroke: INK.axis, "stroke-width": 1 }));
    svg.appendChild(svgEl("line", { x1: x0, y1: yTop, x2: x0, y2: yBase, stroke: INK.axis, "stroke-width": 1 }));
    [0, 6, 12].forEach(function (a) { svg.appendChild(label(x0 - 9, Y(a) + 4, String(a), "end")); });
    [0, xMax / 2, xMax].forEach(function (c) { svg.appendChild(label(X(c), yBase + 18, axisMoney(c), "middle")); });
    svg.appendChild(label((x0 + x1) / 2, CHART.h - 8, "cost ($ · 12 tasks)", "middle"));
    var midY = yTop + (yBase - yTop) / 2;
    var yTitle = label(16, midY, "accuracy (/12)", "middle");
    yTitle.setAttribute("transform", "rotate(-90 16 " + midY.toFixed(1) + ")");
    svg.appendChild(yTitle);

    if (!rows.length) {
      svg.appendChild(label((x0 + x1) / 2, midY, "each finished strategy lands here", "middle"));
      return;
    }

    // Identity is carried by the direct label on every point, never by hue alone:
    // #76b900 and #e8a33d are ~2 ΔE apart under protanopia. Shape doubles it up —
    // the frontier baseline is a hollow diamond, the routed points filled dots.
    var placed = [];
    rows.forEach(function (row) {
      var px = X(row.cost), py = Y(row.accuracy);
      var baseline = row.strategy === "strong_only";
      var color = baseline ? "#e8a33d" : "#76b900";
      var g = svgEl("g", {});
      g.appendChild(svgEl("title", {}, row.strategy + ": " + num(row.accuracy) + "/12 · " + usd(row.cost)));
      g.appendChild(svgEl("circle", { cx: px, cy: py, r: 13, fill: "transparent" }));   // 26px hit target
      if (baseline) {
        g.appendChild(svgEl("rect", {
          x: (px - 6).toFixed(1), y: (py - 6).toFixed(1), width: 12, height: 12,
          fill: "none", stroke: color, "stroke-width": 2,
          transform: "rotate(45 " + px.toFixed(1) + " " + py.toFixed(1) + ")"
        }));
      } else {
        g.appendChild(svgEl("circle", {
          cx: px.toFixed(1), cy: py.toFixed(1), r: 5.5,
          fill: color, stroke: "#0e1116", "stroke-width": 2
        }));
      }

      // Two 11px lines per point (name over values). Placed above the dot when that
      // band is free, then successively further below: race points bunch up at 12/12,
      // and a label written over another label is worse than one written a little
      // away from its dot. Widths are measured in monospace columns, so the check is
      // a real box overlap rather than a guess at horizontal distance.
      var lines = [row.strategy, num(row.accuracy) + "/12 · " + usd(row.cost)];
      var width = Math.max(lines[0].length, lines[1].length) * 6.6;
      var anchor = px > x1 - 70 ? "end" : (px < x0 + 70 ? "start" : "middle");
      var left = anchor === "end" ? px - width : (anchor === "start" ? px : px - width / 2);
      var box = null;
      [-26, 20, 44, -50, 68, 92].forEach(function (dy) {
        if (box) return;
        var slot = { left: left, right: left + width, top: py + dy - 8, bottom: py + dy + 16, y: py + dy };
        if (slot.top < 2 || slot.bottom > yBase + 2) return;
        var clash = placed.some(function (p) {
          return slot.left < p.right && p.left < slot.right && slot.top < p.bottom && p.top < slot.bottom;
        });
        if (!clash) box = slot;
      });
      if (!box) {   // every slot taken: put it back by the dot, clamped into the plot
        var y = Math.min(Math.max(py + 20, 10), yBase - 14);
        box = { left: left, right: left + width, top: y - 8, bottom: y + 16, y: y };
      }
      placed.push(box);
      g.appendChild(label(px, box.y, lines[0], anchor, INK.dim));
      g.appendChild(label(px, box.y + 12, lines[1], anchor, INK.mute));
      svg.appendChild(g);
    });
  }

  // ------------------------------------------------------------------- boot

  function wire() {
    $("#ask").addEventListener("submit", function (event) {
      event.preventDefault();
      var input = $("#q");
      ask(input.value);
      input.value = "";
    });

    Array.prototype.forEach.call(document.querySelectorAll("#chips .ex"), function (button) {
      button.addEventListener("click", function () { ask(button.textContent); });
    });

    $("#run-race").addEventListener("click", runRace);
  }

  setupYard();
  wire();
  drawPareto();
  renderMeters();
  refreshStatus();
  startPolling();
})();
