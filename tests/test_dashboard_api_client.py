import json
import unittest
from unittest.mock import patch

from fkip.interfaces.dashboard.api_client import FastApiClient


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class DashboardApiClientTests(unittest.TestCase):
    def test_client_calls_fastapi_endpoints(self):
        def fake_urlopen(request, timeout):
            url = request.full_url
            if url.endswith("/health"):
                return _FakeResponse({"status": "ok"})
            if "/search?" in url:
                return _FakeResponse([{"document_id": "doc-1", "title": "Risk Report", "score": 0.9}])
            if url.endswith("/analysis/answer"):
                return _FakeResponse({"answer": "Evidence-based answer [1]", "citations": []})
            return _FakeResponse({"path": url})

        with patch("fkip.interfaces.dashboard.api_client.urlopen", side_effect=fake_urlopen):
            client = FastApiClient("http://api.example")
            self.assertEqual(client.health()["status"], "ok")
            self.assertEqual(client.search("risk", limit=1)[0]["document_id"], "doc-1")
            self.assertIn("[1]", client.answer("What is the risk?", limit=1)["answer"])


if __name__ == "__main__":
    unittest.main()
