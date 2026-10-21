# AI Metadata Remover

Small CLI tool to strip AI-generated metadata (EXIF/IPTC/XMP/PNG text chunks)
from images. Useful for scrubbing generator fingerprints (Stable Diffusion,
Midjourney, DALL-E, Adobe Firefly, Leonardo.ai, etc.) before sharing.

## Install

```bash
pip install -r requirements.txt
```

## Usage

Single file (removes only AI-detected metadata):
```bash
python metadata_cleaner.py input.jpg output.jpg
```

Remove *all* metadata from a file:
```bash
python metadata_cleaner.py input.jpg output.jpg --remove-all
```

Batch process a directory (writes cleaned files in-place):
```bash
python metadata_cleaner.py ./photos --batch
```

Batch into a separate output directory:
```bash
python metadata_cleaner.py ./photos --batch --output-dir ./cleaned
```

## Supported formats

JPEG, PNG, WebP, TIFF.

## What it removes

Metadata values/tags containing AI-generator signatures, plus known AI-carrying
EXIF tags (ImageDescription, Software, Artist, Copyright, XPComment/XPAuthor/
XPKeywords/XPTitle/XPSubject, UserComment). In `--remove-all` mode, all EXIF
and PNG text chunks are stripped.
