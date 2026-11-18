#!/usr/bin/env bash
# Local stdio adapter only. Tunnel/service lifecycle belongs to the site operator.
set -euo pipefail
umask 077
: "${GLADOS_BRIDGE_WORKSPACE:?set the coordination Git root}"
: "${GLADOS_BRIDGE_PROFILE:?set the YAML local profile path}"
: "${GLADOS_BRIDGE_WRAPPER:?set the profile-resolved command wrapper}"
: "${GLADOS_BRIDGE_PYTHON:?set the profile-resolved interpreter}"
: "${GLADOS_BRIDGE_STATE:?set the existing private bridge state directory}"
bridge_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
unset GLADOS_BRIDGE_PROMPT GLADOS_BRIDGE_INBOX
export PYTHONDONTWRITEBYTECODE=1
exec node "$bridge_dir/server.mjs"
