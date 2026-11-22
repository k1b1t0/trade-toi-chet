"""
http client chong ban ip khi cao du lieu web va goi api.
xoay vong user-agent, them do tre ngau nhien (jitter delay) va retry exponential backoff.
"""

import random
import time
from typing import Any

import requests

# danh sach user-agent trinh duyet pho bien de xoay vong ngau nhien
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]


def build_headers(referer: str = "https://cafef.vn/") -> dict[str, str]:
    """tao http headers gia lap trinh duyet that voi user-agent ngau nhien."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer,
        "Connection": "keep-alive",
    }


def polite_sleep(min_sec: float = 0.25, max_sec: float = 0.65) -> None:
    """nghi ngau nhien giua cac request de tranh gay tai server va tranh bi chan ip."""
    time.sleep(random.uniform(min_sec, max_sec))


def fetch_url(
    url: str,
    as_json: bool = False,
    max_retries: int = 3,
    min_delay: float = 0.2,
    max_delay: float = 0.5,
) -> Any:
    """
    tai noi dung url voi co che retry exponential backoff.
    tra ve dict neu as_json=True, nguoc lai tra ve chuoi html text.
    """
    polite_sleep(min_delay, max_delay)
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=build_headers(), timeout=12)
            if resp.status_code == 200:
                if as_json:
                    return resp.json()
                resp.encoding = "utf-8"
                return resp.text
            # neu bi gioi han toc do (429) hoac loi server (5xx) thi doi lau hon
            wait_sec = (2**attempt) + random.uniform(0.2, 0.8)
            print(
                f"[WARN] HTTP {resp.status_code} on {url}, retry {attempt}/{max_retries} in {wait_sec:.1f}s"
            )
            time.sleep(wait_sec)
        except requests.RequestException as exc:
            wait_sec = (2**attempt) + random.uniform(0.2, 0.8)
            print(
                f"[WARN] Request error ({exc}), retry {attempt}/{max_retries} in {wait_sec:.1f}s"
            )
            time.sleep(wait_sec)
    raise RuntimeError(f"Failed to fetch URL after {max_retries} attempts: {url}")
