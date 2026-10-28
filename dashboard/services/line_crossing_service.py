# ============================================================
# line_crossing_service.py - LOGIC DEM LINE-CROSSING (STREAMING)
# ------------------------------------------------------------
# Day la ban REFACTOR tu Cell 7 cua "linecrossing.pdf" (notebook
# LINE-CROSSING.ipynb), chuyen tu kieu BATCH sang kieu STREAMING
# (xu ly tung frame ngay khi den, khong biet truoc tuong lai cua
# track_id).
#
# Cong thuc "tinh_phia_diem" GIU NGUYEN 100% nhu notebook goc, va
# da duoc kiem chung khop voi ham "sideValue" trong static/js/app.js.
#
# ------------------------------------------------------------
# DA SUA LOI GAN NHAM HUONG 1 <-> HUONG 2 (2026-09-02)
# ------------------------------------------------------------
# LOI DA PHAT HIEN: quy uoc dau (+/-) frontend dung de TO MAU man
# hinh la:
#     sideValue > 0 (duong) -> to mau XANH -> gan la "Huong 1"
#     sideValue < 0 (am)    -> to mau DO   -> gan la "Huong 2"
# Nhung ban truoc cua process_detection() lai gan NGUOC LAI hoan
# toan. Da SUA: doi cho 2 nhan huong trong khoi if/elif ben duoi
# (xem comment "DA SUA"), khong thay doi bat ky logic nao khac.
#
# KHAC BIET SO VOI NOTEBOOK GOC (batch) - da thong nhat truoc khi code:
#   1. Majority Voting: xu ly TRUC TUYEN (Counter cap nhat moi
#      frame, chon nhan pho bien nhat TINH DEN thoi diem cat vach),
#      thay cho xu ly hau ky tren toan bo quy dao nhu ban goc.
#   2. Bo qua hoan toan buoc "tim cap track_id phan manh" (Cell 8,
#      bytetrack.pdf) - day la cong cu phan tich cho Chuong 4,
#      khong anh huong logic dem.
#   3. Timestamp: dung datetime.now(VN_TZ) THAT tai thoi diem cat
#      vach, thay vi cong thuc gia lap frame/FPS cua notebook batch.
# ============================================================
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

MIN_FRAMES_TRUOC_KHI_DEM = 3
MAX_FRAME_TUOI_TRUOC_KHI_XOA = 300


def tinh_phia_diem(px, py, x1, y1, x2, y2):
    """Tinh tich co huong, dau duong/am the hien phia cua diem
    (px,py) so voi duong thang di qua (x1,y1) va (x2,y2).
    QUY UOC DAU (thong nhat voi frontend static/js/app.js):
        sideValue > 0 (duong) -> phia man hinh to MAU XANH -> Huong 1
        sideValue < 0 (am)    -> phia man hinh to MAU DO   -> Huong 2
    """
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


class _TrackState:
    __slots__ = ("phia_truoc", "so_frame_da_thay", "class_votes",
                 "da_dem", "frame_cuoi_cung_thay")

    def __init__(self, frame_hien_tai):
        self.phia_truoc = None
        self.so_frame_da_thay = 0
        self.class_votes = Counter()
        self.da_dem = False
        self.frame_cuoi_cung_thay = frame_hien_tai


class LineCrossingSession:
    """Quan ly toan bo trang thai dem line-crossing cho MOT PHIEN
    xu ly streaming (tuong ung 1 lan bam "Bat dau" tren dashboard)."""

    def __init__(self, x1, y1, x2, y2, huong_1_label, huong_2_label,
                 min_frames_truoc_khi_dem=MIN_FRAMES_TRUOC_KHI_DEM):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.huong_1_label = huong_1_label
        self.huong_2_label = huong_2_label
        self.min_frames_truoc_khi_dem = min_frames_truoc_khi_dem
        self._tracks = {}

    def process_detection(self, track_id, class_name, cx, cy, frame_idx):
        """Xu ly 1 detection (1 phuong tien tai 1 frame). Tra ve 1
        dict su kien neu day la thoi diem phuong tien vua cat qua
        vach (va chua tung duoc dem truoc do), nguoc lai None."""
        state = self._tracks.get(track_id)
        if state is None:
            state = _TrackState(frame_idx)
            self._tracks[track_id] = state

        state.so_frame_da_thay += 1
        state.frame_cuoi_cung_thay = frame_idx
        state.class_votes[class_name] += 1

        phia_hien_tai = tinh_phia_diem(cx, cy, self.x1, self.y1, self.x2, self.y2)
        event = None

        if (
            state.phia_truoc is not None
            and not state.da_dem
            and state.so_frame_da_thay >= self.min_frames_truoc_khi_dem
        ):
            # ---- DA SUA (2026-09-02): doi cho 2 nhan huong de khop
            # dung quy uoc mau sac cua frontend (xem docstring o tren) ----
            if state.phia_truoc > 0 and phia_hien_tai < 0:
                direction = self.huong_2_label
            elif state.phia_truoc < 0 and phia_hien_tai > 0:
                direction = self.huong_1_label
            else:
                direction = None

            if direction is not None:
                final_class_name = state.class_votes.most_common(1)[0][0]
                event = {
                    "class_name": final_class_name,
                    "direction": direction,
                    "track_id": track_id,
                    "frame_cat_vach": frame_idx,
                }
                state.da_dem = True

        # Keep the last nonzero side when a center lands exactly on the line.
        if phia_hien_tai != 0:
            state.phia_truoc = phia_hien_tai
        return event

    def purge_stale(self, current_frame_idx,
                     max_age=MAX_FRAME_TUOI_TRUOC_KHI_XOA):
        stale_ids = [
            tid for tid, st in self._tracks.items()
            if (current_frame_idx - st.frame_cuoi_cung_thay) > max_age
        ]
        for tid in stale_ids:
            del self._tracks[tid]
        return len(stale_ids)

    def active_track_count(self):
        return len(self._tracks)


def now_vn_timestamp_string():
    return datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
