# Tài liệu tham khảo

Danh mục đánh số theo cách trình bày IEEE, phục vụ báo cáo đồ án Traffic Flow Analysis. Các nguồn trực tuyến được đối chiếu ngày **28/10/2026**. Nếu môn học có mẫu riêng, giữ thông tin nguồn và đổi cách trình bày theo mẫu của giảng viên. Có thể nhập [tệp BibTeX](references.bib) vào Zotero, Mendeley hoặc dùng với LaTeX.

## 1. Danh mục

<a id="ref-1"></a>
**[1]** J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, “You Only Look Once: Unified, Real-Time Object Detection,” in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 779–788. [Bản công bố CVF](https://openaccess.thecvf.com/content_cvpr_2016/html/Redmon_You_Only_Look_CVPR_2016_paper.html).

Dùng cho cơ sở lý thuyết về họ mô hình YOLO và phát hiện đối tượng một giai đoạn. Đây là bài YOLO gốc; mô hình chạy trong đồ án là YOLOv8n ở [2].

<a id="ref-2"></a>
**[2]** G. Jocher, A. Chaurasia, and J. Qiu, *Ultralytics YOLOv8*, phần mềm, 2023. [Tài liệu và hướng dẫn trích dẫn chính thức](https://docs.ultralytics.com/models/yolov8); [mã nguồn phiên bản dùng trong repo, v8.4.116](https://github.com/ultralytics/ultralytics/tree/v8.4.116). Truy cập: 28/10/2026.

Dùng khi giới thiệu YOLOv8n, pretrained weights và thư viện huấn luyện/suy luận. Năm 2023 là năm giới thiệu YOLOv8; phiên bản thư viện được ghim trong repo là 8.4.116. Ultralytics cung cấp cách trích dẫn phần mềm và cho biết chưa phát hành bài báo nghiên cứu chính thức riêng cho YOLOv8; không tự tạo tên hội nghị hoặc DOI cho phiên bản này.

<a id="ref-3"></a>
**[3]** Y. Zhang et al., “ByteTrack: Multi-object Tracking by Associating Every Detection Box,” in *Computer Vision – ECCV 2022*, 2022, pp. 1–21, doi: [10.1007/978-3-031-20047-2_1](https://doi.org/10.1007/978-3-031-20047-2_1). [Bài báo truy cập mở tại ECVA](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136820001.pdf); [mã nguồn tác giả](https://github.com/FoundationVision/ByteTrack).

Dùng cho thuật toán tracking và liên kết detection với tracklet. Dashboard gọi bản triển khai ByteTrack thông qua Ultralytics, với `tracker="bytetrack.yaml"` và `persist=True`; API tích hợp được dẫn ở [12].

<a id="ref-4"></a>
**[4]** T.-Y. Lin et al., “Microsoft COCO: Common Objects in Context,” in *Computer Vision – ECCV 2014*, 2014, pp. 740–755, doi: [10.1007/978-3-319-10602-1_48](https://doi.org/10.1007/978-3-319-10602-1_48). [Thông tin bản công bố](https://link.springer.com/chapter/10.1007/978-3-319-10602-1_48).

Dùng khi giải thích COCO và bối cảnh pretrained COCO. Bộ Vehicles-coco được tải và dùng cho đồ án phải được ghi nguồn riêng ở [5].

<a id="ref-5"></a>
**[5]** Vehicle MSCOCO, “Vehicles-coco Computer Vision Dataset,” phiên bản 2, *Roboflow Universe*, 2022. [Trang bộ dữ liệu v2](https://universe.roboflow.com/vehicle-mscoco/vehicles-coco/dataset/2). Giấy phép ghi trên trang: CC BY 4.0. Truy cập: 28/10/2026.

Trang v2 ghi ngày tạo 23/01/2022, 18.998 ảnh, split gốc 70:20:10 và resize 480×480. Split 70:15:15 trong repo là bước xử lý của nhóm; các số lượng sau khi chia lại và thống kê nhãn phải dẫn tới notebook/log của nhóm trong [dataset.md](dataset.md), thay vì gán cho trang Roboflow.

<a id="ref-6"></a>
**[6]** W. Liu et al., “SSD: Single Shot MultiBox Detector,” in *Computer Vision – ECCV 2016*, 2016, pp. 21–37, doi: [10.1007/978-3-319-46448-0_2](https://doi.org/10.1007/978-3-319-46448-0_2). [Bản tác giả trên arXiv:1512.02325](https://arxiv.org/abs/1512.02325).

Dùng cho nguyên lý SSD, default boxes và phát hiện ở nhiều mức đặc trưng của mô hình đối chứng.

<a id="ref-7"></a>
**[7]** M. Sandler, A. Howard, M. Zhu, A. Zhmoginov, and L.-C. Chen, “MobileNetV2: Inverted Residuals and Linear Bottlenecks,” in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2018, pp. 4510–4520. [Bản tác giả trên arXiv:1801.04381](https://arxiv.org/abs/1801.04381).

Dùng khi trình bày thiết kế mạng nhẹ và SSDLite. Bài này mô tả SSDLite; backbone của mô hình đối chứng đang dùng là MobileNetV3-Large [8], [9].

<a id="ref-8"></a>
**[8]** A. Howard et al., “Searching for MobileNetV3,” in *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, 2019. [Bản tác giả trên arXiv:1905.02244](https://arxiv.org/abs/1905.02244).

Dùng cho MobileNetV3-Large và lựa chọn backbone nhẹ của mô hình đối chứng.

<a id="ref-9"></a>
**[9]** PyTorch Contributors, “ssdlite320_mobilenet_v3_large,” *Torchvision Documentation*. [Tài liệu mô hình chính thức](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.ssdlite320_mobilenet_v3_large.html). Truy cập: 28/10/2026.

Dùng cho cấu hình triển khai thực tế: SSDlite, đầu vào 320×320, backbone MobileNetV3-Large và `num_classes` có tính lớp background. Repo có notebook đối chứng dùng đúng API này.

<a id="ref-10"></a>
**[10]** S. J. Pan and Q. Yang, “A Survey on Transfer Learning,” *IEEE Transactions on Knowledge and Data Engineering*, vol. 22, no. 10, pp. 1345–1359, 2010. [Bản tác giả tại HKUST](https://home.cse.ust.hk/~qyang/Docs/2009/tkde_transfer_learning.pdf); [danh mục công bố của tác giả](https://home.cse.ust.hk/~qyang/publications.html).

Dùng cho cơ sở lý thuyết học chuyển giao và khác biệt miền dữ liệu. Việc so sánh COCO→HCMC với COCO→CanTho→HCMC là thiết kế thí nghiệm trong notebook của nhóm; nguồn này không chứng minh một lộ trình sẽ tốt hơn lộ trình kia.

<a id="ref-11"></a>
**[11]** A. Paszke et al., “PyTorch: An Imperative Style, High-Performance Deep Learning Library,” in *Advances in Neural Information Processing Systems*, vol. 32, 2019. [Bản công bố NeurIPS](https://papers.neurips.cc/paper_files/paper/2019/hash/bdbca288fee7f92f2bfa9f7012727740-Abstract.html).

Dùng khi mô tả nền tảng tensor, huấn luyện và suy luận của các mô hình.

<a id="ref-12"></a>
**[12]** Ultralytics, “Multi-Object Tracking with Ultralytics YOLO,” *Ultralytics Documentation*. [Tài liệu chế độ tracking](https://docs.ultralytics.com/modes/track). Truy cập: 28/10/2026.

Dùng để dẫn API `model.track`, cấu hình ByteTrack và duy trì track giữa các frame. Tài liệu trực tuyến thay đổi theo thời gian; cấu hình thực tế của đồ án nằm trong `dashboard/services/tracker_service.py` và thư viện được ghim ở v8.4.116.

<a id="ref-13"></a>
**[13]** Ultralytics, “Performance Metrics Deep Dive,” *Ultralytics Documentation*. [Hướng dẫn chỉ số đánh giá](https://docs.ultralytics.com/guides/yolo-performance-metrics). Truy cập: 28/10/2026.

Dùng khi giải thích precision, recall, IoU, AP và mAP. Các giá trị mAP/FPS của đồ án phải lấy từ log của nhóm, có split và môi trường chạy tương ứng; không lấy bảng benchmark bên ngoài làm kết quả của nhóm.

<a id="ref-14"></a>
**[14]** OpenCV, “cv::VideoCapture Class Reference,” *OpenCV Documentation*. [Tài liệu đọc video](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html). Truy cập: 28/10/2026.

Dùng khi mô tả đọc video, lấy frame và giải phóng tài nguyên trong worker.

<a id="ref-15"></a>
**[15]** Pallets, “Flask Documentation,” phiên bản tài liệu 3.1.x. [Tài liệu Flask chính thức](https://flask.palletsprojects.com/en/stable/). Truy cập: 28/10/2026.

Dùng cho tầng web, HTTP routes, templates và JSON API của dashboard.

<a id="ref-16"></a>
**[16]** SQLite, “SQLite Documentation.” [Tài liệu SQLite chính thức](https://www.sqlite.org/docs.html). Truy cập: 28/10/2026.

Dùng cho lưu trữ sự kiện đếm xe, truy vấn thống kê và lịch sử phiên bằng SQLite.

<a id="ref-17"></a>
**[17]** N. Bui, H. Yi, and J. Cho, “A Vehicle Counts by Class Framework Using Distinguished Regions Tracking at Multiple Intersections,” in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops*, 2020, pp. 578–579. [Bản công bố CVF](https://openaccess.thecvf.com/content_CVPRW_2020/html/w35/Bui_A_Vehicle_Counts_by_Class_Framework_Using_Distinguished_Regions_Tracking_CVPRW_2020_paper.html).

Dùng ở mục nghiên cứu liên quan về đếm phương tiện kết hợp detection và tracking. Bài sử dụng các thành phần và quy tắc vùng riêng; repo hiện không triển khai lại phương pháp của bài này.

## 2. Đặt trích dẫn vào báo cáo

| Nội dung báo cáo | Nguồn phù hợp | Bằng chứng của riêng đồ án |
|---|---|---|
| Tổng quan phát hiện đối tượng và lựa chọn YOLOv8n | [1], [2] | `src/train_yolo.py`, cấu hình và log huấn luyện |
| Dữ liệu COCO và Vehicles-coco | [4], [5] | `docs/dataset.md`, notebook chia lại dữ liệu |
| Học chuyển giao COCO→CanTho→HCMC | [10], [2] | `notebooks/fine_tuning/`, seed và cấu hình từng run |
| Mô hình đối chứng SSDlite-MobileNetV3 | [6]–[9], [11] | `notebooks/ssd_mobilenet.ipynb` |
| Tracking, ID và liên kết detection | [3], [12] | `dashboard/services/tracker_service.py` |
| Nghiên cứu liên quan về đếm xe | [17] | Mô tả rõ phần nhóm tự xây dựng và phần tham khảo |
| Quy tắc đếm qua vạch hai hướng | [3], [12] cho đầu vào tracking | `line_crossing_service.py`; kiểm tra đổi dấu phía của tâm xe, majority vote và chống đếm lặp do nhóm triển khai |
| Precision, recall, mAP và quy ước đo tốc độ | [13] | `results/yolov8n/`, `docs/experiments.md`, `docs/validation.md` |
| Kiến trúc video worker, web và CSDL | [14]–[16] | `dashboard/app.py`, `dashboard/services/video_worker.py` |

Ví dụ diễn đạt có thể chỉnh theo nội dung báo cáo:

> Nhóm sử dụng YOLOv8n từ thư viện Ultralytics để phát hiện phương tiện [2]. Các detection được liên kết qua các frame bằng ByteTrack [3], thông qua API tracking của Ultralytics [12]. Trên các quỹ đạo thu được, nhóm triển khai quy tắc đếm qua vạch dựa trên sự thay đổi phía của tâm đối tượng và chỉ ghi một sự kiện cho mỗi track trong một phiên.

> Bộ Vehicles-coco v2 được cung cấp qua Roboflow Universe [5], còn COCO được mô tả trong công trình của Lin và cộng sự [4]. Nhóm chia lại dữ liệu theo tỷ lệ 70:15:15 với seed 42; số ảnh và kết quả đánh giá của phép chia này được báo cáo từ notebook và log thí nghiệm của nhóm.

## 3. Nguồn cần bổ sung từ hồ sơ dữ liệu

Notebook hiện cho thấy tên thư mục `CanTho_701515` và `Vehicle Counting AIC HCMC 2020.v1i.yolov8_701515`, nhưng chưa ghi đủ URL nguồn gốc, tác giả/đơn vị cung cấp, phiên bản, giấy phép và quy trình tạo nhãn. Chưa đủ căn cứ để đồng nhất bộ HCMC này với dữ liệu của một cuộc thi chỉ dựa vào tên thư mục.

Trước khi nộp báo cáo, bổ sung cho mỗi bộ CanTho/HCMC: trang công bố hoặc đơn vị cung cấp; phiên bản/ngày nhận; điều kiện sử dụng; số ảnh, lớp và cách gán nhãn; cách chia train/validation/test. Với video mẫu, ghi người cung cấp hoặc URL video gốc, thời điểm/địa điểm ghi hình nếu biết và phạm vi được phép sử dụng. Nếu nhóm tự thu thập, mô tả quy trình và ghi rõ dữ liệu do nhóm xây dựng. Các mục này cần bằng chứng từ hồ sơ dữ liệu; danh mục trên không tự gán nguồn thay thế.

Các bảng điểm số của đồ án là kết quả nội bộ, cần dẫn log/notebook tương ứng. Việc trích dẫn một thuật toán hoặc thư viện không đồng nghĩa với việc đã tái lập kết quả benchmark của tác giả.
