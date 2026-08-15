import sys, io
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

"""
FruitNinjaCV - main.py
Point d'entrée principal du jeu.
Coordonne la caméra, la CV et le moteur de jeu, ainsi que la navigation
entre le menu (choix de difficulté), la partie et l'écran de Game Over.
"""

import sys
import pygame

from src.camera.camera_manager import CameraManager
from src.vision.hand_tracker import HandTracker
from src.blade.blade_tracker import BladeTracker
from src.game.game_manager import GameManager
from src.render.renderer import Renderer
from src.ui.menu import Menu
from src.ui.game_over import GameOverScreen

# ──────────────────────────────────────────────
# Constantes globales
# ──────────────────────────────────────────────
WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 600
FPS           = 60
WINDOW_TITLE  = "Fruit Ninja CV"


def main() -> None:
    """Boucle principale du jeu."""
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # ── Initialisation des modules ──────────────
    camera       = CameraManager(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    hand_tracker = HandTracker()
    blade        = BladeTracker(max_points=20)
    renderer     = Renderer(screen, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    menu         = Menu(screen, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    # ── Boucle d'application : MENU -> PLAYING -> GAME_OVER -> MENU ──
    app_running = True
    while app_running:

        # ── Menu : choix de la difficulté ───────
        difficulty = menu.run()   # None si le joueur quitte
        if difficulty is None:
            app_running = False
            break

        game = GameManager(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, difficulty=difficulty)
        game.start()
        blade.clear()

        # ── Boucle de partie ─────────────────────
        playing = True
        while playing:

            # 1. Événements Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                    app_running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    playing = False
                    app_running = False

            if not playing:
                break

            # 2. Lire la frame webcam
            frame_bgr = camera.read()                    # numpy BGR
            if frame_bgr is None:
                continue

            # 3. Détecter la main -> position du bout de l'index
            finger_pos = hand_tracker.get_index_tip(frame_bgr)  # (x, y) ou None

            # 4. Mettre à jour la trajectoire de la lame
            blade.update(finger_pos)

            # 5. Logique de jeu (spawn, physique, collisions)
            game.update(blade)

            # 6. Rendu complet
            renderer.draw(frame_bgr, game, blade)

            # 7. Game over ?
            if game.is_over():
                go = GameOverScreen(screen, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
                action = go.run(game.score_manager.score)
                if action == "restart":
                    game.restart()
                    blade.clear()
                elif action == "menu":
                    playing = False       # retourne à la boucle de menu, même app_running
                else:
                    playing = False
                    app_running = False

            clock.tick(FPS)

    # ── Nettoyage ────────────────────────────────
    camera.release()
    hand_tracker.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
