import math
import random
from dataclasses import dataclass

import pygame


BACKGROUND = (236, 232, 224)
ANT_COLOR = (20, 18, 16)
TEXT_COLOR = (70, 66, 60)
ANT_COUNT = 320
TARGET_RADIUS = 95
WANDER_STRENGTH = 0.35
SEEK_STRENGTH = 0.9
DRAG = 0.92
MAX_SPEED = 2.2


@dataclass
class Ant:
    x: float
    y: float
    vx: float
    vy: float
    angle: float

    def update(self, target_x: float, target_y: float, width: int, height: int) -> None:
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy) + 1e-6

        if distance < TARGET_RADIUS:
            seek = 1.0 - (distance / TARGET_RADIUS)
            self.vx += (dx / distance) * seek * SEEK_STRENGTH
            self.vy += (dy / distance) * seek * SEEK_STRENGTH
        else:
            self.vx += random.uniform(-WANDER_STRENGTH, WANDER_STRENGTH)
            self.vy += random.uniform(-WANDER_STRENGTH, WANDER_STRENGTH)

        self.vx *= DRAG
        self.vy *= DRAG

        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale

        self.x = (self.x + self.vx) % width
        self.y = (self.y + self.vy) % height

        if speed > 0.01:
            self.angle = math.atan2(self.vy, self.vx)

    def draw(self, surface: pygame.Surface) -> None:
        heading_x = math.cos(self.angle)
        heading_y = math.sin(self.angle)
        side_x = -heading_y
        side_y = heading_x

        head = (self.x + heading_x * 3.0, self.y + heading_y * 3.0)
        tail_left = (self.x - heading_x * 2.3 + side_x * 1.2, self.y - heading_y * 2.3 + side_y * 1.2)
        tail_right = (self.x - heading_x * 2.3 - side_x * 1.2, self.y - heading_y * 2.3 - side_y * 1.2)

        pygame.draw.polygon(surface, ANT_COLOR, (head, tail_left, tail_right))


def spawn_ants(width: int, height: int) -> list[Ant]:
    ants = []
    for _ in range(ANT_COUNT):
        ants.append(
            Ant(
                x=random.uniform(0, width),
                y=random.uniform(0, height),
                vx=random.uniform(-1, 1),
                vy=random.uniform(-1, 1),
                angle=random.uniform(0, math.tau),
            )
        )
    return ants


def create_screen(fullscreen: bool) -> pygame.Surface:
    flags = pygame.FULLSCREEN if fullscreen else 0
    return pygame.display.set_mode((0, 0), flags) if fullscreen else pygame.display.set_mode((1600, 600))


def draw_overlay(surface: pygame.Surface, font: pygame.font.Font, fullscreen: bool) -> None:
    mode = "fullscreen" if fullscreen else "windowed"
    text = "Maus = Zielpunkt | f = fullscreen | r = reset | esc = quit | mode: " + mode
    label = font.render(text, True, TEXT_COLOR)
    surface.blit(label, (20, 18))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Ameisen Monitor Demo")

    fullscreen = False
    screen = create_screen(fullscreen)
    width, height = screen.get_size()
    ants = spawn_ants(width, height)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 22)

    target_x = width * 0.5
    target_y = height * 0.5

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
                    ants = spawn_ants(width, height)
                elif event.key == pygame.K_r:
                    ants = spawn_ants(width, height)
            elif event.type == pygame.MOUSEMOTION:
                target_x, target_y = event.pos

        screen.fill(BACKGROUND)

        pygame.draw.circle(screen, (210, 205, 196), (int(target_x), int(target_y)), TARGET_RADIUS, width=1)

        for ant in ants:
            ant.update(target_x, target_y, width, height)
            ant.draw(screen)

        draw_overlay(screen, font, fullscreen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
