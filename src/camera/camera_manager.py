import cv2
import numpy as np


class CameraManager:
    """Encapsule cv2.VideoCapture et expose une API simple."""

    def __init__(self, camera_index: int = 0,
                 width: int = 800, height: int = 600) -> None:
        """
        Paramètres
        ----------
        camera_index : int
            Index de la caméra (0 = webcam principale).
        width, height : int
            Dimensions cibles des frames retournées.
        """
        self.width  = width
        self.height = height

        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Impossible d'ouvrir la caméra index={camera_index}. "
                "Vérifiez que la webcam est branchée et non utilisée par une autre application."
            )

        # Suggérer la résolution à OpenCV (pas toujours respectée par le driver)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ──────────────────────────────────────────────
    # Lecture
    # ──────────────────────────────────────────────

    def read(self) -> np.ndarray | None:
        """
        Lit une frame, la retourne en miroir horizontal et la redimensionne.

        Retourne
        --------
        np.ndarray (BGR, uint8) ou None si la lecture échoue.
        """
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None

        # Miroir : quand tu bouges la main à droite, le curseur va à droite
        frame = cv2.flip(frame, 1)

        # Redimensionner si nécessaire
        h, w = frame.shape[:2]
        if w != self.width or h != self.height:
            frame = cv2.resize(frame, (self.width, self.height),
                               interpolation=cv2.INTER_LINEAR)
        return frame

    # ──────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────

    def get_fps(self) -> float:
        """Retourne le FPS annoncé par la caméra."""
        return self.cap.get(cv2.CAP_PROP_FPS)

    def release(self) -> None:
        """Libère la ressource caméra."""
        if self.cap.isOpened():
            self.cap.release()

    def __del__(self) -> None:
        self.release()
