from __future__ import annotations

import io


def extract_pdf_text(raw: bytes) -> str:
    try:
        import pypdf
    except ImportError:
        raise RuntimeError("pypdf 未安装，无法解析 PDF，请运行 pip install pypdf")
    reader = pypdf.PdfReader(io.BytesIO(raw))
    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)
    text = "\n".join(pages_text)
    if not text.strip():
        raise RuntimeError("PDF 文本提取失败，该 PDF 可能是扫描件或图片型文档，暂不支持")
    return text[:20000]


def extract_docx_text(raw: bytes) -> str:
    try:
        import docx
    except ImportError:
        raise RuntimeError("python-docx 未安装，请运行 pip install python-docx")
    doc = docx.Document(io.BytesIO(raw))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)
    if not text.strip():
        raise RuntimeError("DOCX 文本提取失败，文档可能为空")
    return text[:20000]


def decode_file(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            text = raw.decode(encoding)
            return text[:20000]
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")[:20000]


def extract_text(raw: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return extract_pdf_text(raw)
    if ext in ("docx", "doc"):
        return extract_docx_text(raw)
    return decode_file(raw)
