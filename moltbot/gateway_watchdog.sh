#!/usr/bin/env bash
set -euo pipefail

# gateway_watchdog.sh
#
# A tiny watchdog wrapper that fails non-zero on WARN/CRIT.
# Intended for cron/systemd timers.

DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

# summary to stdout
"$DIR/gateway_report.sh" --summary
# json + exit code (0 ok, 1 warn, 2 crit)
"$DIR/gateway_report.sh" --json >/dev/null
