#!/bin/bash
set -euo pipefail

ROUTER="http://192.168.1.254"
USER="meo"
PASS="meo"
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT

# --- Login ---
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

# --- Toggle Mesh ---
ACTION="${1:-}"
if [[ "$ACTION" != "enable" && "$ACTION" != "disable" ]]; then
  echo "Usage: $0 <enable|disable>" >&2
  exit 1
fi

[[ "$ACTION" == "enable" ]] && MESH="1" || MESH="0"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  "$ROUTER/locallmngt.cmd?request=/settings" \
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
  --data-raw "{\"version\":\"1.0\",\"smartMesh\":\"$MESH\"}" \
  --compressed \
  --insecure) || CURL_EXIT=$?

# Exit code 52 = empty reply: router likely restarted to apply the change
if [[ "${CURL_EXIT:-0}" -eq 52 ]]; then
  echo "Mesh ${ACTION}d — router restarted to apply the change."
  exit 0
fi

BODY=$(sed '$d' <<< "$RESPONSE")
HTTP_CODE=$(tail -1 <<< "$RESPONSE")

echo "Response ($HTTP_CODE): $BODY"

if [[ "$HTTP_CODE" =~ ^2 ]]; then
  echo "Mesh ${ACTION}d successfully."
else
  echo "Request failed with HTTP $HTTP_CODE." >&2
  exit 1
fi
