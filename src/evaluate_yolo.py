#!/usr/bin/env python3
"""Evaluate a YOLO checkpoint and emit machine-readable detection metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", choices=("val", "test"), default="test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default=None)
    parser.add_argument("--project", type=Path, default=Path("outputs/yolo"))
    parser.add_argument("--name", default="evaluation")
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args()


def build_summary(model: YOLO, metrics: Any, split: str) -> dict[str, Any]:
    names = model.names
    class_indices = [int(value) for value in metrics.box.ap_class_index]
    ap50 = [float(value) for value in metrics.box.ap50]
    per_class = {
        str(names[class_id]): {"mAP50": round(score, 6)}
        for class_id, score in zip(class_indices, ap50, strict=True)
    }
    return {
        "split": split,
        "precision": round(float(metrics.box.mp), 6),
        "recall": round(float(metrics.box.mr), 6),
        "mAP50": round(float(metrics.box.map50), 6),
        "mAP50_95": round(float(metrics.box.map), 6),
        "per_class": per_class,
    }


def main() -> None:
    args = parse_args()
    for path in (args.weights, args.data):
        if not path.is_file():
            raise FileNotFoundError(path)

    val_args: dict[str, Any] = {
        "data": str(args.data),
        "split": args.split,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": str(args.project),
        "name": args.name,
    }
    if args.device is not None:
        val_args["device"] = args.device

    model = YOLO(str(args.weights))
    metrics = model.val(**val_args)
    summary = build_summary(model, metrics, args.split)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
