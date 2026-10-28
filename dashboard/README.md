# Vehicle counting dashboard

Flask serves a Vietnamese dashboard for YOLOv8 detection, ByteTrack tracking, directional line-crossing counts, SQLite history, live frames and CSV export. The source was imported from Drive's `DASHBOARD-DEMO/Source Code DashBoard` snapshot, last modified 26 September 2026.

## Run locally

Use Python 3.11. From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r dashboard/requirements.txt
```

Download the [dashboard checkpoint, best.pt](https://drive.google.com/file/d/1i31zb5cou9gGIdzRLSlfLn-0JiSTK5a7/view) to `models/best.pt` and the [short sample video](https://drive.google.com/file/d/1Z20WdNJ3idfnQzi0KE2eDYu2gAJwkFj7/view) to `dashboard/sample_videos/hcm_traffic_short.mp4`. Drive access may be required. Model weights and videos remain outside Git.

```bash
python dashboard/app.py
```

Open http://127.0.0.1:5000. If port 5000 is occupied, run `PORT=5001 python dashboard/app.py` on macOS/Linux, or set `PORT` in your shell on Windows. The server binds to localhost by default. This is a local, single-operator demo; Flask's development server is not a production deployment.

| Variable | Local default | Purpose |
|---|---|---|
| `VIDEO_DIR` | `dashboard/sample_videos/` | Input MP4/AVI/MOV/MKV files |
| `DATA_DIR` | `dashboard/data/` | Generated SQLite sessions and configuration |
| `MODEL_DIR` | `models/` | `best.pt`, otherwise first `.pt` alphabetically |
| `PORT` | `5000` | HTTP port |
| `HOST` | `127.0.0.1` | Bind address |
| `YOUTUBE_COOKIES_FILE` | unset | Optional local cookies for yt-dlp |

Custom directory overrides should be absolute paths. A `.env` file is read by Docker Compose only; direct Python execution uses your shell's environment variables.

## Use the dashboard

1. Select a local video. Its first frame appears for line placement. YouTube input is also available, subject to upstream stream availability and authentication.
2. Pick the two Cross-Line endpoints on the image, or enter their original-image coordinates. Give the two directions distinct names. The green side is Hướng 1, the red side Hướng 2; the destination side determines the recorded direction.
3. Leave the database selector empty to create a new session, or select an existing database to append counts.
4. Click **Bắt đầu**. The worker detects and tracks vehicles, saves each counted crossing and processing FPS, and displays annotated frames. Use **Tạm dừng**, **Tiếp tục** or **Dừng** as needed.
5. Query a time range and open **Xuất dữ liệu chi tiết** to view events and download CSV. Select a saved database again after stopping or reaching the end of a video.

The original session behavior is preserved: refreshing `/` stops the current worker and disconnects its database; Stop and end-of-video also disconnect the database. Only one session runs at a time. Each track is counted once per session. Timestamps are wall-clock processing times in `Asia/Ho_Chi_Minh`, rather than source-video times. Very slow streams can delay stopping until the current frame read/inference finishes.

For historical data, copy `dashboard/sample_data/he_thong_dem_xe_sample.db` into `dashboard/data/` and select it. It contains 30 source events. Selection upgrades its old schema by adding a nullable FPS column, preserving the events. Directional live totals for an existing database use its adjacent `crossline_config.json`; detail queries and CSV exports work without that sidecar.

## Docker

With Docker running, from the repository root:

```bash
docker compose -f dashboard/docker-compose.yml up --build
```

The portable defaults mount `sample_videos/`, `data/` and `../models/` relative to `dashboard/`; video and model mounts are read-only. Copy `dashboard/.env.example` to `dashboard/.env` to override paths or the published port. Keep cookie files private and outside Git. Docker runtime execution was not verified in this validation because the local daemon was unavailable; Compose configuration was checked.

## Validation

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/validate_notebooks.py
node --check dashboard/static/js/app.js
python scripts/smoke_dashboard.py \
  --video dashboard/sample_videos/hcm_traffic_short.mp4 \
  --model models/best.pt
```

The automated tests use generated video frames and a fake tracker to verify control and persistence behavior without downloading weights. The separate smoke script uses the real checkpoint and ByteTrack, processes the entire supplied sample, checks statistics/export/completion, and saves evidence under ignored `outputs/validation/`. See [validation results](../docs/validation.md).
