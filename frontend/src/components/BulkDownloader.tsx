import { useState, useEffect } from "react";

const API_BASE = import.meta.env.PROD
  ? "https://soooth-backend.onrender.com/api"
  : "http://localhost:8001/api";

interface BulkDownloadStatus {
  running: boolean;
  started_at: string | null;
  current_theme: string | null;
  themes_completed: number;
  total_themes: number;
  videos_downloaded: number;
  current_theme_progress: { downloaded: number; needed: number };
  error: string | null;
  s3_enabled: boolean;
  pixabay_configured: boolean;
}

interface CacheStats {
  themes: Record<string, { count: number; target: number; percentage: number }>;
  total: { count: number; target: number; percentage: number };
}

export function BulkDownloader() {
  const [status, setStatus] = useState<BulkDownloadStatus | null>(null);
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
    loadStats();

    // Poll status every 3 seconds if running
    const interval = setInterval(() => {
      if (status?.running) {
        loadStatus();
        loadStats();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [status?.running]);

  const loadStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/bulk-download/status`);
      const data = await res.json();
      setStatus(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load bulk download status:", err);
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/cache-stats`);
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error("Failed to load cache stats:", err);
    }
  };

  const startDownload = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/bulk-download/start`, {
        method: "POST",
      });

      if (!res.ok) {
        const error = await res.json();
        alert(`Failed to start: ${error.detail}`);
        return;
      }

      await loadStatus();
      alert("Bulk download started! This will take 2-4 hours.");
    } catch (err: any) {
      alert(`Failed to start: ${err.message}`);
    }
  };

  if (loading) {
    return <div className="bulk-downloader">Loading...</div>;
  }

  if (!status) {
    return null;
  }

  const canStart = status.s3_enabled && status.pixabay_configured && !status.running;
  const progress = status.total_themes > 0
    ? Math.round((status.themes_completed / status.total_themes) * 100)
    : 0;

  return (
    <div className="bulk-downloader">
      <div className="bulk-downloader-header">
        <h3>4K Video Cache Builder</h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="details-toggle"
        >
          {showDetails ? "Hide" : "Show"} Details
        </button>
      </div>

      <div className="bulk-downloader-content">
        {/* Configuration Status */}
        <div className="config-status">
          <div className={`status-item ${status.s3_enabled ? "ok" : "error"}`}>
            {status.s3_enabled ? "✓" : "✗"} S3 Storage
          </div>
          <div className={`status-item ${status.pixabay_configured ? "ok" : "error"}`}>
            {status.pixabay_configured ? "✓" : "✗"} Pixabay API
          </div>
        </div>

        {/* Overall Progress */}
        {stats && (
          <div className="cache-stats">
            <div className="stat-row">
              <span>Total Videos Cached:</span>
              <strong>{stats.total.count} / {stats.total.target}</strong>
              <span className="percentage">({stats.total.percentage}%)</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${stats.total.percentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Current Download Status */}
        {status.running && (
          <div className="download-status">
            <div className="status-badge running">Downloading...</div>
            <div className="current-progress">
              <div>Theme: <strong>{status.current_theme || "Starting..."}</strong></div>
              <div>
                Progress: {status.current_theme_progress.downloaded} / {status.current_theme_progress.needed}
              </div>
              <div>Completed: {status.themes_completed} / {status.total_themes} themes</div>
              <div>Total downloaded: {status.videos_downloaded} videos</div>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill active"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error */}
        {status.error && (
          <div className="error-message">
            <strong>Error:</strong> {status.error}
          </div>
        )}

        {/* Action Button */}
        {!status.running && (
          <button
            onClick={startDownload}
            disabled={!canStart}
            className="start-download-btn"
          >
            {canStart
              ? "🚀 Start Bulk Download (100 videos × 15 themes)"
              : "⚠️ Configuration Required"}
          </button>
        )}

        {!canStart && !status.running && (
          <div className="warning-message">
            {!status.s3_enabled && <p>• S3 storage not configured</p>}
            {!status.pixabay_configured && <p>• Pixabay API key not set</p>}
          </div>
        )}

        {/* Detailed Stats */}
        {showDetails && stats && (
          <div className="theme-stats">
            <h4>Cache Details by Theme:</h4>
            <div className="theme-grid">
              {Object.entries(stats.themes).map(([theme, data]) => (
                <div key={theme} className="theme-stat">
                  <div className="theme-name">{theme}</div>
                  <div className="theme-count">
                    {data.count} / {data.target}
                  </div>
                  <div className="mini-progress-bar">
                    <div
                      className="mini-progress-fill"
                      style={{
                        width: `${data.percentage}%`,
                        backgroundColor: data.percentage === 100 ? "#7cb8a0" : "#ffa500",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info */}
        <div className="info-text">
          <p>
            <strong>What this does:</strong> Downloads 100 high-quality 4K/HD videos for each theme
            (1,500 total). This improves video quality and generation speed.
          </p>
          <p>
            <strong>Duration:</strong> 2-4 hours. You can close this page - the download runs on the server.
          </p>
        </div>
      </div>

      <style>{`
        .bulk-downloader {
          background: #1a2a25;
          border: 1px solid #7cb8a0;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 30px;
        }

        .bulk-downloader-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .bulk-downloader-header h3 {
          margin: 0;
          color: #7cb8a0;
        }

        .details-toggle {
          background: transparent;
          border: 1px solid #7cb8a0;
          color: #7cb8a0;
          padding: 5px 15px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.85rem;
        }

        .details-toggle:hover {
          background: rgba(124, 184, 160, 0.1);
        }

        .config-status {
          display: flex;
          gap: 15px;
          margin-bottom: 20px;
        }

        .status-item {
          padding: 8px 16px;
          border-radius: 4px;
          font-size: 0.9rem;
        }

        .status-item.ok {
          background: rgba(124, 184, 160, 0.2);
          color: #7cb8a0;
        }

        .status-item.error {
          background: rgba(255, 100, 100, 0.2);
          color: #ff6464;
        }

        .cache-stats {
          margin-bottom: 20px;
        }

        .stat-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
          font-size: 0.95rem;
        }

        .stat-row .percentage {
          color: #7cb8a0;
        }

        .progress-bar {
          height: 8px;
          background: rgba(124, 184, 160, 0.2);
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: #7cb8a0;
          transition: width 0.3s ease;
        }

        .progress-fill.active {
          background: linear-gradient(90deg, #7cb8a0, #5a8c7a, #7cb8a0);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }

        .download-status {
          background: rgba(124, 184, 160, 0.1);
          border: 1px solid #7cb8a0;
          border-radius: 6px;
          padding: 15px;
          margin-bottom: 20px;
        }

        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 0.85rem;
          font-weight: bold;
          margin-bottom: 10px;
        }

        .status-badge.running {
          background: #7cb8a0;
          color: #0a0a0f;
        }

        .current-progress div {
          margin: 5px 0;
          font-size: 0.9rem;
        }

        .start-download-btn {
          width: 100%;
          padding: 15px;
          background: #7cb8a0;
          color: #0a0a0f;
          border: none;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: bold;
          cursor: pointer;
          margin-bottom: 15px;
        }

        .start-download-btn:hover:not(:disabled) {
          background: #8ec8b0;
        }

        .start-download-btn:disabled {
          background: #555;
          color: #888;
          cursor: not-allowed;
        }

        .error-message {
          background: rgba(255, 100, 100, 0.2);
          border: 1px solid #ff6464;
          color: #ff6464;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 15px;
        }

        .warning-message {
          background: rgba(255, 165, 0, 0.2);
          border: 1px solid #ffa500;
          color: #ffa500;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 15px;
        }

        .warning-message p {
          margin: 5px 0;
          font-size: 0.9rem;
        }

        .theme-stats {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid rgba(124, 184, 160, 0.3);
        }

        .theme-stats h4 {
          color: #7cb8a0;
          margin-bottom: 15px;
        }

        .theme-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 10px;
        }

        .theme-stat {
          background: rgba(124, 184, 160, 0.1);
          padding: 10px;
          border-radius: 6px;
        }

        .theme-name {
          font-size: 0.85rem;
          color: #7cb8a0;
          margin-bottom: 5px;
          text-transform: capitalize;
        }

        .theme-count {
          font-size: 0.9rem;
          margin-bottom: 5px;
        }

        .mini-progress-bar {
          height: 4px;
          background: rgba(124, 184, 160, 0.2);
          border-radius: 2px;
          overflow: hidden;
        }

        .mini-progress-fill {
          height: 100%;
          transition: width 0.3s ease;
        }

        .info-text {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid rgba(124, 184, 160, 0.3);
          font-size: 0.85rem;
          color: #aaa;
        }

        .info-text p {
          margin: 8px 0;
        }

        .info-text strong {
          color: #7cb8a0;
        }
      `}</style>
    </div>
  );
}
