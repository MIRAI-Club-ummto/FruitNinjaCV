class LevelConfig:
    """Configuration d'un niveau."""

    def __init__(
        self,
        level: int,
        spawn_interval: int,   # frames entre chaque spawn
        wave_size: int,        # fruits par vague
        bomb_ratio: float,     # probabilité de bombe
        label: str,
    ) -> None:
        self.level          = level
        self.spawn_interval = spawn_interval
        self.wave_size      = wave_size
        self.bomb_ratio     = bomb_ratio
        self.label          = label


# Niveaux définis par seuil de score
_LEVELS = [
    LevelConfig(1, spawn_interval=120, wave_size=1, bomb_ratio=0.10, label="Ninja Débutant"),
    LevelConfig(2, spawn_interval=100, wave_size=2, bomb_ratio=0.12, label="Ninja Apprenti"),
    LevelConfig(3, spawn_interval=80,  wave_size=2, bomb_ratio=0.15, label="Ninja Confirmé"),
    LevelConfig(4, spawn_interval=60,  wave_size=3, bomb_ratio=0.18, label="Ninja Maître"),
    LevelConfig(5, spawn_interval=45,  wave_size=4, bomb_ratio=0.22, label="Grand Ninja"),
]
_SCORE_THRESHOLDS = [0, 15, 35, 60, 100]   # score minimum pour chaque niveau


# Difficulté choisie au menu : vient moduler la progression par score
# ci-dessus (spawn plus/moins fréquent, plus/moins de fruits, plus/moins
# de bombes, vitesse plus/moins élevée), sans dupliquer toute la table.
_DIFFICULTY_PRESETS = {
    "easy":   {"spawn_mult": 1.4,  "wave_bonus": 0, "bomb_mult": 0.5, "speed_mult": 0.75, "label": "Facile"},
    "normal": {"spawn_mult": 1.0,  "wave_bonus": 0, "bomb_mult": 1.0, "speed_mult": 1.0,  "label": "Intermédiaire"},
    "hard":   {"spawn_mult": 0.65, "wave_bonus": 1, "bomb_mult": 1.5, "speed_mult": 1.3,  "label": "Difficile"},
}
_MIN_SPAWN_INTERVAL = 15
_MAX_BOMB_RATIO = 0.4


class LevelManager:
    """Détermine le niveau courant (par score) et le timing de spawn,
    modulés par la difficulté choisie au menu."""

    def __init__(self, difficulty: str = "normal") -> None:
        self.difficulty = difficulty if difficulty in _DIFFICULTY_PRESETS else "normal"
        self._preset = _DIFFICULTY_PRESETS[self.difficulty]
        self._frame_counter = 0
        self.current_level  = _LEVELS[0]

    def update(self, score: int) -> bool:
        """
        Met à jour le niveau selon le score.
        Retourne True si un spawn doit avoir lieu cette frame.
        """
        # Recalcul du niveau
        lvl_idx = 0
        for i, threshold in enumerate(_SCORE_THRESHOLDS):
            if score >= threshold:
                lvl_idx = i
        self.current_level = _LEVELS[lvl_idx]

        # Timer de spawn (l'intervalle de base est modulé par la difficulté)
        spawn_interval = max(_MIN_SPAWN_INTERVAL,
                              int(self.current_level.spawn_interval * self._preset["spawn_mult"]))
        self._frame_counter += 1
        if self._frame_counter >= spawn_interval:
            self._frame_counter = 0
            return True
        return False

    def reset(self) -> None:
        """Réinitialise la progression, mais conserve la difficulté choisie."""
        self._frame_counter = 0
        self.current_level  = _LEVELS[0]

    @property
    def wave_size(self) -> int:
        return self.current_level.wave_size + self._preset["wave_bonus"]

    @property
    def bomb_ratio(self) -> float:
        return min(_MAX_BOMB_RATIO, self.current_level.bomb_ratio * self._preset["bomb_mult"])

    @property
    def speed_multiplier(self) -> float:
        return self._preset["speed_mult"]

    @property
    def level_label(self) -> str:
        return f"{self.current_level.label} — {self._preset['label']}"
