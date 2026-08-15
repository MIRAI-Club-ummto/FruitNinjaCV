from __future__ import annotations

from typing import TYPE_CHECKING

from src.fruits.fruit import Fruit
from src.fruits.bomb import Bomb

if TYPE_CHECKING:
    from src.blade.blade_tracker import BladeTracker


class CollisionResult:
    """Résultat d'une frame de collision."""

    def __init__(self) -> None:
        self.sliced_fruits: list[Fruit] = []   # fruits tranchés
        self.exploded_bombs: list[Bomb] = []   # bombes touchées
        self.missed_fruits: list[Fruit] = []   # fruits tombés sans être tranchés

    @property
    def points_gained(self) -> int:
        return sum(f.points for f in self.sliced_fruits)

    @property
    def bomb_hit(self) -> bool:
        return len(self.exploded_bombs) > 0


class CollisionManager:
    """
    Vérifie toutes les collisions entre la lame et les objets physiques.

    La détection repose sur :
      - segment_circle_intersects() de fruit.py pour la précision
      - Un test rapide de distance max pour filtrer les candidats lointains
    """

    def __init__(self, blade_speed_required: bool = True) -> None:
        """
        Paramètres
        ----------
        blade_speed_required : bool
            Si True, la lame doit être en mouvement (is_active) pour trancher.
            Mettre False en mode debug uniquement.
        """
        self.blade_speed_required = blade_speed_required

    def check(self,
              blade: "BladeTracker",
              objects: list[Fruit],
              removed_objects: list[Fruit]) -> CollisionResult:
        """
        Paramètres
        ----------
        blade           : lame courante
        objects         : liste des objets actifs (vivants ou en chute)
        removed_objects : objets supprimés cette frame (sortis de l'écran)

        Retourne
        --------
        CollisionResult
        """
        result = CollisionResult()

        # Fruits tombés hors écran sans être tranchés.
        # ATTENTION : ces objets sont déjà à l'état DEAD ici (physics_manager
        # les a mis à jour avant ce check), donc on ne peut pas tester
        # obj.is_alive. On utilise le flag "missed", posé par le fruit
        # lui-même au moment exact où il sort de l'écran encore intact.
        for obj in removed_objects:
            if obj.missed and not isinstance(obj, Bomb):
                result.missed_fruits.append(obj)

        # Pas de lame active -> pas de tranche
        if self.blade_speed_required and not blade.is_active:
            return result

        segment = blade.get_last_segment()
        if segment is None:
            return result

        p1, p2 = segment

        for obj in objects:
            if not obj.is_alive:
                continue
            if obj.is_hit_by_segment(p1, p2):
                obj.slice()
                if isinstance(obj, Bomb):
                    result.exploded_bombs.append(obj)
                else:
                    result.sliced_fruits.append(obj)

        return result
