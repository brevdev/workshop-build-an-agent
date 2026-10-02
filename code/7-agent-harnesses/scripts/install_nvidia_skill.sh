#!/usr/bin/env bash
# Install an NVIDIA Verified Skill into the lab skills directory —
# verifying its signature and showing its skill card BEFORE trusting it.
#
# Usage: bash install_nvidia_skill.sh [skill-name]
set -euo pipefail

SKILL="${1:-accelerated-computing-cudf}"
if [[ ! "$SKILL" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || (( ${#SKILL} > 64 )); then
    echo "ERROR: use a skill name with lowercase letters, numbers, and single hyphens." >&2
    exit 1
fi
if ! command -v model_signing >/dev/null 2>&1; then
    echo "ERROR: install model-signing before installing a verified skill." >&2
    exit 1
fi
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
sed -n '1,30{s/<br>//g;p;}' "${SRC}/skill-card.md"
echo "------------------------------------------------------------------"

echo
echo "==> Verifying signature (skill.oms.sig, OpenSSF Model Signing)..."
if [ ! -f "${SRC}/skill.oms.sig" ]; then
    echo "ERROR: no skill.oms.sig present — refusing to install an unsigned skill." >&2
    exit 1
fi
mkdir -p "${LAB_DIR}/skills"
STAGE="$(mktemp -d "${LAB_DIR}/skills/.verify-XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
cp -R "${SRC}/." "${STAGE}/"
# Verify the staged copy, excluding the signature artifact. The verifier also
# honors the signed manifest's metadata exclusions; other unsigned files fail.
if ! model_signing verify certificate "${STAGE}" \
    --signature "${STAGE}/skill.oms.sig" \
    --certificate_chain "${CACHE_DIR}/nv-agent-root-cert.pem" \
    --ignore-paths skill.oms.sig; then
    echo "ERROR: verification failed. The installed skill has not been changed." >&2
    exit 1
fi
echo "✅ Signature verified against the NVIDIA root certificate."

# Keep an existing installation until its verified replacement is ready.
BACKUP="${STAGE}.previous"
if [ -e "${DEST}" ] || [ -L "${DEST}" ]; then
    mv "${DEST}" "${BACKUP}"
fi
if ! mv "${STAGE}" "${DEST}"; then
    if [ -e "${BACKUP}" ] || [ -L "${BACKUP}" ]; then mv "${BACKUP}" "${DEST}"; fi
    exit 1
fi
rm -rf "${BACKUP}"
echo "✅ Installed: ${DEST}"
echo
echo "The lazy loader will now index it. Try:  python harness_lab.py --exercise 4"
echo
echo "Copy the complete verified folder to a compatible harness (Hermes example):"
echo '  mkdir -p "${HERMES_HOME:-$HOME/.hermes}/skills"'
printf '  cp -R %q "${HERMES_HOME:-$HOME/.hermes}/skills/"\n' "${DEST}"
echo "Keep the references, scripts and signature together with SKILL.md."
