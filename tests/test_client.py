"""Tests for htpbe.Client — run with `python -m unittest` (no extra deps)."""

import unittest

from htpbe import Client


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.content = b"{}"
        self.reason = "OK"
        self.text = ""

    def json(self):
        return self._payload


class _RecordingSession:
    """Stand-in for requests.Session that records outgoing params."""

    def __init__(self, payload_for):
        self._payload_for = payload_for
        self.calls = []

    def request(self, method, url, headers=None, timeout=None, **kwargs):
        params = kwargs.get("params", {})
        self.calls.append({"method": method, "url": url, "params": params})
        return _FakeResponse(self._payload_for(params))


class ListChecksPaginationTest(unittest.TestCase):
    def test_offset_is_sent_and_page_is_not(self):
        session = _RecordingSession(
            lambda params: {"data": [{"id": "id-at-%d" % params["offset"]}]}
        )
        client = Client(api_key="htpbe_test_x", session=session)

        client.list_checks(limit=50)
        client.list_checks(limit=50, offset=50)

        first, second = session.calls
        # The whole point of P1-4: the SDK must speak the API's offset contract,
        # not the silently-ignored `page` param.
        self.assertEqual(first["params"], {"limit": 50, "offset": 0})
        self.assertEqual(second["params"], {"limit": 50, "offset": 50})
        self.assertNotIn("page", first["params"])
        self.assertNotIn("page", second["params"])

    def test_page_two_differs_from_page_one(self):
        session = _RecordingSession(
            lambda params: {"data": [{"id": "id-at-%d" % params["offset"]}]}
        )
        client = Client(api_key="htpbe_test_x", session=session)

        page_one = client.list_checks(limit=1, offset=0)
        page_two = client.list_checks(limit=1, offset=1)

        self.assertNotEqual(page_one["data"], page_two["data"])


if __name__ == "__main__":
    unittest.main()
