import { useState } from "react";
import { listScenes, getScene } from "../api/client";
import type { Scene } from "../api/client";

interface Props {
  onSimulate: (description: string) => void;
  onLoadScene: (scene: Scene) => void;
  loading: boolean;
}

const EXAMPLES = [
  "A heavy ball rolls down a steep ramp and hits a small block at the bottom.",
  "A light ball slowly slides down a gentle slope and barely nudges a heavy block.",
  "A ball drops straight down and bounces off the floor several times.",
];

export default function SceneInput({ onSimulate, onLoadScene, loading }: Props) {
  const [text, setText] = useState("");
  const [scenes, setScenes] = useState<string[]>([]);
  const [showExamples, setShowExamples] = useState(false);

  async function handleLoadSceneList() {
    const res = await listScenes();
    setScenes(res.scenes);
    setShowExamples(true);
  }

  async function handlePickScene(id: string) {
    const scene = await getScene(id);
    onLoadScene(scene);
    setShowExamples(false);
  }

  function handleExample(ex: string) {
    setText(ex);
    setShowExamples(false);
  }

  return (
    <div className="scene-input">
      <label className="input-label">Describe a physics scene</label>
      <textarea
        className="scene-textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. A ball rolls down a 30° ramp and hits a block at the bottom."
        rows={4}
        disabled={loading}
      />

      <div className="input-actions">
        <button
          className="btn btn-primary"
          onClick={() => onSimulate(text)}
          disabled={loading || text.trim() === ""}
        >
          {loading ? "Simulating…" : "Simulate →"}
        </button>

        <button
          className="btn btn-secondary"
          onClick={handleLoadSceneList}
          disabled={loading}
        >
          Load saved scene
        </button>
      </div>

      <div className="examples-row">
        <span className="examples-label">Try an example:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            className="btn btn-ghost"
            onClick={() => handleExample(ex)}
            disabled={loading}
          >
            {ex.slice(0, 40)}…
          </button>
        ))}
      </div>

      {showExamples && scenes.length > 0 && (
        <div className="scene-picker">
          <span className="examples-label">Saved scenes:</span>
          {scenes.map((id) => (
            <button
              key={id}
              className="btn btn-ghost"
              onClick={() => handlePickScene(id)}
            >
              {id}
            </button>
          ))}
          <button className="btn btn-ghost" onClick={() => setShowExamples(false)}>
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
