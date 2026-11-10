import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from backend.app import app
from backend.config import TEMP_DIR, OUTPUT_DIR
from backend.modules.audio_extraction import get_video_metadata
from backend.modules.subtitle_generator import extract_clip_subtitles, generate_ass_file
from backend.modules.metadata_generator import generate_shorts_metadata
from backend.modules.video_editor import render_vertical_short, detect_speaker_focus
from backend.database.db import get_clip

def test_phase3_automatic_shorts_generation():
    print("=" * 60)
    print("STARTING PHASE 3 AUTOMATIC SHORTS GENERATION VERIFICATION")
    print("=" * 60)

    # -------------------------------------------------------------
    # TEST 1: Unit Test Subtitle Generator & ASS Formatting
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Subtitle Extraction & Styled ASS Generation...")
    sample_segments = [
        {
            "start": 0.0,
            "end": 6.5,
            "text": "Did you know this crazy trick?",
            "words": [
                {"word": "Did", "start": 0.0, "end": 0.3},
                {"word": "you", "start": 0.3, "end": 0.5},
                {"word": "know", "start": 0.5, "end": 0.9},
                {"word": "this", "start": 0.9, "end": 1.2},
                {"word": "crazy", "start": 1.2, "end": 1.8},
                {"word": "trick?", "start": 1.8, "end": 2.5}
            ]
        }
    ]
    sub_lines = extract_clip_subtitles(sample_segments, clip_start=0.0, clip_end=5.0, max_words_per_line=3)
    print(f" -> Generated {len(sub_lines)} subtitle phrase lines:")
    for l in sub_lines:
        print(f"    [{l['start']}s -> {l['end']}s]: \"{l['text']}\"")
    assert len(sub_lines) >= 2, "Should group into short mobile phrases"

    ass_output = TEMP_DIR / "unit_test_subs.ass"
    ass_path = generate_ass_file(sub_lines, str(ass_output))
    assert Path(ass_path).exists(), "ASS file should be created"
    with open(ass_path, "r", encoding="utf-8") as f:
        ass_content = f.read()
    assert "PlayResX: 720" in ass_content
    assert "PlayResY: 1280" in ass_content
    assert "ViralShorts" in ass_content
    print(" [PASSED] Subtitle extraction and styled ASS generation verified.")

    # -------------------------------------------------------------
    # TEST 2: Unit Test Metadata Generation (Title, Description, Hashtags)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing YouTube Shorts Metadata Generator...")
    meta = generate_shorts_metadata(
        clip_text="Did you know artificial intelligence can edit videos 10x faster?",
        base_title="AI Video Secret"
    )
    print(f" -> Title: {meta['title']}")
    print(f" -> Hashtags: {meta['hashtags']}")
    print(f" -> Category: {meta['category']}")
    assert "#Shorts" in meta["title"]
    assert "#AI" in meta["hashtags"]
    assert len(meta["description"]) > 50
    print(" [PASSED] YouTube Shorts metadata generation verified.")

    # -------------------------------------------------------------
    # TEST 3: Video Editor 9:16 Vertical Render (720x1280, loudnorm, sub)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing 9:16 Vertical Video Rendering with FFmpeg...")
    test_src_video = TEMP_DIR / "sample_test_video.mp4"
    if not test_src_video.exists():
        raise FileNotFoundError("Source test video not found.")

    rendered_path = render_vertical_short(
        video_path=str(test_src_video),
        clip_id="test_render_clip",
        start_time=0.0,
        end_time=5.0,
        video_width=1280,
        video_height=720,
        ass_subtitle_path=str(ass_output),
        layout_mode="smart_crop",
        target_width=720,
        target_height=1280
    )
    assert Path(rendered_path).exists(), f"Rendered video missing at {rendered_path}"
    print(f" -> Rendered 9:16 Short size: {os.path.getsize(rendered_path)} bytes")

    # Inspect rendered video with FFprobe
    out_meta = get_video_metadata(rendered_path)
    print(f" -> Rendered Dimensions: {out_meta['width']}x{out_meta['height']}")
    print(f" -> Rendered Duration: {out_meta['duration']}s")
    print(f" -> Audio Codec: {out_meta['audio_codec']}, Video Codec: {out_meta['video_codec']}")
    assert out_meta["width"] == 720, f"Expected 720 width, got {out_meta['width']}"
    assert out_meta["height"] == 1280, f"Expected 1280 height, got {out_meta['height']}"
    assert out_meta["duration"] > 0
    print(" [PASSED] 9:16 vertical render and metadata verified.")

    # -------------------------------------------------------------
    # TEST 4: End-to-End API Flow (Upload -> Detect -> Render -> Preview Video)
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing FastAPI End-to-End Flow for Phase 3...")
    with TestClient(app) as client:
        # Check active phase
        res = client.get("/")
        assert res.status_code == 200
        print(f" -> API Active Phase: {res.json()['phase']}")

        # Upload video
        with open(test_src_video, "rb") as f:
            up_res = client.post("/api/videos/upload", files={"file": ("shorts_test.mp4", f, "video/mp4")})
        assert up_res.status_code == 200
        video_id = up_res.json()["video"]["id"]

        # Wait for processing
        print(" -> Awaiting video transcription and clip detection...")
        max_wait = 30
        completed = False
        for _ in range(max_wait):
            st = client.get(f"/api/videos/{video_id}/status").json()["status"]
            if st == "completed":
                completed = True
                break
            time.sleep(1)
        assert completed, "Pipeline failed to complete in time"

        # Fetch clips
        clips_res = client.get(f"/api/videos/{video_id}/clips")
        assert clips_res.status_code == 200
        clips = clips_res.json()["clips"]
        assert len(clips) > 0
        clip_id = clips[0]["id"]
        print(f" -> Selected Clip ID to Render: {clip_id}")

        # Call Render Endpoint
        print(" -> Rendering vertical Short via /api/clips/{clip_id}/render...")
        render_res = client.post(
            f"/api/clips/{clip_id}/render",
            json={"layout_mode": "smart_crop", "include_subtitles": True}
        )
        assert render_res.status_code == 200, f"Render failed: {render_res.text}"
        rendered_clip = render_res.json()["clip"]
        assert rendered_clip["status"] == "rendered"
        assert os.path.exists(rendered_clip["output_path"])
        print(f" -> Short rendered at: {rendered_clip['output_path']}")
        print(f" -> Generated YouTube Title: \"{rendered_clip['title']}\"")

        # Stream / Preview video endpoint
        video_stream_res = client.get(f"/api/clips/{clip_id}/video")
        assert video_stream_res.status_code == 200
        assert video_stream_res.headers["content-type"] == "video/mp4"
        print(f" -> Video preview stream verified (size: {len(video_stream_res.content)} bytes)")

    print("\n" + "=" * 60)
    print("ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase3_automatic_shorts_generation()
