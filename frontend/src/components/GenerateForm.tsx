import { useState, useRef } from "react";

const STOCK_THEMES = [
  { id: "forest", label: "Forest", emoji: "🌲", desc: "Misty forest at sunrise" },
  { id: "ocean", label: "Ocean", emoji: "🌊", desc: "Calm waves on white sand" },
  { id: "rain", label: "Rain", emoji: "🌧️", desc: "Gentle rain on green leaves" },
  { id: "mountain", label: "Mountain", emoji: "🏔️", desc: "Snow-capped peaks above clouds" },
  { id: "meadow", label: "Meadow", emoji: "🌻", desc: "Wildflowers in breeze" },
  { id: "starry_night", label: "Starry Night", emoji: "✨", desc: "Milky Way over peaks" },
  { id: "sunset", label: "Sunset", emoji: "🌅", desc: "Golden hour over horizon" },
  { id: "waterfall", label: "Waterfall", emoji: "💧", desc: "Cascading water in nature" },
  { id: "lake", label: "Lake", emoji: "🏞️", desc: "Still water reflections" },
  { id: "beach", label: "Beach", emoji: "🏖️", desc: "Sandy shores and waves" },
  { id: "clouds", label: "Clouds", emoji: "☁️", desc: "Fluffy clouds drifting by" },
  { id: "snow", label: "Snow", emoji: "❄️", desc: "Snowfall in winter scene" },
  { id: "desert", label: "Desert", emoji: "🏜️", desc: "Sand dunes at sunset" },
  { id: "aurora", label: "Aurora", emoji: "🌌", desc: "Northern lights display" },
  { id: "flowers", label: "Flowers", emoji: "🌸", desc: "Blooming flowers closeup" },
];

const DURATIONS = [
  { value: 60, label: "1 min" },
  { value: 300, label: "5 min" },
  { value: 600, label: "10 min" },
  { value: 0, label: "Custom" },
];

const BATCH_COUNTS = [
  { value: 1, label: "1 video" },
  { value: 3, label: "3 videos" },
  { value: 5, label: "5 videos" },
  { value: 10, label: "10 videos" },
];

interface Props {
  onGenerate: (theme: string, duration: number, videoSource: string, uploadYoutube: boolean, noAudio: boolean, customVideoPrompt?: string, customMusicPrompt?: string, batchCount?: number, customAudio?: File) => void;
  disabled: boolean;
}

export function GenerateForm({ onGenerate, disabled }: Props) {
  const [tab, setTab] = useState<"ai" | "stock">("stock");
  const [selectedThemes, setSelectedThemes] = useState<string[]>(["forest"]);
  const [audioMode, setAudioMode] = useState<"ai" | "custom">("ai");
  const [durationOption, setDurationOption] = useState(60);
  const [customDuration, setCustomDuration] = useState(120);
  const [uploadYoutube, setUploadYoutube] = useState(false);
  const [noAudio, setNoAudio] = useState(false);
  const [batchCount, setBatchCount] = useState(1);
  const [customAudio, setCustomAudio] = useState<File | null>(null);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const finalDuration =
    tab === "stock" && audioMode === "custom" && audioDuration
      ? Math.ceil(audioDuration)
      : durationOption === 0
      ? customDuration
      : durationOption;

  const handleAudioUpload = (file: File | null) => {
    setCustomAudio(file);
    if (file) {
      setNoAudio(false);
      // Detect audio duration
      const url = URL.createObjectURL(file);
      const audio = new Audio(url);
      audio.addEventListener('loadedmetadata', () => {
        setAudioDuration(audio.duration);
        URL.revokeObjectURL(url);
      });
    } else {
      setAudioDuration(null);
    }
  };

  const toggleTheme = (themeId: string) => {
    setSelectedThemes((prev) =>
      prev.includes(themeId)
        ? prev.filter((id) => id !== themeId)
        : [...prev, themeId]
    );
  };

  const theme = tab === "ai" ? "study_babe" : selectedThemes.join(",");
  const videoSource = tab === "ai" ? "ai" : "stock";

  return (
    <div className="generate-form">
      {/* Tab Selector */}
      <div className="source-toggle" style={{ marginBottom: "20px" }}>
        <span className="source-label">Mode:</span>
        <button
          className={`source-btn ${tab === "ai" ? "active" : ""}`}
          onClick={() => setTab("ai")}
          disabled={disabled}
        >
          AI-Based
        </button>
        <button
          className={`source-btn ${tab === "stock" ? "active" : ""}`}
          onClick={() => setTab("stock")}
          disabled={disabled}
        >
          Stock Footage
        </button>
        <span className="source-hint">
          {tab === "ai"
            ? "AI-generated videos with Study Babe theme"
            : "Real footage from Pixabay with nature themes"}
        </span>
      </div>

      {/* AI-Based Tab */}
      {tab === "ai" && (
        <>
          <h2>Study Babe Theme</h2>
          <div className="theme-grid">
            <div className="theme-card selected">
              <span className="theme-emoji">📚</span>
              <span className="theme-label">Study Babe</span>
              <span className="theme-desc">Glamorous study in dreamy world</span>
            </div>
          </div>

          {/* Duration selector */}
          <div className="duration-toggle">
            <span className="source-label">Duration:</span>
            {DURATIONS.map((d) => (
              <button
                key={d.value}
                className={`source-btn ${durationOption === d.value ? "active" : ""}`}
                onClick={() => setDurationOption(d.value)}
                disabled={disabled}
              >
                {d.label}
              </button>
            ))}
            {durationOption === 0 && (
              <div className="custom-duration">
                <input
                  type="number"
                  min={30}
                  max={1800}
                  value={customDuration}
                  onChange={(e) => setCustomDuration(Math.max(30, Number(e.target.value)))}
                  disabled={disabled}
                  className="custom-duration-input"
                />
                <span className="source-hint">seconds (30-1800)</span>
              </div>
            )}
          </div>

          {/* Batch count selector */}
          <div className="duration-toggle">
            <span className="source-label">Batch:</span>
            {BATCH_COUNTS.map((b) => (
              <button
                key={b.value}
                className={`source-btn ${batchCount === b.value ? "active" : ""}`}
                onClick={() => setBatchCount(b.value)}
                disabled={disabled}
              >
                {b.label}
              </button>
            ))}
            <span className="source-hint">
              Each video will have unique style & appearance ✨
            </span>
          </div>
        </>
      )}

      {/* Stock Footage Tab */}
      {tab === "stock" && (
        <>
          <h2>Choose themes (multi-select)</h2>
          <div className="theme-grid-multi">
            {STOCK_THEMES.map((theme) => (
              <button
                key={theme.id}
                className={`theme-card-small ${selectedThemes.includes(theme.id) ? "selected" : ""}`}
                onClick={() => toggleTheme(theme.id)}
                disabled={disabled}
              >
                <span className="theme-emoji-small">{theme.emoji}</span>
                <span className="theme-label-small">{theme.label}</span>
              </button>
            ))}
          </div>
          <div className="source-hint" style={{ marginTop: "10px" }}>
            {selectedThemes.length === 0
              ? "⚠️ Select at least one theme"
              : selectedThemes.length === 1
              ? `✓ ${selectedThemes.length} theme selected`
              : `✓ ${selectedThemes.length} themes selected - videos will be randomly mixed`}
          </div>

          {/* Audio Mode Selector */}
          <div className="source-toggle">
            <span className="source-label">Audio:</span>
            <button
              className={`source-btn ${audioMode === "ai" ? "active" : ""}`}
              onClick={() => setAudioMode("ai")}
              disabled={disabled}
            >
              AI Generated
            </button>
            <button
              className={`source-btn ${audioMode === "custom" ? "active" : ""}`}
              onClick={() => setAudioMode("custom")}
              disabled={disabled}
            >
              Upload Audio
            </button>
            <span className="source-hint">
              {audioMode === "ai"
                ? "AI music matched to duration"
                : "Use your own audio file"}
            </span>
          </div>

          {/* AI Audio Mode - Show Duration Selector */}
          {audioMode === "ai" && (
            <div className="duration-toggle">
              <span className="source-label">Duration:</span>
              {DURATIONS.map((d) => (
                <button
                  key={d.value}
                  className={`source-btn ${durationOption === d.value ? "active" : ""}`}
                  onClick={() => setDurationOption(d.value)}
                  disabled={disabled}
                >
                  {d.label}
                </button>
              ))}
              {durationOption === 0 && (
                <div className="custom-duration">
                  <input
                    type="number"
                    min={30}
                    max={1800}
                    value={customDuration}
                    onChange={(e) => setCustomDuration(Math.max(30, Number(e.target.value)))}
                    disabled={disabled}
                    className="custom-duration-input"
                  />
                  <span className="source-hint">seconds (30-1800)</span>
                </div>
              )}
            </div>
          )}

          {/* Custom Audio Mode - Show Upload */}
          {audioMode === "custom" && (
            <div className="youtube-toggle">
              <label className="toggle-label">
                <span className="toggle-text">Upload Audio File:</span>
                <input
                  type="file"
                  accept="audio/*,.mp3,.wav,.m4a,.aac"
                  onChange={(e) => handleAudioUpload(e.target.files?.[0] || null)}
                  disabled={disabled}
                  style={{ marginLeft: "10px" }}
                />
                {customAudio && (
                  <button
                    onClick={() => handleAudioUpload(null)}
                    disabled={disabled}
                    style={{ marginLeft: "10px", padding: "2px 8px", fontSize: "12px" }}
                  >
                    Clear
                  </button>
                )}
              </label>
              {customAudio && (
                <span className="source-hint">
                  {customAudio.name} ({(customAudio.size / 1024 / 1024).toFixed(2)} MB)
                  {audioDuration && ` - Duration: ${Math.floor(audioDuration / 60)}m ${Math.floor(audioDuration % 60)}s`}
                </span>
              )}
            </div>
          )}
        </>
      )}

      {/* No Audio toggle - only in AI mode */}
      {audioMode === "ai" && (
        <div className="youtube-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={noAudio}
              onChange={(e) => setNoAudio(e.target.checked)}
              disabled={disabled}
            />
            <span className="toggle-text">No Audio (Silent Video)</span>
          </label>
        </div>
      )}

      {/* YouTube upload toggle */}
      <div className="youtube-toggle">
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={uploadYoutube}
            onChange={(e) => setUploadYoutube(e.target.checked)}
            disabled={disabled}
          />
          <span className="toggle-text">Auto-upload to YouTube</span>
        </label>
      </div>

      <button
        className="generate-btn"
        onClick={() => onGenerate(
          theme,
          finalDuration,
          videoSource,
          uploadYoutube,
          noAudio,
          undefined,
          undefined,
          tab === "ai" ? batchCount : 1,
          audioMode === "custom" ? customAudio || undefined : undefined
        )}
        disabled={disabled || (audioMode === "custom" && !customAudio) || (tab === "stock" && selectedThemes.length === 0)}
      >
        {disabled
          ? "Generating..."
          : audioMode === "custom" && !customAudio
          ? "Upload audio to continue"
          : tab === "stock" && selectedThemes.length === 0
          ? "Select at least one theme"
          : `Generate ${tab === "ai" && batchCount > 1 ? `${batchCount} × ` : ""}${finalDuration >= 60 ? `${Math.floor(finalDuration / 60)}m${finalDuration % 60 ? ` ${finalDuration % 60}s` : ""}` : `${finalDuration}s`} ${tab === "ai" && batchCount > 1 ? "Videos" : "Video"}`}
      </button>
    </div>
  );
}
