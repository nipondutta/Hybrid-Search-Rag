import re
from hashlib import sha1

def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_records(records: list[dict], chunk_size: int = 900,
                  overlap: int = 150) -> list[dict]:
    """Split text into overlapping character windows; tune using evaluation."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")
    output = []
    stride = chunk_size - overlap
    for record in records:
        text = clean_text(record["text"])
        for start in range(0, len(text), stride):
            chunk_text = text[start:start + chunk_size].strip()
            if not chunk_text:
                continue
            key = f"{record.get('document_id')}|{record.get('page_number')}|{start}|{chunk_text}"
            chunk_id = sha1(key.encode("utf-8")).hexdigest()[:16]
            output.append({**record, "chunk_id": chunk_id,
                           "text": chunk_text, "chunk_start": start})
            if start + chunk_size >= len(text):
                break
    return output
