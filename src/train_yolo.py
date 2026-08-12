#!/usr/bin/env python3
"""Train a reproducible Ultralytics YOLO vehicle detector."""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Ultralytics dataset YAML")
    parser.add_argument("--model", default="yolov8n.pt", help="Checkpoint or model name")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--device", default=None, help="For example 0, cpu, mps; auto when omitted")
    parser.add_argument("--project", type=Path, default=Path("outputs/yolo"))
    parser.add_argument("--name", default="baseline_100epochs_es")
    parser.add_argument("--cache", action="store_true", help="Cache dataset when memory/disk permits")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.data.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {args.data}")

    train_args = {
        "data": str(args.data),
        "epochs": args.epochs,
        "patience": args.patience,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "seed": args.seed,
        "deterministic": True,
        "workers": args.workers,
        "project": str(args.project),
        "name": args.name,
        "cache": args.cache,
    }
    if args.device is not None:
        train_args["device"] = args.device

    model = YOLO(args.model)
    model.train(**train_args)


if __name__ == "__main__":
    main()
