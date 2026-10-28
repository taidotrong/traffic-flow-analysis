#!/usr/bin/env python3
"""Validate notebook structure and compile cells after IPython transformation.

This does not execute Colab mounts, downloads, training or evaluation.
"""
import warnings
from pathlib import Path

import nbformat
from IPython.core.inputtransformer2 import TransformerManager


def main():
    transform = TransformerManager()
    root = Path(__file__).resolve().parents[1]
    cells = 0
    failures = []
    notebooks = sorted((root / 'notebooks').rglob('*.ipynb'))
    for path in notebooks:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', nbformat.warnings.MissingIDFieldWarning)
            notebook = nbformat.read(path, as_version=4)
            nbformat.validate(notebook)
        for index, cell in enumerate(notebook.cells, start=1):
            if cell.cell_type != 'code' or not cell.source.strip():
                continue
            try:
                compile(transform.transform_cell(cell.source), f'{path.name}:cell{index}', 'exec')
            except SyntaxError as exc:
                failures.append(f'{path.relative_to(root)} cell {index}: {exc}')
            cells += 1
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'Validated {len(notebooks)} notebooks and compiled {cells} code cells; no training executed.')


if __name__ == '__main__':
    main()
