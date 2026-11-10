import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from backend.app import app
from backend.config import TEMP_DIR
from backend.database.db import get_dashboard_analytics, list_youtube_uploads

def test_phase4_fullstack_and_youtube():
    print("=" * 60)
    print("STARTING PHASE 4 FULL-STACK & YOUTUBE INTEGRATION VERIFICATION")
    print("=" * 60)

    with TestClient(app) as client:
        # -------------------------------------------------------------
        # TEST 1: System Health, JSON Root & HTML Root
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing Root Routing (API JSON vs Browser HTML)...")
        json_res = client.get("/", headers={"accept": "application/json"})
        assert json_res.status_code == 200
        root_data = json_res.json()
        print(f" -> Active Phase: {root_data['phase']}")
        assert "Phase 4" in root_data["phase"]

        html_res = client.get("/", headers={"accept": "text/html"})
        assert html_res.status_code == 200
        assert "<title>ViralCut AI" in html_res.text
        print(" [PASSED] Smart root routing (API JSON and Web Dashboard HTML) verified.")

        # -------------------------------------------------------------
        # TEST 2: Dashboard Analytics Metrics Endpoint
        # -------------------------------------------------------------
        print("\n[TEST 2] Testing Dashboard Analytics Endpoint...")
        analytics_res = client.get("/api/dashboard/analytics")
        assert analytics_res.status_code == 200
        analytics = analytics_res.json()
        print(f" -> Total Videos Tracked: {analytics['total_videos']}")
        print(f" -> Total Shorts Generated: {analytics['total_shorts']}")
        print(f" -> Completed YouTube Uploads: {analytics['completed_uploads']}")
        assert "total_videos" in analytics
        assert "total_shorts" in analytics
        print(" [PASSED] Dashboard analytics metrics endpoint verified.")

        # -------------------------------------------------------------
        # TEST 3: YouTube Status Endpoint
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing YouTube OAuth & Connection Status Endpoint...")
        yt_status_res = client.get("/api/youtube/status")
        assert yt_status_res.status_code == 200
        yt_status = yt_status_res.json()
        print(f" -> Mode: {yt_status['mode']}")
        print(f" -> Configured: {yt_status['configured']}, Authenticated: {yt_status['authenticated']}")
        assert "mode" in yt_status
        print(" [PASSED] YouTube status endpoint verified.")

        # -------------------------------------------------------------
        # TEST 4: Full End-to-End Pipeline through YouTube Publishing
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing Video Upload -> Detection -> Render -> YouTube Upload...")
        test_src_video = TEMP_DIR / "sample_test_video.mp4"
        if not test_src_video.exists():
            raise FileNotFoundError("Source test video not found.")

        # Step 4.1: Upload video
        with open(test_src_video, "rb") as f:
            up_res = client.post("/api/videos/upload", files={"file": ("phase4_test.mp4", f, "video/mp4")})
        assert up_res.status_code == 200
        video_id = up_res.json()["video"]["id"]
        print(f" -> Uploaded Video ID: {video_id}")

        # Step 4.2: Wait for auto processing
        max_wait = 30
        completed = False
        for _ in range(max_wait):
            st = client.get(f"/api/videos/{video_id}/status").json()["status"]
            if st == "completed":
                completed = True
                break
            time.sleep(1)
        assert completed, "Video pipeline failed to complete"

        # Step 4.3: Fetch clips
        clips_res = client.get(f"/api/videos/{video_id}/clips")
        assert clips_res.status_code == 200
        clips = clips_res.json()["clips"]
        assert len(clips) > 0
        clip_id = clips[0]["id"]

        # Step 4.4: Render 9:16 Short
        print(f" -> Rendering 9:16 Short for Clip: {clip_id}...")
        render_res = client.post(
            f"/api/clips/{clip_id}/render",
            json={"layout_mode": "smart_crop", "include_subtitles": True}
        )
        assert render_res.status_code == 200
        rendered_clip = render_res.json()["clip"]
        assert rendered_clip["status"] == "rendered"
        print(f" -> Short rendered successfully: {rendered_clip['output_path']}")

        # Step 4.5: Publish to YouTube Shorts
        print(f" -> Publishing Short to YouTube via /api/clips/{clip_id}/upload-youtube...")
        upload_yt_res = client.post(
            f"/api/clips/{clip_id}/upload-youtube",
            json={
                "privacy_status": "public",
                "custom_title": "The Most Insane AI Video Secret! #Shorts",
                "custom_description": "Discover how AI cuts viral moments in seconds.\n\n#Shorts #Viral"
            }
        )
        assert upload_yt_res.status_code == 200, f"YouTube upload failed: {upload_yt_res.text}"
        upload_record = upload_yt_res.json()["upload"]
        assert upload_record["upload_status"] == "published"
        assert upload_record["youtube_video_id"]
        print(f" -> Published Status: {upload_record['upload_status']}")
        print(f" -> YouTube Video ID: {upload_record['youtube_video_id']}")
        print(f" -> YouTube Shorts URL: {upload_record['youtube_url']}")

        # Step 4.6: Verify in YouTube Uploads History List
        history_res = client.get("/api/youtube/uploads")
        assert history_res.status_code == 200
        history = history_res.json()
        assert history["count"] > 0
        print(f" -> Total YouTube Shorts in Publish Log: {history['count']}")
        print(" [PASSED] Full pipeline through YouTube publishing verified.")

    print("\n" + "=" * 60)
    print("ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase4_fullstack_and_youtube()
