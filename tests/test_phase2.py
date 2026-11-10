import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from backend.app import app
from backend.config import BASE_DIR, TEMP_DIR
from backend.modules.transcript_analysis import segment_transcript
from backend.modules.viral_scoring import (
    score_clip_candidate,
    analyze_hook,
    analyze_emotion,
    analyze_information,
    analyze_storytelling,
    analyze_context_completeness,
    analyze_engagement,
    WEIGHTS
)
from backend.modules.clip_detection import suppress_overlapping_clips, detect_and_rank_clips
from backend.database.db import get_video, get_clips_by_video_id, get_clip

def test_phase2_viral_detection():
    print("=" * 60)
    print("STARTING PHASE 2 AI VIRAL CLIP DETECTION VERIFICATION")
    print("=" * 60)

    # -------------------------------------------------------------
    # TEST 1: Unit Test Viral Scoring Algorithm & Formulas
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing 6-Dimension Viral Scoring Engine...")
    viral_hook_text = (
        "Did you know the biggest mistake 99% of creators make? "
        "It started when I lost all my views. Suddenly, I discovered this insane trick "
        "that increased my engagement by 10x! Comment below if you tried this."
    )
    scores = score_clip_candidate(viral_hook_text)
    print(f" -> Hook Score: {scores['hook_score']} (Reason: {scores['reason']})")
    print(f" -> Emotional Score: {scores['emotional_score']}")
    print(f" -> Information Score: {scores['information_score']}")
    print(f" -> Storytelling Score: {scores['storytelling_score']}")
    print(f" -> Context Score: {scores['context_score']}")
    print(f" -> Engagement Score: {scores['engagement_score']}")
    print(f" -> Weighted Viral Score: {scores['viral_score']}")
    print(f" -> Generated Title: \"{scores['title']}\"")

    # Verify formula math
    expected_weighted = round(
        (scores['hook_score'] * WEIGHTS["hook"]) +
        (scores['emotional_score'] * WEIGHTS["emotion"]) +
        (scores['information_score'] * WEIGHTS["information"]) +
        (scores['storytelling_score'] * WEIGHTS["storytelling"]) +
        (scores['context_score'] * WEIGHTS["context"]) +
        (scores['engagement_score'] * WEIGHTS["engagement"]),
        1
    )
    assert abs(scores['viral_score'] - expected_weighted) < 0.1, "Formula weighting mismatch!"
    assert scores['viral_score'] >= 75.0, f"Expected high viral score for viral hook text, got {scores['viral_score']}"
    print(" [PASSED] Viral scoring formulas and 6-dimension weighting verified.")

    # -------------------------------------------------------------
    # TEST 2: Unit Test Transcript Window Segmentation & Overlap Suppression
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Transcript Window Segmentation & Overlap Suppression...")
    dummy_segments = [
        {"start": 0.0, "end": 4.5, "text": "Did you know why videos go viral?"},
        {"start": 4.5, "end": 9.2, "text": "The secret is capturing attention in the first three seconds."},
        {"start": 9.2, "end": 14.0, "text": "If you fail at that, people immediately swipe away."},
        {"start": 14.0, "end": 19.5, "text": "Suddenly, your reach drops down to zero."},
        {"start": 19.5, "end": 25.0, "text": "That is why hooks are the most important part of any Short."},
        {"start": 25.0, "end": 30.5, "text": "Always remember to test different opening questions."},
        {"start": 30.5, "end": 36.0, "text": "Tell me in the comments what hook works best for you."}
    ]

    windows = segment_transcript(dummy_segments, min_duration=12.0, max_duration=25.0)
    print(f" -> Segmented {len(dummy_segments)} speech units into {len(windows)} candidate windows.")
    assert len(windows) >= 1, "Should generate candidate windows"
    for w in windows:
        assert 10.0 <= w["duration"] <= 26.0, f"Window duration out of bounds: {w['duration']}s"

    # Test overlap suppression
    overlapping_candidates = [
        {"id": "c1", "start_time": 0.0, "end_time": 20.0, "viral_score": 92.0},
        {"id": "c2", "start_time": 2.0, "end_time": 22.0, "viral_score": 75.0}, # Overlaps heavily with c1
        {"id": "c3", "start_time": 25.0, "end_time": 40.0, "viral_score": 85.0}  # Distinct interval
    ]
    suppressed = suppress_overlapping_clips(overlapping_candidates, overlap_threshold=0.5)
    print(f" -> Suppressed {len(overlapping_candidates)} candidates to {len(suppressed)} non-overlapping clips.")
    assert len(suppressed) == 2, f"Expected 2 non-overlapping clips, got {len(suppressed)}"
    assert suppressed[0]["id"] == "c1", "c1 should be kept as highest score"
    assert suppressed[1]["id"] == "c3", "c3 should be kept as distinct interval"
    print(" [PASSED] Window segmentation and overlap suppression verified.")

    # -------------------------------------------------------------
    # TEST 3: End-to-End Pipeline & API Verification with Real Audio/Video
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Complete Phase 2 API Flow with Multi-Sentence Video...")

    # Synthesize multi-sentence speech with strong hooks and emotional contrast
    sample_script = (
        "Did you know the secret to viral YouTube shorts? "
        "Most creators fail because they ramble for ten seconds. "
        "Suddenly, viewers swipe away and your video dies! "
        "Instead, start with an insane question and deliver the answer in thirty seconds. "
        "Tell me what you think in the comments."
    )
    temp_wav = TEMP_DIR / "phase2_speech.wav"
    temp_mp4 = TEMP_DIR / "phase2_test_video.mp4"

    # Generate speech WAV with Windows SAPI
    import subprocess
    ps_cmd = f"""
    Add-Type -AssemblyName System.Speech;
    $s = New-Object System.Speech.Synthesis.SpeechSynthesizer;
    $s.SetOutputToWaveFile('{str(temp_wav)}');
    $s.Speak('{sample_script}');
    $s.Dispose();
    """
    subprocess.run(["powershell", "-Command", ps_cmd], check=True)

    # Combine into MP4
    ff_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=purple:s=1280x720:r=30",
        "-i", str(temp_wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(temp_mp4)
    ]
    subprocess.run(ff_cmd, capture_output=True, check=True)

    # Test with FastAPI TestClient
    with TestClient(app) as client:
        # Check root phase
        root_res = client.get("/")
        assert root_res.status_code == 200
        print(f" -> Active Phase: {root_res.json()['phase']}")

        # Upload Video
        with open(temp_mp4, "rb") as f:
            upload_res = client.post(
                "/api/videos/upload",
                files={"file": ("phase2_test_video.mp4", f, "video/mp4")}
            )
        assert upload_res.status_code == 200
        video_id = upload_res.json()["video"]["id"]
        print(f" -> Uploaded Video ID: {video_id}")

        # Wait for pipeline to complete
        print(" -> Awaiting video processing & clip detection pipeline...")
        max_wait = 40
        completed = False
        for _ in range(max_wait):
            st_res = client.get(f"/api/videos/{video_id}/status")
            status = st_res.json()["status"]
            if status == "completed":
                completed = True
                break
            elif status == "failed":
                raise RuntimeError(f"Processing failed: {st_res.json().get('error_message')}")
            time.sleep(1)

        assert completed, f"Pipeline timed out after {max_wait}s."
        print(" -> Pipeline reached 'completed' status!")

        # Query Detected Clips Endpoint
        clips_res = client.get(f"/api/videos/{video_id}/clips")
        assert clips_res.status_code == 200
        clips_data = clips_res.json()
        print(f" -> Detected Clips Count: {clips_data['count']}")
        assert clips_data["count"] > 0, "At least 1 viral clip candidate should be detected"

        top_clip = clips_data["clips"][0]
        clip_id = top_clip["id"]
        print(f" -> Top Clip #{1}:")
        print(f"    Title: \"{top_clip['title']}\"")
        print(f"    Duration: {top_clip['duration']}s [{top_clip['start_time']}s -> {top_clip['end_time']}s]")
        print(f"    Viral Score: {top_clip['viral_score']} / 100")
        print(f"    Hook Score: {top_clip['hook_score']} | Emotion: {top_clip['emotional_score']}")
        print(f"    Reason: {top_clip['reason']}")
        print(f"    Text Excerpt: \"{top_clip['transcript_text'][:60]}...\"")

        # Verify Single Clip Details Endpoint
        clip_detail_res = client.get(f"/api/clips/{clip_id}")
        assert clip_detail_res.status_code == 200
        assert clip_detail_res.json()["id"] == clip_id

        # Test Updating Clip (Approve + Custom Title)
        patch_res = client.patch(
            f"/api/clips/{clip_id}",
            json={"status": "approved", "title": "The Secret to Viral Shorts That Explode!"}
        )
        assert patch_res.status_code == 200
        updated = patch_res.json()["clip"]
        assert updated["status"] == "approved"
        assert updated["title"] == "The Secret to Viral Shorts That Explode!"
        print(f" -> Clip {clip_id} status successfully updated to 'approved' with customized title.")

    print("\n" + "=" * 60)
    print("ALL PHASE 2 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase2_viral_detection()
