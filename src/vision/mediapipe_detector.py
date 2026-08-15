import cv2
import numpy as np


def draw_finger_dot(frame_bgr: np.ndarray,
                    pos: tuple,
                    color: tuple = (0, 255, 0),
                    radius: int = 10) -> None:
    """Dessine un cercle sur le bout du doigt détecté."""
    if pos is not None:
        cv2.circle(frame_bgr, pos, radius, color, -1)


def draw_speed_text(frame_bgr: np.ndarray, speed: float) -> None:
    """Affiche la vitesse courante en haut à gauche (debug)."""
    text = f"Speed: {speed:.1f} px/frame"
    cv2.putText(frame_bgr, text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)


def draw_landmarks_new(frame_bgr: np.ndarray, hand_landmarks_list) -> None:
    """
    Dessine les landmarks avec la nouvelle API MediaPipe Tasks (0.10+).
    hand_landmarks_list = result.hand_landmarks (liste de listes de landmarks)
    """
    h, w = frame_bgr.shape[:2]
    # Connexions entre les points de la main (paires d'indices)
    CONNECTIONS = [
        (0,1),(1,2),(2,3),(3,4),         # pouce
        (0,5),(5,6),(6,7),(7,8),          # index
        (0,9),(9,10),(10,11),(11,12),     # majeur
        (0,13),(13,14),(14,15),(15,16),   # annulaire
        (0,17),(17,18),(18,19),(19,20),   # auriculaire
        (5,9),(9,13),(13,17),             # paume
    ]
    for hand in hand_landmarks_list:
        for start_idx, end_idx in CONNECTIONS:
            p1 = (int(hand[start_idx].x * w), int(hand[start_idx].y * h))
            p2 = (int(hand[end_idx].x * w),   int(hand[end_idx].y * h))
            cv2.line(frame_bgr, p1, p2, (0, 200, 0), 2)
        for lm in hand:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame_bgr, (cx, cy), 4, (255, 255, 255), -1)


def draw_landmarks_old(frame_bgr: np.ndarray, results) -> None:
    """
    Dessine les landmarks avec l'ancienne API mp.solutions (0.9.x).
    results = hands.process(frame_rgb)
    """
    try:
        import mediapipe as mp
        mp_drawing = mp.solutions.drawing_utils
        mp_hands   = mp.solutions.hands
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame_bgr, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
    except Exception:
        pass
