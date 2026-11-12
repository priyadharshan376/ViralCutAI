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
  ArrowRight,
  ExternalLink,
  Zap,
  TrendingUp,
  Layers,
  Link2,
  Search,
  Type,
  Film
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

const DEFAULT_SUBTITLE_STYLES = [
  { id: 'hormozi', name: 'Hormozi Bold', description: 'Chunky Impact uppercase + yellow pop', preview_bg: '#111827', preview_text: '#FFFFFF', preview_accent: '#FFEA00', uppercase: true },
  { id: 'mrbeast', name: 'MrBeast Pop', description: 'Giant Impact + neon green highlight', preview_bg: '#0f172a', preview_text: '#FFFFFF', preview_accent: '#33FF48', uppercase: true },
  { id: 'tiktok_box', name: 'TikTok Pill Box', description: 'Dark contrast box + yellow focus', preview_bg: '#000000', preview_text: '#FFFFFF', preview_accent: '#FFEA00', uppercase: false },
  { id: 'neon_cyan', name: 'Neon Cyber Cyan', description: 'Tech style glowing cyan word pop', preview_bg: '#082f49', preview_text: '#FFFFFF', preview_accent: '#00FFFF', uppercase: true },
  { id: 'iman_clean', name: 'Creator Minimal', description: 'Clean sentence case + amber accent', preview_bg: '#1e293b', preview_text: '#F5F5F5', preview_accent: '#FFB838', uppercase: false },
  { id: 'podcast_yellow', name: 'Cinema Yellow', description: 'Classic warm-yellow film captions', preview_bg: '#18181b', preview_text: '#FFE026', preview_accent: '#FFE026', uppercase: false },
  { id: 'red_hook', name: 'Red Alert Hook', description: 'Bold white + crimson red hook pop', preview_bg: '#2a0a0a', preview_text: '#FFFFFF', preview_accent: '#FF3B3B', uppercase: true },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analytics, setAnalytics] = useState({
    total_videos: 0,
    total_shorts: 0,
    pending_uploads: 0,
    completed_uploads: 0,
    recent_videos: [],
    recent_clips: [],
    top_clips: [],
    upcoming_scheduled: [],
    channel_info: {
      name: 'PDX',
      status: 'connected',
      mode: 'live',
      target_url: 'https://studio.youtube.com'
    }
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
  const [batchLayoutMode, setBatchLayoutMode] = useState('auto');
  const [batchSubtitleStyle, setBatchSubtitleStyle] = useState('hormozi');
  const [batchQualityPreset, setBatchQualityPreset] = useState('high');
  const [batchForceRerender, setBatchForceRerender] = useState(false);
  const [isBatchPublishing, setIsBatchPublishing] = useState(false);
  const [batchProgressText, setBatchProgressText] = useState('');
  const [batchResults, setBatchResults] = useState(null);

  // Active Job State for Real-Time Progress Bar & Activity Tracking
  const [activeJob, setActiveJob] = useState(null);

  // Upload & Pipeline State
  const [uploadMode, setUploadMode] = useState('local'); // 'local' | 'youtube'
  const [uploadFile, setUploadFile] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [youtubeResolution, setYoutubeResolution] = useState('720p');
  const [isInspecting, setIsInspecting] = useState(false);
  const [youtubeMetadata, setYoutubeMetadata] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Editor State
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editLayout, setEditLayout] = useState('auto');
  const [editSubtitleStyle, setEditSubtitleStyle] = useState('hormozi');
  const [editQualityPreset, setEditQualityPreset] = useState('high');
  const [subtitleStyles, setSubtitleStyles] = useState(DEFAULT_SUBTITLE_STYLES);
  const [singleScheduleTime, setSingleScheduleTime] = useState('');
  const [renderingClipId, setRenderingClipId] = useState(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [privacyStatus, setPrivacyStatus] = useState('public');

  // YouTube Discovery State
  const [discoverQuery, setDiscoverQuery] = useState('millionaire mindset discipline success habits speech interview');
  const [discoverMinMinutes, setDiscoverMinMinutes] = useState(5);
  const [discoverSortBy, setDiscoverSortBy] = useState('clip_potential');
  const [discoverPresets, setDiscoverPresets] = useState([
    { id: 'millionaire_mindset', name: '💰 Motivation & Millionaire Mindset', query: 'millionaire mindset discipline success habits speech interview' },
    { id: 'podcast_clips', name: '🎙️ Podcast Clips', query: 'podcast full episode best moments interview life advice' },
    { id: 'luxury_lifestyle', name: '💎 Luxury & Rich Lifestyle', query: 'billionaire luxury lifestyle supercars mansion tour wealth secrets' },
    { id: 'mystery_crime', name: '🕵️ Mystery & True Crime', query: 'unsolved mystery true crime documentary story explained' },
    { id: 'ai_future', name: '🤖 AI & Future Technology', query: 'AI future technology breakthrough explained podcast' },
    { id: 'psychology', name: '🧠 Psychology & Human Behaviour', query: 'human psychology dark psychology behaviour facts lecture' },
    { id: 'gta6_gaming', name: '🎮 GTA 6 & Gaming Hype', query: 'GTA 6 trailer breakdown hidden details gameplay secrets' },
  ]);
  const [discoverResults, setDiscoverResults] = useState([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoverStats, setDiscoverStats] = useState(null);

  useEffect(() => {
    fetchAnalytics();
    fetchVideos();
    fetchYouTubeUploads();
    fetchSubtitleStyles();
    fetchDiscoverPresets();
  }, []);

  const fetchDiscoverPresets = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/youtube/discover/presets`);
      if (res.ok) {
        const data = await res.json();
        if (data.presets && data.presets.length > 0) {
          setDiscoverPresets(data.presets);
        }
      }
    } catch (err) {
      console.error('Failed to load discovery presets:', err);
    }
  };

  const handleRunDiscovery = async (overrideQuery = null) => {
    const q = (overrideQuery !== null ? overrideQuery : discoverQuery).trim();
    if (!q) return;
    if (overrideQuery !== null) setDiscoverQuery(overrideQuery);
    setIsDiscovering(true);
    try {
      const res = await fetch(`${API_BASE}/api/youtube/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          min_duration_minutes: parseInt(discoverMinMinutes) || 5,
          max_duration_minutes: 150,
          max_results: 12,
          sort_by: discoverSortBy
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Discovery search failed');
      }
      const data = await res.json();
      setDiscoverResults(data.videos || []);
      setDiscoverStats({ total_scanned: data.total_scanned, qualified_count: data.qualified_count });
    } catch (err) {
      alert(`Discovery error: ${err.message}`);
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleDiscoverImportAndClip = async (videoItem, autoStart = true) => {
    setYoutubeUrl(videoItem.url);
    setYoutubeResolution('1080p');
    setUploadMode('youtube');
    setActiveTab('upload');

    if (!autoStart) {
      setIsInspecting(true);
      setYoutubeMetadata(null);
      try {
        const res = await fetch(`${API_BASE}/api/videos/youtube-inspect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: videoItem.url })
        });
        const data = await res.json();
        if (res.ok) {
          setYoutubeMetadata(data);
          if (data.available_resolutions?.length > 0) {
            setYoutubeResolution(data.available_resolutions.includes('1080p') ? '1080p' : data.available_resolutions[0]);
          }
        }
      } finally {
        setIsInspecting(false);
      }
      return;
    }

    // Auto-start 1080p download & AI story extraction
    setIsProcessing(true);
    setUploadProgress(15);
    const initialStatus = `Downloading 1080p "${videoItem.title.slice(0, 45)}..." for AI clipping...`;
    setProcessingStatus(initialStatus);
    setActiveJob({
      type: 'youtube',
      title: videoItem.title,
      percent: 15,
      stepIndex: 1,
      statusText: initialStatus
    });

    try {
      const res = await fetch(`${API_BASE}/api/videos/youtube-download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: videoItem.url, resolution: '1080p' })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'YouTube download failed');
      }
      const data = await res.json();
      setUploadProgress(35);
      setProcessingStatus('Downloaded! Starting Whisper AI transcription...');
      setActiveJob(prev => prev ? { ...prev, percent: 35, stepIndex: 2, statusText: 'Downloaded! Starting Whisper AI transcription...' } : null);
      startPipelinePolling(data.video.id, videoItem.title);
    } catch (err) {
      setIsProcessing(false);
      setActiveJob(null);
      alert(`Auto-Import failed: ${err.message}`);
    }
  };

  const fetchSubtitleStyles = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/subtitle-styles`);
      if (res.ok) {
        const data = await res.json();
        if (data.styles && data.styles.length > 0) {
          setSubtitleStyles(data.styles);
        }
      }
    } catch (err) {
      console.error('Failed to load subtitle styles:', err);
    }
  };

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
        setSelectedClipIds([]);

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
    if (clip.subtitle_style) {
      setEditSubtitleStyle(clip.subtitle_style);
    }
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

  // Polling helper with rich live status updates
  const startPipelinePolling = (videoId, videoTitle) => {
    const pollInterval = setInterval(async () => {
      try {
        const stRes = await fetch(`${API_BASE}/api/videos/${videoId}/status`);
        if (stRes.ok) {
          const stData = await stRes.json();
          if (stData.status === 'extracting_metadata' || stData.status === 'extracting_audio') {
            const statusMsg = `Extracting 16kHz audio track for Faster-Whisper AI speech analysis...`;
            setProcessingStatus(statusMsg);
            setUploadProgress(45);
            setActiveJob(prev => prev ? {
              ...prev,
              percent: 45,
              stepIndex: 2,
              statusText: statusMsg
            } : null);
          } else if (stData.status === 'transcribing') {
            const statusMsg = `Transcribing speech with Faster-Whisper CPU INT8 (word timestamps)...`;
            setProcessingStatus(statusMsg);
            setUploadProgress(65);
            setActiveJob(prev => prev ? {
              ...prev,
              percent: 65,
              stepIndex: 3,
              statusText: statusMsg
            } : null);
          } else if (stData.status === 'detecting_clips') {
            const statusMsg = `Analyzing 6 viral dimensions & segmenting distinct narrative moments...`;
            setProcessingStatus(statusMsg);
            setUploadProgress(85);
            setActiveJob(prev => prev ? {
              ...prev,
              percent: 85,
              stepIndex: 4,
              statusText: statusMsg
            } : null);
          } else if (stData.status === 'completed') {
            clearInterval(pollInterval);
            const statusMsg = `Completed! Distinct viral moments ready.`;
            setProcessingStatus(statusMsg);
            setUploadProgress(100);
            setActiveJob(prev => prev ? {
              ...prev,
              percent: 100,
              stepIndex: 4,
              statusText: statusMsg
            } : null);

            setTimeout(() => {
              setIsProcessing(false);
              setActiveJob(null);
            }, 3000);

            await fetchVideos();
            await fetchAnalytics();
            setSelectedVideo(stData);
            await loadClipsForVideo(videoId);
            setActiveTab('clips');
          } else if (stData.status === 'failed') {
            clearInterval(pollInterval);
            setIsProcessing(false);
            setActiveJob(null);
            alert(`Processing failed: ${stData.error_message}`);
          }
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    }, 1500);
  };

  // Video Upload Handler with Real-Time Byte-Level Progress
  const handleUploadSubmit = (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    const file = uploadFile;
    const totalMB = (file.size / (1024 * 1024)).toFixed(1);

    setIsProcessing(true);
    setUploadProgress(0);
    const initialStatus = `Uploading "${file.name}" (0% • 0.0 MB / ${totalMB} MB)...`;
    setProcessingStatus(initialStatus);
    setActiveJob({
      type: 'source_upload',
      title: file.name,
      statusText: initialStatus,
      percent: 0,
      stepIndex: 1,
      stepTotal: 4,
      loadedMB: '0.0',
      totalMB: totalMB
    });

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/api/videos/upload`);

    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) {
        const filePct = Math.round((evt.loaded / evt.total) * 100);
        // Map upload phase to 0% - 35% of total pipeline progress
        const overallProgress = Math.round(filePct * 0.35);
        const loadedMB = (evt.loaded / (1024 * 1024)).toFixed(1);

        setUploadProgress(overallProgress);
        const statusMsg = `Uploading "${file.name}" (${filePct}% • ${loadedMB} MB / ${totalMB} MB)...`;
        setProcessingStatus(statusMsg);
        setActiveJob(prev => prev ? {
          ...prev,
          percent: overallProgress,
          loadedMB: loadedMB,
          totalMB: totalMB,
          statusText: statusMsg
        } : null);
      }
    };

    xhr.onload = async () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          const videoId = data.video.id;

          setUploadProgress(35);
          const nextMsg = `Upload complete! Extracting audio & preparing Faster-Whisper...`;
          setProcessingStatus(nextMsg);
          setActiveJob(prev => prev ? {
            ...prev,
            percent: 35,
            stepIndex: 2,
            statusText: nextMsg
          } : null);

          startPipelinePolling(videoId, file.name);
        } catch (err) {
          setIsProcessing(false);
          setActiveJob(null);
          alert('Failed to parse server response: ' + err.message);
        }
      } else {
        setIsProcessing(false);
        setActiveJob(null);
        alert(`Upload failed (HTTP ${xhr.status}): ${xhr.responseText}`);
      }
    };

    xhr.onerror = () => {
      setIsProcessing(false);
      setActiveJob(null);
      alert('Upload failed due to a network connection error.');
    };

    xhr.send(formData);
  };

  // YouTube Inspect Handler
  const handleInspectYoutubeUrl = async () => {
    if (!youtubeUrl.trim()) return;
    setIsInspecting(true);
    try {
      const res = await fetch(`${API_BASE}/api/videos/youtube-inspect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: youtubeUrl.trim() })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Could not fetch YouTube video details');
      }
      const data = await res.json();
      setYoutubeMetadata(data);
      if (data.available_resolutions && data.available_resolutions.length > 0) {
        setYoutubeResolution(data.available_resolutions.includes('1080p') ? '1080p' : data.available_resolutions[0]);
      }
    } catch (err) {
      alert(`YouTube Inspect Error: ${err.message}`);
    } finally {
      setIsInspecting(false);
    }
  };

  // YouTube Download & Process Pipeline Handler
  const handleYoutubeDownloadSubmit = async (e) => {
    e.preventDefault();
    if (!youtubeUrl.trim()) return;

    const videoTitle = youtubeMetadata ? youtubeMetadata.title : 'YouTube Video';
    setIsProcessing(true);
    setUploadProgress(15);
    const initialStatus = `Connecting & downloading YouTube video (${youtubeResolution}) for "${videoTitle}"...`;
    setProcessingStatus(initialStatus);
    setActiveJob({
      type: 'youtube_download',
      title: videoTitle,
      statusText: initialStatus,
      percent: 15,
      stepIndex: 1,
      stepTotal: 4
    });

    try {
      const res = await fetch(`${API_BASE}/api/videos/youtube-download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: youtubeUrl.trim(),
          resolution: youtubeResolution
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'YouTube download failed');
      }

      const data = await res.json();
      const videoId = data.video.id;

      setUploadProgress(35);
      const nextMsg = `Download complete! Extracting audio & preparing Faster-Whisper CPU INT8...`;
      setProcessingStatus(nextMsg);
      setActiveJob(prev => prev ? {
        ...prev,
        percent: 35,
        stepIndex: 2,
        statusText: nextMsg
      } : null);

      startPipelinePolling(videoId, videoTitle);

    } catch (err) {
      setIsProcessing(false);
      setActiveJob(null);
      alert(`YouTube Download error: ${err.message}`);
    }
  };

  // Render Short Handler
  const handleRenderShort = async (clipId, customLayout = null) => {
    setRenderingClipId(clipId);
    const layout = customLayout || editLayout;
    const subStyle = editSubtitleStyle || 'hormozi';
    const quality = editQualityPreset || 'high';
    try {
      const res = await fetch(`${API_BASE}/api/clips/${clipId}/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          layout_mode: layout,
          include_subtitles: subStyle !== 'none',
          subtitle_style: subStyle,
          quality_preset: quality
        })
      });
      if (!res.ok) throw new Error('Render failed');
      const data = await res.json();
      
      const updated = data.clip;
      selectClipForPreview(updated);
      setClips(prev => prev.map(c => c.id === clipId ? updated : c));
      fetchAnalytics();
      alert(`Short rendered in 1080p Full HD (${quality.toUpperCase()}) with '${subStyle}' subtitles!`);
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
          custom_start_time: customStartTime ? new Date(customStartTime).toISOString() : null,
          layout_mode: batchLayoutMode,
          subtitle_style: batchSubtitleStyle,
          quality_preset: batchQualityPreset,
          force_rerender: batchForceRerender
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
            onClick={() => { setActiveTab('dashboard'); fetchAnalytics(); }}
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
            className={`nav-item ${activeTab === 'discover' ? 'active' : ''}`}
            onClick={() => setActiveTab('discover')}
          >
            <Search size={18} />
            <span>Discover Videos</span>
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

          {/* TAB 1: ENRICHED USEFUL DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div>
              {/* Channel Connection Banner */}
              <div className="channel-banner">
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, #ef4444, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 800, color: '#fff' }}>
                    PDX
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <h2 style={{ fontSize: 18, fontWeight: 800 }}>YouTube Channel: PDX</h2>
                      <span className="badge-live">
                        <span className="pulsing-dot"></span> Live API Connected
                      </span>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 2 }}>
                      Automated 9:16 Shorts pipeline with custom layout framing and 20–30m batch interval scheduling.
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setActiveTab('discover')}
                    style={{ display: 'flex', alignItems: 'center', gap: 6, borderColor: 'rgba(139, 92, 246, 0.45)', color: '#c4b5fd' }}
                  >
                    <Search size={14} /> Discover Best Videos
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => { setUploadMode('youtube'); setActiveTab('upload'); }}
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <Link2 size={14} /> Import from YouTube
                  </button>
                  <a
                    href="https://studio.youtube.com"
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-secondary btn-sm"
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <ExternalLink size={14} /> Open YouTube Studio
                  </a>
                  {clips.length > 0 && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => { selectAllClips(); setShowScheduleModal(true); }}
                      style={{ background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none' }}
                    >
                      <Calendar size={14} /> Schedule All ({clips.length})
                    </button>
                  )}
                </div>
              </div>

              {/* 4 Metric Cards */}
              <div className="metric-cards">
                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">Master Projects</span>
                    <Video size={18} color="var(--accent-red)" />
                  </div>
                  <div className="metric-value">{analytics.total_videos}</div>
                  <div className="metric-footer">Analyzed Long Videos</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">Story Moments</span>
                    <Flame size={18} color="var(--accent-orange)" />
                  </div>
                  <div className="metric-value">{clips.length || analytics.total_shorts}</div>
                  <div className="metric-footer">Distinct Narrative Clips</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">Rendered 9:16 Shorts</span>
                    <Sparkles size={18} color="var(--accent-purple)" />
                  </div>
                  <div className="metric-value">{analytics.total_shorts}</div>
                  <div className="metric-footer">Framed & Subtitled</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-title">PDX Published</span>
                    <Youtube size={18} color="var(--accent-green)" />
                  </div>
                  <div className="metric-value">{analytics.completed_uploads}</div>
                  <div className="metric-footer">Uploaded to YouTube</div>
                </div>
              </div>

              {/* 2-Column Dashboard Grid: Ranked Moments & Live Queue */}
              <div className="dashboard-grid">
                {/* Left Column: Top Viral Highlights with 1-Click Action */}
                <div className="dashboard-panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <div>
                      <h3 style={{ fontSize: 16, fontWeight: 700 }}>🔥 Top Ranked Story Moments</h3>
                      <p style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                        Top AI-scored self-contained clips from your video ready for immediate launch.
                      </p>
                    </div>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setActiveTab('clips')}
                    >
                      View All ({clips.length}) <ArrowRight size={14} />
                    </button>
                  </div>

                  {clips.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-muted)' }}>
                      <p>No project moments loaded.</p>
                      <button className="btn btn-primary btn-sm" style={{ marginTop: 10 }} onClick={() => setActiveTab('upload')}>
                        <Upload size={14} /> Upload Video Project
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {clips.slice(0, 4).map((c, i) => (
                        <div key={c.id} className="top-moment-card">
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12, maxWidth: '65%' }}>
                            <span style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? '#eab308' : '#94a3b8' }}>
                              #{i + 1}
                            </span>
                            <div>
                              <div style={{ fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {c.title}
                              </div>
                              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 3 }}>
                                <span className={`viral-badge ${c.viral_score >= 70 ? 'high' : 'medium'}`} style={{ padding: '2px 6px', fontSize: 11 }}>
                                  <Flame size={12} /> {c.viral_score}
                                </span>
                                {c.has_visual && (
                                  <span className="viral-badge" style={{ padding: '2px 6px', fontSize: 11, background: 'rgba(59, 130, 246, 0.18)', color: '#60a5fa' }}>
                                    🎨 Visual Demo
                                  </span>
                                )}
                                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                  ⏱️ {c.duration.toFixed(0)}s
                                </span>
                              </div>
                            </div>
                          </div>

                          <div style={{ display: 'flex', gap: 6 }}>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => { selectClipForPreview(c); setActiveTab('editor'); }}
                              title="Preview and edit clip"
                            >
                              <Eye size={13} />
                            </button>
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => handleRenderShort(c.id)}
                              disabled={renderingClipId === c.id}
                              title="Render in 9:16"
                            >
                              <Sparkles size={13} /> {c.output_path ? 'Re-Render' : 'Render'}
                            </button>
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handlePublishYouTube(c.id)}
                              disabled={isPublishing || !c.output_path}
                              title="Publish directly to PDX"
                            >
                              <Youtube size={13} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Column: Scheduled Release Queue & Strategy */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  {/* Scheduled Queue Box */}
                  <div className="dashboard-panel">
                    <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>📅 Release Queue</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 12 }}>
                      Upcoming Shorts scheduled on YouTube Data API.
                    </p>

                    {analytics.upcoming_scheduled && analytics.upcoming_scheduled.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 200, overflowY: 'auto' }}>
                        {analytics.upcoming_scheduled.map((sch, sIdx) => (
                          <div key={sch.id} style={{ background: 'var(--bg-secondary)', padding: '8px 12px', borderRadius: 8, fontSize: 12, border: '1px solid var(--border-color)' }}>
                            <div style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {sch.title}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#60a5fa', marginTop: 3 }}>
                              <span>⏰ {new Date(sch.scheduled_publish_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({new Date(sch.scheduled_publish_at).toLocaleDateString([], { month: 'short', day: 'numeric' })})</span>
                              {sch.youtube_url && (
                                <a href={sch.youtube_url} target="_blank" rel="noreferrer" style={{ color: '#3b82f6', textDecoration: 'none' }}>
                                  View ↗
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '16px 0', color: 'var(--text-muted)', fontSize: 12 }}>
                        No videos currently in the queue. Click "Schedule All" to queue your moments at 20–30 min intervals!
                      </div>
                    )}
                  </div>

                  {/* Growth & Algorithm Tips for PDX */}
                  <div className="dashboard-panel">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <TrendingUp size={16} color="var(--accent-orange)" />
                      <h3 style={{ fontSize: 15, fontWeight: 700 }}>PDX Channel Strategy</h3>
                    </div>

                    <div className="tip-box">
                      <strong>⚡ Pacing Velocity:</strong> Publishing every <strong>20 to 30 minutes</strong> gives YouTube's algorithm time to test each Short's seed audience without diluting initial viewer impressions.
                    </div>

                    <div className="tip-box" style={{ background: 'rgba(59, 130, 246, 0.08)', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                      <strong>🎨 Visual Retainers:</strong> Whiteboard demonstrations and visual diagrams achieve <strong>80%+ viewer completion rates</strong> on Shorts. Always prefer "Auto-Detect" or "Blurred Background" for these moments!
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: YOUTUBE BEST VIDEO DISCOVERY ALGORITHM */}
          {activeTab === 'discover' && (
            <div>
              <div className="page-header">
                <div>
                  <h1 className="page-title">🔍 Discover Best YouTube Videos to Clip</h1>
                  <p className="page-subtitle">
                    Smart 5-dimension ranking algorithm scans YouTube to find high-retention, spoken-word long-form videos ideal for viral 1080p Shorts.
                  </p>
                </div>
              </div>

              {/* Search & Filter Panel */}
              <div className="dashboard-panel" style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
                  <div style={{ flex: '1 1 360px' }}>
                    <label style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, display: 'block', marginBottom: 6 }}>
                      Topic, Niche, Guest, or Podcast Keyword
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. podcast mindset discipline, AI explained, entrepreneur interview..."
                      value={discoverQuery}
                      onChange={(e) => setDiscoverQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleRunDiscovery()}
                    />
                  </div>

                  <div style={{ width: 170 }}>
                    <label style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, display: 'block', marginBottom: 6 }}>
                      Min Video Length
                    </label>
                    <select
                      className="form-control"
                      value={discoverMinMinutes}
                      onChange={(e) => setDiscoverMinMinutes(Number(e.target.value))}
                    >
                      <option value={5}>5+ minutes</option>
                      <option value={10}>10+ minutes (Recommended)</option>
                      <option value={20}>20+ minutes (Podcasts)</option>
                      <option value={30}>30+ minutes (Deep-Dive)</option>
                    </select>
                  </div>

                  <div style={{ width: 195 }}>
                    <label style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, display: 'block', marginBottom: 6 }}>
                      Rank Videos By
                    </label>
                    <select
                      className="form-control"
                      value={discoverSortBy}
                      onChange={(e) => setDiscoverSortBy(e.target.value)}
                    >
                      <option value="clip_potential">🔥 Best Clip Potential</option>
                      <option value="max_views">👀 Highest Views (Viral Hype)</option>
                    </select>
                  </div>

                  <button
                    className="btn btn-primary"
                    onClick={() => handleRunDiscovery()}
                    disabled={isDiscovering}
                    style={{ height: 42, display: 'flex', alignItems: 'center', gap: 8 }}
                  >
                    <Search size={16} />
                    {isDiscovering ? 'Scanning & Ranking...' : 'Find Best Videos'}
                  </button>
                </div>

                {/* Preset Niche Chips */}
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>
                    ⚡ Quick Viral Niches (1-Click Search):
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {discoverPresets.map((preset) => (
                      <button
                        key={preset.id}
                        type="button"
                        className={`btn-chip ${discoverQuery === preset.query ? 'selected' : ''}`}
                        onClick={() => handleRunDiscovery(preset.query)}
                        disabled={isDiscovering}
                        title={preset.description}
                      >
                        {preset.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Discovery Results Summary */}
              {discoverStats && (
                <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>
                    Scanned <strong>{discoverStats.total_scanned}</strong> YouTube videos • Filtered out Shorts/music • Ranked top <strong>{discoverResults.length}</strong> clippable long-form matches
                  </span>
                </div>
              )}

              {/* Results Grid */}
              {isDiscovering ? (
                <div className="dashboard-panel" style={{ textAlign: 'center', padding: 48 }}>
                  <RefreshCw size={32} className="spin" style={{ margin: '0 auto 14px', color: '#3b82f6' }} />
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Running Clip-Potential Algorithm...</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                    Evaluating duration, audience reach, spoken-word density, and viral hook signals.
                  </p>
                </div>
              ) : discoverResults.length === 0 ? (
                <div className="dashboard-panel" style={{ textAlign: 'center', padding: 48 }}>
                  <TrendingUp size={36} style={{ margin: '0 auto 12px', color: '#8b5cf6' }} />
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Find Your Next Viral Source Video</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 520, margin: '0 auto 18px' }}>
                    Choose a preset niche above or type any topic and click <strong>Find Best Videos</strong>. Our algorithm scores YouTube videos from 0–100 based on clip yield and viral potential.
                  </p>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleRunDiscovery()}
                  >
                    <Zap size={16} /> Scan Top Podcast & Mindset Videos Now
                  </button>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 18 }}>
                  {discoverResults.map((vid, idx) => {
                    const mins = Math.floor(vid.duration / 60);
                    const secs = vid.duration % 60;
                    const durStr = `${mins}:${secs.toString().padStart(2, '0')}`;
                    const viewsStr = vid.view_count >= 1000000
                      ? `${(vid.view_count / 1000000).toFixed(1)}M views`
                      : vid.view_count >= 1000
                      ? `${(vid.view_count / 1000).toFixed(1)}K views`
                      : `${vid.view_count} views`;

                    return (
                      <div
                        key={vid.id}
                        className="dashboard-panel"
                        style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
                      >
                        <div>
                          {/* Thumbnail + Badges */}
                          <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#09090b' }}>
                            <img
                              src={vid.thumbnail}
                              alt={vid.title}
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                            <div style={{
                              position: 'absolute',
                              top: 10,
                              left: 10,
                              background: idx < 3 ? 'linear-gradient(135deg, #f59e0b, #ef4444)' : 'rgba(15, 23, 42, 0.88)',
                              color: '#fff',
                              padding: '4px 10px',
                              borderRadius: 20,
                              fontSize: 12,
                              fontWeight: 800,
                              boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
                            }}>
                              {idx === 0 ? '🏆 ' : '🔥 '}Score: {vid.clip_potential_score}/100
                            </div>
                            <div style={{
                              position: 'absolute',
                              bottom: 8,
                              right: 8,
                              background: 'rgba(0,0,0,0.82)',
                              color: '#fff',
                              padding: '3px 7px',
                              borderRadius: 6,
                              fontSize: 11,
                              fontWeight: 700
                            }}>
                              {durStr}
                            </div>
                          </div>

                          <div style={{ padding: 16 }}>
                            <h3 style={{
                              fontSize: 14,
                              fontWeight: 700,
                              lineHeight: 1.35,
                              marginBottom: 6,
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden'
                            }}>
                              {vid.title}
                            </h3>
                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10 }}>
                              {vid.channel} • {viewsStr} • <strong style={{ color: '#34d399' }}>~{vid.estimated_clips} Shorts</strong>
                            </div>

                            {/* Reason Chips */}
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                              {vid.reasons.map((r, rIdx) => (
                                <span
                                  key={rIdx}
                                  style={{
                                    fontSize: 11,
                                    padding: '3px 8px',
                                    borderRadius: 6,
                                    background: 'rgba(59, 130, 246, 0.14)',
                                    color: '#93c5fd',
                                    border: '1px solid rgba(59, 130, 246, 0.25)'
                                  }}
                                >
                                  {r}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div style={{ padding: '0 16px 16px', display: 'flex', gap: 8 }}>
                          <button
                            className="btn btn-primary btn-sm"
                            style={{ flex: 1, justifyContent: 'center' }}
                            onClick={() => handleDiscoverImportAndClip(vid, true)}
                            disabled={isProcessing}
                          >
                            <Zap size={14} /> Import & Auto-Clip
                          </button>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleDiscoverImportAndClip(vid, false)}
                            title="Open in YouTube Downloader to inspect resolutions"
                          >
                            <Link2 size={14} /> Inspect
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: NEW PROJECT (LOCAL UPLOAD OR YOUTUBE URL) */}
          {activeTab === 'upload' && (
            <div style={{ maxWidth: 720, margin: '0 auto' }}>
              <div className="editor-form">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div>
                    <h2 style={{ fontSize: 20, fontWeight: 700 }}>New Video Project</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 2 }}>
                      Add a video to detect complete narrative story moments and whiteboard visuals.
                    </p>
                  </div>
                </div>

                {/* Mode Switcher Tabs */}
                <div className="upload-mode-switcher">
                  <button
                    type="button"
                    className={`mode-tab-btn ${uploadMode === 'local' ? 'active' : ''}`}
                    onClick={() => setUploadMode('local')}
                  >
                    <Upload size={16} /> Upload Local File (Up to 1.5 GB)
                  </button>
                  <button
                    type="button"
                    className={`mode-tab-btn ${uploadMode === 'youtube' ? 'active' : ''}`}
                    onClick={() => setUploadMode('youtube')}
                  >
                    <Link2 size={16} /> Paste YouTube Link
                  </button>
                </div>

                {/* MODE 1: LOCAL FILE DROPZONE */}
                {uploadMode === 'local' && (
                  <div>
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
                      <p>{uploadFile ? `${(uploadFile.size / (1024 * 1024)).toFixed(1)} MB` : 'Supports MP4, MOV, MKV, AVI • Up to 1.5 GB'}</p>
                    </div>

                    <button
                      className="btn btn-primary"
                      onClick={handleUploadSubmit}
                      disabled={!uploadFile || isProcessing}
                      style={{ width: '100%', padding: '14px' }}
                    >
                      <Sparkles size={18} />
                      {isProcessing ? 'Processing Pipeline...' : 'Start AI Story Analysis'}
                    </button>
                  </div>
                )}

                {/* MODE 2: YOUTUBE URL DOWNLOAD & RESOLUTION SELECTOR */}
                {uploadMode === 'youtube' && (
                  <div>
                    <div className="form-group" style={{ marginBottom: 16 }}>
                      <label>Paste YouTube Video or Shorts URL</label>
                      <div style={{ display: 'flex', gap: 10 }}>
                        <input
                          type="text"
                          className="form-control"
                          placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/..."
                          value={youtubeUrl}
                          onChange={(e) => {
                            setYoutubeUrl(e.target.value);
                            setYoutubeMetadata(null);
                          }}
                        />
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={handleInspectYoutubeUrl}
                          disabled={!youtubeUrl.trim() || isInspecting || isProcessing}
                          style={{ whiteSpace: 'nowrap' }}
                        >
                          <Search size={15} />
                          {isInspecting ? 'Fetching...' : 'Inspect Video'}
                        </button>
                      </div>
                    </div>

                    {/* YouTube Video Preview Card */}
                    {youtubeMetadata && (
                      <div className="yt-preview-card">
                        {youtubeMetadata.thumbnail && (
                          <div className="yt-thumb-box">
                            <img src={youtubeMetadata.thumbnail} alt="YouTube thumbnail" />
                          </div>
                        )}
                        <div style={{ flex: 1 }}>
                          <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>
                            {youtubeMetadata.title}
                          </h4>
                          <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                            <span>📺 {youtubeMetadata.channel}</span>
                            <span>⏱️ {Math.floor(youtubeMetadata.duration / 60)}m {youtubeMetadata.duration % 60}s</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Target Resolution Selection */}
                    <div className="form-group" style={{ marginBottom: 20 }}>
                      <label>Download Resolution</label>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
                        {['1080p', '720p', '480p', 'Best Available'].map((res) => (
                          <button
                            key={res}
                            type="button"
                            className={`btn-chip ${youtubeResolution === res ? 'selected' : ''}`}
                            onClick={() => setYoutubeResolution(res)}
                            disabled={isProcessing}
                          >
                            {res === '1080p' ? '1080p (Full HD - Best Quality)' : (res === '720p' ? '720p (HD - Fast Download)' : res)}
                          </button>
                        ))}
                      </div>
                    </div>

                    <button
                      className="btn btn-primary"
                      onClick={handleYoutubeDownloadSubmit}
                      disabled={!youtubeUrl.trim() || isProcessing}
                      style={{ width: '100%', padding: '14px', background: 'linear-gradient(135deg, #ef4444, #8b5cf6)' }}
                    >
                      <Download size={18} />
                      {isProcessing ? 'Processing Pipeline...' : `Download ${youtubeResolution} & Start AI Story Detection`}
                    </button>
                  </div>
                )}

                {/* Pipeline Progress Display */}
                {isProcessing && (
                  <div style={{ background: 'var(--bg-secondary)', padding: 16, borderRadius: 8, marginTop: 18, border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
                      <span style={{ color: '#60a5fa', fontWeight: 600 }}>{processingStatus}</span>
                      <span style={{ fontWeight: 700 }}>{uploadProgress}%</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                    </div>
                  </div>
                )}
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

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                        <div className="form-group">
                          <label>Vertical 9:16 Layout</label>
                          <select
                            className="form-control"
                            value={editLayout}
                            onChange={(e) => setEditLayout(e.target.value)}
                          >
                            <option value="auto">⚡ Auto-Detect</option>
                            <option value="blur_background">🌟 Blurred Background</option>
                            <option value="smart_crop">🎯 Smart Crop</option>
                          </select>
                        </div>

                        <div className="form-group">
                          <label style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Film size={13} color="#60a5fa" /> Video Quality
                          </label>
                          <select
                            className="form-control"
                            value={editQualityPreset}
                            onChange={(e) => setEditQualityPreset(e.target.value)}
                          >
                            <option value="high">🎬 1080p Full HD (High)</option>
                            <option value="ultra">💎 1080p Ultra Crisp (Studio)</option>
                            <option value="balanced">⚡ 1080p Balanced (Fast)</option>
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

                      {/* Popular Subtitle Styles Picker */}
                      <div className="form-group">
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                          <Type size={14} color="#f59e0b" /> Popular Creator Subtitle Style
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 8 }}>
                          {subtitleStyles.map((st) => {
                            const isSelected = editSubtitleStyle === st.id;
                            return (
                              <button
                                key={st.id}
                                type="button"
                                onClick={() => setEditSubtitleStyle(st.id)}
                                title={st.description}
                                style={{
                                  background: isSelected ? 'rgba(59, 130, 246, 0.16)' : 'var(--bg-secondary)',
                                  border: isSelected ? '1.5px solid #3b82f6' : '1px solid var(--border-color)',
                                  borderRadius: 10,
                                  padding: '8px 10px',
                                  textAlign: 'left',
                                  cursor: 'pointer',
                                  transition: 'all 0.15s ease'
                                }}
                              >
                                <div style={{
                                  background: st.preview_bg,
                                  borderRadius: 6,
                                  padding: '4px 8px',
                                  marginBottom: 6,
                                  textAlign: 'center',
                                  fontWeight: 800,
                                  fontSize: 11,
                                  letterSpacing: '0.4px',
                                  color: st.preview_text,
                                  border: '1px solid rgba(255,255,255,0.08)'
                                }}>
                                  {st.uppercase ? 'WAIT ' : 'Wait '}
                                  <span style={{ color: st.preview_accent }}>
                                    {st.uppercase ? 'THIS!' : 'this!'}
                                  </span>
                                </div>
                                <div style={{ fontSize: 12, fontWeight: 700, color: isSelected ? '#93c5fd' : '#f0f3fa' }}>
                                  {st.name}
                                </div>
                              </button>
                            );
                          })}
                          <button
                            type="button"
                            onClick={() => setEditSubtitleStyle('none')}
                            style={{
                              background: editSubtitleStyle === 'none' ? 'rgba(239, 68, 68, 0.14)' : 'var(--bg-secondary)',
                              border: editSubtitleStyle === 'none' ? '1.5px solid #ef4444' : '1px solid var(--border-color)',
                              borderRadius: 10,
                              padding: '8px 10px',
                              textAlign: 'left',
                              cursor: 'pointer'
                            }}
                          >
                            <div style={{
                              background: '#09090b',
                              borderRadius: 6,
                              padding: '4px 8px',
                              marginBottom: 6,
                              textAlign: 'center',
                              fontWeight: 600,
                              fontSize: 11,
                              color: '#71717a',
                              border: '1px solid rgba(255,255,255,0.08)'
                            }}>
                              (Clean Video)
                            </div>
                            <div style={{ fontSize: 12, fontWeight: 700, color: editSubtitleStyle === 'none' ? '#fca5a5' : 'var(--text-secondary)' }}>
                              No Subtitles
                            </div>
                          </button>
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

              {/* Informational Alert if Daily Limit Exceeded */}
              {uploads.some(u => (u.error_message || '').includes('uploadLimitExceeded')) && (
                <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: 10, padding: 14, marginBottom: 18, fontSize: 13 }}>
                  <div style={{ fontWeight: 700, color: '#f87171', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    ⚠️ YouTube Daily Upload Quota Limit Reached
                  </div>
                  <p style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Google has a strict limit on brand new channels (around 3 to 10 videos per day) until the channel is verified.
                    To unlock 50+ to 100 daily Shorts uploads:
                  </p>
                  <ol style={{ paddingLeft: 18, marginTop: 6, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <li>Go to <strong>YouTube Studio &gt; Settings &gt; Channel &gt; Feature eligibility</strong></li>
                    <li>Verify your <strong>Phone Number</strong> under <em>Intermediate features</em>.</li>
                    <li>Enable <em>Advanced features</em> (via video verification or 2 months of channel history).</li>
                  </ol>
                  <div style={{ marginTop: 8 }}>
                    <a
                      href="https://studio.youtube.com/channel/UC/editing/details"
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: '#60a5fa', fontWeight: 600 }}
                    >
                      Open YouTube Studio Feature Eligibility ↗
                    </a>
                  </div>
                </div>
              )}

              {uploads.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No Shorts uploaded to YouTube yet.</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Privacy</th>
                      <th>Status / Reason</th>
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
                            {u.upload_status === 'published' ? '✓ Published' : '✕ Failed'}
                          </span>
                          {u.error_message && (
                            <div style={{ fontSize: 11, color: '#f87171', marginTop: 4, maxWidth: 220 }}>
                              {u.error_message.includes('uploadLimitExceeded')
                                ? '⚠️ Daily limit exceeded by YouTube (Verify channel phone number)'
                                : u.error_message.slice(0, 80)}
                            </div>
                          )}
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

      {/* SCHEDULE & BATCH UPLOAD MODAL WITH 9:16 LAYOUT CONTROL */}
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

            {/* NEW: Crop / Vertical 9:16 Framing, Subtitle Style & 1080p Quality in Schedule Section */}
            <div className="form-group" style={{ marginBottom: 16, background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 10, border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <Layers size={16} color="#3b82f6" />
                <label style={{ margin: 0, fontWeight: 700, color: '#f0f3fa' }}>
                  1080p Framing Layout & Popular Subtitle Style
                </label>
              </div>
              <select
                className="form-control"
                value={batchLayoutMode}
                onChange={(e) => setBatchLayoutMode(e.target.value)}
                style={{ marginBottom: 10 }}
              >
                <option value="auto">⚡ Auto-Detect (Best: Keeps full Whiteboards & Charts visible with fit)</option>
                <option value="blur_background">🌟 Blurred Background (Fit & Center full 16:9 with ambient glow)</option>
                <option value="smart_crop">🎯 Smart Crop (Center-fill speaker in 9:16 vertical)</option>
              </select>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>
                    Subtitle Style
                  </label>
                  <select
                    className="form-control"
                    value={batchSubtitleStyle}
                    onChange={(e) => setBatchSubtitleStyle(e.target.value)}
                  >
                    {subtitleStyles.map((st) => (
                      <option key={st.id} value={st.id}>{st.name}</option>
                    ))}
                    <option value="none">No Subtitles</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>
                    Export Video Quality
                  </label>
                  <select
                    className="form-control"
                    value={batchQualityPreset}
                    onChange={(e) => setBatchQualityPreset(e.target.value)}
                  >
                    <option value="high">🎬 1080p Full HD (High)</option>
                    <option value="ultra">💎 1080p Ultra Crisp</option>
                    <option value="balanced">⚡ 1080p Balanced (Fast)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10 }}>
                <input
                  type="checkbox"
                  id="batch-rerender-check"
                  className="batch-checkbox"
                  checked={batchForceRerender}
                  onChange={(e) => setBatchForceRerender(e.target.checked)}
                />
                <label htmlFor="batch-rerender-check" style={{ fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  Re-render selected clips in 1080p HD with this layout & subtitle style before publishing
                </label>
              </div>
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
