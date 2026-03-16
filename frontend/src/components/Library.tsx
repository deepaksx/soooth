import { useState, useEffect } from "react";

const API_BASE = import.meta.env.PROD
  ? "https://soooth-backend.onrender.com/api"
  : "http://localhost:8001/api";

interface VideoFile {
  filename: string;
  path: string;
  size: number;
  size_mb: number;
  modified: number;
}

export function Library() {
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<{ filename: string; url: string } | null>(null);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      const res = await fetch(`${API_BASE}/library/local-output`);
      const data = await res.json();
      setVideos(data.files || []);
    } catch (err) {
      console.error("Failed to load videos:", err);
    } finally {
      setLoading(false);
    }
  };

  const uploadToYouTube = async (video: VideoFile) => {
    setUploading(video.filename);
    setUploadResult(null);

    try {
      const res = await fetch(`${API_BASE}/library/upload-to-youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: video.filename,
          privacy: "public",
          // title & description omitted - backend will auto-generate SEO-optimized metadata
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Upload failed");
      }

      const data = await res.json();
      setUploadResult({ filename: video.filename, url: data.url });
      alert(`✅ Uploaded successfully!\n\nYouTube URL: ${data.url}`);
    } catch (err: any) {
      alert(`❌ Upload failed: ${err.message}`);
    } finally {
      setUploading(null);
    }
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const getVideoUrl = (filename: string) => {
    return `${API_BASE}/library/video/${filename}`;
  };

  if (loading) {
    return <div className="library">Loading videos...</div>;
  }

  return (
    <div className="library">
      <h2>Video Library ({videos.length} videos)</h2>

      {videos.length === 0 ? (
        <p className="library-empty">No videos in output folder yet. Generate some videos first!</p>
      ) : (
        <div className="library-grid">
          {videos.map((video) => (
            <div key={video.filename} className="library-card">
              <div className="library-video">
                <video
                  controls
                  preload="metadata"
                  className="library-video-player"
                  src={getVideoUrl(video.filename)}
                />
              </div>

              <div className="library-info">
                <div className="library-filename">{video.filename}</div>
                <div className="library-meta">
                  {video.size_mb} MB • {formatDate(video.modified)}
                </div>

                <button
                  className="library-upload-btn"
                  onClick={() => uploadToYouTube(video)}
                  disabled={uploading === video.filename}
                >
                  {uploading === video.filename ? (
                    <span>⏳ Uploading...</span>
                  ) : uploadResult?.filename === video.filename ? (
                    <span>✅ Uploaded</span>
                  ) : (
                    <span>📤 Upload to YouTube</span>
                  )}
                </button>

                {uploadResult?.filename === video.filename && (
                  <a
                    href={uploadResult.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="library-youtube-link"
                  >
                    🎥 View on YouTube
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
