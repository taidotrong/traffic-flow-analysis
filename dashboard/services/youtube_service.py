# ============================================================
# youtube_service.py - LAY DUONG DAN STREAM THAT SU TU LINK YOUTUBE
# ------------------------------------------------------------
# Dung yt-dlp de "giai ma" 1 link YouTube (video thuong hoac
# livestream) thanh 1 URL stream truc tiep (thuong la .mp4 hoac
# .m3u8) ma cv2.VideoCapture() co the mo va doc frame y het nhu
# mo 1 file video local. KHONG tai video ve may (khong download),
# chi lay duong dan de doc truc tiep.
#
# Nho tinh chat "module doc lap" nay, video_worker.py va
# tracker_service.py KHONG CAN SUA GI CA: VideoWorker van goi
# cv2.VideoCapture(self.video_path) nhu cu, chi khac la
# video_path luc nay la 1 URL stream thay vi 1 duong dan file
# cuc bo trong VIDEO_DIR.
#
# LUU Y QUAN TRONG VE "HET HAN":
#   URL stream do YouTube cap phat co thoi han su dung (thuong
#   chi vai gio), nen MOI LAN can mo video (ca luc xem truoc
#   khung hinh dau tien LAN luc bam "Bat dau" that su) DEU phai
#   goi lai resolve_stream_url() de lay URL MOI NHAT - KHONG
#   duoc luu 1 URL cu roi dung lai nhieu lan cach nhau lau.
#
# ------------------------------------------------------------
# XU LY LOI "Sign in to confirm you're not a bot" (2026-09-26)
# ------------------------------------------------------------
# YouTube ngay cang sieng kiem tra "bot" doi voi request khong
# xuat phat tu 1 trinh duyet that (nhu server goi qua yt-dlp).
# Ham resolve_stream_url() xu ly theo 2 lop:
#   1) Thu truoc bang "player_client=android" - client gia lap
#      app Android, THUONG IT BI CHAN BOT HON client web mac
#      dinh, khong can cookies.
#   2) Neu van bi chan VA nguoi dung da khai bao bien moi truong
#      YOUTUBE_COOKIES_FILE (duong dan toi 1 file cookies.txt xuat
#      tu trinh duyet That da dang nhap YouTube), thu lai kem
#      cookies - day la cach on dinh nhat, gan nhu luon vuot qua
#      duoc kiem tra bot.
#   3) Neu ca hai deu that bai, tra ve thong bao loi ro rang bang
#      tieng Viet, kem huong dan cau hinh YOUTUBE_COOKIES_FILE.
#
# CACH XUAT FILE cookies.txt (lam 1 LAN tren may ca nhan, khong
# lam trong container):
#   - Cai extension trinh duyet "Get cookies.txt LOCALLY" (Chrome/
#     Edge) hoac tuong tu.
#   - Dang nhap YouTube binh thuong tren trinh duyet.
#   - Dung extension xuat cookies cua trang youtube.com ra 1 file
#     cookies.txt.
#   - Dat file nay vao thu muc da mount vao container (vi du cung
#     thu muc voi Model), roi khai bao trong docker-compose.yml:
#       environment:
#         - YOUTUBE_COOKIES_FILE=/app/models/cookies.txt
#   - Luu y: cookies se het han sau 1 thoi gian (thuong vai tuan
#     toi vai thang tuy YouTube), can xuat lai khi gap loi tuong tu.
# ============================================================
import os
from urllib.parse import urlparse, parse_qs

# Nhan dien cac dang link YouTube pho bien: video thuong, video
# rut gon, va link "/live/" (livestream dang phat).


def is_youtube_url(url):
    """Kiem tra nhanh (khong goi mang) xem chuoi co giong 1 link
    YouTube hop le hay khong, dung de bao loi som truoc khi goi
    yt-dlp (ton thoi gian hon vi phai goi mang)."""
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https") or parsed.username or parsed.password:
            return False
        host = (parsed.hostname or "").lower()
        if host == "youtu.be":
            return bool(parsed.path.strip("/"))
        if host not in ("youtube.com", "www.youtube.com", "m.youtube.com"):
            return False
        return (
            parsed.path == "/watch" and bool(parse_qs(parsed.query).get("v"))
        ) or (parsed.path.startswith("/live/") and bool(parsed.path[len("/live/"):]))
    except ValueError:
        return False


def _build_ydl_opts(player_client, cookies_file):
    opts = {
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "extractor_args": {"youtube": {"player_client": [player_client]}},
    }
    if cookies_file:
        opts["cookiefile"] = cookies_file
    return opts


def resolve_stream_url(youtube_url):
    """Goi yt-dlp de lay URL stream truc tiep tu 1 link YouTube.

    Tra ve tuple (stream_url, error_message):
        - Thanh cong: (stream_url_str, None)
        - That bai:   (None, "ly do loi bang tieng Viet de hien
                        thi truc tiep cho nguoi dung")

    Xem chi tiet co che chong loi "Sign in to confirm you're not
    a bot" o phan comment dau file.
    """
    try:
        import yt_dlp
    except ImportError:
        return None, (
            "Thiếu thư viện yt-dlp trên máy chủ. Vui lòng kiểm tra "
            "lại requirements.txt và rebuild container."
        )

    cookies_file = os.environ.get("YOUTUBE_COOKIES_FILE", "").strip() or None
    if cookies_file and not os.path.exists(cookies_file):
        cookies_file = None

    last_error = None
    # Thu lan luot: android truoc (it bi kiem tra bot hon), web sau.
    for player_client in ("android", "web"):
        ydl_opts = _build_ydl_opts(player_client, cookies_file)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                stream_url = info.get("url") if info else None
                if stream_url:
                    return stream_url, None
                last_error = "Không lấy được đường dẫn phát trực tiếp từ link này."
        except Exception as e:
            last_error = str(e)
            continue

    if last_error and "Sign in to confirm" in last_error:
        return None, (
            "YouTube yêu cầu xác thực chống bot nên chưa lấy được video này. "
            "Cần cấu hình file cookies để xác thực như trình duyệt thật: "
            "xuất file cookies.txt từ trình duyệt đã đăng nhập YouTube, đặt "
            "vào thư mục đã mount, rồi khai báo biến môi trường "
            "YOUTUBE_COOKIES_FILE trong docker-compose.yml. Một số video "
            "công khai đôi khi cũng bị chặn tạm thời, có thể thử lại sau "
            "vài phút hoặc dùng video khác."
        )
    return None, f"Không xử lý được link YouTube: {last_error}"
