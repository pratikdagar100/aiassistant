"""Filesystem tools (spec section 19). Pure mechanism — no permission checks
here, those happen in the approval gateway before these are ever called
(app/security/approval.py + app/api/routes/computer.py).
"""

from __future__ import annotations

import filecmp
import hashlib
import shutil
import zipfile
from pathlib import Path


class FilesystemError(RuntimeError):
    pass


def list_directory(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FilesystemError(f"Path does not exist: {path}")
    if not p.is_dir():
        raise FilesystemError(f"Not a directory: {path}")

    entries = []
    for child in sorted(p.iterdir()):
        try:
            stat = child.stat()
            entries.append(
                {
                    "name": child.name,
                    "path": str(child),
                    "is_dir": child.is_dir(),
                    "size_bytes": stat.st_size if child.is_file() else None,
                    "modified": stat.st_mtime,
                }
            )
        except OSError:
            continue
    return entries


def search(root: str, pattern: str, max_results: int = 200) -> list[str]:
    p = Path(root)
    if not p.exists():
        raise FilesystemError(f"Path does not exist: {root}")
    results = []
    for match in p.rglob(pattern):
        results.append(str(match))
        if len(results) >= max_results:
            break
    return results


def read_file(path: str, max_bytes: int = 1_000_000) -> str:
    p = Path(path)
    if not p.exists():
        raise FilesystemError(f"File does not exist: {path}")
    if not p.is_file():
        raise FilesystemError(f"Not a file: {path}")
    data = p.read_bytes()[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FilesystemError(f"File is not valid UTF-8 text: {path}") from exc


def write_file(path: str, content: str, overwrite: bool = True) -> dict:
    p = Path(path)
    if p.exists() and not overwrite:
        raise FilesystemError(f"File already exists and overwrite=False: {path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"path": str(p), "bytes_written": len(content.encode("utf-8"))}


def create_folder(path: str) -> dict:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return {"path": str(p)}


def create_file(path: str) -> dict:
    p = Path(path)
    if p.exists():
        raise FilesystemError(f"File already exists: {path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()
    return {"path": str(p)}


def copy(src: str, dst: str) -> dict:
    src_p, dst_p = Path(src), Path(dst)
    if not src_p.exists():
        raise FilesystemError(f"Source does not exist: {src}")
    if src_p.is_dir():
        shutil.copytree(src_p, dst_p, dirs_exist_ok=True)
    else:
        dst_p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_p, dst_p)
    return {"src": str(src_p), "dst": str(dst_p)}


def move(src: str, dst: str) -> dict:
    src_p, dst_p = Path(src), Path(dst)
    if not src_p.exists():
        raise FilesystemError(f"Source does not exist: {src}")
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_p), str(dst_p))
    return {"src": str(src_p), "dst": str(dst_p)}


def rename(path: str, new_name: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FilesystemError(f"Path does not exist: {path}")
    target = p.parent / new_name
    p.rename(target)
    return {"old_path": str(p), "new_path": str(target)}


def archive(paths: list[str], output_zip: str) -> dict:
    out = Path(output_zip)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for raw in paths:
            p = Path(raw)
            if not p.exists():
                raise FilesystemError(f"Path does not exist: {raw}")
            if p.is_dir():
                for child in p.rglob("*"):
                    if child.is_file():
                        zf.write(child, child.relative_to(p.parent))
            else:
                zf.write(p, p.name)
    return {"output": str(out), "entries": len(zf.namelist())}


def delete(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FilesystemError(f"Path does not exist: {path}")
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return {"deleted": str(p)}


def compare(path_a: str, path_b: str) -> dict:
    a, b = Path(path_a), Path(path_b)
    if not a.exists() or not b.exists():
        raise FilesystemError("Both paths must exist to compare")
    if a.is_dir() and b.is_dir():
        cmp = filecmp.dircmp(a, b)
        return {"identical": not (cmp.left_only or cmp.right_only or cmp.diff_files), "left_only": cmp.left_only, "right_only": cmp.right_only, "diff_files": cmp.diff_files}
    identical = filecmp.cmp(a, b, shallow=False)
    return {"identical": identical}


def metadata(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FilesystemError(f"Path does not exist: {path}")
    stat = p.stat()
    result = {
        "path": str(p),
        "is_dir": p.is_dir(),
        "size_bytes": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "accessed": stat.st_atime,
    }
    if p.is_file() and stat.st_size < 50_000_000:
        result["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result
