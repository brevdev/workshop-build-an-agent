"""Module 8 single source of truth (spec §8b.7): every volatile string lives
here or in scripts/install_switchyard.sh — never inline in exercises or docs."""

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Mirrors MODEL_CAPABLE / MODEL_EFFICIENT in scripts/install_switchyard.sh
# (THE pin record) — bump both in the same diff.
STRONG_MODEL = "nvidia/nemotron-3-super-120b-a12b"        # plays the frontier role (stand-in — see lab Ex1 aside)
EFFICIENT_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
CLASSIFIER_MODEL = EFFICIENT_MODEL                         # no third model by design

# USD per 1M tokens {in, out}. Teaching rates representative of public per-token
# pricing tiers; recalibrate/source in the Task 20 pass.  <!-- CALIBRATE -->
PRICING = {
    STRONG_MODEL:    {"in": 5.00, "out": 15.00},
    EFFICIENT_MODEL: {"in": 0.30, "out": 1.20},
}

GATEWAY_BASE_URL = "http://localhost:4000/v1"
GATEWAY_ROUTE_ID = "switchyard"

STRATEGIES = ["strong_only", "efficient_only", "manual_classifier",
              "switchyard_stage", "gateway", "mock_demo"]

AT_SCALE_TASKS_PER_DAY = 1000   # the tokenomics extrapolation everyone sees
