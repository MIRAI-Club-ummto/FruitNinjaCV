# 🍉 Fruit Ninja CV

Fruit Ninja contrôlé par **gestes de la main** en temps réel via la webcam.  
Basé sur **OpenCV**, **MediaPipe Hands** et **Pygame**.

---

## Démo rapide

```
python main.py
```

Levez la main devant votre webcam et tranchez les fruits avec un mouvement rapide !

---

## Prérequis

- Python 3.10+
- Webcam fonctionnelle
- OS : Windows / macOS / Linux

---

## Installation

```bash
# 1. Cloner le projet
git clone https://github.com/vous/FruitNinjaCV.git
cd FruitNinjaCV

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le jeu
python main.py
```

---

## Structure du projet

```
FruitNinjaCV/
├── main.py                  # Point d'entrée
├── requirements.txt
├── assets/
│   ├── images/              # Sprites PNG des fruits, bombe, fond
│   ├── sounds/              # Sons WAV/MP3
│   └── fonts/               # Police TTF (optionnel)
├── src/
│   ├── camera/              # Capture webcam
│   ├── vision/              # Détection MediaPipe
│   ├── blade/               # Trajectoire de la lame
│   ├── fruits/              # Logique de chaque fruit
│   ├── physics/             # Spawn + physique
│   ├── collisions/          # Détection de collision
│   ├── game/                # Score, niveaux, chef d'orchestre
│   ├── ui/                  # Menu, HUD, Game Over
│   └── render/              # Rendu Pygame complet
└── tests/                   # Tests pytest
```

---

## Contrôles

| Action            | Commande                        |
|-------------------|---------------------------------|
| Trancher un fruit | Geste rapide de la main         |
| Menu principal    | Clic ou touche Entrée           |
| Rejouer           | Touche `R` ou bouton à l'écran  |
| Quitter           | `Échap` ou bouton Quitter       |

---

## Assets requis

Voir `docs/installation.md` pour la liste complète des assets nécessaires.

---

## Tests

```bash
pytest tests/ -v
```

---

## Architecture détaillée

Voir `docs/architecture.md`.
