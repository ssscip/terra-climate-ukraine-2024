"""Render chronological daily anomaly frames (and optional video) from real LST anomalies.
Usage:
  python src/11_build_chronology.py --anom data_products/real_lst_anomaly.nc --start 2024-06-01 --end 2024-08-31
"""
from __future__ import annotations
import argparse
from pathlib import Path
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import shutil, subprocess


def render_frames(anom_path, start, end, out_dir, vmin=-8, vmax=8):
    ds = xr.open_dataset(anom_path)
    sub = ds.sel(time=slice(start, end))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(sub.time.values):
        arr = sub["LST_anomaly"].sel(time=t)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        im = ax.imshow(arr, origin="upper", cmap="coolwarm", vmin=vmin, vmax=vmax)
        ax.set_title(f"LST Anomaly {np.datetime_as_string(t, unit='D')}")
        plt.colorbar(im, ax=ax, label="K")
        ax.axis("off")
        frame_path = Path(out_dir)/f"frame_{i:03d}.png"
        plt.savefig(frame_path, bbox_inches="tight")
        plt.close(fig)
    print(f"Frames written to {out_dir}")


def make_video(out_dir, fps=6):
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found; skipping video")
        return None
    out_mp4 = Path(out_dir)/"chronology.mp4"
    cmd = [
        "ffmpeg","-y","-framerate", str(fps),
        "-i", f"{out_dir}/frame_%03d.png",
        "-c:v","libx264","-pix_fmt","yuv420p", str(out_mp4)
    ]
    subprocess.run(cmd, check=True)
    print("Video written:", out_mp4)
    return out_mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anom", default="data_products/real_lst_anomaly.nc")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out-dir", default="output/chronology_real")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--fps", type=int, default=6)
    args = ap.parse_args()
    render_frames(args.anom, args.start, args.end, args.out_dir)
    if not args.no_video:
        make_video(args.out_dir, args.fps)


if __name__ == "__main__":
    main()
