#!/usr/bin/env python3
"""Run the real YOLO/ByteTrack dashboard pipeline on a short local video."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('outputs/validation'))
    parser.add_argument('--timeout', type=float, default=180)
    args = parser.parse_args()
    video, model, output = args.video.resolve(), args.model.resolve(), args.output.resolve()
    if not video.is_file() or not model.is_file():
        parser.error('Both --video and --model must name existing files.')
    output.mkdir(parents=True, exist_ok=True)
    os.environ.update(VIDEO_DIR=str(video.parent), MODEL_DIR=str(model.parent), DATA_DIR=str(output / 'sessions'),
                      YOLO_CONFIG_DIR=str(output / 'yolo'), MPLCONFIGDIR=str(output / 'matplotlib'))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
    import app as dashboard
    import cv2
    from importlib.metadata import version

    # Use the exact supplied checkpoint even if its folder contains other models.
    dashboard._get_model_path = lambda: str(model)
    client = dashboard.app.test_client()
    assert client.get('/').status_code == 200
    preview = client.post('/api/video/first_frame', json={'filename': video.name})
    assert preview.status_code == 200, preview.json
    width, height = preview.json['width'], preview.json['height']
    config = dict(video_filename=video.name, source_type='local', x1=0, y1=height / 2,
                  x2=width, y2=height / 2, frame_width=width, frame_height=height,
                  huong_1_label='South', huong_2_label='North')
    assert client.post('/api/config/crossline', json=config).json['ok']
    started = client.post('/api/session/start')
    assert started.status_code == 200, started.json
    worker = dashboard._video_worker
    deadline = time.monotonic() + args.timeout
    last_print = -1
    try:
        while worker.is_alive() and time.monotonic() < deadline:
            if worker.frame_index // 25 != last_print:
                last_print = worker.frame_index // 25
                print(f'Processed {worker.frame_index}/{preview.json["total_frames"]} frames', flush=True)
            time.sleep(0.1)
        assert not worker.is_alive(), 'Timed out waiting for inference'
        assert not worker.error_message, worker.error_message
        assert worker.video_ended
        assert worker.frame_index == preview.json['total_frames']
        assert worker.get_latest_frame_base64()
        stats = client.get('/api/stats/live')
        assert stats.status_code == 200, stats.json
        params = dict(tu_thoi_diem='2000-01-01T00:00', den_thoi_diem='2100-01-01T00:00')
        detail = client.get('/api/query_detail', query_string=params)
        assert detail.status_code == 200, detail.json
        csv = client.get('/api/query_detail/export_csv', query_string=params)
        assert csv.status_code == 200 and csv.data.startswith(b'\xef\xbb\xbf')
        (output / 'events.csv').write_bytes(csv.data)
        import base64
        (output / 'last-frame.jpg').write_bytes(base64.b64decode(worker.get_latest_frame_base64().split(',', 1)[1]))
        ended = client.get('/api/video/live_frame')
        assert ended.json['video_ended'] and not dashboard.get_db_state()['dang_chay']
        result = dict(frames=worker.frame_index, video_frames=preview.json['total_frames'],
                      dimensions=[width, height], crossing_events=detail.json['total_events'],
                      stats=stats.json['counts'], final_smoothed_fps=worker.current_fps,
                      database=started.json['db_path'],
                      model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                      video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
                      versions={name: version(name) for name in ('ultralytics','torch','torchvision','opencv-python','Flask','lap')})
        (output / 'smoke-result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
    finally:
        dashboard._stop_video_worker_if_running()


if __name__ == '__main__':
    main()
