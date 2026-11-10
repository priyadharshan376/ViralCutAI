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
  Eye,
  Calendar,
  CheckSquare,
  Square,
  Send,
  X,
  ListPlus,
  ArrowRight
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

  // Batch Selection & Scheduling State
  const [selectedClipIds, setSelectedClipIds] = useState([]);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleInterval, setScheduleInterval] = useState(30);
  const [scheduleStartNow, setScheduleStartNow] = useState(true);
  const [customStartTime, setCustomStartTime] = useState('');
  const [isBatchPublishing, setIsBatchPublishing] = useState(false);
  const [batchProgressText, setBatchProgressText] = useState('');
  const [batchResults, setBatchResults] = useState(null);

  // Upload & Pipeline State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Editor State
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editLayout, setEditLayout] = useState('auto');
  const [singleScheduleTime, setSingleScheduleTime] = useState('');
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
        setSelectedClipIds([]); // Reset selection when switching video

        if (preserveClipId) {
          const match = loadedClips.find(c => c.id === preserveClipId);
          if (match) selectClipForPreview(match);
        } else if (loadedClips.length > 0) {
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

  // Checkbox selection helpers
  const toggleClipSelection = (clipId) => {
    setSelectedClipIds(prev =>
      prev.includes(clipId) ? prev.filter(id => id !== clipId) : [...prev, clipId]
    );
  };

  const selectAllClips = () => {
    setSelectedClipIds(clips.map(c => c.id));
  };

  const deselectAllClips = () => {
    setSelectedClipIds([]);
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
      
      const updated = data.clip;
      selectClipForPreview(updated);
      setClips(prev => prev.map(c => c.id === clipId ? updated : c));
      fetchAnalytics();
      alert(`Short rendered successfully in 9:16 format with burned-in subtitles!`);
    } catch (err) {
      alert(`Render error: ${err.message}`);
    } finally {
      setRenderingClipId(null);
    }
  };

  // Re-run Detection
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
        alert('Re-analyzed video! Generated distinct narrative story moments with visual chart/whiteboard awareness.');
      }
    } catch (err) {
      alert('Failed to re-detect clips: ' + err.message);
    }
  };

  // Single YouTube Upload Handler
  const handlePublishYouTube = async (clipId, scheduledAt = null) => {
    setIsPublishing(true);
    try {
      const payload = {
        privacy_status: scheduledAt ? 'private' : privacyStatus,
        custom_title: editTitle,
        custom_description: editDescription,
        publish_at: scheduledAt || (singleScheduleTime ? new Date(singleScheduleTime).toISOString() : null)
      };

      const res = await fetch(`${API_BASE}/api/clips/${clipId}/upload-youtube`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'YouTube publish failed');
      }
      const data = await res.json();
      alert(`Published! YouTube URL: ${data.upload.youtube_url}${payload.publish_at ? ` (Scheduled for ${payload.publish_at})` : ''}`);
      fetchYouTubeUploads();
      fetchAnalytics();
    } catch (err) {
      alert(`Publish error: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  // Batch Upload & Schedule Handler
  const handleBatchScheduleSubmit = async (customClipIds = null) => {
    const idsToUpload = customClipIds || (selectedClipIds.length > 0 ? selectedClipIds : clips.map(c => c.id));
    if (idsToUpload.length === 0) {
      alert('No clips selected to upload.');
      return;
    }

    setIsBatchPublishing(true);
    setBatchProgressText(`Uploading & scheduling ${idsToUpload.length} videos at ${scheduleInterval}-minute intervals...`);
    setBatchResults(null);

    try {
      const res = await fetch(`${API_BASE}/api/youtube/batch-upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clip_ids: idsToUpload,
          interval_minutes: parseInt(scheduleInterval) || 30,
          start_now: scheduleStartNow,
          privacy_status: privacyStatus,
          custom_start_time: customStartTime ? new Date(customStartTime).toISOString() : null
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Batch schedule upload failed');
      }

      const data = await res.json();
      setBatchResults(data);
      fetchYouTubeUploads();
      fetchAnalytics();
      setBatchProgressText(`Successfully processed ${data.scheduled_count} videos!`);
    } catch (err) {
      alert(`Batch upload error: ${err.message}`);
    } finally {
      setIsBatchPublishing(false);
    }
  };

  // Helper to preview schedule timeline dates
  const getTimelinePreview = () => {
    const idsToUpload = selectedClipIds.length > 0 ? selectedClipIds : clips.map(c => c.id);
    const base = customStartTime ? new Date(customStartTime) : new Date();
    const interval = parseInt(scheduleInterval) || 30;

    return idsToUpload.slice(0, 8).map((clipId, idx) => {
      const clipObj = clips.find(c => c.id === clipId);
      const offsetMinutes = scheduleStartNow ? (idx * interval) : ((idx + 1) * interval);
      const scheduleTime = new Date(base.getTime() + offsetMinutes * 60000);
      return {
        clipId,
        title: clipObj ? clipObj.title : `Clip #${idx + 1}`,
        isImmediate: scheduleStartNow && idx === 0,
        timeStr: scheduleTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        dateStr: scheduleTime.toLocaleDateString([], { month: 'short', day: 'numeric' })
      };
    });
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-badge">PDX</div>
          <div className="logo-text">
            <h1>ViralCut AI</h1>
            <span>PDX Shorts Studio</span>
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
            <span>Viral Moments ({clips.length})</span>
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
            <span>Publish History ({uploads.length})</span>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="hardware-pill">
            <div className="hardware-title">Channel: PDX</div>
            <div className="hardware-spec">YouTube Connected • Live Upload</div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="content-container">

          {/* TAB 1: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div>
              <div style={{ marginBottom: 28, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h1 style={{ fontSize: 24, fontWeight: 800 }}>PDX Studio Overview</h1>
                  <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
                    Automated story detection, vertical framing, and interval scheduling for YouTube Shorts.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button className="btn btn-primary" onClick={() => setActiveTab('upload')}>
                    <Upload size={16} /> New Video
                  </button>
                  {clips.length > 0 && (
                    <button className="btn btn-success" onClick={() => { selectAllClips(); setShowScheduleModal(true); }}>
                      <Calendar size={16} /> Schedule All ({clips.length})
                    </button>
                  )}
                </div>
              </div>

              {/* Analytics Metric Cards */}
              <div className="metric-cards">
                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">Master Videos</span>
                    <Video size={18} color="var(--accent-red)" />
                  </div>
                  <div className="metric-value">{analytics.total_videos}</div>
                  <div className="metric-footer">Uploaded & Analyzed</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">Story Moments</span>
                    <Flame size={18} color="var(--accent-orange)" />
                  </div>
                  <div className="metric-value">{clips.length}</div>
                  <div className="metric-footer">Active Project Moments</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">Rendered 9:16</span>
                    <Sparkles size={18} color="var(--accent-purple)" />
                  </div>
                  <div className="metric-value">{analytics.total_shorts}</div>
                  <div className="metric-footer">Formatted for YouTube</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">YouTube Uploads</span>
                    <Youtube size={18} color="var(--accent-green)" />
                  </div>
                  <div className="metric-value">{analytics.completed_uploads}</div>
                  <div className="metric-footer">Published to PDX</div>
                </div>
              </div>

              {/* Quick Actions Bar */}
              <div style={{ marginTop: 28, background: 'var(--bg-card)', padding: 20, borderRadius: 12, border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>⚡ 5-Minute Fast Workflow</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
                    Drop a video $\rightarrow$ ViralCut AI detects complete stories with visual charts $\rightarrow$ Batch schedule 1 Short every 20 or 30 minutes!
                  </p>
                </div>
                <button className="btn btn-primary" onClick={() => setActiveTab('clips')}>
                  Go to Viral Moments <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: NEW PROJECT UPLOAD */}
          {activeTab === 'upload' && (
            <div style={{ maxWidth: 700, margin: '0 auto' }}>
              <div className="editor-form">
                <h2 style={{ fontSize: 20, fontWeight: 700 }}>Upload Video Project</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                  Supports MP4, MOV, MKV, AVI. The video will be transcribed and analyzed for complete narrative story arcs and whiteboard demonstrations.
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

          {/* TAB 3: VIRAL MOMENTS & BATCH SCHEDULING */}
          {activeTab === 'clips' && (
            <div>
              {/* Header with Project Selector */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700 }}>
                    Distinct Viral Moments for: {selectedVideo ? selectedVideo.filename : 'No Video Selected'}
                  </h2>
                  <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                    Every moment is a complete story arc with visual chart / whiteboard awareness
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <select
                    className="form-control"
                    style={{ width: 240 }}
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

                  <button className="btn btn-secondary btn-sm" onClick={handleRedetectClips} title="Re-scan transcript">
                    <RefreshCw size={14} /> Re-detect
                  </button>
                </div>
              </div>

              {/* BATCH ACTION TOOLBAR */}
              {clips.length > 0 && (
                <div className="batch-toolbar">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={selectedClipIds.length === clips.length ? deselectAllClips : selectAllClips}
                      style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      {selectedClipIds.length === clips.length ? (
                        <>
                          <CheckSquare size={16} color="#3b82f6" /> Deselect All
                        </>
                      ) : (
                        <>
                          <Square size={16} /> Select All ({clips.length})
                        </>
                      )}
                    </button>

                    <span style={{ fontSize: 13, fontWeight: 700, color: '#f0f3fa' }}>
                      {selectedClipIds.length > 0
                        ? `${selectedClipIds.length} of ${clips.length} moments selected`
                        : `Select moments to upload or schedule`}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: 10 }}>
                    {/* Schedule Batch Release Button */}
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => setShowScheduleModal(true)}
                      style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', border: 'none' }}
                    >
                      <Calendar size={15} />
                      {selectedClipIds.length > 0
                        ? `Schedule Selected (${selectedClipIds.length})`
                        : `Schedule All (${clips.length})`}
                    </button>

                    {/* Fast Upload Selected Button */}
                    <button
                      className="btn btn-success btn-sm"
                      onClick={() => handleBatchScheduleSubmit()}
                      disabled={isBatchPublishing}
                    >
                      <Youtube size={15} />
                      {isBatchPublishing
                        ? 'Publishing...'
                        : (selectedClipIds.length > 0
                            ? `Upload Selected (${selectedClipIds.length})`
                            : `Upload All (${clips.length})`)}
                    </button>
                  </div>
                </div>
              )}

              {/* Clips Grid */}
              {clips.length === 0 ? (
                <div className="editor-form" style={{ textAlign: 'center', padding: 48 }}>
                  <Flame size={48} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                  <h3>No Viral Clips Found Yet</h3>
                  <p style={{ color: 'var(--text-secondary)' }}>Upload a video or click "Re-detect Moments" above.</p>
                </div>
              ) : (
                <div className="clips-grid">
                  {clips.map((clip, idx) => {
                    const isSelected = selectedClipIds.includes(clip.id);
                    return (
                      <div
                        key={clip.id}
                        className="clip-card"
                        style={{
                          border: isSelected ? '1px solid #3b82f6' : '1px solid var(--border-color)',
                          boxShadow: isSelected ? '0 0 16px rgba(59, 130, 246, 0.25)' : 'none'
                        }}
                      >
                        <div>
                          <div className="clip-header">
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              {/* Selection Checkbox */}
                              <input
                                type="checkbox"
                                className="batch-checkbox"
                                checked={isSelected}
                                onChange={() => toggleClipSelection(clip.id)}
                                title="Select this clip for batch upload"
                              />

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
                                <span>Story</span>
                                <span>{clip.storytelling_score}</span>
                              </div>
                              <div className="score-track">
                                <div className="score-fill" style={{ width: `${clip.storytelling_score}%`, background: '#8b5cf6' }}></div>
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
                              {renderingClipId === clip.id ? 'Rendering 9:16...' : (clip.output_path ? 'Re-Render' : 'Render 9:16')}
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

                            {/* Direct Upload Button for this clip */}
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handlePublishYouTube(clip.id)}
                              disabled={isPublishing || !clip.output_path}
                              title="Upload directly to PDX channel"
                            >
                              <Youtube size={14} />
                              Upload
                            </button>
                          </div>

                          {clip.output_path && (
                            <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600, textAlign: 'center' }}>
                              ✓ 9:16 Rendered & Ready to Publish
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
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
                        <label>YouTube Short Title (under 60 chars with #Shorts for mobile discovery)</label>
                        <input
                          type="text"
                          className="form-control"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                        />
                      </div>

                      <div className="form-group">
                        <label>PDX High-Engagement Description & Hashtags</label>
                        <textarea
                          className="form-control"
                          style={{ minHeight: 140 }}
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                        />
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div className="form-group">
                          <label>Vertical 9:16 Layout</label>
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
                            <option value="unlisted">Unlisted (Verify First)</option>
                            <option value="private">Private</option>
                          </select>
                        </div>
                      </div>

                      {/* Optional Custom Schedule Time for Single Clip */}
                      <div className="form-group">
                        <label>📅 Schedule Release Time (Optional — leave empty for immediate publish)</label>
                        <input
                          type="datetime-local"
                          className="form-control"
                          value={singleScheduleTime}
                          onChange={(e) => setSingleScheduleTime(e.target.value)}
                        />
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
                          onClick={() => handlePublishYouTube(selectedClip.id, singleScheduleTime ? new Date(singleScheduleTime).toISOString() : null)}
                          disabled={isPublishing || !selectedClip.output_path}
                        >
                          <Youtube size={16} />
                          {isPublishing ? 'Uploading to PDX...' : (singleScheduleTime ? 'Schedule to YouTube' : 'Publish to YouTube')}
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
                    Audit trail of all published and scheduled Shorts on channel: <strong>PDX</strong>
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
                      <th>Scheduled Release</th>
                      <th>YouTube Link</th>
                      <th>Uploaded At</th>
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
                        <td style={{ color: u.scheduled_publish_at ? '#60a5fa' : 'var(--text-muted)' }}>
                          {u.scheduled_publish_at ? `📅 ${new Date(u.scheduled_publish_at).toLocaleString()}` : 'Immediate'}
                        </td>
                        <td>
                          {u.youtube_url ? (
                            <a href={u.youtube_url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6', fontWeight: 600 }}>
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

      {/* SCHEDULE & BATCH UPLOAD MODAL */}
      {showScheduleModal && (
        <div className="modal-overlay" onClick={() => !isBatchPublishing && setShowScheduleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 800 }}>📅 Automated YouTube Batch Scheduler</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 2 }}>
                  Publish {selectedClipIds.length > 0 ? selectedClipIds.length : clips.length} Shorts to <strong>PDX</strong> on an automatic schedule.
                </p>
              </div>
              <button
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                onClick={() => setShowScheduleModal(false)}
                disabled={isBatchPublishing}
              >
                <X size={20} />
              </button>
            </div>

            {/* Interval Configuration */}
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label>Publishing Interval (Minutes between each Short)</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
                {[15, 20, 30, 45, 60, 120].map((mins) => (
                  <button
                    key={mins}
                    type="button"
                    className={`btn-chip ${scheduleInterval === mins ? 'selected' : ''}`}
                    onClick={() => setScheduleInterval(mins)}
                  >
                    {mins === 30 ? '30 min (Recommended)' : `${mins} min`}
                  </button>
                ))}
              </div>
            </div>

            {/* Timing Options */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
              <div className="form-group">
                <label>Release Sequence</label>
                <select
                  className="form-control"
                  value={scheduleStartNow ? 'now' : 'later'}
                  onChange={(e) => setScheduleStartNow(e.target.value === 'now')}
                >
                  <option value="now">⚡ First Short Immediate, then every {scheduleInterval}m</option>
                  <option value="later">⏳ All Shorts Scheduled at intervals</option>
                </select>
              </div>

              <div className="form-group">
                <label>Privacy on Release</label>
                <select
                  className="form-control"
                  value={privacyStatus}
                  onChange={(e) => setPrivacyStatus(e.target.value)}
                >
                  <option value="public">Public (Automatic YouTube Schedule)</option>
                  <option value="unlisted">Unlisted (Review in Studio)</option>
                </select>
              </div>
            </div>

            {/* Custom Start Time (Optional) */}
            <div className="form-group" style={{ marginBottom: 18 }}>
              <label>Optional: Start Schedule at Specific Time (Leave empty for right now)</label>
              <input
                type="datetime-local"
                className="form-control"
                value={customStartTime}
                onChange={(e) => setCustomStartTime(e.target.value)}
              />
            </div>

            {/* Live Scheduled Timeline Preview */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
                🗓️ Calculated Schedule Timeline Preview:
              </label>
              <div className="schedule-timeline">
                {getTimelinePreview().map((item, idx) => (
                  <div key={idx} className={`timeline-item ${item.isImmediate ? 'active' : ''}`}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, maxWidth: '70%' }}>
                      <span style={{ fontWeight: 700, color: item.isImmediate ? '#10b981' : '#60a5fa' }}>
                        #{idx + 1}
                      </span>
                      <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {item.title}
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, color: item.isImmediate ? '#10b981' : '#fff' }}>
                      {item.isImmediate ? '🚀 Live Immediately' : `⏰ ${item.timeStr} (${item.dateStr})`}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Status / Results Section */}
            {batchProgressText && (
              <div style={{ background: 'var(--bg-secondary)', padding: 12, borderRadius: 8, marginBottom: 16, border: '1px solid var(--border-color)', fontSize: 13, color: '#60a5fa' }}>
                {batchProgressText}
              </div>
            )}

            {batchResults && (
              <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', padding: 14, borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
                <div style={{ fontWeight: 700, color: '#10b981', marginBottom: 6 }}>
                  🎉 {batchResults.scheduled_count} Shorts Successfully Scheduled to PDX!
                </div>
                <div style={{ maxHeight: 120, overflowY: 'auto' }}>
                  {batchResults.results.map((r, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                      <span>{r.title.slice(0, 36)}...</span>
                      <a href={r.youtube_url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6', fontWeight: 600 }}>
                        {r.scheduled_publish_at ? `Scheduled (${new Date(r.scheduled_publish_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})` : 'Live ↗'}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button
                className="btn btn-secondary"
                onClick={() => setShowScheduleModal(false)}
                disabled={isBatchPublishing}
              >
                Close
              </button>
              <button
                className="btn btn-primary"
                onClick={() => handleBatchScheduleSubmit()}
                disabled={isBatchPublishing}
                style={{ background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none' }}
              >
                <Calendar size={16} />
                {isBatchPublishing ? 'Uploading & Scheduling...' : `Schedule to PDX Channel (every ${scheduleInterval}m)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
