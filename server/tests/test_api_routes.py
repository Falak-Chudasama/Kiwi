import io
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "max_upload_mb" in data

def test_system_status(client: TestClient):
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "engines" in data
    assert isinstance(data["engines"], list)
    assert len(data["engines"]) > 0

def test_document_targets(client: TestClient):
    resp = client.get("/api/documents/targets?filename=test.docx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_ext"] == "docx"
    assert len(data["targets"]) > 0

def test_document_convert_invalid_target(client: TestClient):
    file_content = b"fake doc content"
    files = {"file": ("test.xyz", file_content, "application/octet-stream")}
    resp = client.post("/api/documents/convert", files=files, data={"target_ext": "nonexistent"})
    assert resp.status_code == 400

def test_pdf_split_invalid_json_does_not_leak_workspace(client: TestClient):
    files = {"file": ("sample.pdf", b"%PDF-1.4 test", "application/pdf")}
    # Invalid JSON
    resp = client.post("/api/pdf/split", files=files, data={"ranges": "{not valid json}"})
    assert resp.status_code == 400
    assert "Invalid page ranges" in resp.json()["detail"]

def test_pdf_reorder_invalid_json(client: TestClient):
    files = {"file": ("sample.pdf", b"%PDF-1.4 test", "application/pdf")}
    resp = client.post("/api/pdf/reorder", files=files, data={"order": "invalid"})
    assert resp.status_code == 400
    assert "Invalid page order" in resp.json()["detail"]

def test_pdf_watermark_invalid_color(client: TestClient):
    files = {"file": ("sample.pdf", b"%PDF-1.4 test", "application/pdf")}
    resp = client.post("/api/pdf/watermark", files=files, data={"text": "CONFIDENTIAL", "color": "bad,color"})
    assert resp.status_code == 400

def test_pdf_rotate_invalid_degrees(client: TestClient):
    files = {"file": ("sample.pdf", b"%PDF-1.4 test", "application/pdf")}
    resp = client.post("/api/pdf/rotate", files=files, data={"degrees": "45"})
    assert resp.status_code == 400

def test_compress_invalid_level(client: TestClient):
    files = {"file": ("test.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    resp = client.post("/api/compress", files=files, data={"level": "invalid_level"})
    assert resp.status_code == 400

def test_archives_create_invalid_format(client: TestClient):
    files = [("files", ("test.txt", b"hello", "text/plain"))]
    resp = client.post("/api/archives/create", files=files, data={"archive_format": "rar"})
    assert resp.status_code == 400
    assert "Unsupported archive format" in resp.json()["detail"]

def test_job_not_found(client: TestClient):
    resp = client.get("/api/jobs/nonexistent-id-12345")
    assert resp.status_code == 404

def test_job_cancel_not_found(client: TestClient):
    resp = client.post("/api/jobs/nonexistent-id-12345/cancel")
    assert resp.status_code == 404

