#!/usr/bin/env python
"""Universal MODIS LST (MOD11C1) downloader supporting three auth modes:
1. Bearer token via env LAADS_TOKEN
2. App key via env LAADS_APPKEY (adds ?appkey=...)
3. Earthdata Login basic auth via env EDL_USER + EDL_PASS

Usage examples:
  python scripts/01_download_modis_lst_universal.py --start 2024-07-01 --end 2024-07-05
  (set one of the auth methods as env vars beforehand)

Creates directory tree: raw/MOD11C1/<YEAR>/<DOY>/file.hdf

If a file already exists (size > 0) it's skipped.
"""
from __future__ import annotations
import argparse, os, sys, time
from datetime import date, timedelta
from pathlib import Path
import requests

BASE_URL = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD11C1"


def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def build_url(d: date) -> str:
    doy = d.timetuple().tm_yday
    return f"{BASE_URL}/{d.year}/{doy:03d}/"


def fetch_index(url: str, session: requests.Session, headers: dict):
    r = session.get(url, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Index {r.status_code} {r.text[:200]}")
    # Very lightweight HTML listing parse
    return [line.split('"')[1] for line in r.text.splitlines() if line.startswith('<a href="MOD11C1.A')]


def pick_main_file(files, d: date):
    prefix = f"MOD11C1.A{d.year}{d.timetuple().tm_yday:03d}"
    cands = [f for f in files if f.startswith(prefix) and f.endswith('.hdf')]
    return sorted(cands)[-1] if cands else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True, help='YYYY-MM-DD')
    ap.add_argument('--end', required=True, help='YYYY-MM-DD')
    ap.add_argument('--out', default='raw/MOD11C1')
    ap.add_argument('--retry', type=int, default=3)
    args = ap.parse_args()

    token = os.environ.get('LAADS_TOKEN')
    appkey = os.environ.get('LAADS_APPKEY')
    edl_user = os.environ.get('EDL_USER')
    edl_pass = os.environ.get('EDL_PASS')

    if not (token or appkey or (edl_user and edl_pass)):
        print('ERROR: set one of LAADS_TOKEN or LAADS_APPKEY or (EDL_USER & EDL_PASS)', file=sys.stderr)
        sys.exit(1)

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if end < start:
        print('ERROR: end < start', file=sys.stderr)
        sys.exit(1)

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()

    base_headers = {}
    auth = None
    if token:
        base_headers['Authorization'] = f'Bearer {token}'
        print('Auth mode: Bearer token')
    elif edl_user and edl_pass:
        auth = (edl_user, edl_pass)
        print('Auth mode: Earthdata basic')
    elif appkey:
        print('Auth mode: appkey parameter')

    for d in daterange(start, end):
        day_url = build_url(d)
        try:
            files = fetch_index(day_url, session, base_headers)
        except Exception as e:
            print(f'[{d}] index fail: {e}')
            continue
        main_file = pick_main_file(files, d)
        if not main_file:
            print(f'[{d}] no file listed')
            continue

        doy_str = f"{d.timetuple().tm_yday:03d}"
        dest_dir = out_root / f"{d.year}" / doy_str
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / main_file
        if dest.exists() and dest.stat().st_size > 0:
            print(f'[{d}] exists')
            continue

        file_url = day_url + main_file
        if appkey:
            sep = '&' if '?' in file_url else '?'
            file_url = f"{file_url}{sep}appkey={appkey}"

        print(f'[{d}] downloading {main_file}')
        for attempt in range(1, args.retry + 1):
            try:
                with session.get(file_url, headers=base_headers, auth=auth, stream=True, timeout=180) as r:
                    if r.status_code != 200:
                        raise RuntimeError(f'HTTP {r.status_code}')
                    total = int(r.headers.get('Content-Length', 0))
                    done = 0
                    chunk = 1024 * 1024
                    with open(dest, 'wb') as f:
                        for part in r.iter_content(chunk_size=chunk):
                            if not part:
                                continue
                            f.write(part)
                            done += len(part)
                            if total:
                                pct = done / total * 100
                                print(f"\r{main_file} {pct:5.1f}%", end='')
                    print()
                break
            except Exception as e:
                if attempt == args.retry:
                    print(f'FAILED [{d}] {e}')
                else:
                    print(f'Retry {attempt} [{d}] {e}')
                    time.sleep(2 * attempt)

if __name__ == '__main__':
    main()
