from typing import Tuple, List
import io

def extract_text_from_file(data: bytes, filename: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    lower = filename.lower()

    if lower.endswith(".pdf"):
        import fitz  # PyMuPDF
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join([page.get_text("text") for page in doc]).strip()
        if len(text) < 200:
            warnings.append("Extraction PDF très faible (PDF image ou mise en page complexe).")
        return text, warnings

    if lower.endswith(".docx") or lower.endswith(".doc"):
        import docx
        f = io.BytesIO(data)
        d = docx.Document(f)
        text = "\n".join([p.text for p in d.paragraphs]).strip()
        if len(text) < 200:
            warnings.append("Extraction DOCX très faible (document vide ou contenu non standard).")
        return text, warnings

    raise ValueError("Extension non supportée (PDF/DOCX uniquement).")
