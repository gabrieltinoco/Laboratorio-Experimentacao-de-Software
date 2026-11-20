import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(paths: list[Path], out: Path) -> None:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {"files": {}}
    for path in paths:
        path = Path(path)
        if path.exists():
            data["files"][path.as_posix()] = _sha256(path)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
