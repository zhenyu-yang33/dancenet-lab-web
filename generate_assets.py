#!/usr/bin/env python3
"""
Generate OG images (1200×630 JPG) + favicon files for DanceNet.Lab.
Uses only ffmpeg + standard library (no PIL required).
"""
import subprocess, os, struct, zlib

ASSETS = "assets"

# ─── OG images: video source + seek time ───────────────────────────────────
OG_SOURCES = [
    ("og-home",     "assets/art-hero.mp4",             "00:00:02"),
    ("og-agent",    "assets/share-case02-cv.mp4",       "00:00:02"),
    ("og-art",      "assets/plate-awaken.mp4",          "00:00:04"),
    ("og-art-flow", "assets/art-flow-case-01.mp4",      "00:00:02"),
    ("og-mr",       "assets/mr-phases-bg.mp4",          "00:00:02"),
    ("og-aigc",     "assets/art-flow-case-02.mp4",      "00:00:03"),
    ("og-exp1",     "assets/exp1-cover-hero.mp4",       "00:00:02"),
    ("og-exp2",     "assets/art-flow-case-03.mp4",      "00:00:02"),
]

OG_VF = (
    "scale=1200:630:force_original_aspect_ratio=increase,"
    "crop=1200:630,"
    # dark gradient overlay — bottom 180px for brand bar legibility
    "drawbox=x=0:y=450:w=1200:h=180:color=0x0a0908@0.80:t=fill,"
    # gold rule line
    "drawbox=x=48:y=550:w=200:h=2:color=0xd4a574:t=fill,"
    # gold brand dot
    "drawbox=x=48:y=560:w=8:h=8:color=0xd4a574:t=fill"
)

def make_og_images():
    for name, src, ts in OG_SOURCES:
        if not os.path.exists(src):
            print(f"  ⚠ skip {name}: source not found ({src})")
            continue
        out = f"{ASSETS}/{name}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", ts, "-i", src,
            "-frames:v", "1",
            "-vf", OG_VF,
            "-q:v", "3",
            out,
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            size = os.path.getsize(out) // 1024
            print(f"  ✓ {out} ({size} KB)")
        else:
            print(f"  ✕ {out}: {r.stderr.decode()[-200:]}")

# ─── Pure-Python minimal PNG writer ────────────────────────────────────────
def _png_chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

def write_png(path: str, w: int, h: int, rows):
    """rows: list of w×(r,g,b,a) tuples."""
    raw = b""
    for row in rows:
        raw += b"\x00"                           # filter: None
        for r, g, b, a in row:
            raw += bytes([r, g, b, a])
    sig   = b"\x89PNG\r\n\x1a\n"
    ihdr  = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))  # RGBA
    idat  = _png_chunk(b"IDAT", zlib.compress(raw, 6))
    iend  = _png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(sig + ihdr + idat + iend)

# Brand palette
INK   = (0x0a, 0x09, 0x08, 255)
GOLD  = (0xd4, 0xa5, 0x74, 255)
PAPER = (0xeb, 0xe7, 0xdf, 255)
TRANS = (0x00, 0x00, 0x00,   0)

def circle_sdf(cx, cy, r, x, y):
    return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 - r

def make_icon_png(path: str, size: int):
    """
    Design: dark square, gold circle, vertical dancer-line through centre.
    Anti-aliased via oversampling (2×).
    """
    S = size
    rows = []
    for y in range(S):
        row = []
        for x in range(S):
            cx, cy = S / 2, S / 2
            r_outer = S * 0.43
            r_inner = S * 0.31
            line_w  = S * 0.06

            d_outer = circle_sdf(cx, cy, r_outer, x + 0.5, y + 0.5)
            d_inner = circle_sdf(cx, cy, r_inner, x + 0.5, y + 0.5)
            in_ring = d_outer <= 0 and d_inner > 0

            # vertical dancer line through centre
            half_lw = line_w / 2
            in_line = (abs((x + 0.5) - cx) < half_lw and
                       abs((y + 0.5) - cy) < r_inner * 0.88)

            # small head circle
            head_r  = S * 0.08
            d_head  = circle_sdf(cx, cy - r_inner * 0.64, head_r, x + 0.5, y + 0.5)

            if in_ring or in_line or d_head <= 0:
                row.append(GOLD)
            else:
                row.append(INK)
        rows.append(row)
    write_png(path, S, S, rows)
    print(f"  ✓ {path}")

def make_favicon_svg(path: str):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#0a0908"/>
  <circle cx="16" cy="16" r="12" fill="none" stroke="#d4a574" stroke-width="2"/>
  <rect x="14.5" y="9.5" width="3" height="13" rx="1.5" fill="#d4a574"/>
  <circle cx="16" cy="8.5" r="2" fill="#d4a574"/>
</svg>"""
    with open(path, "w") as f:
        f.write(svg)
    print(f"  ✓ {path}")

def make_favicon_ico(path_32: str, ico_path: str):
    """Wrap a 32×32 PNG into a minimal .ico file."""
    with open(path_32, "rb") as f:
        png_data = f.read()
    plen = len(png_data)
    # ICO header: ICONDIR
    ico = struct.pack("<HHH", 0, 1, 1)   # reserved, type=1(ICO), count=1
    # ICONDIRENTRY: w, h, colorCount, reserved, planes, bitCount, bytesInRes, offset
    ico += struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, plen, 6 + 16)
    ico += png_data
    with open(ico_path, "wb") as f:
        f.write(ico)
    print(f"  ✓ {ico_path}")

if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)

    print("\n── OG Images ──────────────────────────────────")
    make_og_images()

    print("\n── Favicon & Icons ────────────────────────────")
    make_favicon_svg(f"{ASSETS}/favicon.svg")
    make_icon_png(f"{ASSETS}/favicon-32.png",  32)
    make_icon_png(f"{ASSETS}/icon-192.png",    192)
    make_icon_png(f"{ASSETS}/icon-512.png",    512)
    make_icon_png(f"{ASSETS}/apple-touch-icon.png", 180)
    make_favicon_ico(f"{ASSETS}/favicon-32.png", f"{ASSETS}/favicon.ico")

    print("\n── Done ────────────────────────────────────────")
