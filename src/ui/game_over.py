from __future__ import annotations

import math
from pathlib import Path

import pygame


# ==========================================================
# PATHS
# ==========================================================

_FONTS = Path(__file__).resolve().parents[2] / "assets" / "fonts"
_IMAGES = Path(__file__).resolve().parents[2] / "assets" / "images"


# ==========================================================
# COLORS
# ==========================================================

WHITE = (255, 255, 255)
RED = (235, 55, 55)
ORANGE = (255, 145, 40)
YELLOW = (255, 220, 80)
GRAY = (190, 190, 190)
DARK = (15, 15, 20)


# ==========================================================
# GAME OVER SCREEN
# ==========================================================

class GameOverScreen:

    def __init__(
        self,
        screen: pygame.Surface,
        width: int,
        height: int
    ) -> None:

        self.screen = screen
        self.width = width
        self.height = height

        # ==================================================
        # FONTS
        # ==================================================

        orbitron_bold = _FONTS / "static" / "Orbitron-Bold.ttf"
        orbitron_regular = _FONTS / "static" / "Orbitron-Regular.ttf"

        if orbitron_bold.exists():

            self.font_title = pygame.font.Font(
                str(orbitron_bold),
                64
            )

            self.font_score = pygame.font.Font(
                str(orbitron_bold),
                42
            )

            self.font_button = pygame.font.Font(
                str(orbitron_bold),
                20
            )

        else:

            self.font_title = pygame.font.SysFont(
                "Arial",
                64,
                bold=True
            )

            self.font_score = pygame.font.SysFont(
                "Arial",
                42,
                bold=True
            )

            self.font_button = pygame.font.SysFont(
                "Arial",
                20,
                bold=True
            )

        if orbitron_regular.exists():

            self.font_small = pygame.font.Font(
                str(orbitron_regular),
                16
            )

        else:

            self.font_small = pygame.font.SysFont(
                "Arial",
                16
            )

        # ==================================================
        # BACKGROUND
        # ==================================================

        bg_path = _IMAGES / "menu_background.png"

        if bg_path.exists():

            bg = pygame.image.load(
                str(bg_path)
            ).convert()

            self.background = pygame.transform.scale(
                bg,
                (width, height)
            )

        else:

            self.background = pygame.Surface(
                (width, height)
            )

            self.background.fill(DARK)

        # ==================================================
        # PANEL
        # ==================================================

        panel_width = 560
        panel_height = 470

        self.panel = pygame.Rect(
            (width - panel_width) // 2,
            (height - panel_height) // 2,
            panel_width,
            panel_height
        )

        # ==================================================
        # BUTTONS
        # ==================================================

        button_width = 270
        button_height = 52

        button_x = width // 2 - button_width // 2

        self.btn_restart = pygame.Rect(
            button_x,
            self.panel.bottom - 125,
            button_width,
            button_height
        )

        self.btn_menu = pygame.Rect(
            button_x,
            self.panel.bottom - 60,
            button_width,
            button_height
        )

        # ==================================================
        # ANIMATION
        # ==================================================

        self.anim = 0

    # ======================================================
    # BUTTON
    # ======================================================

    def _draw_button(
        self,
        text,
        rect,
        mouse_pos,
        primary=False
    ):

        hovered = rect.collidepoint(mouse_pos)

        # ==================================================
        # COLORS
        # ==================================================

        if primary:

            if hovered:
                bg_color = (255, 105, 60)
                border_color = (255, 190, 100)
            else:
                bg_color = (220, 70, 45)
                border_color = (255, 130, 70)

        else:

            if hovered:
                bg_color = (70, 70, 90)
                border_color = (170, 170, 190)
            else:
                bg_color = (45, 45, 60)
                border_color = (110, 110, 130)

        # ==================================================
        # GLOW
        # ==================================================

        if hovered:

            glow_surface = pygame.Surface(
                (rect.width + 24, rect.height + 24),
                pygame.SRCALPHA
            )

            pygame.draw.rect(
                glow_surface,
                (*border_color, 60),
                (12, 12, rect.width, rect.height),
                border_radius=15
            )

            self.screen.blit(
                glow_surface,
                (rect.x - 12, rect.y - 12)
            )

        # ==================================================
        # BUTTON BACKGROUND
        # ==================================================

        pygame.draw.rect(
            self.screen,
            bg_color,
            rect,
            border_radius=15
        )

        # ==================================================
        # BUTTON BORDER
        # ==================================================

        pygame.draw.rect(
            self.screen,
            border_color,
            rect,
            width=2,
            border_radius=15
        )

        # ==================================================
        # ICON
        # ==================================================

        icon_x = rect.x + 40
        icon_y = rect.centery

        # ==================================================
        # REPLAY ICON
        # ==================================================

        if primary:

            # Circular arrow

            pygame.draw.arc(
                self.screen,
                WHITE,
                (
                    icon_x - 12,
                    icon_y - 12,
                    24,
                    24
                ),
                math.radians(45),
                math.radians(320),
                3
            )

            # Arrow head

            points = [
                (icon_x + 10, icon_y - 10),
                (icon_x + 2, icon_y - 11),
                (icon_x + 9, icon_y - 3)
            ]

            pygame.draw.polygon(
                self.screen,
                WHITE,
                points
            )

        # ==================================================
        # MENU ICON
        # ==================================================

        else:

            # Roof

            roof = [
                (icon_x - 13, icon_y - 1),
                (icon_x, icon_y - 13),
                (icon_x + 13, icon_y - 1)
            ]

            pygame.draw.polygon(
                self.screen,
                WHITE,
                roof
            )

            # House body

            pygame.draw.rect(
                self.screen,
                WHITE,
                (
                    icon_x - 9,
                    icon_y - 1,
                    18,
                    13
                )
            )

            # Door

            pygame.draw.rect(
                self.screen,
                bg_color,
                (
                    icon_x - 3,
                    icon_y + 5,
                    6,
                    8
                )
            )

        # ==================================================
        # BUTTON TEXT
        # ==================================================

        text_surface = self.font_button.render(
            text,
            True,
            WHITE
        )

        text_rect = text_surface.get_rect(
            center=(
                rect.centerx + 15,
                rect.centery
            )
        )

        self.screen.blit(
            text_surface,
            text_rect
        )

    # ======================================================
    # LOOP
    # ======================================================

    def run(self, final_score: int) -> str:

        clock = pygame.time.Clock()

        while True:

            self.anim += 1

            mouse_pos = pygame.mouse.get_pos()

            # ==================================================
            # EVENTS
            # ==================================================

            for event in pygame.event.get():

                # Window close

                if event.type == pygame.QUIT:
                    return "quit"

                # Keyboard

                if event.type == pygame.KEYDOWN:

                    # Replay

                    if event.key in (
                        pygame.K_RETURN,
                        pygame.K_r
                    ):
                        return "restart"

                    # Menu

                    if event.key in (
                        pygame.K_m,
                        pygame.K_BACKSPACE
                    ):
                        return "menu"

                    # Quit

                    if event.key in (
                        pygame.K_ESCAPE,
                        pygame.K_q
                    ):
                        return "quit"

                # Mouse

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if self.btn_restart.collidepoint(mouse_pos):
                        return "restart"

                    if self.btn_menu.collidepoint(mouse_pos):
                        return "menu"

            # ==================================================
            # DRAW
            # ==================================================

            self._draw(
                final_score,
                mouse_pos
            )

            clock.tick(60)

    # ======================================================
    # DRAW EVERYTHING
    # ======================================================

    def _draw(
        self,
        score: int,
        mouse_pos: tuple[int, int]
    ) -> None:

        # ==================================================
        # BACKGROUND
        # ==================================================

        self.screen.blit(
            self.background,
            (0, 0)
        )

        # ==================================================
        # DARK OVERLAY
        # ==================================================

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 135)
        )

        self.screen.blit(
            overlay,
            (0, 0)
        )

        # ==================================================
        # PANEL
        # ==================================================

        panel_surface = pygame.Surface(
            self.panel.size,
            pygame.SRCALPHA
        )

        panel_surface.fill(
            (10, 10, 15, 215)
        )

        self.screen.blit(
            panel_surface,
            self.panel.topleft
        )

        # Panel border

        pygame.draw.rect(
            self.screen,
            (255, 255, 255, 70),
            self.panel,
            width=2,
            border_radius=22
        )

        # ==================================================
        # TITLE GLOW
        # ==================================================

        pulse = (
            math.sin(self.anim * 0.06) + 1
        ) / 2

        glow_alpha = int(
            50 + pulse * 70
        )

        glow = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        glow_text = self.font_title.render(
            "GAME OVER",
            True,
            (255, 60, 40)
        )

        glow_text.set_alpha(
            glow_alpha
        )

        glow_rect = glow_text.get_rect(
            center=(
                self.width // 2,
                self.panel.top + 75
            )
        )

        glow.blit(
            glow_text,
            glow_rect
        )

        self.screen.blit(
            glow,
            (0, 0)
        )

        # ==================================================
        # TITLE
        # ==================================================

        title = self.font_title.render(
            "GAME OVER",
            True,
            RED
        )

        title_rect = title.get_rect(
            center=(
                self.width // 2,
                self.panel.top + 75
            )
        )

        # Shadow

        shadow = self.font_title.render(
            "GAME OVER",
            True,
            (0, 0, 0)
        )

        self.screen.blit(
            shadow,
            (
                title_rect.x + 3,
                title_rect.y + 4
            )
        )

        self.screen.blit(
            title,
            title_rect
        )

        # ==================================================
        # DECORATIVE LINE
        # ==================================================

        line_width = 180

        pygame.draw.line(
            self.screen,
            ORANGE,
            (
                self.width // 2 - line_width // 2,
                self.panel.top + 125
            ),
            (
                self.width // 2 + line_width // 2,
                self.panel.top + 125
            ),
            3
        )

        # ==================================================
        # SCORE LABEL
        # ==================================================

        label = self.font_small.render(
            "FINAL SCORE",
            True,
            GRAY
        )

        self.screen.blit(
            label,
            label.get_rect(
                center=(
                    self.width // 2,
                    self.panel.top + 165
                )
            )
        )

        # ==================================================
        # SCORE
        # ==================================================

        score_text = self.font_score.render(
            str(score),
            True,
            YELLOW
        )

        self.screen.blit(
            score_text,
            score_text.get_rect(
                center=(
                    self.width // 2,
                    self.panel.top + 215
                )
            )
        )

        # ==================================================
        # BUTTONS
        # ==================================================

        self._draw_button(
            "REJOUER",
            self.btn_restart,
            mouse_pos,
            primary=True
        )

        self._draw_button(
            "MENU",
            self.btn_menu,
            mouse_pos,
            primary=False
        )

        # ==================================================
        # FOOTER
        # ==================================================

        footer = self.font_small.render(
            "ENTER : Rejouer     M : Menu     ESC : Quitter",
            True,
            (170, 170, 170)
        )

        self.screen.blit(
            footer,
            footer.get_rect(
                center=(
                    self.width // 2,
                    self.height - 18
                )
            )
        )

        # ==================================================
        # DISPLAY
        # ==================================================

        pygame.display.flip()
