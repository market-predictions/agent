"""Idempotent first-deploy bootstrap for Modal runtime secrets.

The GitHub deployment token is the only external prerequisite. On the first
run this script creates one Modal proxy token plus the two named runtime
Secrets required by ``modal_app.py``. Subsequent runs preserve the existing
Secrets and create nothing.

Secret values are generated in-process and are never printed.
"""

from __future__ import annotations

import secrets

import modal

from runtime_versions import MODAL_FREELLMAPI_SECRET, MODAL_HERMES_SECRET


def main() -> int:
    existing = {secret.name for secret in modal.Secret.objects.list()}
    required = {MODAL_HERMES_SECRET, MODAL_FREELLMAPI_SECRET}
    present = existing & required

    if present == required:
        print("Modal runtime secrets already exist; bootstrap skipped.")
        return 0

    if present:
        missing = ", ".join(sorted(required - present))
        raise RuntimeError(
            "Refusing partial Modal runtime-secret state; missing: " + missing
        )

    freellmapi_key = "freellmapi-" + secrets.token_urlsafe(24)
    encryption_key = secrets.token_hex(32)

    workspace = modal.Workspace.from_context()
    proxy_token = workspace.proxy_tokens.create()
    created_secret_names: list[str] = []

    try:
        modal.Secret.objects.create(
            MODAL_HERMES_SECRET,
            {
                "FREELLMAPI_API_KEY": freellmapi_key,
                "MODAL_PROXY_KEY": proxy_token.token_id,
                "MODAL_PROXY_SECRET": proxy_token.token_secret,
            },
        )
        created_secret_names.append(MODAL_HERMES_SECRET)

        modal.Secret.objects.create(
            MODAL_FREELLMAPI_SECRET,
            {"ENCRYPTION_KEY": encryption_key},
        )
        created_secret_names.append(MODAL_FREELLMAPI_SECRET)
    except Exception:
        for name in reversed(created_secret_names):
            modal.Secret.objects.delete(name, allow_missing=True)
        workspace.proxy_tokens.delete(proxy_token.token_id)
        raise

    print("Created Modal runtime secrets and one protected endpoint proxy token.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
