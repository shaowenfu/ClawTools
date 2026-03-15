#!/usr/bin/env node
/**
 * cron_fast.mjs
 *
 * Fast Cron RPC client (cron.list/status/runs/run) that bypasses the heavy CLI.
 *
 * Usage:
 *   node moltbot/cron_fast.mjs list [includeDisabled] [timeoutMs]
 *   node moltbot/cron_fast.mjs status [timeoutMs]
 *   node moltbot/cron_fast.mjs runs <jobId> [timeoutMs]
 *   node moltbot/cron_fast.mjs run <jobId> [mode=now|next-heartbeat] [timeoutMs]
 */

import { loadConfig } from "/opt/moltbot/dist/config/config.js";
import { callGateway } from "/opt/moltbot/dist/gateway/call.js";

const cmd = process.argv[2];
const arg1 = process.argv[3];
const arg2 = process.argv[4];
const arg3 = process.argv[5];

function toBool(v) {
  if (v == null) return undefined;
  const s = String(v).toLowerCase().trim();
  if (["1", "true", "yes", "y"].includes(s)) return true;
  if (["0", "false", "no", "n"].includes(s)) return false;
  return undefined;
}

function toInt(v, def) {
  const n = Number.parseInt(String(v ?? ""), 10);
  return Number.isFinite(n) && n > 0 ? n : def;
}

const cfg = loadConfig();
const token = cfg?.gateway?.auth?.token;
if (!token) {
  console.error("ERR: missing gateway.auth.token in config");
  process.exit(2);
}

let method;
let params;
let timeoutMs = 2000;

if (cmd === "list") {
  method = "cron.list";
  const includeDisabled = toBool(arg1);
  timeoutMs = toInt(arg2, 2000);
  params = includeDisabled === undefined ? {} : { includeDisabled };
} else if (cmd === "status") {
  method = "cron.status";
  timeoutMs = toInt(arg1, 2000);
  params = {};
} else if (cmd === "runs") {
  if (!arg1) {
    console.error("Usage: runs <jobId> [timeoutMs]");
    process.exit(2);
  }
  method = "cron.runs";
  timeoutMs = toInt(arg2, 2000);
  params = { id: String(arg1) };
} else if (cmd === "run") {
  if (!arg1) {
    console.error("Usage: run <jobId> [mode=now|next-heartbeat] [timeoutMs]");
    process.exit(2);
  }
  method = "cron.run";
  const mode = arg2 && ["now", "next-heartbeat"].includes(String(arg2)) ? String(arg2) : "now";
  timeoutMs = toInt(arg3, 2000);
  params = { id: String(arg1), mode };
} else {
  console.error("Commands: list | status | runs | run");
  process.exit(2);
}

try {
  const res = await callGateway({ method, params, timeoutMs, token });
  process.stdout.write(JSON.stringify(res, null, 2));
  process.stdout.write("\n");
} catch (e) {
  console.error(String(e?.message || e));
  process.exit(1);
}
