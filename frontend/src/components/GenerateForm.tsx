import { useState } from "react";

const THEMES = [
  { id: "forest", label: "Forest", emoji: "🌲", desc: "Misty forest at sunrise", stock: true },
  { id: "ocean", label: "Ocean", emoji: "🌊", desc: "Calm waves on white sand", stock: true },
  { id: "rain", label: "Rain", emoji: "🌧️", desc: "Gentle rain on green leaves", stock: true },
  { id: "mountain", label: "Mountain", emoji: "🏔️", desc: "Snow-capped peaks above clouds", stock: true },
  { id: "meadow", label: "Meadow", emoji: "🌻", desc: "Wildflowers swaying in breeze", stock: true },
  { id: "starry_night", label: "Starry Night", emoji: "✨", desc: "Milky Way over mountains", stock: true },
  { id: "study_babe", label: "Study Babe", emoji: "📚", desc: "Glamorous study in dreamy world", stock: false },
];

const DURATIONS = [
  { value: 60, label: "1 min" },
  { value: 300, label: "5 min" },
  { value: 600, label: "10 min" },
  { value: 0, label: "Custom" },
];

interface Props {
  onGenerate: (theme: string, duration: number, videoSource: string, uploadYoutube: boolean) => void;
  disabled: boolean;
}

export function GenerateForm({ onGenerate, disabled }: Props) {
  const [selected, setSelected] = useState("forest");
  const [videoSource, setVideoSource] = useState<"ai" | "stock">("stock");
  const [durationOption, setDurationOption] = useState(60);
  const [customDuration, setCustomDuration] = useState(120);
  const [uploadYoutube, setUploadYoutube] = useState(false);

  const selectedTheme = THEMES.find((t) => t.id === selected);
  const stockAvailable = selectedTheme?.stock ?? false;
  const finalDuration = durationOption === 0 ? customDuration : durationOption;

  return (
    <div className="generate-form">
      <h2>Choose a theme</h2>
      <div className="theme-grid">
        {THEMES.map((theme) => (
          <button
            key={theme.id}
            className={`theme-card ${selected === theme.id ? "selected" : ""}`}
            onClick={() => {
              setSelected(theme.id);
              if (!theme.stock && videoSource === "stock") {
                setVideoSource("ai");
              }
            }}
            disabled={disabled}
          >
            <span className="theme-emoji">{theme.emoji}</span>
            <span className="theme-label">{theme.label}</span>
            <span className="theme-desc">{theme.desc}</span>
          </button>
        ))}
      </div>

      {/* Video source toggle */}
      <div className="source-toggle">
        <span className="source-label">Video source:</span>
        <button
          className={`source-btn ${videoSource === "ai" ? "active" : ""}`}
          onClick={() => setVideoSource("ai")}
          disabled={disabled}
        >
          AI Generated
        </button>
        <button
          className={`source-btn ${videoSource === "stock" ? "active" : ""}`}
          onClick={() => setVideoSource("stock")}
          disabled={disabled || !stockAvailable}
          title={!stockAvailable ? "Stock not available for this theme" : ""}
        >
          Stock Footage
        </button>
        <span className="source-hint">
          {videoSource === "ai"
            ? "Kling Pro AI — unique but takes 3-5 min"
            : "Pixabay HD — instant, real footage, free"}
        </span>
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
        onClick={() => onGenerate(selected, finalDuration, videoSource, uploadYoutube)}
        disabled={disabled}
      >
        {disabled ? "Generating..." : `Generate ${finalDuration >= 60 ? `${Math.floor(finalDuration / 60)}m${finalDuration % 60 ? ` ${finalDuration % 60}s` : ""}` : `${finalDuration}s`} Soothing Video`}
      </button>
    </div>
  );
}
