from __future__ import annotations
import math
from pathlib import Path
import pygame

_FONTS = Path(__file__).resolve().parents[2] / "assets" / "fonts"

WHITE  = (255, 255, 255)
RED    = (220, 50,  50)
ORANGE = (255, 165, 0)
YELLOW = (255, 220, 0)
GRAY   = (180, 180, 180)
BLACK  = (0,   0,   0)


class GameOverScreen:
    """
    Paramètres
    ----------
    screen       : surface Pygame principale
    width/height : dimensions de la fenêtre
    """

    def __init__(self, screen: pygame.Surface,
                 width: int, height: int) -> None:
        self.screen = screen
        self.width  = width
        self.height = height

        font_path = _FONTS / "game_font.ttf"
        if font_path.exists():
            self.font_big    = pygame.font.Font(str(font_path), 72)
            self.font_medium = pygame.font.Font(str(font_path), 36)
            self.font_small  = pygame.font.Font(str(font_path), 22)
        else:
            self.font_big    = pygame.font.SysFont("Arial", 72, bold=True)
            self.font_medium = pygame.font.SysFont("Arial", 36, bold=True)
            self.font_small  = pygame.font.SysFont("Arial", 22)

        # Boutons
        btn_w, btn_h = 240, 55
        cx = width // 2
        cy = height // 2 + 80
        self.btn_restart = pygame.Rect(cx - btn_w - 15, cy, btn_w, btn_h)
        self.btn_menu    = pygame.Rect(cx + 15,         cy, btn_w, btn_h)

        self._anim = 0

    # ──────────────────────────────────────────────
    # Boucle
    # ──────────────────────────────────────────────

    def run(self, final_score: int) -> str:
        """
        Retourne "restart", "menu" ou "quit".
        """
        clock = pygame.time.Clock()

        while True:
            self._anim += 1
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_r:
                        return "restart"
                    if event.key == pygame.K_m or event.key == pygame.K_BACKSPACE:
                        return "menu"
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_restart.collidepoint(mouse_pos):
                        return "restart"
                    if self.btn_menu.collidepoint(mouse_pos):
                        return "menu"

            self._draw(final_score, mouse_pos)
            clock.tick(60)

    # ──────────────────────────────────────────────
    # Rendu
    # ──────────────────────────────────────────────

    def _draw(self, score: int, mouse_pos: tuple[int, int]) -> None:
        # Fond semi-transparent sur ce qui était affiché
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2

        # Titre GAME OVER avec oscillation rouge/orange
        pulse = abs(math.sin(self._anim * 0.05))
        r = int(180 + 75 * pulse)
        title_color = (r, 50, 50)

        title = self.font_big.render("GAME OVER", True, title_color)
        shadow = self.font_big.render("GAME OVER", True, BLACK)
        tx = cx - title.get_width() // 2
        self.screen.blit(shadow, (tx + 4, self.height // 3 + 4))
        self.screen.blit(title,  (tx,     self.height // 3))

        # Score
        score_txt = self.font_medium.render(f"Score final : {score}", True, YELLOW)
        self.screen.blit(score_txt,
                         (cx - score_txt.get_width() // 2,
                          self.height // 3 + 90))

        # Bouton REJOUER
        hover_r = self.btn_restart.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen,
                         ORANGE if hover_r else (180, 90, 0),
                         self.btn_restart, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.btn_restart,
                         2, border_radius=10)
        r_txt = self.font_small.render("↺  REJOUER  (R)", True, WHITE)
        self.screen.blit(r_txt, (
            self.btn_restart.centerx - r_txt.get_width() // 2,
            self.btn_restart.centery - r_txt.get_height() // 2,
        ))

        # Bouton RETOUR AU MENU
        hover_m = self.btn_menu.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen,
                         (90, 90, 140) if hover_m else (55, 55, 90),
                         self.btn_menu, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.btn_menu,
                         2, border_radius=10)
        m_txt = self.font_small.render("⌂  RETOUR AU MENU  (M)", True, WHITE)
        self.screen.blit(m_txt, (
            self.btn_menu.centerx - m_txt.get_width() // 2,
            self.btn_menu.centery - m_txt.get_height() // 2,
        ))

        # Hint clavier
        hint = self.font_small.render(
            "Entrée = Rejouer   |   M = Menu   |   Échap = Quitter", True, GRAY)
        self.screen.blit(hint, (cx - hint.get_width() // 2,
                                 self.btn_restart.bottom + 20))

        pygame.display.flip()
