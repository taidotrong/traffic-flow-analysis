# Dataset: Vehicles-COCO v2

## Nguồn và giấy phép

Dataset được xuất từ [Roboflow Universe](https://universe.roboflow.com/vehicle-mscoco/vehicles-coco/dataset/2) ngày 22/01/2023, có 18.998 ảnh và nhãn định dạng YOLOv8. Tệp nguồn ghi giấy phép CC BY 4.0.

Tiền xử lý được Roboflow áp dụng:

- tự động xoay ảnh theo EXIF và loại bỏ metadata orientation;
- resize kéo giãn về 480×480;
- không áp dụng augmentation.

## Các lớp

| ID | Lớp |
|---:|---|
| 0 | bus |
| 1 | car |
| 2 | motorcycle |
| 3 | truck |

## Split

Bộ tải ban đầu dùng tỷ lệ 70:20:10. Baseline chính gom lại toàn bộ cặp ảnh/nhãn, shuffle với seed 42 rồi chia 70:15:15:

| Split | Số ảnh | Tỷ lệ |
|---|---:|---:|
| Train | 13.298 | 70,0% |
| Validation | 2.849 | 15,0% |
| Test | 2.851 | 15,0% |
| Tổng | 18.998 | 100% |

## Phân bố nhãn

Thống kê trên cả ba split:

| Lớp | Số ảnh chứa lớp | Số bounding box | Tỷ lệ box |
|---|---:|---:|---:|
| car | 12.796 | 45.841 | 63,85% |
| truck | 6.396 | 10.438 | 14,54% |
| motorcycle | 3.680 | 9.149 | 12,74% |
| bus | 4.144 | 6.363 | 8,86% |
| Tổng | — | 71.791 | 100% |

Tỷ lệ lớp nhiều nhất/ít nhất xấp xỉ 7,2:1. Đây là mất cân bằng đáng kể và cần được cân nhắc khi phân tích theo lớp.

## Cấu trúc cần có

```text
vehicles-coco-701515/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

Mỗi dòng nhãn có dạng `class_id center_x center_y width height`, với bốn tọa độ được chuẩn hóa trong khoảng 0–1.

## Lấy dữ liệu

Có hai lựa chọn:

1. tải bản gốc từ Roboflow rồi tái lập bước chia 70:15:15 trong notebook `notebooks/yolov8n_70-15-15.ipynb`;
2. dùng thư mục `Dataset/Vehicles-COCO_701515` trong [Drive đồ án](https://drive.google.com/drive/folders/1WhcqICO5w6iVwbBcCYkPMXQf9-IvVZMs), nếu tài khoản có quyền.

Không commit dataset vào Git. Thư mục `data/` và các file archive đã được `.gitignore` loại trừ.

## Kiểm tra trước khi train

```bash
python src/inspect_dataset.py data/vehicles-coco-701515 \
  --output outputs/dataset_report.json
```

Kiểm tra thêm bằng mắt các ảnh/nhãn ngẫu nhiên, các box sát biên, class ID ngoài 0–3 và trùng lặp giữa các split. Bước chia hiện tại là random theo ảnh, chưa phải group split theo video/camera; nếu nhiều frame cùng video tồn tại, cần chia theo nhóm để tránh leakage.
