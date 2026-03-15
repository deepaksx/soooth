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

interface Props {
  onGenerate: (theme: string, duration: number, videoSource: string) => void;
  disabled: boolean;
}

export function GenerateForm({ onGenerate, disabled }: Props) {
  const [selected, setSelected] = useState("forest");
  const [videoSource, setVideoSource] = useState<"ai" | "stock">("ai");

  const selectedTheme = THEMES.find((t) => t.id === selected);
  const stockAvailable = selectedTheme?.stock ?? false;

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

      <button
        className="generate-btn"
        onClick={() => onGenerate(selected, 60, videoSource)}
        disabled={disabled}
      >
        {disabled ? "Generating..." : "Generate Soothing Video"}
      </button>
    </div>
  );
}
