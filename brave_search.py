#!/usr/bin/env python3
import os
import sys
import json
import argparse
from time import sleep
from pathlib import Path

import requests

API_URL = "https://api.search.brave.com/res/v1/web/search"
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # 2s, 4s, 8s...

CREDS_PATHS = [
    Path(os.path.expanduser("~/.config/brave_search/credentials.json")),
    Path("/home/admin/.config/brave_search/credentials.json"),
]


def _load_credentials_file():
    for p in CREDS_PATHS:
        try:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def _get_keys():
    """Return (paid_key, free_key) without ever printing them."""
    creds = _load_credentials_file()

    paid = (
        os.environ.get("BRAVE_API_KEY_PAID")
        or creds.get("api_key_paid")
        or creds.get("paid")
        or creds.get("BRAVE_API_KEY_PAID")
    )

    # Back-compat: BRAVE_API_KEY historically held the (free) key
    free = (
        os.environ.get("BRAVE_API_KEY_FREE")
        or creds.get("api_key_free")
        or creds.get("free")
        or os.environ.get("BRAVE_API_KEY")
    )

    return paid, free


def _search_with_key(query: str, count: int, api_key: str):
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }

    params = {"q": query, "count": count}

    retry_count = 0
    while retry_count <= MAX_RETRIES:
        try:
            resp = requests.get(API_URL, headers=headers, params=params, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in (data.get("web", {}) or {}).get("results", []) or []:
                    results.append(
                        {
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "description": item.get("description"),
                            "age": item.get("age", ""),
                        }
                    )
                return {"success": True, "query": query, "results": results}, None

            # key-level failures: let caller try fallback key
            if resp.status_code in (401, 403):
                return None, {"kind": "auth", "status": resp.status_code}

            if resp.status_code == 429:
                # we still do a short backoff a few times; if it persists, caller may try fallback key
                wait_time = (BACKOFF_FACTOR**retry_count) + 1
                sys.stderr.write(f"Rate limited (429). Retrying in {wait_time}s...\n")
                sleep(wait_time)
                retry_count += 1
                continue

            # 5xx: retry with backoff
            if resp.status_code >= 500:
                wait_time = BACKOFF_FACTOR**retry_count
                sys.stderr.write(f"API Error {resp.status_code}. Retrying in {wait_time}s...\n")
                sleep(wait_time)
                retry_count += 1
                continue

            # other non-retriable errors
            sys.stderr.write(f"API Error {resp.status_code}: {resp.text[:200]}\n")
            return None, {"kind": "api", "status": resp.status_code}

        except Exception as e:
            sys.stderr.write(f"Request failed: {e}\n")
            sleep(1)
            retry_count += 1

    return None, {"kind": "rate_or_api", "status": 429}


def search(query: str, count: int = 10):
    paid, free = _get_keys()

    if not paid and not free:
        print(json.dumps({"success": False, "error": "Missing Brave API key(s)", "downgrade": True}))
        return

    attempts = []

    if paid:
        attempts.append(("paid", paid))
    if free:
        attempts.append(("free", free))

    last_err = None
    for tier, key in attempts:
        data, err = _search_with_key(query, count, key)
        if data:
            data["tier"] = tier
            print(json.dumps(data, ensure_ascii=False))
            return

        last_err = err
        # If we got here: try next key (fallback)

    print(
        json.dumps(
            {
                "success": False,
                "query": query,
                "error": "Brave Search failed after trying all keys",
                "last_error": last_err,
                "downgrade": True,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brave Search (paid-first, free-fallback) with Retry/Backoff")
    parser.add_argument("queries", nargs="+", help="Search query (or queries)")
    parser.add_argument("--count", type=int, default=10, help="Number of results")
    args = parser.parse_args()

    for q in args.queries:
        search(q, args.count)
