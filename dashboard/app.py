# ============================================================
# app.py - DASHBOARD HE THONG DEM XE (BAN CHAY TRONG DOCKER)
# ------------------------------------------------------------
# LOGIC QUAN LY PHIEN DEM XE:
#
#   - Neu CHUA tung chon CSDL nao (hoac CSDL dang dung la loai
#     "tu dong sinh"), moi lan bam "Bat dau" se TU DONG TAO 1
#     thu muc con moi trong DATA_DIR, dat ten theo dinh dang
#     "dd-mm-yyyy HHMMSS", ben trong chua "he_thong_dem_xe.db"
#     va "crossline_config.json" rieng cho phien do.
#
#   - Neu nguoi dung CHU DONG chon 1 file CSDL co san qua dropdown
#     "Co so du lieu (CSDL)", lan bam "Bat dau" tiep theo se GHI
#     TIEP vao dung file do (cong don), KHONG tao moi.
#
#   - Nut "Dung": mo khoa lai Cross-Line, VA TU DONG NGAT KET NOI
#     CSDL hien tai (xoa db_path, dropdown ve lai "-- Chon
#     database --").
#
#   - Nut "Ngat ket noi": chi bam duoc khi (co CSDL dang ket noi)
#     VA (khong dang chay).
#
#   - QUAN TRONG: Moi khi trang duoc TAI LAI (F5/refresh trinh
#     duyet), route "/" TU DONG dua toan bo trang thai ve GOC:
#       (1) Neu dang_chay=True -> dung han VideoWorker + thuc hien
#           logic "Dung" (mo khoa Cross-Line + ngat CSDL).
#       (2) Neu dang_chay=False nhung van dang ket noi CSDL (chi
#           moi "chon" qua dropdown, chua bam "Bat dau") -> ngat
#           ket noi CSDL.
#
#   - Xu ly AI THAT (YOLO + ByteTrack + line-crossing) chay trong
#     1 VideoWorker o thread rieng, ghi thang vao SQLite ngay khi
#     phat hien xe cat vach. Frontend polling /api/video/live_frame
#     de hien thi khung hinh dang xu ly (co ve bounding box).
#
#   - Bang lich_su_dem co cot fps_tai_thoi_diem, ghi nhan toc do
#     xu ly (da lam muot EMA, tinh trong video_worker.py) tai DUNG
#     thoi diem moi luot xe cat vach duoc ghi nhan. Route
#     /api/video/live_frame tra ve them "current_fps" de giao dien
#     hien thi ngay duoi 3 nut dieu khien phien.
#
#   - CAP NHAT (BO SUNG NGUON YOUTUBE, xem services/youtube_service.py):
#     them 1 lua chon moi trong dropdown "Nguon ghi hinh" cho phep
#     nhap truc tiep link YouTube thay vi chon file video co san
#     trong VIDEO_DIR. Link duoc "giai ma" thanh 1 URL stream that
#     (qua yt-dlp) roi dua thang vao cv2.VideoCapture(), giong het
#     cach VideoWorker da dang mo file video local - vi vay KHONG
#     can sua services/video_worker.py hay services/tracker_service.py.
#     Toan bo phan them moi duoc danh dau ro bang comment
#     "CHI CHEN THEM (YOUTUBE)".
# ============================================================
import os
import io
import csv
import json
import base64
import math
import sqlite3
import threading
from functools import wraps
from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
from flask import Flask, render_template, request, jsonify, Response

from services.tracker_service import find_model_path
from services.video_worker import VideoWorker
from services.youtube_service import is_youtube_url, resolve_stream_url  # CHI CHEN THEM (YOUTUBE)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.environ.get("VIDEO_DIR", os.path.join(BASE_DIR, "sample_videos"))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
MODEL_DIR = os.environ.get("MODEL_DIR", os.path.join(BASE_DIR, "..", "models"))

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

DB_STATE_PATH = os.path.join(DATA_DIR, "db_path_state.json")
STAGING_CONFIG_PATH = os.path.join(DATA_DIR, "crossline_staging.json")

# ============================================================
# QUAN LY 1 VideoWorker DUY NHAT TAI 1 THOI DIEM (chi 1 phien
# dem duoc phep chay cung luc, dung theo thiet ke db_path_state.json)
# ============================================================
_video_worker = None
_session_lock = threading.RLock()


def serialize_session(handler):
    """Keep overlapping browser requests from starting two counting workers."""
    @wraps(handler)
    def wrapped(*args, **kwargs):
        with _session_lock:
            return handler(*args, **kwargs)
    return wrapped


def _get_model_path():
    model_path = find_model_path(MODEL_DIR)
    if model_path is None:
        raise FileNotFoundError(
            f"Không tìm thấy file model (.pt) trong thư mục: {MODEL_DIR}"
        )
    return model_path


def _make_db_event_writer(db_path):
    """Callback ghi 1 su kien (xe cat vach) vao dung file CSDL cua
    phien nay. Moi lan goi TU MO 1 KET NOI SQLITE MOI, an toan khi
    goi tu thread rieng cua VideoWorker.
    CHI CHEN THEM: ghi kem cot fps_tai_thoi_diem (da duoc
    video_worker.py gan san vao event truoc khi goi callback nay)."""
    def _write_event(event):
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO lich_su_dem "
                "(thoi_gian, loai_phuong_tien, chieu_di_chuyen, track_id_goc, fps_tai_thoi_diem) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    event["timestamp"], event["class_name"],
                    event["direction"], event["track_id"],
                    event.get("fps_tai_thoi_diem", 0.0),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return _write_event


def _stop_video_worker_if_running():
    global _video_worker
    if _video_worker is not None:
        _video_worker.stop()
        if _video_worker.is_alive():
            raise WorkerStillStopping()
        _video_worker = None


VALID_VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")

app = Flask(__name__)


class WorkerStillStopping(Exception):
    """The previous frame read or inference has not returned yet."""


@app.errorhandler(WorkerStillStopping)
def worker_still_stopping(error):
    return jsonify({"ok": False, "message": "Đang dừng xử lý khung hình. Vui lòng thử lại sau."}), 409


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

DISPLAY_ORDER = ["bus", "motorbike", "car", "truck"]
DISPLAY_LABELS = {
    "bus": "Xe buýt",
    "motorbike": "Xe máy",
    "car": "Xe hơi",
    "truck": "Xe tải",
}
CLASS_NORMALIZE = {
    "motobike": "motorbike",
    "motorbike": "motorbike",
    "motorcycle": "motorbike",
    "motobyte": "motorbike",
    "car": "car",
    "bus": "bus",
    "truck": "truck",
}

# CHI CHEN THEM (YOUTUBE): them 2 truong moi, mac dinh
# "source_type": "local" de cac cau hinh cu (chua tung co truong
# nay) van duoc hieu dung khi doc lai qua .get(..., "local").
DEFAULT_CROSSLINE_CONFIG = {
    "video_filename": "", "source_type": "local", "youtube_url": "",
    "x1": None, "y1": None, "x2": None, "y2": None,
    "frame_width": None, "frame_height": None,
    "huong_1_label": "", "huong_2_label": "", "locked": False,
}


# ============================================================
# TIEN ICH CHUNG
# ============================================================
def now_vn():
    return datetime.now(VN_TZ)


def now_vn_string():
    return now_vn().strftime("%Y-%m-%d %H:%M:%S")


def normalize_dt_string(raw):
    if not raw:
        return None
    raw = raw.strip().replace("T", " ")
    if len(raw) == 16:
        raw = raw + ":00"
    return raw


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(default)
    return dict(default)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_db_schema(db_path):
    # CHI CHEN THEM: cot "fps_tai_thoi_diem REAL" o cuoi bang.
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lich_su_dem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thoi_gian TEXT NOT NULL,
            loai_phuong_tien TEXT NOT NULL,
            chieu_di_chuyen TEXT NOT NULL,
            track_id_goc INTEGER NOT NULL,
            fps_tai_thoi_diem REAL
        )
    """)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(lich_su_dem)")}
    if "fps_tai_thoi_diem" not in columns:
        conn.execute("ALTER TABLE lich_su_dem ADD COLUMN fps_tai_thoi_diem REAL")
    conn.commit()
    conn.close()


def make_unique_session_dir():
    folder_name = now_vn().strftime("%d-%m-%Y %H%M%S")
    target = os.path.join(DATA_DIR, folder_name)
    suffix = 1
    original = target
    while os.path.exists(target):
        target = f"{original}_{suffix}"
        suffix += 1
    os.makedirs(target, exist_ok=True)
    return target


def get_db_state():
    return load_json(DB_STATE_PATH, {
        "db_path": "", "auto_created": False, "dang_chay": False, "tam_dung": False
    })


def save_db_state(state):
    save_json(DB_STATE_PATH, state)


def _perform_session_stop(state):
    """Logic 'Dung phien' dung chung cho API /api/session/stop VA
    cho viec tu dong reset trang thai khi trang duoc tai lai."""
    db_path = state.get("db_path", "")
    if db_path:
        folder = os.path.dirname(db_path)
        config_path = os.path.join(folder, "crossline_config.json")
        config = load_json(config_path, DEFAULT_CROSSLINE_CONFIG)
        config["locked"] = False
        save_json(config_path, config)
    state["dang_chay"] = False
    state["tam_dung"] = False
    state["db_path"] = ""
    state["auto_created"] = False
    save_db_state(state)


def _perform_full_state_reset_on_page_load():
    """Goi moi khi trang '/' duoc tai lai (F5/refresh). Xu ly ca
    2 truong hop: dang chay that (dung han VideoWorker + dung
    phien) hoac chi moi ket noi CSDL ma chua bam Bat dau (chi
    can ngat CSDL)."""
    state = get_db_state()
    if state.get("dang_chay"):
        _stop_video_worker_if_running()
        _perform_session_stop(state)
    elif state.get("db_path"):
        state["db_path"] = ""
        state["auto_created"] = False
        state["tam_dung"] = False
        save_db_state(state)


def _force_reset_state_on_startup():
    """File DB_STATE_PATH nam trong thu muc da MOUNT tu ngoai
    container, nen no VAN TON TAI qua moi lan container
    restart/rebuild. Moi lan Flask khoi dong LUON ep dang_chay/
    tam_dung ve False."""
    if os.path.exists(DB_STATE_PATH):
        state = load_json(DB_STATE_PATH, {})
        if state.get("dang_chay") or state.get("tam_dung"):
            state["dang_chay"] = False
            state["tam_dung"] = False
            save_json(DB_STATE_PATH, state)


_force_reset_state_on_startup()


def get_connection_for(db_path):
    if not db_path or not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_connection():
    state = get_db_state()
    return get_connection_for(state.get("db_path", ""))


def get_active_crossline_config():
    state = get_db_state()
    if state.get("dang_chay") and state.get("db_path"):
        folder = os.path.dirname(state["db_path"])
        return load_json(
            os.path.join(folder, "crossline_config.json"), DEFAULT_CROSSLINE_CONFIG
        )
    return dict(DEFAULT_CROSSLINE_CONFIG)


def get_stats_display_config():
    state = get_db_state()
    if state.get("db_path"):
        folder = os.path.dirname(state["db_path"])
        return load_json(
            os.path.join(folder, "crossline_config.json"), DEFAULT_CROSSLINE_CONFIG
        )
    return dict(DEFAULT_CROSSLINE_CONFIG)


# ============================================================
# DANH SACH VIDEO
# ============================================================
@app.route("/api/video/list", methods=["GET"])
def api_video_list():
    try:
        files = [
            f for f in sorted(os.listdir(VIDEO_DIR))
            if f.lower().endswith(VALID_VIDEO_EXTENSIONS)
        ]
        return jsonify({"ok": True, "files": files, "video_dir": VIDEO_DIR})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Lỗi khi đọc thư mục video: {e}"}), 500


@app.route("/api/video/first_frame", methods=["POST"])
@serialize_session
def api_video_first_frame():
    state = get_db_state()
    if state.get("dang_chay"):
        return jsonify({
            "ok": False,
            "message": "Không thể đổi nguồn ghi hình khi đang chạy. Hãy bấm 'Dừng' trước."
        }), 400
    data = request.get_json(force=True)
    filename = (data.get("filename") or "").strip()
    if not filename:
        return jsonify({"ok": False, "message": "Chưa chọn file video."}), 400
    safe_name = os.path.basename(filename)
    video_path = os.path.join(VIDEO_DIR, safe_name)
    if not os.path.exists(video_path):
        return jsonify({"ok": False, "message": f"Không tìm thấy file: {safe_name}"}), 404
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({"ok": False, "message": "Không thể mở file video này."}), 400
    ok, frame = cap.read()
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    height, width = frame.shape[:2] if ok else (0, 0)
    cap.release()
    if not ok:
        return jsonify({"ok": False, "message": "Không đọc được khung hình đầu tiên."}), 400
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return jsonify({"ok": False, "message": "Lỗi khi mã hóa khung hình."}), 500
    b64_image = base64.b64encode(buffer).decode("utf-8")
    return jsonify({
        "ok": True,
        "filename": safe_name,
        "image_base64": f"data:image/jpeg;base64,{b64_image}",
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": total_frames,
    })


# ============================================================
# CHI CHEN THEM (YOUTUBE): xem khung hinh dau tien tu 1 link
# YouTube, dong vai tro giong het api_video_first_frame() o tren
# nhung cho nguon la link YouTube thay vi file cuc bo. Tach thanh
# route rieng de KHONG dung cham gi den logic/kiem tra file cua
# route cu dang hoat dong tot.
# ============================================================
@app.route("/api/video/youtube_first_frame", methods=["POST"])
@serialize_session
def api_video_youtube_first_frame():
    state = get_db_state()
    if state.get("dang_chay"):
        return jsonify({
            "ok": False,
            "message": "Không thể đổi nguồn ghi hình khi đang chạy. Hãy bấm 'Dừng' trước."
        }), 400
    data = request.get_json(force=True)
    youtube_url = (data.get("youtube_url") or "").strip()
    if not youtube_url:
        return jsonify({"ok": False, "message": "Chưa nhập link YouTube."}), 400
    if not is_youtube_url(youtube_url):
        return jsonify({
            "ok": False,
            "message": "Link không hợp lệ. Vui lòng dán đúng link YouTube (youtube.com hoặc youtu.be)."
        }), 400

    stream_url, error_message = resolve_stream_url(youtube_url)
    if error_message:
        return jsonify({"ok": False, "message": error_message}), 400

    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        return jsonify({"ok": False, "message": "Không thể mở luồng video từ link YouTube này."}), 400
    ok, frame = cap.read()
    height, width = frame.shape[:2] if ok else (0, 0)
    cap.release()
    if not ok:
        return jsonify({"ok": False, "message": "Không đọc được khung hình đầu tiên từ link này."}), 400
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return jsonify({"ok": False, "message": "Lỗi khi mã hóa khung hình."}), 500
    b64_image = base64.b64encode(buffer).decode("utf-8")
    return jsonify({
        "ok": True,
        "youtube_url": youtube_url,
        "image_base64": f"data:image/jpeg;base64,{b64_image}",
        "width": width,
        "height": height,
    })


@app.route("/api/video/live_frame", methods=["GET"])
@serialize_session
def api_video_live_frame():
    """Tra ve khung hinh MOI NHAT ma VideoWorker vua xu ly xong
    (da ve bounding box), de frontend polling lien tuc thay the
    cho anh tinh trong luc phien dang chay.
    CHI CHEN THEM: truong "current_fps" trong response khi ok=True,
    lay tu VideoWorker.current_fps (da tinh san EMA trong
    video_worker.py), de giao dien hien thi ngay duoi 3 nut dieu
    khien phien ma KHONG can them route moi nao."""
    global _video_worker
    state = get_db_state()
    if not state.get("dang_chay") or _video_worker is None:
        return jsonify({"ok": False, "message": "Không có phiên nào đang chạy."}), 400
    if _video_worker.error_message:
        loi = _video_worker.error_message
        _stop_video_worker_if_running()
        _perform_session_stop(state)
        return jsonify({
            "ok": False,
            "video_ended": False,
            "message": f"Lỗi xử lý video, phiên đã tự động dừng: {loi}",
        })
    if _video_worker.video_ended:
        _stop_video_worker_if_running()
        _perform_session_stop(state)
        return jsonify({
            "ok": True,
            "video_ended": True,
            "message": "Video đã phát hết, phiên đã tự động dừng.",
        })
    frame_b64 = _video_worker.get_latest_frame_base64()
    return jsonify({
        "ok": True,
        "video_ended": False,
        "image_base64": frame_b64,
        "current_fps": _video_worker.current_fps,
    })


# ============================================================
# QUAN LY CSDL: danh sach, chon (dropdown), ngat ket noi, trang thai
# ============================================================
def _is_path_inside(base_dir, target_path):
    if ".." in target_path.replace("\\", "/").split("/"):
        return False
    base_abs = os.path.realpath(base_dir)
    target_abs = os.path.realpath(target_path)
    return target_abs == base_abs or target_abs.startswith(base_abs + os.sep)


@app.route("/api/db/list", methods=["GET"])
def api_db_list():
    try:
        found = []
        for root, dirs, filenames in os.walk(DATA_DIR):
            for fn in filenames:
                if fn.lower().endswith(".db"):
                    full_path = os.path.join(root, fn)
                    rel_path = os.path.relpath(full_path, DATA_DIR).replace(os.sep, "/")
                    try:
                        mtime = os.path.getmtime(full_path)
                    except OSError:
                        mtime = 0
                    found.append((mtime, rel_path))
        found.sort(key=lambda item: item[0], reverse=True)
        return jsonify({"ok": True, "files": [f[1] for f in found], "data_dir": DATA_DIR})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Lỗi khi đọc thư mục dữ liệu: {e}"}), 500


@app.route("/api/db/status", methods=["GET"])
def api_db_status():
    state = get_db_state()
    db_path = state.get("db_path", "")
    exists = bool(db_path) and os.path.exists(db_path)
    info = {
        "db_path": db_path,
        "connected": exists,
        "auto_created": state.get("auto_created", False),
        "dang_chay": state.get("dang_chay", False),
    }
    if exists:
        info["db_relpath"] = os.path.relpath(db_path, DATA_DIR).replace(os.sep, "/")
        conn = get_connection_for(db_path)
        try:
            row = conn.execute(
                "SELECT MIN(thoi_gian) AS min_ts, MAX(thoi_gian) AS max_ts, "
                "COUNT(*) AS tong FROM lich_su_dem"
            ).fetchone()
            info["min_ts"] = row["min_ts"]
            info["max_ts"] = row["max_ts"]
            info["tong_ban_ghi"] = row["tong"]
        except Exception as e:
            info["connected"] = False
            info["error"] = str(e)
        finally:
            conn.close()
    return jsonify(info)


@app.route("/api/db/select", methods=["POST"])
@serialize_session
def api_db_select():
    state = get_db_state()
    if state.get("dang_chay"):
        return jsonify({
            "ok": False,
            "message": "Không thể đổi CSDL khi đang chạy. Hãy bấm 'Dừng' trước."
        }), 400
    data = request.get_json(force=True)
    rel_path = (data.get("filename") or "").strip()
    if not rel_path:
        return jsonify({"ok": False, "message": "Chưa chọn file CSDL."}), 400
    norm_rel = os.path.normpath(rel_path)
    full_path = os.path.join(DATA_DIR, norm_rel)
    if not _is_path_inside(DATA_DIR, full_path):
        return jsonify({"ok": False, "message": "Đường dẫn không hợp lệ."}), 400
    if not os.path.exists(full_path):
        return jsonify({"ok": False, "message": f"Không tìm thấy file: {rel_path}"}), 404
    try:
        conn = sqlite3.connect(full_path)
        exists_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='lich_su_dem'"
        ).fetchone()
        conn.close()
        if not exists_table:
            return jsonify({
                "ok": False,
                "message": "File hợp lệ nhưng không có bảng 'lich_su_dem'."
            }), 400
        create_db_schema(full_path)
    except Exception as e:
        return jsonify({"ok": False, "message": f"Lỗi khi mở file: {e}"}), 400
    state["db_path"] = full_path
    state["auto_created"] = False
    state["dang_chay"] = False
    state["tam_dung"] = False
    save_db_state(state)
    return jsonify({"ok": True, "message": f"Đã kết nối tới {rel_path}."})


@app.route("/api/db/disconnect", methods=["POST"])
@serialize_session
def api_db_disconnect():
    state = get_db_state()
    if state.get("dang_chay"):
        return jsonify({
            "ok": False,
            "message": "Không thể ngắt kết nối khi đang chạy."
        }), 400
    if not state.get("db_path"):
        return jsonify({"ok": False, "message": "Hiện chưa kết nối CSDL nào."}), 400
    state["db_path"] = ""
    state["auto_created"] = False
    state["tam_dung"] = False
    save_db_state(state)
    return jsonify({"ok": True, "message": "Đã ngắt kết nối CSDL."})


# ============================================================
# CAU HINH CROSS-LINE
# ============================================================
@app.route("/api/config/crossline", methods=["GET"])
def api_get_crossline_config():
    return jsonify(get_active_crossline_config())


@app.route("/api/config/crossline", methods=["POST"])
@serialize_session
def api_save_crossline_config():
    state = get_db_state()
    if state.get("dang_chay"):
        return jsonify({
            "ok": False,
            "message": "Không thể sửa cấu hình Cross-Line khi phiên đang chạy. Hãy bấm 'Dừng' trước."
        }), 400
    data = request.get_json(force=True)
    config = {
        "video_filename": data.get("video_filename", ""),
        # CHI CHEN THEM (YOUTUBE): luu them nguon la local hay youtube.
        "source_type": data.get("source_type", "local"),
        "youtube_url": data.get("youtube_url", ""),
        "x1": data.get("x1"), "y1": data.get("y1"),
        "x2": data.get("x2"), "y2": data.get("y2"),
        "frame_width": data.get("frame_width"),
        "frame_height": data.get("frame_height"),
        "huong_1_label": data.get("huong_1_label", ""),
        "huong_2_label": data.get("huong_2_label", ""),
        "locked": False,
        "saved_at": now_vn_string(),
    }
    save_json(STAGING_CONFIG_PATH, config)
    return jsonify({"ok": True, "message": "Đã lưu cấu hình Cross-Line.", "config": config})


# ============================================================
# PHIEN LAM VIEC: BAT DAU / DUNG / TAM DUNG / TIEP TUC
# ============================================================
def validate_crossline_config(config):
    """Reject malformed geometry before creating a database or worker."""
    if config.get("source_type", "local") not in ("local", "youtube"):
        return "Nguồn ghi hình không hợp lệ."
    for key in ("x1", "y1", "x2", "y2", "frame_width", "frame_height"):
        value = config.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return "Tọa độ và kích thước khung hình phải là số hợp lệ."
    width, height = config["frame_width"], config["frame_height"]
    if width <= 0 or height <= 0:
        return "Kích thước khung hình phải lớn hơn 0."
    if any(not 0 <= config[key] <= limit for key, limit in (
        ("x1", width), ("x2", width), ("y1", height), ("y2", height)
    )):
        return "Cross-Line phải nằm trong khung hình."
    if (config["x1"], config["y1"]) == (config["x2"], config["y2"]):
        return "Hai điểm Cross-Line phải khác nhau."
    labels = [config.get("huong_1_label"), config.get("huong_2_label")]
    if any(not isinstance(label, str) or not label.strip() for label in labels):
        return "Chưa khai báo đầy đủ Hướng 1 / Hướng 2."
    if labels[0].strip() == labels[1].strip():
        return "Hướng 1 và Hướng 2 phải có tên khác nhau."
    return None


@app.route("/api/session/start", methods=["POST"])
@serialize_session
def api_session_start():
    global _video_worker
    state = get_db_state()
    if state.get("dang_chay"):
        return jsonify({"ok": False, "message": "Đã có phiên đang chạy."}), 409
    staged = load_json(STAGING_CONFIG_PATH, DEFAULT_CROSSLINE_CONFIG)
    required = ["x1", "y1", "x2", "y2"]
    if any(staged.get(k) is None for k in required):
        return jsonify({"ok": False, "message": "Chưa cấu hình đủ 2 điểm Cross-Line."}), 400
    if not staged.get("huong_1_label") or not staged.get("huong_2_label"):
        return jsonify({"ok": False, "message": "Chưa khai báo đầy đủ Hướng 1 / Hướng 2."}), 400
    config_error = validate_crossline_config(staged)
    if config_error:
        return jsonify({"ok": False, "message": config_error}), 400
    try:
        model_path = _get_model_path()
    except FileNotFoundError as e:
        return jsonify({"ok": False, "message": str(e)}), 400

    # ------------------------------------------------------------
    # CHI CHEN THEM (YOUTUBE): xac dinh video_path theo source_type.
    # Voi nguon YouTube, GIAI MA LAI (fresh) link thanh URL stream
    # NGAY TAI THOI DIEM bam "Bat dau" - KHONG tai su dung stream
    # url da lay luc xem truoc o api_video_youtube_first_frame(),
    # vi URL do YouTube cap co the da het han neu nguoi dung mat
    # nhieu thoi gian cau hinh Cross-Line truoc khi bam "Bat dau".
    # Nhanh "local" ben duoi GIU NGUYEN 100% logic cu.
    # ------------------------------------------------------------
    source_type = staged.get("source_type", "local")
    if source_type == "youtube":
        youtube_url = (staged.get("youtube_url") or "").strip()
        if not youtube_url or not is_youtube_url(youtube_url):
            return jsonify({
                "ok": False,
                "message": "Chưa có link YouTube hợp lệ. Vui lòng chọn lại nguồn ghi hình."
            }), 400
        video_path, resolve_error = resolve_stream_url(youtube_url)
        if resolve_error:
            return jsonify({"ok": False, "message": resolve_error}), 400
    else:
        video_filename = staged.get("video_filename") or ""
        video_path = os.path.join(VIDEO_DIR, os.path.basename(video_filename)) if video_filename else ""
        if not video_filename or not os.path.exists(video_path):
            return jsonify({
                "ok": False,
                "message": "Không tìm thấy file video đã chọn. Vui lòng chọn lại nguồn ghi hình."
            }), 400

    existing_db = state.get("db_path", "")
    reuse_existing = bool(existing_db) and os.path.exists(existing_db) and not state.get("auto_created")
    if reuse_existing:
        target_db = existing_db
        create_db_schema(target_db)
        action = "reuse"
    else:
        target_dir = make_unique_session_dir()
        target_db = os.path.join(target_dir, "he_thong_dem_xe.db")
        create_db_schema(target_db)
        action = "create"
    target_dir = os.path.dirname(target_db)

    finalized_config = dict(staged)
    finalized_config["locked"] = True
    save_json(os.path.join(target_dir, "crossline_config.json"), finalized_config)

    _stop_video_worker_if_running()
    _video_worker = VideoWorker(
        video_path=video_path,
        model_path=model_path,
        crossline_config=finalized_config,
        on_event=_make_db_event_writer(target_db),
    )
    _video_worker.start()

    state["db_path"] = target_db
    state["auto_created"] = (action == "create")
    state["dang_chay"] = True
    state["tam_dung"] = False
    save_db_state(state)

    message = (
        "Đã kết nối tiếp vào CSDL đã chọn (số liệu sẽ cộng dồn)."
        if action == "reuse"
        else f"Đã tạo phiên đếm mới: {os.path.basename(target_dir)}"
    )
    return jsonify({
        "ok": True,
        "message": message,
        "action": action,
        "db_path": target_db,
    })


@app.route("/api/session/stop", methods=["POST"])
@serialize_session
def api_session_stop():
    state = get_db_state()
    if not state.get("dang_chay"):
        return jsonify({"ok": False, "message": "Không có phiên nào đang chạy."}), 400
    _stop_video_worker_if_running()
    _perform_session_stop(state)
    return jsonify({"ok": True, "message": "Đã dừng phiên làm việc và ngắt kết nối CSDL."})


@app.route("/api/session/status", methods=["GET"])
def api_session_status():
    state = get_db_state()
    return jsonify({
        "dang_chay": state.get("dang_chay", False),
        "tam_dung": state.get("tam_dung", False),
    })


@app.route("/api/session/pause", methods=["POST"])
@serialize_session
def api_session_pause():
    state = get_db_state()
    if not state.get("dang_chay"):
        return jsonify({"ok": False, "message": "Chỉ tạm dừng được khi đang chạy."}), 400
    if state.get("tam_dung"):
        return jsonify({"ok": False, "message": "Đã đang ở trạng thái tạm dừng."}), 400
    if _video_worker is not None:
        _video_worker.pause()
    state["tam_dung"] = True
    save_db_state(state)
    return jsonify({"ok": True, "message": "Đã tạm dừng."})


@app.route("/api/session/resume", methods=["POST"])
@serialize_session
def api_session_resume():
    state = get_db_state()
    if not state.get("dang_chay"):
        return jsonify({"ok": False, "message": "Không có phiên nào đang chạy."}), 400
    if not state.get("tam_dung"):
        return jsonify({"ok": False, "message": "Hiện không ở trạng thái tạm dừng."}), 400
    if _video_worker is not None:
        _video_worker.resume()
    state["tam_dung"] = False
    save_db_state(state)
    return jsonify({"ok": True, "message": "Đã tiếp tục."})


# ============================================================
# THONG KE
# ============================================================
@app.route("/api/stats/live", methods=["GET"])
def api_stats_live():
    conn = get_connection()
    config = get_stats_display_config()
    current_time = now_vn_string()
    if conn is None:
        return jsonify({
            "ok": False,
            "message": "Chưa kết nối cơ sở dữ liệu. Vui lòng chọn CSDL hoặc bấm 'Bắt đầu' để tự tạo phiên mới.",
            "current_server_time": current_time,
        }), 400
    huong_1 = config.get("huong_1_label") or ""
    huong_2 = config.get("huong_2_label") or ""
    try:
        row = conn.execute("SELECT MIN(thoi_gian) AS min_ts FROM lich_su_dem").fetchone()
        min_ts = row["min_ts"]
        result_table = {cls: {"huong_1": 0, "huong_2": 0} for cls in DISPLAY_ORDER}
        if min_ts:
            rows = conn.execute("""
                SELECT loai_phuong_tien, chieu_di_chuyen, COUNT(*) AS so_luot
                FROM lich_su_dem
                WHERE thoi_gian BETWEEN ? AND ?
                GROUP BY loai_phuong_tien, chieu_di_chuyen
            """, (min_ts, current_time)).fetchall()
            for r in rows:
                raw_class = (r["loai_phuong_tien"] or "").strip().lower()
                cls = CLASS_NORMALIZE.get(raw_class, raw_class)
                if cls not in result_table:
                    continue
                direction = r["chieu_di_chuyen"] or ""
                if huong_1 and direction == huong_1:
                    result_table[cls]["huong_1"] += r["so_luot"]
                elif huong_2 and direction == huong_2:
                    result_table[cls]["huong_2"] += r["so_luot"]
        return jsonify({
            "ok": True,
            "current_server_time": current_time,
            "huong_1_label": huong_1,
            "huong_2_label": huong_2,
            "counts": [
                {
                    "class_key": cls,
                    "label": DISPLAY_LABELS[cls],
                    "huong_1": result_table[cls]["huong_1"],
                    "huong_2": result_table[cls]["huong_2"],
                }
                for cls in DISPLAY_ORDER
            ],
        })
    finally:
        conn.close()


@app.route("/api/server_time", methods=["GET"])
def api_server_time():
    return jsonify({"current_server_time": now_vn_string()})


# ============================================================
# XUAT DU LIEU CHI TIET (POPUP)
# ------------------------------------------------------------
# CHI CHEN THEM: cot fps_tai_thoi_diem vao SELECT va vao du lieu
# tra ve, de nguoi dung co the doi chieu FPS tai dung thoi diem
# tung xe cat vach khi lam phu luc bao cao.
# ============================================================
@app.route("/api/query_detail", methods=["GET"])
def api_query_detail():
    tu_raw_input = request.args.get("tu_thoi_diem")
    den_raw_input = request.args.get("den_thoi_diem")
    if not tu_raw_input or not den_raw_input:
        return jsonify({
            "ok": False,
            "message": "Cần khai báo đầy đủ 'Từ thời điểm' và 'Đến thời điểm'."
        }), 400
    conn = get_connection()
    if conn is None:
        return jsonify({"ok": False, "message": "Chưa kết nối cơ sở dữ liệu."}), 400
    try:
        row = conn.execute("SELECT MIN(thoi_gian) AS min_ts FROM lich_su_dem").fetchone()
        min_ts = row["min_ts"]
        tu_raw = normalize_dt_string(tu_raw_input)
        den_raw = normalize_dt_string(den_raw_input)
        effective_start = min_ts if (min_ts and tu_raw < min_ts) else tu_raw
        effective_end = den_raw
        summary_rows = conn.execute("""
            SELECT loai_phuong_tien, chieu_di_chuyen, COUNT(*) AS so_luot
            FROM lich_su_dem
            WHERE thoi_gian BETWEEN ? AND ?
            GROUP BY loai_phuong_tien, chieu_di_chuyen
            ORDER BY loai_phuong_tien
        """, (effective_start, effective_end)).fetchall()
        detail_rows = conn.execute("""
            SELECT thoi_gian, track_id_goc, loai_phuong_tien, chieu_di_chuyen, fps_tai_thoi_diem
            FROM lich_su_dem
            WHERE thoi_gian BETWEEN ? AND ?
            ORDER BY thoi_gian
        """, (effective_start, effective_end)).fetchall()
        return jsonify({
            "ok": True,
            "effective_start": effective_start,
            "effective_end": effective_end,
            "summary": [
                {
                    "class_name": r["loai_phuong_tien"],
                    "direction": r["chieu_di_chuyen"],
                    "count": r["so_luot"]
                } for r in summary_rows
            ],
            "detail": [
                {
                    "timestamp": r["thoi_gian"],
                    "track_id": r["track_id_goc"],
                    "class_name": r["loai_phuong_tien"],
                    "direction": r["chieu_di_chuyen"],
                    "fps_tai_thoi_diem": r["fps_tai_thoi_diem"],
                } for r in detail_rows
            ],
            "total_events": len(detail_rows),
        })
    finally:
        conn.close()


@app.route("/api/query_detail/export_csv", methods=["GET"])
def api_export_csv():
    tu_raw_input = request.args.get("tu_thoi_diem")
    den_raw_input = request.args.get("den_thoi_diem")
    if not tu_raw_input or not den_raw_input:
        return jsonify({"ok": False, "message": "Thiếu khoảng thời gian."}), 400
    conn = get_connection()
    if conn is None:
        return jsonify({"ok": False, "message": "Chưa kết nối cơ sở dữ liệu."}), 400
    try:
        row = conn.execute("SELECT MIN(thoi_gian) AS min_ts FROM lich_su_dem").fetchone()
        min_ts = row["min_ts"]
        tu_raw = normalize_dt_string(tu_raw_input)
        den_raw = normalize_dt_string(den_raw_input)
        effective_start = min_ts if (min_ts and tu_raw < min_ts) else tu_raw
        effective_end = den_raw
        rows = conn.execute("""
            SELECT thoi_gian, track_id_goc, loai_phuong_tien, chieu_di_chuyen, fps_tai_thoi_diem
            FROM lich_su_dem
            WHERE thoi_gian BETWEEN ? AND ?
            ORDER BY thoi_gian
        """, (effective_start, effective_end)).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "track_id", "class_name", "direction", "fps_tai_thoi_diem"])
        for r in rows:
            writer.writerow([
                r["thoi_gian"], r["track_id_goc"], r["loai_phuong_tien"],
                r["chieu_di_chuyen"], r["fps_tai_thoi_diem"]
            ])
        csv_bytes = output.getvalue().encode("utf-8-sig")
        filename = f"chi_tiet_dem_xe_{effective_start.replace(':','-').replace(' ','_')}_den_{effective_end.replace(':','-').replace(' ','_')}.csv"
        return Response(
            csv_bytes, mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    finally:
        conn.close()


@app.route("/")
@serialize_session
def index():
    _perform_full_state_reset_on_page_load()
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=False, host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), threaded=True)
