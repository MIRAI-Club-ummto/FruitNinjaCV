import math
import numpy as np
import pytest

from src.vision.hand_tracker import HandTracker


@pytest.fixture
def tracker():
    t = HandTracker(slice_speed_threshold=15.0)
    yield t
    t.close()


def _black_frame(w: int = 640, h: int = 480) -> np.ndarray:
    """Frame noire BGR — aucune main dedans."""
    return np.zeros((h, w, 3), dtype=np.uint8)


# ── Tests sans main ────────────────────────────────

class TestNoHand:
    def test_returns_none_on_black_frame(self, tracker):
        frame = _black_frame()
        result = tracker.get_index_tip(frame)
        assert result is None

    def test_speed_zero_when_no_hand(self, tracker):
        tracker.get_index_tip(_black_frame())
        assert tracker.speed == 0.0

    def test_not_slicing_when_no_hand(self, tracker):
        tracker.get_index_tip(_black_frame())
        assert tracker.is_slicing is False

    def test_history_cleared_after_no_hand(self, tracker):
        # Simuler quelques positions puis absence
        tracker._history.append((100, 100))
        tracker._history.append((200, 200))
        tracker._update_speed(None)
        assert len(tracker._history) == 0


# ── Tests calcul de vitesse ────────────────────────

class TestSpeedCalculation:
    def test_speed_between_two_positions(self, tracker):
        tracker._update_speed((0, 0))
        tracker._update_speed((30, 40))  # distance = 50
        assert abs(tracker.speed - 50.0) < 0.01

    def test_zero_speed_on_first_position(self, tracker):
        tracker._update_speed((100, 100))
        assert tracker.speed == 0.0

    def test_is_slicing_above_threshold(self, tracker):
        tracker._update_speed((0, 0))
        tracker._update_speed((100, 0))   # vitesse = 100 > 15
        assert tracker.is_slicing is True

    def test_not_slicing_below_threshold(self, tracker):
        tracker._update_speed((0, 0))
        tracker._update_speed((5, 0))     # vitesse = 5 < 15
        assert tracker.is_slicing is False


# ── Tests vecteur de tranche ───────────────────────

class TestSliceVector:
    def test_returns_none_with_single_point(self, tracker):
        tracker._update_speed((0, 0))
        assert tracker.get_slice_vector() is None

    def test_horizontal_vector(self, tracker):
        tracker._update_speed((0, 0))
        tracker._update_speed((10, 0))
        vec = tracker.get_slice_vector()
        assert vec is not None
        assert abs(vec[0] - 1.0) < 0.01
        assert abs(vec[1] - 0.0) < 0.01

    def test_vector_is_normalized(self, tracker):
        tracker._update_speed((0, 0))
        tracker._update_speed((30, 40))
        vec = tracker.get_slice_vector()
        assert vec is not None
        norm = math.hypot(vec[0], vec[1])
        assert abs(norm - 1.0) < 0.01


# ── Tests close ───────────────────────────────────

class TestClose:
    def test_close_does_not_raise(self):
        t = HandTracker()
        t.close()   # ne doit pas lever d'exception
