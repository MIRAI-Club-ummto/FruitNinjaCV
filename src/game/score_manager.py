class ScoreManager:
    """
    Gère :
    - Le score courant
    - Le meilleur score de la session
    - Le combo (tranches consécutives rapides)
    - Le nombre de vies restantes
    """

    MAX_LIVES       = 3
    COMBO_TIMEOUT   = 90   # frames sans tranche pour réinitialiser le combo
    MISS_PENALTY    = 1    # vies perdues par fruit manqué

    def __init__(self) -> None:
        self.score      = 0
        self.best_score = 0
        self.lives      = self.MAX_LIVES
        self.combo      = 0
        self.max_combo  = 0
        self._combo_timer = 0

    # ──────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────

    def add_slice(self, base_points: int) -> int:
        """
        Enregistre une tranche et retourne les points effectivement marqués
        (avec multiplicateur de combo).
        """
        self.combo += 1
        self._combo_timer = self.COMBO_TIMEOUT
        self.max_combo = max(self.max_combo, self.combo)

        multiplier = self._combo_multiplier()
        earned = base_points * multiplier
        self.score += earned
        self.best_score = max(self.best_score, self.score)
        return earned

    def add_miss(self) -> None:
        """Un fruit a raté -> perd une vie et reset le combo."""
        self.lives = max(0, self.lives - self.MISS_PENALTY)
        self.combo = 0
        self._combo_timer = 0

    def bomb_hit(self) -> None:
        """Bombe touchée -> game over (vies = 0)."""
        self.lives = 0

    def update(self) -> None:
        """À appeler chaque frame pour gérer le timeout du combo."""
        if self._combo_timer > 0:
            self._combo_timer -= 1
            if self._combo_timer == 0:
                self.combo = 0

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _combo_multiplier(self) -> int:
        if self.combo >= 5:
            return 4
        if self.combo >= 3:
            return 2
        return 1

    def reset(self) -> None:
        self.score  = 0
        self.lives  = self.MAX_LIVES
        self.combo  = 0
        self.max_combo = 0
        self._combo_timer = 0

    @property
    def is_game_over(self) -> bool:
        return self.lives <= 0

    @property
    def combo_label(self) -> str:
        if self.combo >= 5:
            return "ULTRA COMBO x4!"
        if self.combo >= 3:
            return f"COMBO x2!"
        return ""
