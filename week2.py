import pygame
import sys
import math
import random
import os
import threading
import json
import cv2
from pathlib import Path
from maps import MAPS, get_map
from editor_maps import get_editor_map

pygame.init()

# ================================================================
# MAP LOADING - Check editor maps first, fall back to standard maps
# ================================================================
def load_map(theme, level):
    """Load a map, checking editor_maps first, then falling back to maps.py"""
    editor_map = get_editor_map(theme, level)
    if editor_map:
        print(f"  📍 Loaded editor map: {editor_map['name']}")
        return editor_map
    return get_map(theme, level)

# ================================================================
# AUDIO SETUP
# ================================================================
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

SOUND_PATH = os.path.join(os.path.dirname(__file__), "assets", "sounds")


def load_sound(filename):
    if not AUDIO_AVAILABLE:
        return None
    path = os.path.join(SOUND_PATH, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Could not load sound {path}: {e}")
    return None


def play_sound(sound, volume=1.0):
    if sound is not None:
        try:
            sound.set_volume(volume * volume_sfx)
            sound.play()
        except Exception:
            pass


# Load sounds
ambience_sound = load_sound("forest_ambience.wav")
wind_sfx = load_sound("wind_gust.wav")
crash_sfx = load_sound("crash.wav")

# Load multiple paddle splash variants for variety
_paddle_variants = []
for _fname in ["paddle_splash.wav", "paddle_splash2.wav", "paddle_splash3.wav"]:
    _s = load_sound(_fname)
    if _s:
        _paddle_variants.append(_s)
# Load bubble overlay sounds
_bubble_variants = []
for _fname in ["paddle_bubble.ogg", "paddle_bubble2.ogg"]:
    _s = load_sound(_fname)
    if _s:
        _bubble_variants.append(_s)
# Fallback: if no variants loaded, keep None
paddle_sfx = _paddle_variants[0] if _paddle_variants else None


def play_paddle_sound(volume=0.1):
    """Play a random paddle splash variant + optional bubble overlay."""
    if _paddle_variants:
        snd = random.choice(_paddle_variants)
        play_sound(snd, volume * volume_sfx)
    if _bubble_variants and random.random() < 0.5:
        bub = random.choice(_bubble_variants)
        play_sound(bub, volume * 0.3 * volume_sfx)


# Start ambience loop
if ambience_sound:
    try:
        ambience_sound.play(loops=-1)
        ambience_sound.set_volume(0.3)
    except Exception:
        pass

# ================================================================
# VOLUME SETTINGS
# ================================================================
volume_music = 0.15
volume_sfx = 1.0
volume_ambience = 0.3

# Start background music (uses pygame.mixer.music for streaming)
if AUDIO_AVAILABLE:
    _music_path = os.path.join(SOUND_PATH, "background_music.ogg")
    if os.path.exists(_music_path):
        try:
            pygame.mixer.music.load(_music_path)
            pygame.mixer.music.set_volume(volume_music)
            pygame.mixer.music.play(loops=-1)
        except Exception as e:
            print(f"Could not load background music: {e}")


# ================================================================
# VOICEOVER SYSTEM
# ================================================================
VO_PATH = os.path.join(os.path.dirname(__file__), "assets", "sounds", "voiceover")


class VoiceoverSystem:
    """Plays pre-generated voiceover audio files and tracks playback state."""

    def __init__(self):
        self._current_sound = None
        self._channel = None
        self._start_time = 0
        self._duration = 0
        self._cache = {}

    def play(self, filename, volume=0.8):
        if not AUDIO_AVAILABLE:
            return 0
        if filename in self._cache:
            snd = self._cache[filename]
        else:
            path = os.path.join(VO_PATH, filename)
            if not os.path.exists(path):
                print(f"Voiceover not found: {path}")
                return 0
            try:
                snd = pygame.mixer.Sound(path)
                self._cache[filename] = snd
            except Exception as e:
                print(f"Could not load voiceover {path}: {e}")
                return 0
        self.stop()
        snd.set_volume(volume * volume_sfx)
        self._channel = snd.play()
        self._current_sound = snd
        self._duration = snd.get_length()
        self._start_time = pygame.time.get_ticks() / 1000.0
        return self._duration

    def stop(self):
        if self._channel and self._channel.get_busy():
            self._channel.stop()
        self._current_sound = None

    def is_playing(self):
        if self._channel:
            return self._channel.get_busy()
        return False

    def get_progress(self):
        if self._duration <= 0:
            return 1.0
        elapsed = pygame.time.get_ticks() / 1000.0 - self._start_time
        return min(1.0, elapsed / self._duration)


voiceover = VoiceoverSystem()


# ================================================================
# DIALOG BOX (avatar + typing text)
# ================================================================
class DialogBox:
    """Centered dialog with circular avatar and sentence-by-sentence typing animation."""

    def __init__(self, font):
        self.font = font
        self.sentences = []
        self.current_sentence_idx = 0
        self.revealed_chars = 0
        self.chars_per_second = 60
        self._char_accum = 0.0
        self.visible = False
        self._done = False
        self.avatar_radius = 30
        self.box_width = 500
        self.box_height = 80

        # Load avatar image and fit inside circle
        self._avatar_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        avatar_path = os.path.join(os.path.dirname(__file__), "assets", "avatar.png")
        try:
            raw = pygame.image.load(avatar_path).convert_alpha()
            # Scale to fit inside circle (diameter 56px with 4px border margin)
            scaled = pygame.transform.smoothscale(raw, (56, 56))
            # Create circular mask
            mask_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(mask_surf, (255, 255, 255, 255), (32, 32), 28)
            # Blit scaled image centered, then apply mask
            temp = pygame.Surface((64, 64), pygame.SRCALPHA)
            temp.blit(scaled, (4, 4))
            # Apply circular clip by iterating pixels
            for y in range(64):
                for x in range(64):
                    if mask_surf.get_at((x, y)).a == 0:
                        temp.set_at((x, y), (0, 0, 0, 0))
            self._avatar_surf = temp
            # Border ring
            pygame.draw.circle(self._avatar_surf, (100, 160, 255), (32, 32), 30, 2)
        except Exception:
            # Fallback to placeholder
            pygame.draw.circle(self._avatar_surf, (40, 80, 160), (32, 32), 30)
            pygame.draw.circle(self._avatar_surf, (60, 110, 200), (32, 32), 28)
            pygame.draw.circle(self._avatar_surf, (220, 230, 240), (32, 22), 10)
            pygame.draw.ellipse(self._avatar_surf, (220, 230, 240),
                                pygame.Rect(16, 34, 32, 18))
            pygame.draw.circle(self._avatar_surf, (100, 160, 255), (32, 32), 30, 2)

    def _split_sentences(self, text):
        """Split text into sentences (by period, exclamation, question mark)."""
        sentences = []
        current = ""
        for ch in text:
            current += ch
            if ch in '.!?' and current.strip():
                sentences.append(current.strip())
                current = ""
        if current.strip():
            sentences.append(current.strip())
        return sentences if sentences else [text]

    def show(self, text, duration=None):
        self.sentences = self._split_sentences(text)
        self.current_sentence_idx = 0
        self.revealed_chars = 0
        self._char_accum = 0.0
        self.visible = True
        self._done = False
        if duration and duration > 0:
            self.chars_per_second = max(10, len(text) / duration)
        else:
            self.chars_per_second = 60

    def hide(self):
        self.visible = False
        self.sentences = []
        self.current_sentence_idx = 0
        self.revealed_chars = 0
        self._done = False

    def is_done(self):
        return self._done

    def update(self, dt):
        if not self.visible or self._done:
            return
        if not self.sentences:
            self._done = True
            return
        current_text = self.sentences[self.current_sentence_idx]
        if self.revealed_chars < len(current_text):
            self._char_accum += self.chars_per_second * dt
            new_chars = int(self._char_accum)
            if new_chars > 0:
                self.revealed_chars = min(len(current_text), self.revealed_chars + new_chars)
                self._char_accum -= new_chars
        else:
            # Sentence finished — move to next immediately
            if self.current_sentence_idx < len(self.sentences) - 1:
                self.current_sentence_idx += 1
                self.revealed_chars = 0
                self._char_accum = 0.0
            else:
                self._done = True

    def _wrap_text(self, text, max_width):
        words = text.split(' ')
        lines = []
        current = ""
        for w in words:
            test = current + (" " if current else "") + w
            tw, _ = self.font.size(test)
            if tw > max_width and current:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    def draw(self, screen, game_time):
        if not self.visible or not self.sentences:
            return

        sw = screen.get_width()
        sh = screen.get_height()

        # Centered text box at bottom of screen
        box_x = (sw - self.box_width) // 2
        box_y = sh - 50 - self.box_height // 2

        box_surf = pygame.Surface((self.box_width, self.box_height), pygame.SRCALPHA)
        box_surf.fill((15, 20, 35, 200))
        pygame.draw.rect(box_surf, (80, 120, 200, 120),
                         pygame.Rect(0, 0, self.box_width, self.box_height),
                         width=2, border_radius=10)
        screen.blit(box_surf, (box_x, box_y))

        # Render current sentence typing — horizontally centered lines
        current_text = self.sentences[self.current_sentence_idx]
        visible_text = current_text[:self.revealed_chars]
        lines = self._wrap_text(visible_text, self.box_width - 24)
        line_h = 22
        for i, line in enumerate(lines[:3]):
            line_surf = self.font.render(line, True, (220, 230, 245))
            line_rect = line_surf.get_rect(midtop=(box_x + self.box_width // 2,
                                                    box_y + 10 + i * line_h))
            screen.blit(line_surf, line_rect)

        # Blinking cursor at end of last visible line (also centered)
        if not self._done and int(game_time * 4) % 2 == 0 and lines:
            last_line = lines[-1]
            tw, _ = self.font.size(last_line)
            line_left = box_x + (self.box_width - tw) // 2
            cx = line_left + tw + 2
            cy = box_y + 10 + (len(lines) - 1) * line_h
            cursor_surf = self.font.render("|", True, (180, 200, 255))
            screen.blit(cursor_surf, (cx, cy))

# ================================================================
# WINDOW SETUP
# ================================================================
WIDTH, HEIGHT = 1250, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cross River")
clock = pygame.time.Clock()

def calculate_spawn_pos(map_data, default_x=None, default_y=600):
    """Get exact spawn position. Prioritizes spawn_point if set in editor."""
    if default_x is None:
        default_x = WIDTH // 2
    if not map_data:
        return pygame.Vector2(default_x, default_y)

    # Priority 1: explicit spawn_point from map editor
    sp = map_data.get("spawn_point")
    if sp and "x" in sp and "y" in sp:
        return pygame.Vector2(sp["x"], sp["y"])

    # Priority 2: calculate from start line
    start_pos = map_data.get("start", {})
    axis = start_pos.get("axis", "y")

    if axis == "y":
        spawn_x = start_pos.get("x1", default_x)
        spawn_y = start_pos.get("pos", default_y)
    else:
        spawn_x = start_pos.get("x1", start_pos.get("pos", default_x))
        y1 = start_pos.get("y1", 300)
        y2 = start_pos.get("y2", 400)
        spawn_y = (y1 + y2) // 2

    return pygame.Vector2(spawn_x, spawn_y)

def get_spawn_angle(map_data):
    """Get boat facing angle from spawn_point or start line."""
    if not map_data:
        return 0
    sp = map_data.get("spawn_point")
    if sp and "angle" in sp:
        return sp["angle"]
    start = map_data.get("start", {})
    return start.get("angle", 0)

def point_in_polygon(px, py, polygon_points):
    """Ray casting algorithm to check if point is inside polygon."""
    n = len(polygon_points)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon_points[i].get("x", 0), polygon_points[i].get("y", 0)
        xj, yj = polygon_points[j].get("x", 0), polygon_points[j].get("y", 0)
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def point_in_any_slow_zone(px, py, slow_zones):
    """Check if point is inside any slow zone polygon."""
    for zone in slow_zones:
        points = zone.get("points", [])
        if len(points) >= 3 and point_in_polygon(px, py, points):
            return True
    return False


def circle_vs_polygon(cx, cy, r, pts):
    """Returns True if circle (cx,cy,r) overlaps polygon defined by pts list of (x,y)."""
    n = len(pts)
    if n < 2:
        return False
    r2 = r * r
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        len2 = dx * dx + dy * dy
        if len2 == 0:
            dist2 = (cx - ax) ** 2 + (cy - ay) ** 2
        else:
            t = max(0.0, min(1.0, ((cx - ax) * dx + (cy - ay) * dy) / len2))
            px, py2 = ax + t * dx, ay + t * dy
            dist2 = (cx - px) ** 2 + (cy - py2) ** 2
        if dist2 < r2:
            return True
    # Point-in-polygon (handles boat center fully inside a large polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > cy) != (yj > cy)) and (cx < (xj - xi) * (cy - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts")


def _load_font(name, size):
    path = os.path.join(FONT_PATH, name)
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


# Typography system
font = _load_font("Inter-Bold.ttf", 52)                   # HUD timer, season names
title_font = _load_font("BebasNeue-Regular.ttf", 82)      # Menu titles
subtitle_font = _load_font("Inter-Regular.ttf", 22)       # Descriptions, hints
button_font = _load_font("Inter-SemiBold.ttf", 28)        # Button labels
hud_font = _load_font("Inter-Medium.ttf", 26)             # In-game HUD
card_title_font = _load_font("Inter-Bold.ttf", 26)        # Card titles
card_sub_font = _load_font("Inter-Regular.ttf", 18)       # Card subtitles
menu_title_font = _load_font("Sora-ExtraBold.ttf", 72)    # Main menu "CROSS RIVER"

ASSET_PATH = os.path.join(os.path.dirname(__file__), "assets", "images")


# ================================================================
# ASSET LOADING
# ================================================================
def load_image(subdir, filename, size=None):
    path = os.path.join(ASSET_PATH, subdir, filename)
    if not os.path.exists(path):
        print(f"Asset not found: {path}")
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None


tree_canopy1 = load_image("obstacles", "forest1-removebg-preview.png")
tree_canopy2 = load_image("obstacles", "forest2-removebg-preview.png")
forest_floor = load_image("obstacles", "forest_tile.png")

# Load seasonal assets
seasonal_assets = {
    "forest": [load_image("obstacles", "forest_asset_2.png")],
    "snow": [load_image("obstacles", "snow_asset_1.png"), load_image("obstacles", "snow_asset_2.png")],
    "desert": [load_image("obstacles", "desert_asset_1.png"), load_image("obstacles", "desert_asset_2.png")],
    "tropics": [load_image("obstacles", "tropics_asset_1.png"), load_image("obstacles", "tropics_asset_2.png")],
}

# ================================================================
# VIDEO BACKGROUND SYSTEM
# ================================================================
VIDEO_PATH = os.path.join(os.path.dirname(__file__), "assets", "videos")


class VideoBackground:
    """Plays an MP4 video as a looping background (no audio). Uses OpenCV."""

    def __init__(self, filename, target_w, target_h):
        self.target_w = target_w
        self.target_h = target_h
        self.surface = pygame.Surface((target_w, target_h))
        self.surface.fill((20, 30, 50))
        self._ready = False
        path = os.path.join(VIDEO_PATH, filename)
        if not os.path.exists(path):
            print(f"Video not found: {path}")
            return
        try:
            self.cap = cv2.VideoCapture(path)
            if not self.cap.isOpened():
                print(f"Could not open video: {path}")
                return
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self._frame_interval = 1.0 / self.fps
            self._timer = 0.0
            self._ready = True
        except Exception as e:
            print(f"Video init error: {e}")

    def restart(self):
        if self._ready:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._timer = 0.0

    def update(self, dt):
        if not self._ready:
            return
        self._timer += dt
        if self._timer >= self._frame_interval:
            self._timer -= self._frame_interval
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.target_w, self.target_h))
            self.surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def draw(self, target, x=0, y=0, w=None, h=None):
        if w and h and (w != self.target_w or h != self.target_h):
            scaled = pygame.transform.smoothscale(self.surface, (w, h))
            target.blit(scaled, (x, y))
        else:
            target.blit(self.surface, (x, y))


# Pre-load video backgrounds for seasons
print("Loading video backgrounds...")
video_forest = VideoBackground("Desert_river_flowing_with_wind_delpmaspu_-2.mp4", WIDTH, HEIGHT)
video_snow = VideoBackground("Snowfall_on_tree_branches_delpmaspu_.mp4", WIDTH, HEIGHT)
video_desert = VideoBackground("Desert_river_flowing_with_wind_delpmaspu_.mp4", WIDTH, HEIGHT)
video_tropics = VideoBackground("River_flowing_with_swaying_branches_delpmaspu_.mp4", WIDTH, HEIGHT)
season_videos = [video_forest, video_snow, video_desert, video_tropics]
print("Videos loaded.")


# ================================================================
# WATER ANIMATION SYSTEM
# ================================================================
class WaterRenderer:
    """Animated river water with layered waves, flow particles, and sparkles."""

    def __init__(self, w, h):
        self.w, self.h = w, h

        # Deterministic sparkle positions
        rng = random.Random(123)
        self.sparkles = [
            (rng.randint(0, w), rng.randint(0, h), rng.uniform(0, 6.28))
            for _ in range(70)
        ]

        # Flow particles (show current direction)
        rng2 = random.Random(456)
        self.flow_particles = []
        for _ in range(45):
            self.flow_particles.append({
                "x": rng2.uniform(0, w),
                "y": rng2.uniform(0, h),
                "speed": rng2.uniform(18, 40),
                "length": rng2.randint(12, 35),
                "phase": rng2.uniform(0, 6.28),
            })

    def draw(self, screen, dt, time, camera_y=0, palette=None):
        # Use theme-specific colors if palette provided, otherwise use defaults
        if palette is None:
            color_deep = (22, 52, 138)
            color_wave1 = (35, 72, 175)
            color_wave2 = (48, 92, 198)
            color_wave3 = (60, 112, 215)
            color_wave4 = (72, 130, 230)
        else:
            color_deep = palette.get("deep", (22, 52, 138))
            color_wave1 = palette.get("wave1", (35, 72, 175))
            color_wave2 = palette.get("wave2", (48, 92, 198))
            color_wave3 = palette.get("wave3", (60, 112, 215))
            color_wave4 = palette.get("wave4", (72, 130, 230))

        # Deep water base
        screen.fill(color_deep)

        # Wave layer 1: Broad gentle swells
        phase1 = time * 0.7
        for y in range(0, self.h, 16):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 8, 8):
                wy = y + math.sin(x * 0.009 + phase1 + y_world * 0.003) * 5
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, color_wave1, False, pts, 3)

        # Wave layer 2: Medium ripples flowing in the opposite direction
        phase2 = time * -0.45
        for y in range(4, self.h, 22):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 10, 10):
                wy = y + math.sin(x * 0.014 + phase2 + y_world * 0.005) * 3.5
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, color_wave2, False, pts, 2)

        # Wave layer 3: Fine shimmering detail
        phase3 = time * 0.9
        for y in range(8, self.h, 30):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 12, 12):
                wy = (
                    y
                    + math.sin(x * 0.006 + phase3 + y_world * 0.001) * 7
                    + math.sin(x * 0.02 + phase3 * 0.6 + y_world * 0.001) * 2
                )
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, color_wave3, False, pts, 2)

        # Wave layer 4: Highlight accent waves
        phase4 = time * 0.35
        for y in range(2, self.h, 38):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 10, 10):
                wy = y + math.sin(x * 0.011 + phase4 + y_world * 0.002) * 4
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, color_wave4, False, pts, 1)

        # Flow particles (vertical current streaks)
        for p in self.flow_particles:
            p["y"] += p["speed"] * dt
            if p["y"] > self.h + 20:
                p["y"] = -p["length"]
                p["x"] = random.uniform(0, self.w)

            brightness = 0.5 + 0.5 * math.sin(time * 1.5 + p["phase"])
            if brightness > 0.4:
                c = int(55 + brightness * 30)
                x_pos, y_pos = int(p["x"]), int(p["y"])
                end_y = int(p["y"] + p["length"] * brightness)
                pygame.draw.line(
                    screen,
                    (c, min(255, c + 35), min(255, c + 75)),
                    (x_pos, y_pos),
                    (x_pos, end_y),
                    1,
                )

        # Sparkles (twinkling sun reflections)
        for sx, sy, ph in self.sparkles:
            b = math.sin(time * 2.8 + ph)
            if b > 0.55:
                intensity = (b - 0.55) / 0.45
                size = 1 + int(intensity * 2.5)
                r = min(255, int(185 + intensity * 70))
                g = min(255, int(210 + intensity * 45))
                pygame.draw.circle(screen, (r, g, 255), (sx, sy), size)


# ================================================================
# FOREST RENDERING - Pre-rendered with real tree canopy assets
# ================================================================
def create_forest_surface(cubes, w, h, floor_tile, canopy1, canopy2, cap_trees=False):
    """Pre-render forest with floor texture and top-down tree canopy assets."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)

    rng = random.Random(42)

    for cx, cy, cw, ch in cubes:
        # ---- Forest floor ----
        if floor_tile:
            tile_size = 96
            scaled_floor = pygame.transform.scale(floor_tile, (tile_size, tile_size))
            for tx in range(cx, cx + cw, tile_size):
                for ty in range(cy, cy + ch, tile_size):
                    clip_w = min(tile_size, cx + cw - tx)
                    clip_h = min(tile_size, cy + ch - ty)
                    if clip_w > 0 and clip_h > 0:
                        if clip_w >= tile_size and clip_h >= tile_size:
                            surface.blit(scaled_floor, (tx, ty))
                        else:
                            clipped = scaled_floor.subsurface(
                                (0, 0, min(clip_w, tile_size), min(clip_h, tile_size))
                            )
                            surface.blit(clipped, (tx, ty))
        else:
            pygame.draw.rect(surface, (18, 40, 15), (cx, cy, cw, ch))

        # ---- Dark undergrowth spots ----
        for _ in range(max(1, int(cw * ch / 250))):
            ux = cx + rng.randint(0, max(1, cw - 1))
            uy = cy + rng.randint(0, max(1, ch - 1))
            us = rng.randint(5, 12)
            g = rng.randint(18, 40)
            pygame.draw.circle(surface, (g - 8, g, g - 10), (ux, uy), us)

        # ---- Place tree canopies from assets ----
        available = [c for c in [canopy1, canopy2] if c is not None]

        if available:
            margin = 25
            safe_w = max(1, cw - margin * 2)
            safe_h = max(1, ch - margin * 2)
            area = safe_w * safe_h
            tree_count = max(3, int(area / 700))
            if cap_trees:
                tree_count = min(80, tree_count)

            trees = []
            for _ in range(tree_count):
                tx = cx + rng.randint(margin, max(margin + 1, cw - margin))
                ty = cy + rng.randint(margin, max(margin + 1, ch - margin))
                size = rng.randint(50, 90)
                rot = rng.choice([0, 90, 180, 270]) + rng.randint(-20, 20)
                ci = rng.randint(0, len(available) - 1)
                trees.append((tx, ty, size, rot, ci))

            trees.sort(key=lambda t: t[1])

            for tx, ty, size, rot, ci in trees:
                canopy = available[ci]
                scaled = pygame.transform.scale(canopy, (size, size))
                rotated = pygame.transform.rotate(scaled, rot)

                # Shadow (dark version, offset)
                shadow = rotated.copy()
                shadow.fill((0, 0, 0, 55), special_flags=pygame.BLEND_RGBA_MULT)
                sr = shadow.get_rect(center=(tx + 5, ty + 5))
                surface.blit(shadow, sr)

                # Canopy
                cr = rotated.get_rect(center=(tx, ty))
                surface.blit(rotated, cr)
        else:
            # Fallback: procedural trees if no assets found
            margin = 10
            area = max(1, (cw - margin * 2) * (ch - margin * 2))
            tree_count = max(2, int(area / 400))
            if cap_trees:
                tree_count = min(80, tree_count)

            trees = []
            for _ in range(tree_count):
                tx = cx + rng.randint(margin, max(margin + 1, cw - margin))
                ty = cy + rng.randint(margin, max(margin + 1, ch - margin))
                sz = rng.randint(14, 24)
                trees.append((tx, ty, sz))

            trees.sort(key=lambda t: t[1])

            for tx, ty, sz in trees:
                gv = rng.randint(-15, 15)
                pygame.draw.circle(
                    surface, (8, 18, 6), (tx + 3, ty + 3), sz + 2
                )
                pygame.draw.circle(
                    surface, (28 + gv, 85 + gv, 22 + gv), (tx, ty), sz
                )
                pygame.draw.circle(
                    surface,
                    (38 + gv, 110 + gv, 30 + gv),
                    (tx - 1, ty - 1),
                    int(sz * 0.75),
                )
                pygame.draw.circle(
                    surface,
                    (55 + gv, 145 + gv, 42 + gv),
                    (tx - sz // 4, ty - sz // 4),
                    int(sz * 0.5),
                )
                pygame.draw.circle(
                    surface,
                    (70 + gv, 170 + gv, 55 + gv),
                    (tx - sz // 3, ty - sz // 3),
                    int(sz * 0.28),
                )

    # ---- Forest edge (border where forest meets water) ----
    for cx, cy, cw, ch in cubes:
        pygame.draw.rect(surface, (10, 28, 8), (cx, cy, cw, ch), 3)

    return surface


# ================================================================
# ROCK RENDERING - Pre-rendered stone obstacles
# ================================================================
def create_rock_surface(cubes, w, h):
    """Pre-render rock obstacles as gray/brown stone shapes."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    rng = random.Random(314)

    for cx, cy, cw, ch in cubes:
        # Base rock fill
        pygame.draw.rect(surface, (85, 78, 68), (cx, cy, cw, ch))

        # Irregular stone texture
        num_stones = max(3, int(cw * ch / 500))
        for _ in range(num_stones):
            sx = cx + rng.randint(2, max(3, cw - 2))
            sy = cy + rng.randint(2, max(3, ch - 2))
            stone_size = rng.randint(6, 18)
            num_verts = rng.randint(5, 8)
            points = []
            for i in range(num_verts):
                ang = (i / num_verts) * math.pi * 2
                r = stone_size * rng.uniform(0.5, 1.0)
                px = max(cx, min(cx + cw, sx + math.cos(ang) * r))
                py = max(cy, min(cy + ch, sy + math.sin(ang) * r))
                points.append((int(px), int(py)))
            if len(points) >= 3:
                gray = rng.randint(55, 125)
                brown = rng.randint(0, 20)
                color = (min(255, gray + brown), min(255, gray + brown // 2), max(0, gray - brown // 2))
                pygame.draw.polygon(surface, color, points)
                highlight = tuple(min(255, c + 25) for c in color)
                pygame.draw.polygon(surface, highlight, points, 1)

        # Crack lines
        for _ in range(max(1, int(cw * ch / 1500))):
            lx1 = cx + rng.randint(3, max(4, cw - 3))
            ly1 = cy + rng.randint(3, max(4, ch - 3))
            lx2 = max(cx, min(cx + cw, lx1 + rng.randint(-25, 25)))
            ly2 = max(cy, min(cy + ch, ly1 + rng.randint(-25, 25)))
            pygame.draw.line(surface, (45, 40, 35), (lx1, ly1), (lx2, ly2), 1)

        # Dark border
        pygame.draw.rect(surface, (40, 35, 30), (cx, cy, cw, ch), 2)

    return surface


def create_snow_surface(cubes, w, h):
    """Create an icy/snowy-themed obstacle surface."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    surface.fill((200, 220, 245))  # Pale ice blue base

    for cx, cy, cw, ch in cubes:
        # Ice/snow base with white accent
        pygame.draw.rect(surface, (180, 210, 235), (cx, cy, cw, ch))

        # Scattered white snow circles
        rng = random.Random(hash((cx, cy, cw, ch)) % (2**32))
        for _ in range(rng.randint(3, 6)):
            sx = cx + rng.randint(5, cw - 5)
            sy = cy + rng.randint(5, ch - 5)
            sr = rng.randint(3, 12)
            pygame.draw.circle(surface, (245, 248, 255), (sx, sy), sr)

        # Icicle strokes (white/light blue)
        for _ in range(rng.randint(2, 4)):
            ix = cx + rng.randint(10, cw - 10)
            iy = cy + rng.randint(5, 15)
            pygame.draw.line(surface, (200, 230, 255), (ix, iy), (ix + rng.randint(-3, 3), iy + rng.randint(8, 20)), 2)

        # Ice cracks (darker blue-gray)
        for _ in range(rng.randint(1, 3)):
            crx1 = cx + rng.randint(0, cw)
            cry1 = cy + rng.randint(0, ch)
            crx2 = crx1 + rng.randint(-20, 20)
            cry2 = cry1 + rng.randint(-20, 20)
            pygame.draw.line(surface, (140, 170, 200), (crx1, cry1), (crx2, cry2), 1)

        # Border
        pygame.draw.rect(surface, (150, 180, 210), (cx, cy, cw, ch), 2)

    return surface


def create_desert_surface(cubes, w, h):
    """Create a sandy/desert-themed obstacle surface."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    # Don't fill entire surface - only fill obstacle areas

    for cx, cy, cw, ch in cubes:
        # Sand dune base
        pygame.draw.rect(surface, (190, 160, 90), (cx, cy, cw, ch))

        # Irregular rock polygons (darker stones)
        rng = random.Random(hash((cx, cy, cw, ch)) % (2**32))
        for _ in range(rng.randint(4, 7)):
            rock_x = cx + rng.randint(5, cw - 5)
            rock_y = cy + rng.randint(5, ch - 5)
            rock_w = rng.randint(20, 45)
            rock_h = rng.randint(15, 35)
            points = [
                (rock_x, rock_y),
                (rock_x + rock_w, rock_y + rng.randint(-5, 5)),
                (rock_x + rock_w + rng.randint(-10, 10), rock_y + rock_h),
                (rock_x + rng.randint(-5, 5), rock_y + rock_h),
            ]
            pygame.draw.polygon(surface, (100, 85, 60), points)
            pygame.draw.polygon(surface, (70, 60, 45), points, 2)

        # Sand grain dots
        for _ in range(rng.randint(8, 15)):
            gx = cx + rng.randint(0, cw)
            gy = cy + rng.randint(0, ch)
            gr = rng.randint(1, 2)
            pygame.draw.circle(surface, (160, 135, 75), (gx, gy), gr)

        # Border
        pygame.draw.rect(surface, (160, 125, 65), (cx, cy, cw, ch), 2)

    return surface


def create_tropics_surface(cubes, w, h):
    """Create a jungle/tropics-themed obstacle surface."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    surface.fill((30, 90, 35))  # Deep jungle green base

    for cx, cy, cw, ch in cubes:
        # Dense vegetation base
        pygame.draw.rect(surface, (25, 75, 30), (cx, cy, cw, ch))

        # Foliage circles (3 shades of green)
        rng = random.Random(hash((cx, cy, cw, ch)) % (2**32))
        for _ in range(rng.randint(6, 10)):
            fx = cx + rng.randint(5, cw - 5)
            fy = cy + rng.randint(5, ch - 5)
            fr = rng.randint(8, 20)
            shade = rng.choice([(45, 120, 50), (35, 100, 40), (50, 140, 55)])
            pygame.draw.circle(surface, shade, (fx, fy), fr)

        # Vine strokes (darker green)
        for _ in range(rng.randint(2, 4)):
            vx = cx + rng.randint(10, cw - 10)
            vy = cy + rng.randint(10, ch - 10)
            vx2 = vx + rng.randint(-30, 30)
            vy2 = vy + rng.randint(-30, 30)
            pygame.draw.line(surface, (15, 50, 20), (vx, vy), (vx2, vy2), 2)

        # Border
        pygame.draw.rect(surface, (15, 55, 20), (cx, cy, cw, ch), 2)

    return surface


# ================================================================
# SHORELINE FOAM (animated dots at water-forest boundary)
# ================================================================
def precompute_foam(cubes, w, h):
    pts = []
    rng = random.Random(789)
    for cx, cy, cw, ch in cubes:
        # Top edge
        for x in range(cx, cx + cw, 10):
            if 0 <= cy - 4 <= h:
                pts.append((x, cy - 4, rng.uniform(0, 6.28)))
        # Bottom edge
        for x in range(cx, cx + cw, 10):
            if 0 <= cy + ch + 4 <= h:
                pts.append((x, cy + ch + 4, rng.uniform(0, 6.28)))
        # Left edge
        for y in range(cy, cy + ch, 10):
            if 0 <= cx - 4 <= w:
                pts.append((cx - 4, y, rng.uniform(0, 6.28)))
        # Right edge
        for y in range(cy, cy + ch, 10):
            if 0 <= cx + cw + 4 <= w:
                pts.append((cx + cw + 4, y, rng.uniform(0, 6.28)))
    return [(x, y, p) for x, y, p in pts if 0 <= x <= w and 0 <= y <= h]


def draw_foam(screen, foam_pts, time, camera_y=0):
    for fx, fy, phase in foam_pts:
        sy = fy - camera_y
        if sy < -10 or sy > HEIGHT + 10:
            continue
        b = 0.5 + 0.5 * math.sin(time * 1.8 + phase)
        if b > 0.45:
            c = min(255, int(90 + b * 110))
            size = 1 + int(b * 1.5)
            pygame.draw.circle(screen, (c, min(255, c + 25), 255), (int(fx), int(sy)), size)


# ================================================================
# OAR (RAMP) ANIMATION
# ================================================================
class OarAnimator:
    """Animates left and right oar rowing strokes."""

    def __init__(self):
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_time = -1.0
        self.right_time = -1.0
        self.stroke_duration = 0.35
        self.max_sweep = 40

        self.left_splash = 0.0
        self.right_splash = 0.0

    def trigger_left(self):
        self.left_time = 0.0
        self.left_splash = 1.0

    def trigger_right(self):
        self.right_time = 0.0
        self.right_splash = 1.0

    def update(self, dt):
        if self.left_time >= 0:
            self.left_time += dt
            if self.left_time >= self.stroke_duration:
                self.left_time = -1.0
                self.left_angle = 0.0
            else:
                p = self.left_time / self.stroke_duration
                self.left_angle = math.sin(p * math.pi) * self.max_sweep

        if self.right_time >= 0:
            self.right_time += dt
            if self.right_time >= self.stroke_duration:
                self.right_time = -1.0
                self.right_angle = 0.0
            else:
                p = self.right_time / self.stroke_duration
                self.right_angle = math.sin(p * math.pi) * self.max_sweep

        self.left_splash = max(0, self.left_splash - dt * 3.5)
        self.right_splash = max(0, self.right_splash - dt * 3.5)


# ================================================================
# BOAT RENDERING (hull + deck + animated oars)
# ================================================================
def draw_boat(surface, pos, angle, oar_anim, speed=0):
    """Draw a detailed top-down boat with animated oar ramps."""

    # ---- Hull (outer shell) ----
    hull = [
        pygame.Vector2(0, -22),
        pygame.Vector2(4, -18),
        pygame.Vector2(8, -10),
        pygame.Vector2(10, 0),
        pygame.Vector2(10, 10),
        pygame.Vector2(8, 18),
        pygame.Vector2(4, 20),
        pygame.Vector2(0, 21),
        pygame.Vector2(-4, 20),
        pygame.Vector2(-8, 18),
        pygame.Vector2(-10, 10),
        pygame.Vector2(-10, 0),
        pygame.Vector2(-8, -10),
        pygame.Vector2(-4, -18),
    ]
    rot_hull = [pos + p.rotate(angle) for p in hull]

    # Shadow under boat
    shadow_off = pygame.Vector2(3, 3)
    pygame.draw.polygon(surface, (12, 25, 70), [p + shadow_off for p in rot_hull])

    # Hull base (dark wood)
    pygame.draw.polygon(surface, (110, 68, 28), rot_hull)
    pygame.draw.polygon(surface, (75, 45, 15), rot_hull, 2)

    # ---- Deck (lighter inner area) ----
    deck = [
        pygame.Vector2(0, -18),
        pygame.Vector2(3, -15),
        pygame.Vector2(6, -8),
        pygame.Vector2(7, 0),
        pygame.Vector2(7, 9),
        pygame.Vector2(6, 16),
        pygame.Vector2(3, 18),
        pygame.Vector2(0, 19),
        pygame.Vector2(-3, 18),
        pygame.Vector2(-6, 16),
        pygame.Vector2(-7, 9),
        pygame.Vector2(-7, 0),
        pygame.Vector2(-6, -8),
        pygame.Vector2(-3, -15),
    ]
    rot_deck = [pos + p.rotate(angle) for p in deck]
    pygame.draw.polygon(surface, (155, 105, 50), rot_deck)

    # Deck planks (cross lines)
    for plank_y in range(-14, 18, 4):
        p1 = pos + pygame.Vector2(-5, plank_y).rotate(angle)
        p2 = pos + pygame.Vector2(5, plank_y).rotate(angle)
        pygame.draw.line(
            surface,
            (125, 82, 35),
            (int(p1.x), int(p1.y)),
            (int(p2.x), int(p2.y)),
            1,
        )

    # Center plank (lengthwise)
    p1 = pos + pygame.Vector2(0, -16).rotate(angle)
    p2 = pos + pygame.Vector2(0, 17).rotate(angle)
    pygame.draw.line(
        surface, (130, 85, 38), (int(p1.x), int(p1.y)), (int(p2.x), int(p2.y)), 1
    )

    # Bow decoration
    bow = pos + pygame.Vector2(0, -22).rotate(angle)
    pygame.draw.circle(surface, (90, 55, 18), (int(bow.x), int(bow.y)), 3)
    pygame.draw.circle(surface, (145, 100, 42), (int(bow.x), int(bow.y)), 2)

    # ---- OARS (Ramps) ----
    for side in ("left", "right"):
        if side == "left":
            pivot_local = pygame.Vector2(-10, 4)
            sweep = oar_anim.left_angle
            extend = -1
            splash_val = oar_anim.left_splash
        else:
            pivot_local = pygame.Vector2(10, 4)
            sweep = oar_anim.right_angle
            extend = 1
            splash_val = oar_anim.right_splash

        pivot = pos + pivot_local.rotate(angle)

        # Oar direction: perpendicular to boat + animated sweep
        oar_ang = angle + extend * (90 + sweep)
        oar_dir = pygame.Vector2(0, -1).rotate(oar_ang)

        # Handle (inside boat)
        handle = pivot - oar_dir * 5
        # Shaft end
        shaft = pivot + oar_dir * 18

        # Draw shaft
        pygame.draw.line(
            surface,
            (100, 65, 22),
            (int(handle.x), int(handle.y)),
            (int(shaft.x), int(shaft.y)),
            3,
        )

        # Paddle blade at end of shaft
        paddle_end = shaft + oar_dir * 7
        perp = pygame.Vector2(oar_dir.y, -oar_dir.x)

        blade = [
            shaft + perp * 4,
            shaft - perp * 4,
            paddle_end - perp * 2.5,
            paddle_end + perp * 2.5,
        ]
        blade_int = [(int(p.x), int(p.y)) for p in blade]
        pygame.draw.polygon(surface, (125, 80, 32), blade_int)
        pygame.draw.polygon(surface, (85, 52, 18), blade_int, 1)

        # Oar lock at pivot
        pygame.draw.circle(surface, (70, 45, 15), (int(pivot.x), int(pivot.y)), 3)
        pygame.draw.circle(surface, (50, 30, 10), (int(pivot.x), int(pivot.y)), 3, 1)

        # Splash ring when oar dips
        if splash_val > 0.1:
            sp = paddle_end
            sz = int(5 + splash_val * 10)
            sc = (
                min(255, int(140 + splash_val * 115)),
                min(255, int(185 + splash_val * 70)),
                255,
            )
            pygame.draw.circle(surface, sc, (int(sp.x), int(sp.y)), sz, 1)
            if splash_val > 0.4:
                pygame.draw.circle(
                    surface, sc, (int(sp.x), int(sp.y)), sz + 5, 1
                )


# ================================================================
# WAKE EFFECT (trailing foam behind boat)
# ================================================================
class WakeSystem:
    def __init__(self):
        self.trail = []
        self.spawn_timer = 0

    def update(self, dt, boat_pos, boat_angle, speed):
        self.trail = [(x, y, a + dt) for x, y, a in self.trail if a + dt < 1.0]

        self.spawn_timer += dt
        if speed > 0.5 and self.spawn_timer > 0.04:
            self.spawn_timer = 0
            back = pygame.Vector2(0, 1).rotate(boat_angle)
            right = pygame.Vector2(1, 0).rotate(boat_angle)
            stern = boat_pos + back * 20
            spread = min(1.0, speed / 5.0)

            for s in (-1, 1):
                px = stern.x + right.x * s * (4 + spread * 3)
                py = stern.y + right.y * s * (4 + spread * 3)
                self.trail.append((px, py, 0))

    def draw(self, screen, camera_y=0):
        for px, py, age in self.trail:
            sy = py - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            progress = age / 1.0
            size = max(1, int(3 * (1 - progress * 0.7)))
            brightness = int(180 * (1 - progress))
            if brightness > 25:
                c = (
                    min(255, 80 + brightness // 2),
                    min(255, 120 + brightness // 2),
                    255,
                )
                pygame.draw.circle(screen, c, (int(px), int(sy)), size)

    def clear(self):
        self.trail = []
        self.spawn_timer = 0


# ================================================================
# PARTICLE SYSTEM (for splash effects)
# ================================================================
class ParticleSystem:
    """General purpose particle system with gravity and fading."""

    def __init__(self):
        # Each particle: [x, y, vx, vy, life, max_life, color, size]
        self.particles = []

    def emit_splash(self, x, y, count):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(30, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.3, 0.8)
            color = (
                random.randint(150, 220),
                random.randint(200, 240),
                255,
            )
            size = random.uniform(1.5, 4.0)
            self.particles.append([x, y, vx, vy, life, life, color, size])

    def update(self, dt):
        alive = []
        for p in self.particles:
            p[4] -= dt  # life
            if p[4] <= 0:
                continue
            p[3] += 150 * dt  # gravity on vy
            p[0] += p[2] * dt  # x += vx*dt
            p[1] += p[3] * dt  # y += vy*dt
            alive.append(p)
        self.particles = alive

    def draw(self, screen, camera_y=0):
        for p in self.particles:
            x, y, vx, vy, life, max_life, color, size = p
            sy = y - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            alpha_ratio = max(0, life / max_life)
            r = min(255, int(color[0] * alpha_ratio))
            g = min(255, int(color[1] * alpha_ratio))
            b = min(255, int(color[2] * alpha_ratio))
            sz = max(1, int(size * alpha_ratio))
            pygame.draw.circle(screen, (r, g, b), (int(x), int(sy)), sz)


# ================================================================
# CRASH ANIMATION
# ================================================================
class CrashAnimation:
    """Boat crash: debris particles + splash rings + callback on complete."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.duration = 1.2
        self.crash_pos = pygame.Vector2(0, 0)
        self.debris = []
        self.splash_rings = []
        self.on_complete = None

    def trigger(self, pos, angle, on_complete):
        self.active = True
        self.timer = 0
        self.crash_pos = pygame.Vector2(pos.x, pos.y)
        self.on_complete = on_complete
        # Wood debris
        self.debris = []
        for _ in range(random.randint(14, 20)):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(80, 220)
            life = random.uniform(0.5, 1.1)
            color = random.choice([
                (139, 69, 19), (110, 68, 28), (155, 105, 50),
                (100, 65, 22), (125, 80, 32), (75, 45, 15)
            ])
            self.debris.append([
                pos.x, pos.y,
                math.cos(ang) * spd, math.sin(ang) * spd,
                random.uniform(3, 7), color, life, life
            ])
        # Splash rings
        self.splash_rings = []
        for i in range(3):
            self.splash_rings.append({
                "x": pos.x, "y": pos.y,
                "radius": 5.0, "max_radius": 35 + i * 18,
                "delay": i * 0.12, "life": 0.7, "max_life": 0.7
            })

    def update(self, dt):
        if not self.active:
            return
        self.timer += dt
        # Debris
        alive = []
        for d in self.debris:
            d[6] -= dt
            if d[6] <= 0:
                continue
            d[3] += 250 * dt  # gravity
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            alive.append(d)
        self.debris = alive
        # Splash rings
        for ring in self.splash_rings:
            if ring["delay"] > 0:
                ring["delay"] -= dt
                continue
            ring["life"] -= dt
            ring["radius"] += ring["max_radius"] / ring["max_life"] * dt
        # Done?
        if self.timer >= self.duration:
            self.active = False
            if self.on_complete:
                self.on_complete()

    def draw(self, screen, camera_y=0):
        if not self.active:
            return
        for ring in self.splash_rings:
            if ring["delay"] > 0 or ring["life"] <= 0:
                continue
            alpha = max(0, ring["life"] / ring["max_life"])
            r = int(ring["radius"])
            sy = ring["y"] - camera_y
            bright = int(180 * alpha)
            c = (min(255, 100 + bright), min(255, 150 + bright // 2), 255)
            if r > 1:
                pygame.draw.circle(screen, c, (int(ring["x"]), int(sy)), r, max(1, int(3 * alpha)))
        for d in self.debris:
            x, y, vx, vy, size, color, life, max_life = d
            sy = y - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            alpha = max(0, life / max_life)
            c = tuple(max(0, int(v * alpha)) for v in color)
            sz = max(1, int(size * alpha))
            pygame.draw.circle(screen, c, (int(x), int(sy)), sz)


# ================================================================
# FISH SYSTEM (small fish swimming in the river)
# ================================================================
class FishSystem:
    """Small ambient fish swimming horizontally in the river."""

    def __init__(self, map_height):
        self.fish = []
        rng = random.Random(999)
        for _ in range(25):
            x = rng.uniform(220, WIDTH - 220)
            y = rng.uniform(100, map_height - 100)
            vx = rng.choice([-1, 1]) * rng.uniform(20, 60)
            size = rng.randint(4, 8)
            r = rng.randint(140, 200)
            g = rng.randint(160, 220)
            b = rng.randint(60, 120)
            self.fish.append({
                "x": x, "y": y, "vx": vx, "size": size,
                "color": (r, g, b),
            })

    def update(self, dt):
        for f in self.fish:
            f["x"] += f["vx"] * dt
            # Bounce off river walls
            if f["x"] < 220:
                f["x"] = 220
                f["vx"] = abs(f["vx"])
            elif f["x"] > WIDTH - 220:
                f["x"] = WIDTH - 220
                f["vx"] = -abs(f["vx"])

    def draw(self, screen, camera_y=0):
        for f in self.fish:
            sy = f["y"] - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            sx = int(f["x"])
            isy = int(sy)
            sz = f["size"]
            # Body ellipse
            pygame.draw.ellipse(screen, f["color"],
                                (sx - sz, isy - sz // 2, sz * 2, sz))
            # Tail triangle
            direction = 1 if f["vx"] > 0 else -1
            tail_x = sx - direction * sz
            pygame.draw.polygon(screen, f["color"], [
                (tail_x, isy),
                (tail_x - direction * sz, isy - sz // 2),
                (tail_x - direction * sz, isy + sz // 2),
            ])


# ================================================================
# SCREEN SHAKE
# ================================================================
class ScreenShake:
    """Triggers screen shake effects that decay over time."""

    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.timer = 0
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, intensity, duration):
        self.intensity = intensity
        self.duration = duration
        self.timer = duration

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 0
                self.offset_x = 0
                self.offset_y = 0
            else:
                progress = self.timer / self.duration
                current_intensity = self.intensity * progress
                self.offset_x = random.uniform(-current_intensity, current_intensity)
                self.offset_y = random.uniform(-current_intensity, current_intensity)
        else:
            self.offset_x = 0
            self.offset_y = 0


# ================================================================
# FADE TRANSITION
# ================================================================
class FadeTransition:
    """Fade to black and back, firing a callback at peak darkness."""

    def __init__(self):
        self.active = False
        self.alpha = 0
        self.fading_in = True  # True = going to black, False = coming back
        self.callback = None
        self.speed = 500  # alpha per second
        self.callback_fired = False

    def start(self, callback):
        self.active = True
        self.alpha = 0
        self.fading_in = True
        self.callback = callback
        self.callback_fired = False

    def update(self, dt):
        if not self.active:
            return
        if self.fading_in:
            self.alpha += self.speed * dt
            if self.alpha >= 255:
                self.alpha = 255
                if not self.callback_fired and self.callback:
                    self.callback()
                    self.callback_fired = True
                self.fading_in = False
        else:
            self.alpha -= self.speed * dt
            if self.alpha <= 0:
                self.alpha = 0
                self.active = False

    def draw(self, screen):
        if not self.active:
            return
        if self.alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(min(255, max(0, self.alpha)))))
            screen.blit(overlay, (0, 0))


# ================================================================
# WIND SYSTEM (periodic gusts for Level 2)
# ================================================================
class WindSystem:
    """Periodic wind gusts that push the boat sideways."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.next_gust_in = random.uniform(4, 7)
        self.gust_duration = 0
        self.gust_timer = 0
        self.direction = 0  # -1 left, 1 right
        self.strength = 0

    def update(self, dt):
        if self.active:
            self.gust_timer += dt
            if self.gust_timer >= self.gust_duration:
                self.active = False
                self.next_gust_in = random.uniform(4, 7)
                self.timer = 0
        else:
            self.timer += dt
            if self.timer >= self.next_gust_in:
                self.active = True
                self.gust_timer = 0
                self.gust_duration = random.uniform(1.5, 3.0)
                self.direction = random.choice([-1, 1])
                self.strength = random.uniform(0.8, 1.5)

    def get_force(self):
        if not self.active:
            return pygame.Vector2(0, 0)
        # Sine ease: ramps up then down
        progress = self.gust_timer / self.gust_duration
        ease = math.sin(progress * math.pi)
        return pygame.Vector2(self.direction * self.strength * ease, 0)


# ================================================================
# RIVER CURRENT (constant downstream push for Level 2)
# ================================================================
class RiverCurrent:
    """Constant downstream push, stronger at center, weaker at edges."""

    def __init__(self, strength=30):
        self.strength = strength

    def get_force(self, boat_x):
        # Stronger at center of river (between the walls at x=200 and x=WIDTH-200)
        river_left = 200
        river_right = WIDTH - 200
        river_width = river_right - river_left
        if river_width <= 0:
            return pygame.Vector2(0, 0)
        # Normalize position to 0..1 (0=edge, 1=center)
        center = (river_left + river_right) / 2
        dist_from_center = abs(boat_x - center) / (river_width / 2)
        dist_from_center = min(1.0, dist_from_center)
        # Stronger at center: 1.0 at center, 0.3 at edges
        factor = 1.0 - 0.7 * dist_from_center
        return pygame.Vector2(0, self.strength * factor)


# ================================================================
# START MENU
# ================================================================
class Button:
    """Polished rounded button with hover/press effects and consistent styling."""

    RADIUS = 20

    def __init__(self, x, y, w, h, text, color, hover_color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.pressed = False
        self._blend = 0.0

    def update(self, mouse_pos, mouse_pressed, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.hovered else 0.0
        self._blend += (target - self._blend) * min(1.0, 10.0 * dt)
        clicked = False
        if self.hovered and mouse_pressed:
            if not self.pressed:
                clicked = True
            self.pressed = True
        else:
            self.pressed = False
        return clicked

    def draw(self, surface):
        t = self._blend
        r = tuple(int(self.color[i] + (self.hover_color[i] - self.color[i]) * t) for i in range(3))

        # Hover scale
        inflate = int(t * 6)
        draw_rect = self.rect.inflate(inflate * 2, inflate)

        # Soft wide shadow
        shadow_surf = pygame.Surface((draw_rect.w + 16, draw_rect.h + 12), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, int(35 + 15 * t)),
                         pygame.Rect(4, 4, draw_rect.w + 8, draw_rect.h + 4),
                         border_radius=self.RADIUS + 2)
        surface.blit(shadow_surf, (draw_rect.x - 8, draw_rect.y - 2))

        # Button body
        btn_surf = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (*r, 240), pygame.Rect(0, 0, draw_rect.w, draw_rect.h),
                         border_radius=self.RADIUS)

        # Top highlight (subtle gradient feel)
        highlight = pygame.Surface((draw_rect.w - 8, draw_rect.h // 3), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, int(15 + 10 * t)))
        btn_surf.blit(highlight, (4, 2))

        # Border
        border_alpha = int(50 + 60 * t)
        border_c = tuple(min(255, c + 50) for c in r)
        pygame.draw.rect(btn_surf, (*border_c, border_alpha),
                         pygame.Rect(0, 0, draw_rect.w, draw_rect.h),
                         width=2, border_radius=self.RADIUS)

        surface.blit(btn_surf, draw_rect.topleft)

        # Text with subtle shadow
        txt = button_font.render(self.text, True, self.text_color)
        txt_rect = txt.get_rect(center=draw_rect.center)
        shadow_txt = button_font.render(self.text, True, (0, 0, 0))
        shadow_txt.set_alpha(60)
        surface.blit(shadow_txt, txt_rect.move(1, 2))
        surface.blit(txt, txt_rect)


class Slider:
    """Horizontal slider for settings menus."""

    def __init__(self, x, y, width, label, value=0.5, color=(60, 130, 220)):
        self.x = x
        self.y = y
        self.width = width
        self.label = label
        self.value = value
        self.color = color
        self.track_height = 8
        self.knob_radius = 12
        self.dragging = False
        self._hover = False

    def update(self, mouse_pos, mouse_down):
        mx, my = mouse_pos
        knob_x = self.x + int(self.value * self.width)
        knob_y = self.y
        dx = mx - knob_x
        dy = my - knob_y

        # Check if mouse is on knob or track
        on_knob = dx * dx + dy * dy <= (self.knob_radius + 4) ** 2
        on_track = (self.x - 5 <= mx <= self.x + self.width + 5 and
                    abs(my - self.y) <= 20)
        self._hover = on_knob or on_track

        if mouse_down:
            if self.dragging or on_knob or on_track:
                self.dragging = True
                raw = (mx - self.x) / self.width
                self.value = max(0.0, min(1.0, raw))
        else:
            self.dragging = False

        return self.value

    def draw(self, surface, font):
        # Label
        label_surf = font.render(self.label, True, (200, 215, 235))
        surface.blit(label_surf, (self.x - 25 - label_surf.get_width(), self.y - 10))

        # Track background
        track_rect = pygame.Rect(self.x, self.y - self.track_height // 2,
                                 self.width, self.track_height)
        pygame.draw.rect(surface, (40, 45, 60), track_rect, border_radius=4)

        # Filled portion
        fill_w = int(self.value * self.width)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.x, self.y - self.track_height // 2,
                                    fill_w, self.track_height)
            pygame.draw.rect(surface, self.color, fill_rect, border_radius=4)

        # Knob
        knob_x = self.x + fill_w
        knob_color = tuple(min(255, c + 40) for c in self.color) if self._hover else self.color
        pygame.draw.circle(surface, (20, 25, 35), (knob_x, self.y), self.knob_radius + 1)
        pygame.draw.circle(surface, knob_color, (knob_x, self.y), self.knob_radius)
        pygame.draw.circle(surface, (255, 255, 255, 80), (knob_x, self.y), self.knob_radius, 2)

        # Value percentage
        pct = f"{int(self.value * 100)}%"
        pct_surf = font.render(pct, True, (180, 195, 210))
        surface.blit(pct_surf, (self.x + self.width + 15, self.y - 10))


class ModeCard:
    """Premium card for mode selection with expand/glow/hover states."""

    RADIUS = 22

    def __init__(self, x, y, w, h, title, bg_color, icon_text, locked=False, icon_image=None):
        self.base_x = x
        self.base_y = y
        self.base_w = w
        self.base_h = h
        self.title = title
        self.bg_color = bg_color
        self.icon_text = icon_text
        self.locked = locked
        self._icon_img_raw = None
        self._icon_img_full = None  # Pre-scaled to expanded size
        if icon_image:
            try:
                self._icon_img_raw = pygame.image.load(icon_image).convert_alpha()
                # Pre-scale to the fully expanded card size
                max_expand = 40
                full_w = w + max_expand // 2
                full_h = h + max_expand
                self._icon_img_full = pygame.transform.smoothscale(self._icon_img_raw, (full_w, full_h))
            except Exception:
                self._icon_img_raw = None
                self._icon_img_full = None
        self.selected = False
        self.hovered = False
        self.expand_amount = 0.0
        self.hover_blend = 0.0
        self._bob_phase = random.uniform(0, 6.28)
        self._alpha_blend = 0.0

    def get_rect(self):
        expand = int(self.expand_amount)
        return pygame.Rect(self.base_x - expand // 4, self.base_y - expand // 2,
                           self.base_w + expand // 2, self.base_h + expand)

    def update(self, mouse_pos, mouse_click, dt, game_time):
        rect = self.get_rect()
        self.hovered = rect.collidepoint(mouse_pos)

        target_h = 1.0 if self.hovered else 0.0
        self.hover_blend += (target_h - self.hover_blend) * min(1.0, 10.0 * dt)

        # Expand on hover (not on select)
        expand_target = 40.0 if (self.hovered and not self.locked) else 0.0
        self.expand_amount += (expand_target - self.expand_amount) * min(1.0, 8.0 * dt)

        alpha_target = 1.0 if (self.hovered or self.selected) else 0.7
        self._alpha_blend += (alpha_target - self._alpha_blend) * min(1.0, 6.0 * dt)

        clicked = False
        if self.hovered and mouse_click and not self.locked:
            clicked = True
        return clicked

    def draw(self, surface, game_time, unused1, unused2):
        rect = self.get_rect()
        R = self.RADIUS

        # --- Soft shadow behind card ---
        shadow_w, shadow_h = rect.w + 12, rect.h + 10
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        shadow_alpha = int(30 + 40 * self._alpha_blend)
        pygame.draw.rect(shadow_surf, (0, 0, 0, shadow_alpha),
                         pygame.Rect(0, 0, shadow_w, shadow_h), border_radius=R + 4)
        surface.blit(shadow_surf, (rect.x - 6, rect.y + 4))

        # --- Glow layers on hover ---
        if self.hovered and not self.locked:
            glow_i = 0.5 + 0.5 * math.sin(game_time * 3.5)
            for i in range(3, 0, -1):
                gw, gh = rect.w + i * 8, rect.h + i * 8
                glow_s = pygame.Surface((gw, gh), pygame.SRCALPHA)
                ga = int((25 + 18 * glow_i) * self.hover_blend / i)
                pygame.draw.rect(glow_s, (100, 200, 255, ga),
                                 pygame.Rect(0, 0, gw, gh), border_radius=R + i * 2)
                surface.blit(glow_s, (rect.x - i * 4, rect.y - i * 4))

        # --- Card body ---
        card_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)

        # Fill with image — always at full expanded scale, cropped to current rect
        if self._icon_img_full:
            full_w, full_h = self._icon_img_full.get_size()
            # Crop from center of full image to current card size
            crop_x = (full_w - rect.w) // 2
            crop_y = (full_h - rect.h) // 2
            crop_rect = pygame.Rect(crop_x, crop_y, rect.w, rect.h)
            cropped = self._icon_img_full.subsurface(crop_rect).copy()
            # Apply rounded corners by masking
            mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255),
                             pygame.Rect(0, 0, rect.w, rect.h), border_radius=R)
            cropped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            card_surf.blit(cropped, (0, 0))
        else:
            # Fallback: dark glass background
            base_r, base_g, base_b = self.bg_color
            if self.locked:
                gray = (base_r + base_g + base_b) // 4
                bg = (gray, gray, int(gray * 1.1))
            else:
                bg = (base_r // 2 + 10, base_g // 2 + 10, base_b // 2 + 10)
            card_alpha = int(180 + 50 * self._alpha_blend)
            pygame.draw.rect(card_surf, (*bg, card_alpha),
                             pygame.Rect(0, 0, rect.w, rect.h), border_radius=R)

        # Dark gradient at bottom for title readability
        title_bar_h = 60
        title_bar = pygame.Surface((rect.w, title_bar_h), pygame.SRCALPHA)
        for row in range(title_bar_h):
            a = int(180 * (row / title_bar_h) ** 1.5)
            pygame.draw.line(title_bar, (0, 0, 0, a), (0, row), (rect.w, row))
        card_surf.blit(title_bar, (0, rect.h - title_bar_h))

        # Title text
        title_surf = card_title_font.render(self.title, True, (230, 240, 255))
        card_surf.blit(title_surf, title_surf.get_rect(center=(rect.w // 2, rect.h - 22)))

        # --- Lock overlay ---
        if self.locked:
            lock_overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            lock_overlay.fill((0, 0, 0, 120))
            pygame.draw.rect(lock_overlay, (0, 0, 0, 0),
                             pygame.Rect(0, 0, rect.w, rect.h), border_radius=R)
            card_surf.blit(lock_overlay, (0, 0))

            lx, ly = rect.w // 2, rect.h // 2 - 15
            pygame.draw.rect(card_surf, (190, 170, 60),
                             pygame.Rect(lx - 20, ly, 40, 30), border_radius=6)
            pygame.draw.rect(card_surf, (150, 130, 40),
                             pygame.Rect(lx - 20, ly, 40, 30), width=2, border_radius=6)
            pygame.draw.arc(card_surf, (190, 170, 60),
                            pygame.Rect(lx - 13, ly - 22, 26, 26), 0, math.pi, 4)
            pygame.draw.circle(card_surf, (90, 70, 25), (lx, ly + 12), 5)
            pygame.draw.rect(card_surf, (90, 70, 25),
                             pygame.Rect(lx - 2, ly + 15, 4, 8))
            lock_label = card_sub_font.render("LOCKED", True, (190, 170, 60))
            card_surf.blit(lock_label, lock_label.get_rect(center=(rect.w // 2, ly + 45)))

        # --- Border: shine on hover, subtle on selected, dim otherwise ---
        if self.hovered and not self.locked:
            glow_i = 0.5 + 0.5 * math.sin(game_time * 3.5)
            border_a = int((180 + 75 * glow_i) * self.hover_blend)
            pygame.draw.rect(card_surf, (130, 200, 255, border_a),
                             pygame.Rect(0, 0, rect.w, rect.h), width=2, border_radius=R)
        elif self.selected:
            pygame.draw.rect(card_surf, (130, 200, 255, 160),
                             pygame.Rect(0, 0, rect.w, rect.h), width=2, border_radius=R)
        else:
            pygame.draw.rect(card_surf, (80, 100, 140, int(30 + 30 * self._alpha_blend)),
                             pygame.Rect(0, 0, rect.w, rect.h), width=1, border_radius=R)

        surface.blit(card_surf, (rect.x, rect.y))


class SeasonItem:
    """Represents a season/level in the seasons scroll menu."""

    def __init__(self, name, subtitle, bg_color, accent_color, playable=True):
        self.name = name
        self.subtitle = subtitle
        self.bg_color = bg_color
        self.accent_color = accent_color
        self.playable = playable


def draw_menu(screen, water, game_time, dt, buttons, menu_boat_angle):
    """Draw the start menu screen with polished typography and layout."""

    # Animated water background
    water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))

    # Dark overlay with subtle vignette
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 80))
    screen.blit(overlay, (0, 0))

    # Center vignette (darker edges)
    vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(6):
        r = pygame.Rect(i * 30, i * 20, WIDTH - i * 60, HEIGHT - i * 40)
        pygame.draw.rect(vig, (0, 0, 0, max(0, 25 - i * 5)), r)
    screen.blit(vig, (0, 0))

    # Decorative boat floating gently
    menu_boat_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2 - 50 + math.sin(game_time * 0.8) * 6)
    menu_oar = OarAnimator()
    menu_oar.left_angle = math.sin(game_time * 2) * 15
    menu_oar.right_angle = math.sin(game_time * 2 + math.pi) * 15
    menu_oar.left_splash = 0
    menu_oar.right_splash = 0
    draw_boat(screen, menu_boat_pos, menu_boat_angle, menu_oar, 0)

    # Title
    title_y = 60
    title_str = "CROSS RIVER"

    # Soft glow behind title
    for offset, alpha in [(3, 30), (1, 50)]:
        glow = menu_title_font.render(title_str, True, (60, 130, 220))
        glow.set_alpha(alpha)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + offset, title_y + offset)))

    # Main title
    title_surf = menu_title_font.render(title_str, True, (210, 230, 250))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, title_y)))

    # Subtitle with breathing room
    sub_str = "Navigate the river. Avoid the forest."
    sub_surf = subtitle_font.render(sub_str, True, (140, 170, 200))
    screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, title_y + 50)))

    # Thin separator
    line_y = title_y + 75
    sep_surf = pygame.Surface((240, 1), pygame.SRCALPHA)
    for x in range(240):
        a = int(60 * (1.0 - abs(x - 120) / 120.0))
        sep_surf.set_at((x, 0), (100, 150, 220, a))
    screen.blit(sep_surf, (WIDTH // 2 - 120, line_y))

    # Buttons
    for btn in buttons:
        btn.draw(screen)



def draw_settings(screen, water, game_time, dt, sliders, back_btn):
    """Draw the settings menu screen."""
    water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 130))
    screen.blit(overlay, (0, 0))

    # No panel - sliders float on overlay

    # Title
    title_str = "SETTINGS"
    title_surf = title_font.render(title_str, True, (210, 225, 245))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 100)))

    # Sliders
    for s in sliders:
        s.draw(screen, card_sub_font)

    back_btn.draw(screen)


def draw_mode_select(screen, water, game_time, dt, cards, back_btn):
    """Draw the mode selection screen."""
    water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 80))
    screen.blit(overlay, (0, 0))

    # Title
    title_str = "SELECT MODE"
    title_surf = title_font.render(title_str, True, (210, 225, 245))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 55)))

    # Subtitle
    sub = subtitle_font.render("Choose how you want to play", True, (120, 150, 185))
    screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 95)))

    # Cards
    for card in cards:
        card.draw(screen, game_time, None, None)

    back_btn.draw(screen)


def draw_seasons_menu(screen, water, game_time, dt, seasons, scroll_idx, scroll_offset,
                      bg_color_current, play_btn, back_btn):
    """Draw the seasons selection menu with animated video background."""
    # Animated video background for selected season
    vid = season_videos[scroll_idx] if scroll_idx < len(season_videos) else None
    if vid and vid._ready:
        vid.update(dt)
        vid.draw(screen)
    else:
        r, g, b = bg_color_current
        screen.fill((int(r), int(g), int(b)))

    # Dark gradient overlay for readability
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 90))
    screen.blit(overlay, (0, 0))

    # Title
    title_str = "SELECT SEASON"
    title_surf = title_font.render(title_str, True, (210, 225, 245))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 85)))

    sub = subtitle_font.render("Choose your environment", True, (255, 255, 255))
    screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 120)))

    # Season items
    center_y = HEIGHT // 2
    item_spacing = 110
    R = 18

    # Up/down chevron arrows
    if scroll_idx > 0:
        pulse = 0.5 + 0.5 * math.sin(game_time * 3)
        a = int(120 + 100 * pulse)
        pts = [(WIDTH // 2, center_y - item_spacing - 45),
               (WIDTH // 2 - 14, center_y - item_spacing - 30),
               (WIDTH // 2 + 14, center_y - item_spacing - 30)]
        chev_s = pygame.Surface((30, 18), pygame.SRCALPHA)
        pygame.draw.polygon(screen, (180, 210, 255, a), pts)

    if scroll_idx < len(seasons) - 1:
        pulse = 0.5 + 0.5 * math.sin(game_time * 3 + math.pi)
        a = int(120 + 100 * pulse)
        pts = [(WIDTH // 2, center_y + item_spacing + 45),
               (WIDTH // 2 - 14, center_y + item_spacing + 30),
               (WIDTH // 2 + 14, center_y + item_spacing + 30)]
        pygame.draw.polygon(screen, (180, 210, 255, a), pts)

    # Draw season cards
    for i, season in enumerate(seasons):
        offset_from_center = i - scroll_idx
        if abs(offset_from_center) > 1:
            continue

        y_pos = center_y + offset_from_center * item_spacing
        is_selected = (i == scroll_idx)

        # Card dimensions
        card_w = 650 if is_selected else 520
        card_h = 90 if is_selected else 65
        card_x = WIDTH // 2 - card_w // 2
        card_y = y_pos - card_h // 2

        # Shadow
        if is_selected:
            shadow = pygame.Surface((card_w + 12, card_h + 10), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 35),
                             pygame.Rect(0, 0, card_w + 12, card_h + 10), border_radius=R + 3)
            screen.blit(shadow, (card_x - 6, card_y + 2))

        # Glow for selected
        if is_selected:
            glow_i = 0.5 + 0.5 * math.sin(game_time * 3.5)
            for gi in range(2, 0, -1):
                gs = pygame.Surface((card_w + gi * 8, card_h + gi * 8), pygame.SRCALPHA)
                ga = int((25 + 15 * glow_i) / gi)
                pygame.draw.rect(gs, (100, 200, 255, ga),
                                 pygame.Rect(0, 0, gs.get_width(), gs.get_height()),
                                 border_radius=R + gi * 2)
                screen.blit(gs, (card_x - gi * 4, card_y - gi * 4))

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)

        # Card background
        ar, ag, ab = season.accent_color
        if is_selected:
            pygame.draw.rect(card_surf, (ar // 2 + 10, ag // 2 + 10, ab // 2 + 10, 200),
                             pygame.Rect(0, 0, card_w, card_h), border_radius=R)
        else:
            pygame.draw.rect(card_surf, (ar // 3, ag // 3, ab // 3, 120),
                             pygame.Rect(0, 0, card_w, card_h), border_radius=R)

        # Season name
        if is_selected:
            name_surf = card_title_font.render(season.name, True, (240, 245, 255))
            name_y = card_h // 2 - 12
        else:
            name_surf = card_sub_font.render(season.name, True, (160, 175, 200))
            name_y = card_h // 2
        card_surf.blit(name_surf, name_surf.get_rect(center=(card_w // 2, name_y)))

        # Subtitle for selected
        if is_selected:
            sub_surf = card_sub_font.render(season.subtitle, True, (170, 195, 225))
            card_surf.blit(sub_surf, sub_surf.get_rect(center=(card_w // 2, card_h // 2 + 16)))

        # Border
        if is_selected:
            glow_i = 0.5 + 0.5 * math.sin(game_time * 3.5)
            ba = int(160 + 80 * glow_i)
            pygame.draw.rect(card_surf, (130, 200, 255, ba),
                             pygame.Rect(0, 0, card_w, card_h), width=2, border_radius=R)
        else:
            pygame.draw.rect(card_surf, (70, 90, 130, 50),
                             pygame.Rect(0, 0, card_w, card_h), width=1, border_radius=R)

        screen.blit(card_surf, (card_x, card_y))

    # Play button (only if selected season is playable)
    if seasons[scroll_idx].playable:
        play_btn.draw(screen)

    back_btn.draw(screen)


def draw_tutorial(screen, water, game_time, dt, boat_pos, boat_angle, oar_anim,
                  wake, step, prompt_text, prompt_alpha):
    """Draw the tutorial screen."""
    water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))

    # Boat
    wake.draw(screen)
    draw_boat(screen, boat_pos, boat_angle, oar_anim, 0)

    # Prompt text with fade
    if prompt_text:
        prompt_surf = font.render(prompt_text, True, (255, 255, 255))
        prompt_surf.set_alpha(int(prompt_alpha))
        prompt_rect = prompt_surf.get_rect(center=(WIDTH // 2, 100))

        # Glow behind text
        glow_surf = font.render(prompt_text, True, (80, 180, 255))
        glow_surf.set_alpha(int(prompt_alpha * 0.4))
        screen.blit(glow_surf, glow_surf.get_rect(center=(WIDTH // 2 + 2, 102)))
        screen.blit(prompt_surf, prompt_rect)

        # Pulsing highlight
        pulse = 0.5 + 0.5 * math.sin(game_time * 3)
        arrow_alpha = int((160 + 80 * pulse) * (prompt_alpha / 255.0))

        # Draw arrow key indicator
        if step == 0:
            _draw_key_indicator(screen, WIDTH // 2, 180, "RIGHT", arrow_alpha, game_time)
        elif step == 1:
            _draw_key_indicator(screen, WIDTH // 2, 180, "LEFT", arrow_alpha, game_time)


def _draw_key_indicator(screen, x, y, direction, alpha, game_time):
    """Draw an arrow key indicator."""
    key_size = 60
    key_surf = pygame.Surface((key_size, key_size), pygame.SRCALPHA)

    # Key background
    pygame.draw.rect(key_surf, (40, 60, 100, min(255, alpha)),
                     pygame.Rect(0, 0, key_size, key_size), border_radius=10)
    pulse = 0.5 + 0.5 * math.sin(game_time * 4)
    border_a = min(255, int(alpha * (0.6 + 0.4 * pulse)))
    pygame.draw.rect(key_surf, (100, 180, 255, border_a),
                     pygame.Rect(0, 0, key_size, key_size), width=2, border_radius=10)

    # Arrow
    cx, cy = key_size // 2, key_size // 2
    arrow_a = min(255, alpha)
    if direction == "RIGHT":
        pts = [(cx + 12, cy), (cx - 6, cy - 10), (cx - 6, cy + 10)]
    else:
        pts = [(cx - 12, cy), (cx + 6, cy - 10), (cx + 6, cy + 10)]
    pygame.draw.polygon(key_surf, (220, 240, 255, arrow_a), pts)

    screen.blit(key_surf, (x - key_size // 2, y))


# ================================================================
# GAME SETUP
# ================================================================

# Game state
game_state = "menu"  # "menu", "playing", "level1_complete", "level2", "level2_win",
#                       "settings", "mode_select", "tutorial", "seasons", "level3"

# Menu buttons (Play, Settings, Quit)
btn_play = Button(WIDTH // 2, HEIGHT // 2 + 50, 220, 55, "PLAY", (30, 100, 200), (50, 140, 255))
btn_settings = Button(WIDTH // 2, HEIGHT // 2 + 120, 220, 55, "SETTINGS", (45, 85, 60), (65, 130, 85))
btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 190, 220, 55, "QUIT", (60, 60, 75), (90, 90, 110))
menu_buttons = [btn_play, btn_settings, btn_quit]
menu_boat_angle = 0

# ---- Settings state ----
_slider_x = WIDTH // 2 - 100
_slider_w = 220
settings_sliders = [
    Slider(_slider_x, HEIGHT // 2 - 110, _slider_w, "Music", volume_music, (50, 120, 200)),
    Slider(_slider_x, HEIGHT // 2 - 20, _slider_w, "SFX", volume_sfx, (200, 100, 50)),
    Slider(_slider_x, HEIGHT // 2 + 70, _slider_w, "Ambience", volume_ambience, (50, 160, 80)),
]
settings_back_btn = Button(WIDTH // 2, HEIGHT // 2 + 200, 180, 50, "BACK", (60, 60, 75), (90, 90, 110))

# ---- Mode Select state ----
card_w, card_h = 280, 300
card_gap = 35
total_cards_w = card_w * 3 + card_gap * 2
card_start_x = (WIDTH - total_cards_w) // 2
card_y = HEIGHT // 2 - card_h // 2 + 20

_assets = os.path.join(os.path.dirname(__file__), "assets")
mode_cards = [
    ModeCard(card_start_x, card_y, card_w, card_h,
             "Tutorial", (40, 100, 180), "?", icon_image=os.path.join(_assets, "tutorial.png")),
    ModeCard(card_start_x + card_w + card_gap, card_y, card_w, card_h,
             "Seasons", (34, 120, 50), "", icon_image=os.path.join(_assets, "seasons.png")),
    ModeCard(card_start_x + (card_w + card_gap) * 2, card_y, card_w, card_h,
             "Speed Run", (180, 100, 30), "", locked=False, icon_image=os.path.join(_assets, "speedrun.png")),
]
mode_selected_idx = None
current_mode = "seasons"  # "tutorial", "seasons", "speedrun"

# Speed Run state
speedrun_active = False
speedrun_season_order = ["forest", "snow", "desert"]
speedrun_season_idx = 0
speedrun_level = 1
speedrun_chrono = 0.0
speedrun_num_players = 1
speedrun_current_player = 1
speedrun_player_names = ["", ""]
speedrun_player_times = [0.0, 0.0]
speedrun_name_input = ""
speedrun_name_phase = 1
speedrun_choosing_players = True

mode_play_btn = Button(WIDTH // 2, HEIGHT - 80, 200, 50, "PLAY", (30, 140, 60), (50, 200, 80))
mode_back_btn = Button(80, HEIGHT - 40, 140, 45, "BACK", (60, 60, 75), (90, 90, 110))

# ---- Tutorial state ----
# Steps: 0=intro_vo, 1=prompt_left, 2=left_success, 3=prompt_right,
#         4=right_success, 5=free_practice, 6=outro, 7=done
tutorial_step = 0
tutorial_boat_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2 + 80)
tutorial_boat_angle = 0.0
tutorial_boat_vel = pygame.Vector2(0, 0)
tutorial_oar = OarAnimator()
tutorial_wake = WakeSystem()
tutorial_prompt_alpha = 0.0
tutorial_step_timer = 0.0
tutorial_vo_triggered = False
tutorial_back_btn = Button(80, HEIGHT - 40, 140, 45, "BACK", (60, 60, 75), (90, 90, 110))
tutorial_skip_btn = Button(WIDTH - 220, HEIGHT - 60, 160, 42, "SKIP  >>", (60, 75, 60), (80, 110, 80))

# ---- Seasons state ----
seasons_list = [
    SeasonItem("Forest", "Navigate through the woodland river", (34, 80, 34), (40, 100, 50), playable=True),
    SeasonItem("Snow", "Brave the frozen waters", (180, 200, 230), (100, 140, 180), playable=True),
    SeasonItem("Desert", "Cross the oasis canyon", (210, 170, 100), (160, 120, 60), playable=True),
    SeasonItem("Tropics", "Coming Soon", (30, 140, 80), (40, 120, 70), playable=False),
]
seasons_scroll_idx = 0
seasons_prev_idx = 0
seasons_scroll_offset = 0.0
seasons_bg_color = list(seasons_list[0].bg_color)
seasons_play_btn = Button(WIDTH // 2, HEIGHT - 80, 200, 50, "PLAY", (30, 140, 60), (50, 200, 80))
seasons_back_btn = Button(80, HEIGHT - 40, 140, 45, "BACK", (60, 60, 75), (90, 90, 110))

# ---- Current season and theme data ----
current_season = "forest"

# Build SEASON_DATA from maps.py or editor_maps
def build_season_data():
    """Convert maps data into SEASON_DATA format for game logic.
    Checks editor_maps first, falls back to maps.py."""
    season_data = {}
    print("\n📋 Checking for editor maps...")
    for season_name in MAPS.keys():
        season_data[season_name] = {}

        # Level 1 - check editor_maps first
        editor_l1 = get_editor_map(season_name, 1)
        l1_map = editor_l1 or MAPS.get(season_name, {}).get(1)
        if l1_map:
            if "obstacles" in l1_map:
                season_data[season_name]["l1_cubes"] = l1_map.get("obstacles", [])
                n_obs = len(season_data[season_name]["l1_cubes"])
                if editor_l1:
                    print(f"  ✅ EDITOR {season_name.upper()} L1: {n_obs} obstacles")
                else:
                    print(f"  📦 FALLBACK {season_name.upper()} L1: {n_obs} obstacles")
            season_data[season_name]["l1_timer"] = l1_map.get("time_limit", 60)
            # Finish line - check if from editor map with axis info
            finish_data = l1_map.get("finish", l1_map)  # editor maps have "finish" dict
            if isinstance(finish_data, dict) and "axis" in finish_data:
                season_data[season_name]["l1_finish_axis"] = finish_data.get("axis", "y")
                season_data[season_name]["l1_finish_pos"] = finish_data.get("pos", 40)
                season_data[season_name]["l1_finish_y"] = finish_data.get("pos", 40)
                season_data[season_name]["l1_finish_x1"] = finish_data.get("x1", 100)
                season_data[season_name]["l1_finish_x2"] = finish_data.get("x2", 1150)
                season_data[season_name]["l1_finish_y1"] = finish_data.get("y1", 0)
                season_data[season_name]["l1_finish_y2"] = finish_data.get("y2", HEIGHT)
            else:
                season_data[season_name]["l1_finish_axis"] = "y"
                season_data[season_name]["l1_finish_y"] = l1_map.get("finish_y", 40)
                season_data[season_name]["l1_finish_pos"] = l1_map.get("finish_y", 40)
                season_data[season_name]["l1_finish_x1"] = l1_map.get("finish_x1", 100)
                season_data[season_name]["l1_finish_x2"] = l1_map.get("finish_x2", 1150)
            season_data[season_name]["l1_slow_zones"] = l1_map.get("slow_zones", [])

        # Level 2 - check editor_maps first
        editor_l2 = get_editor_map(season_name, 2)
        l2_map = editor_l2 or MAPS.get(season_name, {}).get(2)
        if l2_map:
            season_data[season_name]["l2_cubes"] = l2_map.get("obstacles", [])
            season_data[season_name]["l2_timer"] = l2_map.get("time_limit", 45)
            season_data[season_name]["l2_wall_width"] = l2_map.get("l2_wall_width", 100)
            season_data[season_name]["l2_slow_zones"] = l2_map.get("slow_zones", [])
            # L2 finish data
            l2_finish = l2_map.get("finish", l2_map)
            if isinstance(l2_finish, dict) and "axis" in l2_finish:
                season_data[season_name]["l2_finish_axis"] = l2_finish.get("axis", "y")
                season_data[season_name]["l2_finish_pos"] = l2_finish.get("pos", 40)
                season_data[season_name]["l2_finish_y"] = l2_finish.get("pos", 40)
                season_data[season_name]["l2_finish_x1"] = l2_finish.get("x1", 150)
                season_data[season_name]["l2_finish_x2"] = l2_finish.get("x2", WIDTH - 150)
                season_data[season_name]["l2_finish_y1"] = l2_finish.get("y1", 0)
                season_data[season_name]["l2_finish_y2"] = l2_finish.get("y2", HEIGHT)
            else:
                season_data[season_name]["l2_finish_axis"] = "y"
                season_data[season_name]["l2_finish_y"] = 40
                season_data[season_name]["l2_finish_pos"] = 40
                season_data[season_name]["l2_finish_x1"] = 150
                season_data[season_name]["l2_finish_x2"] = WIDTH - 150
            n_obs = len(season_data[season_name].get("l2_cubes", []))
            if editor_l2:
                print(f"  ✅ EDITOR {season_name.upper()} L2: {n_obs} obstacles")
            else:
                print(f"  📦 FALLBACK {season_name.upper()} L2: {n_obs} obstacles")

        # Level 3 - check editor_maps first
        editor_l3 = get_editor_map(season_name, 3)
        l3_map = editor_l3 or MAPS.get(season_name, {}).get(3)
        if l3_map:
            season_data[season_name]["l3_cubes"] = l3_map.get("obstacles", [])
            season_data[season_name]["l3_timer"] = l3_map.get("time_limit", 40)
            season_data[season_name]["l3_slow_zones"] = l3_map.get("slow_zones", [])
            season_data[season_name]["l3_poly_obstacles"] = l3_map.get("poly_obstacles", [])
            finish_data = l3_map.get("finish", l3_map)
            if isinstance(finish_data, dict) and "axis" in finish_data:
                season_data[season_name]["l3_finish_axis"] = finish_data.get("axis", "y")
                season_data[season_name]["l3_finish_pos"] = finish_data.get("pos", 40)
                season_data[season_name]["l3_finish_y"] = finish_data.get("pos", 40)
                season_data[season_name]["l3_finish_x1"] = finish_data.get("x1", 100)
                season_data[season_name]["l3_finish_x2"] = finish_data.get("x2", 1150)
                season_data[season_name]["l3_finish_y1"] = finish_data.get("y1", 0)
                season_data[season_name]["l3_finish_y2"] = finish_data.get("y2", HEIGHT)
            else:
                season_data[season_name]["l3_finish_axis"] = "y"
                season_data[season_name]["l3_finish_y"] = l3_map.get("finish_y", 40)
                season_data[season_name]["l3_finish_pos"] = l3_map.get("finish_y", 40)
                season_data[season_name]["l3_finish_x1"] = l3_map.get("finish_x1", 100)
                season_data[season_name]["l3_finish_x2"] = l3_map.get("finish_x2", 1150)
            n_obs = len(season_data[season_name].get("l3_cubes", []))
            if editor_l3:
                print(f"  ✅ EDITOR {season_name.upper()} L3: {n_obs} obstacles")
            else:
                print(f"  📦 FALLBACK {season_name.upper()} L3: {n_obs} obstacles")

    return season_data

print("\n" + "="*60)
print("Building SEASON_DATA...")
SEASON_DATA = build_season_data()
print("="*60)
for season in SEASON_DATA:
    l1_obs = len(SEASON_DATA[season].get('l1_cubes', []))
    l3_obs = len(SEASON_DATA[season].get('l3_cubes', []))
    print(f"{season.upper()}: L1={l1_obs} obs, L3={l3_obs} obs")
print("="*60 + "\n")

# Theme-specific water color palettes
WATER_PALETTES = {
    "forest": None,  # Use existing deep ocean blues
    "snow": {"deep": (190, 215, 240), "wave1": (200, 225, 248), "wave2": (210, 232, 252), "wave3": (220, 238, 255), "wave4": (230, 243, 255)},
    "desert": {"deep": (80, 160, 180), "wave1": (90, 175, 195), "wave2": (100, 185, 205), "wave3": (110, 195, 215), "wave4": (120, 205, 225)},
    "tropics": {"deep": (20, 80, 130), "wave1": (30, 100, 150), "wave2": (40, 115, 165), "wave3": (50, 130, 180), "wave4": (60, 145, 195)},
}

# ---- Dialog box ----
dialog = DialogBox(subtitle_font)
intro_vo_played = False

# Fade transition
fade = FadeTransition()

# Visual systems
water = WaterRenderer(WIDTH, HEIGHT)
oar_anim = OarAnimator()
wake = WakeSystem()

# Timer
timer_seconds = 60

# Level 1 finish line positions (vary by theme, set in reset_game)
l1_finish_x1 = 200
l1_finish_x2 = 330

# Boat state
INITIAL_BOAT_POS = pygame.Vector2(WIDTH // 2, 600)
boat_pos = INITIAL_BOAT_POS.copy()
boat_velocity = pygame.Vector2(0, 0)
boat_angle = 0

# Input tracking
left_pressed = False
right_pressed = False
input_buffer = 0
input_decay_time = 0.25

# Physics constants
MAX_SPEED = 10
ROTATION_SPEED = 450
ROTATION_STEP = 25
BASE_ACCEL = 0.6
ACCEL_PER_PRESS = 0.35
BASE_FRICTION = 0.99
SIDEWAYS_FRICTION = 0.985
SIDEWAYS_DRIFT_MULT = 0.75
SINGLE_KEY_ACCEL_MULT = 0.8
SINGLE_KEY_SIDEWAYS_MULT = 0.55

# Rotation state
rotating = False
rotation_start_angle = boat_angle
rotation_direction = 0
target_angle = boat_angle
down_pressed = False

# Obstacle cubes (x, y, width, height)
left_cube_width = 200
right_cube_width = 200
cubes = [
    (0, 0, left_cube_width, HEIGHT),
    (WIDTH - right_cube_width, 0, right_cube_width, HEIGHT),
    (200, 450, 380, 200),
    (200, 330, 750, 150),
    (670, 570, 500, 300),
    (330, 0, 720, 230),
]

boat_collision_radius = 15

# Pre-render forest surface once at startup
print("Pre-rendering Level 1 forest...")
forest_surface = create_forest_surface(
    cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2
)
print("Level 1 forest ready.")

# Pre-compute shoreline foam points
foam_points = precompute_foam(cubes, WIDTH, HEIGHT)

# Level 1 extra systems
l1_crash = CrashAnimation()
l1_shake = ScreenShake()
l1_frame = pygame.Surface((WIDTH, HEIGHT))
l1_complete_timer = 0


# ================================================================
# LEVEL 2 SETUP (single-screen, rocks, wind, 45s timer)
# ================================================================
LEVEL2_FINISH_Y = 40
l2_finish_axis = "y"
l2_finish_pos = 40
l2_finish_y = 40
l2_finish_x1 = 150
l2_finish_x2 = WIDTH - 150
l2_finish_y1 = 0
l2_finish_y2 = HEIGHT
LEVEL2_INITIAL_POS = pygame.Vector2(WIDTH // 2, 600)

# Level 2 walls are narrower (150px vs L1's 200px) for wider river
# Rock obstacles scattered in the river
level2_cubes = [
    (0, 0, 150, HEIGHT),                   # Left forest wall
    (WIDTH - 150, 0, 150, HEIGHT),          # Right forest wall
    # Rocks in the river
    (150, 500, 220, 80),                    # Bottom-left rock
    (680, 520, 260, 100),                   # Bottom-right rock
    (320, 340, 200, 75),                    # Mid-left rock
    (580, 220, 240, 70),                    # Mid-right rock
    (820, 350, 180, 85),                    # Far-right rock
    (250, 130, 180, 65),                    # Upper-left rock
    (500, 0, 350, 80),                      # Top barrier (gap left: 150-500, gap right: 850-1100)
]

# Level 2 rock obstacles (only the non-wall cubes)
level2_rock_cubes = [c for c in level2_cubes if c[2] != 150 or c[3] != HEIGHT]

# Pre-render Level 2 forest (walls only) and rocks (obstacles only)
print("Pre-rendering Level 2...")
level2_wall_cubes = [(0, 0, 150, HEIGHT), (WIDTH - 150, 0, 150, HEIGHT)]
l2_forest = create_forest_surface(
    level2_wall_cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2
)
l2_rock_surface = create_rock_surface(level2_rock_cubes, WIDTH, HEIGHT)
print("Level 2 ready.")

l2_foam_points = precompute_foam(level2_cubes, WIDTH, HEIGHT)

# Level 2 state
l2_boat_pos = LEVEL2_INITIAL_POS.copy()
l2_boat_vel = pygame.Vector2(0, 0)
l2_boat_angle = 0
l2_timer = 45
l2_rotating = False
l2_rotation_start_angle = 0
l2_rotation_direction = 0
l2_target_angle = 0
l2_input_buffer = 0
l2_left_pressed = False
l2_right_pressed = False
l2_down_pressed = False

# Level 2 systems
l2_oar = OarAnimator()
l2_wake = WakeSystem()
l2_particles = ParticleSystem()
l2_shake = ScreenShake()
l2_wind = WindSystem()
l2_crash = CrashAnimation()
l2_frame = pygame.Surface((WIDTH, HEIGHT))
l2_wall_width = 150  # Default, set in reset_level2

# Win screen
l2_win_blink_timer = 0
l2_complete_timer = 0

# Level 3 state
l3_boat_pos = pygame.Vector2(WIDTH // 2, 600)
l3_boat_vel = pygame.Vector2(0, 0)
l3_boat_angle = 0
l3_rotating = False
l3_rotation_start_angle = 0
l3_rotation_direction = 0
l3_target_angle = 0
l3_input_buffer = 0
l3_left_pressed = False
l3_right_pressed = False
l3_down_pressed = False
l3_timer = 40
l3_oar = OarAnimator()
l3_wake = WakeSystem()
l3_shake = ScreenShake()
l3_crash = CrashAnimation()
l3_frame = pygame.Surface((WIDTH, HEIGHT))
l3_cubes = []
l3_poly_obstacles = []
l3_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
l3_canopy = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
l3_foam_points = []
l3_slow_zones = []
l3_finish_axis = "y"
l3_finish_pos = 40
l3_finish_y = 40
l3_finish_x1 = 100
l3_finish_x2 = 1150
l3_finish_y1 = 0
l3_finish_y2 = HEIGHT
l3_win_blink_timer = 0
l3_spawn_pos = pygame.Vector2(WIDTH // 2, 600)


def reset_level2():
    global l2_boat_pos, l2_boat_vel, l2_boat_angle, l2_timer
    global l2_rotating, l2_rotation_start_angle, l2_rotation_direction, l2_target_angle
    global l2_input_buffer, l2_left_pressed, l2_right_pressed, l2_down_pressed
    global l2_oar, l2_wake, l2_particles, l2_shake, l2_wind, l2_crash
    global level2_cubes, level2_wall_cubes, level2_rock_cubes, l2_forest, l2_rock_surface, l2_foam_points, l2_wall_width
    global l2_finish_axis, l2_finish_pos, l2_finish_y, l2_finish_x1, l2_finish_x2, l2_finish_y1, l2_finish_y2

    # Load theme-specific Level 2 data
    theme = SEASON_DATA[current_season]
    level2_cubes = theme["l2_cubes"]
    l2_finish_axis = theme.get("l2_finish_axis", "y")
    l2_finish_pos = theme.get("l2_finish_pos", 40)
    l2_finish_y = theme.get("l2_finish_y", 40)
    l2_finish_x1 = theme.get("l2_finish_x1", 150)
    l2_finish_x2 = theme.get("l2_finish_x2", WIDTH - 150)
    l2_finish_y1 = theme.get("l2_finish_y1", 0)
    l2_finish_y2 = theme.get("l2_finish_y2", HEIGHT)
    l2_timer = theme["l2_timer"]
    l2_wall_width = theme["l2_wall_width"]

    # Split cubes into walls and obstacles
    level2_wall_cubes = [(0, 0, l2_wall_width, HEIGHT), (WIDTH - l2_wall_width, 0, l2_wall_width, HEIGHT)]
    level2_rock_cubes = [c for c in level2_cubes if c not in level2_wall_cubes]

    # Generate theme-specific surfaces
    if current_season == "forest":
        l2_forest = create_forest_surface(level2_wall_cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2)
        l2_rock_surface = create_rock_surface(level2_rock_cubes, WIDTH, HEIGHT)
    elif current_season == "snow":
        l2_forest = create_snow_surface(level2_wall_cubes, WIDTH, HEIGHT)
        l2_rock_surface = create_snow_surface(level2_rock_cubes, WIDTH, HEIGHT)
    elif current_season == "desert":
        l2_forest = create_desert_surface(level2_wall_cubes, WIDTH, HEIGHT)
        l2_rock_surface = create_desert_surface(level2_rock_cubes, WIDTH, HEIGHT)
    elif current_season == "tropics":
        l2_forest = create_tropics_surface(level2_wall_cubes, WIDTH, HEIGHT)
        l2_rock_surface = create_tropics_surface(level2_rock_cubes, WIDTH, HEIGHT)

    # Precompute foam points for all cubes
    l2_foam_points = precompute_foam(level2_cubes, WIDTH, HEIGHT)

    # Render assets on Level 2 surfaces - load EXACT assets from map JSON
    map_data = load_map(current_season, 2)
    if map_data and "assets" in map_data:
        for asset_info in map_data["assets"]:
            # Load the exact asset file referenced in the JSON
            asset_src = asset_info.get("src", "")
            if asset_src:
                asset_path = Path(asset_src)
                if asset_path.exists():
                    try:
                        asset_img = pygame.image.load(asset_path)
                        # Use exact dimensions from JSON if provided
                        json_w = asset_info.get("w")
                        json_h = asset_info.get("h")

                        if json_w and json_h:
                            scaled_asset = pygame.transform.scale(asset_img, (int(json_w), int(json_h)))
                        else:
                            scaled_asset = asset_img

                        x = int(asset_info.get("x", 0))
                        y = int(asset_info.get("y", 0))
                        w = int(json_w or scaled_asset.get_width())
                        h = int(json_h or scaled_asset.get_height())

                        # Apply rotation around center to match editor
                        rotation = asset_info.get("rotation", 0)
                        if rotation != 0:
                            cx, cy = x + w // 2, y + h // 2
                            scaled_asset = pygame.transform.rotate(scaled_asset, rotation)
                            new_rect = scaled_asset.get_rect(center=(cx, cy))
                            blit_x, blit_y = new_rect.topleft
                        else:
                            blit_x, blit_y = x, y

                        # Blit to both wall and obstacle surfaces for visual distribution
                        l2_forest.blit(scaled_asset, (blit_x, blit_y))
                        l2_rock_surface.blit(scaled_asset, (blit_x, blit_y))
                    except Exception as e:
                        print(f"  ⚠️ Could not load L2 asset {asset_src}: {e}")

    # Reset physics state - use calculate_spawn_pos for correct axis handling
    l2_boat_pos = calculate_spawn_pos(map_data)
    spawn_angle = get_spawn_angle(map_data)

    l2_boat_vel = pygame.Vector2(0, 0)
    l2_boat_angle = spawn_angle
    l2_rotating = False
    l2_rotation_start_angle = spawn_angle
    l2_rotation_direction = 0
    l2_target_angle = spawn_angle
    l2_input_buffer = 0
    l2_left_pressed = False
    l2_right_pressed = False
    l2_down_pressed = False
    l2_oar = OarAnimator()
    l2_wake = WakeSystem()
    l2_particles = ParticleSystem()
    l2_shake = ScreenShake()
    l2_wind = WindSystem()
    l2_crash = CrashAnimation()


# ================================================================
def reset_level3():
    global l3_boat_pos, l3_boat_vel, l3_boat_angle, l3_timer
    global l3_rotating, l3_rotation_start_angle, l3_rotation_direction, l3_target_angle
    global l3_input_buffer, l3_left_pressed, l3_right_pressed, l3_down_pressed
    global l3_oar, l3_wake, l3_shake, l3_crash
    global l3_cubes, l3_poly_obstacles, l3_surface, l3_canopy, l3_foam_points, l3_slow_zones, l3_spawn_pos
    global l3_finish_axis, l3_finish_pos, l3_finish_y, l3_finish_x1, l3_finish_x2, l3_finish_y1, l3_finish_y2

    theme = SEASON_DATA[current_season]
    l3_cubes = theme.get("l3_cubes", [])
    l3_poly_obstacles = theme.get("l3_poly_obstacles", [])
    l3_timer = theme.get("l3_timer", 40)
    l3_slow_zones = theme.get("l3_slow_zones", [])

    l3_finish_axis = theme.get("l3_finish_axis", "y")
    l3_finish_pos = theme.get("l3_finish_pos", 40)
    l3_finish_y = theme.get("l3_finish_y", 40)
    l3_finish_x1 = theme.get("l3_finish_x1", 100)
    l3_finish_x2 = theme.get("l3_finish_x2", 1150)
    l3_finish_y1 = theme.get("l3_finish_y1", 0)
    l3_finish_y2 = theme.get("l3_finish_y2", HEIGHT)

    # Generate surface
    if current_season == "forest":
        l3_surface = create_forest_surface(l3_cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2)
    elif current_season == "snow":
        l3_surface = create_snow_surface(l3_cubes, WIDTH, HEIGHT)
    elif current_season == "desert":
        l3_surface = create_desert_surface(l3_cubes, WIDTH, HEIGHT)
    elif current_season == "tropics":
        l3_surface = create_tropics_surface(l3_cubes, WIDTH, HEIGHT)

    l3_foam_points = precompute_foam(l3_cubes, WIDTH, HEIGHT)

    # Render assets
    map_data = load_map(current_season, 3)
    l3_canopy = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    TREE_NAMES = {'forest1', 'forest2', 'forest', 'tree', 'canopy', 'forest1-removebg-preview', 'forest2-removebg-preview'}

    if map_data and "assets" in map_data:
        for asset_info in map_data["assets"]:
            asset_src = asset_info.get("src", "")
            if asset_src:
                asset_path = Path(asset_src)
                if asset_path.exists():
                    try:
                        asset_img = pygame.image.load(asset_path).convert_alpha()
                        json_w = asset_info.get("w")
                        json_h = asset_info.get("h")
                        if json_w and json_h:
                            scaled_asset = pygame.transform.scale(asset_img, (int(json_w), int(json_h)))
                        else:
                            scaled_asset = asset_img
                        x = int(asset_info.get("x", 0))
                        y = int(asset_info.get("y", 0))
                        w = int(json_w or scaled_asset.get_width())
                        h = int(json_h or scaled_asset.get_height())
                        rotation = asset_info.get("rotation", 0)
                        if rotation != 0:
                            cx, cy = x + w // 2, y + h // 2
                            scaled_asset = pygame.transform.rotate(scaled_asset, rotation)
                            new_rect = scaled_asset.get_rect(center=(cx, cy))
                            blit_x, blit_y = new_rect.topleft
                        else:
                            blit_x, blit_y = x, y
                        asset_name = asset_info.get("name", "")
                        if asset_name in TREE_NAMES or "forest" in asset_name.lower() or "tree" in asset_name.lower() or "canopy" in asset_name.lower():
                            l3_canopy.blit(scaled_asset, (blit_x, blit_y))
                        else:
                            l3_surface.blit(scaled_asset, (blit_x, blit_y))
                    except Exception as e:
                        print(f"  ⚠️ Could not load L3 asset {asset_src}: {e}")

    # Spawn position
    l3_boat_pos = calculate_spawn_pos(map_data)
    l3_spawn_pos = pygame.Vector2(l3_boat_pos.x, l3_boat_pos.y)  # save for win direction check
    spawn_angle = get_spawn_angle(map_data)

    l3_boat_vel = pygame.Vector2(0, 0)
    l3_boat_angle = spawn_angle
    l3_rotating = False
    l3_rotation_start_angle = 0
    l3_rotation_direction = 0
    l3_target_angle = spawn_angle
    l3_input_buffer = 0
    l3_left_pressed = False
    l3_right_pressed = False
    l3_down_pressed = False
    l3_oar = OarAnimator()
    l3_wake = WakeSystem()
    l3_shake = ScreenShake()
    l3_crash = CrashAnimation()


# MAIN GAME LOOP
# ================================================================
running = True
last_input_time = pygame.time.get_ticks() / 1000.0
input_this_frame = False
game_time = 0



def reset_game():
    """Reset all game state for a fresh start (Level 1)."""
    global boat_pos, boat_velocity, boat_angle, rotating, input_buffer
    global rotation_direction, target_angle, rotation_start_angle
    global left_pressed, right_pressed, down_pressed, timer_seconds
    global l1_crash, l1_shake
    global cubes, forest_surface, canopy_surface, l1_finish_axis, l1_finish_pos, l1_finish_y, l1_finish_x1, l1_finish_x2, l1_finish_y1, l1_finish_y2, l1_slow_zones, l1_spawn_pos

    # Load theme-specific data
    theme = SEASON_DATA[current_season]
    cubes = theme["l1_cubes"]
    print(f"\n🎮 LOADED: {current_season.upper()} L1 with {len(cubes)} obstacles")
    timer_seconds = theme["l1_timer"]
    l1_finish_axis = theme.get("l1_finish_axis", "y")
    l1_finish_pos = theme.get("l1_finish_pos", 40)
    l1_finish_y = theme.get("l1_finish_y", 40)
    l1_finish_x1 = theme.get("l1_finish_x1", 100)
    l1_finish_x2 = theme.get("l1_finish_x2", 1150)
    l1_finish_y1 = theme.get("l1_finish_y1", 0)
    l1_finish_y2 = theme.get("l1_finish_y2", HEIGHT)
    l1_slow_zones = theme.get("l1_slow_zones", [])

    # Generate theme-specific surface
    if current_season == "forest":
        forest_surface = create_forest_surface(cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2)
    elif current_season == "snow":
        forest_surface = create_snow_surface(cubes, WIDTH, HEIGHT)
    elif current_season == "desert":
        forest_surface = create_desert_surface(cubes, WIDTH, HEIGHT)
    elif current_season == "tropics":
        forest_surface = create_tropics_surface(cubes, WIDTH, HEIGHT)

    # Render assets on the surface - load EXACT assets from map JSON
    # Tree/canopy assets go on a separate surface rendered ABOVE the boat
    map_data = load_map(current_season, 1)
    canopy_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    TREE_NAMES = {'forest1', 'forest2', 'forest', 'tree', 'canopy', 'forest1-removebg-preview', 'forest2-removebg-preview'}

    if map_data and "assets" in map_data:
        for asset_info in map_data["assets"]:
            asset_src = asset_info.get("src", "")
            if asset_src:
                asset_path = Path(asset_src)
                if asset_path.exists():
                    try:
                        asset_img = pygame.image.load(asset_path).convert_alpha()
                        json_w = asset_info.get("w")
                        json_h = asset_info.get("h")

                        if json_w and json_h:
                            scaled_asset = pygame.transform.scale(asset_img, (int(json_w), int(json_h)))
                        else:
                            scaled_asset = asset_img

                        x = int(asset_info.get("x", 0))
                        y = int(asset_info.get("y", 0))
                        w = int(json_w or scaled_asset.get_width())
                        h = int(json_h or scaled_asset.get_height())

                        rotation = asset_info.get("rotation", 0)
                        if rotation != 0:
                            # Rotate around center to match editor behavior
                            cx, cy = x + w // 2, y + h // 2
                            scaled_asset = pygame.transform.rotate(scaled_asset, rotation)
                            new_rect = scaled_asset.get_rect(center=(cx, cy))
                            blit_x, blit_y = new_rect.topleft
                        else:
                            blit_x, blit_y = x, y

                        # Tree assets go on canopy (above boat), others on ground
                        asset_name = asset_info.get("name", "")
                        if asset_name in TREE_NAMES or "forest" in asset_name.lower() or "tree" in asset_name.lower() or "canopy" in asset_name.lower():
                            canopy_surface.blit(scaled_asset, (blit_x, blit_y))
                        else:
                            forest_surface.blit(scaled_asset, (blit_x, blit_y))
                    except Exception as e:
                        print(f"  ⚠️ Could not load asset {asset_src}: {e}")

    # Reset physics state - use calculate_spawn_pos for correct axis handling
    boat_pos = calculate_spawn_pos(map_data)
    l1_spawn_pos = pygame.Vector2(boat_pos.x, boat_pos.y)

    spawn_angle = get_spawn_angle(map_data)

    boat_velocity = pygame.Vector2(0, 0)
    boat_angle = spawn_angle
    rotating = False
    rotation_direction = 0
    target_angle = spawn_angle
    rotation_start_angle = 0
    input_buffer = 0
    left_pressed = False
    right_pressed = False
    down_pressed = False
    wake.clear()
    l1_crash = CrashAnimation()
    l1_shake = ScreenShake()


# ================================================================
# SHARED GAMEPLAY HELPERS
# ================================================================

def _smooth_rotation(angle, target_angle, rotating, rotation_direction, dt):
    """Advance angle toward target at ROTATION_SPEED deg/s."""
    if rotating:
        diff = (target_angle - angle + 180) % 360 - 180
        step = math.copysign(min(abs(diff), ROTATION_SPEED * dt), diff)
        angle += step
        if abs((target_angle - angle + 180) % 360 - 180) < 0.01:
            angle = target_angle % 360
            rotating = False
            rotation_direction = 0
    return angle % 360, rotating, rotation_direction


def _apply_boat_physics(vel, angle, input_buffer, left_pressed, right_pressed, dt, season=None):
    """Acceleration + speed clamp + friction. Returns new vel."""
    forward = pygame.Vector2(0, -1).rotate(angle)
    if input_buffer > 0.01:
        accel = BASE_ACCEL + ACCEL_PER_PRESS * input_buffer
        if left_pressed != right_pressed:
            accel *= SINGLE_KEY_ACCEL_MULT
        vel = vel + forward * accel * dt
    speed = vel.length()
    if speed > MAX_SPEED:
        vel = (vel / speed) * MAX_SPEED
    if speed > 0.01:
        alignment = vel.normalize().dot(forward)
        sideways_effect = SIDEWAYS_DRIFT_MULT
        if left_pressed != right_pressed:
            sideways_effect *= SINGLE_KEY_SIDEWAYS_MULT
        if season == "snow":
            friction = 0.997
        else:
            friction = (
                BASE_FRICTION
                + (1 - abs(alignment))
                * (SIDEWAYS_FRICTION - BASE_FRICTION)
                * sideways_effect
            )
        vel = vel * friction
    else:
        vel = pygame.Vector2(0, 0)
    return vel


def _aabb_circle(px, py, r, cubes):
    """True if circle (px,py,r) intersects any AABB in cubes."""
    for cx, cy, cw, ch in cubes:
        if px - r < cx + cw and px + r > cx and py - r < cy + ch and py + r > cy:
            return True
    return False


def _poly_circle_hit(px, py, r, poly_obstacles):
    """True if circle intersects any polygon obstacle."""
    for poly in poly_obstacles:
        pts = [(p["x"], p["y"]) for p in poly.get("points", [])]
        if len(pts) >= 2 and circle_vs_polygon(px, py, r, pts):
            return True
    return False


def _do_l1_respawn():
    global boat_pos, boat_velocity, boat_angle, rotating, timer_seconds, target_angle
    l1_map = load_map(current_season, 1)
    boat_pos = calculate_spawn_pos(l1_map)
    ra = get_spawn_angle(l1_map)
    boat_velocity = pygame.Vector2(0, 0)
    boat_angle = ra
    target_angle = ra
    rotating = False
    timer_seconds = SEASON_DATA[current_season].get("l1_timer", 60)
    wake.clear()


def _do_l2_respawn():
    global l2_boat_pos, l2_boat_vel, l2_boat_angle, l2_rotating, l2_timer, l2_target_angle
    l2_map = load_map(current_season, 2)
    l2_boat_pos = calculate_spawn_pos(l2_map)
    ra = get_spawn_angle(l2_map)
    l2_boat_vel = pygame.Vector2(0, 0)
    l2_boat_angle = ra
    l2_target_angle = ra
    l2_rotating = False
    l2_timer = SEASON_DATA[current_season].get("l2_timer", 45)
    l2_wake.clear()


def _do_l3_respawn():
    global l3_boat_pos, l3_boat_vel, l3_boat_angle, l3_rotating, l3_timer, l3_target_angle
    l3_map = load_map(current_season, 3)
    l3_boat_pos = calculate_spawn_pos(l3_map)
    ra = get_spawn_angle(l3_map)
    l3_boat_vel = pygame.Vector2(0, 0)
    l3_boat_angle = ra
    l3_target_angle = ra
    l3_rotating = False
    l3_timer = SEASON_DATA[current_season].get("l3_timer", 40)
    l3_wake.clear()


def _check_win(pos, spawn_pos, axis, finish_pos, finish_y, finish_x1, finish_x2, finish_y1, finish_y2):
    """Spawn-relative finish-line check for x-axis and y-axis rivers."""
    if axis == "x":
        in_gap = finish_y1 <= pos.y <= finish_y2
        return (pos.x > finish_pos if finish_pos > spawn_pos.x else pos.x < finish_pos) and in_gap
    else:
        return pos.y < finish_y if finish_y < spawn_pos.y else pos.y > finish_y


def _draw_finish_glow(frame, axis, finish_pos, finish_x1, finish_x2, finish_y, finish_y1, finish_y2, game_time):
    """Pulsing green finish-line indicator."""
    glow_pulse = 0.5 + 0.5 * math.sin(game_time * 3)
    glow_alpha = int(60 + 80 * glow_pulse)
    if axis == "x":
        h = max(1, finish_y2 - finish_y1)
        surf = pygame.Surface((12, h), pygame.SRCALPHA)
        surf.fill((80, 255, 120, glow_alpha))
        frame.blit(surf, (finish_pos - 6, finish_y1))
        pygame.draw.line(frame, (80, 255, 120), (finish_pos, finish_y1), (finish_pos, finish_y2), 2)
    else:
        w = max(1, finish_x2 - finish_x1)
        surf = pygame.Surface((w, 12), pygame.SRCALPHA)
        surf.fill((80, 255, 120, glow_alpha))
        frame.blit(surf, (finish_x1, finish_y - 6))
        pygame.draw.line(frame, (80, 255, 120), (finish_x1, finish_y), (finish_x2, finish_y), 2)


def _draw_speedrun_hud(frame, chrono, season_idx, level):
    """Speedrun chrono + level label at top-left."""
    sr_mins = int(chrono // 60)
    sr_secs = chrono % 60
    chrono_str = f"{sr_mins}:{sr_secs:04.1f}"
    chrono_surf = font.render(chrono_str, True, (255, 220, 80))
    chrono_shadow = font.render(chrono_str, True, (0, 0, 0))
    frame.blit(chrono_shadow, (22, 22))
    frame.blit(chrono_surf, (20, 20))
    sr_label = f"{speedrun_season_order[season_idx].title()} L{level}"
    label_surf = subtitle_font.render(sr_label, True, (200, 210, 230))
    frame.blit(label_surf, (20, 60))


def _draw_timer_hud(frame, timer_val):
    """Countdown timer at top-center; hidden in seasons/speedrun; jitters at <=10s."""
    if current_mode in ("seasons", "speedrun"):
        return
    color = (255, 0, 0) if timer_val <= 10 else (255, 255, 255)
    txt = font.render(f"{timer_val:.1f}", True, color)
    shd = font.render(f"{timer_val:.1f}", True, (0, 0, 0))
    r = txt.get_rect(midtop=(WIDTH // 2, 20))
    sr = r.copy()
    sr.x += 2
    sr.y += 2
    if timer_val <= 10:
        sx, sy = random.randint(-2, 2), random.randint(-2, 2)
        r.x += sx; r.y += sy
        sr.x += sx; sr.y += sy
    frame.blit(shd, sr)
    frame.blit(txt, r)


def _advance_speedrun():
    """Move to next season in speedrun, or complete the run."""
    global game_state, speedrun_season_idx, speedrun_level, current_season
    speedrun_season_idx += 1
    if speedrun_season_idx >= len(speedrun_season_order):
        speedrun_player_times[0] = speedrun_chrono
        game_state = "speedrun_complete"
    else:
        speedrun_level = 1
        current_season = speedrun_season_order[speedrun_season_idx]
        game_state = "playing"
        reset_game()


def _draw_desert_storm(frame, boat_pos, shake, game_time, level):
    """Desert sandstorm. level=2 moderate, level=3 heavy."""
    if level == 2:
        gust_freq = 0.6
        tint_alpha = 50
        curtain_base, curtain_swing = 60, 80
        n_streaks, spx, spy, slen = 100, 200, 60, 60
        vis_base, vis_shrink, vis_fade, fog_base = 140, 30, 60, 100
        vig_y, vig_x, vig_base_a, vig_swing = 80, 60, 80, 30
        vib_base, vib_scale = 0.5, 1.5
    else:
        gust_freq = 0.5
        tint_alpha = 60
        curtain_base, curtain_swing = 80, 90
        n_streaks, spx, spy, slen = 130, 220, 70, 70
        vis_base, vis_shrink, vis_fade, fog_base = 120, 35, 70, 120
        vig_y, vig_x, vig_base_a, vig_swing = 100, 80, 100, 40
        vib_base, vib_scale = 0.7, 2.0

    gust_cycle = math.sin(game_time * gust_freq) * 0.5 + 0.5

    tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    tint.fill((160, 120, 60, tint_alpha))
    frame.blit(tint, (0, 0))

    curtain = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    curtain.fill((190, 155, 90, int(curtain_base + curtain_swing * gust_cycle)))
    frame.blit(curtain, (0, 0))

    wind_dx = math.sin(game_time * 1.0) * 0.5 + 0.7
    wind_dy = math.cos(game_time * 0.8) * 0.3
    seed_off = 999 if level == 3 else 0
    for i in range(n_streaks):
        rng = random.Random(int(game_time * 8) + i + seed_off)
        sx = (rng.randint(-100, WIDTH) + int(game_time * spx * wind_dx)) % (WIDTH + 100) - 50
        sy = (rng.randint(-50, HEIGHT) + int(game_time * spy * wind_dy)) % (HEIGHT + 50) - 25
        length = rng.randint(25 if level == 3 else 20, slen)
        color = (210 + rng.randint(-20, 20), 175 + rng.randint(-20, 20), 110 + rng.randint(-15, 15))
        pygame.draw.line(frame, color,
            (int(sx), int(sy)),
            (int(sx + length * wind_dx), int(sy + length * wind_dy * 0.5)),
            rng.randint(1, 2 if level == 2 else 3))

    bx, by = int(boat_pos.x), int(boat_pos.y)
    vis_r = int(vis_base - vis_shrink * gust_cycle)
    vis_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    vis_surf.fill((170, 140, 80, int(fog_base + 40 * gust_cycle)))
    if level == 2:
        for r in range(vis_r, 0, -4):
            pygame.draw.circle(vis_surf, (0, 0, 0, 0), (bx, by), r)
    for r in range(vis_r, vis_r + vis_fade, 2):
        a = min(255, int((r - vis_r) / vis_fade * (180 if level == 2 else 200)))
        pygame.draw.circle(vis_surf, (170, 140, 80, a), (bx, by), r, 2)
    pygame.draw.circle(vis_surf, (0, 0, 0, 0), (bx, by), vis_r)
    frame.blit(vis_surf, (0, 0))

    vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    vig_alpha = int(vig_base_a + vig_swing * gust_cycle)
    for yb in range(vig_y):
        a = int(vig_alpha * (1 - yb / vig_y))
        pygame.draw.line(vig, (80, 60, 30, a), (0, yb), (WIDTH, yb))
        pygame.draw.line(vig, (80, 60, 30, a), (0, HEIGHT - yb), (WIDTH, HEIGHT - yb))
    for xb in range(vig_x):
        a = int(vig_alpha * 0.7 * (1 - xb / vig_x))
        pygame.draw.line(vig, (80, 60, 30, a), (xb, 0), (xb, HEIGHT))
        pygame.draw.line(vig, (80, 60, 30, a), (WIDTH - xb, 0), (WIDTH - xb, HEIGHT))
    frame.blit(vig, (0, 0))

    vib = vib_base + gust_cycle * vib_scale
    shake.offset_x += math.sin(game_time * 18) * vib
    shake.offset_y += math.cos(game_time * 14) * vib * 0.6


def _draw_snow_storm(frame, boat_pos, shake, game_time):
    """Blizzard storm effect for snow L2."""
    gust_cycle = math.sin(game_time * 0.4) * 0.5 + 0.5
    cold_tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cold_tint.fill((40, 50, 80, 45))
    frame.blit(cold_tint, (0, 0))
    whiteout = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    whiteout.fill((220, 230, 245, int(30 + 70 * gust_cycle)))
    frame.blit(whiteout, (0, 0))
    wind_dx = math.sin(game_time * 1.5) * 0.4 + math.sin(game_time * 0.7) * 0.3
    for i in range(200):
        rng = random.Random(int(game_time * 6) + i)
        sm = 0.5 + (i % 4) * 0.4
        sx = (rng.randint(-50, WIDTH + 50) + int(game_time * 80 * wind_dx * sm)) % (WIDTH + 100) - 50
        sy = (rng.randint(-50, HEIGHT + 50) + int(game_time * (60 + i % 5 * 30) * sm)) % (HEIGHT + 100) - 50
        pygame.draw.circle(frame, (240, 245, 255, rng.randint(120, 240)), (int(sx), int(sy)), rng.randint(1, 4))
    for i in range(80):
        rng = random.Random(int(game_time * 5) + i + 300)
        sx = (rng.randint(-100, WIDTH) + int(game_time * 150 * (wind_dx + 0.5))) % (WIDTH + 100) - 50
        sy = (rng.randint(-50, HEIGHT) + int(game_time * 100)) % (HEIGHT + 50) - 25
        length = rng.randint(15, 45)
        pygame.draw.line(frame, (220, 230, 250, rng.randint(40, 120)),
            (int(sx), int(sy)), (int(sx + length * (wind_dx + 0.3)), int(sy + length * 0.8)), 1)
    bx, by = int(boat_pos.x), int(boat_pos.y)
    vis_r = int(150 - 40 * gust_cycle)
    fog_a = int(90 + 50 * gust_cycle)
    vis_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    vis_surf.fill((210, 220, 240, fog_a))
    pygame.draw.circle(vis_surf, (0, 0, 0, 0), (bx, by), vis_r)
    for r in range(vis_r, vis_r + 70, 2):
        a = min(255, int((r - vis_r) / 70 * fog_a))
        pygame.draw.circle(vis_surf, (210, 220, 240, a), (bx, by), r, 2)
    frame.blit(vis_surf, (0, 0))
    vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    vig_a = int(70 + 30 * gust_cycle)
    for yb in range(90):
        a = int(vig_a * (1 - yb / 90))
        pygame.draw.line(vig, (200, 210, 230, a), (0, yb), (WIDTH, yb))
        pygame.draw.line(vig, (200, 210, 230, a), (0, HEIGHT - yb), (WIDTH, HEIGHT - yb))
    for xb in range(70):
        a = int(vig_a * 0.7 * (1 - xb / 70))
        pygame.draw.line(vig, (200, 210, 230, a), (xb, 0), (xb, HEIGHT))
        pygame.draw.line(vig, (200, 210, 230, a), (WIDTH - xb, 0), (WIDTH - xb, HEIGHT))
    frame.blit(vig, (0, 0))
    frost = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    frost_a = int(50 + 20 * math.sin(game_time * 0.3))
    for edge_i in range(40):
        for _ in range(8):
            fx = random.Random(edge_i * 100 + _ + 7777).choice([
                random.Random(edge_i * 100 + _).randint(0, 50 + edge_i),
                random.Random(edge_i * 100 + _ + 50).randint(WIDTH - 50 - edge_i, WIDTH)])
            fy = random.Random(edge_i * 200 + _ + 8888).randint(0, HEIGHT)
            pygame.draw.circle(frost, (230, 240, 255, frost_a), (fx, fy), random.Random(edge_i + _).randint(2, 6))
    frame.blit(frost, (0, 0))
    lc = math.sin(game_time * 0.35) + math.sin(game_time * 0.47)
    if lc > 1.85:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((240, 245, 255, min(180, int(180 * (lc - 1.85) / 0.15))))
        frame.blit(flash, (0, 0))
    vib = 0.4 + gust_cycle * 1.2
    shake.offset_x += math.sin(game_time * 16) * vib
    shake.offset_y += math.cos(game_time * 13) * vib * 0.5

while running:
    dt = clock.tick(60) / 1000.0
    dt = min(dt, 0.05)  # Cap dt to prevent physics explosion
    current_time = pygame.time.get_ticks() / 1000.0
    game_time += dt

    # Update fade transition globally
    fade.update(dt)

    # ============================================================
    # MENU STATE
    # ============================================================
    if game_state == "menu":
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        # Play intro voiceover once
        if not intro_vo_played:
            intro_vo_played = True
            dur = voiceover.play("intro.mp3", 0.9)
            if dur > 0:
                dialog.show(
                    "Welcome to Cross River! Navigate your boat through treacherous waters "
                    "and reach the other side. Choose your mode and begin your journey.",
                    dur)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if not fade.active:
                        def go_mode_select_key():
                            global game_state, mode_selected_idx
                            game_state = "mode_select"
                            mode_selected_idx = None
                            for c in mode_cards:
                                c.selected = False
                                c.expand_amount = 0
                            dialog.hide()
                            voiceover.stop()
                        fade.start(go_mode_select_key)

        for btn in menu_buttons:
            if btn.update(mouse_pos, mouse_click, dt):
                if btn is btn_play:
                    if not fade.active:
                        def go_mode_select_play():
                            global game_state, mode_selected_idx
                            game_state = "mode_select"
                            mode_selected_idx = None
                            for c in mode_cards:
                                c.selected = False
                                c.expand_amount = 0
                            dialog.hide()
                            voiceover.stop()
                        fade.start(go_mode_select_play)
                elif btn is btn_settings:
                    if not fade.active:
                        def go_settings():
                            global game_state
                            game_state = "settings"
                            dialog.hide()
                            voiceover.stop()
                        fade.start(go_settings)
                elif btn is btn_quit:
                    running = False

        menu_boat_angle = math.sin(game_time * 0.3) * 12
        draw_menu(screen, water, game_time, dt, menu_buttons, menu_boat_angle)
        dialog.update(dt)
        dialog.draw(screen, game_time)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # SETTINGS STATE
    # ============================================================
    if game_state == "settings":
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_settings():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_settings)

        # Update sliders
        for s in settings_sliders:
            s.update(mouse_pos, mouse_down)

        # Apply volume changes (module-level vars, no global needed in while loop)
        volume_music = settings_sliders[0].value
        volume_sfx = settings_sliders[1].value
        volume_ambience = settings_sliders[2].value

        if AUDIO_AVAILABLE:
            try:
                pygame.mixer.music.set_volume(volume_music)
            except Exception:
                pass
            if ambience_sound:
                try:
                    ambience_sound.set_volume(volume_ambience)
                except Exception:
                    pass

        # Back button
        if settings_back_btn.update(mouse_pos, mouse_click, dt):
            if not fade.active:
                def go_menu_from_settings_btn():
                    global game_state
                    game_state = "menu"
                fade.start(go_menu_from_settings_btn)

        draw_settings(screen, water, game_time, dt, settings_sliders, settings_back_btn)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # MODE SELECT STATE
    # ============================================================
    if game_state == "mode_select":
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_mode():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_mode)

        # Update cards — click directly navigates
        for i, card in enumerate(mode_cards):
            if card.update(mouse_pos, mouse_click, dt, game_time):
                if not fade.active:
                    selected_mode = card.title
                    if selected_mode == "Tutorial":
                        def go_tutorial():
                            global game_state, tutorial_step, tutorial_boat_pos, tutorial_boat_angle
                            global tutorial_boat_vel, tutorial_oar, tutorial_wake
                            global tutorial_prompt_alpha, tutorial_step_timer, tutorial_vo_triggered
                            game_state = "tutorial"
                            tutorial_step = 0
                            tutorial_boat_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2 + 80)
                            tutorial_boat_angle = 0.0
                            tutorial_boat_vel = pygame.Vector2(0, 0)
                            tutorial_oar = OarAnimator()
                            tutorial_wake = WakeSystem()
                            tutorial_prompt_alpha = 0.0
                            tutorial_step_timer = 0.0
                            tutorial_vo_triggered = False
                        fade.start(go_tutorial)
                    elif selected_mode == "Seasons":
                        def go_seasons():
                            global game_state, seasons_scroll_idx, seasons_prev_idx
                            global seasons_scroll_offset, seasons_bg_color, current_mode
                            current_mode = "seasons"
                            game_state = "seasons"
                            seasons_scroll_idx = 0
                            seasons_prev_idx = 0
                            seasons_scroll_offset = 0.0
                            seasons_bg_color = list(seasons_list[0].bg_color)
                            if season_videos[0]:
                                season_videos[0].restart()
                        fade.start(go_seasons)
                    elif selected_mode == "Speed Run":
                        def go_speedrun_setup():
                            global game_state, current_mode
                            global speedrun_active, speedrun_season_idx, speedrun_level, speedrun_chrono
                            global speedrun_num_players, speedrun_current_player
                            global speedrun_player_names, speedrun_player_times
                            global speedrun_name_input, speedrun_name_phase, speedrun_choosing_players
                            current_mode = "speedrun"
                            game_state = "speedrun_setup"
                            speedrun_active = False
                            speedrun_season_idx = 0
                            speedrun_level = 1
                            speedrun_chrono = 0.0
                            speedrun_num_players = 1
                            speedrun_current_player = 1
                            speedrun_player_names = ["", ""]
                            speedrun_player_times = [0.0, 0.0]
                            speedrun_name_input = ""
                            speedrun_name_phase = 1
                            speedrun_choosing_players = True
                        fade.start(go_speedrun_setup)

        # Back button
        if mode_back_btn.update(mouse_pos, mouse_click, dt):
            if not fade.active:
                def go_menu_from_mode_back():
                    global game_state
                    game_state = "menu"
                fade.start(go_menu_from_mode_back)

        draw_mode_select(screen, water, game_time, dt, mode_cards, mode_back_btn)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # TUTORIAL STATE
    # Steps: 0=intro_vo, 1=prompt_left, 2=left_success, 3=prompt_right,
    #         4=right_success, 5=free_practice, 6=outro, 7=done
    # ============================================================
    if game_state == "tutorial":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_mode_from_tutorial():
                            global game_state
                            game_state = "mode_select"
                            dialog.hide()
                            voiceover.stop()
                        fade.start(go_mode_from_tutorial)
                # Step 1: waiting for LEFT key
                elif tutorial_step == 1 and event.key == pygame.K_LEFT:
                    tutorial_oar.trigger_left()
                    play_paddle_sound()
                    tutorial_boat_angle += ROTATION_STEP
                    tutorial_boat_vel = pygame.Vector2(0, -1).rotate(tutorial_boat_angle) * 3
                    tutorial_step = 2
                    tutorial_step_timer = 0.0
                    tutorial_vo_triggered = False
                    tutorial_prompt_alpha = 0.0
                    dialog.hide()
                    voiceover.stop()
                # Step 3: waiting for RIGHT key
                elif tutorial_step == 3 and event.key == pygame.K_RIGHT:
                    tutorial_oar.trigger_right()
                    play_paddle_sound()
                    tutorial_boat_angle -= ROTATION_STEP
                    tutorial_boat_vel = pygame.Vector2(0, -1).rotate(tutorial_boat_angle) * 3
                    tutorial_step = 4
                    tutorial_step_timer = 0.0
                    tutorial_vo_triggered = False
                    tutorial_prompt_alpha = 0.0
                    dialog.hide()
                    voiceover.stop()
                # Step 5 & 7: free practice - any arrow key moves the boat
                elif tutorial_step in (5, 7):
                    if event.key == pygame.K_LEFT:
                        tutorial_oar.trigger_left()
                        play_paddle_sound()
                        tutorial_boat_angle += ROTATION_STEP
                        tutorial_boat_vel += pygame.Vector2(0, -1).rotate(tutorial_boat_angle) * 2
                    elif event.key == pygame.K_RIGHT:
                        tutorial_oar.trigger_right()
                        play_paddle_sound()
                        tutorial_boat_angle -= ROTATION_STEP
                        tutorial_boat_vel += pygame.Vector2(0, -1).rotate(tutorial_boat_angle) * 2

        # Update boat physics
        tutorial_boat_vel *= 0.95
        tutorial_boat_pos += tutorial_boat_vel * dt * 20
        tutorial_boat_pos.x = max(50, min(WIDTH - 50, tutorial_boat_pos.x))
        tutorial_boat_pos.y = max(50, min(HEIGHT - 50, tutorial_boat_pos.y))

        tutorial_oar.update(dt)
        tutorial_wake.update(dt, tutorial_boat_pos, tutorial_boat_angle,
                             tutorial_boat_vel.length())
        tutorial_prompt_alpha = min(255, tutorial_prompt_alpha + 300 * dt)
        tutorial_step_timer += dt

        # ---- Step logic and voiceovers ----
        # Step 0: Intro voiceover
        if tutorial_step == 0:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                intro_text = (
                    "Welcome, captains! You share one canoe — one paddle each. "
                    "Player 1 uses the Left key, Player 2 uses the Right key. "
                    "Sync your strokes to move forward. Let's try it!"
                )
                dur = voiceover.play("tutorial_intro.mp3", 0.9)
                if dur > 0:
                    dialog.show(intro_text, dur)
                else:
                    dialog.show(intro_text)
            # Wait for VO to finish, then advance
            if tutorial_vo_triggered and not voiceover.is_playing() and tutorial_step_timer > 2.0:
                tutorial_step = 1
                tutorial_step_timer = 0.0
                tutorial_vo_triggered = False
                tutorial_prompt_alpha = 0.0
                dialog.hide()

        # Step 1: Prompt LEFT key
        elif tutorial_step == 1:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                dur = voiceover.play("tutorial_left.mp3", 0.9)
                text = "Player 1, press the Left Key to use the left paddle."
                if dur > 0:
                    dialog.show(text, dur)
                else:
                    dialog.show(text)

        # Step 2: Left success feedback
        elif tutorial_step == 2:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                dur = voiceover.play("tutorial_left_success.mp3", 0.9)
                text = "Nice! Look at that technique. Olympic committee already watching."
                if dur > 0:
                    dialog.show(text, dur)
                else:
                    dialog.show(text)
            if not voiceover.is_playing() and tutorial_step_timer > 1.5:
                tutorial_step = 3
                tutorial_step_timer = 0.0
                tutorial_vo_triggered = False
                tutorial_prompt_alpha = 0.0
                dialog.hide()

        # Step 3: Prompt RIGHT key
        elif tutorial_step == 3:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                dur = voiceover.play("tutorial_right.mp3", 0.9)
                text = "Now Player 2, press the Right Key to use the right paddle."
                if dur > 0:
                    dialog.show(text, dur)
                else:
                    dialog.show(text)

        # Step 4: Right success feedback
        elif tutorial_step == 4:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                dur = voiceover.play("tutorial_right_success.mp3", 0.9)
                text = "Perfect! Now you're both in control of the canoe."
                if dur > 0:
                    dialog.show(text, dur)
                else:
                    dialog.show(text)
            if not voiceover.is_playing() and tutorial_step_timer > 1.5:
                tutorial_step = 5
                tutorial_step_timer = 0.0
                tutorial_vo_triggered = False
                tutorial_prompt_alpha = 0.0
                dialog.hide()

        # Step 5: Free practice
        elif tutorial_step == 5:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                dur = voiceover.play("tutorial_practice.mp3", 0.9)
                text = "Now paddle together. Alternate left and right to go straight."
                if dur > 0:
                    dialog.show(text, dur)
                else:
                    dialog.show(text)
            if not voiceover.is_playing() and tutorial_step_timer > 3.0:
                tutorial_step = 6
                tutorial_step_timer = 0.0
                tutorial_vo_triggered = False
                dialog.hide()

        # Step 6: Outro
        elif tutorial_step == 6:
            if not tutorial_vo_triggered:
                tutorial_vo_triggered = True
                dur = voiceover.play("tutorial_outro.mp3", 0.9)
                text = "Well done! Head to Seasons mode to start your adventure. Good luck, captains!"
                if dur > 0:
                    dialog.show(text, dur)
                else:
                    dialog.show(text)
            if not voiceover.is_playing() and tutorial_step_timer > 2.0:
                tutorial_step = 7

        # Step 7: Done - stay in tutorial for free practice
        elif tutorial_step == 7:
            dialog.hide()
            voiceover.stop()

        # Determine prompt text for on-screen display
        if tutorial_step == 0:
            prompt_text = ""
        elif tutorial_step == 1:
            prompt_text = "Press LEFT arrow"
        elif tutorial_step == 2:
            prompt_text = "Nice!"
        elif tutorial_step == 3:
            prompt_text = "Press RIGHT arrow"
        elif tutorial_step == 4:
            prompt_text = "Perfect!"
        elif tutorial_step == 5:
            prompt_text = "Free Practice"
        elif tutorial_step == 6:
            prompt_text = ""
        else:
            prompt_text = ""

        # Map step to draw_tutorial's step param (0=right prompt, 1=left prompt)
        draw_step = 1 if tutorial_step == 1 else (0 if tutorial_step == 3 else -1)

        draw_tutorial(screen, water, game_time, dt, tutorial_boat_pos,
                      tutorial_boat_angle, tutorial_oar, tutorial_wake,
                      draw_step, prompt_text, tutorial_prompt_alpha)
        dialog.update(dt)
        dialog.draw(screen, game_time)

        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]

        # Skip button: visible from step 0 through step 6
        if tutorial_step < 7:
            if tutorial_skip_btn.update(mouse_pos, mouse_down, dt):
                voiceover.stop()
                dialog.hide()
                tutorial_step = 7
            tutorial_skip_btn.draw(screen)

        # Back button: visible once tutorial is done (step 7)
        if tutorial_step == 7:
            if tutorial_back_btn.update(mouse_pos, mouse_down, dt):
                if not fade.active:
                    def go_mode_from_tutorial_back():
                        global game_state
                        game_state = "mode_select"
                        dialog.hide()
                        voiceover.stop()
                    fade.start(go_mode_from_tutorial_back)
            tutorial_back_btn.draw(screen)

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # SEASONS SELECT STATE
    # ============================================================
    if game_state == "seasons":
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_mode_from_seasons():
                            global game_state
                            game_state = "mode_select"
                        fade.start(go_mode_from_seasons)
                elif event.key == pygame.K_UP:
                    if seasons_scroll_idx > 0:
                        seasons_scroll_idx -= 1
                elif event.key == pygame.K_DOWN:
                    if seasons_scroll_idx < len(seasons_list) - 1:
                        seasons_scroll_idx += 1
                elif event.key == pygame.K_RETURN:
                    if seasons_list[seasons_scroll_idx].playable and not fade.active:
                        def start_from_seasons():
                            global game_state, current_season
                            current_season = seasons_list[seasons_scroll_idx].name.lower()
                            game_state = "playing"
                            reset_game()
                        fade.start(start_from_seasons)
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0 and seasons_scroll_idx > 0:
                    seasons_scroll_idx -= 1
                elif event.y < 0 and seasons_scroll_idx < len(seasons_list) - 1:
                    seasons_scroll_idx += 1

        # Restart video when season selection changes
        if seasons_scroll_idx != seasons_prev_idx:
            seasons_prev_idx = seasons_scroll_idx
            vid = season_videos[seasons_scroll_idx] if seasons_scroll_idx < len(season_videos) else None
            if vid:
                vid.restart()

        # Smooth background color transition
        target_bg = seasons_list[seasons_scroll_idx].bg_color
        for i in range(3):
            seasons_bg_color[i] += (target_bg[i] - seasons_bg_color[i]) * min(1.0, 3.0 * dt)

        # Smooth scroll offset (always lerp to 0 since items position relative to scroll_idx)
        seasons_scroll_offset *= max(0, 1.0 - 8.0 * dt)

        # Play button
        play_clicked = False
        if seasons_list[seasons_scroll_idx].playable:
            play_clicked = seasons_play_btn.update(mouse_pos, mouse_click, dt)

        # Back button
        if seasons_back_btn.update(mouse_pos, mouse_click, dt):
            if not fade.active:
                def go_mode_from_seasons_btn():
                    global game_state
                    game_state = "mode_select"
                fade.start(go_mode_from_seasons_btn)

        if play_clicked and not fade.active:
            def start_from_seasons_btn():
                global game_state, current_season
                current_season = seasons_list[seasons_scroll_idx].name.lower()
                game_state = "playing"
                reset_game()
            fade.start(start_from_seasons_btn)

        draw_seasons_menu(screen, water, game_time, dt, seasons_list, seasons_scroll_idx,
                          seasons_scroll_offset, seasons_bg_color, seasons_play_btn,
                          seasons_back_btn)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # SPEED RUN SETUP STATE
    # ============================================================
    if game_state == "speedrun_setup":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def sr_back():
                            global game_state
                            game_state = "menu"
                        fade.start(sr_back)
                if speedrun_choosing_players:
                    if event.key == pygame.K_1:
                        speedrun_num_players = 1
                        speedrun_choosing_players = False
                        speedrun_name_input = ""
                        speedrun_name_phase = 1
                    elif event.key == pygame.K_2:
                        speedrun_num_players = 2
                        speedrun_choosing_players = False
                        speedrun_name_input = ""
                        speedrun_name_phase = 1
                else:
                    if event.key == pygame.K_RETURN and len(speedrun_name_input.strip()) > 0:
                        speedrun_player_names[speedrun_name_phase - 1] = speedrun_name_input.strip()
                        if speedrun_name_phase < speedrun_num_players:
                            speedrun_name_phase += 1
                            speedrun_name_input = ""
                        else:
                            def start_speedrun():
                                global game_state, current_season, speedrun_active
                                global speedrun_season_idx, speedrun_level, speedrun_chrono, speedrun_current_player
                                speedrun_active = True
                                speedrun_season_idx = 0
                                speedrun_level = 1
                                speedrun_current_player = 1
                                speedrun_chrono = 0.0
                                current_season = speedrun_season_order[0]
                                game_state = "playing"
                                reset_game()
                            fade.start(start_speedrun)
                    elif event.key == pygame.K_BACKSPACE:
                        speedrun_name_input = speedrun_name_input[:-1]
                    elif len(speedrun_name_input) < 12 and event.unicode.isprintable() and event.unicode:
                        speedrun_name_input += event.unicode

        water.draw(screen, dt, game_time)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Title
        sr_title = title_font.render("SPEED RUN", True, (255, 180, 40))
        screen.blit(sr_title, sr_title.get_rect(center=(WIDTH // 2, 120)))

        if speedrun_choosing_players:
            p_text = font.render("How many players?", True, (220, 220, 220))
            screen.blit(p_text, p_text.get_rect(center=(WIDTH // 2, 250)))
            b1 = font.render("Press 1 - Single Player", True, (100, 255, 150))
            b2 = font.render("Press 2 - Two Players", True, (100, 200, 255))
            screen.blit(b1, b1.get_rect(center=(WIDTH // 2, 340)))
            screen.blit(b2, b2.get_rect(center=(WIDTH // 2, 400)))
            info = subtitle_font.render("Forest > Snow > Desert  |  9 Levels  |  1 Run", True, (150, 150, 150))
            screen.blit(info, info.get_rect(center=(WIDTH // 2, 500)))
        else:
            prompt = font.render(f"Player {speedrun_name_phase} - Enter your name:", True, (220, 220, 220))
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, 260)))
            # Input box
            box_w, box_h = 400, 50
            box_x = WIDTH // 2 - box_w // 2
            box_y = 320
            pygame.draw.rect(screen, (40, 40, 60), (box_x, box_y, box_w, box_h), border_radius=8)
            pygame.draw.rect(screen, (100, 150, 255), (box_x, box_y, box_w, box_h), 2, border_radius=8)
            name_surf = subtitle_font.render(speedrun_name_input, True, (255, 255, 255))
            # Center text vertically in box
            name_y = box_y + (box_h - name_surf.get_height()) // 2
            screen.blit(name_surf, (box_x + 15, name_y))
            # Cursor blink
            if int(game_time * 2) % 2 == 0:
                cx = box_x + 15 + name_surf.get_width() + 2
                pygame.draw.line(screen, (255, 255, 255), (cx, name_y + 2), (cx, name_y + name_surf.get_height() - 2), 2)
            hint = subtitle_font.render("Press ENTER to confirm", True, (150, 150, 150))
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 420)))

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # SPEED RUN COMPLETE STATE
    # ============================================================
    if game_state == "speedrun_complete":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def sr_to_menu():
                            global game_state, speedrun_active
                            game_state = "menu"
                            speedrun_active = False
                        fade.start(sr_to_menu)

        water.draw(screen, dt, game_time)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        complete_title = title_font.render("SPEED RUN COMPLETE!", True, (255, 180, 40))
        screen.blit(complete_title, complete_title.get_rect(center=(WIDTH // 2, 120)))

        t = speedrun_player_times[0]
        if speedrun_num_players == 1:
            name = speedrun_player_names[0]
            result = font.render(f"{name} finished in {int(t//60)}:{t%60:04.1f}", True, (100, 255, 150))
            screen.blit(result, result.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        else:
            n1 = speedrun_player_names[0]
            n2 = speedrun_player_names[1]
            result = font.render(f"{n1} & {n2} finished in {int(t//60)}:{t%60:04.1f}", True, (100, 255, 150))
            screen.blit(result, result.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        hint = subtitle_font.render("Press ENTER", True, (150, 150, 150))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 80)))

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 1 COMPLETE STATE
    # ============================================================
    if game_state == "level1_complete":
        l1_complete_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        complete_text = title_font.render("LEVEL COMPLETE!", True, (50, 255, 80))
        # glow
        glow = title_font.render("LEVEL COMPLETE!", True, (30, 180, 50))
        glow.set_alpha(60)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 57)))
        screen.blit(complete_text, complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
        # Subtitle
        sub = subtitle_font.render("Preparing Level 2...", True, (180, 200, 220))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
        if l1_complete_timer >= (0.5 if speedrun_active else 2.0) and not fade.active:
            def start_l2():
                global game_state, speedrun_level
                game_state = "level2"
                if speedrun_active:
                    speedrun_level = 2
                reset_level2()
            fade.start(start_l2)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 2 WIN STATE
    # ============================================================
    if game_state == "level2_win":
        l2_win_blink_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_win():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_win)

        # Draw water background
        water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))

        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # "YOU WIN!" in green
        complete_text = title_font.render("YOU WIN!", True, (50, 255, 80))
        complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        # Glow
        glow = title_font.render("YOU WIN!", True, (30, 180, 50))
        glow.set_alpha(60)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 57)))
        screen.blit(complete_text, complete_rect)

        # Score (hidden in seasons mode)
        if current_mode not in ("seasons",):
            score_str = f"Time remaining: {l2_timer:.1f}s"
            score_surf = font.render(score_str, True, (255, 255, 200))
            score_rect = score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            screen.blit(score_surf, score_rect)

        # Blinking hint
        if int(l2_win_blink_timer * 2) % 2 == 0:
            hint_surf = subtitle_font.render("Press ENTER or ESC", True, (180, 200, 220))
            hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen.blit(hint_surf, hint_rect)

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 2 COMPLETE STATE (transition to Level 3)
    # ============================================================
    if game_state == "level2_complete":
        l2_complete_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        complete_text = title_font.render("LEVEL 2 COMPLETE!", True, (50, 255, 80))
        glow = title_font.render("LEVEL 2 COMPLETE!", True, (30, 180, 50))
        glow.set_alpha(60)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 57)))
        screen.blit(complete_text, complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
        sub = subtitle_font.render("Preparing Level 3...", True, (180, 200, 220))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
        if l2_complete_timer >= (0.5 if speedrun_active else 2.0) and not fade.active:
            def start_l3():
                global game_state, speedrun_level
                game_state = "level3"
                if speedrun_active:
                    speedrun_level = 3
                reset_level3()
            fade.start(start_l3)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 3 WIN STATE
    # ============================================================
    if game_state == "level3_win":
        l3_win_blink_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        if speedrun_active:
                            fade.start(_advance_speedrun)
                        else:
                            def go_menu_from_l3():
                                global game_state
                                game_state = "menu"
                            fade.start(go_menu_from_l3)

        if current_season == "snow":
            # Frozen water for L3 win screen
            screen.fill((220, 230, 245))
        else:
            water.draw(screen, dt, game_time, palette=WATER_PALETTES.get(current_season))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        complete_text = title_font.render("YOU WIN!", True, (50, 255, 80))
        glow = title_font.render("YOU WIN!", True, (30, 180, 50))
        glow.set_alpha(60)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 57)))
        screen.blit(complete_text, complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
        if current_mode not in ("seasons",):
            score_str = f"Time remaining: {l3_timer:.1f}s"
            score_surf = font.render(score_str, True, (255, 255, 200))
            screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
        if int(l3_win_blink_timer * 2) % 2 == 0:
            hint_surf = subtitle_font.render("Press ENTER or ESC", True, (180, 200, 220))
            screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 3 PLAYING STATE
    # ============================================================
    if game_state == "level3":
        l3_input_this_frame = False

        # Timer countdown (disabled in seasons/speedrun mode)
        if current_mode not in ("seasons", "speedrun"):
            l3_timer -= dt
        if speedrun_active:
            speedrun_chrono += dt
        if l3_timer <= 0:
            l3_timer = 0
            if not fade.active:
                def l3_timeout():
                    global game_state
                    game_state = "menu"
                fade.start(l3_timeout)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_l3():
                            global game_state, speedrun_active
                            game_state = "menu"
                            speedrun_active = False
                        fade.start(go_menu_l3)

                if not l3_crash.active:
                    if event.key == pygame.K_LEFT:
                        if not l3_left_pressed:
                            l3_left_pressed = True
                            l3_oar.trigger_left()
                            play_paddle_sound()
                            if not l3_rotating:
                                l3_rotation_start_angle = l3_boat_angle
                                l3_rotation_direction = 1
                                l3_target_angle = (l3_rotation_start_angle + ROTATION_STEP) % 360
                                l3_rotating = True
                            else:
                                if l3_rotation_direction == -1:
                                    l3_target_angle = l3_rotation_start_angle % 360
                                    l3_rotation_direction = 0
                        l3_input_buffer += 1
                        last_input_time = current_time
                        l3_input_this_frame = True

                    if event.key == pygame.K_RIGHT:
                        if not l3_right_pressed:
                            l3_right_pressed = True
                            l3_oar.trigger_right()
                            play_paddle_sound()
                            if not l3_rotating:
                                l3_rotation_start_angle = l3_boat_angle
                                l3_rotation_direction = -1
                                l3_target_angle = (l3_rotation_start_angle - ROTATION_STEP) % 360
                                l3_rotating = True
                            else:
                                if l3_rotation_direction == 1:
                                    l3_target_angle = l3_rotation_start_angle % 360
                                    l3_rotation_direction = 0
                        l3_input_buffer += 1
                        last_input_time = current_time
                        l3_input_this_frame = True

                    if event.key == pygame.K_DOWN:
                        if not l3_down_pressed:
                            l3_down_pressed = True
                            l3_oar.trigger_left()
                            l3_oar.trigger_right()
                            play_paddle_sound()
                            if not l3_rotating:
                                l3_rotation_start_angle = l3_boat_angle
                                l3_rotation_direction = 1
                                l3_target_angle = (l3_rotation_start_angle + ROTATION_STEP) % 360
                                l3_rotating = True
                            else:
                                if l3_rotation_direction == -1:
                                    l3_target_angle = l3_rotation_start_angle % 360
                                    l3_rotation_direction = 0
                        last_input_time = current_time
                        l3_input_this_frame = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    l3_left_pressed = False
                if event.key == pygame.K_RIGHT:
                    l3_right_pressed = False
                if event.key == pygame.K_DOWN:
                    l3_down_pressed = False

        if not l3_input_this_frame:
            if current_time - last_input_time > input_decay_time:
                l3_input_buffer = 0
            else:
                l3_input_buffer *= math.exp(-dt / input_decay_time)

        # ---- SMOOTH ROTATION ----
        l3_boat_angle, l3_rotating, l3_rotation_direction = _smooth_rotation(
            l3_boat_angle, l3_target_angle, l3_rotating, l3_rotation_direction, dt)

        # ---- PHYSICS ----
        l3_boat_vel = _apply_boat_physics(
            l3_boat_vel, l3_boat_angle, l3_input_buffer,
            l3_left_pressed, l3_right_pressed, dt, season=current_season)

        # Sandstorm wind for desert L3
        if current_season == "desert":
            l3_boat_vel.x += math.sin(game_time * 1.0) * 0.15 * dt
            l3_boat_vel.y += math.cos(game_time * 0.8) * 0.1 * dt

        # Slow zones
        if l3_slow_zones and point_in_any_slow_zone(l3_boat_pos.x, l3_boat_pos.y, l3_slow_zones):
            l3_boat_vel *= 0.5

        l3_boat_pos += l3_boat_vel

        # ---- COLLISION DETECTION ----
        if (_aabb_circle(l3_boat_pos.x, l3_boat_pos.y, boat_collision_radius, l3_cubes) or
                _poly_circle_hit(l3_boat_pos.x, l3_boat_pos.y, boat_collision_radius, l3_poly_obstacles)):
            if not l3_crash.active:
                l3_shake.trigger(6, 0.5)
                play_sound(crash_sfx)
                l3_crash.trigger(l3_boat_pos, l3_boat_angle, _do_l3_respawn)
                l3_boat_vel = pygame.Vector2(0, 0)

        # Clamp to screen
        l3_boat_pos.x = max(boat_collision_radius, min(WIDTH - boat_collision_radius, l3_boat_pos.x))
        l3_boat_pos.y = max(0, min(HEIGHT, l3_boat_pos.y))

        # ---- WIN CONDITION ----
        if (_check_win(l3_boat_pos, l3_spawn_pos,
                       l3_finish_axis, l3_finish_pos, l3_finish_y,
                       l3_finish_x1, l3_finish_x2, l3_finish_y1, l3_finish_y2)
                and not l3_crash.active and not fade.active):
            if speedrun_active:
                fade.start(_advance_speedrun)
            else:
                def go_l3_win():
                    global game_state, l3_win_blink_timer
                    game_state = "level3_win"
                    l3_win_blink_timer = 0
                fade.start(go_l3_win)

        # ---- UPDATE SYSTEMS ----
        l3_crash.update(dt)
        l3_oar.update(dt)
        l3_wake.update(dt, l3_boat_pos, l3_boat_angle, l3_boat_vel.length())

        # ---- DRAWING ----
        frame = l3_frame

        # Water: frozen (static white) for snow, normal for others
        if current_season == "snow":
            frame.fill((215, 228, 245))
            # Ice cracks/texture
            for i in range(20):
                rng = random.Random(i * 777)
                x1 = rng.randint(0, WIDTH)
                y1 = rng.randint(0, HEIGHT)
                x2 = x1 + rng.randint(-80, 80)
                y2 = y1 + rng.randint(-80, 80)
                pygame.draw.line(frame, (200, 215, 235), (x1, y1), (x2, y2), 1)
        else:
            water.draw(frame, dt, game_time, palette=WATER_PALETTES.get(current_season))

        # Finish glow
        _draw_finish_glow(frame, l3_finish_axis, l3_finish_pos,
                          l3_finish_x1, l3_finish_x2, l3_finish_y,
                          l3_finish_y1, l3_finish_y2, game_time)

        # Foam
        draw_foam(frame, l3_foam_points, game_time)

        # Obstacle surface
        frame.blit(l3_surface, (0, 0))

        # Wake
        l3_wake.draw(frame)

        # Crash
        l3_crash.draw(frame)

        # Boat
        if not l3_crash.active:
            draw_boat(frame, l3_boat_pos, l3_boat_angle, l3_oar, l3_boat_vel.length())

        # Canopy
        frame.blit(l3_canopy, (0, 0))

        # Speedrun chrono + countdown timer
        if speedrun_active:
            _draw_speedrun_hud(frame, speedrun_chrono, speedrun_season_idx, speedrun_level)
        _draw_timer_hud(frame, l3_timer)

        # Level indicator
        lvl_text = subtitle_font.render("Level 3", True, (200, 200, 200))
        frame.blit(lvl_text, (10, 10))

        # SANDSTORM for desert L3
        if current_season == "desert":
            _draw_desert_storm(frame, l3_boat_pos, l3_shake, game_time, 3)

        # Apply shake
        l3_shake.update(dt)
        shake_ox = int(l3_shake.offset_x)
        shake_oy = int(l3_shake.offset_y)
        screen.blit(frame, (shake_ox, shake_oy))
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 2 PLAYING STATE (single-screen, rocks, wind)
    # ============================================================
    if game_state == "level2":
        l2_input_this_frame = False

        # Timer countdown (disabled in seasons/speedrun mode)
        if current_mode not in ("seasons", "speedrun"):
            l2_timer -= dt
        if speedrun_active:
            speedrun_chrono += dt
        if l2_timer <= 0:
            l2_timer = 0
            # Time's up - reset
            reset_level2()

        # Update crash animation
        l2_crash.update(dt)
        l2_shake.update(dt)

        # ---- INPUT HANDLING ----
        if l2_crash.active:
            # During crash, only process QUIT/ESC
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not fade.active:
                            def go_menu_from_l2_crash():
                                global game_state
                                game_state = "menu"
                            fade.start(go_menu_from_l2_crash)
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not fade.active:
                            def go_menu_from_l2():
                                global game_state
                                game_state = "menu"
                            fade.start(go_menu_from_l2)
                        continue
                    if event.key == pygame.K_LEFT:
                        if not l2_left_pressed:
                            l2_left_pressed = True
                            l2_oar.trigger_left()
                            play_paddle_sound()
                            if not l2_rotating:
                                l2_rotation_start_angle = l2_boat_angle
                                l2_rotation_direction = 1
                                l2_target_angle = (l2_rotation_start_angle + ROTATION_STEP) % 360
                                l2_rotating = True
                            else:
                                if l2_rotation_direction == -1:
                                    l2_target_angle = l2_rotation_start_angle % 360
                                    l2_rotation_direction = 0
                        l2_input_buffer += 1
                        last_input_time = current_time
                        l2_input_this_frame = True

                    if event.key == pygame.K_RIGHT:
                        if not l2_right_pressed:
                            l2_right_pressed = True
                            l2_oar.trigger_right()
                            play_paddle_sound()
                            if not l2_rotating:
                                l2_rotation_start_angle = l2_boat_angle
                                l2_rotation_direction = -1
                                l2_target_angle = (l2_rotation_start_angle - ROTATION_STEP) % 360
                                l2_rotating = True
                            else:
                                if l2_rotation_direction == 1:
                                    l2_target_angle = l2_rotation_start_angle % 360
                                    l2_rotation_direction = 0
                        l2_input_buffer += 1
                        last_input_time = current_time
                        l2_input_this_frame = True

                    if event.key == pygame.K_DOWN:
                        if not l2_down_pressed:
                            l2_down_pressed = True
                            l2_oar.trigger_left()
                            l2_oar.trigger_right()
                            play_paddle_sound()
                            if not l2_rotating:
                                l2_rotation_start_angle = l2_boat_angle
                                l2_rotation_direction = 1
                                l2_target_angle = (l2_rotation_start_angle + ROTATION_STEP) % 360
                                l2_rotating = True
                            else:
                                if l2_rotation_direction == -1:
                                    l2_target_angle = l2_rotation_start_angle % 360
                                    l2_rotation_direction = 0
                        last_input_time = current_time
                        l2_input_this_frame = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        l2_left_pressed = False
                    if event.key == pygame.K_RIGHT:
                        l2_right_pressed = False
                    if event.key == pygame.K_DOWN:
                        l2_down_pressed = False

            if not l2_input_this_frame:
                if current_time - last_input_time > input_decay_time:
                    l2_input_buffer = 0
                else:
                    l2_input_buffer *= math.exp(-dt / input_decay_time)

            # ---- SMOOTH ROTATION ----
            l2_boat_angle, l2_rotating, l2_rotation_direction = _smooth_rotation(
                l2_boat_angle, l2_target_angle, l2_rotating, l2_rotation_direction, dt)

            # ---- PHYSICS ----
            # Pre-physics: wind force (not for forest)
            if current_season != "forest":
                l2_wind.update(dt)
                if l2_wind.active and l2_wind.gust_timer < dt * 2:
                    play_sound(wind_sfx, 0.5)
                wind_force = l2_wind.get_force()
                if current_season == "snow":
                    wind_force.x = math.sin(game_time * 1.5) * 0.4 + math.sin(game_time * 0.7) * 0.3
                    wind_force.y = math.cos(game_time * 1.2) * 0.35 + math.sin(game_time * 0.9) * 0.25
                elif current_season == "desert":
                    wind_force *= 0.5
                    wind_force.x += math.sin(game_time * 1.0) * 0.2
                    wind_force.y += math.cos(game_time * 0.8) * 0.15
                l2_boat_vel += wind_force * dt

            l2_boat_vel = _apply_boat_physics(
                l2_boat_vel, l2_boat_angle, l2_input_buffer,
                l2_left_pressed, l2_right_pressed, dt)

            # Slow zones (fix: was missing in L2)
            if l2_slow_zones and point_in_any_slow_zone(l2_boat_pos.x, l2_boat_pos.y, l2_slow_zones):
                l2_boat_vel *= 0.5

            l2_boat_pos += l2_boat_vel

            # ---- COLLISION DETECTION ----
            if _aabb_circle(l2_boat_pos.x, l2_boat_pos.y, boat_collision_radius, level2_cubes):
                if not l2_crash.active:
                    l2_shake.trigger(6, 0.5)
                    play_sound(crash_sfx)
                    l2_crash.trigger(l2_boat_pos, l2_boat_angle, _do_l2_respawn)
                    l2_boat_vel = pygame.Vector2(0, 0)

            # Clamp boat to screen bounds
            l2_boat_pos.x = max(boat_collision_radius, min(WIDTH - boat_collision_radius, l2_boat_pos.x))
            l2_boat_pos.y = max(0, min(HEIGHT, l2_boat_pos.y))

            # ---- WIN CONDITION ----
            if (_check_win(l2_boat_pos, l2_spawn_pos,
                           l2_finish_axis, l2_finish_pos, l2_finish_y,
                           l2_finish_x1, l2_finish_x2, l2_finish_y1, l2_finish_y2)
                    and not l2_crash.active):
                if not fade.active:
                    # Check if Level 3 exists for this season
                    if SEASON_DATA[current_season].get("l3_cubes"):
                        def go_l2_complete():
                            global game_state, l2_complete_timer
                            game_state = "level2_complete"
                            l2_complete_timer = 0
                        fade.start(go_l2_complete)
                    else:
                        def go_l2_win():
                            global game_state, l2_win_blink_timer
                            game_state = "level2_win"
                            l2_win_blink_timer = 0
                        fade.start(go_l2_win)

        # ---- UPDATE SYSTEMS ----
        l2_oar.update(dt)
        l2_speed_for_draw = l2_boat_vel.length()
        l2_wake.update(dt, l2_boat_pos, l2_boat_angle, l2_speed_for_draw)
        l2_particles.update(dt)

        # ---- DRAWING (to frame buffer for shake offset) ----
        frame = l2_frame

        # 1. Water
        water.draw(frame, dt, game_time, palette=WATER_PALETTES.get(current_season))

        # 2. Finish line glow
        _draw_finish_glow(frame, l2_finish_axis, l2_finish_pos,
                          l2_finish_x1, l2_finish_x2, l2_finish_y,
                          l2_finish_y1, l2_finish_y2, game_time)

        # 3. Shoreline foam
        draw_foam(frame, l2_foam_points, game_time)

        # 4. Forest walls
        frame.blit(l2_forest, (0, 0))

        # 5. Rock obstacles
        frame.blit(l2_rock_surface, (0, 0))

        # 6. Wake
        l2_wake.draw(frame)

        # 7. Crash animation
        l2_crash.draw(frame)

        # 8. Boat (hide during crash)
        if not l2_crash.active:
            draw_boat(frame, l2_boat_pos, l2_boat_angle, l2_oar, l2_speed_for_draw)

        # 9. HUD
        if speedrun_active:
            _draw_speedrun_hud(frame, speedrun_chrono, speedrun_season_idx, speedrun_level)
        _draw_timer_hud(frame, l2_timer)
        # Wind indicator removed per user request

        # "Level 2" label (bottom right)
        lvl_label = hud_font.render("Level 2", True, (180, 200, 220))
        frame.blit(lvl_label, (WIDTH - 100, HEIGHT - 35))

        # SANDSTORM / SNOW STORM for L2
        if current_season == "desert":
            _draw_desert_storm(frame, l2_boat_pos, l2_shake, game_time, 2)
        if current_season == "snow":
            _draw_snow_storm(frame, l2_boat_pos, l2_shake, game_time)

        # Blit frame to screen with shake offset
        shake_ox = int(l2_shake.offset_x)
        shake_oy = int(l2_shake.offset_y)
        screen.fill((0, 0, 0))
        screen.blit(frame, (shake_ox, shake_oy))

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 1 PLAYING STATE
    # ============================================================
    input_this_frame = False

    # Timer countdown (disabled in seasons mode)
    if current_mode not in ("seasons", "speedrun"):
        timer_seconds -= dt
    if speedrun_active:
        speedrun_chrono += dt
    if timer_seconds <= 0:
        timer_seconds = 60
        boat_pos = INITIAL_BOAT_POS.copy()
        boat_velocity = pygame.Vector2(0, 0)
        boat_angle = 0
        rotating = False
        input_buffer = 0

    # Update crash and shake
    l1_crash.update(dt)
    l1_shake.update(dt)

    # ---- INPUT HANDLING ----
    if l1_crash.active:
        # During crash, only process QUIT/ESC
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_l1_crash():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_l1_crash)
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_l1():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_l1)
                    continue
                if event.key == pygame.K_LEFT:
                    if not left_pressed:
                        left_pressed = True
                        oar_anim.trigger_left()
                        play_paddle_sound()
                        if not rotating:
                            rotation_start_angle = boat_angle
                            rotation_direction = 1
                            target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                            rotating = True
                        else:
                            if rotation_direction == -1:
                                target_angle = rotation_start_angle % 360
                                rotation_direction = 0
                    input_buffer += 1
                    last_input_time = current_time
                    input_this_frame = True

                if event.key == pygame.K_RIGHT:
                    if not right_pressed:
                        right_pressed = True
                        oar_anim.trigger_right()
                        play_paddle_sound()
                        if not rotating:
                            rotation_start_angle = boat_angle
                            rotation_direction = -1
                            target_angle = (rotation_start_angle - ROTATION_STEP) % 360
                            rotating = True
                        else:
                            if rotation_direction == 1:
                                target_angle = rotation_start_angle % 360
                                rotation_direction = 0
                    input_buffer += 1
                    last_input_time = current_time
                    input_this_frame = True

                if event.key == pygame.K_DOWN:
                    if not down_pressed:
                        down_pressed = True
                        oar_anim.trigger_left()
                        oar_anim.trigger_right()
                        play_paddle_sound()
                        if not rotating:
                            rotation_start_angle = boat_angle
                            rotation_direction = 1
                            target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                            rotating = True
                        else:
                            if rotation_direction == -1:
                                target_angle = rotation_start_angle % 360
                                rotation_direction = 0
                    last_input_time = current_time
                    input_this_frame = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    left_pressed = False
                if event.key == pygame.K_RIGHT:
                    right_pressed = False
                if event.key == pygame.K_DOWN:
                    down_pressed = False

        if not input_this_frame:
            if current_time - last_input_time > input_decay_time:
                input_buffer = 0
            else:
                input_buffer *= math.exp(-dt / input_decay_time)

        # ---- SMOOTH ROTATION ----
        boat_angle, rotating, rotation_direction = _smooth_rotation(
            boat_angle, target_angle, rotating, rotation_direction, dt)

        # ---- PHYSICS ----
        boat_velocity = _apply_boat_physics(
            boat_velocity, boat_angle, input_buffer,
            left_pressed, right_pressed, dt)

        # Slow zones
        if l1_slow_zones and point_in_any_slow_zone(boat_pos.x, boat_pos.y, l1_slow_zones):
            boat_velocity *= 0.5

        boat_pos += boat_velocity

        # Screen clamp (fix: was missing in L1)
        boat_pos.x = max(boat_collision_radius, min(WIDTH - boat_collision_radius, boat_pos.x))
        boat_pos.y = max(0, min(HEIGHT, boat_pos.y))

        # ---- COLLISION DETECTION ----
        if _aabb_circle(boat_pos.x, boat_pos.y, boat_collision_radius, cubes):
            if not l1_crash.active:
                l1_shake.trigger(6, 0.5)
                play_sound(crash_sfx)
                l1_crash.trigger(boat_pos, boat_angle, _do_l1_respawn)
                boat_velocity = pygame.Vector2(0, 0)

        # ---- WIN CONDITION ----
        if (_check_win(boat_pos, l1_spawn_pos,
                       l1_finish_axis, l1_finish_pos, l1_finish_y,
                       l1_finish_x1, l1_finish_x2, l1_finish_y1, l1_finish_y2)
                and not l1_crash.active and not fade.active):
            def go_level1_complete():
                global game_state, l1_complete_timer
                game_state = "level1_complete"
                l1_complete_timer = 0
            fade.start(go_level1_complete)

    # ---- UPDATE ANIMATIONS ----
    oar_anim.update(dt)
    wake.update(dt, boat_pos, boat_angle, boat_velocity.length())

    # ---- DRAWING (to frame buffer for shake) ----
    frame = l1_frame

    # 1. Animated water background
    water.draw(frame, dt, game_time, palette=WATER_PALETTES.get(current_season))

    # 2. Exit glow indicator
    _draw_finish_glow(frame, l1_finish_axis, l1_finish_pos,
                      l1_finish_x1, l1_finish_x2, l1_finish_y,
                      l1_finish_y1, l1_finish_y2, game_time)

    # 3. Shoreline foam (before forest so it's partly hidden at edges)
    draw_foam(frame, foam_points, game_time)

    # 4. Pre-rendered forest overlay
    frame.blit(forest_surface, (0, 0))

    # 5. Wake trail
    wake.draw(frame)

    # 6. Crash animation
    l1_crash.draw(frame)

    # 7. Boat with animated oars (hide during crash)
    if not l1_crash.active:
        draw_boat(frame, boat_pos, boat_angle, oar_anim, boat_velocity.length())

    # 7b. Tree canopy overlay (rendered ABOVE boat so boat goes under trees)
    frame.blit(canopy_surface, (0, 0))

    # Speedrun chrono + countdown timer
    if speedrun_active:
        _draw_speedrun_hud(frame, speedrun_chrono, speedrun_season_idx, speedrun_level)
    _draw_timer_hud(frame, timer_seconds)

    # Blit frame to screen with shake offset
    shake_ox = int(l1_shake.offset_x)
    shake_oy = int(l1_shake.offset_y)
    screen.fill((0, 0, 0))
    screen.blit(frame, (shake_ox, shake_oy))

    fade.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
