# htpbe — Python client

Python client for the [HTPBE](https://htpbe.tech) API — **structural PDF tamper & forgery detection**. It analyses a PDF's byte-level structure (xref tables, incremental updates, signatures, object streams) to detect whether a document was modified after creation. No original copy needed.

Not a KYC/identity platform — it's the structural PDF-forensics layer. Full API reference: **https://htpbe.tech/api**

## Install

```bash
pip install htpbe
```

## Quickstart

```python
from htpbe import Client

client = Client(api_key="htpbe_live_...")  # get a key at https://htpbe.tech/api

result = client.analyze_and_wait("https://example.com/invoice.pdf")

print(result["status"])               # "intact" | "modified" | "inconclusive"
print(result["modification_markers"]) # e.g. ["HTPBE_POST_SIGNATURE_EDIT"]
```

The API works on any **publicly accessible** PDF URL (≤ 10 MB), downloadable without authentication.

### Two-step flow

`analyze_and_wait` is shorthand for the underlying two calls:

```python
check_id = client.analyze("https://example.com/contract.pdf")
result = client.get_result(check_id)
```

### List your checks

```python
page = client.list_checks(limit=50)
for check in page["data"]:
    print(check["id"], check["status"])
print(page["total"])  # total number of checks
```

### Error handling

```python
from htpbe import HtpbeAPIError

try:
    result = client.analyze_and_wait(url)
except HtpbeAPIError as exc:
    print(exc.status, exc.code, exc.message)  # e.g. 402 payment_required ...
```

## Testing without spending credits

Test keys (`htpbe_test_...`) return deterministic synthetic results and only accept the documented test URLs — see the API docs. Live keys (`htpbe_live_...`) accept any public PDF URL and draw from your credit balance.

## What you can detect

The verdict is `intact`, `modified`, or `inconclusive`, with named `modification_markers`. Common use cases:

- [Fake invoice detection](https://htpbe.tech/use-cases/fake-invoice-detection)
- [Fake bank statement detection](https://htpbe.tech/use-cases/fake-bank-statement-detection)
- [Insurance claims fraud detection](https://htpbe.tech/use-cases/insurance-claims-fraud-detection)
- [All use cases](https://htpbe.tech/use-cases)

## Links

- API reference & keys: https://htpbe.tech/api
- Free web checker: https://htpbe.tech
- How it works: https://htpbe.tech/how

## License

MIT
