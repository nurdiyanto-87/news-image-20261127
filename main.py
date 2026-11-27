#!/usr/bin/env python3
"""news-image-20261127: sum up Friday 27 November 2026's world news in one image.

Pure stdlib (zlib + struct). Draws a 1024x1024 newspaper front page with six
verified stories from 27 November 2026 and writes it to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png). Fully deterministic: no randomness,
no timestamps, no network.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)
INK = (24, 24, 24)
NAVY = (20, 38, 63)
GOLD = (201, 162, 75)
WHITE = (255, 255, 255)
PANEL_LINE = (198, 190, 172)
KICKER_RED = (154, 32, 32)
SUB_GREY = (74, 74, 74)

BANDS = [
    (122, 31, 31),    # Kuwait strike   - dark red
    (58, 58, 58),     # Gaza           - charcoal
    (46, 74, 107),    # Thanksgiving   - steel blue
    (31, 77, 46),     # Chess          - dark green
    (31, 107, 90),    # Migration      - teal
    (122, 101, 16),   # Black Friday   - dark gold
]

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows, each row a 5-bit string (left to right, top to bottom).
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns list of lines."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def poly(self, points, c):
        """Filled polygon via scanline fill."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    if y1 != y0:
                        x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                        xs.append(x)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_centered(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)


# ---------------------------------------------------------------- pictograms
def pic_drone(cv, x0, y0, w, h):
    # explosion burst (left) + drone silhouette (right)
    cx, cy = x0 + w // 4, y0 + h // 2 + 8
    pts = []
    import math
    for i in range(16):
        ang = math.pi * i / 8
        r = 34 if i % 2 == 0 else 16
        pts.append((int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang))))
    cv.poly(pts, (240, 140, 40))
    cv.circle(cx, cy, 12, (250, 200, 60))
    # drone body (bigger, clearer rotors)
    bx, by = x0 + int(w * 0.68), y0 + 34
    cv.fill_rect(bx - 30, by, 60, 14, (30, 30, 30))
    cv.fill_rect(bx - 9, by - 9, 18, 32, (30, 30, 30))
    for dx in (-40, 40):
        cv.line(bx + dx - 16, by - 6, bx + dx + 16, by - 6, (30, 30, 30), 4)
        cv.circle(bx + dx, by - 8, 6, (220, 220, 220))
    cv.line(bx - 30, by + 14, bx - 46, by + 40, (30, 30, 30), 4)
    cv.line(bx + 30, by + 14, bx + 46, by + 40, (30, 30, 30), 4)


def pic_gaza(cv, x0, y0, w, h):
    # damaged skyline with smoke
    base = y0 + h - 18
    cv.fill_rect(x0 + 60, base - 62, 52, 62, (20, 20, 20))
    cv.fill_rect(x0 + 130, base - 84, 48, 84, (20, 20, 20))
    cv.poly([(x0 + 196, base), (x0 + 196, base - 50),
             (x0 + 220, base - 78), (x0 + 244, base - 50),
             (x0 + 244, base)], (20, 20, 20))
    cv.fill_rect(x0 + 262, base - 56, 50, 56, (20, 20, 20))
    cv.fill_rect(x0 + 330, base - 74, 46, 74, (20, 20, 20))
    # windows
    for wx in (x0 + 72, x0 + 92, x0 + 142, x0 + 162, x0 + 274, x0 + 294,
               x0 + 342, x0 + 360):
        for wy in (base - 50, base - 30):
            cv.fill_rect(wx, wy, 8, 10, (240, 200, 60))
    # smoke
    for sx, sy, r in ((x0 + 155, y0 + 22, 12), (x0 + 175, y0 + 12, 15),
                      (x0 + 300, y0 + 26, 11), (x0 + 318, y0 + 14, 13)):
        cv.circle(sx, sy, r, (200, 200, 200))


def pic_storm(cv, x0, y0, w, h):
    cx, cy = x0 + w // 2 - 20, y0 + 44
    for dx, dy, r in ((-38, 6, 22), (0, -6, 26), (38, 8, 20), (-14, 12, 20),
                      (18, 12, 18)):
        cv.circle(cx + dx, cy + dy, r, (235, 235, 235))
    # lightning bolt
    cv.poly([(cx + 8, cy + 22), (cx - 6, cy + 52), (cx + 4, cy + 52),
             (cx - 10, cy + 84), (cx + 16, cy + 46), (cx + 6, cy + 46),
             (cx + 22, cy + 22)], (250, 210, 40))
    # rain
    for rx in (x0 + 90, x0 + 140, x0 + 330, x0 + 380):
        cv.line(rx, y0 + 66, rx - 8, y0 + 92, (180, 205, 230), 3)
    # wind lines
    for wy in (y0 + 20, y0 + 34):
        cv.line(x0 + 330, wy, x0 + 400, wy, (200, 215, 230), 3)


def pic_chess(cv, x0, y0, w, h):
    # 4x4 mini board + king
    bx, by, s = x0 + 150, y0 + 16, 20
    for r in range(4):
        for c in range(4):
            col = WHITE if (r + c) % 2 == 0 else (30, 30, 30)
            cv.fill_rect(bx + c * s, by + r * s, s, s, col)
    cv.rect(bx, by, 4 * s, 4 * s, (200, 200, 200), 2)
    # king piece to the right: crowned head, robe, base
    kx = x0 + 320
    cv.poly([(kx - 14, by + 26), (kx - 14, by + 6), (kx - 7, by + 14),
             (kx, by + 2), (kx + 7, by + 14), (kx + 14, by + 6),
             (kx + 14, by + 26)], WHITE)
    cv.circle(kx, by + 2, 4, WHITE)
    cv.poly([(kx - 14, by + 30), (kx + 14, by + 30),
             (kx + 22, by + 74), (kx - 22, by + 74)], WHITE)
    cv.fill_rect(kx - 26, by + 72, 52, 6, WHITE)


def pic_migration(cv, x0, y0, w, h):
    # descending bars + big downward arrow
    base = y0 + h - 20
    heights = [66, 52, 38, 24]
    for i, hh in enumerate(heights):
        x = x0 + 90 + i * 52
        cv.fill_rect(x, base - hh, 34, hh, (235, 235, 235))
    ax = x0 + 330
    cv.poly([(ax - 26, y0 + 14), (ax + 26, y0 + 14), (ax + 26, y0 + 52),
             (ax + 44, y0 + 52), (ax, y0 + 92), (ax - 44, y0 + 52),
             (ax - 26, y0 + 52)], (250, 210, 40))


def pic_shopping(cv, x0, y0, w, h):
    # shopping bag + percent tag
    bx, by = x0 + 170, y0 + 26
    cv.poly([(bx, by), (bx + 110, by), (bx + 100, by + 62),
             (bx + 10, by + 62)], (235, 235, 235))
    cv.line(bx + 30, by, bx + 38, by - 18, (235, 235, 235), 4)
    cv.line(bx + 80, by, bx + 72, by - 18, (235, 235, 235), 4)
    cv.line(bx + 38, by - 18, bx + 72, by - 18, (235, 235, 235), 4)
    # percent tag
    tx, ty = x0 + 320, y0 + 30
    cv.circle(tx, ty, 26, (250, 210, 40))
    cv.text(tx - text_width("%", 3) // 2, ty - 10, "%", 3, (20, 38, 63))


PICS = [pic_drone, pic_gaza, pic_storm, pic_chess, pic_migration, pic_shopping]

STORIES = [
    ("MIDDLE EAST", "DRONE STRIKE KILLS TWO IN KUWAIT",
     "Two Italian workers killed; Iran denies responsibility.",
     "BBC - NYT"),
    ("MIDDLE EAST", "ISRAELI STRIKES KILL 10 IN GAZA",
     "Hamas weighs its response after a deadly day of strikes.",
     "REUTERS"),
    ("UNITED STATES", "THANKSGIVING STORMS HIT US",
     "Macy's parade postponed for the first time; 800,000 lose power.",
     "BBC"),
    ("SPORT", "GUKESH HOLDS SINDAROV IN GAME 3",
     "Marathon Game 3 of the World Championship ends in a draw.",
     "INDIA TODAY"),
    ("EUROPE", "UK MIGRATION LOWEST SINCE 1997",
     "Net migration falls to its lowest level since 1997.",
     "NYT"),
    ("ECONOMY", "BLACK FRIDAY, CAUTIOUS SHOPPERS",
     "Shoppers spend carefully as inflation bites into holiday sales.",
     "REUTERS"),
]


# ---------------------------------------------------------------- compose
def draw(cv):
    # masthead
    cv.fill_rect(0, 0, W, 172, NAVY)
    cv.text_centered(W // 2, 22, "FRIDAY - THE WORLD IN ONE IMAGE", 3, GOLD)
    cv.text_centered(W // 2, 62, "27 NOVEMBER 2026", 7, WHITE)
    cv.fill_rect(60, 148, W - 120, 3, GOLD)

    # grid of panels
    mx, my = 24, 188
    gap = 16
    pw = (W - 2 * mx - gap) // 2
    ph = 246
    for i, (kicker, headline, sub, source) in enumerate(STORIES):
        col, row = i % 2, i // 2
        x = mx + col * (pw + gap)
        y = my + row * (ph + gap)
        cv.fill_rect(x, y, pw, ph, WHITE)
        cv.rect(x, y, pw, ph, PANEL_LINE, 2)
        # pictogram band
        cv.fill_rect(x + 2, y + 2, pw - 4, 106, BANDS[i])
        PICS[i](cv, x + 2, y + 2, pw - 4, 106)
        # source tag, bottom-left inside the band (free corner)
        cv.text(x + 12, y + 92, source, 2, (215, 215, 215))
        # kicker + headline + sub
        tx = x + 18
        ty = y + 120
        cv.text(tx, ty, kicker, 2, KICKER_RED)
        lines = wrap_text(headline, 4, pw - 36)
        hy = ty + 20
        for ln in lines[:2]:
            cv.text(tx, hy, ln, 4, INK)
            hy += 31
        sub_lines = wrap_text(sub, 2, pw - 36)
        sy = hy + 4
        for ln in sub_lines[:3]:
            cv.text(tx, sy, ln, 2, SUB_GREY)
            sy += 16

    # footer
    fy = 972
    cv.fill_rect(24, fy - 8, W - 48, 2, GOLD)
    cv.text_centered(W // 2, fy + 6,
                     "FRIDAY, 27 NOVEMBER 2026 - SOURCES: BBC, REUTERS, "
                     "THE NEW YORK TIMES, INDIA TODAY", 2, INK)


# ---------------------------------------------------------------- png out
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        start = y * cv.w * 3
        raw += cv.px[start:start + cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw(cv)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path} ({W}x{H}, {size} bytes)")


if __name__ == "__main__":
    main()
