#!/usr/bin/env bash
# Local child command. Use the same installation bindings as start.sh.
set -euo pipefail
umask 077
: "${GLADOS_BRIDGE_WORKSPACE:?set the coordination Git root}"
: "${GLADOS_BRIDGE_PROFILE:?set the YAML local profile path}"
: "${GLADOS_BRIDGE_WRAPPER:?set the profile-resolved command wrapper}"
: "${GLADOS_BRIDGE_PYTHON:?set the profile-resolved interpreter}"
: "${GLADOS_BRIDGE_STATE:?set the existing private bridge state directory}"
: "${GLADOS_BRIDGE_CODEX:?set the installation CLI executable}"
if [[ $# != 2 || ( $1 != submit && $1 != status ) ]]; then
  echo 'usage: manual.sh {submit|status} REQUEST_ID' >&2
  exit 2
fi
bridge_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
action=--prompt-file
if [[ $1 == status ]]; then action=--task-status; fi
unset CONTROL_PLANE_API_KEY OPENAI_API_KEY CODEX_API_KEY
export PYTHONDONTWRITEBYTECODE=1
"$GLADOS_BRIDGE_WRAPPER" "$GLADOS_BRIDGE_PYTHON" -s -B "$bridge_dir/bridge.py" \
  --workspace "$GLADOS_BRIDGE_WORKSPACE" --governed-profile "$GLADOS_BRIDGE_PROFILE" \
  --command-wrapper "$GLADOS_BRIDGE_WRAPPER" --state "$GLADOS_BRIDGE_STATE" \
  --codex "$GLADOS_BRIDGE_CODEX" --rpc "$action" "$2"
