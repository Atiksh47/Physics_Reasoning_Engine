class Camera:
    """
    Converts pymunk world coordinates (origin bottom-left, y-up)
    to pygame screen coordinates (origin top-left, y-down).
    """

    def __init__(self, screen_w: int, screen_h: int, world_w: float = 20.0):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.scale = screen_w / world_w
        # Leave a margin at the bottom of the screen for the HUD
        self.hud_height = 60
        self.viewport_h = screen_h - self.hud_height

    def to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        sx = int(wx * self.scale)
        sy = int(self.viewport_h - wy * self.scale)
        return sx, sy

    def length(self, world_len: float) -> int:
        return max(1, int(world_len * self.scale))
