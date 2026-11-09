from pathlib import Path
from app.core.files import safe_filename, unique_output_name, new_job_workspace, cleanup_dir, PROJECT_MARKER
from app.core.errors import sanitize_text, sanitize_command

def test_safe_filename():
    assert safe_filename("simple.txt") == "simple.txt"
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename(r"..\..\Windows\System32\cmd.exe") == "cmd.exe"
    assert safe_filename("file\x00name.png") == "filename.png"
    assert safe_filename("C:\\Users\\admin\\secret.pdf") == "secret.pdf"
    # Reserved name protection
    assert safe_filename("con.txt").startswith("safe_")
    assert safe_filename("AUX.png").startswith("safe_")
    # Empty fallback
    assert safe_filename("") == "file"
    assert safe_filename("   ") == "file"

def test_unique_output_name(tmp_path: Path):
    dest = unique_output_name(tmp_path, "report.pdf")
    assert dest.name == "report.pdf"
    dest.touch()

    # Second file with same name must not collide
    dest2 = unique_output_name(tmp_path, "report.pdf")
    assert dest2.name != "report.pdf"
    assert dest2.stem.startswith("report-")
    assert dest2.suffix == ".pdf"

def test_workspace_lifecycle():
    ws = new_job_workspace()
    assert ws.exists()
    assert (ws / "input").exists()
    assert (ws / "output").exists()
    assert (ws / PROJECT_MARKER).exists()

    cleanup_dir(ws)
    assert not ws.exists()

def test_error_and_log_sanitization():
    # Passwords should be redacted
    cmd = ["qpdf", "--password=SuperSecret123", "input.pdf", "output.pdf"]
    sanitized = sanitize_command(cmd)
    assert "SuperSecret123" not in str(sanitized)
    assert "[REDACTED]" in str(sanitized)

    # Text containing user paths and passwords
    text = r"Error opening C:\Users\ADMIN\Documents\secret.pdf with password=MyPass99"
    cleaned = sanitize_text(text)
    assert "ADMIN" not in cleaned
    assert "MyPass99" not in cleaned

