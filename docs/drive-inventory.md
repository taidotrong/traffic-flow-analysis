# Kiểm kê nguồn Google Drive

Nguồn được kiểm kê từ [thư mục Drive đồ án](https://drive.google.com/drive/folders/1WhcqICO5w6iVwbBcCYkPMXQf9-IvVZMs) ngày 09/08/2026.

## Cây nguồn chính

```text
Drive root
├── NỘP THẦY/
│   ├── CODE-YOLOv8n/
│   │   ├── Vehicles-COCO_702010.ipynb
│   │   └── Vehicles_COCO_701515.ipynb
│   ├── BÁO CÁO THỬ NGHIỆM BASELINE-Tuần 1.docx
│   ├── BÁO CÁO THỬ NGHIỆM BASELINE-Tuần 2.docx
│   ├── Ketqua_Baseline/
│   └── Dataset/
├── Baseline/
│   ├── CODE-YOLOv8n/
│   ├── SSD_MobileNet/SSD_MobileNet.ipynb
│   ├── Ketqua_Baseline/YOLOv8n/
│   ├── Ketqua_SSD_MobileNet/{best.pt,last.pt}
│   └── hai báo cáo DOCX
└── Dataset/
    ├── Vehicles-COCO_702010/
    │   ├── Vehicles-coco.v2i.yolov8/
    │   └── Vehicles-coco.v2i.yolov8.zip (861.900.452 byte)
    └── Vehicles-COCO_701515/{train,valid,test}/
```

`NỘP THẦY` chứa bản sao phục vụ nộp bài; `Baseline` và `Dataset` là nguồn rõ ràng hơn để dựng repository. Các notebook/báo cáo bị trùng không được đưa vào Git hai lần.

## Ánh xạ vào repository

| Nguồn Drive | Trong repo | Quyết định |
|---|---|---|
| Hai notebook YOLO | `notebooks/` | Giữ để tái lập lịch sử thí nghiệm |
| Notebook SSD-MobileNet | `notebooks/ssd_mobilenet.ipynb` | Giữ nhưng ghi rõ chưa có output |
| Báo cáo tuần 1/2 | `docs/experiments.md` | Tổng hợp thành Markdown thay vì commit DOCX trùng |
| `results.csv` 10/20/100 epoch | `results/yolov8n/` | Giữ vì nhỏ và hữu ích để kiểm chứng |
| Biểu đồ loss/mAP tổng hợp | `assets/results/` | Giữ để hiển thị trong README |
| Dataset và ZIP | Không đưa vào Git | Quá lớn; có nguồn/giấy phép riêng |
| `best.pt`, `last.pt` | Không đưa vào Git | Binary artefact; liên kết trong `models/README.md` |
| Ảnh batch/curve/confusion matrix lặp lại | Không đưa vào bản gọn | Có thể thêm sau nếu cần báo cáo trực quan đầy đủ |

## Tệp lớn đã loại trừ

- Dataset ZIP: khoảng 861,9 MB.
- Dataset đã giải nén: 18.998 ảnh và nhãn.
- YOLOv8n `best.pt`/`last.pt`: khoảng 6,26 MB mỗi file.
- SSD-MobileNet `best.pt`/`last.pt`: khoảng 9,28 MB mỗi file.

GitHub chặn file đơn lớn hơn 100 MB. Trọng số dưới giới hạn nhưng vẫn được tách khỏi source để repo nhẹ và tránh commit binary thay đổi thường xuyên. Nếu cần versioning trọng số, dùng Git LFS hoặc GitHub Releases.

## Việc cần người sở hữu xác nhận trước khi public

1. Chọn giấy phép cho mã nguồn.
2. Xác nhận tên đồ án, tên nhóm/tác giả và thông tin môn học muốn hiển thị.
3. Quyết định để Drive weight ở chế độ công khai, dùng GitHub Release hay Git LFS.
4. Kiểm tra quyền sử dụng mọi ảnh minh họa ngoài dataset CC BY 4.0.
