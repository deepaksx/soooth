import { useState, useRef, useCallback, useEffect } from "react";
import type { Job } from "../api/client";
import { startGeneration, getJobStatus, listJobs, cancelJob } from "../api/client";

export function useGeneration() {
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (jobId: string) => {
      stopPolling();
      setLoading(true);
      intervalRef.current = window.setInterval(async () => {
        try {
          const updated = await getJobStatus(jobId);
          setJob(updated);

          if (updated.status === "complete" || updated.status === "failed") {
            stopPolling();
            setLoading(false);
            localStorage.removeItem("soooth_job_id");
            if (updated.status === "failed") {
              setError(updated.error || "Generation failed");
            }
          }
        } catch (err) {
          setError(String(err));
          stopPolling();
          setLoading(false);
        }
      }, 3000);
    },
    [stopPolling]
  );

  // On mount, restore from localStorage OR find active job from backend
  useEffect(() => {
    const savedJobId = localStorage.getItem("soooth_job_id");
    if (savedJobId) {
      getJobStatus(savedJobId)
        .then((savedJob) => {
          setJob(savedJob);
          if (savedJob.status !== "complete" && savedJob.status !== "failed") {
            startPolling(savedJob.id);
          }
        })
        .catch(() => {
          localStorage.removeItem("soooth_job_id");
        });
    } else {
      // No saved job — check if there's an active job on the backend
      listJobs().then((jobs) => {
        const active = jobs.find(
          (j) => j.status !== "complete" && j.status !== "failed"
        );
        if (active) {
          setJob(active);
          localStorage.setItem("soooth_job_id", active.id);
          startPolling(active.id);
        }
      }).catch(() => {});
    }
  }, [startPolling]);

  const generate = useCallback(
    async (theme: string, duration: number = 60, videoSource: string = "ai", uploadYoutube: boolean = false, noAudio: boolean = false, customVideoPrompt?: string, customMusicPrompt?: string, batchCount: number = 1, customAudio?: File) => {
      setLoading(true);
      setError(null);
      stopPolling();

      try {
        const batchResponse = await startGeneration(theme, duration, videoSource, uploadYoutube, noAudio, customVideoPrompt, customMusicPrompt, batchCount, customAudio);

        // For now, track the first job (we can enhance this later to show all jobs)
        const firstJob = batchResponse.jobs[0];
        setJob(firstJob);
        localStorage.setItem("soooth_job_id", firstJob.id);
        startPolling(firstJob.id);

        // Store all job IDs for batch tracking
        if (batchResponse.batch_count > 1) {
          const jobIds = batchResponse.jobs.map(j => j.id);
          localStorage.setItem("soooth_batch_ids", JSON.stringify(jobIds));
        }
      } catch (err) {
        setError(String(err));
        setLoading(false);
      }
    },
    [stopPolling, startPolling]
  );

  const cancel = useCallback(async () => {
    if (!job) return;
    try {
      await cancelJob(job.id);
      stopPolling();
      setJob((prev) => prev ? { ...prev, status: "failed", error: "Cancelled by user" } : null);
      setLoading(false);
      localStorage.removeItem("soooth_job_id");
    } catch (err) {
      setError(String(err));
    }
  }, [job, stopPolling]);

  return { job, loading, error, generate, cancel };
}
