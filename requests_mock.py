"""Minimal requests-mock replacement for local tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class _MockResponse:
    status_code: int
    _json_data: Any
    text: str

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("No JSON data for this response")
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)


class Mocker:
    """Simple mocker for requests.Session.get used in tests."""

    def __init__(self) -> None:
        self._registry: Dict[str, _MockResponse] = {}
        self._original_session_get = None
        self._original_requests_get = None

    def get(
        self,
        url: str,
        *,
        json: Optional[Any] = None,
        text: Optional[str] = None,
        status_code: int = 200,
    ) -> None:
        self._registry[url] = _MockResponse(
            status_code=status_code,
            _json_data=json,
            text=text or "",
        )

    def __enter__(self) -> "Mocker":
        self._original_session_get = requests.Session.get
        self._original_requests_get = requests.get

        def _mock_get(session: requests.Session, url: str, **kwargs: Any) -> _MockResponse:
            if url in self._registry:
                return self._registry[url]
            raise requests.RequestException(f"No mock registered for {url}")

        def _mock_requests_get(url: str, **kwargs: Any) -> _MockResponse:
            return _mock_get(requests.Session(), url, **kwargs)

        requests.Session.get = _mock_get  # type: ignore[assignment]
        requests.get = _mock_requests_get  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._original_session_get is not None:
            requests.Session.get = self._original_session_get  # type: ignore[assignment]
        if self._original_requests_get is not None:
            requests.get = self._original_requests_get  # type: ignore[assignment]
        self._registry.clear()
