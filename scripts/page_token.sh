#!/usr/bin/env bash
# Prints a Page access token for page $1.
# If FB_SYSTEM_TOKEN is set (a never-expiring System User token from Meta Business Suite),
# the Page token is fetched with it on every run. Otherwise the fallback token in $2 is used.
set -euo pipefail
page="$1"; fallback="${2:-}"
ver="${GRAPH_VERSION:-v23.0}"
if [ -n "${FB_SYSTEM_TOKEN:-}" ]; then
  res=$(curl -sS --connect-timeout 20 --max-time 60 -G "https://graph.facebook.com/${ver}/${page}" \
        -d "fields=access_token" -d "access_token=${FB_SYSTEM_TOKEN}")
  tok=$(printf '%s' "$res" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null || true)
  if [ -n "$tok" ]; then echo "::add-mask::${tok}" >&2; printf '%s' "$tok"; exit 0; fi
  msg=$(printf '%s' "$res" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("error",{}).get("message","unknown"))' 2>/dev/null || echo unknown)
  echo "::warning::system token could not get the page token (${msg}); trying the saved page token" >&2
fi
printf '%s' "$fallback"
