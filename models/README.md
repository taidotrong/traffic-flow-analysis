# Model weights

Các file `*.pt` không được commit vào repository. Tải chúng từ Drive rồi đổi tên/đặt vào thư mục này:

| Model | Artefact | Nguồn Drive | Tên đề xuất |
|---|---|---|---|
| YOLOv8n 70:15:15, 100 epoch | best.pt (~6,26 MB) | [Tải](https://drive.google.com/file/d/1cRJBcXMJtlIBElvux_L476T_YHHjSUK6/view) | `yolov8n_701515_best.pt` |
| YOLOv8n 70:15:15, 100 epoch | last.pt (~6,26 MB) | [Tải](https://drive.google.com/file/d/1xsTZaOepCf8xUS0iESh4esvo8HfblUez/view) | `yolov8n_701515_last.pt` |
| SSDlite320-MobileNetV3 | best.pt (~9,28 MB) | [Tải](https://drive.google.com/file/d/1ek3L3mvlbHb4WF6yA2eTXvLHkkW6y5_1/view) | `ssdlite320_mobilenetv3_best.pt` |
| SSDlite320-MobileNetV3 | last.pt (~9,28 MB) | [Tải](https://drive.google.com/file/d/1M1VM6-d6fmCXZ0awFwqAvHudUm_rM98W/view) | `ssdlite320_mobilenetv3_last.pt` |

Các URL có thể yêu cầu quyền Drive. Trước khi phát hành public, nên chuyển checkpoint đã chọn sang GitHub Release hoặc kho artefact có version, kèm SHA-256 và thông tin model/dataset.

Lưu ý: checkpoint SSD tồn tại nhưng chưa có log test đã lưu trong nguồn; không dùng nó để khẳng định kết quả định lượng trước khi đánh giá lại.
