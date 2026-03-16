import { GenerateForm } from "./components/GenerateForm";
import { ProgressTracker } from "./components/ProgressTracker";
import { VideoPlayer } from "./components/VideoPlayer";
import { useGeneration } from "./hooks/useGeneration";
import "./App.css";

function App() {
  const { job, loading, error, generate, cancel } = useGeneration();
  const isComplete = job?.status === "complete";

  return (
    <div className="app">
      <header className="header">
        <h1 className="logo">Soooth</h1>
        <p className="tagline">AI-generated soothing nature videos with synchronized music</p>
      </header>

      <main className="main">
        <GenerateForm onGenerate={(theme, dur, src, yt) => generate(theme, dur, src, yt)} disabled={loading} />

        {job && !isComplete && <ProgressTracker job={job} onCancel={cancel} />}

        {error && !job?.error && <p className="error">{error}</p>}

        {isComplete && job && (
          <VideoPlayer jobId={job.id} theme={job.theme} youtubeId={job.youtube_id} />
        )}
      </main>

      <footer className="footer">
        <p>Powered by fal.ai & ElevenLabs</p>
      </footer>
    </div>
  );
}

export default App;
