from __future__ import annotations

from pathlib import Path
import pygame
import numpy as np
import cv2

from src.game.game_manager import GameManager
from src.blade.blade_tracker import BladeTracker

_ASSETS = Path(__file__).resolve().parents[2] / "assets"
_FONTS  = _ASSETS / "fonts"
_IMAGES = _ASSETS / "images"

# ── Couleurs ──────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
RED        = (220, 50,  50)
YELLOW     = (255, 220, 0)
CYAN       = (0,   220, 220)
ORANGE     = (255, 140, 0)
BLADE_COL  = (255, 255, 200)
BLADE_TIP  = (255, 255, 255)


class Renderer:
    """Gère tout le rendu Pygame."""

    def __init__(self, screen: pygame.Surface,
                 width: int, height: int) -> None:
        self.screen = screen
        self.width  = width
        self.height = height

        # Polices
        font_path = _FONTS / "game_font.ttf"
        if font_path.exists():
            self.font_large  = pygame.font.Font(str(font_path), 48)
            self.font_medium = pygame.font.Font(str(font_path), 28)
            self.font_small  = pygame.font.Font(str(font_path), 20)
        else:
            self.font_large  = pygame.font.SysFont("Arial", 48, bold=True)
            self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_small  = pygame.font.SysFont("Arial", 20)

        # Fond statique (fallback si pas de webcam)
        self._bg_surface: pygame.Surface | None = None
        bg_path = _IMAGES / "background.png"
        if bg_path.exists():
            bg = pygame.image.load(str(bg_path)).convert()
            self._bg_surface = pygame.transform.scale(bg, (width, height))

        # Cœurs (vies)
        self._heart_surf = self._make_heart()

    # ──────────────────────────────────────────────
    # Point d'entrée principal
    # ──────────────────────────────────────────────

    def draw(self, frame_bgr: np.ndarray,
             game: GameManager,
             blade: BladeTracker) -> None:
        """Dessine une frame complète."""

        # 1. Fond
        self._draw_background(frame_bgr)

        # 2. Objets du jeu
        for obj in game.objects:
            obj.draw(self.screen)

        # 3. Lame
        self._draw_blade(blade)

        # 4. HUD
        self._draw_hud(game)

        # 5. Effets flottants (+points, combo)
        self._draw_effects(game)

        pygame.display.flip()

    # ──────────────────────────────────────────────
    # Fond
    # ──────────────────────────────────────────────

    def _draw_background(self, frame_bgr: np.ndarray) -> None:
        """Affiche la frame webcam (convertie BGR->RGB) comme fond."""
        try:
            # OpenCV BGR -> RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            # numpy (H, W, 3) -> pygame Surface
            # surfarray.make_surface attend (W, H, 3)
            surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            self.screen.blit(surf, (0, 0))
        except Exception:
            # Fallback : fond noir ou image statique
            if self._bg_surface:
                self.screen.blit(self._bg_surface, (0, 0))
            else:
                self.screen.fill((20, 20, 30))

    # ──────────────────────────────────────────────
    # Lame
    # ──────────────────────────────────────────────

    def _draw_blade(self, blade: BladeTracker) -> None:
        """Dessine la traînée de la lame avec dégradé d'opacité."""
        segments = blade.get_all_segments()
        n = len(segments)
        if n == 0:
            return

        for i, (p1, p2) in enumerate(segments):
            # Opacité croissante vers la pointe
            alpha   = int(255 * (i + 1) / n)
            # Épaisseur croissante vers la pointe
            width   = max(1, int(6 * (i + 1) / n))

            # Créer une surface transparente pour le segment
            tmp = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            color_a = (*BLADE_COL, alpha)
            pygame.draw.line(tmp, color_a, p1, p2, width)
            self.screen.blit(tmp, (0, 0))

        # Point lumineux à la pointe
        tip = blade.get_tip()
        if tip and blade.is_active:
            pygame.draw.circle(self.screen, BLADE_TIP, tip, 6)

    # ──────────────────────────────────────────────
    # HUD
    # ──────────────────────────────────────────────

    def _draw_hud(self, game: GameManager) -> None:
        sm = game.score_manager
        lm = game.level_manager

        # Score
        score_surf = self.font_large.render(str(sm.score), True, WHITE)
        self.screen.blit(score_surf, (20, 10))

        # Niveau
        lvl_surf = self.font_small.render(lm.level_label, True, CYAN)
        self.screen.blit(lvl_surf, (20, 65))

        # Vies (cœurs)
        for i in range(sm.MAX_LIVES):
            x = self.width - 45 - i * 40
            if i < sm.lives:
                self.screen.blit(self._heart_surf, (x, 12))
            else:
                # Cœur vide (plus sombre)
                empty = self._heart_surf.copy()
                empty.set_alpha(60)
                self.screen.blit(empty, (x, 12))

        # Combo
        if sm.combo_label:
            combo_surf = self.font_medium.render(sm.combo_label, True, ORANGE)
            cx = self.width // 2 - combo_surf.get_width() // 2
            self.screen.blit(combo_surf, (cx, 15))

    # ──────────────────────────────────────────────
    # Effets visuels
    # ──────────────────────────────────────────────

    def _draw_effects(self, game: GameManager) -> None:
        """Affiche les textes +points flottants."""
        for effect in game.slice_effects:
            t = effect["timer"]
            alpha = min(255, t * 6)
            y_offset = (40 - t) * 2   # monte vers le haut

            surf = self.font_medium.render(effect["text"], True, YELLOW)
            surf.set_alpha(alpha)
            x = effect["pos"][0] - surf.get_width() // 2
            y = effect["pos"][1] - y_offset
            self.screen.blit(surf, (x, y))

        # Flash de combo (overlay rouge subtil)
        if game.combo_flash_timer > 0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            a = int(60 * game.combo_flash_timer / 50)
            flash.fill((255, 100, 0, a))
            self.screen.blit(flash, (0, 0))

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _make_heart(self) -> pygame.Surface:
        """Dessine un cœur rouge 30×30 en pur Pygame (pas de sprite requis)."""
        size = 30
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Deux cercles + triangle
        r = size // 4
        pygame.draw.circle(surf, RED, (r,     r), r)
        pygame.draw.circle(surf, RED, (3 * r, r), r)
        pygame.draw.polygon(surf, RED, [
            (0,      r),
            (size,   r),
            (size // 2, size),
        ])
        return surf
