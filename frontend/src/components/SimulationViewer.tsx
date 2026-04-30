import { useEffect, useRef, useState, useCallback } from "react";
import type { Scene, SimulationResult } from "../api/client";

interface Props {
  scene: Scene;
  result: SimulationResult;
}

// Palette matching the Python renderer
const BG            = "#0f0f14";
const STATIC_CLR    = "#646e78";
const BALL_CLR      = "#50a0ff";
const BLOCK_CLR     = "#ffa03c";
const TRAIL_CLR     = "#50a0ff";
const COLLISION_CLR = "#ff5050";
const HUD_BG        = "#191919";
const HUD_TEXT      = "#c8d2dc";
const FLASH_DURATION = 0.4;
const HUD_H = 60;
const WORLD_W = 20;

function worldToScreen(
  wx: number, wy: number,
  scale: number, viewportH: number
): [number, number] {
  return [wx * scale, viewportH - wy * scale];
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

export default function SimulationViewer({ scene, result }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef   = useRef<number>(0);
  const stateRef  = useRef({ frame: 0, paused: false, speed: 1.0, accum: 0 });

  const [paused, setPaused]     = useState(false);
  const [speed, setSpeed]       = useState(1.0);
  const [simTime, setSimTime]   = useState(0);

  const trajectories = result.trajectories;
  const collisions   = result.collisions;
  const duration     = result.duration;
  const objects      = Object.fromEntries(scene.objects.map((o) => [o.name, o]));

  const totalFrames = Math.max(
    ...Object.values(trajectories).map((t) => t.length), 1
  );

  // Build collision flash lookup: object name → latest collision time
  const collisionTimes: Record<string, number> = {};
  for (const c of collisions) {
    for (const name of c.objects) {
      collisionTimes[name] = Math.max(collisionTimes[name] ?? 0, c.time);
    }
  }

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const viewportH = H - HUD_H;
    const scale = W / WORLD_W;

    const { frame } = stateRef.current;
    const t = totalFrames > 1 ? (frame / (totalFrames - 1)) * duration : 0;

    setSimTime(t);

    // Flash ages
    const flashAges: Record<string, number> = {};
    for (const [name, ct] of Object.entries(collisionTimes)) {
      if (t >= ct) {
        const age = t - ct;
        if (age < FLASH_DURATION) flashAges[name] = age;
      }
    }

    // Background
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, W, H);

    // Static objects
    for (const obj of scene.objects) {
      if (obj.type === "slope" || obj.type === "ramp" || obj.type === "wall") {
        if (!obj.start || !obj.end) continue;
        const [sx, sy] = worldToScreen(obj.start[0], obj.start[1], scale, viewportH);
        const [ex, ey] = worldToScreen(obj.end[0], obj.end[1], scale, viewportH);
        ctx.strokeStyle = STATIC_CLR;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(ex, ey);
        ctx.stroke();
      }
    }

    // Dynamic objects
    for (const [name, traj] of Object.entries(trajectories)) {
      const idx = Math.min(frame, traj.length - 1);
      const [wx, wy] = traj[idx];
      const obj = objects[name];
      if (!obj) continue;
      const flash = name in flashAges;

      if (obj.type === "ball") {
        // Trail
        const trailLen = 30;
        const startIdx = Math.max(0, frame - trailLen);
        const pts = traj.slice(startIdx, frame + 1);
        for (let i = 0; i < pts.length; i++) {
          const alpha = Math.pow(i / Math.max(pts.length, 1), 1.5) * 0.7;
          const [tx, ty] = worldToScreen(pts[i][0], pts[i][1], scale, viewportH);
          const r = Math.max(1, 0.06 * scale);
          ctx.beginPath();
          ctx.arc(tx, ty, r, 0, Math.PI * 2);
          ctx.fillStyle = hexToRgba(TRAIL_CLR, alpha);
          ctx.fill();
        }

        // Ball
        const radius = Math.max(2, (obj.radius ?? 0.5) * scale);
        const [bx, by] = worldToScreen(wx, wy, scale, viewportH);
        ctx.beginPath();
        ctx.arc(bx, by, radius, 0, Math.PI * 2);
        ctx.fillStyle = flash ? COLLISION_CLR : BALL_CLR;
        ctx.fill();
        ctx.strokeStyle = "white";
        ctx.lineWidth = 1;
        ctx.stroke();

      } else if (obj.type === "block") {
        const [bw, bh] = (obj.size ?? [1, 1]).map((v) => v * scale);
        const [bx, by] = worldToScreen(wx, wy, scale, viewportH);
        ctx.fillStyle = flash ? COLLISION_CLR : BLOCK_CLR;
        ctx.fillRect(bx - bw / 2, by - bh / 2, bw, bh);
        ctx.strokeStyle = "white";
        ctx.lineWidth = 1;
        ctx.strokeRect(bx - bw / 2, by - bh / 2, bw, bh);
      }
    }

    // HUD
    ctx.fillStyle = HUD_BG;
    ctx.fillRect(0, viewportH, W, HUD_H);
    ctx.strokeStyle = STATIC_CLR;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, viewportH);
    ctx.lineTo(W, viewportH);
    ctx.stroke();

    ctx.fillStyle = HUD_TEXT;
    ctx.font = "14px monospace";
    ctx.fillText(`t = ${t.toFixed(2)}s / ${duration.toFixed(1)}s`, 12, viewportH + 18);

    // Progress bar
    const barX = 12, barY = viewportH + 34, barW = 200;
    const progress = Math.min(1, t / duration);
    ctx.strokeStyle = STATIC_CLR;
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, barY, barW, 8);
    ctx.fillStyle = BALL_CLR;
    ctx.fillRect(barX, barY, barW * progress, 8);

    // Collision notification
    const upcoming = collisions.filter((c) => c.time <= t);
    if (upcoming.length > 0) {
      const last = upcoming[upcoming.length - 1];
      const age = t - last.time;
      if (age < 1.5) {
        const alpha = Math.max(0, 1 - age / 1.5);
        const label = `COLLISION  ${last.objects.join(" + ")}  @ t=${last.time.toFixed(2)}s`;
        ctx.font = "12px monospace";
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = `rgba(255,80,80,${alpha})`;
        ctx.fillText(label, W - tw - 12, viewportH + 16);
      }
    }

    // Paused overlay
    if (stateRef.current.paused) {
      ctx.fillStyle = "rgba(200,210,220,0.6)";
      ctx.font = "16px monospace";
      const msg = "PAUSED  [Space] resume  [R] restart";
      ctx.fillText(msg, W / 2 - ctx.measureText(msg).width / 2, 20);
    }
  }, [scene, result, totalFrames, duration, collisions, trajectories, objects, collisionTimes]);

  // Animation loop
  useEffect(() => {
    let lastTime = 0;
    const simFps = totalFrames / duration;

    function loop(ts: number) {
      const dt = Math.min((ts - lastTime) / 1000, 0.05);
      lastTime = ts;

      const s = stateRef.current;
      if (!s.paused) {
        s.accum += dt * s.speed * simFps;
        const steps = Math.floor(s.accum);
        s.accum -= steps;
        s.frame = Math.min(s.frame + steps, totalFrames - 1);
        if (s.frame >= totalFrames - 1) s.paused = true;
      }

      draw();
      animRef.current = requestAnimationFrame(loop);
    }

    animRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animRef.current);
  }, [draw, totalFrames, duration]);

  // Keyboard controls
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const s = stateRef.current;
      if (e.key === " ") {
        s.paused = !s.paused;
        setPaused(s.paused);
      } else if (e.key === "r" || e.key === "R") {
        s.frame = 0;
        s.accum = 0;
        s.paused = false;
        setPaused(false);
      } else if (e.key === "+" || e.key === "=") {
        s.speed = Math.min(s.speed * 1.5, 8);
        setSpeed(s.speed);
      } else if (e.key === "-") {
        s.speed = Math.max(s.speed / 1.5, 0.125);
        setSpeed(s.speed);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function togglePause() {
    stateRef.current.paused = !stateRef.current.paused;
    if (!stateRef.current.paused && stateRef.current.frame >= totalFrames - 1) {
      stateRef.current.frame = 0;
      stateRef.current.accum = 0;
    }
    setPaused(stateRef.current.paused);
  }

  function restart() {
    stateRef.current.frame = 0;
    stateRef.current.accum = 0;
    stateRef.current.paused = false;
    setPaused(false);
  }

  function changeSpeed(delta: number) {
    const s = stateRef.current;
    s.speed = delta > 0
      ? Math.min(s.speed * 1.5, 8)
      : Math.max(s.speed / 1.5, 0.125);
    setSpeed(s.speed);
  }

  return (
    <div className="sim-viewer">
      <canvas
        ref={canvasRef}
        width={800}
        height={500}
        className="sim-canvas"
        style={{ width: "100%", height: "auto" }}
      />
      <div className="sim-controls">
        <button className="btn btn-secondary" onClick={togglePause}>
          {paused ? "▶ Resume" : "⏸ Pause"}
        </button>
        <button className="btn btn-secondary" onClick={restart}>↺ Restart</button>
        <button className="btn btn-secondary" onClick={() => changeSpeed(-1)}>− Slow</button>
        <span className="speed-label">{speed.toFixed(2)}×</span>
        <button className="btn btn-secondary" onClick={() => changeSpeed(1)}>+ Fast</button>
        <span className="sim-time">{simTime.toFixed(2)}s</span>
      </div>
    </div>
  );
}
