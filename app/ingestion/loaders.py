from pathlib import Path
import fitz

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

def load_document(path: str | Path) -> list[dict]:
    """Extract text from TXT, Markdown, or PDF into page-like records."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type {suffix!r}")
    records = []
    if suffix == ".pdf":
        with fitz.open(file_path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                if text:
                    records.append({"document_id": file_path.stem,
                                    "title": file_path.name, "source": file_path.name,
                                    "page_number": page_number, "text": text})
    else:
        text = file_path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            records.append({"document_id": file_path.stem,
                            "title": file_path.name, "source": file_path.name,
                            "page_number": None, "text": text})
    if not records:
        raise ValueError(f"No extractable text found in {file_path.name}")
    return records
