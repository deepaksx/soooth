import uuid
import subprocess
import shutil
from pathlib import Path
from app.config import settings

# Find FFmpeg binaries
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def get_duration(file_path: Path) -> float:
    """Get duration of a media file in seconds."""
    probe_cmd = [
        FFPROBE, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 5.0


def concat_clips_with_crossfade(clip_paths: list[Path], target_duration: int = 60, slowdown: float = 2.0) -> Path:
    """Concatenate video clips with crossfade transitions and slow-motion.

    slowdown: factor to slow clips by (2.0 = half speed, doubling duration)
    """
    output_path = settings.media_dir / "videos" / f"concat_{uuid.uuid4()}.mp4"

    if len(clip_paths) == 1:
        return clip_paths[0]

    # Get durations after slowdown
    durations = [get_duration(p) * slowdown for p in clip_paths]
    fade_duration = 1.0  # 1 second crossfade (longer for smoother soothing feel)

    # Build input list
    inputs = []
    for p in clip_paths:
        inputs.extend(["-i", str(p)])

    # Build filter: first slow down each clip, then xfade between them
    filter_parts = []
    num_clips = len(clip_paths)

    # Step 1: Normalize all clips to same resolution/fps, optionally slow down
    for i in range(num_clips):
        base_filter = f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30"
        if slowdown > 1.0:
            base_filter += f",setpts={slowdown}*PTS"
        filter_parts.append(f"{base_filter}[slow{i}]")

    # Step 2: Chain xfade transitions between slowed clips
    if num_clips == 2:
        offset = durations[0] - fade_duration
        filter_parts.append(f"[slow0][slow1]xfade=transition=fade:duration={fade_duration}:offset={offset}[outv]")
    else:
        offset = durations[0] - fade_duration
        filter_parts.append(f"[slow0][slow1]xfade=transition=fade:duration={fade_duration}:offset={offset}[v1]")
        cumulative = durations[0] + durations[1] - fade_duration

        for i in range(2, num_clips):
            prev_label = f"v{i-1}"
            offset = cumulative - fade_duration
            if i == num_clips - 1:
                filter_parts.append(f"[{prev_label}][slow{i}]xfade=transition=fade:duration={fade_duration}:offset={offset}[outv]")
            else:
                next_label = f"v{i}"
                filter_parts.append(f"[{prev_label}][slow{i}]xfade=transition=fade:duration={fade_duration}:offset={offset}[{next_label}]")
            cumulative += durations[i] - fade_duration

    filter_complex = ";".join(filter_parts)

    cmd = [FFMPEG, "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        "-movflags", "+faststart",
        str(output_path),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {proc.stderr[:500]}")

    return output_path


def merge_audio_video(video_path: Path, audio_path: Path, duration: int = 60) -> Path:
    """Merge video and audio into a single MP4 with exact duration."""
    output_path = settings.media_dir / "output" / f"{uuid.uuid4()}.mp4"

    video_duration = get_duration(video_path)

    cmd = [FFMPEG, "-y"]

    # Loop video if shorter than target duration
    if video_duration < duration:
        loop_count = int(duration / video_duration) + 1
        cmd.extend(["-stream_loop", str(loop_count)])

    cmd.extend([
        "-i", str(video_path),
        "-i", str(audio_path),
        "-t", str(duration),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        str(output_path),
    ])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg merge failed: {proc.stderr[:500]}")

    return output_path
