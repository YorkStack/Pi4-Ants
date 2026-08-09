import math
import random
from dataclasses import dataclass

import cv2
import numpy as np
import pygame


BACKGROUND = (236, 232, 224)
ANT_COLOR = (20, 18, 16)
TEXT_COLOR = (70, 66, 60)
PREVIEW_TINT = (160, 154, 146)

CAPTURE_DEVICE = 0
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 360
PROCESS_WIDTH = 160
PROCESS_HEIGHT = 90

ANT_COUNT = 520
TRAIL_FADE_ALPHA = 16
MAX_TRAIL_POINTS = 240
TARGET_REFRESH_FRAMES = 3
MOUSE_TARGET_RADIUS = 95
SEEK_STRENGTH = 0.55
WANDER_STRENGTH = 0.24
DRAG = 0.9
MAX_SPEED = 2.0


@dataclass
class Ant:
    x: float
    y: float
    vx: float
    vy: float
    angle: float
    target_x: float
    target_y: float

    def retarget(self, points: list[tuple[int, int]], width: int, height: int) -> None:
        if points:
            self.target_x, self.target_y = random.choice(points)
        else:
            self.target_x = random.uniform(0, width)
            self.target_y = random.uniform(0, height)

    def update(self, points: list[tuple[int, int]], width: int, height: int) -> tuple[float, float]:
        if points:
            if random.random() < 0.03:
                self.retarget(points, width, height)
        elif random.random() < 0.01:
            self.retarget(points, width, height)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy) + 1e-6

        if distance < 16:
            self.retarget(points, width, height)
        else:
            self.vx += (dx / distance) * SEEK_STRENGTH
            self.vy += (dy / distance) * SEEK_STRENGTH

        self.vx += random.uniform(-WANDER_STRENGTH, WANDER_STRENGTH)
        self.vy += random.uniform(-WANDER_STRENGTH, WANDER_STRENGTH)

        self.vx *= DRAG
        self.vy *= DRAG

        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale

        previous = (self.x, self.y)
        self.x = (self.x + self.vx) % width
        self.y = (self.y + self.vy) % height

        if speed > 0.01:
            self.angle = math.atan2(self.vy, self.vx)

        return previous

    def draw(self, surface: pygame.Surface) -> None:
        heading_x = math.cos(self.angle)
        heading_y = math.sin(self.angle)
        side_x = -heading_y
        side_y = heading_x

        head = (self.x + heading_x * 3.0, self.y + heading_y * 3.0)
        tail_left = (self.x - heading_x * 2.3 + side_x * 1.2, self.y - heading_y * 2.3 + side_y * 1.2)
        tail_right = (self.x - heading_x * 2.3 - side_x * 1.2, self.y - heading_y * 2.3 - side_y * 1.2)

        pygame.draw.polygon(surface, ANT_COLOR, (head, tail_left, tail_right))


class CameraTracker:
    def __init__(self) -> None:
        self.cap = cv2.VideoCapture(CAPTURE_DEVICE)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)

        self.background: np.ndarray | None = None
        self.previous_gray: np.ndarray | None = None

    def is_open(self) -> bool:
        return self.cap.isOpened()

    def release(self) -> None:
        if self.cap.isOpened():
            self.cap.release()

    def get_targets(self, display_size: tuple[int, int]) -> tuple[list[tuple[int, int]], pygame.Surface | None]:
        ok, frame = self.cap.read()
        if not ok:
            return [], None

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        if self.background is None:
            self.background = gray.astype(np.float32)
            self.previous_gray = gray.copy()
            return [], self.make_preview(gray, np.zeros_like(gray), display_size)

        cv2.accumulateWeighted(gray, self.background, 0.02)
        background_u8 = cv2.convertScaleAbs(self.background)
        foreground_diff = cv2.absdiff(gray, background_u8)
        _, foreground_mask = cv2.threshold(foreground_diff, 28, 255, cv2.THRESH_BINARY)
        foreground_mask = cv2.medianBlur(foreground_mask, 5)

        motion_diff = cv2.absdiff(gray, self.previous_gray)
        _, motion_mask = cv2.threshold(motion_diff, 18, 255, cv2.THRESH_BINARY)
        motion_mask = cv2.GaussianBlur(motion_mask, (5, 5), 0)

        edges = cv2.Canny(gray, 45, 110)
        edges = cv2.bitwise_and(edges, foreground_mask)
        combined = cv2.addWeighted(edges, 0.75, motion_mask, 0.65, 0)
        _, combined = cv2.threshold(combined, 45, 255, cv2.THRESH_BINARY)

        self.previous_gray = gray.copy()

        points = self.sample_points(combined, display_size)
        preview = self.make_preview(gray, combined, display_size)
        return points, preview

    def sample_points(self, mask: np.ndarray, display_size: tuple[int, int]) -> list[tuple[int, int]]:
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return []

        width, height = display_size
        scale_x = width / PROCESS_WIDTH
        scale_y = height / PROCESS_HEIGHT

        step = max(1, len(xs) // MAX_TRAIL_POINTS)
        points = []
        for index in range(0, len(xs), step):
            x = int(xs[index] * scale_x)
            y = int(ys[index] * scale_y)
            points.append((x, y))
            if len(points) >= MAX_TRAIL_POINTS:
                break
        return points

    def make_preview(
        self,
        gray: np.ndarray,
        combined: np.ndarray,
        display_size: tuple[int, int],
    ) -> pygame.Surface:
        preview = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        preview[:, :, 0] = np.minimum(preview[:, :, 0], PREVIEW_TINT[0])
        preview[:, :, 1] = np.minimum(preview[:, :, 1], PREVIEW_TINT[1])
        preview[:, :, 2] = np.minimum(preview[:, :, 2], PREVIEW_TINT[2])
        preview[combined > 0] = (12, 12, 12)

        preview = cv2.resize(preview, display_size, interpolation=cv2.INTER_NEAREST)
        preview = np.transpose(preview, (1, 0, 2))
        return pygame.surfarray.make_surface(preview)


def spawn_ants(width: int, height: int, points: list[tuple[int, int]] | None = None) -> list[Ant]:
    ants = []
    points = points or []
    for _ in range(ANT_COUNT):
        ant = Ant(
            x=random.uniform(0, width),
            y=random.uniform(0, height),
            vx=random.uniform(-0.6, 0.6),
            vy=random.uniform(-0.6, 0.6),
            angle=random.uniform(0, math.tau),
            target_x=random.uniform(0, width),
            target_y=random.uniform(0, height),
        )
        ant.retarget(points, width, height)
        ants.append(ant)
    return ants


def create_screen(fullscreen: bool) -> pygame.Surface:
    flags = pygame.FULLSCREEN if fullscreen else 0
    return pygame.display.set_mode((0, 0), flags) if fullscreen else pygame.display.set_mode((1600, 600))


def draw_overlay(
    surface: pygame.Surface,
    font: pygame.font.Font,
    fullscreen: bool,
    camera_ready: bool,
    target_count: int,
) -> None:
    mode = "fullscreen" if fullscreen else "windowed"
    camera_label = "camera" if camera_ready else "mouse fallback"
    text = (
        f"mode: {mode} | input: {camera_label} | targets: {target_count} | "
        "f = fullscreen | r = reset | c = recenter bg | esc = quit"
    )
    label = font.render(text, True, TEXT_COLOR)
    surface.blit(label, (20, 18))


def fade_trails(trail_surface: pygame.Surface) -> None:
    trail_surface.blit(
        pygame.Surface(trail_surface.get_size(), pygame.SRCALPHA).convert_alpha(),
        (0, 0),
    )
    trail_surface.fill((255, 255, 255, TRAIL_FADE_ALPHA), special_flags=pygame.BLEND_RGBA_SUB)


def draw_mouse_target(surface: pygame.Surface, pos: tuple[int, int]) -> None:
    pygame.draw.circle(surface, (210, 205, 196), pos, MOUSE_TARGET_RADIUS, width=1)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Pi4 Ants Camera Demo")

    fullscreen = False
    screen = create_screen(fullscreen)
    width, height = screen.get_size()
    font = pygame.font.SysFont("dejavusans", 22)
    clock = pygame.time.Clock()

    camera = CameraTracker()
    target_points: list[tuple[int, int]] = []
    ants = spawn_ants(width, height, target_points)
    trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    target_x = width // 2
    target_y = height // 2
    preview_surface: pygame.Surface | None = None
    frame_index = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    screen = create_screen(fullscreen)
                    width, height = screen.get_size()
                    ants = spawn_ants(width, height, target_points)
                    trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                elif event.key == pygame.K_r:
                    ants = spawn_ants(width, height, target_points)
                    trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                elif event.key == pygame.K_c:
                    camera.background = None
            elif event.type == pygame.MOUSEMOTION:
                target_x, target_y = event.pos

        frame_index += 1
        if camera.is_open() and frame_index % TARGET_REFRESH_FRAMES == 0:
            target_points, preview_surface = camera.get_targets((width, height))

        screen.fill(BACKGROUND)

        if preview_surface is not None:
            screen.blit(preview_surface, (0, 0))

        fade_trails(trail_surface)

        use_camera_targets = len(target_points) > 0
        if not use_camera_targets:
            draw_mouse_target(screen, (target_x, target_y))

        for ant in ants:
            if use_camera_targets:
                previous = ant.update(target_points, width, height)
            else:
                ant.target_x = target_x
                ant.target_y = target_y
                previous = ant.update([], width, height)

            pygame.draw.line(
                trail_surface,
                (0, 0, 0, 28),
                previous,
                (ant.x, ant.y),
                width=1,
            )

        screen.blit(trail_surface, (0, 0))

        for ant in ants:
            ant.draw(screen)

        draw_overlay(screen, font, fullscreen, camera.is_open(), len(target_points))
        pygame.display.flip()
        clock.tick(60)

    camera.release()
    pygame.quit()


if __name__ == "__main__":
    main()
