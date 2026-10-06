#!/usr/bin/env python3
"""Turn dropped source folders (01_Bluebay/, 02_…/) into web media under images/<slug>/.

    python3 build_images.py            # process every folder listed in SOURCES

Per project: "order" lists photo file names (without extension) in slot order;
"cover" names the hero-square photo; "videos" lists clips as
{"src": "file.mp4", "poster": seconds, "audio": False} → images/<slug>/video-NN.mp4
(720p H.264, 2.5 Mbps, AAC unless "audio": False) plus video-NN-poster.jpg.
"copy": True keeps a file as-is (already web-ready or too low-res to re-encode).
"cover" may name a photo key or "video-NN" to use that clip's poster frame. Videos use tools/transcode.swift and
tools/poster.swift (AVFoundation), so no ffmpeg is needed. Existing outputs
newer than their source are skipped. Add an entry whenever a new folder lands.
"""
import os, subprocess, sys
from PIL import Image, ImageOps

SOURCES = {
    "01_Bluebay": {"slug": "blue-bay", "order": ["3", "4", "2", "1", "5"], "cover": "3"},
    "02_Interlude 1_MV": {"slug": "interlude-01-house-session",
                          "order": ["DSC01344", "DSC01342", "DSC01349", "DSC01353"], "cover": "DSC01353",
                          "videos": [{"src": "Snippet MV .mp4", "poster": 5}]},
    "03_Microfest": {"slug": "microfest", "order": ["1", "2", "3"], "cover": "3",
                     "videos": [{"src": "Snippet Fest .mp4", "poster": 3, "audio": False},
                                {"src": "Snippet Fest 2.mp4", "poster": 3, "audio": False},
                                {"src": "Snippet Fest 3.mp4", "poster": 1, "audio": False}]},
    "04_The Fridge": {"slug": "the-fridge", "order": ["1"], "cover": "video-01",
                      "videos": [{"src": "Snippet The Fridge.mp4", "poster": 20},
                                 {"src": "Serge Volant - Live Modular Improv (Live at The Fridge Concert Series Season 44).mp4", "poster": 30, "copy": True}]},
    "05_Interlude 2_Bluerose": {"slug": "interlude-02-blue-rose", "order": ["3", "1", "2"], "cover": "3",
                                "videos": [{"src": "Snippet BR.mp4", "poster": 5}]},
    "06_Imagine x Automatic": {"slug": "imagine-family-x-automatic-01", "order": ["2", "3", "4", "5", "6", "7", "1"], "cover": "2"},
    "07_La ruche": {"slug": "la-ruche", "order": ["2", "1"], "cover": "2"},
    "08_Interlude 3_Magnolia": {"slug": "interlude-03-nouveau-magnolia", "order": ["2", "1", "3"], "cover": "2",
                                "videos": [{"src": "Snippet Sarba .mp4", "poster": 5}]},
    "09_Interlude 4_Impasse": {"slug": "interlude-04-limpasse", "order": ["1", "2"], "cover": "video-01",
                               "videos": [{"src": "Snippet Amer .mp4", "poster": 5}]},
    "10_Sample": {"slug": "le-sample", "order": ["DSC01450", "DSC01509", "DSC01414", "DSC01444"], "cover": "DSC01450"},
    "11_Paname All Starz": {"slug": "paname-all-starz", "order": ["DSC01986", "DSC01953", "4", "5"], "cover": "DSC01986"},
    "12_Interlude 5_Impasse bis": {"slug": "interlude-05-limpasse-bis",
                                   "order": ["Interlude Hungu(1)", "Interlude Joy(1)", "Interlude Hungu", "Interlude Joy"], "cover": "video-01",
                                   "videos": [{"src": "Snippet Hungu.mp4", "poster": 5}, {"src": "Snippet Joy.mp4", "poster": 5}]},
    "13_Interlude 6_Wrong side": {"slug": "interlude-06-the-wrong-side", "order": ["DSC02121", "0730(1)", "0730"], "cover": "video-03",
                                  "videos": [{"src": "Snippet 1.mp4", "poster": 5}, {"src": "Snippet 2.mp4", "poster": 5},
                                             {"src": "Snippet 3.mp4", "poster": 5}, {"src": "Snippet 4.mp4", "poster": 5},
                                             {"src": "BTS 1.mp4", "poster": 1}]},
    "14_Interlude Bekaata": {"slug": "interlude-07-lebanon-concert", "order": ["Still 1", "Still 2"], "cover": "video-01",
                             "videos": [{"src": "BC 21.08-1.mp4", "poster": 5}, {"src": "BC x Miki.mp4", "poster": 3, "copy": True}]},
    "15_Imagine x Automatic 0307": {"slug": "imagine-family-x-automatic-02",
                                    "order": ["2026_07_04_Automatic-Writing_Imagine@Wanderlust_Romain-GUEDE_0372", "2026_07_04_Automatic-Writing_Imagine@Wanderlust_Romain-GUEDE_0760", "2026_07_04_Automatic-Writing_Imagine@Wanderlust_Romain-GUEDE_1964", "2026_07_04_Automatic-Writing_Imagine@Wanderlust_Romain-GUEDE_0083", "2026_07_04_Automatic-Writing_Imagine@Wanderlust_Romain-GUEDE_2223"], "cover": "2026_07_04_Automatic-Writing_Imagine@Wanderlust_Romain-GUEDE_0372",
                                    "videos": [{"src": "MP4.mp4", "poster": 3, "copy": True}]},
}
MAX_EDGE = 1600      # long edge in px
QUALITY = 85
VIDEO_W, VIDEO_H, VIDEO_KBPS, AUDIO_KBPS = 1280, 720, 2500, 128
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic")

import json
Image.MAX_IMAGE_PIXELS = None
MANIFEST = {}   # per output folder: {output file: source description}; regenerate when the source changes

def load_manifest(out):
    p = os.path.join(out, ".build.json")
    MANIFEST[out] = json.load(open(p)) if os.path.exists(p) else {}

def note(out, dst, desc):
    MANIFEST[out][os.path.basename(dst)] = desc
    json.dump(MANIFEST[out], open(os.path.join(out, ".build.json"), "w"), indent=1)

def fresh(dst, src, desc=None):
    out = os.path.dirname(dst)
    same = desc is None or MANIFEST.get(out, {}).get(os.path.basename(dst)) == desc
    return same and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)

def flatten(im):
    """Drop transparency onto white so PNG renders keep their edges."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA"); bg = Image.new("RGB", rgba.size, (255, 255, 255)); bg.paste(rgba, mask=rgba.getchannel("A")); return bg
    return im.convert("RGB")

def save(src, dst):
    desc = os.path.relpath(src)
    if fresh(dst, src, desc):
        return None
    im = flatten(ImageOps.exif_transpose(Image.open(src)))
    im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
    im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    note(os.path.dirname(dst), dst, desc)
    return im.size, os.path.getsize(dst)

def swift(script, *args):
    r = subprocess.run(["swift", script, *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{script} failed:\n{r.stderr[-2000:]}")
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""

os.chdir(os.path.dirname(os.path.abspath(__file__)))
for folder, spec in SOURCES.items():
    if not os.path.isdir(folder):
        print(f"skip {folder}: not found"); continue
    files = {os.path.splitext(f)[0]: f for f in os.listdir(folder) if f.lower().endswith(EXTS)}
    out = os.path.join("images", spec["slug"]); os.makedirs(out, exist_ok=True); load_manifest(out)
    for n, key in enumerate(spec.get("order", []), 1):
        dst = os.path.join(out, f"{n:02d}.jpg"); r = save(os.path.join(folder, files[key]), dst)
        print(f"{dst}  <- {files[key]}  " + (f"{r[0][0]}x{r[0][1]}  {r[1]//1024} KB" if r else "(up to date)"))
    for n, v in enumerate(spec.get("videos", []), 1):
        src = os.path.join(folder, v["src"]); mp4 = os.path.join(out, f"video-{n:02d}.mp4"); poster = os.path.join(out, f"video-{n:02d}-poster.jpg")
        vdesc = f"{os.path.relpath(src)}|{'copy' if v.get('copy') else f'{VIDEO_W}x{VIDEO_H}@{VIDEO_KBPS}k'}|audio={v.get('audio', True)}"
        if fresh(mp4, src, vdesc):
            print(f"{mp4}  (up to date)")
        elif v.get("copy"):
            import shutil; shutil.copyfile(src, mp4); note(out, mp4, vdesc); print(f"{mp4}  <- {v['src']}  copied as-is  {os.path.getsize(mp4)//1024} KB")
        else:
            print(f"{mp4}  <- {v['src']}  transcoding…", flush=True)
            print("   " + swift("tools/transcode.swift", src, mp4, str(VIDEO_W), str(VIDEO_H), str(VIDEO_KBPS), str(AUDIO_KBPS if v.get("audio", True) else 0)), flush=True)
            note(out, mp4, vdesc)
        pdesc = f"{os.path.relpath(src)}@{v.get('poster', 1)}s"
        if not fresh(poster, src, pdesc):
            tmp = os.path.join(out, "video-%02d-frame" % n); swift("tools/poster.swift", src, tmp, str(v.get("poster", 1)))
            frame = f"{tmp}-{int(v.get('poster', 1))}.jpg"
            im = Image.open(frame).convert("RGB"); im.thumbnail((VIDEO_W, VIDEO_H), Image.LANCZOS)
            im.save(poster, "JPEG", quality=QUALITY, optimize=True, progressive=True); os.remove(frame); note(out, poster, pdesc)
            print(f"{poster}  frame at {v.get('poster', 1)}s  {os.path.getsize(poster)//1024} KB", flush=True)
    cover = spec.get("cover")
    if cover:
        dst = os.path.join(out, "cover.jpg")
        src = os.path.join(out, f"{cover}-poster.jpg") if cover.startswith("video-") else os.path.join(folder, files[cover])
        r = save(src, dst)
        print(f"{dst}  <- {os.path.basename(src)}  " + (f"{r[1]//1024} KB" if r else "(up to date)"))
