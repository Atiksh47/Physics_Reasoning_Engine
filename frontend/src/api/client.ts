const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface SceneObject {
  type: "ball" | "slope" | "ramp" | "wall" | "block";
  name: string;
  position?: [number, number];
  radius?: number;
  mass?: number;
  elasticity?: number;
  friction?: number;
  size?: [number, number];
  start?: [number, number];
  end?: [number, number];
  static?: boolean;
}

export interface Scene {
  name?: string;
  gravity: [number, number];
  damping?: number;
  duration: number;
  steps_per_second: number;
  objects: SceneObject[];
  queries?: string[];
}

export interface CollisionEvent {
  time: number;
  objects: string[];
  impact_impulse: number;
}

export interface ObjectState {
  position: [number, number];
  velocity: [number, number];
  peak_velocity: number;
}

export interface SimulationResult {
  duration: number;
  collisions: CollisionEvent[];
  final_states: Record<string, ObjectState>;
  trajectories: Record<string, [number, number][]>;
}

export interface SimulationResponse {
  scene: Scene;
  result: SimulationResult;
  explanation: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export function simulateText(description: string): Promise<SimulationResponse> {
  return request<SimulationResponse>("/simulate", {
    method: "POST",
    body: JSON.stringify({ description }),
  });
}

export function simulateJson(scene: Scene): Promise<SimulationResponse> {
  return request<SimulationResponse>("/simulate/json", {
    method: "POST",
    body: JSON.stringify({ scene }),
  });
}

export function whatIf(
  scene: Scene,
  changes: Record<string, unknown>
): Promise<SimulationResponse> {
  return request<SimulationResponse>("/whatif", {
    method: "POST",
    body: JSON.stringify({ scene, changes }),
  });
}

export function listScenes(): Promise<{ scenes: string[] }> {
  return request<{ scenes: string[] }>("/scenes");
}

export function getScene(id: string): Promise<Scene> {
  return request<Scene>(`/scenes/${id}`);
}
