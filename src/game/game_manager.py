from __future__ import annotations

from typing import TYPE_CHECKING

from src.physics.physics_manager import PhysicsManager
from src.collisions.collision_manager import CollisionManager
from src.game.score_manager import ScoreManager
from src.game.level_manager import LevelManager
from src.fruits.fruit import FruitState

if TYPE_CHECKING:
    from src.blade.blade_tracker import BladeTracker


class GameState:
    IDLE    = "idle"
    PLAYING = "playing"
    OVER    = "over"


class GameManager:
    """
    Coordonne tous les sous-systèmes du jeu.

    Utilisation :
        game = GameManager(800, 600)
        game.start()
        while True:
            game.update(blade)
            if game.is_over(): ...
    """

    def __init__(self, width: int, height: int, difficulty: str = "normal") -> None:
        self.width  = width
        self.height = height
        self.difficulty = difficulty

        self.physics    = PhysicsManager(width, height)
        self.collisions = CollisionManager()
        self.score_manager = ScoreManager()
        self.level_manager = LevelManager(difficulty=difficulty)

        self._state = GameState.IDLE

        # Effets visuels temporaires (affichés par le renderer)
        self.slice_effects: list[dict] = []  # {"pos": (x,y), "timer": int, "text": str}
        self.combo_flash_timer = 0

        # Bombe en cours d'explosion : le Game Over est retardé jusqu'à
        # la fin de son animation (voir update()).
        self._exploding_bomb = None

    # ──────────────────────────────────────────────
    # Cycle de vie
    # ──────────────────────────────────────────────

    def start(self) -> None:
        self._state = GameState.PLAYING

    def restart(self) -> None:
        self.physics.clear()
        self.score_manager.reset()
        self.level_manager.reset()
        self.slice_effects.clear()
        self.combo_flash_timer = 0
        self._exploding_bomb = None
        self._state = GameState.PLAYING

    # ──────────────────────────────────────────────
    # Boucle principale (appelée chaque frame)
    # ──────────────────────────────────────────────

    def update(self, blade: "BladeTracker") -> None:
        if self._state != GameState.PLAYING:
            return

        # Une bombe explose : on laisse l'animation se terminer avant de
        # déclencher le vrai Game Over (pas de spawn ni de score entre-temps).
        if self._exploding_bomb is not None:
            self.physics.update()
            if self._exploding_bomb.state == FruitState.DEAD:
                self.score_manager.bomb_hit()
                self._exploding_bomb = None
                self._state = GameState.OVER
            return

        # 1. Mise à jour du niveau et spawn conditionnel
        self.physics.bomb_ratio = self.level_manager.bomb_ratio
        self.physics.speed_multiplier = self.level_manager.speed_multiplier
        should_spawn = self.level_manager.update(self.score_manager.score)
        if should_spawn:
            self.physics.spawn_wave(self.level_manager.wave_size)

        # 2. Physique (déplacements + suppression des objets hors écran)
        removed = self.physics.update()

        # 3. Détection de collisions
        result = self.collisions.check(blade, self.physics.objects, removed)

        # 4. Traitement du résultat

        # 4a. Fruits tranchés
        for fruit in result.sliced_fruits:
            earned = self.score_manager.add_slice(fruit.points)
            self.slice_effects.append({
                "pos":   (int(fruit.x), int(fruit.y)),
                "timer": 40,
                "text":  f"+{earned}" if earned > fruit.points else f"+{fruit.points}",
            })

        # 4b. Combo flash
        if result.sliced_fruits and self.score_manager.combo >= 3:
            self.combo_flash_timer = 50

        # 4c. Bombes : on ne perd pas les vies tout de suite, l'explosion
        # doit d'abord s'afficher (voir en haut de cette méthode).
        if result.bomb_hit:
            self._exploding_bomb = result.exploded_bombs[0]

        # 4d. Fruits manqués
        for _ in result.missed_fruits:
            self.score_manager.add_miss()

        # 5. Mise à jour score (combo timeout)
        self.score_manager.update()

        # 6. Mise à jour des effets visuels
        self.slice_effects = [
            {**e, "timer": e["timer"] - 1}
            for e in self.slice_effects
            if e["timer"] > 1
        ]
        if self.combo_flash_timer > 0:
            self.combo_flash_timer -= 1

        # 7. Vérification game over
        if self.score_manager.is_game_over:
            self._state = GameState.OVER

    # ──────────────────────────────────────────────
    # Accesseurs
    # ──────────────────────────────────────────────

    def is_over(self) -> bool:
        return self._state == GameState.OVER

    @property
    def objects(self):
        return self.physics.objects
