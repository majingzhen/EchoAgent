from fastapi import APIRouter, File, UploadFile

from app.utils.file_utils import extract_text

router = APIRouter(prefix="/utils", tags=["utils"])

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "doc", "docx"}


@router.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{ext}，请上传 PDF / TXT / MD / DOC / DOCX")
    raw = await file.read()
    text = extract_text(raw, filename)
    return {"text": text, "filename": filename}
