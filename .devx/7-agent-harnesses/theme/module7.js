/* ==========================================================================
   Module 7 — widget runtime.
   One docsify plugin; all widgets initialize in doneEach with an explicit
   teardown registry so SPA navigation never leaks observers or timers.
   Markdown carries only attribute-driven HTML — no inline <script>.
   ========================================================================== */
(function () {
  'use strict';

  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- teardown registry -------------------------------------------------- */
  var cleanups = [];
  function onCleanup(fn) { cleanups.push(fn); }
  function teardown() {
    cleanups.forEach(function (fn) { try { fn(); } catch (e) { /* noop */ } });
    cleanups = [];
  }
  function observe(targets, cb, opts) {
    var io = new IntersectionObserver(cb, opts || { threshold: 0.35 });
    targets.forEach(function (t) { io.observe(t); });
    onCleanup(function () { io.disconnect(); });
    return io;
  }

  /* ---- 1. hero band ------------------------------------------------------- */
  function initHero(root) {
    root.querySelectorAll('.m7-hero[data-title]').forEach(function (el) {
      if (el.dataset.built) return;
      el.dataset.built = '1';
      var meta = (el.dataset.meta || '')
        .split('|')
        .filter(Boolean)
        .map(function (m) {
          var kv = m.split('::');
          return '<span>' + (kv[1] ? '<b>' + kv[0] + '</b> ' + kv[1] : kv[0]) + '</span>';
        })
        .join('');
      el.innerHTML =
        '<p class="m7-eyebrow">' + (el.dataset.eyebrow || 'MODULE 07') + '</p>' +
        '<h1>' + el.dataset.title + '</h1>' +
        (el.dataset.sub ? '<p class="m7-sub">' + el.dataset.sub + '</p>' : '') +
        (meta ? '<div class="m7-meta">' + meta + '</div>' : '');
    });
  }

  /* ---- 2. reveal on scroll ------------------------------------------------- */
  function initReveals(root) {
    var els = Array.prototype.slice.call(root.querySelectorAll('.m7-reveal'));
    if (!els.length) return;
    if (REDUCED) { els.forEach(function (el) { el.classList.add('is-in'); }); return; }
    observe(els, function (entries, io) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.15 });
  }

  /* ---- 3. token gauges (conic donut + count-up) ----------------------------- */
  function countUp(el, to, suffix, ms) {
    if (REDUCED) { el.textContent = to + (suffix || ''); return; }
    var t0 = null;
    function frame(t) {
      if (!t0) t0 = t;
      var p = Math.min((t - t0) / ms, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * eased) + (suffix || '');
      if (p < 1) {
        var id = requestAnimationFrame(frame);
        onCleanup(function () { cancelAnimationFrame(id); });
      }
    }
    var id = requestAnimationFrame(frame);
    onCleanup(function () { cancelAnimationFrame(id); });
  }

  function initGauges(root) {
    var gauges = Array.prototype.slice.call(root.querySelectorAll('.m7-gauge'));
    if (!gauges.length) return;
    gauges.forEach(function (g) {
      var pct = parseFloat(g.dataset.pct || '0');
      var ring = g.querySelector('.m7-gauge-ring');
      if (ring) ring.style.setProperty('--m7-gauge-to', pct + '%');
    });
    observe(gauges, function (entries, io) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        en.target.classList.add('is-on');
        var ring = en.target.querySelector('.m7-gauge-ring');
        var pct = parseFloat(en.target.dataset.pct || '0');
        if (ring) countUp(ring, Math.round(pct), '%', 1100);
      });
    });
  }

  /* ---- 4. context tax meter ------------------------------------------------ */
  function initTax(root) {
    var meters = Array.prototype.slice.call(root.querySelectorAll('.m7-tax'));
    if (!meters.length) return;
    observe(meters, function (entries, io) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-on'); io.unobserve(en.target); }
      });
    }, { threshold: 0.25 });
  }

  /* ---- 5. self-typing terminal ---------------------------------------------- */
  function parseLines(el) {
    // lines authored as child <span data-kind=... data-delay=...>text</span>
    return Array.prototype.slice.call(el.querySelectorAll('.m7-term-line')).map(function (l) {
      return { el: l, text: l.textContent, kind: l.dataset.kind, delay: parseInt(l.dataset.delay || '0', 10) };
    });
  }

  function typeTerminal(term) {
    var lines = parseLines(term);
    var timers = [];
    function clearTimers() { timers.forEach(clearTimeout); timers = []; }
    onCleanup(clearTimers);

    function showAll() {
      lines.forEach(function (l) { l.el.textContent = l.text; l.el.classList.remove('m7-typing'); });
    }
    if (REDUCED) { showAll(); return { replay: showAll }; }

    function run() {
      clearTimers();
      lines.forEach(function (l) { l.el.textContent = ''; l.el.classList.remove('m7-typing'); });
      var t = 250;
      lines.forEach(function (l) {
        t += l.delay;
        var isTyped = l.kind === 'prompt' || l.kind === 'answer';
        if (isTyped) {
          for (var i = 1; i <= l.text.length; i++) {
            (function (i) {
              timers.push(setTimeout(function () {
                l.el.classList.add('m7-typing');
                l.el.textContent = l.text.slice(0, i);
                if (i === l.text.length) l.el.classList.remove('m7-typing');
              }, t + i * 18));
            })(i);
          }
          t += l.text.length * 18 + 120;
        } else {
          (function (l, t) {
            timers.push(setTimeout(function () { l.el.textContent = l.text; }, t));
          })(l, t);
          t += 320;
        }
      });
    }
    return { replay: run, start: run };
  }

  function initTerminals(root) {
    var terms = Array.prototype.slice.call(root.querySelectorAll('.m7-term'));
    if (!terms.length) return;
    terms.forEach(function (term) {
      if (term.dataset.built) return;
      term.dataset.built = '1';
      var ctl = typeTerminal(term);
      if (!REDUCED) {
        var btn = document.createElement('button');
        btn.className = 'm7-term-replay';
        btn.type = 'button';
        btn.textContent = '↻ replay';
        btn.setAttribute('aria-label', 'Replay terminal animation');
        btn.addEventListener('click', ctl.replay);
        term.appendChild(btn);
        observe([term], function (entries, io) {
          entries.forEach(function (en) {
            if (en.isIntersecting) { io.unobserve(en.target); ctl.start(); }
          });
        }, { threshold: 0.4 });
      }
    });
  }

  /* ---- 6. quiz --------------------------------------------------------------
     markup: .m7-quiz > .m7-quiz-q + button.m7-quiz-opt[data-right][data-fb] */
  function initQuizzes(root) {
    root.querySelectorAll('.m7-quiz').forEach(function (quiz) {
      if (quiz.dataset.built) return;
      quiz.dataset.built = '1';
      var fb = document.createElement('div');
      fb.className = 'm7-quiz-fb';
      fb.setAttribute('role', 'status');
      fb.hidden = true;
      quiz.appendChild(fb);
      quiz.querySelectorAll('.m7-quiz-opt').forEach(function (opt) {
        opt.type = 'button';
        opt.addEventListener('click', function () {
          var right = opt.hasAttribute('data-right');
          quiz.querySelectorAll('.m7-quiz-opt').forEach(function (o) { o.removeAttribute('data-state'); });
          opt.dataset.state = right ? 'right' : 'wrong';
          fb.hidden = false;
          fb.classList.toggle('is-right', right);
          fb.innerHTML = (right ? '<b>Correct.</b> ' : '<b>Not quite.</b> ') + (opt.dataset.fb || '');
        });
      });
    });
  }

  /* ---- 7. predict-before-reveal ---------------------------------------------
     markup: .m7-bet[data-answer][data-explain] > .m7-bet-opts > button.m7-bet-opt */
  function initBets(root) {
    root.querySelectorAll('.m7-bet').forEach(function (bet) {
      if (bet.dataset.built) return;
      bet.dataset.built = '1';
      var reveal = document.createElement('p');
      reveal.className = 'm7-bet-reveal';
      reveal.setAttribute('role', 'status');
      reveal.hidden = true;
      bet.appendChild(reveal);
      bet.querySelectorAll('.m7-bet-opt').forEach(function (opt) {
        opt.type = 'button';
        opt.addEventListener('click', function () {
          bet.querySelectorAll('.m7-bet-opt').forEach(function (o) { o.removeAttribute('data-state'); });
          opt.dataset.state = 'picked';
          reveal.hidden = false;
          reveal.innerHTML = 'Measured answer: <b>' + bet.dataset.answer + '</b> — ' + (bet.dataset.explain || '');
        });
      });
    });
  }

  /* ---- 8. sidebar completion checkmarks -------------------------------------- */
  var DONE_KEY = 'm7-visited';
  function markVisited(route) {
    try {
      var seen = JSON.parse(localStorage.getItem(DONE_KEY) || '[]');
      if (seen.indexOf(route) < 0) { seen.push(route); localStorage.setItem(DONE_KEY, JSON.stringify(seen)); }
    } catch (e) { /* private mode */ }
  }
  function paintSidebar() {
    var seen;
    try { seen = JSON.parse(localStorage.getItem(DONE_KEY) || '[]'); } catch (e) { seen = []; }
    document.querySelectorAll('.sidebar-nav > ul > li').forEach(function (li) {
      var a = li.querySelector('a');
      if (!a) return;
      var href = (a.getAttribute('href') || '').replace(/^#\/?/, '').split('?')[0];
      li.classList.toggle('m7-done', seen.indexOf(href || 'README') >= 0);
    });
  }

  /* ---- 9. module progress beam (reads the unfold nav's "Section x of y") ----- */
  function ensureProgressBeam() {
    var beam = document.getElementById('m7-progress');
    if (!beam) {
      beam = document.createElement('div');
      beam.id = 'm7-progress';
      beam.setAttribute('aria-hidden', 'true');
      document.body.appendChild(beam);
    }
    return beam;
  }
  function watchUnfoldProgress() {
    var beam = ensureProgressBeam();
    function update() {
      var ind = document.querySelector('.progressive-unfold-nav .section-indicator');
      var m = ind && ind.textContent.match(/(\d+)\s+of\s+(\d+)/i);
      beam.style.setProperty('--m7-progress', m ? String(parseInt(m[1], 10) / parseInt(m[2], 10)) : '0');
    }
    update();
    var mo = new MutationObserver(update);
    mo.observe(document.body, { childList: true, subtree: true, characterData: true });
    onCleanup(function () { mo.disconnect(); });
  }

  /* ---- docsify plugin -------------------------------------------------------- */
  function plugin(hook, vm) {
    hook.doneEach(function () {
      teardown();
      var root = document.querySelector('.markdown-section') || document;
      if (root.classList) {
        root.classList.remove('m7-page-in');
        void root.offsetWidth;            /* restart the entrance animation */
        root.classList.add('m7-page-in');
      }
      watchUnfoldProgress();
      initHero(root);
      initTerminals(root);
      initGauges(root);
      initTax(root);
      initQuizzes(root);
      initBets(root);
      initReveals(root);
      // tag code panels with their language for the pre::after chip
      root.querySelectorAll('pre[data-lang]').forEach(function () { /* docsify sets data-lang already */ });
      markVisited((vm.route.path || '/').replace(/^\//, '') || 'README');
      paintSidebar();
    });
  }

  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(plugin);
})();
