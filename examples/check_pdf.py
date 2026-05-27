"""Minimal example: check whether a PDF has been modified.

    export HTPBE_API_KEY=htpbe_live_...
    python examples/check_pdf.py https://example.com/invoice.pdf
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
    # Reject documents that should be untouched institutional originals.
    if status == "modified":
        print("→ MODIFIED: request an untouched digital original.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
