import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from backend.config import BASE_DIR

logger = logging.getLogger(__name__)

CLIENT_SECRETS_FILE = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "backend" / "database" / "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeUploader:
    def __init__(self):
        self.client_secrets_file = str(CLIENT_SECRETS_FILE)
        self.token_file = str(TOKEN_FILE)

    def is_configured(self) -> bool:
        """Check if OAuth client credentials exist."""
        return os.path.exists(self.client_secrets_file)

    def is_authenticated(self) -> bool:
        """Check if user has an authorized token saved."""
        if not os.path.exists(self.token_file):
            return False
        try:
            with open(self.token_file, "r") as f:
                data = json.load(f)
                return bool(data.get("token") or data.get("access_token") or data.get("refresh_token"))
        except Exception:
            return False

    def get_auth_status(self) -> Dict[str, Any]:
        """Returns YouTube connection status."""
        configured = self.is_configured()
        authenticated = self.is_authenticated()
        return {
            "configured": configured,
            "authenticated": authenticated,
            "mode": "live" if (configured and authenticated) else "simulation"
        }

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list] = None,
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """
        Uploads a video to YouTube Shorts using YouTube Data API v3.
        If credentials are not yet configured, runs in high-fidelity simulation mode
        for immediate local testing and dashboard operation.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file to upload does not exist: {video_path}")

        status = self.get_auth_status()

        if status["mode"] == "live":
            # Live YouTube Data API v3 upload
            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaFileUpload

                with open(self.token_file, "r") as f:
                    token_data = json.load(f)
                credentials = Credentials.from_authorized_user_info(token_data, SCOPES)
                youtube = build("youtube", "v3", credentials=credentials)

                body = {
                    "snippet": {
                        "title": title[:100],
                        "description": description,
                        "tags": tags or ["Shorts", "ViralCutAI"],
                        "categoryId": "22"  # People & Blogs / Entertainment
                    },
                    "status": {
                        "privacyStatus": privacy_status,
                        "selfDeclaredMadeForKids": False
                    }
                }

                media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
                request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                response = request.execute()

                video_id = response.get("id")
                return {
                    "success": True,
                    "mode": "live",
                    "youtube_video_id": video_id,
                    "youtube_url": f"https://www.youtube.com/shorts/{video_id}"
                }
            except Exception as e:
                logger.error(f"Live YouTube upload failed: {e}")
                raise RuntimeError(f"YouTube upload error: {str(e)}")

        else:
            # High-fidelity Simulation Mode (Dry-Run for Local Dev)
            logger.info("Executing YouTube upload in verified Simulation / Sandbox mode.")
            simulated_id = f"VC_{uuid.uuid4().hex[:10]}"
            return {
                "success": True,
                "mode": "simulation",
                "youtube_video_id": simulated_id,
                "youtube_url": f"https://www.youtube.com/shorts/{simulated_id}",
                "note": "Uploaded in local simulation mode. Add client_secrets.json to enable live channel sync."
            }

_uploader_instance = None

def get_youtube_uploader() -> YouTubeUploader:
    global _uploader_instance
    if _uploader_instance is None:
        _uploader_instance = YouTubeUploader()
    return _uploader_instance
