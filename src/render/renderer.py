from __future__ import annotations

from pathlib import Path
import pygame
import numpy as np
import cv2
import random
import math

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

        # ── Loading screen ─────────────────────────
        self.WIDTH = width
        self.HEIGHT = height
        self.clock = pygame.time.Clock()
        self.FPS = 60

        self.loading_fruits = []

        fruit_names = [
            "apple1.png",
            "banana1.png",
            "watermelon1.png",
            "orange1.png"
        ]

        for _ in range(8):

            name = random.choice(fruit_names)
            path = _IMAGES / name

            if not path.exists():
                continue

            image = pygame.image.load(
                str(path)
            ).convert_alpha()

            # Taille des fruits
            size = random.randint(45, 75)

            image = pygame.transform.smoothscale(
                image,
                (size, size)
            )

            self.loading_fruits.append({
                "image": image,
                "x": random.randint(20, width - 20),
                "y": random.randint(-height, -30),
                "speed": random.uniform(1.5, 3.5),
                "rotation": random.randint(0, 360),
                "rotation_speed": random.uniform(-3, 3)
            })

        pygame.mixer.init()

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

        # ── Polices du loading ─────────────────────
        if font_path.exists():
            self.TITLE_FONT = pygame.font.Font(
                "assets/fonts/static/Orbitron-Bold.ttf",
                70
            )
            self.TEXT_FONT = pygame.font.Font(
                "assets/fonts/static/Orbitron-Regular.ttf",
            28
            )
            self.SMALL_FONT = pygame.font.Font(
                "assets/fonts/static/Orbitron-Regular.ttf",
            18
            )
        else:
            self.TITLE_FONT = pygame.font.SysFont(
                "Arial", 60, bold=True
            )
            self.TEXT_FONT = pygame.font.SysFont(
                "Arial", 24
            )
            self.SMALL_FONT = pygame.font.SysFont(
                "Arial", 18
            )

        # Fond statique (fallback si pas de webcam)
        self._bg_surface: pygame.Surface | None = None
        bg_path = _IMAGES / "background.png"
        if bg_path.exists():
            bg = pygame.image.load(str(bg_path)).convert()
            self._bg_surface = pygame.transform.scale(bg, (width, height))

        # ── Background du loading ──────────────────
        loading_bg_path = _IMAGES / "loading_bg.jpg"

        if loading_bg_path.exists():

            loading_bg = pygame.image.load(
                str(loading_bg_path)
            ).convert()

            self.loading_background = pygame.transform.scale(
                loading_bg,
                (width, height)
            )

        elif self._bg_surface is not None:

            self.loading_background = self._bg_surface

        else:

            # Fallback obligatoire
            self.loading_background = pygame.Surface(
                (width, height)
            )

            self.loading_background.fill(
                (20, 20, 30)
            )

                # ── Logo ───────────────────────────────────
        logo_path = _IMAGES / "logo.png"

        if logo_path.exists():
            self.logo = pygame.image.load(
                str(logo_path)
            ).convert_alpha()
        else:
            self.logo = None

        # Cœurs (vies)
        self._heart_surf = self._make_heart()

    def load_sounds(self):

        pygame.mixer.music.load(
            "assets/sounds/intro.mp3"
        )

        pygame.mixer.music.set_volume(
            0.5
        )

    # FRUITS DU LOADING

    def _update_loading_fruits(self):

        for fruit in self.loading_fruits:

            # Descente
            fruit["y"] += fruit["speed"]

            # Rotation
            fruit["rotation"] += fruit["rotation_speed"]

            # Si le fruit sort de l'écran
            if fruit["y"] > self.HEIGHT + 80:

                fruit["y"] = random.randint(-150, -40)
                fruit["x"] = random.randint(
                    20,
                    self.WIDTH - 20
                )

                fruit["speed"] = random.uniform(
                    1.5,
                    3.5
                )

            # Rotation de l'image
            rotated = pygame.transform.rotate(
                fruit["image"],
                fruit["rotation"]
            )

            rect = rotated.get_rect(
                center=(
                    int(fruit["x"]),
                    int(fruit["y"])
                )
            )

            self.screen.blit(
                rotated,
                rect
            )

    def loading_screen(self):

        self.load_sounds()

        pygame.mixer.music.play(-1)

        loading_steps = [
            "Loading textures...",
            "Loading fruits...",
            "Loading fonts...",
            "Loading sounds...",
            "Initializing Renderer...",
            "Connecting Game Manager...",
            "Preparing UI...",
            "Ready..."
        ]

        progress = 0
        alpha = 0

        blink = True
        blink_timer = 0

        while True:

            self.clock.tick(self.FPS)

            # EVENTS

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    return False

                if progress >= 100:

                    if event.type == pygame.KEYDOWN:

                        if event.key == pygame.K_SPACE:
                            pygame.mixer.music.fadeout(800)
                            return True

            # BACKGROUND

            self.screen.blit(
                self.loading_background,
                (0, 0)
            )


            self._update_loading_fruits()

            # DARK OVERLAY

            overlay = pygame.Surface(
                (self.WIDTH, self.HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 115)
            )

            self.screen.blit(
                overlay,
                (0, 0)
            )

            # LOGO FADE

            if self.logo:

                if alpha < 255:
                    alpha += 4

                logo = self.logo.copy()

                logo.set_alpha(alpha)

                # On garde une taille raisonnable
                max_width = 250

                if logo.get_width() > max_width:

                    ratio = (
                        max_width /
                        logo.get_width()
                    )

                    logo = pygame.transform.smoothscale(
                        logo,
                        (
                            int(
                                logo.get_width()
                                * ratio
                            ),
                            int(
                                logo.get_height()
                                * ratio
                            )
                        )
                    )

                    logo.set_alpha(alpha)

                self.screen.blit(
                    logo,
                    logo.get_rect(
                        center=(
                            self.WIDTH // 2,
                            150
                        )
                    )
                )

            # TITLE

            title = self.TITLE_FONT.render(
                "FRUIT NINJA",
                True,
                WHITE
            )

            self.screen.blit(
                title,
                title.get_rect(
                    center=(
                        self.WIDTH // 2,
                        300
                    )
                )
            )

            # LOADING STEP

            if progress < 100:

                index = min(
                    len(loading_steps) - 1,
                    progress // 15
                )

                step = self.TEXT_FONT.render(
                    loading_steps[index],
                    True,
                    (225, 225, 225)
                )

            else:

                blink_timer += 1

                if blink_timer > 30:

                    blink = not blink

                    blink_timer = 0

                if blink:

                    step = self.TEXT_FONT.render(
                        "Press SPACE to Start",
                        True,
                        WHITE
                    )

                else:

                    step = self.TEXT_FONT.render(
                        "",
                        True,
                        WHITE
                    )

            self.screen.blit(
                step,
                step.get_rect(
                    center=(
                        self.WIDTH // 2,
                        390
                    )
                )
            )

            # PROGRESS BAR

            bar_width = 500
            bar_height = 26

            bar_x = (
                self.WIDTH - bar_width
            ) // 2

            bar_y = 445

            # Background
            pygame.draw.rect(
                self.screen,
                (45, 45, 45),
                (
                    bar_x,
                    bar_y,
                    bar_width,
                    bar_height
                ),
                border_radius=20
            )

            # Progress
            progress_width = int(
                bar_width * progress / 100
            )

            if progress_width > 0:

                pygame.draw.rect(
                    self.screen,
                    (45, 180, 255),
                    (
                        bar_x,
                        bar_y,
                        progress_width,
                        bar_height
                    ),
                    border_radius=20
                )

            # REFLECTION

            if progress < 100:

                shine_x = (
                    bar_x
                    + progress_width
                    - 25
                )

                if shine_x > bar_x:

                    pygame.draw.rect(
                        self.screen,
                        WHITE,
                        (
                            shine_x,
                            bar_y + 2,
                            18,
                            bar_height - 4
                        ),
                        border_radius=10
                    )

            # Border
            pygame.draw.rect(
                self.screen,
                WHITE,
                (
                    bar_x,
                    bar_y,
                    bar_width,
                    bar_height
                ),
                2,
                border_radius=20
            )

            # ──────────────────────────────────────
            # PERCENT

            percent = self.TEXT_FONT.render(
                f"{progress} %",
                True,
                WHITE
            )

            self.screen.blit(
                percent,
                percent.get_rect(
                    center=(
                        self.WIDTH // 2,
                        500
                    )
                )
            )

            # ──────────────────────────────────────
            # FOOTER
            # ──────────────────────────────────────

            footer = self.SMALL_FONT.render(
                "Powered by MIRAI Club UMMTO",
                True,
                (190, 190, 190)
            )

            self.screen.blit(
                footer,
                footer.get_rect(
                    center=(
                        self.WIDTH // 2,
                        self.HEIGHT - 25
                    )
                )
            )

            version = self.SMALL_FONT.render(
                "Version 1.0",
                True,
                (190, 190, 190)
            )

            self.screen.blit(
                version,
                (20, self.HEIGHT - 30)
            )

            # ──────────────────────────────────────
            # LOADING
            # ──────────────────────────────────────

            if progress < 100:
                progress += 1

            

            pygame.display.flip()


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
