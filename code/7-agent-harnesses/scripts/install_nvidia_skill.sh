#!/usr/bin/env bash
# Install an NVIDIA Verified Skill into the lab skills directory —
# verifying its signature and showing its skill card BEFORE trusting it.
#
# Usage: bash install_nvidia_skill.sh [skill-name]
set -euo pipefail

SKILL="${1:-accelerated-computing-cudf}"
LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_DIR="${LAB_DIR}/.nvidia-skills-cache"
DEST="${LAB_DIR}/skills/${SKILL}"

echo "==> Fetching NVIDIA/skills catalog..."
if [ -d "${CACHE_DIR}/.git" ]; then
    git -C "${CACHE_DIR}" pull --quiet
else
    git clone --quiet --depth 1 https://github.com/NVIDIA/skills "${CACHE_DIR}"
fi

SRC="${CACHE_DIR}/skills/${SKILL}"
if [ ! -f "${SRC}/SKILL.md" ]; then
    echo "ERROR: skill '${SKILL}' not found. Browse the catalog:" >&2
    echo "  ls ${CACHE_DIR}/skills/" >&2
    exit 1
fi

echo
echo "==> Skill card (read this — it records ownership, license, and risks):"
echo "------------------------------------------------------------------"
sed -e 's/<br>//g' "${SRC}/skill-card.md" | head -30
echo "------------------------------------------------------------------"

echo
echo "==> Verifying signature (skill.oms.sig, OpenSSF Model Signing)..."
if [ ! -f "${SRC}/skill.oms.sig" ]; then
    echo "ERROR: no skill.oms.sig present — refusing to install an unsigned skill." >&2
    exit 1
fi
if command -v model_signing >/dev/null 2>&1; then
    model_signing verify certificate "${SRC}" \
        --signature "${SRC}/skill.oms.sig" \
        --certificate_chain "${CACHE_DIR}/nv-agent-root-cert.pem" \
        --ignore_unsigned_files \
        && echo "✅ Signature verified against the NVIDIA root certificate."
else
    echo "⚠️  model_signing CLI not installed — signature present but unverified."
    echo "   Install it to verify cryptographically:  pip install model-signing"
    sha256sum "${SRC}/skill.oms.sig" 2>/dev/null || shasum -a 256 "${SRC}/skill.oms.sig"
fi

echo
echo "==> Installing into lab skills directory..."
rm -rf "${DEST}"
mkdir -p "${DEST}"
cp -R "${SRC}/." "${DEST}/"
echo "✅ Installed: ${DEST}"
echo
echo "The lazy loader will now index it. Try:  python harness_lab.py --exercise 4"
echo
echo "Same skill, other harnesses (the portability story):"
echo "  npx skills add nvidia/skills --skill ${SKILL} --agent claude-code"
echo "  npx skills add nvidia/skills --skill ${SKILL} --agent codex"
