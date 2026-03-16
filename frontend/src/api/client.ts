const API_BASE = import.meta.env.PROD
  ? "https://soooth-backend.onrender.com/api"
  : "http://localhost:8000/api";

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

export async function startGeneration(
  theme: string,
  duration: number = 60,
  videoSource: string = "ai",
  uploadYoutube: boolean = false
): Promise<Job> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, duration, video_source: videoSource, upload_youtube: uploadYoutube }),
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
