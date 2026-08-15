import pytest
from src.fruits.fruit import FruitState
from src.fruits.apple import Apple
from src.fruits.banana import Banana
from src.fruits.watermelon import Watermelon
from src.fruits.bomb import Bomb
from src.game.score_manager import ScoreManager
from src.game.level_manager import LevelManager
from src.physics.physics_manager import PhysicsManager


SCREEN_H = 600
SCREEN_W = 800


# ──────────────────────────────────────────────────
# Physique de base
# ──────────────────────────────────────────────────

class TestFruitPhysics:

    def test_fruit_falls_due_to_gravity(self):
        apple = Apple(400, 300, 0, -15)
        initial_y = apple.y
        for _ in range(10):
            apple.update(SCREEN_H)
        # Après 10 frames, la gravité doit ramener le fruit vers le bas
        assert apple.y != initial_y

    def test_fruit_dies_below_screen(self):
        apple = Apple(400, SCREEN_H + 100, 0, 5)
        apple.update(SCREEN_H)
        assert apple.state == FruitState.DEAD

    def test_fruit_alive_initially(self):
        for cls in [Apple, Banana, Watermelon, Bomb]:
            obj = cls(100, 100, 0, 0)
            assert obj.state == FruitState.ALIVE

    def test_slice_transitions_to_falling(self):
        apple = Apple(100, 100, 0, 0)
        apple.slice()
        # Avec le vrai sprite apple_sliced.png present, l'etat passe a
        # SLICED (affichage du sprite dedie) plutot qu'au fallback FALLING
        # (deux moities) qui ne sert que si l'image n'existe pas.
        expected = FruitState.SLICED if apple.image_sliced else FruitState.FALLING
        assert apple.state == expected

    def test_double_slice_no_effect(self):
        apple = Apple(100, 100, 0, 0)
        apple.slice()
        state_after_first = apple.state
        apple.slice()   # deuxième tranche -> pas de crash, pas de changement
        assert apple.state == state_after_first

    def test_is_alive_property(self):
        apple = Apple(100, 100, 0, 0)
        assert apple.is_alive is True
        apple.slice()
        assert apple.is_alive is False

    def test_is_dead_property(self):
        apple = Apple(400, SCREEN_H + 200, 0, 5)
        apple.update(SCREEN_H)
        assert apple.is_dead is True


# ──────────────────────────────────────────────────
# Points
# ──────────────────────────────────────────────────

class TestFruitPoints:

    def test_apple_worth_1(self):
        assert Apple(0, 0, 0, 0).points == 1

    def test_banana_worth_2(self):
        assert Banana(0, 0, 0, 0).points == 2

    def test_watermelon_worth_3(self):
        assert Watermelon(0, 0, 0, 0).points == 3

    def test_bomb_worth_0(self):
        assert Bomb(0, 0, 0, 0).points == 0


# ──────────────────────────────────────────────────
# ScoreManager
# ──────────────────────────────────────────────────

class TestScoreManager:

    def test_initial_score_zero(self):
        sm = ScoreManager()
        assert sm.score == 0

    def test_add_slice_increases_score(self):
        sm = ScoreManager()
        sm.add_slice(1)
        assert sm.score >= 1

    def test_combo_multiplier_x2_at_3(self):
        sm = ScoreManager()
        sm.add_slice(1)  # combo 1
        sm.add_slice(1)  # combo 2
        earned = sm.add_slice(1)  # combo 3 -> x2
        assert earned == 2

    def test_combo_multiplier_x4_at_5(self):
        sm = ScoreManager()
        for _ in range(4):
            sm.add_slice(1)
        earned = sm.add_slice(1)  # combo 5 -> x4
        assert earned == 4

    def test_miss_removes_life(self):
        sm = ScoreManager()
        initial = sm.lives
        sm.add_miss()
        assert sm.lives == initial - 1

    def test_bomb_hit_kills(self):
        sm = ScoreManager()
        sm.bomb_hit()
        assert sm.is_game_over is True

    def test_reset_restores_defaults(self):
        sm = ScoreManager()
        sm.add_slice(10)
        sm.add_miss()
        sm.reset()
        assert sm.score == 0
        assert sm.lives == ScoreManager.MAX_LIVES
        assert sm.combo == 0

    def test_best_score_tracks_maximum(self):
        sm = ScoreManager()
        sm.add_slice(5)
        best = sm.best_score
        sm.reset()
        # best_score ne se reset pas
        assert sm.best_score == best


# ──────────────────────────────────────────────────
# LevelManager
# ──────────────────────────────────────────────────

class TestLevelManager:

    def test_starts_at_level_1(self):
        lm = LevelManager()
        lm.update(0)
        assert lm.current_level.level == 1

    def test_level_increases_with_score(self):
        lm = LevelManager()
        lm.update(0)
        lv1 = lm.current_level.level
        lm.update(100)
        lv5 = lm.current_level.level
        assert lv5 > lv1

    def test_spawn_triggered_after_interval(self):
        lm = LevelManager()
        spawned = False
        for _ in range(200):
            if lm.update(0):
                spawned = True
                break
        assert spawned is True

    def test_reset_restores_frame_counter(self):
        lm = LevelManager()
        for _ in range(50):
            lm.update(0)
        lm.reset()
        assert lm._frame_counter == 0


# ──────────────────────────────────────────────────
# PhysicsManager
# ──────────────────────────────────────────────────

class TestPhysicsManager:

    def test_spawn_adds_object(self):
        pm = PhysicsManager(SCREEN_W, SCREEN_H)
        pm.spawn_fruit()
        assert len(pm.objects) == 1

    def test_spawn_wave_adds_multiple(self):
        pm = PhysicsManager(SCREEN_W, SCREEN_H)
        pm.spawn_wave(3)
        assert len(pm.objects) == 3

    def test_dead_objects_removed_on_update(self):
        pm = PhysicsManager(SCREEN_W, SCREEN_H)
        fruit = pm.spawn_fruit()
        fruit.state = fruit.state.__class__.DEAD  # forcer la mort
        from src.fruits.fruit import FruitState
        fruit.state = FruitState.DEAD
        pm.update()
        assert fruit not in pm.objects

    def test_clear_empties_list(self):
        pm = PhysicsManager(SCREEN_W, SCREEN_H)
        pm.spawn_wave(5)
        pm.clear()
        assert len(pm.objects) == 0
