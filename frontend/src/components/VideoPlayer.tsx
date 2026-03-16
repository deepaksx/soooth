import { getVideoUrl } from "../api/client";

interface Props {
  jobId: string;
  theme: string;
  youtubeId?: string | null;
}

export function VideoPlayer({ jobId, theme, youtubeId }: Props) {
  const videoUrl = getVideoUrl(jobId);

  return (
    <div className="video-player">
      <video controls autoPlay loop width="100%">
        <source src={videoUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      <div className="video-actions">
        <a href={videoUrl} download={`soooth-${theme}.mp4`} className="download-btn">
          Download Video
        </a>
        {youtubeId && (
          <a
            href={`https://www.youtube.com/watch?v=${youtubeId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="youtube-btn"
          >
            View on YouTube
          </a>
        )}
      </div>
    </div>
  );
}
