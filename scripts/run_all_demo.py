"""Python fallback runner for synthetic demo (avoids PowerShell execution policy issues).

Usage:
  python scripts/run_all_demo.py --regenerate --video
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REQUIRED_IMPORTS = [
    ("numpy", "numpy"),
    ("xarray", "xarray"),
]

def check_deps():
    missing = []
    for mod, disp in REQUIRED_IMPORTS:
        try:
            __import__(mod)
        except Exception:  # noqa: BLE001
            missing.append(disp)
    if missing:
        print("\n[ERROR] Відсутні пакети: " + ", ".join(missing))
        print("Python інтерпретатор:", sys.executable)
        print("\nЯк виправити (варіант A – conda, рекомендовано):")
        print("  conda env create -f environment.yml")
        print("  conda activate terra-climate")
        print("\nЯкщо conda немає (варіант B – тимчасово pip мінімально):")
        print("  python -m pip install --upgrade pip")
        print("  python -m pip install numpy xarray pandas matplotlib shapely")
        print("\nПісля установки перезапусти:  python scripts/run_all_demo.py --regenerate")
        sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]):
    print("[run]", " ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"Command failed: {' '.join(cmd)} (exit {r.returncode})")
        sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser(description="Run synthetic demo pipeline (Python only)")
    ap.add_argument("--regenerate", action="store_true", help="Force regenerate synthetic data")
    ap.add_argument("--no-video", action="store_true", help="Skip video creation")
    args = ap.parse_args()

    check_deps()

    data_event = ROOT / "data_products" / "lst_event.nc"
    if args.regenerate or not data_event.exists():
        run([sys.executable, "scripts/demo_generate_mock_data.py", "--run-metrics", "--make-frames"])
    else:
        # Update metrics & frames only
        run([sys.executable, "src/08_metrics.py"])
        run([sys.executable, "src/09_generate_frames.py"])

    # Histogram
    run([sys.executable, "src/07_histogram_distribution.py"]) 

    # Global anomaly synthetic (ensure global products exist for preview)
    run([sys.executable, "src/06_global_anomalies.py", "--synthetic"]) 

    # Video
    if not args.no_video:
        import shutil
        if shutil.which("ffmpeg") is None:
            print("[warn] ffmpeg not found -> пропускаю створення відео (встанови ffmpeg та перезапусти без --no-video)")
        else:
            ps1 = ROOT / "src" / "10_make_video.ps1"
            if ps1.exists():
                run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)])
            else:
                sh = ROOT / "src" / "10_make_video.sh"
                if sh.exists():
                    run(["bash", str(sh)])
    print("Synthetic demo completed. Check output/video and output/frames_local.")


if __name__ == "__main__":
    main()
