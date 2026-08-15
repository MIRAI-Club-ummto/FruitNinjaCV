import pytest
from unittest.mock import MagicMock

from src.fruits.fruit import _segment_circle_intersects
from src.fruits.apple import Apple
from src.fruits.bomb import Bomb
from src.fruits.fruit import FruitState
from src.collisions.collision_manager import CollisionManager
from src.blade.blade_tracker import BladeTracker


# ──────────────────────────────────────────────────
# Tests géométriques bas niveau
# ──────────────────────────────────────────────────

class TestSegmentCircle:

    def test_segment_passes_through_center(self):
        # Segment horizontal qui passe pile par le centre
        assert _segment_circle_intersects(
            (0, 100), (200, 100), (100, 100), 30
        ) is True

    def test_segment_misses_circle(self):
        # Segment loin du cercle
        assert _segment_circle_intersects(
            (0, 0), (200, 0), (100, 200), 30
        ) is False

    def test_segment_endpoint_inside_circle(self):
        # Un des points du segment est dans le cercle
        assert _segment_circle_intersects(
            (90, 100), (200, 100), (100, 100), 20
        ) is True

    def test_segment_tangent_to_circle(self):
        # Tangence exacte (distance = rayon)
        assert _segment_circle_intersects(
            (0, 50), (200, 50), (100, 80), 30
        ) is True

    def test_degenerate_segment_inside(self):
        # p1 == p2, point à l'intérieur
        assert _segment_circle_intersects(
            (100, 100), (100, 100), (100, 100), 10
        ) is True

    def test_degenerate_segment_outside(self):
        # p1 == p2, point à l'extérieur
        assert _segment_circle_intersects(
            (0, 0), (0, 0), (100, 100), 10
        ) is False

    def test_vertical_segment_hits(self):
        assert _segment_circle_intersects(
            (100, 0), (100, 300), (100, 150), 25
        ) is True

    def test_diagonal_segment_misses_narrowly(self):
        assert _segment_circle_intersects(
            (0, 0), (100, 100), (200, 0), 10
        ) is False


# ──────────────────────────────────────────────────
# Tests Fruit.is_hit_by_segment
# ──────────────────────────────────────────────────

class TestFruitHit:

    def _make_apple(self, x=100, y=100):
        a = Apple(x, y, 0, 0)
        return a

    def test_apple_hit_by_passing_segment(self):
        apple = self._make_apple(100, 100)
        # Segment vertical qui traverse le centre
        assert apple.is_hit_by_segment((100, 0), (100, 300)) is True

    def test_apple_not_hit_by_far_segment(self):
        apple = self._make_apple(100, 100)
        assert apple.is_hit_by_segment((300, 0), (300, 300)) is False

    def test_sliced_apple_not_hittable_again(self):
        apple = self._make_apple(100, 100)
        apple.slice()
        assert apple.is_hit_by_segment((100, 0), (100, 300)) is False

    def test_slice_changes_state(self):
        apple = self._make_apple(100, 100)
        assert apple.state == FruitState.ALIVE
        apple.slice()
        expected = FruitState.SLICED if apple.image_sliced else FruitState.FALLING
        assert apple.state == expected


# ──────────────────────────────────────────────────
# Tests Bomb
# ──────────────────────────────────────────────────

class TestBomb:

    def test_bomb_slice_sets_exploded(self):
        bomb = Bomb(100, 100, 0, 0)
        bomb.slice()
        assert bomb.exploded is True
        # La bombe explose (animation) avant de mourir, elle ne meurt pas
        # instantanément.
        assert bomb.state == FruitState.EXPLODING

    def test_bomb_dies_after_explosion_animation(self):
        bomb = Bomb(100, 100, 0, 0)
        bomb.slice()
        for _ in range(bomb.EXPLOSION_DURATION):
            bomb.update(600)
        assert bomb.state == FruitState.DEAD

    def test_bomb_not_exploded_before_slice(self):
        bomb = Bomb(100, 100, 0, 0)
        assert bomb.exploded is False


# ──────────────────────────────────────────────────
# Tests CollisionManager
# ──────────────────────────────────────────────────

class TestCollisionManager:

    def _make_blade(self, p1, p2, active=True):
        blade = MagicMock(spec=BladeTracker)
        blade.is_active = active
        blade.get_last_segment.return_value = (p1, p2)
        return blade

    def test_slices_apple_in_path(self):
        cm = CollisionManager()
        apple = Apple(100, 100, 0, 0)
        blade = self._make_blade((100, 0), (100, 300))

        result = cm.check(blade, [apple], [])
        assert apple in result.sliced_fruits
        assert result.points_gained == apple.points

    def test_no_slice_when_blade_inactive(self):
        cm = CollisionManager(blade_speed_required=True)
        apple = Apple(100, 100, 0, 0)
        blade = self._make_blade((100, 0), (100, 300), active=False)

        result = cm.check(blade, [apple], [])
        assert len(result.sliced_fruits) == 0
        assert apple.state == FruitState.ALIVE

    def test_detects_bomb_explosion(self):
        cm = CollisionManager()
        bomb = Bomb(100, 100, 0, 0)
        blade = self._make_blade((100, 0), (100, 300))

        result = cm.check(blade, [bomb], [])
        assert result.bomb_hit is True
        assert bomb.exploded is True

    def test_missed_fruit_counted(self):
        cm = CollisionManager()
        apple = Apple(100, 700, 0, 5)
        # Simule ce que fait physics_manager.update() : l'appel a update()
        # fait sortir le fruit de l'ecran, ce qui pose missed=True et
        # bascule state -> DEAD (l'objet arrive donc deja "DEAD" dans
        # removed_objects, comme en jeu reel).
        apple.update(screen_height=600)
        assert apple.state == FruitState.DEAD
        assert apple.missed is True

        blade = self._make_blade((999, 0), (999, 1), active=False)
        result = cm.check(blade, [], [apple])
        assert apple in result.missed_fruits

    def test_sliced_fruit_not_counted_as_missed(self):
        cm = CollisionManager()
        apple = Apple(100, 700, 0, 5)
        apple.slice()  # tranché avant de sortir de l'écran
        for _ in range(80):
            apple.update(screen_height=600)
            if apple.state == FruitState.DEAD:
                break
        assert apple.missed is False

        blade = self._make_blade((999, 0), (999, 1), active=False)
        result = cm.check(blade, [], [apple])
        assert apple not in result.missed_fruits

    def test_no_segment_returns_empty_result(self):
        cm = CollisionManager()
        blade = MagicMock(spec=BladeTracker)
        blade.is_active = True
        blade.get_last_segment.return_value = None

        result = cm.check(blade, [Apple(100, 100, 0, 0)], [])
        assert len(result.sliced_fruits) == 0
