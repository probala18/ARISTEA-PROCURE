from pathlib import Path
from typing import Iterable


def validate_upload(
    filename: str | None,
    content: bytes,
    allowed_extensions: Iterable[str],
    max_bytes: int,
    content_type: str | None = None,
    allowed_content_types: Iterable[str] | None = None,
) -> str:
    """Validate bounded upload input and return a safe basename."""
    if not content:
        raise ValueError("Uploaded file is empty.")
    if len(content) > max_bytes:
        raise ValueError("Uploaded file exceeds the configured size limit.")

    name = filename or ""
    safe_name = Path(name).name
    if not safe_name or safe_name != name or safe_name in {".", ".."}:
        raise ValueError("Unsafe upload filename.")
    extension = Path(safe_name).suffix.lower().lstrip(".")
    if extension not in {item.lower().lstrip(".") for item in allowed_extensions}:
        raise ValueError("Unsupported upload file format.")
    if allowed_content_types and content_type and content_type.lower() not in {
        item.lower() for item in allowed_content_types
    }:
        raise ValueError("Unsupported upload content type.")
    return safe_name


def validate_dataset_path(dataset_path: str | None) -> None:
    """Allow only the supplied benchmark dataset through the API boundary."""
    if not dataset_path:
        return
    path = Path(dataset_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Only the supplied benchmark dataset is allowed.")
    normalized = str(path).replace("\\", "/")
    if normalized != "csvfiles/query_dataset.json":
        raise ValueError("Only csvfiles/query_dataset.json is allowed.")
