"""CLI for AI metadata remover."""

import argparse
from pathlib import Path
from typing import Optional

from cleaner import clean_image, iter_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove AI-generated metadata from images."
    )
    parser.add_argument("input", help="Input image file or directory")
    parser.add_argument(
        "output", nargs="?", default=None, help="Output file (single file mode only)"
    )
    parser.add_argument(
        "--batch", action="store_true", help="Process all images in the input directory"
    )
    parser.add_argument(
        "--remove-all",
        action="store_true",
        help="Remove all metadata, not just AI-generated",
    )
    parser.add_argument(
        "--output-dir", default=None, help="Output directory for batch mode"
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input not found: {input_path}")
        return 1

    if args.batch:
        if not input_path.is_dir():
            print(f"Error: --batch requires a directory: {input_path}")
            return 1
        output_dir = Path(args.output_dir) if args.output_dir else None
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        total = 0
        count = 0
        for img_path in iter_images(input_path):
            out = (output_dir / img_path.name) if output_dir else None
            removed = clean_image(img_path, out, args.remove_all)
            total += removed
            if removed:
                count += 1
                print(f"Cleaned {removed} AI metadata item(s) from {img_path}")
        print(f"Done. Cleaned {count} file(s), {total} metadata item(s) removed.")
        return 0

    removed = clean_image(
        input_path, Path(args.output) if args.output else None, args.remove_all
    )
    if removed:
        print(f"Removed {removed} AI metadata item(s).")
    else:
        print("No AI-generated metadata found.")
    return 0
