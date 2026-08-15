# Guide utilisateur

## Comment jouer

### Position recommandée
- Asseyez-vous à **50–80 cm** de la webcam
- Éclairage frontal (pas de fenêtre derrière vous)
- Fond uni de préférence (aide MediaPipe à détecter la main)

### Geste de tranche
Levez l'**index** tendu et faites un mouvement **rapide et net**
de gauche à droite (ou en diagonale) pour trancher les fruits.

```
        🍎
    ────────────►  ← geste de tranche
```

La vitesse minimale est **12 pixels/frame**. Un geste lent n'est pas détecté.

---

## Règles du jeu

| Événement              | Conséquence              |
|------------------------|--------------------------|
| Trancher un fruit 🍎   | +1 à +3 points           |
| Trancher une pastèque  | +3 points                |
| Trancher une bombe 💣  | **Game Over instantané** |
| Fruit raté (hors écran)| -1 vie                   |
| 0 vies restantes       | Game Over                |

---

## Système de combo

| Tranches consécutives | Multiplicateur |
|-----------------------|----------------|
| 1 – 2                 | ×1             |
| 3 – 4                 | ×2             |
| 5+                    | ×4             |

Un flash orange indique un combo actif.  
Le combo se réinitialise si vous n'tranchez rien pendant **1.5 secondes**.

---

## Niveaux de difficulté

La difficulté augmente automatiquement avec le score :

| Score | Niveau           | Fréquence de spawn |
|-------|------------------|--------------------|
| 0     | Ninja Débutant   | 1 fruit toutes 2s  |
| 15    | Ninja Apprenti   | 2 fruits rapprochés|
| 35    | Ninja Confirmé   | Encore plus vite   |
| 60    | Ninja Maître     | 3 fruits d'un coup |
| 100   | Grand Ninja      | 4 fruits + bombes  |

---

## Calibration

Si la détection est mauvaise, modifiez dans `src/vision/hand_tracker.py` :

```python
HandTracker(
    min_detection_confidence=0.5,   # baisser si détection lente
    min_tracking_confidence=0.4,    # baisser si tracking saccadé
    slice_speed_threshold=10.0,     # baisser si gestes non détectés
)
```
