"""Thin Python client for the HTPBE PDF tamper/forgery detection API.

Docs: https://htpbe.tech/api
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

DEFAULT_BASE_URL = "https://api.htpbe.tech/v1"


class HtpbeError(Exception):
    """Base class for all client errors."""


class HtpbeAPIError(HtpbeError):
    """Raised when the API returns a non-2xx response.

    Attributes:
        status: HTTP status code.
        code: machine-readable error code from the API (e.g. "not_found"), if any.
        message: human-readable error message.
    """

    def __init__(self, status: int, code: Optional[str], message: str) -> None:
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"[{status}{f'/{code}' if code else ''}] {message}")


class Client:
    """Client for the HTPBE API.

    Two-step flow: :meth:`analyze` returns a check id, then :meth:`get_result`
    fetches the verdict. :meth:`analyze_and_wait` does both in one call.

    Example:
        >>> from htpbe import Client
        >>> client = Client(api_key="htpbe_live_...")
        >>> result = client.analyze_and_wait("https://example.com/invoice.pdf")
        >>> result["status"]          # "intact" | "modified" | "inconclusive"
        >>> result["modification_markers"]  # e.g. ["HTPBE_POST_SIGNATURE_EDIT"]
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    # -- internals ---------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.request(
                method, url, headers=self._headers(), timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:  # network/timeout
            raise HtpbeError(f"request to {url} failed: {exc}") from exc

        if resp.status_code >= 400:
            code, message = None, resp.text or resp.reason
            try:
                body = resp.json()
                code = body.get("code")
                message = body.get("error") or body.get("message") or message
            except ValueError:
                pass
            raise HtpbeAPIError(resp.status_code, code, message)

        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # -- public API --------------------------------------------------------

    def analyze(self, url: str, original_filename: Optional[str] = None) -> str:
        """Submit a publicly accessible PDF URL for analysis.

        Returns the check id (a UUID). Use :meth:`get_result` to fetch the verdict.
        """
        payload: Dict[str, Any] = {"url": url}
        if original_filename:
            payload["original_filename"] = original_filename
        data = self._request("POST", "/analyze", json=payload)
        check_id = data.get("id")
        if not check_id:
            raise HtpbeError(f"analyze response missing 'id': {data!r}")
        return check_id

    def get_result(self, check_id: str) -> Dict[str, Any]:
        """Fetch the full analysis result for a check id."""
        return self._request("GET", f"/result/{check_id}")

    def analyze_and_wait(
        self,
        url: str,
        original_filename: Optional[str] = None,
        poll_interval: float = 1.0,
        max_wait: float = 30.0,
    ) -> Dict[str, Any]:
        """Analyze a PDF and return its result in one call.

        Analysis is synchronous, so the result is normally ready immediately;
        this retries briefly on a transient 404 (read-after-write lag).
        """
        check_id = self.analyze(url, original_filename)
        deadline = time.monotonic() + max_wait
        while True:
            try:
                return self.get_result(check_id)
            except HtpbeAPIError as exc:
                if exc.status == 404 and time.monotonic() < deadline:
                    time.sleep(poll_interval)
                    continue
                raise

    def list_checks(
        self,
        limit: int = 100,
        page: Optional[int] = None,
        tool: Optional[str] = None,
        creator: Optional[str] = None,
        producer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List your checks (paginated, most recent first)."""
        params: Dict[str, Any] = {"limit": limit}
        if page is not None:
            params["page"] = page
        if tool:
            params["tool"] = tool
        if creator:
            params["creator"] = creator
        if producer:
            params["producer"] = producer
        return self._request("GET", "/checks", params=params)
