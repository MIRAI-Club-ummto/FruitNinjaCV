import math
from collections import deque


class BladeTracker:
    """
    Mémorise les N dernières positions du bout du doigt.

    Attributs publics
    -----------------
    points      : deque des (x, y) récents (le plus récent en dernier)
    is_active   : True si une position a été reçue cette frame
    speed       : vitesse instantanée en px/frame
    """

    def __init__(self, max_points: int = 20,
                 min_slice_speed: float = 12.0) -> None:
        """
        Paramètres
        ----------
        max_points : int
            Longueur maximale de la traînée (influe sur l'effet visuel).
        min_slice_speed : float
            Vitesse minimale (px/frame) pour considérer que la lame est active.
        """
        self.max_points      = max_points
        self.min_slice_speed = min_slice_speed

        self.points: deque[tuple[int, int]] = deque(maxlen=max_points)
        self.is_active: bool  = False
        self.speed: float     = 0.0

    # ──────────────────────────────────────────────
    # Mise à jour
    # ──────────────────────────────────────────────

    def update(self, pos: tuple[int, int] | None) -> None:
        """
        Ajoute une nouvelle position.

        Paramètres
        ----------
        pos : (x, y) ou None si la main n'est pas détectée.
        """
        if pos is None:
            self.is_active = False
            self.speed     = 0.0
            # On vide progressivement la traînée pour un effet de disparition
            if self.points:
                self.points.popleft()
            return

        # Calcul de la vitesse instantanée
        if self.points:
            prev = self.points[-1]
            dx = pos[0] - prev[0]
            dy = pos[1] - prev[1]
            self.speed = math.hypot(dx, dy)
        else:
            self.speed = 0.0

        self.is_active = self.speed >= self.min_slice_speed
        self.points.append(pos)

    # ──────────────────────────────────────────────
    # Géométrie utile pour la collision
    # ──────────────────────────────────────────────

    def get_last_segment(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """
        Retourne le segment (p1, p2) formé par les deux derniers points.
        Retourne None si moins de 2 points disponibles.
        """
        if len(self.points) < 2:
            return None
        pts = list(self.points)
        return (pts[-2], pts[-1])

    def get_all_segments(self) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """
        Retourne tous les segments de la traînée.
        Utile pour dessiner la lame complète.
        """
        pts = list(self.points)
        return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]

    def get_tip(self) -> tuple[int, int] | None:
        """Retourne la position la plus récente ou None."""
        return self.points[-1] if self.points else None

    # ──────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────

    def clear(self) -> None:
        """Vide la traînée (ex. après un game over)."""
        self.points.clear()
        self.is_active = False
        self.speed     = 0.0

    def __len__(self) -> int:
        return len(self.points)
