# Notebooks

- `yolov8n_70-20-10.ipynb`: thử nghiệm YOLOv8n 10/20 epoch trên split gốc 70:20:10 và đánh giá test.
- `yolov8n_70-15-15.ipynb`: gom dữ liệu, chia lại 70:15:15 với seed 42, train tối đa 100 epoch, thống kê imbalance và đánh giá test.
- `ssd_mobilenet.ipynb`: pipeline đối chứng SSDlite320-MobileNetV3; notebook nguồn chưa lưu execution output.

Đây là các artefact Colab gốc nên còn đường dẫn `/content/drive/MyDrive/Do an AI giao thong/...`. Khi chạy trong Drive khác, sửa các biến `src`, `dst`, `BASE` và `ROOT`. Với môi trường local/CI, ưu tiên các CLI trong `src/`.
