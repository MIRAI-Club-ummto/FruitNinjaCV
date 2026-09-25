from __future__ import annotations

import math
import random
import cv2
import numpy as np
import pygame
from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path


class FruitState(Enum):
    ALIVE = auto()       # Fruit intact
    SLICED = auto()      # Ancien état pour compatibilité
    FALLING = auto()     # Les deux moitiés tombent après la tranche
    EXPLODING = auto()   # Bombe : explosion en cours
    DEAD = auto()        # Hors écran / terminé


# ============================================================
# CHEMIN DES ASSETS
# ============================================================

_ASSETS = Path(__file__).resolve().parents[2] / "assets" / "images"


# ============================================================
# TRANSPARENCE
# ============================================================

def _detect_background_gray_range(
    gray: np.ndarray,
    border: int = 3
) -> tuple[float, float]:

    h, w = gray.shape

    strip = np.concatenate([
        gray[0:border, :].ravel(),
        gray[h - border:h, :].ravel(),
        gray[:, 0:border].ravel(),
        gray[:, w - border:w].ravel(),
    ])

    lo, hi = np.percentile(strip, [0.5, 99.5])

    return max(0.0, lo - 6), min(255.0, hi + 6)


def _strip_checkerboard_alpha(bgr: np.ndarray) -> np.ndarray:
    """
    Transforme un faux fond en damier gris en vraie transparence.
    """

    h, w = bgr.shape[:2]

    b = bgr[:, :, 0].astype(int)
    g = bgr[:, :, 1].astype(int)
    r = bgr[:, :, 2].astype(int)

    saturation = (
        np.maximum(np.maximum(b, g), r)
        - np.minimum(np.minimum(b, g), r)
    )

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    lo, hi = _detect_background_gray_range(gray)

    candidate = (
        (saturation < 20)
        & (gray >= lo)
        & (gray <= hi)
    ).astype(np.uint8) * 255

    kernel = np.ones((5, 5), np.uint8)

    cleaned = cv2.morphologyEx(
        candidate,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    # Flood fill depuis les bords
    flood_mask = np.zeros((h + 2, w + 2), np.uint8)

    seeds = []

    for x in range(0, w, max(1, w // 60)):
        seeds += [(x, 1), (x, h - 2)]

    for y in range(0, h, max(1, h // 60)):
        seeds += [(1, y), (w - 2, y)]

    for sx, sy in seeds:

        if (
            cleaned[sy, sx] == 0
            or flood_mask[sy + 1, sx + 1] != 0
        ):
            continue

        cv2.floodFill(
            cleaned.copy(),
            flood_mask,
            (sx, sy),
            0,
            0,
            0,
            cv2.FLOODFILL_MASK_ONLY
            | cv2.FLOODFILL_FIXED_RANGE
            | (255 << 8)
        )

    alpha = np.where(
        flood_mask[1:-1, 1:-1] > 0,
        0,
        255
    ).astype(np.uint8)

    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha

    return bgra


def _crop_to_content(
    bgra: np.ndarray,
    pad: int = 6
) -> np.ndarray:
    """
    Recadre l'image autour du contenu visible.
    """

    ys, xs = np.where(bgra[:, :, 3] > 10)

    if len(xs) == 0:
        return bgra

    x0 = max(0, xs.min() - pad)
    x1 = min(bgra.shape[1], xs.max() + pad)

    y0 = max(0, ys.min() - pad)
    y1 = min(bgra.shape[0], ys.max() + pad)

    return bgra[y0:y1, x0:x1]


def _fit_into_square(
    bgra: np.ndarray,
    target: int
) -> np.ndarray:
    """
    Redimensionne sans déformer et place dans un carré transparent.
    """

    h, w = bgra.shape[:2]

    if h == 0 or w == 0:
        return np.zeros(
            (target, target, 4),
            dtype=np.uint8
        )

    scale = target / max(h, w)

    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))

    resized = cv2.resize(
        bgra,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    canvas = np.zeros(
        (target, target, 4),
        dtype=np.uint8
    )

    x_off = (target - new_w) // 2
    y_off = (target - new_h) // 2

    canvas[
        y_off:y_off + new_h,
        x_off:x_off + new_w
    ] = resized

    return canvas


# ============================================================
# CHARGEMENT DES IMAGES
# ============================================================

def load_scaled_image(
    image_name: str,
    size: tuple[int, int]
) -> "pygame.Surface | None":

    full_path = _ASSETS / image_name

    if not full_path.exists():
        return None

    bgr_or_bgra = cv2.imread(
        str(full_path),
        cv2.IMREAD_UNCHANGED
    )

    if bgr_or_bgra is None:
        return None

    if bgr_or_bgra.ndim == 2:
        bgr_or_bgra = cv2.cvtColor(
            bgr_or_bgra,
            cv2.COLOR_GRAY2BGR
        )

    if bgr_or_bgra.shape[2] == 4:

        # Déjà transparent
        bgra = bgr_or_bgra

    else:

        # Faux damier éventuel
        bgra = _strip_checkerboard_alpha(
            bgr_or_bgra
        )

    bgra = _crop_to_content(bgra)

    target = max(size)

    bgra = _fit_into_square(
        bgra,
        target
    )

    rgba = cv2.cvtColor(
        bgra,
        cv2.COLOR_BGRA2RGBA
    )

    surface = pygame.image.frombuffer(
        rgba.tobytes(),
        (target, target),
        "RGBA"
    )

    try:
        return surface.convert_alpha()

    except pygame.error:
        return surface.copy()


# ============================================================
# FRUIT
# ============================================================

class Fruit(ABC):

    GRAVITY = 0.4
    MAX_FALL_SPEED = 20.0

    # Ancien système de sprite sliced
    SLICE_DISPLAY_FRAMES = 24

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        radius: int,
        image_path: str,
        points: int = 1,
    ) -> None:

        self.x = x
        self.y = y

        self.vx = vx
        self.vy = vy

        self.radius = radius
        self.points = points

        self.state = FruitState.ALIVE

        # True si le fruit sort de l'écran intact
        self.missed = False

        # ====================================================
        # ROTATION DU FRUIT ENTIER
        # ====================================================

        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-4, 4)

        # ====================================================
        # IMAGE ORIGINALE
        # ====================================================

        diameter = radius * 2

        self.image_original = load_scaled_image(
            image_path,
            (diameter, diameter)
        )

        # ====================================================
        # NOUVEAU SYSTÈME :
        #
        # apple.png
        # apple_left.png
        # apple_right.png
 
        #
        # etc.
        # ====================================================

        stem, suffix = image_path.rsplit(".", 1)

        left_name = f"{stem}_left.{suffix}"
        right_name = f"{stem}_right.{suffix}"

        self.half_left = load_scaled_image(
            left_name,
            (diameter, diameter)
        )

        self.half_right = load_scaled_image(
            right_name,
            (diameter, diameter)
        )

        # ====================================================
        # ANCIEN SYSTÈME _sliced
        #
        # Gardé uniquement comme fallback.
        # ====================================================

        self.image_sliced = None

        if not (
            self.half_left is not None
            and self.half_right is not None
        ):

            sliced_name = (
                f"{stem}_sliced.{suffix}"
            )

            self.image_sliced = load_scaled_image(
                sliced_name,
                (diameter, diameter)
            )

        self._slice_timer = 0

        # ====================================================
        # POSITIONS DES MOITIÉS
        # ====================================================

        self.hx_l = x
        self.hy_l = y

        self.hx_r = x
        self.hy_r = y

        # Vitesses des morceaux
        self.hvy_l = -3.0
        self.hvy_r = -3.0

        self.hvx_l = -3.0
        self.hvx_r = 3.0

        # ====================================================
        # ROTATION DES MOITIÉS
        # ====================================================

        self.hangle_l = random.uniform(
            -10,
            10
        )

        self.hangle_r = random.uniform(
            -10,
            10
        )

        self.hrot_speed_l = random.uniform(
            -6,
            -2
        )

        self.hrot_speed_r = random.uniform(
            2,
            6
        )

        # ====================================================
        # TIMER DE DISPARITION
        # ====================================================

        self._death_timer = 0

        # ====================================================
        # FALLBACK :
        # si aucun left/right n'existe,
        # on coupe l'image originale.
        # ====================================================

        if (
            self.half_left is None
            or self.half_right is None
        ):

            self._create_fallback_halves()

    # ========================================================
    # PROPRIÉTÉS ABSTRAITES
    # ========================================================

    @property
    @abstractmethod
    def color(self) -> tuple[int, int, int]:
        """Couleur utilisée si le sprite n'existe pas."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        screen_height: int
    ) -> None:

        if self.state == FruitState.ALIVE:

            self._update_alive(
                screen_height
            )

        elif self.state == FruitState.SLICED:

            self._update_sliced(
                screen_height
            )

        elif self.state == FruitState.FALLING:

            self._update_falling(
                screen_height
            )

    # ========================================================
    # FRUIT SLICED LEGACY
    # ========================================================

    def _update_sliced(
        self,
        screen_height: int
    ) -> None:

        self.vy = min(
            self.vy + self.GRAVITY,
            self.MAX_FALL_SPEED
        )

        self.x += self.vx
        self.y += self.vy

        self._slice_timer -= 1

        if (
            self._slice_timer <= 0
            or self.y > screen_height + self.radius * 2
        ):

            self.state = FruitState.DEAD

    # ========================================================
    # FRUIT NORMAL
    # ========================================================

    def _update_alive(
        self,
        screen_height: int
    ) -> None:

        self.vy = min(
            self.vy + self.GRAVITY,
            self.MAX_FALL_SPEED
        )

        self.x += self.vx
        self.y += self.vy

        self.angle = (
            self.angle + self.rot_speed
        ) % 360

        # Fruit raté
        if self.y > screen_height + self.radius * 2:

            self.missed = True
            self.state = FruitState.DEAD

    # ========================================================
    # MOITIÉS QUI TOMBENT
    # ========================================================

    def _update_falling(
        self,
        screen_height: int
    ) -> None:

        # Gravité gauche
        self.hvy_l = min(
            self.hvy_l + self.GRAVITY,
            self.MAX_FALL_SPEED
        )

        # Gravité droite
        self.hvy_r = min(
            self.hvy_r + self.GRAVITY,
            self.MAX_FALL_SPEED
        )

        # Positions
        self.hx_l += self.hvx_l
        self.hy_l += self.hvy_l

        self.hx_r += self.hvx_r
        self.hy_r += self.hvy_r

        # Rotation
        self.hangle_l += self.hrot_speed_l
        self.hangle_r += self.hrot_speed_r

        # Fade / disparition
        self._death_timer += 1

        if (
            self._death_timer > 70
            or (
                self.hy_l > screen_height + 100
                and self.hy_r > screen_height + 100
            )
        ):

            self.state = FruitState.DEAD

    # ========================================================
    # TRANCHE
    # ========================================================

    def slice(self) -> None:
        """
        Coupe le fruit.

        Priorité :
        1. image_left + image_right
        2. image_sliced
        3. découpe automatique de l'image originale
        """

        if self.state != FruitState.ALIVE:
            return

        # ====================================================
        # NOUVEAU SYSTÈME LEFT / RIGHT
        # ====================================================

        if (
            self.half_left is not None
            and self.half_right is not None
        ):

            # Vitesses basées sur la vitesse actuelle
            self.hvy_l = self.vy - 5
            self.hvy_r = self.vy - 5

            # Séparation horizontale
            self.hvx_l = self.vx - 3.5
            self.hvx_r = self.vx + 3.5

            # Positions initiales
            self.hx_l = self.x - 4
            self.hy_l = self.y

            self.hx_r = self.x + 4
            self.hy_r = self.y

            # Reset rotation
            self.hangle_l = self.angle
            self.hangle_r = self.angle

            # Petit effet de rotation opposée
            self.hrot_speed_l = random.uniform(
                -7,
                -3
            )

            self.hrot_speed_r = random.uniform(
                3,
                7
            )

            self._death_timer = 0

            # Les deux morceaux commencent à tomber
            self.state = FruitState.FALLING

            return

        # ====================================================
        # ANCIEN SPRITE _SLICED
        # ====================================================

        if self.image_sliced is not None:

            self.state = FruitState.SLICED

            self._slice_timer = (
                self.SLICE_DISPLAY_FRAMES
            )

            return

        # ====================================================
        # FALLBACK
        # ====================================================

        self.hvy_l = self.vy - 5
        self.hvy_r = self.vy - 5

        self.hvx_l = self.vx - 3
        self.hvx_r = self.vx + 3

        self.hx_l = self.x
        self.hy_l = self.y

        self.hx_r = self.x
        self.hy_r = self.y

        self._death_timer = 0

        self.state = FruitState.FALLING

    # ========================================================
    # COLLISION
    # ========================================================

    def is_hit_by_point(
        self,
        px: int,
        py: int
    ) -> bool:

        return (
            self.state == FruitState.ALIVE
            and math.hypot(
                px - self.x,
                py - self.y
            ) <= self.radius
        )

    def is_hit_by_segment(
        self,
        p1: tuple[int, int],
        p2: tuple[int, int]
    ) -> bool:

        if self.state != FruitState.ALIVE:
            return False

        return _segment_circle_intersects(
            p1,
            p2,
            (self.x, self.y),
            self.radius
        )

    # ========================================================
    # DRAW
    # ========================================================

    def draw(
        self,
        surface: pygame.Surface
    ) -> None:

        if self.state == FruitState.ALIVE:

            self._draw_whole(surface)

        elif self.state == FruitState.SLICED:

            self._draw_sliced(surface)

        elif self.state == FruitState.FALLING:

            self._draw_halves(surface)

    # ========================================================
    # DRAW SLICED LEGACY
    # ========================================================

    def _draw_sliced(
        self,
        surface: pygame.Surface
    ) -> None:

        if not self.image_sliced:
            return

        alpha = 255

        if self._slice_timer < 8:

            alpha = max(
                0,
                int(
                    255
                    * self._slice_timer
                    / 8
                )
            )

        img = self.image_sliced.copy()

        img.set_alpha(alpha)

        rect = img.get_rect(
            center=(
                int(self.x),
                int(self.y)
            )
        )

        surface.blit(
            img,
            rect
        )

    # ========================================================
    # DRAW FRUIT ENTIER
    # ========================================================

    def _draw_whole(
        self,
        surface: pygame.Surface
    ) -> None:

        if self.image_original:

            rotated = pygame.transform.rotate(
                self.image_original,
                self.angle
            )

            rect = rotated.get_rect(
                center=(
                    int(self.x),
                    int(self.y)
                )
            )

            surface.blit(
                rotated,
                rect
            )

        else:

            pygame.draw.circle(
                surface,
                self.color,
                (
                    int(self.x),
                    int(self.y)
                ),
                self.radius
            )

    # ========================================================
    # DRAW DES DEUX MOITIÉS
    # ========================================================

    def _draw_halves(
        self,
        surface: pygame.Surface
    ) -> None:

        # Fade progressif
        alpha = max(
            0,
            255 - self._death_timer * 4
        )

        if (
            self.half_left
            and self.half_right
        ):

            # ------------------------------------------------
            # MOITIÉ GAUCHE
            # ------------------------------------------------

            hl = pygame.transform.rotate(
                self.half_left,
                self.hangle_l
            )

            hl.set_alpha(alpha)

            rect_l = hl.get_rect(
                center=(
                    int(self.hx_l),
                    int(self.hy_l)
                )
            )

            surface.blit(
                hl,
                rect_l
            )

            # ------------------------------------------------
            # MOITIÉ DROITE
            # ------------------------------------------------

            hr = pygame.transform.rotate(
                self.half_right,
                self.hangle_r
            )

            hr.set_alpha(alpha)

            rect_r = hr.get_rect(
                center=(
                    int(self.hx_r),
                    int(self.hy_r)
                )
            )

            surface.blit(
                hr,
                rect_r
            )

        else:

            # ------------------------------------------------
            # FALLBACK VISUEL
            # ------------------------------------------------

            c = (
                *self.color,
                alpha
            )

            half_surf = pygame.Surface(
                (
                    self.radius,
                    self.radius * 2
                ),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                half_surf,
                c,
                (
                    self.radius // 2,
                    self.radius
                ),
                self.radius
            )

            surface.blit(
                half_surf,
                (
                    int(self.hx_l)
                    - self.radius // 2,
                    int(self.hy_l)
                    - self.radius
                )
            )

            surface.blit(
                half_surf,
                (
                    int(self.hx_r)
                    - self.radius // 2,
                    int(self.hy_r)
                    - self.radius
                )
            )

    # ========================================================
    # FALLBACK : DÉCOUPAGE AUTOMATIQUE
    # ========================================================

    def _create_fallback_halves(
        self
    ) -> None:

        if not self.image_original:
            return

        w, h = (
            self.image_original.get_size()
        )

        self.half_left = (
            self.image_original
            .subsurface(
                pygame.Rect(
                    0,
                    0,
                    w // 2,
                    h
                )
            )
            .copy()
        )

        self.half_right = (
            self.image_original
            .subsurface(
                pygame.Rect(
                    w // 2,
                    0,
                    w - w // 2,
                    h
                )
            )
            .copy()
        )

    # ========================================================
    # PROPRIÉTÉS
    # ========================================================

    @property
    def is_alive(self) -> bool:

        return (
            self.state == FruitState.ALIVE
        )

    @property
    def is_dead(self) -> bool:

        return (
            self.state == FruitState.DEAD
        )

    def __repr__(self) -> str:

        return (
            f"<{self.name} "
            f"x={self.x:.0f} "
            f"y={self.y:.0f} "
            f"state={self.state.name}>"
        )


# ============================================================
# GÉOMÉTRIE : SEGMENT / CERCLE
# ============================================================

def _segment_circle_intersects(
    p1: tuple[int, int],
    p2: tuple[int, int],
    center: tuple[float, float],
    radius: float,
) -> bool:

    ax, ay = p1
    bx, by = p2

    cx, cy = center

    abx = bx - ax
    aby = by - ay

    acx = cx - ax
    acy = cy - ay

    ab_len_sq = (
        abx * abx
        + aby * aby
    )

    if ab_len_sq == 0:

        return (
            math.hypot(
                cx - ax,
                cy - ay
            )
            <= radius
        )

    t = max(
        0.0,
        min(
            1.0,
            (
                acx * abx
                + acy * aby
            )
            / ab_len_sq
        )
    )

    closest_x = ax + t * abx
    closest_y = ay + t * aby

    dist_sq = (
        (cx - closest_x) ** 2
        + (cy - closest_y) ** 2
    )

    return dist_sq <= radius * radius
