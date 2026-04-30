import { useState } from "react";
import type { Scene } from "../api/client";

interface Props {
  scene: Scene;
  onRerun: (changes: Record<string, unknown>) => void;
  loading: boolean;
}

interface ObjectParam {
  objectName: string;
  param: string;
  value: string;
}

const OBJECT_PARAMS: Record<string, string[]> = {
  ball: ["mass", "radius", "elasticity", "friction"],
  block: ["mass", "elasticity", "friction"],
  slope: ["friction", "elasticity"],
  ramp: ["friction", "elasticity"],
};

function paramLabel(p: string): string {
  return p.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function WhatIfPanel({ scene, onRerun, loading }: Props) {
  const [topLevel, setTopLevel] = useState<Record<string, string>>({
    gravity_y: String(scene.gravity[1]),
    duration: String(scene.duration),
    damping: String(scene.damping ?? 0.99),
  });

  const [objParams, setObjParams] = useState<ObjectParam[]>(() => {
    return scene.objects
      .filter((o) => OBJECT_PARAMS[o.type])
      .flatMap((o) =>
        (OBJECT_PARAMS[o.type] ?? []).map((param) => ({
          objectName: o.name,
          param,
          value: String((o as unknown as Record<string, unknown>)[param] ?? ""),
        }))
      );
  });

  function setObjParam(objectName: string, param: string, value: string) {
    setObjParams((prev) =>
      prev.map((p) =>
        p.objectName === objectName && p.param === param ? { ...p, value } : p
      )
    );
  }

  function buildChanges(): Record<string, unknown> {
    const changes: Record<string, unknown> = {};

    const gy = parseFloat(topLevel.gravity_y);
    if (!isNaN(gy)) changes.gravity = [scene.gravity[0], gy];

    const dur = parseFloat(topLevel.duration);
    if (!isNaN(dur)) changes.duration = dur;

    const damp = parseFloat(topLevel.damping);
    if (!isNaN(damp)) changes.damping = damp;

    // Group object param changes by name
    const byObject: Record<string, Record<string, number>> = {};
    for (const { objectName, param, value } of objParams) {
      const num = parseFloat(value);
      if (!isNaN(num)) {
        byObject[objectName] = byObject[objectName] ?? {};
        byObject[objectName][param] = num;
      }
    }
    for (const [name, vals] of Object.entries(byObject)) {
      changes[name] = vals;
    }

    return changes;
  }

  // Group objects for display
  const dynamicObjs = scene.objects.filter((o) => OBJECT_PARAMS[o.type]);

  return (
    <div className="whatif-panel">
      <h3 className="panel-title">What If?</h3>
      <p className="panel-hint">Adjust parameters and re-run to compare results.</p>

      <div className="whatif-section">
        <span className="section-label">Scene</span>
        <div className="param-grid">
          <label>
            Gravity Y
            <input
              type="number"
              step="0.1"
              value={topLevel.gravity_y}
              onChange={(e) =>
                setTopLevel((prev) => ({ ...prev, gravity_y: e.target.value }))
              }
              disabled={loading}
            />
          </label>
          <label>
            Duration (s)
            <input
              type="number"
              step="0.5"
              min="1"
              value={topLevel.duration}
              onChange={(e) =>
                setTopLevel((prev) => ({ ...prev, duration: e.target.value }))
              }
              disabled={loading}
            />
          </label>
          <label>
            Damping
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={topLevel.damping}
              onChange={(e) =>
                setTopLevel((prev) => ({ ...prev, damping: e.target.value }))
              }
              disabled={loading}
            />
          </label>
        </div>
      </div>

      {dynamicObjs.map((obj) => (
        <div key={obj.name} className="whatif-section">
          <span className="section-label">
            {obj.name} <span className="obj-type">({obj.type})</span>
          </span>
          <div className="param-grid">
            {(OBJECT_PARAMS[obj.type] ?? []).map((param) => {
              const entry = objParams.find(
                (p) => p.objectName === obj.name && p.param === param
              );
              return (
                <label key={param}>
                  {paramLabel(param)}
                  <input
                    type="number"
                    step="0.1"
                    value={entry?.value ?? ""}
                    onChange={(e) =>
                      setObjParam(obj.name, param, e.target.value)
                    }
                    disabled={loading}
                  />
                </label>
              );
            })}
          </div>
        </div>
      ))}

      <button
        className="btn btn-primary"
        onClick={() => onRerun(buildChanges())}
        disabled={loading}
      >
        {loading ? "Simulating…" : "Re-run →"}
      </button>
    </div>
  );
}
