import { useState } from "react";
import type { Job } from "../api/client";

const STEPS = [
  { key: "pending", label: "Preparing job" },
  { key: "generating", label: "Downloading clips + composing music" },
  { key: "merging", label: "Crossfading & merging" },
  { key: "uploading", label: "Uploading to YouTube" },
  { key: "complete", label: "Done!" },
];

const STATUS_DETAIL: Record<string, string> = {
  pending: "Setting up generation pipeline...",
  generating:
    "Downloading video clips and composing music (ElevenLabs) in parallel.",
  merging:
    "Normalizing clips, applying crossfade transitions, and mixing with audio.",
  uploading:
    "Uploading your video to YouTube...",
  complete: "Your soothing video is ready!",
  failed: "Something went wrong.",
};

function getStepIndex(status: string): number {
  if (status === "failed") return -1;
  const idx = STEPS.findIndex((s) => s.key === status);
  return idx >= 0 ? idx : 0;
}

interface Props {
  job: Job;
  onCancel: () => void;
}

export function ProgressTracker({ job, onCancel }: Props) {
  const [confirming, setConfirming] = useState(false);
  const currentIdx = getStepIndex(job.status);
  const progress =
    job.status === "complete"
      ? 100
      : job.status === "failed"
        ? 0
        : Math.round(((currentIdx + 0.5) / STEPS.length) * 100);

  const isActive = job.status !== "complete" && job.status !== "failed";

  const handleStop = () => {
    if (confirming) {
      onCancel();
      setConfirming(false);
    } else {
      setConfirming(true);
    }
  };

  return (
    <div className="progress-tracker">
      {/* Step indicators */}
      <div className="steps">
        {STEPS.map((step, i) => {
          const isDone = currentIdx > i;
          const isStepActive = currentIdx === i;
          return (
            <div
              key={step.key}
              className={`step ${isDone ? "done" : ""} ${isStepActive ? "active" : ""}`}
            >
              <div className="step-dot">
                {isDone ? "\u2713" : i + 1}
              </div>
              <span className="step-label">{step.label}</span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="progress-bar-container">
        <div className="progress-bar" style={{ width: `${progress}%` }} />
      </div>

      {/* Detail text */}
      <p className="progress-detail">
        {STATUS_DETAIL[job.status] ?? job.status}
      </p>

      {/* Stop button */}
      {isActive && (
        <div className="cancel-section">
          {confirming ? (
            <div className="cancel-confirm">
              <span className="cancel-msg">Are you sure you want to stop?</span>
              <button className="cancel-btn confirm" onClick={handleStop}>
                Yes, stop generation
              </button>
              <button className="cancel-btn dismiss" onClick={() => setConfirming(false)}>
                No, keep going
              </button>
            </div>
          ) : (
            <button className="cancel-btn" onClick={handleStop}>
              Stop Generation
            </button>
          )}
        </div>
      )}

      {job.status === "failed" && job.error && (
        <p className="progress-error">{job.error}</p>
      )}
    </div>
  );
}
