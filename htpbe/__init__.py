"""HTPBE — Python client for the PDF tamper/forgery detection API.

https://htpbe.tech/api
"""

from .client import Client, HtpbeAPIError, HtpbeError

__all__ = ["Client", "HtpbeError", "HtpbeAPIError"]
__version__ = "0.1.0"
