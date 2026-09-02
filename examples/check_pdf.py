"""Minimal example: check whether a PDF has been modified.

    export HTPBE_API_KEY=htpbe_live_...
    python examples/check_pdf.py https://example.com/invoice.pdf

Exit codes: 0 no action needed, 1 API error, 2 usage error,
3 route to a human reviewer, 4 verify with the issuing organisation.
"""

import os
import sys

from htpbe import Client, HtpbeAPIError


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python check_pdf.py <pdf-url>", file=sys.stderr)
        return 2

    api_key = os.environ.get("HTPBE_API_KEY")
    if not api_key:
        print("set HTPBE_API_KEY", file=sys.stderr)
        return 2

    client = Client(api_key=api_key)
    try:
        result = client.analyze_and_wait(sys.argv[1])
    except HtpbeAPIError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        return 1

    status = result.get("status")
    markers = result.get("modification_markers", [])
    print(f"file:    {result.get('filename')}")
    print(f"verdict: {status}")
    if markers:
        print(f"markers: {', '.join(markers)}")

    # A structural verdict describes the file, not the person who sent it, and is
    # never safe as the sole basis for an automatic adverse decision. The API ships
    # `usage_caution.recommended_action` on every result to route the case instead
    # of auto-rejecting. Branch on it; only `no_action` is a clean pass. Anything
    # else — including a missing or unrecognised action — routes to a human.
    usage_caution = result.get("usage_caution") or {}
    action = usage_caution.get("recommended_action")
    message = usage_caution.get("message")
    if message:
        print(f"caution: {message}")

    if action == "no_action":
        return 0
    if action == "request_from_issuer":
        print("→ Verify this document directly with the issuing organisation.")
        return 4
    # route_to_human_review, or anything unexpected: fail safe to human review.
    print("→ Route to a human reviewer before any decision.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
