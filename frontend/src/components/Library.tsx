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
      // Use S3 library for production (persistent storage)
      const res = await fetch(`${API_BASE}/library/output`);
      const data = await res.json();
      setVideos(data.files || []);
    } catch (err) {
      console.error("Failed to load videos:", err);
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
            <div key={video.key} className="library-card">
              <div className="library-video">
                <video
                  controls
                  preload="metadata"
                  className="library-video-player"
                  src={video.url}
                />
              </div>

              <div className="library-info">
                <div className="library-filename">{getFilename(video.key)}</div>
                <div className="library-meta">
                  {formatSize(video.size)} MB • {formatDate(video.last_modified)}
                </div>

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
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
