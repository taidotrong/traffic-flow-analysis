#!/usr/bin/env python3
"""Validate a YOLO dataset and summarize image/box class imbalance."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
DEFAULT_CLASSES = ("bus", "car", "motorcycle", "truck")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Dataset root containing train/valid/test")
    parser.add_argument("--classes", nargs="+", default=list(DEFAULT_CLASSES))
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path")
    return parser.parse_args()


def inspect(root: Path, class_names: list[str]) -> dict[str, Any]:
    boxes: Counter[int] = Counter()
    images_with_class: Counter[int] = Counter()
    split_summary: dict[str, dict[str, int]] = {}
    malformed: list[str] = []

    for split in ("train", "valid", "test"):
        image_dir = root / split / "images"
        label_dir = root / split / "labels"
        if not image_dir.is_dir() or not label_dir.is_dir():
            raise NotADirectoryError(f"Missing images/labels directories for split: {split}")

        images = {path.stem for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES}
        labels = list(label_dir.glob("*.txt"))
        split_summary[split] = {
            "images": len(images),
            "labels": len(labels),
            "images_without_label": len(images - {path.stem for path in labels}),
        }

        for label_path in labels:
            classes_in_image: set[int] = set()
            for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                parts = line.split()
                try:
                    class_id = int(float(parts[0]))
                    coordinates = [float(value) for value in parts[1:5]]
                except (IndexError, ValueError):
                    malformed.append(f"{label_path}:{line_number}")
                    continue
                if class_id not in range(len(class_names)) or len(coordinates) != 4:
                    malformed.append(f"{label_path}:{line_number}")
                    continue
                boxes[class_id] += 1
                classes_in_image.add(class_id)
            images_with_class.update(classes_in_image)

    total_boxes = sum(boxes.values())
    class_summary = {}
    for class_id, name in enumerate(class_names):
        count = boxes[class_id]
        class_summary[name] = {
            "images": images_with_class[class_id],
            "boxes": count,
            "share_percent": round(100 * count / total_boxes, 2) if total_boxes else 0.0,
        }

    nonzero_counts = [boxes[class_id] for class_id in range(len(class_names)) if boxes[class_id]]
    imbalance_ratio = max(nonzero_counts) / min(nonzero_counts) if nonzero_counts else None
    return {
        "root": str(root.resolve()),
        "splits": split_summary,
        "total_boxes": total_boxes,
        "classes": class_summary,
        "max_to_min_box_ratio": round(imbalance_ratio, 2) if imbalance_ratio else None,
        "malformed_annotations": malformed,
    }


def main() -> None:
    args = parse_args()
    if not args.root.is_dir():
        raise NotADirectoryError(args.root)
    report = inspect(args.root, args.classes)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
