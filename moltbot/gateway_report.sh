#!/usr/bin/env bash
set -euo pipefail

# Wrapper around gateway_report.mjs
#
# Usage:
#   ./moltbot/gateway_report.sh           # JSON (default)
#   ./moltbot/gateway_report.sh --json    # JSON
#   ./moltbot/gateway_report.sh --summary # short summary

DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
node "$DIR/gateway_report.mjs" "$@"
