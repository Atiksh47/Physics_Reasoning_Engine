import math
import pygame
from visualization.camera import Camera

# Palette
BG          = (15,  15,  20)
STATIC_CLR  = (100, 110, 120)
BALL_CLR    = (80,  160, 255)
BLOCK_CLR   = (255, 160,  60)
TRAIL_CLR   = (80,  160, 255)
HUD_BG      = (25,  25,  30)
HUD_TEXT    = (200, 210, 220)
COLLISION_CLR = (255, 80,  80)
FLASH_DURATION = 0.4  # seconds a collision flash stays visible


def _flash_alpha(age: float) -> int:
    """0-255 alpha for a collision flash that fades over FLASH_DURATION."""
    t = max(0.0, 1.0 - age / FLASH_DURATION)
    return int(200 * t)


class Renderer:
    def __init__(self, scene: dict, result: dict,
                 screen_w: int = 1200, screen_h: int = 700):
        pygame.init()
        pygame.display.set_caption("Physics Reasoning Engine")
        self.screen = pygame.display.set_mode((screen_w, screen_h))
        self.clock = pygame.time.Clock()
        self.cam = Camera(screen_w, screen_h)
        self.scene = scene
        self.result = result
        self.font_large = pygame.font.SysFont("monospace", 18)
        self.font_small = pygame.font.SysFont("monospace", 14)

        self.duration = result["duration"]
        self.steps_per_second = scene.get("steps_per_second", 120)
        self.sample_rate = max(1, self.steps_per_second // 10)

        # Pre-index trajectories: name → list of [x, y]
        self.trajectories = result.get("trajectories", {})
        self.collisions = result.get("collisions", [])

        # Build a name → scene object lookup
        self.objects = {o["name"]: o for o in scene.get("objects", [])}

    def _sim_time_to_frame(self, t: float) -> int:
        """Convert simulation time to trajectory sample index."""
        return int(t / self.duration * (len(next(iter(self.trajectories.values()), [[]])) - 1))

    def _get_positions(self, frame: int) -> dict[str, tuple[float, float]]:
        positions = {}
        for name, traj in self.trajectories.items():
            idx = min(frame, len(traj) - 1)
            positions[name] = tuple(traj[idx])
        return positions

    def _draw_static_objects(self):
        for obj in self.scene.get("objects", []):
            t = obj["type"]
            if t in ("slope", "ramp", "wall"):
                start = self.cam.to_screen(*obj["start"])
                end = self.cam.to_screen(*obj["end"])
                pygame.draw.line(self.screen, STATIC_CLR, start, end, 3)

    def _draw_trail(self, name: str, frame: int, trail_len: int = 30):
        traj = self.trajectories.get(name, [])
        if len(traj) < 2:
            return
        start_idx = max(0, frame - trail_len)
        points = traj[start_idx: frame + 1]
        for i, (wx, wy) in enumerate(points):
            alpha = int(180 * (i / len(points)) ** 1.5)
            sx, sy = self.cam.to_screen(wx, wy)
            r = max(1, self.cam.length(0.06))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*TRAIL_CLR, alpha), (r, r), r)
            self.screen.blit(surf, (sx - r, sy - r))

    def _draw_ball(self, name: str, pos: tuple[float, float], flash_age: float | None):
        obj = self.objects.get(name, {})
        radius = self.cam.length(obj.get("radius", 0.5))
        sx, sy = self.cam.to_screen(*pos)
        color = COLLISION_CLR if flash_age is not None else BALL_CLR
        pygame.draw.circle(self.screen, color, (sx, sy), radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), radius, 1)

    def _draw_block(self, name: str, pos: tuple[float, float], flash_age: float | None):
        obj = self.objects.get(name, {})
        w, h = obj.get("size", [1.0, 1.0])
        pw, ph = self.cam.length(w), self.cam.length(h)
        sx, sy = self.cam.to_screen(*pos)
        rect = pygame.Rect(sx - pw // 2, sy - ph // 2, pw, ph)
        color = COLLISION_CLR if flash_age is not None else BLOCK_CLR
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

    def _draw_hud(self, sim_time: float, positions: dict):
        hud_y = self.cam.viewport_h
        pygame.draw.rect(self.screen, HUD_BG,
                         (0, hud_y, self.cam.screen_w, self.cam.hud_height))
        pygame.draw.line(self.screen, STATIC_CLR,
                         (0, hud_y), (self.cam.screen_w, hud_y), 1)

        # Time and progress bar
        t_text = self.font_large.render(
            f"t = {sim_time:.2f}s / {self.duration:.1f}s", True, HUD_TEXT)
        self.screen.blit(t_text, (16, hud_y + 8))

        bar_x, bar_y = 16, hud_y + 34
        bar_w = 300
        progress = min(1.0, sim_time / self.duration)
        pygame.draw.rect(self.screen, STATIC_CLR, (bar_x, bar_y, bar_w, 8), 1)
        pygame.draw.rect(self.screen, BALL_CLR,
                         (bar_x, bar_y, int(bar_w * progress), 8))

        # Velocities for dynamic objects
        x_off = 340
        final = self.result.get("final_states", {})
        for name in self.trajectories:
            traj = self.trajectories[name]
            frame = min(self._sim_time_to_frame(sim_time), len(traj) - 1)
            if frame < len(traj) - 1:
                dx = traj[frame + 1][0] - traj[frame][0]
                dy = traj[frame + 1][1] - traj[frame][1]
                speed = math.hypot(dx, dy) * 10  # 10 samples/s
            else:
                fs = final.get(name, {})
                vx, vy = fs.get("velocity", [0, 0])
                speed = math.hypot(vx, vy)
            label = self.font_small.render(
                f"{name}: {speed:.1f} m/s", True, HUD_TEXT)
            self.screen.blit(label, (x_off, hud_y + 10))
            x_off += label.get_width() + 24

        # Collision events
        upcoming = [c for c in self.collisions if c["time"] <= sim_time]
        if upcoming:
            last = upcoming[-1]
            age = sim_time - last["time"]
            if age < 1.5:
                alpha = int(255 * max(0, 1.0 - age / 1.5))
                names = " + ".join(last["objects"])
                c_text = self.font_small.render(
                    f"COLLISION  {names}  @ t={last['time']:.2f}s", True, COLLISION_CLR)
                c_text.set_alpha(alpha)
                cx = self.cam.screen_w - c_text.get_width() - 16
                self.screen.blit(c_text, (cx, hud_y + 10))

    def run(self, playback_speed: float = 1.0):
        """
        Replay the pre-computed simulation.
        Space: pause/resume   R: restart   Q/Esc: quit
        +/-: speed up/slow down
        """
        total_frames = len(next(iter(self.trajectories.values()), [[]]))
        fps = 60
        frame = 0
        paused = False
        speed = playback_speed
        # frame advance accumulator (fractional frames)
        accum = 0.0

        # Build a collision flash lookup: object_name → latest flash time
        collision_times: dict[str, float] = {}
        for c in self.collisions:
            for name in c["objects"]:
                collision_times[name] = max(collision_times.get(name, 0.0), c["time"])

        while True:
            dt_ms = self.clock.tick(fps)
            dt = dt_ms / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit()
                        return
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    if event.key == pygame.K_r:
                        frame = 0
                        accum = 0.0
                    if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        speed = min(speed * 1.5, 8.0)
                    if event.key == pygame.K_MINUS:
                        speed = max(speed / 1.5, 0.125)

            if not paused:
                # How many frames to advance this tick
                sim_fps = total_frames / self.duration  # samples per sim-second
                accum += dt * speed * sim_fps
                steps = int(accum)
                accum -= steps
                frame = min(frame + steps, total_frames - 1)

            sim_time = frame / (total_frames - 1) * self.duration if total_frames > 1 else 0.0
            positions = self._get_positions(frame)

            # Flash ages
            flash_ages: dict[str, float] = {}
            for name, ct in collision_times.items():
                if sim_time >= ct:
                    age = sim_time - ct
                    if age < FLASH_DURATION:
                        flash_ages[name] = age

            # Draw
            self.screen.fill(BG)
            self._draw_static_objects()

            for name, pos in positions.items():
                obj = self.objects.get(name, {})
                t = obj.get("type")
                flash_age = flash_ages.get(name)
                if t == "ball":
                    self._draw_trail(name, frame)
                    self._draw_ball(name, pos, flash_age)
                elif t == "block":
                    self._draw_block(name, pos, flash_age)

            self._draw_hud(sim_time, positions)

            if paused:
                p_text = self.font_large.render("PAUSED  [Space] resume  [R] restart", True, HUD_TEXT)
                self.screen.blit(p_text, (self.cam.screen_w // 2 - p_text.get_width() // 2, 12))

            speed_text = self.font_small.render(f"{speed:.2f}x  [+/-]", True, STATIC_CLR)
            self.screen.blit(speed_text, (self.cam.screen_w - speed_text.get_width() - 8, 8))

            pygame.display.flip()

            if not paused and frame >= total_frames - 1:
                # Hold on last frame
                paused = True
