"""
Tests for STEP 48: API Polish & OpenAPI contract verification.
Validates:
- All API routes strictly adhere to /v1 prefix.
- Generated OpenAPI schema is complete with operation IDs, models, and error responses.
- Error envelope {error: {code, message, request_id}} is consistently formatted.
- X-Request-ID header is propagated on all responses.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1_prefix_on_all_routes():
    """Verify that every functional endpoint exposed by the FastAPI app is prefixed with /v1/."""
    spec = app.openapi()
    paths = list(spec["paths"].keys())

    assert len(paths) >= 22, f"Expected at least 22 paths in OpenAPI spec, found {len(paths)}"
    non_v1 = [p for p in paths if not p.startswith("/v1/")]
    assert len(non_v1) == 0, f"Found endpoints without /v1 prefix: {non_v1}"

    # Also inspect all internal app.routes including mounted sub-routers
    for route in app.routes:
        if hasattr(route, "path") and route.path:
            if route.path.startswith(("/docs", "/redoc", "/openapi.json")):
                continue
            assert route.path.startswith("/v1/"), f"Route '{route.path}' missing /v1 prefix"
        elif hasattr(route, "prefix") and route.prefix:
            assert route.prefix.startswith("/v1/"), (
                f"Sub-router prefix '{route.prefix}' missing /v1 prefix"
            )


def test_openapi_spec_completeness():
    """Verify OpenAPI spec generates cleanly with all tags, operation IDs, and schemas."""
    spec = app.openapi()
    assert spec["info"]["title"] == "Allcited API"
    assert spec["info"]["version"] == "1.0.0"

    expected_tags = {
        "System",
        "Ingestion",
        "Q&A",
        "Library",
        "Payments",
        "Telegram",
        "Audit & Stats",
        "Feedback & Trace",
    }
    actual_tags = {t["name"] for t in spec.get("tags", [])}
    assert expected_tags.issubset(actual_tags), f"Missing tags: {expected_tags - actual_tags}"

    paths = spec["paths"]
    assert len(paths) >= 22

    schemas = spec["components"]["schemas"]
    required_schemas = {
        "ErrorResponse",
        "ErrorDetail",
        "HealthResponse",
        "IngestResponse",
        "QueryRequest",
        "CheckoutResponse",
        "PlatformStatsResponse",
        "TraceRecord",
    }
    assert required_schemas.issubset(set(schemas.keys())), (
        f"Missing schemas: {required_schemas - set(schemas.keys())}"
    )

    # Verify every route has an operationId
    for path, methods in paths.items():
        for method, details in methods.items():
            assert "operationId" in details, f"Missing operationId in {method.upper()} {path}"
            assert len(details["operationId"]) > 0


def test_error_envelope_and_request_id():
    """Verify error responses include standard error envelope and X-Request-ID."""
    # 404 for non-existent session
    res = client.get("/v1/session/non_existent_session_id_12345")
    assert res.status_code == 404
    data = res.json()

    # Must contain both envelope and request_id
    assert "error" in data, f"Missing error envelope: {data}"
    assert data["error"]["code"] == "session_not_found"
    assert "request_id" in data["error"]
    assert data["error"]["request_id"].startswith("req_")
    assert res.headers.get("X-Request-ID") == data["error"]["request_id"]


def test_validation_error_envelope():
    """Verify 422 request validation errors follow standard error envelope."""
    # POST /v1/ingest/url with missing url field
    res = client.post("/v1/ingest/url", json={})
    assert res.status_code == 422
    data = res.json()

    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "request_id" in data["error"]
    assert "errors" in data["error"]
    assert res.headers.get("X-Request-ID") is not None
