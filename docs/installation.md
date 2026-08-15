# Guide d'installation

## 1. Dépendances Python

```bash
pip install -r requirements.txt
```

Contenu de `requirements.txt` :
```
opencv-python==4.9.0.80
mediapipe==0.10.11
pygame==2.5.2
numpy==1.26.4
```

---

## 2. Assets — ce qu'il faut mettre dans `assets/`

Le jeu fonctionne **sans aucun asset** grâce aux fallbacks intégrés
(formes colorées, police système, pas de son). Mais avec les assets,
l'expérience est bien meilleure.

---

### assets/images/

| Fichier           | Taille recommandée | Description                        |
|-------------------|--------------------|------------------------------------|
| `apple.png`       | 100×100 px         | Pomme, fond transparent (PNG RGBA) |
| `banana.png`      | 100×100 px         | Banane, fond transparent           |
| `watermelon.png`  | 130×130 px         | Pastèque, fond transparent         |
| `bomb.png`        | 90×90 px           | Bombe noire, fond transparent      |
| `background.png`  | 800×600 px         | Image de fond du jeu               |

**Où les trouver gratuitement :**
- https://opengameart.org (chercher "fruit", "bomb", "ninja")
- https://itch.io/game-assets/free (assets 2D libres)
- https://kenney.nl/assets (packs gratuits, licence CC0)
- Générer avec DALL·E, Midjourney ou Stable Diffusion

**Format obligatoire :** PNG avec canal alpha (transparence).  
Le code fait `pygame.image.load(...).convert_alpha()` — les JPEG ne fonctionneront pas correctement.

**Si vous n'avez pas les images :**  
Le jeu dessine automatiquement des cercles colorés (pomme rouge, banane jaune, pastèque verte, bombe noire). C'est suffisant pour jouer.

---

### assets/sounds/

| Fichier          | Format | Description                         |
|------------------|--------|-------------------------------------|
| `slice.wav`      | WAV    | Son de tranche (court, ~0.3s)       |
| `explosion.wav`  | WAV    | Explosion quand on touche une bombe |
| `music.mp3`      | MP3    | Musique de fond en boucle           |

**Note :** Les sons ne sont pas encore intégrés dans le code v1.  
Pour les ajouter : `pygame.mixer.Sound("assets/sounds/slice.wav").play()`  
dans `game_manager.py` quand `result.sliced_fruits` n'est pas vide.

**Sources gratuites :**
- https://freesound.org (licence Creative Commons)
- https://opengameart.org/content/sfx-starter-pack

---

###  assets/fonts/

| Fichier          | Description                              |
|------------------|------------------------------------------|
| `game_font.ttf`  | Police d'affichage pour le score et l'UI |

**Où trouver une police de jeu gratuite :**
- https://www.dafont.com (filtrer "Free for commercial use")
- https://fonts.google.com (toutes gratuites, chercher "Press Start 2P" ou "Bangers")
- https://fontsquirrel.com

**Si vous n'avez pas de police :** Le code utilise automatiquement `Arial` système.

---

## 3. Vérifier l'installation

```bash
# Tester que la webcam s'ouvre
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'ERREUR'); cap.release()"

# Tester MediaPipe
python -c "import mediapipe; print('MediaPipe OK')"

# Tester Pygame
python -c "import pygame; pygame.init(); print('Pygame OK')"

# Lancer les tests
pytest tests/ -v
```

---

## 4. Lancer le jeu

```bash
python main.py
```

---

## 5. Problèmes courants

### "Impossible d'ouvrir la caméra"
- Vérifier que la webcam n'est pas utilisée par une autre application (Zoom, Teams, etc.)
- Essayer `camera_index=1` ou `camera_index=2` dans `main.py`

### FPS trop bas (<15fps)
- Réduire la résolution : passer `width=640, height=480` dans `CameraManager`
- Fermer les autres applications gourmandes

### MediaPipe ne détecte pas la main
- Assurer un bon éclairage (pas de contre-jour)
- Fond contrasté avec la main
- Ajuster `min_detection_confidence=0.5` dans `HandTracker`

### La lame est inversée (gauche/droite)
- Le `cv2.flip(frame, 1)` dans `CameraManager` doit être présent — vérifier qu'il n'a pas été retiré
