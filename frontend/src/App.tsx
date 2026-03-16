import { useState } from "react";
import { GenerateForm } from "./components/GenerateForm";
import { ProgressTracker } from "./components/ProgressTracker";
import { VideoPlayer } from "./components/VideoPlayer";
import { Library } from "./components/Library";
import { useGeneration } from "./hooks/useGeneration";
import "./App.css";

function App() {
  const { job, loading, error, generate, cancel } = useGeneration();
  const isComplete = job?.status === "complete";
  const [showLibrary, setShowLibrary] = useState(false);

  return (
    <div className="app">
      <header className="header">
        <h1 className="logo">Soooth</h1>
        <p className="tagline">AI-generated soothing nature videos with synchronized music</p>
        <div style={{ marginTop: "1rem" }}>
          <button
            onClick={() => setShowLibrary(!showLibrary)}
            style={{
              padding: "0.5rem 1rem",
              background: showLibrary ? "#7cb8a0" : "#1a2a25",
              border: "1px solid #7cb8a0",
              borderRadius: "6px",
              color: showLibrary ? "#0a0a0f" : "#7cb8a0",
              cursor: "pointer",
              fontSize: "0.85rem"
            }}
          >
            {showLibrary ? "📝 Generate" : "📚 Library"}
          </button>
        </div>
      </header>

      <main className="main">
        {!showLibrary ? (
          <>
            <GenerateForm onGenerate={(theme, dur, src, yt, noAudio, videoPrompt, musicPrompt, batchCount, customAudio) => generate(theme, dur, src, yt, noAudio, videoPrompt, musicPrompt, batchCount, customAudio)} disabled={loading} />

            {job && !isComplete && <ProgressTracker job={job} onCancel={cancel} />}

            {error && !job?.error && <p className="error">{error}</p>}

            {isComplete && job && (
              <VideoPlayer jobId={job.id} theme={job.theme} youtubeId={job.youtube_id} />
            )}
          </>
        ) : (
          <Library />
        )}
      </main>

      <footer className="footer">
        <p>Powered by fal.ai</p>
      </footer>
    </div>
  );
}

export default App;
