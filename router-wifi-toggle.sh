#!/bin/bash
set -euo pipefail

ROUTER="http://192.168.1.254"
USER="meo"
PASS="meo"
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT

# --- Login ---
# The router uses HTTP Basic Auth: GET /index.html with Authorization header.
# The server responds with Set-Cookie: SESSIONID=...
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -c "$COOKIE_JAR" \
  -H "Authorization: Basic $(echo -n "$USER:$PASS" | base64)" \
  "$ROUTER/index.html" \
  --insecure)

SESSION_ID=$(awk '/SESSIONID/{print $NF}' "$COOKIE_JAR")

if [[ -z "$SESSION_ID" ]]; then
  echo "Login failed (HTTP $HTTP_CODE) — no SESSIONID cookie received." >&2
  exit 1
fi

echo "Logged in. Session: $SESSION_ID"

# --- Toggle Wi-Fi ---
# Change "enableWifi" to "1" to re-enable, "0" to disable.
ENABLE="${1:-0}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  "$ROUTER/locallmngt.cmd?request=/generic-wifi" \
  -X PUT \
  -H "Accept: application/json, text/plain, */*" \
  -H "Accept-Language: pt-PT" \
  -H "Cache-Control: no-cache" \
  -H "Connection: keep-alive" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Cookie: SESSIONID=$SESSION_ID" \
  -H "Origin: $ROUTER" \
  -H "Pragma: no-cache" \
  -H "Referer: $ROUTER/index.html" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" \
  --data-raw "{\"version\":\"1.0\",\"enableWifi\":\"$ENABLE\"}" \
  --compressed \
  --insecure)

BODY=$(sed '$d' <<< "$RESPONSE")
HTTP_CODE=$(tail -1 <<< "$RESPONSE")

echo "Response ($HTTP_CODE): $BODY"

if [[ "$HTTP_CODE" =~ ^2 ]]; then
  echo "Wi-Fi $([ "$ENABLE" = "1" ] && echo "enabled" || echo "disabled") successfully."
else
  echo "Request failed with HTTP $HTTP_CODE." >&2
  exit 1
fi
