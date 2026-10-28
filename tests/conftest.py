import importlib
from pathlib import Path

import pytest


@pytest.fixture
def dashboard(monkeypatch, tmp_path):
    monkeypatch.setenv('VIDEO_DIR', str(tmp_path / 'videos'))
    monkeypatch.setenv('DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setenv('MODEL_DIR', str(tmp_path / 'models'))
    module = importlib.import_module('app')
    for name in ('VIDEO_DIR', 'DATA_DIR', 'MODEL_DIR'):
        path = tmp_path / name.lower()
        path.mkdir()
        monkeypatch.setattr(module, name, str(path))
    monkeypatch.setattr(module, 'DB_STATE_PATH', str(tmp_path / 'data_dir/db_path_state.json'))
    monkeypatch.setattr(module, 'STAGING_CONFIG_PATH', str(tmp_path / 'data_dir/crossline_staging.json'))
    monkeypatch.setattr(module, '_video_worker', None)
    module.app.config.update(TESTING=True)
    yield module
    module._stop_video_worker_if_running()


@pytest.fixture
def config():
    return dict(video_filename='traffic.avi', source_type='local', x1=0, y1=20,
                x2=63, y2=20, frame_width=64, frame_height=48,
                huong_1_label='South', huong_2_label='North')


@pytest.fixture
def ready_dashboard(dashboard, config, monkeypatch):
    import cv2
    import numpy as np
    video = Path(dashboard.VIDEO_DIR) / 'traffic.avi'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 10, (64, 48))
    assert writer.isOpened()
    for _ in range(3):
        writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
    writer.release()
    (Path(dashboard.MODEL_DIR) / 'best.pt').touch()

    class Worker:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.error_message = None
            self.video_ended = False
            self.current_fps = 12.5
            self.paused = False
            self.alive = False
        def start(self): self.alive = True
        def stop(self): self.alive = False
        def is_alive(self): return self.alive
        def pause(self): self.paused = True
        def resume(self): self.paused = False
        def get_latest_frame_base64(self): return 'data:image/jpeg;base64,test'

    monkeypatch.setattr(dashboard, 'VideoWorker', Worker)
    dashboard.save_json(dashboard.STAGING_CONFIG_PATH, config)
    return dashboard
