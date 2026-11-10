import React, { useState, useEffect } from 'react';
import {
  Flame,
  Upload,
  Video,
  Play,
  CheckCircle,
  Youtube,
  BarChart3,
  Clock,
  Sparkles,
  RefreshCw,
  Sliders,
  Download,
  Eye
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analytics, setAnalytics] = useState({
    total_videos: 0,
    total_shorts: 0,
    pending_uploads: 0,
    completed_uploads: 0,
    recent_videos: [],
    recent_clips: []
  });

  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [clips, setClips] = useState([]);
  const [selectedClip, setSelectedClip] = useState(null);
  const [uploads, setUploads] = useState([]);

  // Upload & Pipeline State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Editor State
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editLayout, setEditLayout] = useState('auto');
  const [renderingClipId, setRenderingClipId] = useState(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [privacyStatus, setPrivacyStatus] = useState('public');

  useEffect(() => {
    fetchAnalytics();
    fetchVideos();
    fetchYouTubeUploads();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/analytics`);
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  const fetchVideos = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/videos`);
      if (res.ok) {
        const data = await res.json();
        const vids = data.videos || [];
        setVideos(vids);
        if (vids.length > 0 && !selectedVideo) {
          setSelectedVideo(vids[0]);
          loadClipsForVideo(vids[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load videos:', err);
    }
  };

  const loadClipsForVideo = async (videoId, preserveClipId = null) => {
    try {
      const res = await fetch(`${API_BASE}/api/videos/${videoId}/clips`);
      if (res.ok) {
        const data = await res.json();
        const loadedClips = data.clips || [];
        setClips(loadedClips);

        if (preserveClipId) {
          const match = loadedClips.find(c => c.id === preserveClipId);
          if (match) selectClipForPreview(match);
        } else if (loadedClips.length > 0) {
          // If no clip is selected yet, or current clip belongs to a different video
          if (!selectedClip || selectedClip.video_id !== videoId) {
            selectClipForPreview(loadedClips[0]);
          }
        } else {
          setSelectedClip(null);
        }
      }
    } catch (err) {
      console.error('Failed to load clips:', err);
    }
  };

  const fetchYouTubeUploads = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/youtube/uploads`);
      if (res.ok) {
        const data = await res.json();
        setUploads(data.uploads || []);
      }
    } catch (err) {
      console.error('Failed to load YouTube uploads:', err);
    }
  };

  const selectClipForPreview = (clip) => {
    setSelectedClip(clip);
    setEditTitle(clip.title || '');
    setEditDescription(clip.description || '');
    setEditLayout(clip.layout_mode || 'auto');
  };

  // Video Upload Handler
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsProcessing(true);
    setUploadProgress(15);
    setProcessingStatus('Uploading video to backend...');

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const res = await fetch(`${API_BASE}/api/videos/upload`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      const videoId = data.video.id;

      setUploadProgress(35);
      setProcessingStatus('Extracting audio & transcribing with Faster-Whisper INT8...');

      const pollInterval = setInterval(async () => {
        try {
          const stRes = await fetch(`${API_BASE}/api/videos/${videoId}/status`);
          if (stRes.ok) {
            const stData = await stRes.json();
            if (stData.status === 'transcribing') {
              setProcessingStatus('Transcribing speech with word-level timestamps...');
              setUploadProgress(60);
            } else if (stData.status === 'detecting_clips') {
              setProcessingStatus('Analyzing 6 viral dimensions & segmenting distinct moments...');
              setUploadProgress(85);
            } else if (stData.status === 'completed') {
              clearInterval(pollInterval);
              setProcessingStatus('Completed! Distinct viral moments ready.');
              setUploadProgress(100);
              setIsProcessing(false);
              await fetchVideos();
              await fetchAnalytics();
              setSelectedVideo(stData);
              await loadClipsForVideo(videoId);
              setActiveTab('clips');
            } else if (stData.status === 'failed') {
              clearInterval(pollInterval);
              setIsProcessing(false);
              alert(`Processing failed: ${stData.error_message}`);
            }
          }
        } catch (err) {
          console.error('Poll error:', err);
        }
      }, 1500);

    } catch (err) {
      setIsProcessing(false);
      alert(err.message);
    }
  };

  // Render Short Handler
  const handleRenderShort = async (clipId, customLayout = null) => {
    setRenderingClipId(clipId);
    const layout = customLayout || editLayout;
    try {
      const res = await fetch(`${API_BASE}/api/clips/${clipId}/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layout_mode: layout, include_subtitles: true })
      });
      if (!res.ok) throw new Error('Render failed');
      const data = await res.json();
      
      // Update local clip state without jumping to clip 0!
      const updated = data.clip;
      selectClipForPreview(updated);
      setClips(prev => prev.map(c => c.id === clipId ? updated : c));
      fetchAnalytics();
      alert(`Short rendered successfully in 9:16 format with ${layout === 'smart_crop' ? 'face centering' : 'blurred background'} and burned-in subtitles!`);
    } catch (err) {
      alert(`Render error: ${err.message}`);
    } finally {
      setRenderingClipId(null);
    }
  };

  // Re-run Detection with Custom Durations
  const handleRedetectClips = async () => {
    if (!selectedVideo) return;
    try {
      const res = await fetch(`${API_BASE}/api/videos/${selectedVideo.id}/detect-clips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ min_duration: 35.0, max_duration: 75.0, max_clips: 10 })
      });
      if (res.ok) {
        await loadClipsForVideo(selectedVideo.id);
        alert('Re-analyzed video! Generated 10 distinct narrative story moments with visual chart/whiteboard awareness.');
      }
    } catch (err) {
      alert('Failed to re-detect clips: ' + err.message);
    }
  };

  // YouTube Upload Handler
  const handlePublishYouTube = async (clipId) => {
    setIsPublishing(true);
    try {
      const res = await fetch(`${API_BASE}/api/clips/${clipId}/upload-youtube`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          privacy_status: privacyStatus,
          custom_title: editTitle,
          custom_description: editDescription
        })
      });
      if (!res.ok) throw new Error('YouTube publish failed');
      const data = await res.json();
      alert(`Published! YouTube URL: ${data.upload.youtube_url}`);
      fetchYouTubeUploads();
      fetchAnalytics();
    } catch (err) {
      alert(`Publish error: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-badge">⚡</div>
          <div className="logo-text">
            <h1>ViralCut AI</h1>
            <span>Shorts & Reels Generator</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart3 size={18} />
            <span>Dashboard</span>
          </div>

          <div
            className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <Upload size={18} />
            <span>New Project</span>
          </div>

          <div
            className={`nav-item ${activeTab === 'clips' ? 'active' : ''}`}
            onClick={() => setActiveTab('clips')}
          >
            <Flame size={18} />
            <span>Viral Moments</span>
          </div>

          <div
            className={`nav-item ${activeTab === 'editor' ? 'active' : ''}`}
            onClick={() => setActiveTab('editor')}
          >
            <Sliders size={18} />
            <span>Shorts Editor</span>
          </div>

          <div
            className={`nav-item ${activeTab === 'youtube' ? 'active' : ''}`}
            onClick={() => setActiveTab('youtube')}
          >
            <Youtube size={18} />
            <span>Publish History</span>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="hardware-pill">
            <div className="hardware-title">HP ProDesk Optimized</div>
            <div className="hardware-spec">i3 8th Gen • CPU INT8 • 8GB RAM</div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="top-bar">
          <div className="page-title">
            {activeTab === 'dashboard' && 'System Overview'}
            {activeTab === 'upload' && 'Upload Video Project'}
            {activeTab === 'clips' && 'AI Viral Candidates'}
            {activeTab === 'editor' && 'Vertical Short Preview & Editor'}
            {activeTab === 'youtube' && 'YouTube Upload Manager'}
          </div>

          <div className="top-status-group">
            <span className="status-badge online">
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }}></span>
              FastAPI Online
            </span>
            <span className="status-badge youtube">
              <Youtube size={14} />
              YouTube Ready
            </span>
          </div>
        </header>

        <div className="content-body">
          {/* TAB 1: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' }}>
                    <Video size={24} />
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{analytics.total_videos}</div>
                    <div className="stat-label">Videos Processed</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' }}>
                    <Flame size={24} />
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{analytics.total_shorts}</div>
                    <div className="stat-label">Shorts Generated</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#eab308' }}>
                    <Clock size={24} />
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{analytics.pending_uploads}</div>
                    <div className="stat-label">Pending Approval</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
                    <CheckCircle size={24} />
                  </div>
                  <div className="stat-info">
                    <div className="stat-value">{analytics.completed_uploads}</div>
                    <div className="stat-label">YouTube Uploads</div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px' }}>
                <div className="editor-form">
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Uploaded Video Projects</h3>
                  {videos.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No videos uploaded yet. Click "New Project" to start.</p>
                  ) : (
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Duration</th>
                          <th>Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {videos.slice(0, 6).map((v) => (
                          <tr key={v.id}>
                            <td style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {v.filename}
                            </td>
                            <td>{v.duration ? `${(v.duration / 60).toFixed(1)}m` : '-'}</td>
                            <td>
                              <span style={{ color: v.status === 'completed' ? '#10b981' : '#eab308', fontWeight: 600 }}>
                                {v.status}
                              </span>
                            </td>
                            <td>
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => {
                                  setSelectedVideo(v);
                                  loadClipsForVideo(v.id);
                                  setActiveTab('clips');
                                }}
                              >
                                View Moments
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                <div className="editor-form">
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Quick Project Creation</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>
                    Upload any video. ViralCut AI transcribes with Faster-Whisper, detects distinct viral moments, centers the speaker, and exports ready-to-publish 9:16 Shorts.
                  </p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('upload')}>
                    <Upload size={16} />
                    Start New Video Project
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: NEW PROJECT UPLOAD */}
          {activeTab === 'upload' && (
            <div style={{ maxWidth: 700, margin: '0 auto' }}>
              <div className="editor-form">
                <h2 style={{ fontSize: 20, fontWeight: 700 }}>Upload Video Project</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                  Supports MP4, MOV, MKV, AVI. The video will be analyzed for distinct viral sections across the timeline.
                </p>

                <div
                  className="dropzone"
                  onClick={() => document.getElementById('file-input').click()}
                >
                  <input
                    id="file-input"
                    type="file"
                    accept="video/mp4,video/quicktime,video/x-matroska,video/x-msvideo"
                    style={{ display: 'none' }}
                    onChange={(e) => setUploadFile(e.target.files[0])}
                  />
                  <div className="dropzone-icon">
                    <Upload size={32} />
                  </div>
                  <h3>{uploadFile ? uploadFile.name : 'Select or drop video file here'}</h3>
                  <p>{uploadFile ? `${(uploadFile.size / (1024 * 1024)).toFixed(1)} MB` : 'Up to 1 GB • 720p/1080p supported'}</p>
                </div>

                {isProcessing && (
                  <div style={{ background: 'var(--bg-secondary)', padding: 16, borderRadius: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
                      <span>{processingStatus}</span>
                      <span style={{ fontWeight: 700 }}>{uploadProgress}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                    </div>
                  </div>
                )}

                <button
                  className="btn btn-primary"
                  onClick={handleUploadSubmit}
                  disabled={!uploadFile || isProcessing}
                  style={{ width: '100%', padding: '14px' }}
                >
                  <Sparkles size={18} />
                  {isProcessing ? 'Processing Pipeline...' : 'Start AI Analysis'}
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: VIRAL MOMENTS */}
          {activeTab === 'clips' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700 }}>
                    Distinct Viral Moments for: {selectedVideo ? selectedVideo.filename : 'No Video Selected'}
                  </h2>
                  <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                    Every moment is from a different, non-overlapping section of the video
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <select
                    className="form-control"
                    style={{ width: 260 }}
                    value={selectedVideo?.id || ''}
                    onChange={(e) => {
                      const v = videos.find(x => x.id === e.target.value);
                      setSelectedVideo(v);
                      loadClipsForVideo(v.id);
                    }}
                  >
                    {videos.map(v => (
                      <option key={v.id} value={v.id}>{v.filename}</option>
                    ))}
                  </select>

                  <button className="btn btn-secondary btn-sm" onClick={handleRedetectClips} title="Re-scan transcript for distinct moments">
                    <RefreshCw size={14} /> Re-detect Moments
                  </button>
                </div>
              </div>

              {clips.length === 0 ? (
                <div className="editor-form" style={{ textAlign: 'center', padding: 48 }}>
                  <Flame size={48} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                  <h3>No Viral Clips Found Yet</h3>
                  <p style={{ color: 'var(--text-secondary)' }}>Upload a video or click "Re-detect Moments" above.</p>
                </div>
              ) : (
                <div className="clips-grid">
                  {clips.map((clip, idx) => (
                    <div key={clip.id} className="clip-card">
                      <div>
                        <div className="clip-header">
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span className={`viral-badge ${clip.viral_score >= 70 ? 'high' : 'medium'}`}>
                              <Flame size={14} />
                              Score: {clip.viral_score}
                            </span>
                            {clip.has_visual && (
                              <span className="viral-badge" style={{ background: 'rgba(59, 130, 246, 0.18)', color: '#60a5fa', borderColor: 'rgba(59, 130, 246, 0.4)' }}>
                                🎨 Visual Demo
                              </span>
                            )}
                          </div>
                          <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600 }}>
                            ⏱️ {Math.floor(clip.start_time / 60)}m{Math.floor(clip.start_time % 60)}s → {Math.floor(clip.end_time / 60)}m{Math.floor(clip.end_time % 60)}s ({clip.duration.toFixed(1)}s)
                          </span>
                        </div>

                        <div className="clip-title" style={{ marginTop: 10 }}>{clip.title}</div>
                        <div className="clip-reason" style={{ marginTop: 4 }}>💡 {clip.reason}</div>

                        <div className="score-bars" style={{ marginTop: 12 }}>
                          <div className="score-item">
                            <div className="score-label-row">
                              <span>Hook</span>
                              <span>{clip.hook_score}</span>
                            </div>
                            <div className="score-track">
                              <div className="score-fill" style={{ width: `${clip.hook_score}%`, background: '#ef4444' }}></div>
                            </div>
                          </div>

                          <div className="score-item">
                            <div className="score-label-row">
                              <span>Emotion</span>
                              <span>{clip.emotional_score}</span>
                            </div>
                            <div className="score-track">
                              <div className="score-fill" style={{ width: `${clip.emotional_score}%`, background: '#f97316' }}></div>
                            </div>
                          </div>

                          <div className="score-item">
                            <div className="score-label-row">
                              <span>Story</span>
                              <span>{clip.storytelling_score}</span>
                            </div>
                            <div className="score-track">
                              <div className="score-fill" style={{ width: `${clip.storytelling_score}%`, background: '#8b5cf6' }}></div>
                            </div>
                          </div>

                          <div className="score-item">
                            <div className="score-label-row">
                              <span>Info</span>
                              <span>{clip.information_score}</span>
                            </div>
                            <div className="score-track">
                              <div className="score-fill" style={{ width: `${clip.information_score}%`, background: '#3b82f6' }}></div>
                            </div>
                          </div>
                        </div>

                        <div className="clip-text" style={{ marginTop: 12 }}>
                          "{clip.transcript_text}"
                        </div>
                      </div>

                      <div className="clip-actions" style={{ flexDirection: 'column', gap: 8 }}>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <button
                            className="btn btn-primary btn-sm"
                            style={{ flex: 1 }}
                            onClick={() => handleRenderShort(clip.id)}
                            disabled={renderingClipId === clip.id}
                          >
                            <Sparkles size={14} />
                            {renderingClipId === clip.id ? 'Rendering 9:16...' : (clip.output_path ? 'Re-Render Short' : 'Render 9:16 Short')}
                          </button>

                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              selectClipForPreview(clip);
                              setActiveTab('editor');
                            }}
                          >
                            <Eye size={14} />
                            Preview
                          </button>
                        </div>
                        {clip.output_path && (
                          <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600, textAlign: 'center' }}>
                            ✓ 9:16 Short Rendered & Ready
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: SHORTS EDITOR & PREVIEW */}
          {activeTab === 'editor' && (
            <div>
              {!selectedClip ? (
                <div className="editor-form" style={{ textAlign: 'center', padding: 48 }}>
                  <p>Select a clip from the Viral Moments tab to edit and preview.</p>
                </div>
              ) : (
                <div>
                  {/* Clip Switcher Bar */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-secondary)', padding: '12px 18px', borderRadius: 12, marginBottom: 24, border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' }}>Current Clip:</span>
                      <select
                        className="form-control"
                        style={{ width: 340 }}
                        value={selectedClip.id}
                        onChange={(e) => {
                          const c = clips.find(x => x.id === e.target.value);
                          if (c) selectClipForPreview(c);
                        }}
                      >
                        {clips.map((c, i) => (
                          <option key={c.id} value={c.id}>
                            Moment #{i + 1} ({Math.floor(c.start_time / 60)}m{Math.floor(c.start_time % 60)}s → {Math.floor(c.end_time / 60)}m{Math.floor(c.end_time % 60)}s): {c.title.slice(0, 32)}...
                          </option>
                        ))}
                      </select>
                    </div>

                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      Clip Duration: <strong style={{ color: '#fff' }}>{selectedClip.duration.toFixed(1)}s</strong> (from {selectedClip.start_time.toFixed(1)}s to {selectedClip.end_time.toFixed(1)}s)
                    </div>
                  </div>

                  <div className="shorts-editor-view">
                    {/* Left: 9:16 Video Mockup */}
                    <div>
                      <div className="shorts-phone-mockup">
                        {selectedClip.output_path ? (
                          <video
                            key={`${selectedClip.id}_${selectedClip.rendered_at || ''}`}
                            className="shorts-video-player"
                            controls
                            autoPlay
                            loop
                            src={`${API_BASE}/api/clips/${selectedClip.id}/video?t=${new Date(selectedClip.rendered_at || Date.now()).getTime()}`}
                          />
                        ) : (
                          <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                            <Play size={40} style={{ margin: '0 auto 12px' }} />
                            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>This clip has not been rendered yet.</p>
                            <p style={{ fontSize: 12, marginTop: 8 }}>Click <strong>"Render 9:16 Short"</strong> on the right to center the speaker and add animated subtitles.</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right: Metadata & Rendering Controls */}
                    <div className="editor-form">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h2 style={{ fontSize: 18, fontWeight: 700 }}>9:16 Short Configuration</h2>
                        <span className="viral-badge high">Viral Score: {selectedClip.viral_score}</span>
                      </div>

                      <div className="form-group">
                        <label>YouTube Short Title (under 60 chars for mobile visibility)</label>
                        <input
                          type="text"
                          className="form-control"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                        />
                      </div>

                      <div className="form-group">
                        <label>Description & Hashtags</label>
                        <textarea
                          className="form-control"
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                        />
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div className="form-group">
                          <label>Vertical 9:16 Framing Layout</label>
                          <select
                            className="form-control"
                            value={editLayout}
                            onChange={(e) => setEditLayout(e.target.value)}
                          >
                            <option value="auto">⚡ Auto-Detect (Best for Whiteboards & Charts)</option>
                            <option value="blur_background">🌟 Blurred Background (Fit & Center 9:16)</option>
                            <option value="smart_crop">🎯 Smart Crop (Speaker Centered 9:16)</option>
                          </select>
                        </div>

                        <div className="form-group">
                          <label>YouTube Privacy</label>
                          <select
                            className="form-control"
                            value={privacyStatus}
                            onChange={(e) => setPrivacyStatus(e.target.value)}
                          >
                            <option value="public">Public</option>
                            <option value="unlisted">Unlisted</option>
                            <option value="private">Private</option>
                          </select>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                        <button
                          className="btn btn-primary"
                          onClick={() => handleRenderShort(selectedClip.id)}
                          disabled={renderingClipId === selectedClip.id}
                        >
                          <Sparkles size={16} />
                          {renderingClipId === selectedClip.id ? 'Rendering 9:16 Short...' : 'Render 9:16 Short'}
                        </button>

                        {selectedClip.output_path && (
                          <a
                            className="btn btn-secondary"
                            href={`${API_BASE}/api/clips/${selectedClip.id}/video`}
                            download={`Short_${selectedClip.id}.mp4`}
                          >
                            <Download size={16} />
                            Download MP4
                          </a>
                        )}

                        <button
                          className="btn btn-success"
                          onClick={() => handlePublishYouTube(selectedClip.id)}
                          disabled={isPublishing || !selectedClip.output_path}
                        >
                          <Youtube size={16} />
                          {isPublishing ? 'Uploading...' : 'Publish to YouTube'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: YOUTUBE PUBLISHER & HISTORY */}
          {activeTab === 'youtube' && (
            <div className="editor-form">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700 }}>YouTube Shorts Publishing Log</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                    Audit trail of all published Shorts and external YouTube IDs
                  </p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={fetchYouTubeUploads}>
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>

              {uploads.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No Shorts uploaded to YouTube yet.</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Privacy</th>
                      <th>Status</th>
                      <th>YouTube Link</th>
                      <th>Published At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploads.map((u) => (
                      <tr key={u.id}>
                        <td style={{ fontWeight: 600 }}>{u.title}</td>
                        <td>{u.privacy_status}</td>
                        <td>
                          <span style={{ color: u.upload_status === 'published' ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                            {u.upload_status}
                          </span>
                        </td>
                        <td>
                          {u.youtube_url ? (
                            <a href={u.youtube_url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6' }}>
                              {u.youtube_video_id} ↗
                            </a>
                          ) : '-'}
                        </td>
                        <td style={{ color: 'var(--text-muted)' }}>{u.uploaded_at || u.created_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
