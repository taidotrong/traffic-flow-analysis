# Tổng hợp thí nghiệm baseline

## 1. YOLOv8n, split 70:20:10

Mô hình YOLOv8n pretrained COCO được huấn luyện trên Google Colab/Tesla T4 với ảnh 640, batch 16. Hai mốc 10 và 20 epoch dùng để có baseline nhanh.

### Validation

| Chỉ số | 10 epoch | 20 epoch | Cải thiện theo báo cáo |
|---|---:|---:|---:|
| mAP@0.5 | 0.601 | 0.635 | +5,7% |
| mAP@0.5:0.95 | 0.406 | 0.432 | +6,4% |
| Precision | 0.674 | 0.708 | +5,0% |
| Recall | 0.526 | 0.556 | +5,7% |

CSV gốc ở `results/yolov8n/train_10_epochs.csv` và `train_20_epochs.csv`. Giá trị cuối epoch trong CSV có thể lệch vài phần nghìn so với bảng báo cáo do bảng dùng checkpoint/bản tổng hợp đã làm tròn.

### Test của mô hình 20 epoch

Tập test có 1.900 ảnh / 7.036 đối tượng.

| Chỉ số | Giá trị |
|---|---:|
| Precision | 0.7191 |
| Recall | 0.5794 |
| mAP@0.5 | 0.6591 |
| mAP@0.5:0.95 | 0.4580 |

| Lớp | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|
| bus | 0.791 | 0.740 | 0.811 | 0.663 |
| car | 0.722 | 0.552 | 0.632 | 0.400 |
| motorcycle | 0.755 | 0.551 | 0.645 | 0.391 |
| truck | 0.609 | 0.475 | 0.549 | 0.379 |

Log ghi 3,9 ms inference/ảnh trên Tesla T4, không tính đầy đủ tiền/hậu xử lý và I/O.

## 2. YOLOv8n, split 70:15:15, tối đa 100 epoch

Cấu hình:

- pretrained `yolov8n.pt`;
- 100 epoch, patience 20;
- ảnh 640, batch 16, seed 42, deterministic;
- Google Colab, Tesla T4;
- thời gian train 23.833 giây, tương đương khoảng 6,62 giờ.

Early stopping không kích hoạt vì metric vẫn cải thiện nhỏ. Checkpoint tốt nhất theo mAP@0.5:0.95 validation xuất hiện ở epoch 95:

| Chỉ số validation | 20 epoch (split cũ) | 100 epoch (split mới) |
|---|---:|---:|
| Precision | 0.708 | 0.7258 |
| Recall | 0.556 | 0.5975 |
| mAP@0.5 | 0.635 | 0.6794 |
| mAP@0.5:0.95 | 0.432 | 0.4731 |

Hai cột dùng split khác nhau, nên chỉ nên đọc như xu hướng thí nghiệm, không phải ablation được kiểm soát hoàn toàn.

### Test độc lập

Tập test có 2.851 ảnh / 10.683 đối tượng.

| Chỉ số | Validation | Test |
|---|---:|---:|
| Precision | 0.7258 | 0.7420 |
| Recall | 0.5975 | 0.6069 |
| mAP@0.5 | 0.6794 | 0.6862 |
| mAP@0.5:0.95 | 0.4731 | 0.4798 |

| Lớp test | Ảnh | Đối tượng | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|---:|
| bus | 656 | 973 | 0.799 | 0.744 | 0.8162 | 0.660 |
| car | 1.937 | 6.901 | 0.742 | 0.582 | 0.6599 | 0.424 |
| motorcycle | 531 | 1.245 | 0.806 | 0.622 | 0.7188 | 0.453 |
| truck | 940 | 1.564 | 0.621 | 0.480 | 0.5500 | 0.383 |

Log test ghi 1,2 ms preprocess, 3,7 ms inference và 1,3 ms postprocess mỗi ảnh. Quy đổi riêng inference là khoảng 270 FPS; đây không phải tốc độ pipeline video end-to-end.

### Hội tụ

- mAP tăng nhanh trong khoảng 40 epoch đầu.
- Khoảng epoch 59 đạt xấp xỉ 99% mAP tốt nhất.
- Từ epoch 60 đến 100, mAP@0.5 tăng khoảng 0,006.
- Với mục tiêu tiết kiệm thời gian, 60–70 epoch là điểm dừng hợp lý; checkpoint báo cáo tốt nhất vẫn lấy từ run 100 epoch.

Loss train giảm đều, còn loss validation gần như đi ngang về cuối. Không thấy dấu hiệu suy giảm test trong run này, nhưng kết luận “không overfit” nên được hiểu trong phạm vi một split; cần cross-validation hoặc dữ liệu ngoài miền để khẳng định mạnh hơn.

## 3. SSDlite320-MobileNetV3-Large

Notebook đối chứng dùng `torchvision.models.detection.ssdlite320_mobilenet_v3_large`, thay classification head thành năm lớp (bốn lớp xe + background), ảnh 320, batch 16, SGD, cosine scheduler và dự kiến 50 epoch.

Drive hiện có `best.pt` và `last.pt` (mỗi file khoảng 9,28 MB), nhưng notebook được lưu với 0/8 code cell đã thực thi và bảng so sánh vẫn để trống mAP/FPS. Vì vậy repository không công bố số liệu SSD như một kết quả đã kiểm chứng.

Để hoàn tất so sánh, cần chạy lại notebook trên đúng split 70:15:15, lưu `history`, metric test, phiên bản thư viện và thời gian inference với cùng quy ước đo như YOLO.

## 4. Kết luận thực nghiệm

- YOLOv8n là baseline đã được xác nhận, nhỏ (khoảng 3,0 triệu tham số, 8,1 GFLOPs) và đủ nhanh cho bước phát hiện thời gian thực trên GPU.
- `bus` dễ nhất; `truck` khó nhất, cho thấy độ đa dạng hình dạng/nhầm lớp quan trọng không kém số lượng mẫu.
- Dataset imbalance là rủi ro chính cần xử lý ở giai đoạn cải thiện.
- Chưa có bằng chứng định lượng để xếp hạng SSD-MobileNet so với YOLOv8n.
