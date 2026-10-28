# Local validation — 28 October 2026

The GitHub baseline (`211dfdd`) was compared with the current Drive project folder. The latest dashboard source (26 September snapshot), ten fine-tuning notebooks, two tracking notebooks and two database notebooks were imported; existing baseline sources and metrics were preserved. File provenance is recorded in [drive-import-manifest.json](drive-import-manifest.json).

## Environment

macOS arm64, Python 3.11.15, Ultralytics 8.4.116, PyTorch 2.14.1, torchvision 0.29.1, OpenCV 4.14.0.94, Flask 3.1.3, lap 0.5.13. Inference ran on CPU. Dashboard and baseline requirements install together, and `pip check` reports no broken requirements.

## Checks

- 29 pytest regression cases pass: session lifecycle, concurrent/duplicate starts, malformed configuration, old schema migration, class normalization, exact-zero crossing in both directions, majority votes, duplicate count prevention, stale track cleanup, DB traversal/symlink rejection, worker write failure reporting, capture release, safe handling of a slow worker stop, historical query and CSV export.
- Python sources compile; dashboard JavaScript passes `node --check`.
- All 17 notebooks pass nbformat validation; 148 nonempty code cells compile after IPython transformation. Two invalid stream-output metadata fields were removed during import.
- Baseline train/evaluate/dataset-inspection CLIs open their `--help` successfully.
- Docker Compose resolves successfully with portable local mounts. The Docker daemon was unavailable, so container build and execution were not tested.

## Real model pipeline

Executed from the repository root:

```bash
python scripts/smoke_dashboard.py \
  --video dashboard/sample_videos/hcm_traffic_short.mp4 \
  --model models/best.pt
```

The script exercises Flask preview/configuration/start, the real YOLO model and ByteTrack worker, SQLite event writing, statistics, detail queries, CSV export and end-of-video cleanup.

| Observation | Result |
|---|---|
| Input | `hcm_traffic_short.mp4`, 634×374, 30 FPS |
| Frames processed | 149 / 149 |
| Counted crossing events | 6 |
| Direction totals with horizontal mid-frame line | South: 1 bus + 4 motorbikes; North: 1 motorbike |
| Final smoothed processing FPS | 53.9 (one local run; not a benchmark) |
| Worker errors | None |
| SQLite, live statistics and CSV | Successful |
| End-of-video | Worker stopped and database disconnected |

Model SHA-256: `ee04b28824ef58c76906f3a0f592701873e2c8d9c66f62acf54ae1ca10f77210`.

Video SHA-256: `ae3c492ee855d2e4de22ce27fb656156a06c7cfc98b36ac84cae042ec41eb44b`.

The local smoke JSON, CSV, last annotated JPEG and session database are saved under ignored `outputs/validation/`. The six events demonstrate pipeline behavior, not counting accuracy against human annotations. Wall-clock event times differ on reruns.

The browser interface was also exercised on localhost: source selection, manual line coordinates, Start, automatic end-of-video stop and reconnecting the saved six-event database. Counts read back as 1 bus and 5 motorbikes. The responsive preview and persisted dropdown choices were checked in a narrow browser panel.

## Fixes validated

- Replaced `/app`-only defaults and Windows `D:` Compose mounts with configurable local paths.
- Upgraded legacy databases with the FPS column before querying or appending; preserved historical rows.
- Unified `motorcycle`, `motobike` and `motobyte` under the displayed `motorbike` class.
- Preserved the previous nonzero side when a tracked center lands on the counting line.
- Propagated failed event writes to the API and always released video capture resources.
- Rejected overlapping starts and serialized session-changing browser requests.
- Validated line geometry and direction names before starting a worker.
- Restricted YouTube input to recognized URL hosts, protected database paths against symlink escapes and rendered query values as plain text.
- Preserved dropdown choices when list requests complete and made the video panel usable on narrow screens.

## Limits

Full training, dataset-backed mAP evaluation, quantitative tracking/counting accuracy and live YouTube playback were not rerun. The notebooks still depend on their original Colab/data inputs. This remains a local, single-operator application; loading the home page resets the current session, as in the Drive source. It is not validated for multi-user or production hosting.
