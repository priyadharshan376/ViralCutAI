import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from backend.config import DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    """Create a database connection with dict-like row access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                duration REAL DEFAULT 0.0,
                width INTEGER DEFAULT 0,
                height INTEGER DEFAULT 0,
                fps REAL DEFAULT 0.0,
                video_codec TEXT DEFAULT '',
                audio_codec TEXT DEFAULT '',
                status TEXT DEFAULT 'uploaded',
                error_message TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transcripts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                full_text TEXT NOT NULL,
                language TEXT DEFAULT '',
                language_probability REAL DEFAULT 0.0,
                duration REAL DEFAULT 0.0,
                segments_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
        """)
        
        # Clips table (Phase 2 & 3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration REAL NOT NULL,
                transcript_text TEXT NOT NULL,
                hook_score REAL DEFAULT 0.0,
                emotional_score REAL DEFAULT 0.0,
                information_score REAL DEFAULT 0.0,
                storytelling_score REAL DEFAULT 0.0,
                context_score REAL DEFAULT 0.0,
                engagement_score REAL DEFAULT 0.0,
                viral_score REAL DEFAULT 0.0,
                reason TEXT DEFAULT '',
                title TEXT DEFAULT '',
                status TEXT DEFAULT 'detected',
                output_path TEXT DEFAULT '',
                description TEXT DEFAULT '',
                hashtags TEXT DEFAULT '',
                rendered_at TIMESTAMP,
                has_visual INTEGER DEFAULT 0,
                layout_mode TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
        """)
        
        # Safe migration for existing DB
        cursor.execute("PRAGMA table_info(clips)")
        columns = [row[1] for row in cursor.fetchall()]
        if "output_path" not in columns:
            cursor.execute("ALTER TABLE clips ADD COLUMN output_path TEXT DEFAULT ''")
        if "description" not in columns:
            cursor.execute("ALTER TABLE clips ADD COLUMN description TEXT DEFAULT ''")
        if "hashtags" not in columns:
            cursor.execute("ALTER TABLE clips ADD COLUMN hashtags TEXT DEFAULT ''")
        if "rendered_at" not in columns:
            cursor.execute("ALTER TABLE clips ADD COLUMN rendered_at TIMESTAMP")
        if "has_visual" not in columns:
            cursor.execute("ALTER TABLE clips ADD COLUMN has_visual INTEGER DEFAULT 0")
        if "layout_mode" not in columns:
            cursor.execute("ALTER TABLE clips ADD COLUMN layout_mode TEXT DEFAULT 'auto'")
        
        # YouTube Uploads table (Phase 4)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_uploads (
                id TEXT PRIMARY KEY,
                clip_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                youtube_video_id TEXT DEFAULT '',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                privacy_status TEXT DEFAULT 'public',
                upload_status TEXT DEFAULT 'pending',
                youtube_url TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                scheduled_publish_at TEXT DEFAULT '',
                uploaded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clip_id) REFERENCES clips (id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
        """)

        cursor.execute("PRAGMA table_info(youtube_uploads)")
        yt_columns = [row[1] for row in cursor.fetchall()]
        if "scheduled_publish_at" not in yt_columns:
            cursor.execute("ALTER TABLE youtube_uploads ADD COLUMN scheduled_publish_at TEXT DEFAULT ''")
        
        conn.commit()

# Database Helper Functions

def create_video_record(video_id: str, filename: str, filepath: str, file_size: int) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO videos (id, filename, filepath, file_size, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'uploaded', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (video_id, filename, filepath, file_size))
        conn.commit()
    return get_video(video_id)

def update_video_metadata(video_id: str, metadata: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE videos
            SET duration = ?,
                width = ?,
                height = ?,
                fps = ?,
                video_codec = ?,
                audio_codec = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            metadata.get("duration", 0.0),
            metadata.get("width", 0),
            metadata.get("height", 0),
            metadata.get("fps", 0.0),
            metadata.get("video_codec", ""),
            metadata.get("audio_codec", ""),
            video_id
        ))
        conn.commit()

def update_video_status(video_id: str, status: str, error_message: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE videos
            SET status = ?,
                error_message = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, error_message, video_id))
        conn.commit()

def get_video(video_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def list_videos() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_video(video_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transcripts WHERE video_id = ?", (video_id,))
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()

def save_transcript(
    video_id: str,
    full_text: str,
    language: str,
    language_probability: float,
    duration: float,
    segments: List[Dict[str, Any]]
) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transcripts (video_id, full_text, language, language_probability, duration, segments_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            video_id,
            full_text,
            language,
            language_probability,
            duration,
            json.dumps(segments, ensure_ascii=False)
        ))
        conn.commit()
        return cursor.lastrowid

def get_transcript(video_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcripts WHERE video_id = ? ORDER BY id DESC LIMIT 1", (video_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        data["segments"] = json.loads(data["segments_json"])
        return data

# Clips Helper Functions (Phase 2)

def save_clip(clip_data: Dict[str, Any]) -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO clips (
                id, video_id, start_time, end_time, duration, transcript_text,
                hook_score, emotional_score, information_score, storytelling_score,
                context_score, engagement_score, viral_score, reason, title, status,
                has_visual, layout_mode, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            clip_data["id"],
            clip_data["video_id"],
            clip_data["start_time"],
            clip_data["end_time"],
            clip_data["duration"],
            clip_data["transcript_text"],
            clip_data.get("hook_score", 0.0),
            clip_data.get("emotional_score", 0.0),
            clip_data.get("information_score", 0.0),
            clip_data.get("storytelling_score", 0.0),
            clip_data.get("context_score", 0.0),
            clip_data.get("engagement_score", 0.0),
            clip_data.get("viral_score", 0.0),
            clip_data.get("reason", ""),
            clip_data.get("title", ""),
            clip_data.get("status", "detected"),
            1 if clip_data.get("has_visual") else 0,
            clip_data.get("layout_mode", "auto")
        ))
        conn.commit()
    return clip_data["id"]

def get_clips_by_video_id(video_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clips WHERE video_id = ? ORDER BY viral_score DESC",
            (video_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_clip(clip_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_clip_status(clip_id: str, status: str, title: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if title is not None:
            cursor.execute(
                "UPDATE clips SET status = ?, title = ? WHERE id = ?",
                (status, title, clip_id)
            )
        else:
            cursor.execute(
                "UPDATE clips SET status = ? WHERE id = ?",
                (status, clip_id)
            )
        conn.commit()

def update_clip_render_result(
    clip_id: str,
    output_path: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    hashtags: Optional[str] = None
):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clips
            SET output_path = ?,
                title = COALESCE(?, title),
                description = COALESCE(?, description),
                hashtags = COALESCE(?, hashtags),
                status = 'rendered',
                rendered_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (output_path, title, description, hashtags, clip_id))
        conn.commit()

def delete_clips_for_video(video_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clips WHERE video_id = ?", (video_id,))
        conn.commit()

# YouTube Uploads & Analytics Helper Functions (Phase 4)

def record_youtube_upload(
    upload_id: str,
    clip_id: str,
    video_id: str,
    title: str,
    description: str,
    privacy_status: str = "public",
    scheduled_publish_at: str = ""
) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO youtube_uploads (
                id, clip_id, video_id, title, description, privacy_status, upload_status, scheduled_publish_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
        """, (upload_id, clip_id, video_id, title, description, privacy_status, scheduled_publish_at))
        conn.commit()
    return get_youtube_upload(upload_id)

def update_youtube_upload_status(
    upload_id: str,
    status: str,
    youtube_video_id: str = "",
    youtube_url: str = "",
    error_message: str = ""
):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE youtube_uploads
            SET upload_status = ?,
                youtube_video_id = ?,
                youtube_url = ?,
                error_message = ?,
                uploaded_at = CASE WHEN ? = 'published' THEN CURRENT_TIMESTAMP ELSE uploaded_at END
            WHERE id = ?
        """, (status, youtube_video_id, youtube_url, error_message, status, upload_id))
        conn.commit()

def get_youtube_upload(upload_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM youtube_uploads WHERE id = ?", (upload_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def list_youtube_uploads() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM youtube_uploads ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_dashboard_analytics() -> Dict[str, Any]:
    """Computes summary metrics, scheduled queue, and top viral highlights for Dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM videos")
        total_videos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM clips WHERE status = 'rendered'")
        total_shorts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM clips WHERE status = 'approved'")
        pending_uploads = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM youtube_uploads WHERE upload_status = 'published'")
        completed_uploads = cursor.fetchone()[0]

        # Recent activities
        cursor.execute("""
            SELECT id, filename, status, created_at FROM videos ORDER BY created_at DESC LIMIT 5
        """)
        recent_videos = [dict(row) for row in cursor.fetchall()]

        # Top viral moments (ranked by viral score)
        cursor.execute("""
            SELECT c.id, c.video_id, c.title, c.viral_score, c.hook_score, c.storytelling_score,
                   c.duration, c.has_visual, c.layout_mode, c.status, c.output_path, c.reason, c.created_at
            FROM clips c
            ORDER BY c.viral_score DESC LIMIT 6
        """)
        top_clips = [dict(row) for row in cursor.fetchall()]

        # Scheduled release queue
        cursor.execute("""
            SELECT id, title, youtube_video_id, youtube_url, privacy_status, scheduled_publish_at, created_at
            FROM youtube_uploads
            WHERE scheduled_publish_at != '' AND scheduled_publish_at IS NOT NULL
            ORDER BY scheduled_publish_at DESC LIMIT 6
        """)
        upcoming_scheduled = [dict(row) for row in cursor.fetchall()]

        return {
            "total_videos": total_videos,
            "total_shorts": total_shorts,
            "pending_uploads": pending_uploads,
            "completed_uploads": completed_uploads,
            "recent_videos": recent_videos,
            "recent_clips": top_clips,
            "top_clips": top_clips,
            "upcoming_scheduled": upcoming_scheduled,
            "channel_info": {
                "name": "PDX",
                "status": "connected",
                "mode": "live",
                "target_url": "https://studio.youtube.com"
            }
        }


