# ============================================================
# tracker_service.py - WRAPPER CHO YOLOv8 + ByteTrack (STREAMING)
# ------------------------------------------------------------
# Refactor tu Cell 3+4 cua bytetrack.pdf, chuyen tu goi model.track()
# 1 lan cho ca video sang goi TUNG FRAME MOT (streaming).
#
# "ultralytics" va "torch" duoc import LAZY (chi import ben trong
# ham can dung), de cac ham thuan tuy (chuan hoa ten lop...) van
# unit test duoc ma khong can may co GPU/cai dat thu vien AI.
# ============================================================
import os

CLASS_NAME_FIXES = {
    "motobyte": "motorbike",
    "motobike": "motorbike",
    "motorbike": "motorbike",
    "motorcycle": "motorbike",
    "car": "car",
    "bus": "bus",
    "truck": "truck",
}


def normalize_class_name(raw_class_name):
    if not raw_class_name:
        return raw_class_name
    key = raw_class_name.strip().lower()
    return CLASS_NAME_FIXES.get(key, key)


def compute_center(x1, y1, x2, y2):
    """GIONG HET cong thuc trong Cell 4 cua bytetrack.pdf."""
    return (x1 + x2) // 2, (y1 + y2) // 2


def find_model_path(model_dir):
    """Tim file model (.pt) trong thu muc da mount (MODEL_DIR).
    Uu tien "best.pt"; neu khong co, lay file .pt dau tien theo
    bang chu cai."""
    if not os.path.isdir(model_dir):
        return None
    preferred = os.path.join(model_dir, "best.pt")
    if os.path.exists(preferred):
        return preferred
    pt_files = sorted(
        f for f in os.listdir(model_dir) if f.lower().endswith(".pt")
    )
    if pt_files:
        return os.path.join(model_dir, pt_files[0])
    return None


class TrackerService:
    """Wrapper cho model YOLOv8 + ByteTrack, xu ly TUNG FRAME MOT."""

    def __init__(self, model_path):
        self.model_path = model_path
        self._model = None
        self._device = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        import torch
        from ultralytics import YOLO

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Khong tim thay file model: {self.model_path}"
            )
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = YOLO(self.model_path)

    def process_frame(self, frame):
        """Xu ly 1 frame (anh numpy BGR), tra ve list cac phuong
        tien phat hien duoc kem track_id (persist=True giu ID on
        dinh giua cac lan goi lien tiep - giong Cell 4 bytetrack.pdf)."""
        self._ensure_loaded()
        results = self._model.track(
            frame,
            tracker="bytetrack.yaml",
            persist=True,
            device=self._device,
            verbose=False,
        )
        detections = []
        if not results:
            return detections
        res = results[0]
        if res.boxes is None or res.boxes.id is None:
            return detections
        boxes = res.boxes.xyxy.cpu().numpy().astype(int)
        ids = res.boxes.id.cpu().numpy().astype(int)
        clss = res.boxes.cls.cpu().numpy().astype(int)
        names = res.names if hasattr(res, "names") else self._model.names
        for (x1, y1, x2, y2), track_id, cls_idx in zip(boxes, ids, clss):
            cx, cy = compute_center(x1, y1, x2, y2)
            raw_class_name = names.get(int(cls_idx), str(cls_idx))
            class_name = normalize_class_name(raw_class_name)
            detections.append({
                "track_id": int(track_id),
                "class_name": class_name,
                "cx": int(cx),
                "cy": int(cy),
                "x1": int(x1), "y1": int(y1),
                "x2": int(x2), "y2": int(y2),
            })
        return detections
