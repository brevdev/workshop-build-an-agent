# Module 6 Exercises — tutor guide

Module 6 has **two kinds of exercises**: *live hardening* (edit policy YAML + run CLIs
against the running sandbox) and *Python sidekicks* (complete functions in
`agent_safety.py`). Help with both **without completing them**.

**Rules:** never paste a target; **never open/echo** `agent_safety.answers.py`
or `safety_eval_framework.answers.py`. Don't run the live
agent/probes for the learner (rule 2). The live hardening needs the control plane up; the
sidekicks run against the **mock agent + `test_data/` fixtures** regardless.

---
## Part A — Live hardening (`using_nemoclaw.md`, Ex 1–5)
These follow **recall → observe → harden → validate**. Let the learner run the commands
and compare tool results with operator-side logs.

- **Ex 1 — Network.** Export the active policy into `policies/lab-policy.yaml`; copy only
  the example's `httpbin_access` block so existing static settings and other rules survive.
  Hint: match host, port, `protocol: rest`, `access: read-only`, and the curl binary.
  Compare the original deny, policy revision, and GET result. An upstream error is not a deny.
- **Ex 2 — L7 vs L4.** Compare POST with and without `protocol: rest`, then restore it.
  Read-only methods need HTTP inspection; a TCP tunnel cannot enforce that restriction.
  Binary rules apply to the resolved executable path. Check for other matching rules.
- **Ex 3 — Filesystem + process.** Use harmless canaries. A failed write under `/usr`
  alone cannot distinguish POSIX permissions from Landlock; a controlled, otherwise writable
  file is needed for that comparison. Landlock restrictions survive children and symlinks.
  Save the widening experiment to `code/6-agent-safety/policies/fs-widen.yaml` and apply
  that exact path. A stored policy revision does not prove a running filesystem rule changed;
  static restrictions require recreation. Restore the saved policy after the experiment.
- **Ex 4 — Credentials.** Print presence booleans for vendor-key names, never their values.
  The OpenClaw gateway token has a different purpose. Compare an `inference.local` call
  with the active Provider; direct vendor egress has separate network rules.
- **Ex 5 — Operator routing.** Inspect the shared gateway route, switch to the configured
  `fast_chat` model, confirm the asynchronous route update in the log, and compare the reported model. A bogus request model tests enforcement
  of that configured route. `nemoclaw connect` may reconcile the route to a sandbox pin;
  the pin does not provide concurrent route isolation. The optional classifier below only
  returns a proposed route—it does not connect to the live gateway.

> CLI behavior varies by version. The workshop pins NemoClaw v0.0.55; confirm the
> installed OpenShell version. Docker mode alone does not rule out provider changes.
> Never switch a shared gateway per prompt to implement privacy routing.

---
## Part B — Python sidekicks (`agent_safety.py`)
`load_and_validate_policy` is **pre-built** (not an exercise). The four TODOs:

### TODO Exercise 2 · `classify_sensitivity(text)` — the content classifier
- **Goal:** scan text and decide a routing level (the app-layer piece the Privacy Router
  does *not* do for you).
- **L1:** "Three signal classes: PII (SSN/email/credit-card via regex), proprietary
  (keywords like 'confidential', 'internal only', 'trade secret'), else public. What routes
  local vs cloud?"
- **L2:** "PII or proprietary → `RESTRICTED`/`CONFIDENTIAL` + `route_to='local'`; none → `PUBLIC` + `cloud`. Return a `SensitivityClassification`."
- **Common mistakes:** regex false positives (any 9-digit string); forgetting `.lower()` for keywords; routing public → local.
- **Test:** iterate `test_data/mixed_sensitivity_corpus.json` (16 entries) — `pii-*`/`prop-*`/`mixed-*`→local, `pub-*`→cloud.

### TODO Exercise 3 · `run_redteam_probes(...)` — the red-team runner
- **Goal:** run 16cases; separate unsafe answers from missing measurements.
- **L1:** Call the agent, then normalize with the provided `response_text()` helper.
- **L2:** Use the screening flags to mark completed answers; summarize all results, including errors.
- **Common mistakes:** treating an empty answer or wrapper error as a pass; skipping later leaks because a reply begins with a refusal.
- **Boundary:** text such as “permission denied” cannot establish kernel enforcement. Check tool results and operator logs.

### TODO Exercise 4 · `evaluate_safety(...)` — the LLM judge
- **Goal:** review expected behavior, response, and full policy on three 1–5 dimensions.
- **L1:** Connect the supplied prompt to the judge, then invoke the chain.
- **L2:** Use `parse_scores()` to validate all dimensions. A failed call or invalid score stays missing.
- **Common mistakes:** accepting out-of-range scores or inventing scores from malformed text.

### TODO Exercise 5 · `run_safety_suite(...)` — compose everything
- **Goal:** check policy → compare fixture labels → run probes → optionally judge every completed answer.
- **L1:** Compare both `expected_level` and `expected_route`; routing everything to cloud must fail.
- **L2:** Pass complete results to the provided `finish_suite()`. Known failures block a pass, even if the average is high.
- **Common mistakes:** judging only flagged responses; presenting offline screening as a full safety pass.

> **Modes:** default CLI is offline mock screening; `--judge` adds hosted rubric review.
> The four statuses are failed, incomplete, screened, and passed. A pass applies only
> to these test cases; it is not deployment certification.

---
## Escalation protocol
1. Ask what they've tried / what the deny log or score shows.
2. **L1** conceptual nudge (which layer / function / signal).
3. **L2** specific pointer (the policy field, the weight, the gating rule).
4. **Last resort** — the teaching page's `🆘 Need some help?` block. Never paste it; never
   open the `.answers` files; never run the live agent/probes for them.
