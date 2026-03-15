# Moltbot Gateway Fast Probes (ClawTools)

These tools are for **ops / self-hosted Moltbot** environments where the official `moltbot status` / `moltbot gateway health` commands may be **slow on cold start** (e.g., ~13s) and can be killed by external watchdog timeouts.

They bypass the heavy CLI path and call Gateway RPC directly.

## Requirements

- Moltbot installed on the machine (expects `/opt/moltbot/dist/*` to exist)
- A local Gateway running (default loopback port `18789`)
- `lsof` installed (for listener diagnostics)

## Tools

### 1) `moltbot/gateway_report.sh`

Dual-mode report:

- JSON (default):
  ```bash
  ./moltbot/gateway_report.sh --json
  ```
- Short summary:
  ```bash
  ./moltbot/gateway_report.sh --summary
  ```

Exit codes:
- `0` OK
- `1` WARN
- `2` CRIT

### 2) `moltbot/gateway_status_fast.mjs`

Fast RPC probe:

```bash
node moltbot/gateway_status_fast.mjs status 2000
node moltbot/gateway_status_fast.mjs health 2000
```

### 3) `moltbot/cron_fast.mjs`

Fast cron RPC client:

```bash
node moltbot/cron_fast.mjs status 2000
node moltbot/cron_fast.mjs list false 2000
node moltbot/cron_fast.mjs runs <jobId> 2000
node moltbot/cron_fast.mjs run <jobId> now 2000
```

### 4) `moltbot/gateway_watchdog.sh`

Minimal wrapper suitable for cron:

```bash
*/10 * * * * /path/to/ClawTools/moltbot/gateway_watchdog.sh
```

## Why this exists

In some VPS environments, `moltbot gateway health` can take ~13 seconds due to CLI cold start costs (module loading, plugin registry init, GC). The Gateway RPC itself is fast.

These scripts keep ops observability fast and reliable.
