"""
GIF/PNG export for simulations.

Usage:
    export_gif(scene, result, "output.gif")
    export_frames(scene, result, "frames/")  # individual PNGs
"""

import os
import math
import pygame
import pygame.surfarray

from visualization.camera import Camera

# Same palette as renderer.py
BG            = (15,  15,  20)
STATIC_CLR    = (100, 110, 120)
BALL_CLR      = (80,  160, 255)
BLOCK_CLR     = (255, 160,  60)
TRAIL_CLR     = (80,  160, 255)
HUD_BG        = (25,  25,  30)
HUD_TEXT      = (200, 210, 220)
COLLISION_CLR = (255, 80,  80)
FLASH_DURATION = 0.4


def _render_frame(surface: pygame.Surface, cam: Camera,
                  scene: dict, result: dict,
                  frame: int, total_frames: int,
                  font_large: pygame.font.Font, font_small: pygame.font.Font) -> None:
    """Draw one frame onto surface (mirrors Renderer draw logic)."""
    trajectories = result.get("trajectories", {})
    collisions   = result.get("collisions", [])
    objects      = {o["name"]: o for o in scene.get("objects", [])}
    duration     = result["duration"]

    sim_time = frame / (total_frames - 1) * duration if total_frames > 1 else 0.0

    # Build collision flash lookup
    collision_times: dict[str, float] = {}
    for c in collisions:
        for name in c["objects"]:
            collision_times[name] = max(collision_times.get(name, 0.0), c["time"])

    flash_ages: dict[str, float] = {}
    for name, ct in collision_times.items():
        if sim_time >= ct:
            age = sim_time - ct
            if age < FLASH_DURATION:
                flash_ages[name] = age

    surface.fill(BG)

    # Static objects
    for obj in scene.get("objects", []):
        if obj["type"] in ("slope", "ramp", "wall"):
            start = cam.to_screen(*obj["start"])
            end   = cam.to_screen(*obj["end"])
            pygame.draw.line(surface, STATIC_CLR, start, end, 3)

    # Dynamic objects
    for name, traj in trajectories.items():
        idx = min(frame, len(traj) - 1)
        pos = tuple(traj[idx])
        obj = objects.get(name, {})
        t   = obj.get("type")
        flash_age = flash_ages.get(name)

        if t == "ball":
            # Trail
            trail_len = 30
            start_idx = max(0, frame - trail_len)
            trail_pts  = traj[start_idx: frame + 1]
            for i, (wx, wy) in enumerate(trail_pts):
                alpha = int(180 * (i / max(len(trail_pts), 1)) ** 1.5)
                sx, sy = cam.to_screen(wx, wy)
                r = max(1, cam.length(0.06))
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*TRAIL_CLR, alpha), (r, r), r)
                surface.blit(surf, (sx - r, sy - r))

            radius = cam.length(obj.get("radius", 0.5))
            sx, sy = cam.to_screen(*pos)
            color  = COLLISION_CLR if flash_age is not None else BALL_CLR
            pygame.draw.circle(surface, color, (sx, sy), radius)
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), radius, 1)

        elif t == "block":
            w, h   = obj.get("size", [1.0, 1.0])
            pw, ph = cam.length(w), cam.length(h)
            sx, sy = cam.to_screen(*pos)
            rect   = pygame.Rect(sx - pw // 2, sy - ph // 2, pw, ph)
            color  = COLLISION_CLR if flash_age is not None else BLOCK_CLR
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 1)

    # HUD
    hud_y = cam.viewport_h
    pygame.draw.rect(surface, HUD_BG, (0, hud_y, cam.screen_w, cam.hud_height))
    pygame.draw.line(surface, STATIC_CLR, (0, hud_y), (cam.screen_w, hud_y), 1)

    t_text = font_large.render(
        f"t = {sim_time:.2f}s / {duration:.1f}s", True, HUD_TEXT)
    surface.blit(t_text, (16, hud_y + 8))

    bar_x, bar_y = 16, hud_y + 34
    bar_w = 300
    progress = min(1.0, sim_time / duration)
    pygame.draw.rect(surface, STATIC_CLR, (bar_x, bar_y, bar_w, 8), 1)
    pygame.draw.rect(surface, BALL_CLR,   (bar_x, bar_y, int(bar_w * progress), 8))

    upcoming = [c for c in collisions if c["time"] <= sim_time]
    if upcoming:
        last = upcoming[-1]
        age  = sim_time - last["time"]
        if age < 1.5:
            alpha  = int(255 * max(0, 1.0 - age / 1.5))
            names  = " + ".join(last["objects"])
            c_text = font_small.render(
                f"COLLISION  {names}  @ t={last['time']:.2f}s", True, COLLISION_CLR)
            c_text.set_alpha(alpha)
            cx = cam.screen_w - c_text.get_width() - 16
            surface.blit(c_text, (cx, hud_y + 10))


def export_frames(scene: dict, result: dict,
                  output_dir: str = "frames",
                  screen_w: int = 800, screen_h: int = 480,
                  fps: int = 20) -> list[str]:
    """
    Render the simulation to individual PNG files.
    Returns the list of file paths written.
    """
    os.makedirs(output_dir, exist_ok=True)

    trajectories = result.get("trajectories", {})
    if not trajectories:
        raise ValueError("result has no trajectories — run the simulation first")

    total_frames = len(next(iter(trajectories.values())))
    duration     = result["duration"]

    # Which trajectory frames to export (sub-sample to target fps)
    sim_fps     = total_frames / duration          # samples per sim-second
    step        = max(1, int(sim_fps / fps))       # trajectory frames per export frame
    export_idxs = list(range(0, total_frames, step))

    pygame.init()
    pygame.font.init()
    surface    = pygame.Surface((screen_w, screen_h))
    cam        = Camera(screen_w, screen_h)
    font_large = pygame.font.SysFont("monospace", 18)
    font_small = pygame.font.SysFont("monospace", 14)

    paths = []
    for i, frame in enumerate(export_idxs):
        _render_frame(surface, cam, scene, result, frame, total_frames,
                      font_large, font_small)
        path = os.path.join(output_dir, f"frame_{i:04d}.png")
        pygame.image.save(surface, path)
        paths.append(path)

    pygame.quit()
    return paths


def export_gif(scene: dict, result: dict,
               output_path: str = "simulation.gif",
               screen_w: int = 800, screen_h: int = 480,
               fps: int = 20) -> str:
    """
    Render the simulation and save as an animated GIF.
    Returns the path of the written file.

    Requires: pip install pillow
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Pillow is required for GIF export.\n"
            "Install it with: pip install pillow"
        )

    frames_dir = output_path + "_frames_tmp"
    frame_paths = export_frames(scene, result, frames_dir,
                                screen_w=screen_w, screen_h=screen_h, fps=fps)

    if not frame_paths:
        raise ValueError("No frames were rendered")

    pil_frames = [Image.open(p).convert("RGB") for p in frame_paths]
    duration_ms = int(1000 / fps)

    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )

    # Clean up temp frames
    for p in frame_paths:
        os.remove(p)
    os.rmdir(frames_dir)

    return output_path


if __name__ == "__main__":
    import sys
    import json

    scene_path = sys.argv[1] if len(sys.argv) > 1 else "scenes/example_basic.json"
    out_path   = sys.argv[2] if len(sys.argv) > 2 else "simulation.gif"

    with open(scene_path) as f:
        scene = json.load(f)

    from physics.simulation import run_simulation
    print("Running simulation...")
    result = run_simulation(scene)

    print(f"Exporting GIF → {out_path} ...")
    export_gif(scene, result, out_path)
    print("Done.")
