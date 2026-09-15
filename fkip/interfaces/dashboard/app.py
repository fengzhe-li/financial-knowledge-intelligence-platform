from __future__ import annotations

import os
from collections import Counter

import streamlit as st

from fkip.interfaces.dashboard.api_client import ApiClientError, FastApiClient


DEFAULT_API_URL = os.getenv("FKIP_API_URL", "http://localhost:8000")


def main() -> None:
    st.set_page_config(
        page_title="Financial Knowledge Intelligence",
        layout="wide",
    )
    st.title("Financial Knowledge Intelligence Platform")
    st.caption("Search and inspect indexed financial documents through the FastAPI service layer.")

    api_url = st.sidebar.text_input("FastAPI base URL", value=DEFAULT_API_URL)
    client = FastApiClient(api_url)

    try:
        health = client.health()
    except ApiClientError as exc:
        st.error(str(exc))
        st.info("Start the API with: `uvicorn fkip.interfaces.api.main:app --reload`")
        return

    st.sidebar.success(f"API connected: {health.get('status', 'unknown')}")
    st.sidebar.caption(health.get("service", "Financial Knowledge Intelligence Platform"))

    stats_tab, search_tab, analysis_tab, catalog_tab = st.tabs(["Pipeline Statistics", "Document Search", "Financial Analysis", "Document Catalog"])
    with stats_tab:
        render_pipeline_statistics(client)
    with search_tab:
        render_search(client)
    with analysis_tab:
        render_financial_analysis(client)
    with catalog_tab:
        render_catalog(client)


def render_pipeline_statistics(client: FastApiClient) -> None:
    st.subheader("Pipeline Statistics")
    try:
        payload = client.pipeline_stats()
    except ApiClientError as exc:
        st.error(str(exc))
        return

    if not payload.get("available"):
        st.warning(payload.get("message", "No metrics available."))
        st.code("python -m fkip.cli ingest samples/financial_sources.json --metrics-output data/metrics/latest_ingestion.json")
        return

    metrics = payload.get("metrics", {})
    cols = st.columns(5)
    cols[0].metric("Sources Seen", metrics.get("sources_seen", 0))
    cols[1].metric("Ingested", metrics.get("documents_ingested", 0))
    cols[2].metric("Skipped", metrics.get("documents_skipped", 0))
    cols[3].metric("Duplicates", metrics.get("duplicate_sources", 0))
    cols[4].metric("Duration (s)", metrics.get("duration_seconds", 0))

    st.caption(f"Metrics file: `{payload.get('metrics_path')}`")
    if metrics.get("errors"):
        st.error("Pipeline errors were reported.")
        st.dataframe(metrics["errors"], use_container_width=True)
    else:
        st.success("No pipeline errors reported in the latest metrics file.")

    with st.expander("Raw pipeline metrics JSON"):
        st.json(metrics)


def render_search(client: FastApiClient) -> None:
    st.subheader("Document Search")
    query = st.text_input("Search query", value="operational resilience fca")
    limit = st.slider("Result limit", min_value=1, max_value=20, value=5)
    if not query.strip():
        st.info("Enter a query to search indexed documents.")
        return

    try:
        results = client.search(query, limit=limit)
    except ApiClientError as exc:
        st.error(str(exc))
        return

    st.caption(f"{len(results)} results returned")
    for result in results:
        render_search_result(client, result)


def render_search_result(client: FastApiClient, result: dict) -> None:
    document_id = result.get("document_id", "")
    try:
        metadata = client.get_document(document_id) if document_id else {}
    except ApiClientError:
        metadata = {}

    title = metadata.get("title") or result.get("title", "Untitled document")
    score = result.get("score", 0)
    with st.container(border=True):
        left, right = st.columns([4, 1])
        left.markdown(f"### {title}")
        right.metric("Score", score)
        st.write(metadata.get("summary") or result.get("summary", "No summary available."))

        chips = metadata.get("topics") or result.get("topics") or []
        if chips:
            st.caption("Topics: " + ", ".join(chips))

        meta_cols = st.columns(4)
        meta_cols[0].write(f"**Issuer:** {metadata.get('issuer') or 'Unknown'}")
        meta_cols[1].write(f"**Source type:** {metadata.get('source_type') or 'Unknown'}")
        meta_cols[2].write(f"**Published:** {metadata.get('published_at') or 'Unknown'}")
        meta_cols[3].write(f"**Document ID:** `{document_id}`")

        if metadata.get("uri"):
            st.write(f"**Source URI:** `{metadata['uri']}`")
        if metadata.get("keywords"):
            st.write("**Keywords:** " + ", ".join(metadata["keywords"]))


def render_financial_analysis(client: FastApiClient) -> None:
    st.subheader("Traceable Financial Analysis")
    st.caption("Ask a focused question about indexed financial documents. Answers are limited to retrieved evidence and include citations.")
    question = st.text_area("Financial analysis question", value="What does the FCA say about operational resilience?")
    limit = st.slider("Evidence chunks", min_value=1, max_value=10, value=3)
    if st.button("Generate cited answer", type="primary"):
        if not question.strip():
            st.warning("Enter a financial document analysis question.")
            return
        try:
            result = client.answer(question, limit=limit)
        except ApiClientError as exc:
            st.error(str(exc))
            return

        st.markdown("### Answer")
        st.write(result.get("answer", "No answer returned."))
        citations = result.get("citations", [])
        st.markdown("### Citations")
        if not citations:
            st.info("No cited evidence was retrieved.")
        for index, citation in enumerate(citations, start=1):
            with st.expander(f"[{index}] {citation.get('title', 'Untitled')} - score {citation.get('score', 0)}"):
                st.write(citation.get("excerpt", ""))
                st.write(f"**Issuer:** {citation.get('issuer') or 'Unknown'}")
                st.write(f"**Source URI:** `{citation.get('uri')}`")
                st.write(f"**Chunk:** `{citation.get('chunk_id')}`")


def render_catalog(client: FastApiClient) -> None:
    st.subheader("Document Catalog")
    try:
        documents = client.list_documents()
    except ApiClientError as exc:
        st.error(str(exc))
        return

    if not documents:
        st.info("No indexed documents found.")
        return

    source_counts = Counter(document.get("source_type", "unknown") for document in documents)
    cols = st.columns(3)
    cols[0].metric("Indexed Documents", len(documents))
    cols[1].metric("Source Types", len(source_counts))
    cols[2].metric("Top Source Type", source_counts.most_common(1)[0][0])

    st.dataframe(documents, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
