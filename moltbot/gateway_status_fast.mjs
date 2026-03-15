#!/usr/bin/env node
/**
 * gateway_status_fast.mjs
 *
 * Fast Moltbot Gateway RPC probe that bypasses the heavy `moltbot status` CLI path.
 *
 * Requirements:
 * - Moltbot installed on the machine (expects /opt/moltbot/dist/* to exist)
 * - Local gateway running (default ws://127.0.0.1:18789)
 *
 * Usage:
 *   node moltbot/gateway_status_fast.mjs [status|health] [timeoutMs]
 */

import { loadConfig } from "/opt/moltbot/dist/config/config.js";
import { callGateway } from "/opt/moltbot/dist/gateway/call.js";

const method = process.argv[2] || "status";
const timeoutMs = Number.parseInt(process.argv[3] || "2000", 10);

const cfg = loadConfig();
const token = cfg?.gateway?.auth?.token;

if (!token) {
  console.error("ERR: missing gateway.auth.token in config");
  process.exit(2);
}

try {
  const res = await callGateway({ method, timeoutMs, token });
  process.stdout.write(JSON.stringify(res, null, 2));
  process.stdout.write("\n");
} catch (e) {
  console.error(String(e?.message || e));
  process.exit(1);
}
