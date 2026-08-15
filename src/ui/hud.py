import pygame


def draw_score_panel(surface: pygame.Surface,
                     score: int,
                     font: pygame.font.Font,
                     x: int = 20, y: int = 10,
                     color=(255, 255, 255)) -> None:
    """Dessine le score avec une ombre portée."""
    shadow = font.render(str(score), True, (0, 0, 0))
    surface.blit(shadow, (x + 2, y + 2))
    text = font.render(str(score), True, color)
    surface.blit(text, (x, y))


def draw_lives(surface: pygame.Surface,
               lives: int,
               max_lives: int,
               heart_surf: pygame.Surface,
               right_x: int,
               y: int = 12) -> None:
    """Dessine les cœurs de vie alignés à droite."""
    w = heart_surf.get_width()
    for i in range(max_lives):
        x = right_x - w - i * (w + 8)
        if i < lives:
            surface.blit(heart_surf, (x, y))
        else:
            dim = heart_surf.copy()
            dim.set_alpha(50)
            surface.blit(dim, (x, y))
