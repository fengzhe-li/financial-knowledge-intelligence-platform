from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class FastApiClient:
    base_url: str
    timeout_seconds: int = 10

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def pipeline_stats(self) -> dict[str, Any]:
        return self._get("/pipeline-stats")

    def list_documents(self) -> list[dict[str, Any]]:
        return self._get("/documents")

    def get_document(self, document_id: str) -> dict[str, Any]:
        return self._get(f"/documents/{document_id}")

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        return self._get(f"/search?{urlencode({'q': query, 'limit': limit})}")

    def answer(self, question: str, limit: int = 5) -> dict[str, Any]:
        return self._post("/analysis/answer", {"question": question, "limit": limit})

    def _get(self, path: str) -> Any:
        url = f"{self.base_url.rstrip('/')}{path}"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ApiClientError(f"API request failed with HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise ApiClientError(f"Could not connect to API at {self.base_url}: {exc}") from exc

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        url = f"{self.base_url.rstrip('/')}{path}"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ApiClientError(f"API request failed with HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise ApiClientError(f"Could not connect to API at {self.base_url}: {exc}") from exc
