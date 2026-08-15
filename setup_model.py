import sys
import io
import urllib.request
from pathlib import Path

# Forcer UTF-8 sur Windows
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

MODEL_DIR  = Path(__file__).parent / "assets"
MODEL_PATH = MODEL_DIR / "hand_landmarker.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


def download():
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 1_000_000:
        print(f"[OK] Modele deja present : {MODEL_PATH}")
        return True

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("Telechargement du modele MediaPipe (~25 MB)...")
    print(f"  Source : {MODEL_URL}")
    print(f"  Dest   : {MODEL_PATH}")
    print()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        )
    }

    try:
        req = urllib.request.Request(MODEL_URL, headers=headers)
        downloaded = 0
        data = bytearray()

        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                data.extend(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    filled = int(pct / 5)
                    bar = "#" * filled + "." * (20 - filled)
                    print(f"\r  [{bar}] {pct:.0f}%  ({downloaded//1024} KB)", end="", flush=True)

        print()
        MODEL_PATH.write_bytes(data)
        print(f"\n[OK] Modele telecharge : {MODEL_PATH}")
        return True

    except Exception as e:
        print(f"\n[ERREUR] Telechargement echoue : {e}")
        print()
        print("=" * 56)
        print("  TELECHARGEMENT MANUEL REQUIS")
        print("=" * 56)
        print("  1. Ouvre ce lien dans ton navigateur :")
        print(f"     {MODEL_URL}")
        print(f"  2. Place le fichier ici :")
        print(f"     {MODEL_PATH}")
        print("  3. Relance : python main.py")
        print("=" * 56)
        return False


def check_deps():
    print("Verification des dependances...")
    deps = {
        "cv2":       "opencv-python",
        "mediapipe": "mediapipe",
        "pygame":    "pygame",
        "numpy":     "numpy",
    }
    ok = True
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"  [OK]  {package}")
        except ImportError:
            print(f"  [!!]  {package}  ->  pip install {package}")
            ok = False
    return ok


if __name__ == "__main__":
    print("=" * 40)
    print("  FruitNinja CV - Setup")
    print("=" * 40)
    print()

    deps_ok = check_deps()
    print()

    if not deps_ok:
        print("[!!] Installe d'abord les dependances :")
        print("     pip install -r requirements.txt")
        sys.exit(1)

    model_ok = download()
    print()

    if model_ok:
        print("Tout est pret ! Lance le jeu avec :")
        print("  python main.py")
    else:
        sys.exit(1)
