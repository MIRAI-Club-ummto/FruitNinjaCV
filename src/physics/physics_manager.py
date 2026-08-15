from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.fruits.fruit import Fruit
from src.fruits.apple import Apple
from src.fruits.banana import Banana
from src.fruits.watermelon import Watermelon
from src.fruits.orange import Orange
from src.fruits.bomb import Bomb

if TYPE_CHECKING:
    pass


# ── Paramètres de spawn ──────────────────────────
_FRUIT_TYPES = [Apple, Banana, Watermelon, Orange]

# Probabilité relative de chaque type (indice identique)
_SPAWN_WEIGHTS = [0.30, 0.25, 0.20, 0.25]

# Vitesse verticale initiale (vers le haut -> négatif)
_VY_MIN = -18.0
_VY_MAX = -12.0

# Vitesse horizontale
_VX_ABS_MAX = 4.0


class PhysicsManager:
    """
    Responsable du spawn aléatoire et de la mise à jour physique des objets.

    Paramètres
    ----------
    screen_width, screen_height : dimensions de la fenêtre
    bomb_ratio : probabilité qu'un objet spawné soit une bombe (0-1)
    """

    def __init__(self,
                 screen_width: int,
                 screen_height: int,
                 bomb_ratio: float = 0.15) -> None:
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self.bomb_ratio    = bomb_ratio
        self.speed_multiplier = 1.0   # module la vitesse selon la difficulté

        self.objects: list[Fruit] = []

    # ──────────────────────────────────────────────
    # Spawn
    # ──────────────────────────────────────────────

    def spawn_fruit(self) -> Fruit:
        """Crée et ajoute un fruit ou une bombe aléatoire."""
        x  = random.randint(80, self.screen_width - 80)
        y  = self.screen_height + 10   # sous l'écran
        vx = random.uniform(-_VX_ABS_MAX, _VX_ABS_MAX) * self.speed_multiplier
        vy = random.uniform(_VY_MIN, _VY_MAX) * self.speed_multiplier

        if random.random() < self.bomb_ratio:
            obj: Fruit = Bomb(x, y, vx, vy)
        else:
            cls = random.choices(_FRUIT_TYPES, weights=_SPAWN_WEIGHTS, k=1)[0]
            obj = cls(x, y, vx, vy)

        self.objects.append(obj)
        return obj

    def spawn_wave(self, count: int) -> list[Fruit]:
        """Spawn plusieurs fruits d'un coup."""
        return [self.spawn_fruit() for _ in range(count)]

    # ──────────────────────────────────────────────
    # Mise à jour
    # ──────────────────────────────────────────────

    def update(self) -> list[Fruit]:
        """
        Met à jour tous les objets et supprime ceux qui sont morts.

        Retourne
        --------
        list[Fruit] : objets supprimés cette frame (utile pour les pénalités).
        """
        removed = []
        for obj in self.objects:
            obj.update(self.screen_height)

        dead = [o for o in self.objects if o.is_dead]
        self.objects = [o for o in self.objects if not o.is_dead]
        return dead

    # ──────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────

    def clear(self) -> None:
        self.objects.clear()

    def alive_count(self) -> int:
        return sum(1 for o in self.objects if o.is_alive)
