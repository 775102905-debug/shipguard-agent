import uuid
import zipfile
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

from ..core.config import settings


ALLOWED_EXTENSIONS = {".zip"}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_upload(file: UploadFile) -> None:
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}，仅支持 .zip")
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大 (>{settings.MAX_UPLOAD_SIZE_MB}MB)，请压缩后上传",
        )


def extract_zip_safe(file: UploadFile) -> Path:
    extract_id = uuid.uuid4().hex
    extract_path = settings.EXTRACT_DIR / extract_id
    extract_path.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(file.file) as zf:
            for info in zf.infolist():
                sanitized_name = info.filename.replace("\\", "/")
                resolved = (extract_path / sanitized_name).resolve()
                if not str(resolved).startswith(str(extract_path.resolve())):
                    zf.close()
                    shutil.rmtree(extract_path, ignore_errors=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"检测到 zip slip 路径穿越攻击: {info.filename}",
                    )
                if info.is_dir():
                    resolved.mkdir(parents=True, exist_ok=True)
                else:
                    resolved.parent.mkdir(parents=True, exist_ok=True)
                    zf.extract(info, extract_path)
    except zipfile.BadZipFile:
        shutil.rmtree(extract_path, ignore_errors=True)
        raise HTTPException(status_code=400, detail="无效的 ZIP 文件")

    return extract_path


def cleanup_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
