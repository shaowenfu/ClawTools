#!/usr/bin/env node
/**
 * gateway_report.mjs
 *
 * Dual-mode report for Moltbot Gateway health.
 * - --json (default): machine-readable JSON
 * - --summary: one-line summary + findings
 *
 * Exit codes:
 * 0 = OK
 * 1 = WARN
 * 2 = CRIT
 */

import { execFileSync } from "node:child_process";
import { loadConfig } from "/opt/moltbot/dist/config/config.js";
import { callGateway } from "/opt/moltbot/dist/gateway/call.js";

const args = new Set(process.argv.slice(2));
const wantSummary = args.has("--summary");
const wantJson = args.has("--json") || !wantSummary;

const PORT = 18789;
const TIMEOUT_MS = 2000;

function sh(cmd, cmdArgs) {
  try {
    return execFileSync(cmd, cmdArgs, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) {
    const out = String(e?.stdout ?? "");
    const err = String(e?.stderr ?? e?.message ?? e);
    return (out + (out && err ? "\n" : "") + err).trim();
  }
}

function systemdShow(unit) {
  const raw = sh("systemctl", [
    "--user",
    "show",
    unit,
    "-p",
    "ActiveState",
    "-p",
    "SubState",
    "-p",
    "MainPID",
    "-p",
    "ActiveEnterTimestamp",
    "-p",
    "NRestarts",
    "-p",
    "ExecMainStatus",
    "-p",
    "ExecMainCode",
  ]);
  const obj = {};
  for (const line of raw.split(/\r?\n/)) {
    const idx = line.indexOf("=");
    if (idx === -1) continue;
    obj[line.slice(0, idx)] = line.slice(idx + 1);
  }
  return obj;
}

function parseLsofListeners(port) {
  const raw = sh("lsof", ["-nP", `-iTCP:${port}`, "-sTCP:LISTEN"]);
  const lines = raw.split(/\r?\n/).filter(Boolean);
  const rows = lines.filter((l) => !l.startsWith("COMMAND"));
  const listeners = rows
    .map((l) => {
      const parts = l.trim().split(/\s+/);
      return {
        command: parts[0],
        pid: Number.parseInt(parts[1], 10),
        user: parts[2],
        raw: l,
      };
    })
    .filter((r) => Number.isFinite(r.pid));
  for (const rec of listeners) {
    const m = rec.raw.match(/TCP\s+(.+)\s*\(LISTEN\)/);
    if (m) rec.address = m[1];
  }
  return listeners;
}

function levelRank(level) {
  return level === "crit" ? 2 : level === "warn" ? 1 : 0;
}

function addFinding(findings, level, code, message, data) {
  findings.push({ level, code, message, ...(data ? { data } : {}) });
}

async function main() {
  const ts = Date.now();
  const findings = [];

  const svc = systemdShow("moltbot-gateway.service");
  const active = svc.ActiveState === "active" && svc.SubState === "running";
  if (!active) {
    addFinding(findings, "crit", "systemd.inactive", "moltbot-gateway.service not active", svc);
  }

  let listeners = [];
  try {
    listeners = parseLsofListeners(PORT);
  } catch (e) {
    addFinding(findings, "warn", "listen.lsof_failed", "failed to read listeners via lsof", { error: String(e) });
  }
  const pids = Array.from(new Set(listeners.map((l) => l.pid))).sort((a, b) => a - b);
  if (listeners.length === 0) {
    addFinding(findings, "crit", "listen.none", `no listener on port ${PORT}`);
  } else if (pids.length !== 1) {
    addFinding(findings, "crit", "listen.multi_pid", `multiple PIDs listening on port ${PORT}`, {
      pids,
      sample: listeners.slice(0, 5),
    });
  }

  const cfg = loadConfig();
  const token = cfg?.gateway?.auth?.token;
  if (!token) {
    addFinding(findings, "crit", "gateway.token_missing", "missing gateway.auth.token in config");
  }

  let rpcStatus = null;
  let rpcHealth = null;
  if (token) {
    try {
      rpcStatus = await callGateway({ method: "status", timeoutMs: TIMEOUT_MS, token });
    } catch (e) {
      addFinding(findings, "crit", "rpc.status_fail", "gateway status RPC failed", { error: String(e?.message || e) });
    }

    try {
      rpcHealth = await callGateway({ method: "health", timeoutMs: TIMEOUT_MS, token });
      if (rpcHealth && rpcHealth.ok === false) {
        addFinding(findings, "warn", "rpc.health_not_ok", "gateway health returned ok=false", rpcHealth);
      }
    } catch (e) {
      addFinding(findings, "crit", "rpc.health_fail", "gateway health RPC failed", { error: String(e?.message || e) });
    }
  }

  let cronStatus = null;
  let cronList = null;
  if (token) {
    try {
      cronStatus = await callGateway({ method: "cron.status", params: {}, timeoutMs: TIMEOUT_MS, token });
      if (cronStatus?.enabled !== true) {
        addFinding(findings, "warn", "cron.disabled", "cron scheduler not enabled", cronStatus);
      }
    } catch (e) {
      addFinding(findings, "crit", "cron.status_fail", "cron.status RPC failed", { error: String(e?.message || e) });
    }

    try {
      cronList = await callGateway({ method: "cron.list", params: { includeDisabled: false }, timeoutMs: TIMEOUT_MS, token });
    } catch (e) {
      addFinding(findings, "warn", "cron.list_fail", "cron.list RPC failed", { error: String(e?.message || e) });
    }
  }

  let overall = "ok";
  for (const f of findings) {
    if (levelRank(f.level) > levelRank(overall)) overall = f.level;
  }

  const report = {
    ts,
    iso: new Date(ts).toISOString(),
    overall,
    port: PORT,
    systemd: {
      active,
      activeState: svc.ActiveState,
      subState: svc.SubState,
      mainPid: Number.parseInt(svc.MainPID || "0", 10) || null,
      since: svc.ActiveEnterTimestamp || null,
      restarts: Number.parseInt(svc.NRestarts || "0", 10) || 0,
      execMainStatus: svc.ExecMainStatus || null,
      execMainCode: svc.ExecMainCode || null,
    },
    listen: {
      uniquePids: pids,
      listeners: listeners.slice(0, 10),
    },
    rpc: {
      status: rpcStatus,
      health: rpcHealth,
    },
    cron: {
      status: cronStatus,
      enabledJobs: Array.isArray(cronList?.jobs) ? cronList.jobs.length : null,
    },
    findings,
  };

  if (wantSummary) {
    const parts = [];
    parts.push(`overall=${overall}`);
    parts.push(`pid=${report.systemd.mainPid ?? "?"}`);
    parts.push(`restarts=${report.systemd.restarts}`);
    parts.push(`listenPids=${pids.length ? pids.join(",") : "none"}`);
    const linked = report.rpc.status?.linkChannel?.linked;
    if (linked !== undefined) parts.push(`whatsapp_linked=${linked}`);
    const dur = report.rpc.health?.durationMs;
    if (typeof dur === "number") parts.push(`healthMs=${dur}`);
    const jobs = report.cron.enabledJobs;
    if (typeof jobs === "number") parts.push(`cronJobs=${jobs}`);
    console.log(parts.join("  "));
    if (findings.length) {
      for (const f of findings) console.log(`- ${f.level.toUpperCase()} ${f.code}: ${f.message}`);
    }
  }

  if (wantJson) {
    if (wantSummary) console.log("\nJSON:");
    console.log(JSON.stringify(report, null, 2));
  }

  process.exit(overall === "crit" ? 2 : overall === "warn" ? 1 : 0);
}

await main();
