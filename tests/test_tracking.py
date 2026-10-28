import pytest
import numpy as np

from services.line_crossing_service import LineCrossingSession
from services.tracker_service import normalize_class_name
from services.video_worker import VideoWorker
from services.youtube_service import is_youtube_url


@pytest.mark.parametrize('positions,direction', [([2, 1, 0, -1], 'North'), ([-2, -1, 0, 1], 'South')])
def test_crossing_through_zero_once_with_majority_vote(positions, direction):
    session = LineCrossingSession(0, 0, 10, 0, 'South', 'North')
    events = []
    for frame, y in enumerate(positions):
        event = session.process_detection(1, 'car' if frame != 1 else 'bus', 5, y, frame)
        if event: events.append(event)
    assert len(events) == 1
    assert events[0]['direction'] == direction and events[0]['class_name'] == 'car'
    assert session.process_detection(1, 'car', 5, -positions[-1], 5) is None
    assert session.purge_stale(400) == 1


@pytest.mark.parametrize('label', ['motorcycle', 'motobyte', 'motobike', ' MOTORBIKE '])
def test_motorcycle_labels(label):
    assert normalize_class_name(label) == 'motorbike'


@pytest.mark.parametrize('url,valid', [
    ('https://www.youtube.com/watch?v=abc', True), ('https://youtu.be/abc', True),
    ('https://youtube.com/live/abc', True), ('https://evil.test/youtu.be/abc', False),
    ('https://youtube.com.evil.test/watch?v=abc', False),
    ('file:///tmp/youtu.be/abc', False), ('https://youtube.com/watch?v=', False),
])
def test_youtube_source_validation(url, valid):
    assert is_youtube_url(url) is valid


def test_worker_reports_write_failure_and_releases_capture(config):
    class Capture:
        released = False
        def isOpened(self): return True
        def read(self): return True, np.zeros((48, 64, 3), dtype=np.uint8)
        def release(self): self.released = True
    class Tracker:
        index = 0
        def process_frame(self, frame):
            self.index += 1
            y = 25 if self.index < 3 else 15
            return [dict(track_id=1, class_name='car', cx=20, cy=y, x1=10, y1=10, x2=30, y2=30)]
    def fail(event): raise RuntimeError('database write failed')
    cap = Capture()
    worker = VideoWorker('test', 'test', config, fail, tracker_factory=lambda _: Tracker(), capture_factory=lambda _: cap)
    worker.start()
    worker._thread.join(timeout=5)
    assert not worker.is_alive()
    assert worker.error_message == 'database write failed'
    assert cap.released
