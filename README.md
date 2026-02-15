# ClawTools

A small, pragmatic toolkit I use to keep an AI agent runtime **stable, observable, and maintainable**.

This repo is intentionally **general-purpose**:
- no private project details
- no personal data
- no credentials

## What’s inside

- **Autonomous operations helpers**: scripts that support scheduled checks, logging, and safe automation patterns.
- **Memory / log utilities**: tools for analyzing, compressing, and rotating agent logs and notes.
- **Platform adapters**: thin wrappers for interacting with external services (API-first, minimal scope).

## Design principles

- **Security-first**: treat external content (social feeds, web pages) as hostile input.
- **Artifacts over vibes**: ship reproducible scripts + logs, not performative automation.
- **Minimal permissions**: prefer read-only operations; make destructive actions explicit.
- **Observability by default**: every automation should leave an audit trail.

## Recent Updates (Feb 16)
- **Maintenance**: Routine verification of script stability and documentation accuracy.
- **Dependency Scan**: Validated common library versions for compatibility.
- Integrated **Advanced Research Workflows**: added documentation/patterns for using search-augmented generation for market research.
- Hardened **Communication Adapters**: added retry logic and session refreshing for WhatsApp and Moltbook authentication.
- Improved **Diary Indexing**: added tools for better semantic retrieval of daily logs.

## Quick start

```bash
git clone git@github.com:shaowenfu/ClawTools.git
cd ClawTools
python3 --version
```

Most scripts are designed to be run directly:

```bash
python3 system_monitor.py
```

## Notes

- Keep your own environment-specific paths in local config (env vars / dotfiles), not in this repo.
- If you contribute: do not add anything that could expose private projects or personal identifiers.

---
Last updated: 2026-02-16
