import json
import os
import pytest
import tempfile
from generate_report import app, generate_pdf, load_employee_json

# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture
def sample_employee():
    return {"name": "Jane Smith", "role": "Software Engineer", "department": "Engineering"}

@pytest.fixture
def employee_json_file(tmp_path, sample_employee):
    f = tmp_path / "jane.json"
    f.write_text(json.dumps(sample_employee))
    return str(f)

# ─────────────────────────────────────────
# 1. JSON PARSING TESTS
# ─────────────────────────────────────────
class TestJsonParsing:
    def test_load_valid_json(self, employee_json_file, sample_employee):
        """load_employee_json should return the correct dict"""
        data = load_employee_json(employee_json_file)
        assert data["name"]       == sample_employee["name"]
        assert data["role"]       == sample_employee["role"]
        assert data["department"] == sample_employee["department"]

    def test_load_json_all_fields_present(self, employee_json_file):
        """All three required fields must exist in loaded JSON"""
        data = load_employee_json(employee_json_file)
        for field in ["name", "role", "department"]:
            assert field in data

    def test_load_invalid_json_raises(self, tmp_path):
        """Malformed JSON should raise an exception"""
        bad = tmp_path / "bad.json"
        bad.write_text("{ not valid json }")
        with pytest.raises(json.JSONDecodeError):
            load_employee_json(str(bad))

    def test_load_missing_file_raises(self):
        """Missing file should raise FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_employee_json("nonexistent.json")

# ─────────────────────────────────────────
# 2. PDF GENERATION TESTS
# ─────────────────────────────────────────
class TestPdfGeneration:
    def test_pdf_file_created(self, tmp_path, sample_employee):
        """generate_pdf should create a file at the given path"""
        out = str(tmp_path / "reports" / "test.pdf")
        result = generate_pdf(sample_employee, out)
        assert os.path.exists(result)

    def test_pdf_returns_correct_path(self, tmp_path, sample_employee):
        """generate_pdf should return the output path"""
        out = str(tmp_path / "reports" / "test.pdf")
        result = generate_pdf(sample_employee, out)
        assert result == out

    def test_pdf_file_has_content(self, tmp_path, sample_employee):
        """Generated PDF should not be empty"""
        out = str(tmp_path / "reports" / "test.pdf")
        generate_pdf(sample_employee, out)
        assert os.path.getsize(out) > 1000

    def test_pdf_is_valid_pdf(self, tmp_path, sample_employee):
        """Generated file should start with PDF magic bytes"""
        out = str(tmp_path / "reports" / "test.pdf")
        generate_pdf(sample_employee, out)
        with open(out, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_pdf_creates_output_directory(self, tmp_path, sample_employee):
        """generate_pdf should create the output dir if it doesn't exist"""
        out = str(tmp_path / "new_dir" / "deep" / "report.pdf")
        generate_pdf(sample_employee, out)
        assert os.path.exists(out)

    def test_pdf_missing_fields_uses_defaults(self, tmp_path):
        """Missing fields should fallback to 'Unknown' without crashing"""
        out = str(tmp_path / "reports" / "partial.pdf")
        generate_pdf({}, out)
        assert os.path.exists(out)

# ─────────────────────────────────────────
# 3. FLASK ROUTE TESTS
# ─────────────────────────────────────────
class TestFlaskRoutes:
    def test_index_returns_200(self, client):
        """GET / should return 200"""
        res = client.get("/")
        assert res.status_code == 200

    def test_index_returns_json(self, client):
        """GET / should return JSON with service info"""
        res  = client.get("/")
        data = json.loads(res.data)
        assert data["status"] == "running"
        assert "service" in data

    def test_generate_returns_201(self, client, sample_employee):
        """POST /generate with valid data should return 201"""
        res = client.post(
            "/generate",
            data=json.dumps(sample_employee),
            content_type="application/json"
        )
        assert res.status_code == 201

    def test_generate_returns_report_filename(self, client, sample_employee):
        """POST /generate response should include the report filename"""
        res  = client.post("/generate", data=json.dumps(sample_employee), content_type="application/json")
        data = json.loads(res.data)
        assert "report" in data
        assert data["report"].endswith(".pdf")

    def test_generate_missing_body_returns_400(self, client):
        """POST /generate without body should return 400"""
        res = client.post("/generate", content_type="application/json")
        assert res.status_code == 400

    def test_generate_missing_fields_returns_400(self, client):
        """POST /generate with incomplete data should return 400"""
        res = client.post(
            "/generate",
            data=json.dumps({"name": "Jane"}),
            content_type="application/json"
        )
        assert res.status_code == 400

    def test_report_not_found_returns_404(self, client):
        """GET /report/<nonexistent> should return 404"""
        res = client.get("/report/doesnotexist.pdf")
        assert res.status_code == 404

    def test_generate_creates_downloadable_report(self, client, sample_employee):
        """After /generate, /report/<file> should return 200"""
        gen  = client.post("/generate", data=json.dumps(sample_employee), content_type="application/json")
        name = json.loads(gen.data)["report"]
        res  = client.get(f"/report/{name}")
        assert res.status_code == 200