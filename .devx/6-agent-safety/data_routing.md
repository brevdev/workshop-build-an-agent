# Data Routing with Privacy Router

<img src="_static/robots/supervisor.png" alt="Data Routing Robot" style="float:right;max-width:300px;margin:25px;" />

Your agent's constraints are enforced at the kernel level. It can only read, write, and connect where the policy allows. But inside that perimeter, every piece of data looks the same. An email containing a customer's Social Security number is treated identically to a public RSS feed summary.

The Privacy Router fixes this by **classifying data before it reaches the LLM**, then routing it to the appropriate inference endpoint based on sensitivity.

<!-- fold:break -->

## The Problem: Mixed-Sensitivity Data Streams

An always-on agent processes data from multiple sources throughout the day:

- **Email** — Customer messages that may contain names, addresses, SSNs, or credit card numbers
- **Documents** — Internal memos marked confidential, quarterly reports, policy drafts
- **RSS feeds** — Public research papers, blog posts, news articles
- **Chat messages** — Slack and Telegram conversations ranging from casual to sensitive
- **Webhooks** — Automated alerts that may include infrastructure credentials or tokens

Without classification, all of this data flows through the same pipeline to the same cloud LLM endpoint. This creates three problems:

1. **Compliance risk** — PII sent to a cloud API may violate GDPR, HIPAA, or internal data governance policies
2. **Data exposure** — Proprietary information processed by a third-party service extends your attack surface
3. **Resource waste** — Public data that could be processed cheaply in the cloud instead burns expensive local GPU cycles

The goal is simple: **sensitive data stays local, public data goes to the cloud**.

<!-- fold:break -->

## Classification Before Routing

The Privacy Router makes a routing decision for every piece of text before it reaches any LLM. The decision tree is:

```
Input text
  |
  +-- PII scan (regex patterns)
  |     |
  |     +-- SSN detected?        --> RESTRICTED, route to local
  |     +-- Email detected?      --> RESTRICTED, route to local
  |     +-- Credit card detected? --> RESTRICTED, route to local
  |
  +-- Proprietary scan (keyword matching)
  |     |
  |     +-- "confidential"?      --> CONFIDENTIAL, route to local
  |     +-- "proprietary"?       --> CONFIDENTIAL, route to local
  |     +-- "internal only"?     --> CONFIDENTIAL, route to local
  |     +-- "trade secret"?      --> CONFIDENTIAL, route to local
  |
  +-- No matches                 --> PUBLIC, route to cloud
```

The classification adds **sub-5ms overhead** per document. For an agent processing hundreds of documents per day, this is negligible compared to LLM inference time.

<!-- fold:break -->

## The Four Sensitivity Levels

The Privacy Router uses four sensitivity tiers:

| Level | Meaning | Route | Example |
|-------|---------|-------|---------|
| **RESTRICTED** | Contains PII (SSN, email, credit card) | Local Nemotron | "Customer SSN: 123-45-6789" |
| **CONFIDENTIAL** | Contains proprietary business information | Local Nemotron | "CONFIDENTIAL: Q3 revenue projections" |
| **INTERNAL** | Organization-internal but not sensitive | Either (prefer local) | "Team standup notes from Monday" |
| **PUBLIC** | No sensitive content detected | Cloud API | "Recent advances in transformer architecture" |

The key boundary is between CONFIDENTIAL and PUBLIC. Everything at CONFIDENTIAL or above **must** stay on local infrastructure. PUBLIC data **can** go to the cloud for maximum model capability and lower cost.

<!-- fold:break -->

## Building the Classifier

The classifier is the core of the Privacy Router. It scans text for patterns and keywords, then assigns a sensitivity level and routing decision.

### PII Detection Patterns

Three regex patterns catch the most common PII types:

| Pattern | Regex | Matches |
|---------|-------|---------|
| SSN | `\b\d{3}-\d{2}-\d{4}\b` | 123-45-6789 |
| Email | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z\|a-z]{2,}\b` | user@company.com |
| Credit card | `\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b` | 4111-1111-1111-1111 |

### Proprietary Keyword Matching

Four keywords (case-insensitive) flag proprietary content:

- `confidential`
- `proprietary`
- `internal only`
- `trade secret`

### Priority Order

PII takes priority over proprietary markers. If a document contains both an SSN and the word "confidential," it's classified as RESTRICTED (the higher tier), not CONFIDENTIAL.

<!-- fold:break -->

## Exercise 2: Classify Data Sensitivity

<button onclick="goToLineAndSelect('code/6-agent-safety/agent_safety.py', '# TODO: Exercise 2');"><i class="fas fa-code"></i> # TODO: Exercise 2</button>

### What You'll Build

The `classify_sensitivity()` function:

1. **Scans** the input text for PII patterns (SSN, email, credit card)
2. **Scans** for proprietary keywords (confidential, proprietary, internal only, trade secret)
3. **Classifies** the text into a sensitivity level (RESTRICTED, CONFIDENTIAL, or PUBLIC)
4. **Determines** the routing destination (local or cloud)
5. **Returns** a `SensitivityClassification` with the full analysis

### Test Data

The `test_data/mixed_sensitivity_corpus.json` file contains documents at every sensitivity level. After implementing the classifier, run it against this corpus and verify:

- Documents with SSNs or emails are classified as RESTRICTED and routed locally
- Documents with "confidential" or "proprietary" keywords are classified as CONFIDENTIAL and routed locally
- Clean documents are classified as PUBLIC and routed to cloud

<!-- fold:break -->

<details>
<summary><strong>Hint: Exercise 2 Solution</strong></summary>

```python
def classify_sensitivity(text: str) -> SensitivityClassification:
    detected_patterns = []

    pii_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    }

    for pattern_name, regex in pii_patterns.items():
        if re.search(regex, text):
            detected_patterns.append(pattern_name)

    proprietary_keywords = ["confidential", "proprietary", "internal only", "trade secret"]
    text_lower = text.lower()
    for keyword in proprietary_keywords:
        if keyword in text_lower:
            detected_patterns.append(f"proprietary:{keyword}")

    if any(p in detected_patterns for p in ["ssn", "email", "credit_card"]):
        level = SensitivityLevel.RESTRICTED
        route_to = "local"
        reasoning = f"PII detected ({', '.join(p for p in detected_patterns if not p.startswith('proprietary:'))}) — must stay on local infrastructure"
    elif any(p.startswith("proprietary:") for p in detected_patterns):
        level = SensitivityLevel.CONFIDENTIAL
        route_to = "local"
        reasoning = f"Proprietary markers detected ({', '.join(p.split(':')[1] for p in detected_patterns if p.startswith('proprietary:'))}) — route to local inference"
    else:
        level = SensitivityLevel.PUBLIC
        route_to = "cloud"
        reasoning = "No sensitive patterns detected — safe for cloud routing"

    return SensitivityClassification(
        text_preview=text[:100],
        level=level,
        detected_patterns=detected_patterns,
        route_to=route_to,
        reasoning=reasoning,
    )
```

</details>

<!-- fold:break -->

## From Classifier to Router

In the NemoClaw stack, the classifier doesn't just label data — it controls the network path. Here's how classification connects to enforcement:

1. **Text arrives** at the agent (email, message, document)
2. **Privacy Router classifies** the text in sub-5ms
3. **If RESTRICTED or CONFIDENTIAL** --> the text is sent to **local Nemotron** (localhost:8080)
4. **If PUBLIC** --> the text is sent to the **cloud NVIDIA NIM API** (integrate.api.nvidia.com)

OpenShell's network policy enforces this at the kernel level:

```yaml
network_policies:
  - name: "local_nemotron"
    endpoints:
      - "localhost:8080"
    methods: ["POST"]

  - name: "llm_api"
    endpoints:
      - "integrate.api.nvidia.com:443"
    methods: ["POST"]
```

The Privacy Router decides the route. OpenShell enforces it. Even if the routing logic is bypassed (bug, injection), the network policy ensures the agent can only reach these two endpoints.

### Local Inference: Nemotron 3 Nano 4B

For local inference of sensitive data, NemoClaw uses a compact model like **Nemotron 3 Nano 4B** that runs efficiently on a single GPU. The agent uses a larger model (e.g., Nemotron Super) via the cloud API for general reasoning, while sensitive queries are handled locally by this compact model. It handles:

- Summarization of sensitive documents
- PII-safe question answering
- Internal memo processing

The tradeoff is capability: Nemotron Nano is smaller than cloud models. But for sensitive data, keeping it local is a hard requirement, not a preference.

<!-- fold:break -->

## Limitations of Regex-Based Detection

The regex classifier you built in Exercise 2 is fast and deterministic. But it has known limitations.

| Approach | Speed | Precision | Recall | Handles Context |
|----------|-------|-----------|--------|----------------|
| **Regex patterns** | Sub-ms | Medium — false positives on number sequences | Medium — misses redacted or formatted PII | No |
| **NER models** (spaCy, Presidio) | ~10ms | High | High for trained entity types | Partially |
| **LLM-based classification** | ~500ms | Very high | Very high | Yes — understands context |
| **Hybrid** (regex + NER + LLM) | ~50ms | Very high | Very high | Yes |

### Common Failure Modes

**False positives** — The SSN regex `\b\d{3}-\d{2}-\d{4}\b` matches any 9-digit number in XXX-XX-XXXX format, including product codes, serial numbers, and date-like strings.

**False negatives** — A redacted SSN like `***-**-6789` or a spelled-out number like "one two three forty-five six seven eight nine" won't match.

**Context blindness** — "My phone number is 555-12-3456" matches the SSN regex. A human (or LLM) would recognize this as a phone number. Regex cannot.

For a production system, you'd layer regex (fast, cheap) with NER (accurate) and LLM-based classification (contextual) in a cascade — only escalating to the slower model when the fast check is ambiguous.

> The classifier tells the agent where to send data. OpenShell enforces the network boundary. But how do you know the agent is actually safe in practice? Head to [NemoClaw: The Complete Stack](nemoclaw_stack) to put it all together and test it.
