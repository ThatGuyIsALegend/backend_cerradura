import mimetypes
import re
from pathlib import Path

from app.core.config import settings

EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

_SAFE_EXT_RE = re.compile(r"^\.[a-z0-9]{1,9}$")


def storage_dir() -> Path:
    directory = Path(settings.ACCESS_ATTEMPTS_DIR)
    if not directory.is_absolute():
        directory = Path.cwd() / directory
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def extension_for(content_type: str | None, filename: str | None = None) -> str:
    """Elige una extensión segura para la foto guardada.

    Los tipos válidos (jpeg/png) conservan su extensión. Para cualquier
    otro tipo se intenta deducir de `content_type` o del nombre original
    y se usa `.bin` como último recurso.
    """
    content_type = (content_type or "").split(";")[0].strip().lower()
    if content_type in EXTENSIONS:
        return EXTENSIONS[content_type]
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        # Ignorar el genérico `.bin`: en ese caso el nombre original
        # suele ser más informativo (p. ej. `scan.bmp`).
        if (guessed and guessed.lower() != ".bin"
                and _SAFE_EXT_RE.match(guessed.lower())):
            return guessed.lower()
    ext = Path(filename or "").suffix.lower()
    if ext and _SAFE_EXT_RE.match(ext):
        return ext
    return ".bin"


def read_upload_bytes(upload, cap_bytes: int) -> tuple[bytes, bool]:
    """Lee el upload completo por chunks.

    Devuelve `(datos, truncado)`. Si `truncado` es True, el upload supera
    `cap_bytes` y los datos devueltos están incompletos (deben descartarse).
    """
    try:
        upload.file.seek(0)
    except (OSError, ValueError):
        pass
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = upload.file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > cap_bytes:
            return b"", True
        chunks.append(chunk)
    return b"".join(chunks), False


def save_attempt_image(log_id, image_bytes: bytes,
                       content_type: str | None,
                       filename: str | None = None) -> str:
    """Guarda en disco la foto de un intento y devuelve su ruta relativa."""
    extension = extension_for(content_type, filename)
    destination = storage_dir() / f"{log_id}{extension}"
    with open(destination, "wb") as fh:
        fh.write(image_bytes)
    # Guardar ruta relativa al cwd para que sea portable entre entornos.
    try:
        return str(destination.relative_to(Path.cwd()))
    except ValueError:
        return str(destination)


def delete_attempt_image(image_path: str | None) -> None:
    if not image_path:
        return
    try:
        path = Path(image_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path.unlink(missing_ok=True)
    except OSError:
        pass


def resolve_attempt_image_path(image_path: str | None) -> Path | None:
    if not image_path:
        return None
    path = Path(image_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.is_file():
        return None
    return path
