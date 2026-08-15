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
    ALIVE     = auto()   # En l'air, intact
    SLICED    = auto()   # Sprite "tranché" affiché brièvement
    FALLING   = auto()   # Moitiés tombent après tranche (fallback sans sprite dédié)
    EXPLODING = auto()   # Bombe : explosion en cours (avant Game Over)
    DEAD      = auto()   # Hors écran ou expiré


# Chemin racine du projet (2 niveaux au-dessus de ce fichier)
_ASSETS = Path(__file__).resolve().parents[2] / "assets" / "images"


def _detect_background_gray_range(gray: np.ndarray, border: int = 3) -> tuple[float, float]:
    """Echantillonne une fine bordure de l'image (fond garanti) pour trouver
    la plage de gris du damier, quelle que soit l'image (adaptatif)."""
    h, w = gray.shape
    strip = np.concatenate([
        gray[0:border, :].ravel(), gray[h - border:h, :].ravel(),
        gray[:, 0:border].ravel(), gray[:, w - border:w].ravel(),
    ])
    lo, hi = np.percentile(strip, [0.5, 99.5])
    return max(0.0, lo - 6), min(255.0, hi + 6)


def _strip_checkerboard_alpha(bgr: np.ndarray) -> np.ndarray:
    """
    Certains assets exportés n'ont pas de vrai canal alpha : le "fond
    transparent" a été peint en damier gris opaque (pixels réels, pas de
    transparence). On détecte ce damier et on le convertit en vraie
    transparence, sans toucher au fichier source.

    Un pixel est considéré comme fond si :
      - il est peu saturé (gris neutre, comme le damier) ET
      - sa luminosité correspond à la plage détectée sur la bordure de
        l'image (garantie être du fond).
    On ne retire ensuite que les zones connectées suffisamment grandes
    (élimine le bruit, garde les vrais reflets/détails du sprite).
    """
    h, w = bgr.shape[:2]
    b, g, r = bgr[:, :, 0].astype(int), bgr[:, :, 1].astype(int), bgr[:, :, 2].astype(int)
    saturation = np.maximum(np.maximum(b, g), r) - np.minimum(np.minimum(b, g), r)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    lo, hi = _detect_background_gray_range(gray)

    candidate = ((saturation < 20) & (gray >= lo) & (gray <= hi)).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    cleaned = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel, iterations=2)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

    # Flood-fill depuis le bord de l'image : seules les zones réellement
    # reliées au fond (pas de simples reflets gris internes) sont effacées.
    flood_mask = np.zeros((h + 2, w + 2), np.uint8)
    seeds = []
    for x in range(0, w, max(1, w // 60)):
        seeds += [(x, 1), (x, h - 2)]
    for y in range(0, h, max(1, h // 60)):
        seeds += [(1, y), (w - 2, y)]
    for sx, sy in seeds:
        if cleaned[sy, sx] == 0 or flood_mask[sy + 1, sx + 1] != 0:
            continue
        cv2.floodFill(cleaned.copy(), flood_mask, (sx, sy), 0, 0, 0,
                      cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8))

    alpha = np.where(flood_mask[1:-1, 1:-1] > 0, 0, 255).astype(np.uint8)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha
    return bgra


def _crop_to_content(bgra: np.ndarray, pad: int = 6) -> np.ndarray:
    """Recadre l'image sur le sujet réellement visible (alpha > 0)."""
    ys, xs = np.where(bgra[:, :, 3] > 10)
    if len(xs) == 0:
        return bgra
    x0, x1 = max(0, xs.min() - pad), min(bgra.shape[1], xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), min(bgra.shape[0], ys.max() + pad)
    return bgra[y0:y1, x0:x1]


def _fit_into_square(bgra: np.ndarray, target: int) -> np.ndarray:
    """Redimensionne SANS déformer (proportions conservées), centré dans un
    canevas carré transparent de taille target x target."""
    h, w = bgra.shape[:2]
    if h == 0 or w == 0:
        return np.zeros((target, target, 4), dtype=np.uint8)
    scale = target / max(h, w)
    new_w, new_h = max(1, round(w * scale)), max(1, round(h * scale))
    resized = cv2.resize(bgra, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((target, target, 4), dtype=np.uint8)
    x_off = (target - new_w) // 2
    y_off = (target - new_h) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return canvas


def load_scaled_image(image_name: str, size: tuple[int, int]) -> "pygame.Surface | None":
    """
    Charge une image dans assets/images/, retire un éventuel damier de
    "fausse transparence" (voir _strip_checkerboard_alpha), recadre sur le
    sujet et le redimensionne SANS déformation dans un carré `size`.
    Retourne None si le fichier n'existe pas encore (fallback géré par l'appelant).
    """
    full_path = _ASSETS / image_name
    if not full_path.exists():
        return None

    bgr_or_bgra = cv2.imread(str(full_path), cv2.IMREAD_UNCHANGED)
    if bgr_or_bgra is None:
        return None
    if bgr_or_bgra.ndim == 2:
        bgr_or_bgra = cv2.cvtColor(bgr_or_bgra, cv2.COLOR_GRAY2BGR)

    if bgr_or_bgra.shape[2] == 4:
        # L'image a déjà un vrai canal alpha : rien à corriger.
        bgra = bgr_or_bgra
    else:
        bgra = _strip_checkerboard_alpha(bgr_or_bgra)

    bgra = _crop_to_content(bgra)
    target = max(size)
    bgra = _fit_into_square(bgra, target)

    rgba = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA)
    surface = pygame.image.frombuffer(rgba.tobytes(), (target, target), "RGBA")
    # La surface a deja un alpha correct par pixel ; convert_alpha() optimise
    # juste le format pour l'affichage courant, mais necessite un display
    # pygame initialise (absent par ex. dans les tests unitaires headless).
    try:
        return surface.convert_alpha()
    except pygame.error:
        return surface.copy()


class Fruit(ABC):
    """
    Classe de base pour un fruit.

    Paramètres
    ----------
    x, y       : position de spawn (pixels)
    vx, vy     : vélocités initiales (px/frame)
    radius     : rayon de collision (pixels)
    image_path : chemin vers le sprite PNG
    points     : score gagné quand tranché
    """

    # ── Physique globale ────────────────────────
    GRAVITY = 0.4          # px/frame² (accélération vers le bas)
    MAX_FALL_SPEED = 20.0  # vitesse verticale max

    # Durée d'affichage du sprite "tranché" avant disparition (~0.4s à 60 FPS)
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
        self.state  = FruitState.ALIVE

        # True uniquement si le fruit est sorti de l'écran ENCORE ALIVE
        # (jamais tranché). Sert a compter les fruits rates, car au moment
        # ou collision_manager regarde l'objet, son state est deja DEAD.
        self.missed = False

        # Rotation pour effet esthétique
        self.angle      = random.uniform(0, 360)
        self.rot_speed  = random.uniform(-4, 4)   # degrés/frame

        # Chargement du sprite entier
        diameter = radius * 2
        self.image_original = load_scaled_image(image_path, (diameter, diameter))
        # Si le sprite n'existe pas, on dessine un cercle coloré (fallback)

        # Chargement du sprite "tranché" dédié (ex: apple.png -> apple_sliced.png)
        stem, suffix = image_path.rsplit(".", 1)
        sliced_name = f"{stem}_sliced.{suffix}"
        self.image_sliced = load_scaled_image(sliced_name, (diameter, diameter))
        self._slice_timer = 0

        # Moitiés après tranche (fallback utilisé si image_sliced n'existe pas)
        self.half_left:  pygame.Surface | None = None
        self.half_right: pygame.Surface | None = None
        self._create_halves()

        # Position des moitiés
        self.hx_l, self.hy_l = x, y
        self.hx_r, self.hy_r = x, y
        self.hvy_l = self.hvy_r = -3.0
        self.hvx_l = -3.0
        self.hvx_r =  3.0

        # Timer pour supprimer les moitiés après quelques secondes
        self._death_timer = 0

    # ──────────────────────────────────────────────
    # Propriétés abstraites
    # ──────────────────────────────────────────────

    @property
    @abstractmethod
    def color(self) -> tuple[int, int, int]:
        """Couleur de fallback (si pas de sprite)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    # ──────────────────────────────────────────────
    # Physique
    # ──────────────────────────────────────────────

    def update(self, screen_height: int) -> None:
        """Met à jour la position selon l'état."""
        if self.state == FruitState.ALIVE:
            self._update_alive(screen_height)
        elif self.state == FruitState.SLICED:
            self._update_sliced(screen_height)
        elif self.state == FruitState.FALLING:
            self._update_falling(screen_height)

    def _update_sliced(self, screen_height: int) -> None:
        """Physique du sprite 'tranché' (une seule image, pas deux moitiés)."""
        self.vy = min(self.vy + self.GRAVITY, self.MAX_FALL_SPEED)
        self.x += self.vx
        self.y += self.vy
        self._slice_timer -= 1
        if self._slice_timer <= 0 or self.y > screen_height + self.radius * 2:
            self.state = FruitState.DEAD

    def _update_alive(self, screen_height: int) -> None:
        self.vy = min(self.vy + self.GRAVITY, self.MAX_FALL_SPEED)
        self.x += self.vx
        self.y += self.vy
        self.angle = (self.angle + self.rot_speed) % 360

        # Hors écran sans avoir été tranché -> rate
        if self.y > screen_height + self.radius * 2:
            self.missed = True
            self.state = FruitState.DEAD

    def _update_falling(self, screen_height: int) -> None:
        """Physique des deux moitiés après tranche."""
        self.hvy_l = min(self.hvy_l + self.GRAVITY, self.MAX_FALL_SPEED)
        self.hvy_r = min(self.hvy_r + self.GRAVITY, self.MAX_FALL_SPEED)
        self.hx_l += self.hvx_l
        self.hy_l += self.hvy_l
        self.hx_r += self.hvx_r
        self.hy_r += self.hvy_r

        self._death_timer += 1
        if (self._death_timer > 60 or
                self.hy_l > screen_height + 100 and
                self.hy_r > screen_height + 100):
            self.state = FruitState.DEAD

    # ──────────────────────────────────────────────
    # Tranche
    # ──────────────────────────────────────────────

    def slice(self) -> None:
        """
        Déclenche l'animation de tranche.
        - Si l'image "_sliced" existe déjà (assets fournis) : on l'affiche
          telle quelle pendant SLICE_DISPLAY_FRAMES puis le fruit disparaît.
        - Sinon (fallback MVP) : on découpe le sprite/cercle en deux moitiés
          qui tombent chacune de leur côté.
        Dans les deux cas, un seul objet physique reste (pas de duplication),
        donc pas de double collision / double score / double perte de vie.
        """
        if self.state != FruitState.ALIVE:
            return

        if self.image_sliced is not None:
            self.state = FruitState.SLICED
            self._slice_timer = self.SLICE_DISPLAY_FRAMES
            return

        self.state = FruitState.SLICED
        # Vitesse des moitiés = vitesse actuelle ± déflexion
        self.hvy_l = self.vy - 5
        self.hvy_r = self.vy - 5
        self.hvx_l = self.vx - 3
        self.hvx_r = self.vx + 3
        self.hx_l  = self.x
        self.hy_l  = self.y
        self.hx_r  = self.x
        self.hy_r  = self.y
        # Frame suivante : moitiés en chute libre
        self.state = FruitState.FALLING

    # ──────────────────────────────────────────────
    # Collision
    # ──────────────────────────────────────────────

    def is_hit_by_point(self, px: int, py: int) -> bool:
        """Test de collision simple point/cercle."""
        return self.state == FruitState.ALIVE and \
               math.hypot(px - self.x, py - self.y) <= self.radius

    def is_hit_by_segment(self,
                           p1: tuple[int, int],
                           p2: tuple[int, int]) -> bool:
        """
        Test de collision segment/cercle.
        Retourne True si le segment [p1->p2] passe à moins de radius du centre.
        """
        if self.state != FruitState.ALIVE:
            return False
        return _segment_circle_intersects(p1, p2, (self.x, self.y), self.radius)

    # ──────────────────────────────────────────────
    # Rendu
    # ──────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine le fruit, son sprite tranché ou ses moitiés selon l'état."""
        if self.state == FruitState.ALIVE:
            self._draw_whole(surface)
        elif self.state == FruitState.SLICED:
            self._draw_sliced(surface)
        elif self.state == FruitState.FALLING:
            self._draw_halves(surface)

    def _draw_sliced(self, surface: pygame.Surface) -> None:
        """Affiche l'image '_sliced' pendant la fin du timer, avec un léger fondu."""
        if not self.image_sliced:
            return
        alpha = 255
        if self._slice_timer < 8:
            alpha = max(0, int(255 * self._slice_timer / 8))
        img = self.image_sliced.copy()
        img.set_alpha(alpha)
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(img, rect)

    def _draw_whole(self, surface: pygame.Surface) -> None:
        if self.image_original:
            rotated = pygame.transform.rotate(self.image_original, self.angle)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)
        else:
            # Fallback : cercle coloré
            pygame.draw.circle(surface, self.color,
                                (int(self.x), int(self.y)), self.radius)

    def _draw_halves(self, surface: pygame.Surface) -> None:
        alpha = max(0, 255 - self._death_timer * 4)
        if self.half_left and self.half_right:
            # Moitié gauche
            hl = self.half_left.copy()
            hl.set_alpha(alpha)
            rect_l = hl.get_rect(center=(int(self.hx_l), int(self.hy_l)))
            surface.blit(hl, rect_l)
            # Moitié droite
            hr = self.half_right.copy()
            hr.set_alpha(alpha)
            rect_r = hr.get_rect(center=(int(self.hx_r), int(self.hy_r)))
            surface.blit(hr, rect_r)
        else:
            # Fallback
            c = (*self.color, alpha)
            half_surf = pygame.Surface((self.radius, self.radius * 2),
                                       pygame.SRCALPHA)
            pygame.draw.circle(half_surf, c,
                                (self.radius // 2, self.radius), self.radius)
            surface.blit(half_surf, (int(self.hx_l) - self.radius // 2,
                                     int(self.hy_l) - self.radius))
            surface.blit(half_surf, (int(self.hx_r) - self.radius // 2,
                                     int(self.hy_r) - self.radius))

    def _create_halves(self) -> None:
        """Découpe le sprite en deux moitiés verticales."""
        if not self.image_original:
            return
        w, h = self.image_original.get_size()
        self.half_left  = self.image_original.subsurface(pygame.Rect(0, 0, w // 2, h)).copy()
        self.half_right = self.image_original.subsurface(pygame.Rect(w // 2, 0, w - w // 2, h)).copy()

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @property
    def is_alive(self) -> bool:
        return self.state == FruitState.ALIVE

    @property
    def is_dead(self) -> bool:
        return self.state == FruitState.DEAD

    def __repr__(self) -> str:
        return f"<{self.name} x={self.x:.0f} y={self.y:.0f} state={self.state.name}>"


# ──────────────────────────────────────────────────────
# Géométrie : intersection segment / cercle
# ──────────────────────────────────────────────────────

def _segment_circle_intersects(
    p1: tuple[int, int],
    p2: tuple[int, int],
    center: tuple[float, float],
    radius: float,
) -> bool:
    """
    Retourne True si le segment [p1, p2] intersecte le cercle (center, radius).

    Algorithme : projection du centre sur la droite p1->p2,
    clamp sur le segment, puis test de distance.
    """
    ax, ay = p1
    bx, by = p2
    cx, cy = center

    abx, aby = bx - ax, by - ay
    acx, acy = cx - ax, cy - ay

    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq == 0:
        # Segment dégénéré (p1 == p2)
        return math.hypot(cx - ax, cy - ay) <= radius

    # Paramètre t de la projection (entre 0 et 1 sur le segment)
    t = max(0.0, min(1.0, (acx * abx + acy * aby) / ab_len_sq))

    # Point le plus proche sur le segment
    closest_x = ax + t * abx
    closest_y = ay + t * aby

    dist_sq = (cx - closest_x) ** 2 + (cy - closest_y) ** 2
    return dist_sq <= radius * radius
