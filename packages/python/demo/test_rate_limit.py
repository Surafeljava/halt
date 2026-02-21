"""Simple client to exercise rate limiting.

Run:
  python demo/test_rate_limit.py

Make sure the Flask app is running first.
"""

import time
import urllib.request

URL = "http://127.0.0.1:5000/limited"


def make_request(i: int) -> None:
    req = urllib.request.Request(URL, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            headers = dict(resp.headers)
            print(
                f"[{i}] status={resp.status} "
                f"remaining={headers.get('RateLimit-Remaining')} "
                f"reset={headers.get('RateLimit-Reset')}"
            )
    except urllib.error.HTTPError as err:
        headers = dict(err.headers)
        print(
            f"[{i}] status={err.code} "
            f"remaining={headers.get('RateLimit-Remaining')} "
            f"retry_after={headers.get('Retry-After')}"
        )


if __name__ == "__main__":
    for i in range(1, 7):
        make_request(i)
        time.sleep(0.5)
