"""Image cleaning logic."""

import os
import shutil
import struct
import zlib
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ExifTags

from config import AI_EXIF_TAG_IDS, IMAGE_EXTENSIONS
from metadata import is_ai_metadata_value


def _is_ai_tag(tag_id: int) -> bool:
    return tag_id in AI_EXIF_TAG_IDS


def remove_ai_exif(image: Image.Image) -> Tuple[Image.Image, int]:
    removed = 0
    exif = image.getexif()
    if not exif:
        return image, 0

    to_delete = []
    for tag_id, value in list(exif.items()):
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        value_str = str(value)
        if (
            _is_ai_tag(tag_id)
            or is_ai_metadata_value(value_str)
            or is_ai_metadata_value(tag_name)
        ):
            to_delete.append(tag_id)

    for tag_id in to_delete:
        del exif[tag_id]
        removed += 1

    return image, removed


def _decode_png_text(chunk_type: bytes, data: bytes) -> str:
    try:
        if chunk_type == b"tEXt":
            keyword, _, text = data.partition(b"\x00")
            return (keyword + b" " + text).decode("latin-1", errors="ignore")
        if chunk_type == b"zTXt":
            keyword, _, rest = data.partition(b"\x00")
            if rest:
                method = rest[0:1]
                compressed = rest[1:]
                if method == b"\x00":
                    text = zlib.decompress(compressed).decode(
                        "latin-1", errors="ignore"
                    )
                else:
                    text = compressed.decode("latin-1", errors="ignore")
            else:
                text = ""
            return keyword.decode("latin-1", errors="ignore") + " " + text
        if chunk_type == b"iTXt":
            parts = data.split(b"\x00")
            decoded = [p.decode("latin-1", errors="ignore") for p in parts]
            return " ".join(decoded)
    except Exception:
        pass
    return data.decode("latin-1", errors="ignore")


def _strip_png_text_chunks(data: bytes) -> Tuple[bytes, int]:
    removed = 0
    out = bytearray(data[:8])
    pos = 8
    length = len(data)

    while pos < length:
        if pos + 8 > length:
            out.extend(data[pos:])
            break

        chunk_len = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + chunk_len]

        if chunk_type in (b"tEXt", b"zTXt", b"iTXt"):
            text = _decode_png_text(chunk_type, chunk_data)
            if is_ai_metadata_value(text) or any(
                sig in text.lower()
                for sig in [
                    "parameters",
                    "software",
                    "prompt",
                    "negative prompt",
                    "steps",
                    "sampler",
                    "cfg",
                    "seed",
                    "model",
                ]
            ):
                removed += 1
                pos += 12 + chunk_len
                continue

        out.extend(data[pos : pos + 12 + chunk_len])
        pos += 12 + chunk_len

    return bytes(out), removed


def _strip_all_png_text_chunks(data: bytes) -> Tuple[bytes, int]:
    removed = 0
    out = bytearray(data[:8])
    pos = 8
    length = len(data)
    while pos < length:
        if pos + 8 > length:
            out.extend(data[pos:])
            break
        chunk_len = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        pos += 12 + chunk_len
        if chunk_type in (b"tEXt", b"zTXt", b"iTXt"):
            removed += 1
            continue
        out.extend(data[pos - 12 - chunk_len : pos])
    return bytes(out), removed


def clean_png(path: Path, remove_all: bool) -> int:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return 0

    if remove_all:
        new_data, removed = _strip_all_png_text_chunks(data)
    else:
        new_data, removed = _strip_png_text_chunks(data)

    if removed and new_data != data:
        path.write_bytes(new_data)
    return removed


def clean_image(path: Path, output: Optional[Path], remove_all: bool) -> int:
    suffix = path.suffix.lower()

    if suffix == ".png":
        target = output if output else path
        if output and output != path:
            shutil.copyfile(path, output)
            path = output
        return clean_png(path, remove_all)

    try:
        with Image.open(path) as img:
            removed = 0
            _img, exif_removed = remove_ai_exif(img)
            removed += exif_removed

            exif = img.getexif()
            if remove_all:
                exif.clear()

            fmt = img.format
            save_kwargs = {}
            if fmt in ("JPEG", "WEBP", "TIFF"):
                save_kwargs["exif"] = exif.tobytes() if len(exif) else b""

            target = output if output else path
            img.save(target, format=fmt, **save_kwargs)
            return removed
    except Exception as exc:
        print(
            f"Warning: could not process {path}: {exc}", file=__import__("sys").stderr
        )
        return 0


def iter_images(directory: Path):
    for root, _dirs, files in os.walk(directory):
        for name in files:
            if Path(name).suffix.lower() in IMAGE_EXTENSIONS:
                yield Path(root) / name
