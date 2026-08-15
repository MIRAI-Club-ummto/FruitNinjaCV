import math
import sys
import urllib.request
from collections import deque
from pathlib import Path

import cv2
import numpy as np

# Forcer UTF-8 sur Windows (evite les crashes cp1252)
if sys.platform == "win32":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Indices landmarks ──────────────────────────────
INDEX_TIP = 8
THUMB_TIP = 4
WRIST     = 0

# ── Modele Tasks API ───────────────────────────────
_MODEL_DIR  = Path(__file__).resolve().parents[2] / "assets"
_MODEL_PATH = _MODEL_DIR / "hand_landmarker.task"
_MODEL_URLS = [
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
]


def _log(msg: str) -> None:
    """print() safe sur Windows (pas de caracteres unicode exotiques)."""
    try:
        print(msg)
    except (UnicodeEncodeError, Exception):
        print(msg.encode("ascii", errors="replace").decode("ascii"))


def _download_model() -> bool:
    """Tente de telecharger le modele. Retourne True si succes."""
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        )
    }
    for url in _MODEL_URLS:
        try:
            _log(f"[HandTracker] Telechargement du modele (~25 MB)...")
            _log(f"  URL : {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            _MODEL_PATH.write_bytes(data)
            _log(f"[HandTracker] Modele sauvegarde : {_MODEL_PATH}")
            return True
        except Exception as e:
            _log(f"[HandTracker] Echec ({url}) : {e}")
    return False


def _ensure_model() -> str:
    """Garantit que le fichier modele existe."""
    if _MODEL_PATH.exists() and _MODEL_PATH.stat().st_size > 1_000_000:
        return str(_MODEL_PATH)

    success = _download_model()
    if not success:
        msg = (
            "\n"
            "=========================================================\n"
            " TELECHARGEMENT MANUEL DU MODELE MEDIAPIPE REQUIS\n"
            "=========================================================\n"
            " 1. Ouvre ce lien dans ton navigateur et telecharge :\n"
            "    https://storage.googleapis.com/mediapipe-models/\n"
            "    hand_landmarker/hand_landmarker/float16/1/\n"
            "    hand_landmarker.task\n"
            f" 2. Place le fichier ici : {_MODEL_PATH}\n"
            " 3. Relance : python main.py\n"
            "=========================================================\n"
        )
        _log(msg)
        raise RuntimeError(f"Modele MediaPipe introuvable. Voir instructions ci-dessus.")
    return str(_MODEL_PATH)


def _try_new_api(max_hands, min_det, min_track):
    """Initialise la nouvelle API MediaPipe Tasks (0.10+)."""
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

    model_path = _ensure_model()
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_hands=max_hands,
        min_hand_detection_confidence=min_det,
        min_hand_presence_confidence=min_det,
        min_tracking_confidence=min_track,
    )
    return ("new", HandLandmarker.create_from_options(options))


def _try_old_api(max_hands, min_det, min_track):
    """Initialise l'ancienne API mp.solutions (0.9.x)."""
    import mediapipe as mp
    if not hasattr(mp, "solutions"):
        raise AttributeError("mp.solutions non disponible (version 0.10+)")
    hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=max_hands,
        min_detection_confidence=min_det,
        min_tracking_confidence=min_track,
    )
    return ("old", hands)


class HandTracker:
    """
    Wrapper MediaPipe Hands - compatible 0.9.x et 0.10+.

    Parametres
    ----------
    max_num_hands             : 1 ou 2 mains
    min_detection_confidence  : seuil detection (0.0-1.0)
    min_tracking_confidence   : seuil tracking  (0.0-1.0)
    slice_speed_threshold     : vitesse min px/frame pour une tranche
    history_len               : nb de positions memorisees
    """

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
        slice_speed_threshold: float = 15.0,
        history_len: int = 5,
    ) -> None:
        self.slice_speed_threshold = slice_speed_threshold
        self._api: str = ""
        self._detector = None

        errors = []
        for fn in (_try_new_api, _try_old_api):
            try:
                self._api, self._detector = fn(
                    max_num_hands,
                    min_detection_confidence,
                    min_tracking_confidence,
                )
                _log(f"[HandTracker] Backend '{self._api}' initialise.")
                break
            except Exception as e:
                errors.append(f"{fn.__name__}: {e}")

        if self._detector is None:
            raise RuntimeError(
                "Impossible d'initialiser MediaPipe Hands.\n" +
                "\n".join(errors)
            )

        self._history: deque = deque(maxlen=history_len)
        self.current_pos = None
        self.speed: float = 0.0
        self.is_slicing: bool = False

    # ──────────────────────────────────────────────
    # API principale
    # ──────────────────────────────────────────────

    def get_index_tip(self, frame_bgr: np.ndarray):
        """Analyse une frame BGR -> retourne (x, y) ou None."""
        h, w = frame_bgr.shape[:2]
        pos = self._detect_new(frame_bgr, w, h) if self._api == "new" \
              else self._detect_old(frame_bgr, w, h)
        self._update_speed(pos)
        if pos is not None:
            self.current_pos = pos
        return pos

    def _detect_new(self, frame_bgr, w, h):
        """Tasks API (0.10+)."""
        import mediapipe as mp
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_img    = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result    = self._detector.detect(mp_img)
        if not result.hand_landmarks:
            return None
        tip = result.hand_landmarks[0][INDEX_TIP]
        return (int(tip.x * w), int(tip.y * h))

    def _detect_old(self, frame_bgr, w, h):
        """Solutions API (0.9.x)."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self._detector.process(frame_rgb)
        frame_rgb.flags.writeable = True
        if not results.multi_hand_landmarks:
            return None
        tip = results.multi_hand_landmarks[0].landmark[INDEX_TIP]
        return (int(tip.x * w), int(tip.y * h))

    # ──────────────────────────────────────────────
    # Calcul vitesse / tranche
    # ──────────────────────────────────────────────

    def _update_speed(self, pos) -> None:
        if pos is None:
            self.speed = 0.0
            self.is_slicing = False
            self._history.clear()
            return
        if self._history:
            prev = self._history[-1]
            self.speed = math.hypot(pos[0] - prev[0], pos[1] - prev[1])
        else:
            self.speed = 0.0
        self.is_slicing = self.speed >= self.slice_speed_threshold
        self._history.append(pos)

    def get_slice_vector(self):
        """Vecteur normalise (dx, dy) ou None."""
        if len(self._history) < 2:
            return None
        p1, p2 = self._history[-2], self._history[-1]
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        norm = math.hypot(dx, dy)
        return (dx / norm, dy / norm) if norm > 0 else None

    def close(self) -> None:
        if self._detector is not None:
            try:
                self._detector.close()
            except Exception:
                pass
