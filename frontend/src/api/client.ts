const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : import.meta.env.PROD
  ? "https://soooth-backend.onrender.com/api"
  : "http://localhost:8001/api";

export interface Job {
  id: string;
  status: string;
  theme: string;
  duration: number;
  youtube_id: string | null;
  error: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface BatchJobResponse {
  jobs: Job[];
  batch_count: number;
}

export async function startGeneration(
  theme: string,
  duration: number = 60,
  videoSource: string = "ai",
  uploadYoutube: boolean = false,
  noAudio: boolean = false,
  customVideoPrompt?: string,
  customMusicPrompt?: string,
  batchCount: number = 1,
  customAudio?: File
): Promise<BatchJobResponse> {
  const formData = new FormData();
  formData.append("theme", theme);
  formData.append("duration", duration.toString());
  formData.append("video_source", videoSource);
  formData.append("upload_youtube", uploadYoutube.toString());
  formData.append("no_audio", noAudio.toString());
  formData.append("batch_count", batchCount.toString());

  if (customVideoPrompt) formData.append("custom_video_prompt", customVideoPrompt);
  if (customMusicPrompt) formData.append("custom_music_prompt", customMusicPrompt);
  if (customAudio) formData.append("custom_audio", customAudio);

  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Generation failed: ${res.statusText}`);
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.statusText}`);
  return res.json();
}

export async function listJobs(): Promise<Job[]> {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) throw new Error(`Failed to list jobs: ${res.statusText}`);
  const data = await res.json();
  return data.jobs;
}

export async function cancelJob(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to cancel: ${res.statusText}`);
}

export function getVideoUrl(jobId: string): string {
  return `${API_BASE}/videos/${jobId}`;
}
