import pygame

from .fruit import Fruit, FruitState, load_scaled_image


class Bomb(Fruit):
    # Durée d'affichage de l'explosion (~0.75s à 60 FPS)
    EXPLOSION_DURATION = 45

    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(x, y, vx, vy,
                         radius=42,
                         image_path="bomb.png",
                         points=0)
        self._exploded = False
        self._explosion_timer = 0

        # Sprite d'explosion dédié (fallback = cercle qui grandit si absent)
        diameter = self.radius * 4
        self.image_explosion = load_scaled_image("bomb_explosion.png", (diameter, diameter))

    @property
    def color(self) -> tuple[int, int, int]:
        return (30, 30, 30)    # noir

    @property
    def name(self) -> str:
        return "Bomb"

    @property
    def exploded(self) -> bool:
        return self._exploded

    # ──────────────────────────────────────────────
    # Surcharges : la bombe explose au lieu de se trancher
    # ──────────────────────────────────────────────

    def slice(self) -> None:
        if self.state != FruitState.ALIVE:
            return
        self._exploded = True
        self.state = FruitState.EXPLODING
        self._explosion_timer = self.EXPLOSION_DURATION

    def update(self, screen_height: int) -> None:
        if self.state == FruitState.ALIVE:
            self._update_alive(screen_height)
        elif self.state == FruitState.EXPLODING:
            self._explosion_timer -= 1
            if self._explosion_timer <= 0:
                self.state = FruitState.DEAD

    def draw(self, surface: pygame.Surface) -> None:
        if self.state == FruitState.ALIVE:
            self._draw_whole(surface)
        elif self.state == FruitState.EXPLODING:
            self._draw_explosion(surface)

    def _draw_explosion(self, surface: pygame.Surface) -> None:
        progress = 1 - (self._explosion_timer / self.EXPLOSION_DURATION)
        if self.image_explosion:
            alpha = 255 if progress < 0.7 else int(255 * (1 - progress) / 0.3)
            img = self.image_explosion.copy()
            img.set_alpha(max(0, alpha))
            rect = img.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(img, rect)
        else:
            # Fallback : cercle orange/rouge qui grandit puis s'estompe
            max_r = self.radius * 3
            r = int(self.radius + max_r * progress)
            alpha = max(0, int(255 * (1 - progress)))
            burst = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(burst, (255, 140, 0, alpha), (r, r), r)
            pygame.draw.circle(burst, (255, 60, 0, alpha), (r, r), int(r * 0.6))
            surface.blit(burst, (int(self.x) - r, int(self.y) - r))
