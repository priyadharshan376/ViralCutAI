import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from backend.app import app
from backend.config import BASE_DIR, TEMP_DIR, VIDEOS_DIR
from backend.modules.audio_extraction import get_video_metadata, extract_audio
from backend.modules.transcription import get_transcriber
from backend.database.db import get_video, get_transcript, list_videos

def test_phase1_pipeline():
    print("=" * 60)
    print("STARTING PHASE 1 VERIFICATION & BENCHMARK")
    print("=" * 60)

    sample_video = TEMP_DIR / "sample_test_video.mp4"
    if not sample_video.exists():
        raise FileNotFoundError(f"Test video not found at {sample_video}")

    # 1. Test Video Metadata Extraction
    print("\n[TEST 1] Testing Metadata Extraction via FFprobe...")
    metadata = get_video_metadata(str(sample_video))
    print(f" -> Duration: {metadata['duration']}s")
    print(f" -> Resolution: {metadata['width']}x{metadata['height']}")
    print(f" -> Framerate: {metadata['fps']} fps")
    print(f" -> Video Codec: {metadata['video_codec']}, Audio Codec: {metadata['audio_codec']}")
    assert metadata["duration"] > 0, "Duration should be greater than 0"
    assert metadata["width"] == 1280, f"Expected width 1280, got {metadata['width']}"
    assert metadata["height"] == 720, f"Expected height 720, got {metadata['height']}"
    print(" [PASSED] Metadata extraction verified.")

    # 2. Test Audio Extraction
    print("\n[TEST 2] Testing Audio Extraction (16kHz Mono WAV) via FFmpeg...")
    extracted_wav = TEMP_DIR / "unit_test_audio.wav"
    out_audio = extract_audio(str(sample_video), str(extracted_wav))
    assert Path(out_audio).exists(), "Extracted audio file does not exist"
    wav_size = os.path.getsize(out_audio)
    print(f" -> Generated WAV size: {wav_size} bytes")
    assert wav_size > 1000, "Extracted audio should contain data"
    print(" [PASSED] Audio extraction verified.")

    # 3. Test Faster-Whisper Transcription (CPU INT8)
    print("\n[TEST 3] Testing Faster-Whisper CPU INT8 Transcription...")
    start_time = time.time()
    transcriber = get_transcriber()
    result = transcriber.transcribe(str(extracted_wav))
    elapsed = time.time() - start_time
    print(f" -> Transcribed in {elapsed:.2f} seconds.")
    print(f" -> Detected Language: {result['language']} (confidence: {result['language_probability']})")
    print(f" -> Full Text: \"{result['full_text']}\"")
    print(f" -> Segments Count: {len(result['segments'])}")
    for seg in result["segments"]:
        print(f"    [{seg['start']}s -> {seg['end']}s]: {seg['text']}")
        if seg.get("words"):
            print(f"      (Sample word timestamps: {seg['words'][:3]}...)")

    assert len(result["full_text"]) > 0, "Transcript text should not be empty"
    assert len(result["segments"]) > 0, "Transcript should have at least 1 segment"
    print(" [PASSED] Faster-Whisper CPU INT8 transcription verified.")

    # 4. Test End-to-End FastAPI Endpoints
    print("\n[TEST 4] Testing FastAPI Endpoints (Upload, Background Task, Query)...")
    with TestClient(app) as client:
        # Health check
        res = client.get("/")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print(f" -> Root health check: {res.json()['status']}")

        # Video Upload
        with open(sample_video, "rb") as f:
            upload_res = client.post(
                "/api/videos/upload",
                files={"file": ("sample_test_video.mp4", f, "video/mp4")}
            )
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
        upload_data = upload_res.json()
        video_id = upload_data["video"]["id"]
        print(f" -> Uploaded Video ID: {video_id}")

        # Poll status until transcribed or timeout (max 30s)
        print(" -> Awaiting background processing pipeline...")
        max_wait = 30
        poll_interval = 1
        completed = False
        for _ in range(max_wait):
            status_res = client.get(f"/api/videos/{video_id}/status")
            assert status_res.status_code == 200
            curr_status = status_res.json()["status"]
            if curr_status in ["transcribed", "completed"]:
                completed = True
                break
            elif curr_status == "failed":
                raise RuntimeError(f"Processing failed: {status_res.json().get('error_message')}")
            time.sleep(poll_interval)

        assert completed, f"Pipeline did not complete within {max_wait} seconds."
        print(" -> Background pipeline completed with status 'transcribed'!")

        # Verify Video Details & Transcript endpoint
        details_res = client.get(f"/api/videos/{video_id}")
        assert details_res.status_code == 200
        details = details_res.json()
        print(f" -> Stored Duration: {details['duration']}s, Codec: {details['video_codec']}")
        assert details["duration"] > 0

        transcript_res = client.get(f"/api/videos/{video_id}/transcript")
        assert transcript_res.status_code == 200
        transcript_data = transcript_res.json()
        print(f" -> Saved Transcript Language: {transcript_data['language']}")
        print(f" -> Saved Transcript Segment Count: {len(transcript_data['segments'])}")
        assert len(transcript_data["segments"]) > 0
        print(" [PASSED] Full FastAPI end-to-end flow verified.")

    print("\n" + "=" * 60)
    print("ALL PHASE 1 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase1_pipeline()
