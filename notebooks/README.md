# Notebooks

- `yolov8n_70-20-10.ipynb`: thử nghiệm YOLOv8n 10/20 epoch trên split gốc 70:20:10 và đánh giá test.
- `yolov8n_70-15-15.ipynb`: gom dữ liệu, chia lại 70:15:15 với seed 42, train tối đa 100 epoch, thống kê imbalance và đánh giá test.
- `ssd_mobilenet.ipynb`: pipeline đối chứng SSDlite320-MobileNetV3; notebook nguồn chưa lưu execution output.

Đây là các artefact Colab gốc nên còn đường dẫn `/content/drive/MyDrive/Do an AI giao thong/...`. Khi chạy trong Drive khác, sửa các biến `src`, `dst`, `BASE` và `ROOT`. Với môi trường local/CI, ưu tiên các CLI trong `src/`.

## Updated Drive sources (28 October 2026)

- `fine_tuning/`: all ten notebooks from `Fine-Tune`, including seeds 1407/1712 for COCO→Can Tho→HCMC, sequential-vs-direct ablation and comparison notebooks.
- `tracking/`: `BYTETRACK.ipynb` and `LINE-CROSSING.ipynb` from `DASHBOARD-DEMO/Source AI`; the same-size copies under `Tracking-LineCrossing/Code` were not duplicated.
- `database/`: `SQLite.ipynb` from `SQLite/Code` and `Viec_CDE.ipynb` from the project root.

All 17 repository notebooks pass nbformat structure validation and syntax compilation of 148 nonempty code cells after IPython transformation. Two imported notebooks contained invalid `metadata` on stream output objects; only that unsupported field was removed. Existing outputs and code are preserved. These checks do not execute the notebooks or reproduce model accuracy. Colab mounts, datasets, GPU training and experiment evaluation still require their original external inputs.
