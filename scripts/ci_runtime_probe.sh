#!/usr/bin/env bash
set -euo pipefail

IMAGE="$(python -c 'import runtime_versions; print(runtime_versions.FREELLMAPI_IMAGE)')"
CONTAINER=agent-freeapi-ci
export ENCRYPTION_KEY="$(printf 'a%.0s' $(seq 1 64))"
export FREELLMAPI_API_KEY="freellmapi-ci-${GITHUB_RUN_ID:-local}"
export MODAL_PROXY_KEY="ci-local-key"
export MODAL_PROXY_SECRET="ci-local-secret"
# The disposable Hermes user plugin imports the canonical policy module from
# this repository. Make that module path explicit for the child `hermes`
# process instead of relying on console-script sys.path behavior.
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
report_failure() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "runtime probe failed with exit code $rc"
    echo "--- FreeLLMAPI log tail ---"
    docker logs --tail 160 "$CONTAINER" 2>&1 || true
    echo "--- model response ---"
    cat /tmp/model.json 2>/dev/null || true
    echo
    echo "--- Hermes result ---"
    cat /tmp/hermes-result.json 2>/dev/null || true
  fi
  cleanup
  exit "$rc"
}
trap report_failure EXIT

# One ephemeral pinned FreeLLMAPI instance is shared by the direct model probe
# and Hermes proof. This mirrors the Phase-1 runtime without adding state.
docker run --rm -d \
  --name "$CONTAINER" \
  -p 3001:3001 \
  -e ENCRYPTION_KEY \
  -e FREELLMAPI_API_KEY \
  -e FREEAPI_CONFIG_PATH=/app/agent-freellmapi-default.json \
  -v "$PWD/runtime/freellmapi-bootstrap.mjs:/app/agent-freellmapi-bootstrap.mjs:ro" \
  -v "$PWD/runtime/freellmapi.default.json:/app/agent-freellmapi-default.json:ro" \
  "$IMAGE" \
  sh -lc 'node /app/agent-freellmapi-bootstrap.mjs >/dev/null && exec node server/dist/index.js'

ready=false
for attempt in $(seq 1 45); do
  if curl --fail --silent http://127.0.0.1:3001/api/ping >/dev/null; then
    ready=true
    break
  fi
  if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "FreeLLMAPI container exited before readiness"
    exit 1
  fi
  sleep 1
done
[ "$ready" = true ] || { echo "FreeLLMAPI did not become ready"; exit 1; }

echo "FreeLLMAPI ready"
unauth_status="$(curl --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:3001/v1/models)"
[ "$unauth_status" = 401 ] || { echo "expected unauthenticated /v1/models=401, got $unauth_status"; exit 1; }

curl --fail --silent \
  -H "Authorization: Bearer $FREELLMAPI_API_KEY" \
  http://127.0.0.1:3001/v1/models > /tmp/models.json
curl --fail --silent \
  -H "Authorization: Bearer $FREELLMAPI_API_KEY" \
  http://127.0.0.1:3001/v1/providers > /tmp/providers.json

python - <<'PY'
import json
from pathlib import Path
models = json.loads(Path('/tmp/models.json').read_text())
providers = json.loads(Path('/tmp/providers.json').read_text())
assert models['object'] == 'list'
assert any(item.get('id') == 'auto' for item in models['data'])
summary = []
for item in providers.get('providers', []):
    summary.append({k: item.get(k) for k in ('platform', 'name', 'configured', 'enabled', 'status') if k in item})
print('provider summary:', json.dumps(summary, sort_keys=True))
print('model count:', len(models['data']))
PY

model_status="$(curl --silent --show-error --max-time 180 \
  --output /tmp/model.json \
  --dump-header /tmp/model-headers.txt \
  --write-out '%{http_code}' \
  -H "Authorization: Bearer $FREELLMAPI_API_KEY" \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:3001/v1/chat/completions \
  -d '{"model":"auto","messages":[{"role":"user","content":"Reply with one short sentence confirming you can answer."}],"max_tokens":64,"stream":false}')"

if [ "$model_status" != 200 ]; then
  echo "FreeLLMAPI model request returned HTTP $model_status"
  exit 1
fi

python - <<'PY'
import json
from pathlib import Path
body = json.loads(Path('/tmp/model.json').read_text())
text = body['choices'][0]['message'].get('content') or ''
assert text.strip(), body
headers = Path('/tmp/model-headers.txt').read_text().lower()
assert 'x-routed-via:' in headers, headers
print('direct model route: OK')
PY

python agent_carrier.py \
  --execute \
  --task-id ci-real-hermes \
  --objective "Find one public technical fact about HTTP semantics and cite the public source you looked up." \
  --freellmapi-base-url http://127.0.0.1:3001/v1 \
  > /tmp/hermes-result.json

python - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('/tmp/hermes-result.json').read_text())
assert result['status'] == 'CANDIDATE', result
assert result['result']['claims'], result
print('Hermes -> FreeLLMAPI -> model -> web: OK')
PY
