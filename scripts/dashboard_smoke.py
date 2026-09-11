"""Production-only smoke for the deployed Hermes dashboard auth boundary.

This intentionally uses plain HTTPS rather than ``modal run``. A Modal local
entrypoint creates temporary ``-dev.modal.run`` web functions, which is the
wrong object to validate after a production deployment.

This smoke proves the local Hermes auth wiring and fail-closed gate. It cannot
prove that Nous Portal has provisioned the configured OAuth client; only a real
Portal authorization round trip can prove that external registration.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from runtime_versions import (
    HERMES_DASHBOARD_OAUTH_CLIENT_ID,
    HERMES_DASHBOARD_PUBLIC_URL,
)

# Modal's web_server startup_timeout is 180 seconds. A scale-to-zero dashboard
# may legitimately spend most of that budget starting its larger Hermes/UI
# image, so the external smoke must not impose a shorter contradictory timeout.
_REQUEST_TIMEOUT_SECONDS = 210
_REDIRECT_STATUSES = {302, 303, 307, 308}
_NOUS_PORTAL_AUTHORITY = "portal.nousresearch.com"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _get(path: str) -> tuple[int, str | None, bytes]:
    root = HERMES_DASHBOARD_PUBLIC_URL.rstrip("/")
    request = urllib.request.Request(
        f"{root}{path}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            return response.status, response.headers.get("Location"), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location"), exc.read()


def _same_origin_login(location: str | None) -> bool:
    if not location:
        return False
    root = urllib.parse.urlparse(HERMES_DASHBOARD_PUBLIC_URL)
    target = urllib.parse.urlparse(
        urllib.parse.urljoin(HERMES_DASHBOARD_PUBLIC_URL, location)
    )
    return (
        target.scheme == root.scheme
        and target.netloc == root.netloc
        and target.path == "/login"
    )


def _valid_nous_authorize_redirect(location: str | None) -> bool:
    if not location:
        return False
    target = urllib.parse.urlparse(location)
    if (
        target.scheme != "https"
        or target.netloc != _NOUS_PORTAL_AUTHORITY
        or target.path != "/oauth/authorize"
    ):
        return False

    query = urllib.parse.parse_qs(target.query)
    expected_callback = (
        f"{HERMES_DASHBOARD_PUBLIC_URL.rstrip('/')}/auth/callback"
    )
    return (
        query.get("client_id") == [HERMES_DASHBOARD_OAUTH_CLIENT_ID]
        and query.get("redirect_uri") == [expected_callback]
    )


def main() -> None:
    # This proves that Hermes has activated the Nous auth provider locally.
    # It does NOT prove that Nous Portal recognizes/provisioned the client id.
    providers_status, _, providers_body = _get("/api/auth/providers")
    if providers_status != 200:
        raise RuntimeError(
            f"Hermes auth-provider bootstrap returned HTTP {providers_status}"
        )
    try:
        providers_payload = json.loads(providers_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Hermes auth-provider bootstrap returned invalid JSON"
        ) from exc

    providers = providers_payload.get("providers")
    if not isinstance(providers, list) or not any(
        isinstance(provider, dict) and provider.get("name") == "nous"
        for provider in providers
    ):
        raise RuntimeError("Hermes Nous OAuth provider is not active")

    # Prove that the browser login start is wired to the expected Portal,
    # configured client id, and exact public callback without following the
    # external redirect. Portal-side provisioning remains an external check.
    oauth_status, oauth_location, _ = _get("/auth/login?provider=nous")
    if (
        oauth_status not in _REDIRECT_STATUSES
        or not _valid_nous_authorize_redirect(oauth_location)
    ):
        raise RuntimeError(
            "Hermes Nous OAuth start did not produce the expected Portal "
            f"authorization request: HTTP {oauth_status}, location={oauth_location!r}"
        )

    # Prove the gate itself is engaged without ever following an OAuth/login
    # redirect. Hermes versions may represent an unauthenticated API request as
    # 401 or as a same-origin redirect to /login; either is fail-closed.
    gated_status, location, _ = _get("/api/sessions")
    gated = gated_status == 401 or (
        gated_status in _REDIRECT_STATUSES and _same_origin_login(location)
    )
    if not gated:
        raise RuntimeError(
            "Hermes dashboard auth gate did not reject anonymous sessions "
            f"access: HTTP {gated_status}"
        )

    print(
        json.dumps(
            {
                "dashboard": HERMES_DASHBOARD_PUBLIC_URL,
                "auth_provider": "nous",
                "anonymous_sessions_status": gated_status,
                "oauth_request_status": "READY",
                "portal_provisioning": "UNVERIFIED",
                "status": "LOCAL_AUTH_BOUNDARY_OK",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
