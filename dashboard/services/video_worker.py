# ============================================================
# video_worker.py - DIEU PHOI XU LY VIDEO STREAMING
# ------------------------------------------------------------
# Ghep tracker_service.py (YOLO + ByteTrack) va
# line_crossing_service.py (logic dem line-crossing), chay trong
# 1 THREAD RIENG de khong lam nghen luong xu ly HTTP chinh cua Flask.
#
# CHI CHEN THEM (khong doi gi khac so voi ban goc dang chay tot):
#   - self.current_fps: FPS da lam muot (EMA), doc tu app.py de
#     tra ve cho giao dien hien thi ngay duoi 3 nut dieu khien.
#   - Do thoi gian bao quanh TRON VEN 1 vong lap xu ly (doc frame
#     + detect + track + line-crossing + ve overlay), vi day moi
#     la con so phan anh dung kha nang "theo kip" video cua toan
#     bo pipeline, dung nhu tieu chi da quy dinh o muc 3.7.5.
#   - Gan "fps_tai_thoi_diem" vao TUNG su kien cat vach TRUOC KHI
#     goi on_event(event), de app.py ghi thang cot nay vao CSDL
#     ma KHONG can file log FPS rieng (tranh anh huong hieu nang
#     do them thao tac ghi dia moi frame).
#
# GHI CHU (khong sua code, chi ghi chu them de ro rang): video_path
# truyen vao co the la 1 duong dan file cuc bo (nguon local) HOAC
# 1 URL stream (vi du khi nguon la link YouTube da duoc
# services/youtube_service.py giai ma) - cv2.VideoCapture() xu ly
# duoc ca hai truong hop giong nhau nen KHONG can sua gi o day.
# ============================================================
import base64
import threading
import time

import cv2

from .tracker_service import TrackerService
from .line_crossing_service import LineCrossingSession, now_vn_timestamp_string

PURGE_INTERVAL_FRAMES = 200
DRAW_BOX_COLOR = (0, 255, 0)
DRAW_TEXT_COLOR = (0, 255, 0)
FPS_SMOOTHING_ALPHA = 0.2  # he so lam muot EMA cho FPS hien thi


class VideoWorker:
    """Quan ly 1 phien xu ly video streaming (1 thread rieng cho
    1 lan bam "Bat dau")."""

    def __init__(self, video_path, model_path, crossline_config, on_event,
                 tracker_factory=None, capture_factory=None):
        self.video_path = video_path
        self.model_path = model_path
        self.crossline_config = crossline_config
        self.on_event = on_event
        self._tracker_factory = tracker_factory or TrackerService
        self._capture_factory = capture_factory or cv2.VideoCapture

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = None
        self._frame_lock = threading.Lock()
        self._latest_frame_b64 = None

        self.frame_index = 0
        self.video_ended = False
        self.error_message = None
        # ---- CHI CHEN THEM: bien luu FPS da lam muot ----
        self.current_fps = 0.0

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self, timeout=5):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def pause(self):
        self._pause_event.set()

    def resume(self):
        self._pause_event.clear()

    def is_paused(self):
        return self._pause_event.is_set()

    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()

    def get_latest_frame_base64(self):
        with self._frame_lock:
            return self._latest_frame_b64

    def _set_latest_frame(self, frame):
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            return
        b64 = base64.b64encode(buffer).decode("utf-8")
        with self._frame_lock:
            self._latest_frame_b64 = f"data:image/jpeg;base64,{b64}"

    def _draw_detections(self, frame, detections):
        """Chi ve bounding box + nhan "loai_xe #track_id" - Cross-Line
        van do client-side canvas overlay tu ve de len tren."""
        for det in detections:
            x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
            label = f"{det['class_name']} #{det['track_id']}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), DRAW_BOX_COLOR, 2)
            cv2.putText(
                frame, label, (x1, max(y1 - 6, 0)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, DRAW_TEXT_COLOR, 2
            )
        return frame

    def _run_loop(self):
        cap = None
        try:
            cap = self._capture_factory(self.video_path)
            if not cap.isOpened():
                self.error_message = f"Không thể mở video: {self.video_path}"
                return

            tracker = self._tracker_factory(self.model_path)
            session = LineCrossingSession(
                x1=self.crossline_config["x1"],
                y1=self.crossline_config["y1"],
                x2=self.crossline_config["x2"],
                y2=self.crossline_config["y2"],
                huong_1_label=self.crossline_config["huong_1_label"],
                huong_2_label=self.crossline_config["huong_2_label"],
            )

            # ---- CHI CHEN THEM: bien noi bo cho EMA cua FPS ----
            ema_fps = None

            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    time.sleep(0.05)
                    continue

                # ---- CHI CHEN THEM: danh dau thoi diem BAT DAU vong lap ----
                t_start = time.perf_counter()

                ret, frame = cap.read()
                if not ret:
                    self.video_ended = True
                    break

                self.frame_index += 1
                detections = tracker.process_frame(frame)

                for det in detections:
                    event = session.process_detection(
                        det["track_id"], det["class_name"],
                        det["cx"], det["cy"], self.frame_index,
                    )
                    if event is not None:
                        event["timestamp"] = now_vn_timestamp_string()
                        # ---- CHI CHEN THEM: gan FPS da lam muot vao su
                        # kien TRUOC khi day ra ngoai qua callback ----
                        event["fps_tai_thoi_diem"] = round(ema_fps, 2) if ema_fps else 0.0
                        self.on_event(event)

                if self.frame_index % PURGE_INTERVAL_FRAMES == 0:
                    session.purge_stale(self.frame_index)

                annotated = self._draw_detections(frame, detections)
                self._set_latest_frame(annotated)

                # ---- CHI CHEN THEM: tinh FPS tuc thoi cua TRON VEN
                # vong lap nay (doc frame+detect+track+line-crossing+
                # ve overlay), roi lam muot bang EMA truoc khi luu ----
                t_end = time.perf_counter()
                processing_time_ms = (t_end - t_start) * 1000
                fps_instant = 1000.0 / processing_time_ms if processing_time_ms > 0 else 0.0
                ema_fps = fps_instant if ema_fps is None else (
                    FPS_SMOOTHING_ALPHA * fps_instant + (1 - FPS_SMOOTHING_ALPHA) * ema_fps
                )
                self.current_fps = round(ema_fps, 1)

        except Exception as e:
            self.error_message = str(e)
        finally:
            if cap is not None:
                cap.release()
