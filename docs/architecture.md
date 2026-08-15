# Architecture du projet

## Vue d'ensemble

```
Webcam (OpenCV)
    │
    ▼
CameraManager        → frame BGR (numpy array)
    │
    ▼
HandTracker          → position (x, y) du bout de l'index
    │
    ▼
BladeTracker         → trajectoire + vitesse + segment actif
    │
    ▼
GameManager ─────────────────────────────────────┐
    │                                             │
    ├─► PhysicsManager   (spawn + gravité)        │
    ├─► CollisionManager (segment ∩ cercle)       │
    ├─► ScoreManager     (score, vies, combo)     │
    └─► LevelManager     (difficulté progressive) │
                                                  │
Renderer ◄────────────────────────────────────────┘
    │
    ▼
Écran Pygame
```

---

## Flux d'une frame (60 fps)

1. `camera.read()` — capture frame BGR
2. `hand_tracker.get_index_tip(frame)` — détecte main → (x, y)
3. `blade.update(pos)` — mémorise trajectoire, calcule vitesse
4. `game.update(blade)` :
   - `level_manager.update(score)` → décide si spawn
   - `physics.spawn_wave(n)` si oui
   - `physics.update()` → gravité sur tous les objets, retire les morts
   - `collision_manager.check(blade, objects, removed)` → tranches & bombes
   - Mise à jour score / vies / effets visuels
5. `renderer.draw(frame, game, blade)` :
   - fond = frame webcam convertie BGR→RGB→Surface Pygame
   - fruits et bombes
   - traînée de lame (dégradé alpha)
   - HUD (score, vies, combo)
   - effets flottants (+points)
6. `pygame.display.flip()`

---

## Détection de collision

Algorithme **segment/cercle** :

```
Pour chaque fruit vivant :
    1. Projeter le centre du fruit sur la droite portant le segment lame
    2. Clamp la projection entre les deux extrémités du segment
    3. Calculer la distance entre le point projeté et le centre du fruit
    4. Si distance ≤ radius → collision
```

Complexité : O(n) par frame, n = nombre de fruits actifs (toujours < 20).

---

## Modules et responsabilités

| Module              | Responsabilité unique                              |
|---------------------|----------------------------------------------------|
| `CameraManager`     | Ouvrir/lire/fermer la webcam                       |
| `HandTracker`       | MediaPipe → (x, y) index + vitesse                 |
| `BladeTracker`      | Historique de la lame + segment courant            |
| `Fruit` (ABC)       | Physique, état, rendu d'un objet                   |
| `PhysicsManager`    | Spawn aléatoire + mise à jour physique de tous     |
| `CollisionManager`  | Détecter les tranches et bombes touchées           |
| `ScoreManager`      | Score, combo, vies                                 |
| `LevelManager`      | Difficulté progressive selon le score              |
| `GameManager`       | Orchestrer tous les sous-systèmes                  |
| `Renderer`          | Rendu complet d'une frame (webcam + jeu + UI)      |
| `Menu`              | Écran de démarrage                                 |
| `GameOverScreen`    | Écran de fin + boutons restart/quit                |

---

## Performances

- Résolution de capture : 640×480 recommandé (plus rapide que 1080p)
- MediaPipe fonctionne sur CPU — cible 30fps avec `static_image_mode=False`
- Pygame vise 60fps ; le rendu de la webcam en fond est le goulot principal
- Ne jamais boucler pixel par pixel — utiliser NumPy vectorisé
