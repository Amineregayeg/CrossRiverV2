"""Preview the new stylized titles by rendering each transition screen to a PNG.
Run with: ./.venv/bin/python preview_titles.py
"""
import os, sys, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

WIDTH, HEIGHT = 1280, 720
FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")


def load_font(name, size):
    path = os.path.join(FONT_DIR, name)
    return pygame.font.Font(path, size) if os.path.exists(path) else pygame.font.Font(None, size)


# Mirror week2.py title themes / fonts
title_font = load_font("LilitaOne.ttf", 100)
hud_timer_font = load_font("LilitaOne.ttf", 68)
subtitle_font = load_font("Inter-Regular.ttf", 22)
score_font = load_font("Inter-Regular.ttf", 26)
hud_badge_font = load_font("LilitaOne.ttf", 26)

UI_GOLD = (255, 205, 55)
UI_FOAM = (235, 245, 255)
UI_WATER = (160, 205, 245)
UI_MIST = (130, 160, 195)
UI_SAGE = (120, 210, 155)

TITLE_THEMES = {
    "victory": ((255, 235, 130), (255, 175, 55),  (200, 100, 25),  (38, 18, 8),    (255, 175, 50)),
    "primary": ((230, 245, 255), (160, 210, 250), (60, 130, 215),  (12, 26, 58),   (90, 170, 255)),
    "ember":   ((255, 220, 120), (255, 140, 55),  (175, 45, 35),   (40, 15, 10),   (255, 110, 45)),
}

_title_cache = {}


def _gradient_text_surface(text, fnt, top, mid, bot):
    base = fnt.render(text, True, (255, 255, 255))
    w, h = base.get_size()
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    split = h * 0.55
    for y in range(h):
        if y < split:
            t = y / max(1, split)
            r = int(top[0] * (1 - t) + mid[0] * t)
            g = int(top[1] * (1 - t) + mid[1] * t)
            b = int(top[2] * (1 - t) + mid[2] * t)
        else:
            t = (y - split) / max(1, h - split)
            r = int(mid[0] * (1 - t) + bot[0] * t)
            g = int(mid[1] * (1 - t) + bot[1] * t)
            b = int(mid[2] * (1 - t) + bot[2] * t)
        pygame.draw.line(grad, (r, g, b, 255), (0, y), (w, y))
    grad.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return grad


def build_stylized_title(text, fnt, theme="victory", extrude=9, stroke=4, glow=True):
    key = (text, id(fnt), theme, extrude, stroke, glow)
    if key in _title_cache:
        return _title_cache[key]
    top, mid, bot, stroke_col, glow_col = TITLE_THEMES.get(theme, TITLE_THEMES["victory"])
    grad = _gradient_text_surface(text, fnt, top, mid, bot)
    tw, th = grad.get_size()
    pad = max(stroke + extrude + 32, 40)
    surf = pygame.Surface((tw + pad * 2, th + pad * 2), pygame.SRCALPHA)
    cx, cy = pad, pad

    if glow:
        glow_text = fnt.render(text, True, glow_col)
        for ang_i in range(8):
            ang = 2 * math.pi * ang_i / 8
            stamp = glow_text.copy()
            stamp.set_alpha(45)
            surf.blit(stamp, (cx + 2 * math.cos(ang), cy + 2 * math.sin(ang)))

    for i in range(extrude, 0, -1):
        t = i / extrude
        r = int(stroke_col[0] * t + bot[0] * (1 - t) * 0.55)
        g = int(stroke_col[1] * t + bot[1] * (1 - t) * 0.55)
        b = int(stroke_col[2] * t + bot[2] * (1 - t) * 0.55)
        col = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        layer = fnt.render(text, True, col)
        surf.blit(layer, (cx + i, cy + i))

    stroke_surf = fnt.render(text, True, stroke_col)
    steps = 18
    for i in range(steps):
        ang = 2 * math.pi * i / steps
        dx = stroke * math.cos(ang)
        dy = stroke * math.sin(ang)
        surf.blit(stroke_surf, (cx + dx, cy + dy))

    surf.blit(grad, (cx, cy))

    highlight = fnt.render(text, True, (255, 255, 255))
    highlight.set_alpha(70)
    band = pygame.Surface((tw, max(2, int(th * 0.32))), pygame.SRCALPHA)
    band.blit(highlight, (0, 0))
    surf.blit(band, (cx, cy))

    _title_cache[key] = surf
    return surf


def draw_stylized_title(screen, text, fnt, cx, cy, theme="victory",
                        scale=1.0, alpha=255, extrude=9, stroke=4, glow=True,
                        max_width=None):
    surf = build_stylized_title(text, fnt, theme, extrude, stroke, glow)
    eff_scale = scale
    if max_width is None:
        max_width = int(WIDTH * 0.86)
    if surf.get_width() * eff_scale > max_width:
        eff_scale *= max_width / (surf.get_width() * eff_scale)
    if abs(eff_scale - 1.0) > 0.001:
        sw = max(1, int(surf.get_width() * eff_scale))
        sh = max(1, int(surf.get_height() * eff_scale))
        surf = pygame.transform.smoothscale(surf, (sw, sh))
    if alpha < 255:
        surf = surf.copy()
        surf.set_alpha(int(max(0, min(255, alpha))))
    screen.blit(surf, surf.get_rect(center=(cx, cy)))


def light_burst(theme):
    glow_col = TITLE_THEMES[theme][4]
    sw, sh = WIDTH // 8, HEIGHT // 8
    small = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx, cy = sw // 2, sh // 2 - 4
    max_r = int(math.hypot(sw, sh) * 0.6)
    for r in range(max_r, 0, -2):
        t = 1.0 - (r / max_r)
        a = int(70 * t * t)
        if a <= 0:
            continue
        pygame.draw.circle(small, (*glow_col, a), (cx, cy), r)
    return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))


def vignette():
    vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(10):
        a = max(0, 22 - i * 2)
        if a == 0:
            continue
        rect = pygame.Rect(i * 22, i * 16, WIDTH - i * 44, HEIGHT - i * 32)
        pygame.draw.rect(vig, (0, 0, 0, a), rect, border_radius=10)
    return vig


def fake_water_bg():
    """Quick approximation of the water background — dark navy with subtle horizontal stripes."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + 12 * (1 - t))
        g = int(20 + 10 * (1 - t))
        b = int(48 + 18 * (1 - t))
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    # subtle stripes
    for y in range(0, HEIGHT, 4):
        a = 18 if y % 8 == 0 else 8
        pygame.draw.line(bg, (60, 80, 120), (0, y), (WIDTH, y), 1)
    return bg


def render_screen(filename, title_text, title_theme, subtitle_text=None,
                  score_text=None, hint_text=None, big_time=None):
    screen = pygame.Surface((WIDTH, HEIGHT))
    screen.blit(fake_water_bg(), (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    burst = light_burst(title_theme)
    burst.set_alpha(int(255 * 1.0))
    screen.blit(burst, (0, 0))

    screen.blit(vignette(), (0, 0))

    title_y = HEIGHT // 2 - 60
    if subtitle_text or score_text or hint_text or big_time:
        title_y = HEIGHT // 2 - 110
    draw_stylized_title(screen, title_text, title_font, WIDTH // 2, title_y,
                        theme=title_theme, extrude=11, stroke=5)

    y_cursor = title_y + 110

    if big_time:
        draw_stylized_title(screen, big_time, hud_timer_font, WIDTH // 2, y_cursor + 30,
                            theme="ember", extrude=8, stroke=4)
        y_cursor += 90

    if score_text:
        s = score_font.render(score_text, True, UI_WATER)
        screen.blit(s, s.get_rect(center=(WIDTH // 2, y_cursor + 30)))
        y_cursor += 50

    if subtitle_text:
        s = subtitle_font.render(subtitle_text, True, UI_MIST)
        screen.blit(s, s.get_rect(center=(WIDTH // 2, y_cursor + 30)))
        y_cursor += 40

    if hint_text:
        h = subtitle_font.render(hint_text, True, UI_MIST)
        screen.blit(h, h.get_rect(center=(WIDTH // 2, HEIGHT - 80)))

    pygame.image.save(screen, filename)
    print(f"  → {filename}")


os.makedirs("/tmp/title_previews", exist_ok=True)
print("Rendering title previews...")
render_screen("/tmp/title_previews/01_you_win.png", "YOU WIN!", "victory",
              score_text="Time remaining  ·  12.4s", hint_text="Press ENTER or ESC")
render_screen("/tmp/title_previews/02_level_complete.png", "LEVEL COMPLETE!", "victory",
              subtitle_text="Preparing Level 2...")
render_screen("/tmp/title_previews/03_speed_run.png", "SPEED RUN", "ember",
              subtitle_text="HOW MANY PLAYERS?")
render_screen("/tmp/title_previews/04_speedrun_complete.png", "SPEED RUN COMPLETE!", "victory",
              big_time="2:14.7", score_text="Amine  ·  finished the run",
              hint_text="Press ENTER")
render_screen("/tmp/title_previews/05_select_mode.png", "SELECT MODE", "primary",
              subtitle_text="Choose how you want to play")
render_screen("/tmp/title_previews/06_cross_river.png", "CROSS RIVER", "primary",
              subtitle_text="Navigate the river. Avoid the forest.")
print("Done.")
