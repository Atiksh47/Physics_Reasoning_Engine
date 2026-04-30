import { useState } from "react";
import {
  simulateText,
  simulateJson,
  whatIf,
} from "./api/client";
import type { Scene, SimulationResponse } from "./api/client";
import SceneInput from "./components/SceneInput";
import SimulationViewer from "./components/SimulationViewer";
import ExplanationPanel from "./components/ExplanationPanel";
import WhatIfPanel from "./components/WhatIfPanel";
import "./App.css";

type Mode = "idle" | "single" | "comparison";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [primary, setPrimary] = useState<SimulationResponse | null>(null);
  const [modified, setModified] = useState<SimulationResponse | null>(null);
  const [mode, setMode] = useState<Mode>("idle");

  async function handleSimulate(description: string) {
    setLoading(true);
    setError(null);
    setModified(null);
    try {
      const res = await simulateText(description);
      setPrimary(res);
      setMode("single");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadScene(scene: Scene) {
    setLoading(true);
    setError(null);
    setModified(null);
    try {
      const res = await simulateJson(scene);
      setPrimary(res);
      setMode("single");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleWhatIf(changes: Record<string, unknown>) {
    if (!primary) return;
    setLoading(true);
    setError(null);
    try {
      const res = await whatIf(primary.scene, changes);
      setModified(res);
      setMode("comparison");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Physics Reasoning Engine</h1>
        <p className="app-subtitle">Natural language → simulation → explanation</p>
      </header>

      <main className="app-main">
        <aside className="left-col">
          <SceneInput
            onSimulate={handleSimulate}
            onLoadScene={handleLoadScene}
            loading={loading}
          />
          {primary && (
            <div className="section-divider"><span>What If</span></div>
          )}
          {primary && (
            <WhatIfPanel
              scene={primary.scene}
              onRerun={handleWhatIf}
              loading={loading}
            />
          )}
        </aside>

        <section className="right-col">
          {loading && (
            <div className="loading-overlay">
              <span className="loading-spinner" />
              <span className="loading-label">Running simulation…</span>
            </div>
          )}

          {error && (
            <div className="error-banner">
              <strong>Error:</strong> {error}
            </div>
          )}

          {!loading && !primary && !error && (
            <div className="empty-state">
              <div className="empty-reticle" />
              <p>describe a scene to initialise the simulation</p>
            </div>
          )}

          {primary && !loading && (
            <>
              {mode === "comparison" && modified ? (
                <div className="comparison-grid">
                  <div className="comparison-col">
                    <h4 className="comparison-label">Original</h4>
                    <SimulationViewer scene={primary.scene} result={primary.result} />
                    <ExplanationPanel explanation={primary.explanation} result={primary.result} />
                  </div>
                  <div className="comparison-col">
                    <h4 className="comparison-label">Modified</h4>
                    <SimulationViewer scene={modified.scene} result={modified.result} />
                    <ExplanationPanel explanation={modified.explanation} result={modified.result} />
                  </div>
                </div>
              ) : (
                <>
                  <SimulationViewer scene={primary.scene} result={primary.result} />
                  <ExplanationPanel explanation={primary.explanation} result={primary.result} />
                </>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}
