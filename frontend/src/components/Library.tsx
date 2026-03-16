import { useState, useEffect } from "react";

const API_BASE = import.meta.env.PROD
  ? "https://soooth-backend.onrender.com/api"
  : "http://localhost:8001/api";

interface VideoFile {
  key: string;
  url: string;
  size: number;
  last_modified: string;
}

type FolderType = "videos" | "audio" | "output";

export function Library() {
  const [activeFolder, setActiveFolder] = useState<FolderType>("output");
  const [files, setFiles] = useState<VideoFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<{ filename: string; url: string } | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  useEffect(() => {
    loadFiles(activeFolder);
  }, [activeFolder]);

  const loadFiles = async (folder: FolderType) => {
    setLoading(true);
    try {
      // Use S3 library for production (persistent storage)
      const res = await fetch(`${API_BASE}/library/${folder}`);
      const data = await res.json();
      setFiles(data.files || []);
    } catch (err) {
      console.error(`Failed to load ${folder}:`, err);
    } finally {
      setLoading(false);
    }
  };

  const uploadToYouTube = async (video: VideoFile) => {
    setUploading(video.key);
    setUploadResult(null);

    try {
      // Extract filename from S3 key (e.g., "output/job-id.mp4" -> "job-id.mp4")
      const filename = video.key.split('/').pop() || video.key;

      const res = await fetch(`${API_BASE}/library/upload-to-youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: filename,
          privacy: "public",
          // title & description omitted - backend will auto-generate SEO-optimized metadata
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Upload failed");
      }

      const data = await res.json();
      setUploadResult({ filename: video.key, url: data.url });
      alert(`✅ Uploaded successfully!\n\nYouTube URL: ${data.url}`);
    } catch (err: any) {
      alert(`❌ Upload failed: ${err.message}`);
    } finally {
      setUploading(null);
    }
  };

  const deleteFile = async (video: VideoFile) => {
    setDeleting(video.key);

    try {
      const res = await fetch(`${API_BASE}/library/delete`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          key: video.key,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Delete failed");
      }

      // Remove from local state
      setFiles(files.filter(f => f.key !== video.key));
      setConfirmDelete(null);
      alert(`✅ Deleted successfully: ${getFilename(video.key)}`);
    } catch (err: any) {
      alert(`❌ Delete failed: ${err.message}`);
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const getFilename = (key: string) => {
    return key.split('/').pop() || key;
  };

  const formatSize = (bytes: number) => {
    return (bytes / (1024 * 1024)).toFixed(2);
  };

  const getFolderLabel = (folder: FolderType) => {
    switch (folder) {
      case "videos": return "📹 Stock Clips";
      case "audio": return "🎵 Audio Files";
      case "output": return "🎬 Final Videos";
    }
  };

  const getFolderEmptyMessage = (folder: FolderType) => {
    switch (folder) {
      case "videos": return "No stock video clips cached yet. Generate a video to download clips.";
      case "audio": return "No audio files generated yet. Create a video with audio.";
      case "output": return "No output videos yet. Generate your first video!";
    }
  };

  const isVideo = (key: string) => key.endsWith('.mp4') || key.endsWith('.webm');
  const isAudio = (key: string) => key.endsWith('.mp3') || key.endsWith('.wav') || key.endsWith('.m4a');

  if (loading) {
    return <div className="library">Loading {activeFolder}...</div>;
  }

  return (
    <div className="library">
      <div className="library-header">
        <h2>AWS S3 Media Library</h2>
        <div className="library-tabs">
          <button
            className={`library-tab ${activeFolder === "output" ? "active" : ""}`}
            onClick={() => setActiveFolder("output")}
          >
            {getFolderLabel("output")} ({files.length})
          </button>
          <button
            className={`library-tab ${activeFolder === "videos" ? "active" : ""}`}
            onClick={() => setActiveFolder("videos")}
          >
            {getFolderLabel("videos")}
          </button>
          <button
            className={`library-tab ${activeFolder === "audio" ? "active" : ""}`}
            onClick={() => setActiveFolder("audio")}
          >
            {getFolderLabel("audio")}
          </button>
        </div>
      </div>

      {files.length === 0 ? (
        <p className="library-empty">{getFolderEmptyMessage(activeFolder)}</p>
      ) : (
        <div className="library-grid">
          {files.map((video) => (
            <div key={video.key} className="library-card">
              <div className="library-media">
                {isVideo(video.key) ? (
                  <video
                    controls
                    preload="metadata"
                    className="library-video-player"
                    src={video.url}
                  />
                ) : isAudio(video.key) ? (
                  <div className="library-audio-player">
                    🎵
                    <audio controls src={video.url} />
                  </div>
                ) : (
                  <div className="library-file-icon">📄</div>
                )}
              </div>

              <div className="library-info">
                <div className="library-filename" title={video.key}>
                  {getFilename(video.key)}
                </div>
                <div className="library-meta">
                  {formatSize(video.size)} MB • {formatDate(video.last_modified)}
                </div>
                <div className="library-url">
                  <a href={video.url} target="_blank" rel="noopener noreferrer">
                    🔗 Direct Link
                  </a>
                </div>

                {confirmDelete === video.key ? (
                  <div className="library-delete-confirm">
                    <p>Delete this file?</p>
                    <div className="library-delete-actions">
                      <button
                        className="library-btn library-btn-danger"
                        onClick={() => deleteFile(video)}
                        disabled={deleting === video.key}
                      >
                        {deleting === video.key ? "Deleting..." : "Yes, Delete"}
                      </button>
                      <button
                        className="library-btn library-btn-secondary"
                        onClick={() => setConfirmDelete(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    className="library-btn library-btn-delete"
                    onClick={() => setConfirmDelete(video.key)}
                  >
                    🗑️ Delete File
                  </button>
                )}

                {activeFolder === "output" && isVideo(video.key) && (
                  <>
                    <button
                      className="library-upload-btn"
                      onClick={() => uploadToYouTube(video)}
                      disabled={uploading === video.key}
                    >
                      {uploading === video.key ? (
                        <span>⏳ Uploading...</span>
                      ) : uploadResult?.filename === video.key ? (
                        <span>✅ Uploaded</span>
                      ) : (
                        <span>📤 Upload to YouTube</span>
                      )}
                    </button>

                    {uploadResult?.filename === video.key && (
                      <a
                        href={uploadResult.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="library-youtube-link"
                      >
                        🎥 View on YouTube
                      </a>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
