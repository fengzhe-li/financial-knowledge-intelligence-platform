import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from fastapi.testclient import TestClient
except Exception:
    TestClient = None

from fkip.application.analysis import FinancialAnalysisService
from fkip.domain.chunking import chunk_document_text
from fkip.domain.models import ProcessedDocument, SourceType
from fkip.infrastructure.document_reader import validate_url_for_ssrf
from fkip.infrastructure.metadata_repository import SQLiteMetadataRepository
from fkip.infrastructure.vector_store import LocalVectorStore
from fkip.interfaces.api.main import app


class ApiExtensionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if TestClient is None:
            raise unittest.SkipTest("TestClient or httpx not available")
        cls.client = TestClient(app)


    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_overview_endpoint_returns_structured_metrics(self):
        response = self.client.get("/overview")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("indexed_document_count", payload)
        self.assertIn("unique_issuers_count", payload)
        self.assertIn("issuers", payload)
        self.assertIn("source_type_distribution", payload)
        self.assertIn("publication_year_distribution", payload)
        self.assertIn("topic_distribution", payload)
        self.assertIn("recent_documents", payload)
        self.assertIn("recent_pipeline_runs", payload)
        self.assertIsInstance(payload["issuers"], list)

    def test_legacy_documents_endpoint_returns_list(self):
        # Without pagination parameters, returns raw list of summaries for backward compatibility
        response = self.client.get("/documents")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_paginated_documents_endpoint(self):
        response = self.client.get("/documents?page=1&page_size=3")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsInstance(payload, dict)
        self.assertIn("items", payload)
        self.assertIn("total", payload)
        self.assertIn("page", payload)
        self.assertIn("page_size", payload)
        self.assertIn("total_pages", payload)
        self.assertIn("available_issuers", payload)
        self.assertEqual(payload["page"], 1)
        self.assertLessEqual(len(payload["items"]), 3)

    def test_filtered_documents_endpoint_by_issuer(self):
        response = self.client.get("/documents?page=1&issuer=Barclays+PLC")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for item in payload["items"]:
            self.assertEqual(item["issuer"], "Barclays PLC")

    def test_document_detail_and_chunks_endpoints(self):
        docs_res = self.client.get("/documents?page=1&page_size=1")
        payload = docs_res.json()
        if payload["items"]:
            doc_id = payload["items"][0]["document_id"]
            detail_res = self.client.get(f"/documents/{doc_id}")
            self.assertEqual(detail_res.status_code, 200)
            detail = detail_res.json()
            self.assertEqual(detail["document_id"], doc_id)
            self.assertIn("clean_text", detail)
            self.assertIn("object_key", detail)
            self.assertIn("created_at", detail)

            chunks_res = self.client.get(f"/documents/{doc_id}/chunks")
            self.assertEqual(chunks_res.status_code, 200)
            self.assertIsInstance(chunks_res.json(), list)

    def test_document_detail_404_for_unknown_id(self):
        response = self.client.get("/documents/non-existent-doc-id-000")
        self.assertEqual(response.status_code, 404)

    def test_search_endpoint_with_validation(self):
        response = self.client.get("/search?q=operational+resilience&limit=3")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)

    def test_analysis_answer_endpoint(self):
        response = self.client.post("/analysis/answer", json={"question": "What does the FCA say about operational resilience?", "limit": 2})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("question", payload)
        self.assertIn("answer", payload)
        self.assertIn("citations", payload)
        self.assertIn("retrieval_count", payload)

    def test_company_comparison_endpoint(self):
        response = self.client.post(
            "/analysis/compare",
            json={
                "topic": "Operational resilience",
                "issuer_a": "Barclays PLC",
                "issuer_b": "Financial Conduct Authority",
                "limit": 2,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("topic", payload)
        self.assertIn("company_a", payload)
        self.assertIn("company_b", payload)
        self.assertIn("comparison_notes", payload)
        self.assertEqual(payload["company_a"]["issuer"], "Barclays PLC")
        self.assertEqual(payload["company_b"]["issuer"], "Financial Conduct Authority")
        self.assertIn("citations", payload["company_a"])
        self.assertIn("citations", payload["company_b"])

    def test_pipeline_runs_endpoint(self):
        response = self.client.get("/pipeline-runs?limit=5")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_ssrf_validator_rejects_private_and_loopback_ips(self):
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("http://127.0.0.1:8000/secret")
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("http://localhost:5432")
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("http://169.254.169.254/latest/meta-data/")
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("http://10.0.0.1/admin")
        with self.assertRaises(ValueError):
            validate_url_for_ssrf("ftp://example.com/test")

    def test_issuer_specific_chunk_retrieval_isolation(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = SQLiteMetadataRepository(root / "meta.db")
            store = LocalVectorStore(root / "index.json")

            from datetime import UTC, datetime

            doc_a = ProcessedDocument(
                document_id="a1",
                title="Apple 10-K",
                source_type=SourceType.ANNUAL_REPORT,
                issuer="Apple Inc.",
                published_at="2026-01-01",
                uri="a1.htm",
                object_key="a1.txt",
                clean_text="Apple cloud cyber automation revenue profit margin.",
                summary="Apple summary.",
                keywords=["cloud", "cyber"],
                topics=["Technology & Operations"],
                created_at=datetime.now(UTC),
            )
            doc_b = ProcessedDocument(
                document_id="b1",
                title="Microsoft 10-K",
                source_type=SourceType.ANNUAL_REPORT,
                issuer="MICROSOFT CORP",
                published_at="2026-01-01",
                uri="b1.htm",
                object_key="b1.txt",
                clean_text="Microsoft cloud cyber platform software resilience.",
                summary="Microsoft summary.",
                keywords=["cloud", "resilience"],
                topics=["Technology & Operations"],
                created_at=datetime.now(UTC),
            )

            repo.upsert(doc_a)
            repo.upsert(doc_b)
            store.upsert(doc_a)
            store.upsert(doc_b)
            store.upsert_chunks(doc_a, chunk_document_text(doc_a.document_id, doc_a.clean_text, 10, 2))
            store.upsert_chunks(doc_b, chunk_document_text(doc_b.document_id, doc_b.clean_text, 10, 2))

            # Query with issuer_a filter
            retrieved_a = store.search_chunks("cyber cloud", limit=5, issuer="Apple Inc.")
            self.assertTrue(len(retrieved_a) > 0)
            for item in retrieved_a:
                self.assertEqual(item["issuer"], "Apple Inc.")
                self.assertEqual(item["document_id"], "a1")

            # Query with issuer_b filter
            retrieved_b = store.search_chunks("cyber cloud", limit=5, issuer="MICROSOFT CORP")
            self.assertTrue(len(retrieved_b) > 0)
            for item in retrieved_b:
                self.assertEqual(item["issuer"], "MICROSOFT CORP")
                self.assertEqual(item["document_id"], "b1")

            # Compare service isolation
            svc = FinancialAnalysisService(store, repo)
            comp = svc.compare_issuers("cyber cloud", "Apple Inc.", "MICROSOFT CORP", limit=2)
            self.assertFalse(comp.company_a.evidence_gap)
            self.assertFalse(comp.company_b.evidence_gap)
            self.assertEqual(comp.company_a.citations[0].issuer, "Apple Inc.")
            self.assertEqual(comp.company_b.citations[0].issuer, "MICROSOFT CORP")


if __name__ == "__main__":
    unittest.main()
