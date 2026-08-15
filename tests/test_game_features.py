import pytest

from src.game.level_manager import LevelManager
from src.game.score_manager import ScoreManager
from src.game.game_manager import GameManager, GameState
from src.fruits.apple import Apple
from src.fruits.bomb import Bomb
from src.fruits.fruit import FruitState


# ──────────────────────────────────────────────────
# Difficulté
# ──────────────────────────────────────────────────

class TestDifficulty:

    def test_default_difficulty_is_normal(self):
        lm = LevelManager()
        assert lm.difficulty == "normal"

    def test_unknown_difficulty_falls_back_to_normal(self):
        lm = LevelManager(difficulty="nawak")
        assert lm.difficulty == "normal"

    def test_easy_spawns_less_often_than_hard(self):
        easy = LevelManager(difficulty="easy")
        hard = LevelManager(difficulty="hard")
        easy.update(0)
        hard.update(0)
        easy_interval = easy.current_level.spawn_interval * easy._preset["spawn_mult"]
        hard_interval = hard.current_level.spawn_interval * hard._preset["spawn_mult"]
        assert easy_interval > hard_interval

    def test_hard_has_more_bombs_than_easy(self):
        easy = LevelManager(difficulty="easy")
        hard = LevelManager(difficulty="hard")
        easy.update(0)
        hard.update(0)
        assert hard.bomb_ratio > easy.bomb_ratio

    def test_reset_keeps_difficulty(self):
        lm = LevelManager(difficulty="hard")
        lm.update(50)
        lm.reset()
        assert lm.difficulty == "hard"


# ──────────────────────────────────────────────────
# Fruit compté une seule fois
# ──────────────────────────────────────────────────

class TestFruitCountedOnce:

    def test_slice_prevents_second_slice_effect(self):
        apple = Apple(100, 100, 0, 0)
        apple.slice()
        state_after_first = apple.state
        apple.slice()  # deuxième appel : ne doit rien changer
        assert apple.state == state_after_first

    def test_sliced_fruit_no_longer_hittable(self):
        apple = Apple(100, 100, 0, 0)
        apple.slice()
        assert apple.is_hit_by_point(100, 100) is False


# ──────────────────────────────────────────────────
# GameManager : bombe -> game over différé
# ──────────────────────────────────────────────────

class TestGameManagerBomb:

    def test_bomb_hit_triggers_game_over_after_explosion(self):
        game = GameManager(800, 600, difficulty="normal")
        game.start()
        bomb = Bomb(100, 100, 0, 0)
        game.physics.objects.append(bomb)
        bomb.slice()  # simule une collision détectée
        game._exploding_bomb = bomb

        class DummyBlade:
            is_active = False
            def get_last_segment(self):
                return None

        # Tant que l'explosion joue, pas encore de Game Over
        for _ in range(bomb.EXPLOSION_DURATION - 1):
            game.update(DummyBlade())
        assert game.is_over() is False

        # Une fois l'explosion terminée, le Game Over est déclenché
        game.update(DummyBlade())
        assert game.is_over() is True
        assert game.score_manager.lives == 0

    def test_no_spawn_while_bomb_exploding(self):
        game = GameManager(800, 600, difficulty="normal")
        game.start()
        bomb = Bomb(100, 100, 0, 0)
        bomb.slice()
        game._exploding_bomb = bomb
        objects_before = list(game.physics.objects)

        class DummyBlade:
            is_active = False
            def get_last_segment(self):
                return None

        game.update(DummyBlade())
        # Aucun nouvel objet n'a été ajouté pendant l'explosion
        assert len(game.physics.objects) <= len(objects_before)


# ──────────────────────────────────────────────────
# GameManager : vies à zéro -> game over
# ──────────────────────────────────────────────────

class TestGameOver:

    def test_game_over_when_lives_reach_zero(self):
        sm = ScoreManager()
        sm.add_miss()
        sm.add_miss()
        sm.add_miss()
        assert sm.is_game_over is True

    def test_restart_clears_game_over_state(self):
        game = GameManager(800, 600)
        game.start()
        game.score_manager.lives = 0
        game._state = GameState.OVER
        game.restart()
        assert game.is_over() is False
        assert game.score_manager.lives == ScoreManager.MAX_LIVES


# ──────────────────────────────────────────────────
# Vies : chaîne complète fruit raté -> perte de vie
# (régression du bug où missed_fruits restait toujours vide)
# ──────────────────────────────────────────────────

class DummyBlade:
    def __init__(self, active=False, seg=None):
        self.is_active = active
        self._seg = seg

    def get_last_segment(self):
        return self._seg


class TestMissedFruitLosesLife:

    def test_missed_fruit_removes_one_life(self):
        game = GameManager(800, 600, difficulty="normal")
        game.start()
        apple = Apple(400, 550, 0, 20)
        game.physics.objects.append(apple)
        blade = DummyBlade(active=False)
        for _ in range(50):
            game.update(blade)
            if apple.state == FruitState.DEAD:
                break
        assert game.score_manager.lives == ScoreManager.MAX_LIVES - 1

    def test_three_missed_fruits_trigger_game_over(self):
        game = GameManager(800, 600, difficulty="normal")
        game.start()
        blade = DummyBlade(active=False)
        for _ in range(3):
            apple = Apple(400, 550, 0, 20)
            game.physics.objects.append(apple)
            for _ in range(50):
                game.update(blade)
                if apple.state == FruitState.DEAD:
                    break
        assert game.score_manager.lives == 0
        assert game.is_over() is True

    def test_sliced_fruit_leaving_screen_does_not_lose_life(self):
        game = GameManager(800, 600, difficulty="normal")
        game.start()
        apple = Apple(400, 300, 0, 5)
        game.physics.objects.append(apple)
        game.update(DummyBlade(active=True, seg=((350, 300), (450, 300))))
        lives_before = game.score_manager.lives
        for _ in range(100):
            game.update(DummyBlade(active=False))
            if apple.state == FruitState.DEAD:
                break
        assert game.score_manager.lives == lives_before

    def test_missed_bomb_does_not_lose_life(self):
        game = GameManager(800, 600, difficulty="normal")
        game.start()
        bomb = Bomb(400, 550, 0, 20)
        game.physics.objects.append(bomb)
        lives_before = game.score_manager.lives
        for _ in range(50):
            game.update(DummyBlade(active=False))
            if bomb.state == FruitState.DEAD:
                break
        assert game.score_manager.lives == lives_before


# ──────────────────────────────────────────────────
# Transparence des sprites (damier -> vraie transparence)
# ──────────────────────────────────────────────────

class TestSpriteTransparency:

    def test_apple_sprite_has_real_alpha_channel(self):
        apple = Apple(100, 100, 0, 0)
        assert apple.image_original is not None
        assert apple.image_original.get_flags() & 65536 != 0 or \
            apple.image_original.get_masks()[3] != 0  # canal alpha present

    def test_apple_sprite_not_fully_opaque(self):
        # Le damier occupait la majorite de l'image : une fois nettoye,
        # une bonne partie du sprite carre doit etre transparente
        # (le fruit rond ne remplit pas tout le carre).
        apple = Apple(100, 100, 0, 0)
        surf = apple.image_original
        transparent = 0
        total = 0
        for x in range(0, surf.get_width(), 4):
            for y in range(0, surf.get_height(), 4):
                total += 1
                if surf.get_at((x, y))[3] < 10:
                    transparent += 1
        assert transparent / total > 0.15

    def test_sprite_size_matches_requested_diameter(self):
        apple = Apple(100, 100, 0, 0)
        diameter = apple.radius * 2
        assert apple.image_original.get_size() == (diameter, diameter)


# ──────────────────────────────────────────────────
# Taille des fruits (rayon = collision ET affichage, donc coherents)
# ──────────────────────────────────────────────────

class TestFruitSize:

    def test_fruits_are_reasonably_large(self):
        from src.fruits.banana import Banana
        from src.fruits.watermelon import Watermelon
        from src.fruits.orange import Orange
        for cls in (Apple, Banana, Watermelon, Orange, Bomb):
            obj = cls(100, 100, 0, 0)
            assert 35 <= obj.radius <= 70

    def test_collision_radius_matches_sprite_diameter(self):
        apple = Apple(100, 100, 0, 0)
        assert apple.image_original.get_width() == apple.radius * 2
