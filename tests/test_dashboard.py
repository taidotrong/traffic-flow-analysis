import json
import shutil
import sqlite3
from pathlib import Path

import pytest


def test_initial_page_and_invalid_actions(dashboard):
    client = dashboard.app.test_client()
    assert client.get('/').status_code == 200
    assert client.get('/static/js/app.js').status_code == 200
    assert client.get('/api/video/list').json['files'] == []
    assert client.get('/api/db/list').json['files'] == []
    assert not client.get('/api/db/status').json['connected']
    for endpoint in ('start', 'stop', 'pause', 'resume'):
        assert client.post('/api/session/' + endpoint).status_code == 400
    assert client.get('/api/stats/live').status_code == 400
    assert client.get('/api/query_detail').status_code == 400
    assert client.post('/api/video/youtube_first_frame', json={'youtube_url': 'https://evil.test/youtu.be/id'}).status_code == 400


def test_preview_and_session_lifecycle(ready_dashboard):
    d = ready_dashboard
    client = d.app.test_client()
    preview = client.post('/api/video/first_frame', json={'filename': 'traffic.avi'})
    assert preview.status_code == 200
    assert (preview.json['width'], preview.json['height'], preview.json['total_frames']) == (64, 48, 3)
    assert preview.json['image_base64'].startswith('data:image/jpeg;base64,')
    started = client.post('/api/session/start')
    assert started.json['action'] == 'create'
    worker = d._video_worker
    assert client.post('/api/session/start').status_code == 409
    assert d._video_worker is worker
    assert client.post('/api/db/disconnect').status_code == 400
    assert client.post('/api/config/crossline', json={}).status_code == 400
    assert client.post('/api/session/pause').json['ok'] and worker.paused
    assert client.post('/api/session/resume').json['ok'] and not worker.paused
    assert client.get('/api/video/live_frame').json['current_fps'] == 12.5
    assert client.post('/api/session/stop').json['ok']
    assert not worker.alive
    assert not client.get('/api/db/status').json['connected']
    assert not json.loads((Path(started.json['db_path']).parent / 'crossline_config.json').read_text())['locked']
    # A new automatic session must not append to the previous database.
    second = client.post('/api/session/start')
    assert second.json['db_path'] != started.json['db_path']
    assert client.get('/').status_code == 200
    assert not d.get_db_state()['dang_chay']


@pytest.mark.parametrize('field,value', [
    ('x1', 'zero'), ('x1', float('nan')), ('x1', -1), ('x2', 65),
    ('frame_width', 0), ('source_type', 'other'), ('huong_1_label', 'North'),
])
def test_reject_invalid_configuration_before_creating_session(ready_dashboard, config, field, value):
    d = ready_dashboard
    config[field] = value
    d.save_json(d.STAGING_CONFIG_PATH, config)
    assert d.app.test_client().post('/api/session/start').status_code == 400
    assert d._video_worker is None
    assert not list(Path(d.DATA_DIR).rglob('*.db'))


def test_legacy_database_migration_query_export_and_reuse(ready_dashboard, config):
    d = ready_dashboard
    db = Path(d.DATA_DIR) / 'legacy.db'
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'dashboard/sample_data/he_thong_dem_xe_sample.db', db)
    with sqlite3.connect(db) as conn:
        assert 'fps_tai_thoi_diem' not in {row[1] for row in conn.execute('PRAGMA table_info(lich_su_dem)')}
        count_before = conn.execute('SELECT COUNT(*) FROM lich_su_dem').fetchone()[0]
    client = d.app.test_client()
    assert client.post('/api/db/select', json={'filename': 'legacy.db'}).json['ok']
    d.save_json(str(db.parent / 'crossline_config.json'), config)
    d._make_db_event_writer(str(db))(dict(timestamp=d.now_vn_string(), class_name='motorcycle', direction='South', track_id=999, fps_tai_thoi_diem=11.5))
    stats = client.get('/api/stats/live').json
    assert next(row for row in stats['counts'] if row['class_key'] == 'motorbike')['huong_1'] >= 1
    query = '?tu_thoi_diem=2000-01-01T00:00&den_thoi_diem=2100-01-01T00:00'
    detail = client.get('/api/query_detail' + query)
    assert detail.status_code == 200
    assert detail.json['total_events'] == count_before + 1
    assert any(row['fps_tai_thoi_diem'] is None for row in detail.json['detail'])
    csv = client.get('/api/query_detail/export_csv' + query)
    assert csv.status_code == 200 and csv.data.startswith(b'\xef\xbb\xbf')
    assert b'fps_tai_thoi_diem' in csv.data
    started = client.post('/api/session/start')
    assert started.json['action'] == 'reuse'
    assert started.json['db_path'] == str(db)


def test_database_traversal_and_symlinks_rejected(dashboard, tmp_path):
    outside = tmp_path / 'outside.db'
    dashboard.create_db_schema(str(outside))
    (Path(dashboard.DATA_DIR) / 'link.db').symlink_to(outside)
    client = dashboard.app.test_client()
    for filename in ('../outside.db', str(outside), 'link.db'):
        assert client.post('/api/db/select', json={'filename': filename}).status_code == 400


@pytest.mark.parametrize('finished', ['video_ended', 'error_message'])
def test_worker_completion_disconnects_and_unlocks(ready_dashboard, finished):
    d = ready_dashboard
    client = d.app.test_client()
    db = client.post('/api/session/start').json['db_path']
    setattr(d._video_worker, finished, True if finished == 'video_ended' else 'write failed')
    result = client.get('/api/video/live_frame').json
    assert result['ok'] == (finished == 'video_ended')
    assert not d.get_db_state()['dang_chay'] and not d.get_db_state()['db_path']
    assert not d.load_json(str(Path(db).parent / 'crossline_config.json'), {})['locked']


def test_concurrent_start_creates_only_one_worker(ready_dashboard):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    d = ready_dashboard
    barrier = Barrier(2)
    def start():
        with d.app.test_client() as client:
            barrier.wait()
            return client.post('/api/session/start').status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: start(), range(2)))
    assert sorted(statuses) == [200, 409]
    assert len(list(Path(d.DATA_DIR).rglob('*.db'))) == 1


def test_slow_stop_retains_worker_and_database(ready_dashboard, monkeypatch):
    d = ready_dashboard
    client = d.app.test_client()
    client.post('/api/session/start')
    worker = d._video_worker
    monkeypatch.setattr(worker, 'stop', lambda: None)
    assert client.post('/api/session/stop').status_code == 409
    assert d._video_worker is worker and d.get_db_state()['dang_chay']
    assert client.post('/api/session/start').status_code == 409
    worker.alive = False
    assert client.post('/api/session/stop').json['ok']
    assert d._video_worker is None and not d.get_db_state()['db_path']
