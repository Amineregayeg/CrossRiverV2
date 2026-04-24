#!/usr/bin/env python3
"""
CrossRiver Map Editor — Local visual editor for designing game maps.
Run: python map_editor.py
Then open http://localhost:8099 in your browser.

Features:
- Import sketch as reference background (with opacity slider)
- Draw obstacle rectangles (walls) on canvas at 1250×650 game resolution
- Asset panel with all project assets (auto-cropped thumbnails)
- Drag assets onto canvas, resize/rotate them
- Set finish line position
- Save/load map JSON files
- Export maps.py compatible data
"""

import http.server
import json
import os
import io
import base64
import urllib.parse
import socketserver
from pathlib import Path

PORT = 8099
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
SKETCHES_DIR = os.path.join(PROJECT_DIR, "sketches")
MAPS_DIR = os.path.join(PROJECT_DIR, "saved_maps")

# Ensure saved_maps directory exists
os.makedirs(MAPS_DIR, exist_ok=True)

def get_asset_catalog():
    """Scan assets directory and return categorized list."""
    catalog = {}
    for root, dirs, files in os.walk(ASSETS_DIR):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, PROJECT_DIR)
                cat = os.path.relpath(root, ASSETS_DIR)
                if cat not in catalog:
                    catalog[cat] = []
                catalog[cat].append(rel)
    return catalog

def get_sketch_catalog():
    """Scan sketches directory."""
    catalog = {}
    for root, dirs, files in os.walk(SKETCHES_DIR):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, PROJECT_DIR)
                cat = os.path.relpath(root, SKETCHES_DIR)
                if cat not in catalog:
                    catalog[cat] = []
                catalog[cat].append(rel)
    return catalog

def get_saved_maps():
    """List saved map JSON files."""
    maps = []
    if os.path.exists(MAPS_DIR):
        for f in sorted(os.listdir(MAPS_DIR)):
            if f.endswith('.json'):
                maps.append(f)
    return maps

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CrossRiver Map Editor</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #1a1a2e; color: #eee; font-family: 'Segoe UI', system-ui, sans-serif; overflow: hidden; height: 100vh; }

/* Layout */
.app { display: flex; height: 100vh; }
.sidebar-left { width: 280px; background: #16213e; border-right: 1px solid #334; display: flex; flex-direction: column; overflow: hidden; }
.canvas-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.sidebar-right { width: 260px; background: #16213e; border-left: 1px solid #334; display: flex; flex-direction: column; overflow-y: auto; }

/* Top toolbar */
.toolbar { background: #0f3460; padding: 8px 16px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #334; min-height: 48px; flex-shrink: 0; }
.toolbar button { background: #1a1a4e; color: #ddd; border: 1px solid #445; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all 0.15s; }
.toolbar button:hover { background: #2a2a6e; border-color: #668; }
.toolbar button.active { background: #e94560; border-color: #e94560; color: #fff; }
.toolbar .sep { width: 1px; height: 28px; background: #445; margin: 0 4px; }
.toolbar label { font-size: 12px; color: #aab; }
.toolbar select, .toolbar input[type="text"] { background: #1a1a4e; color: #eee; border: 1px solid #445; padding: 4px 8px; border-radius: 4px; font-size: 13px; }

/* Sidebar sections */
.section-header { background: #0f3460; padding: 8px 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #8ab4f8; cursor: pointer; user-select: none; border-bottom: 1px solid #334; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.section-header:hover { background: #144080; }
.section-header .arrow { transition: transform 0.2s; }
.section-header.collapsed .arrow { transform: rotate(-90deg); }

/* Asset panel */
.asset-panel { flex: 1; overflow-y: auto; padding: 4px; }
.asset-category { margin-bottom: 4px; }
.asset-category-title { font-size: 11px; color: #7a8; padding: 4px 8px; background: #1a2a3e; border-radius: 4px; margin: 2px 0; }
.asset-grid { display: flex; flex-wrap: wrap; gap: 4px; padding: 4px; }
.asset-thumb { width: 60px; height: 60px; border: 2px solid transparent; border-radius: 6px; cursor: pointer; background: #111; position: relative; overflow: hidden; transition: all 0.15s; }
.asset-thumb:hover { border-color: #668; transform: scale(1.05); }
.asset-thumb.selected { border-color: #e94560; box-shadow: 0 0 8px rgba(233,69,96,0.4); }
.asset-thumb img { width: 100%; height: 100%; object-fit: contain; }
.asset-thumb .label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.75); font-size: 8px; padding: 1px 3px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Sketch panel */
.sketch-panel { max-height: 200px; overflow-y: auto; padding: 4px; flex-shrink: 0; }
.sketch-item { display: flex; align-items: center; gap: 8px; padding: 4px 8px; cursor: pointer; border-radius: 4px; font-size: 12px; }
.sketch-item:hover { background: #1a2a4e; }
.sketch-item.active { background: #2a3a5e; }
.sketch-thumb { width: 48px; height: 30px; object-fit: cover; border-radius: 3px; border: 1px solid #445; }

/* Canvas */
.canvas-container { flex: 1; display: flex; align-items: center; justify-content: center; background: #111; position: relative; overflow: hidden; }
#mainCanvas { cursor: crosshair; border: 1px solid #445; image-rendering: pixelated; }

/* Properties panel */
.prop-group { padding: 10px 12px; border-bottom: 1px solid #223; }
.prop-group label { display: block; font-size: 11px; color: #889; margin-bottom: 3px; }
.prop-group input, .prop-group select { width: 100%; background: #1a1a3e; color: #eee; border: 1px solid #445; padding: 5px 8px; border-radius: 4px; font-size: 12px; margin-bottom: 6px; }
.prop-group input[type="range"] { padding: 0; }
.prop-row { display: flex; gap: 6px; }
.prop-row > div { flex: 1; }
.prop-row label { font-size: 10px; }

/* Items list */
.items-list { flex: 1; overflow-y: auto; padding: 4px; }
.item-entry { padding: 6px 10px; font-size: 11px; cursor: pointer; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
.item-entry:hover { background: #1a2a4e; }
.item-entry.selected { background: #2a3a5e; border-left: 3px solid #e94560; }
.item-entry .delete-btn { color: #e94560; cursor: pointer; font-size: 14px; padding: 0 4px; }
.item-entry .delete-btn:hover { color: #ff6b8a; }

/* Status bar */
.statusbar { background: #0f3460; padding: 4px 16px; font-size: 11px; color: #889; display: flex; gap: 20px; border-top: 1px solid #334; flex-shrink: 0; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 999; }
.modal { background: #1a1a2e; border: 1px solid #445; border-radius: 12px; padding: 24px; min-width: 400px; max-width: 500px; }
.modal h3 { margin-bottom: 16px; color: #8ab4f8; }
.modal input, .modal select { width: 100%; background: #111; color: #eee; border: 1px solid #445; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 14px; }
.modal .btn-row { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.modal button { padding: 8px 20px; border-radius: 6px; border: 1px solid #445; cursor: pointer; font-size: 13px; }
.modal .btn-primary { background: #e94560; color: #fff; border-color: #e94560; }
.modal .btn-secondary { background: #333; color: #ddd; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #445; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #556; }

/* Finish line handle */
.finish-handle { position: absolute; height: 4px; background: #0f0; cursor: ns-resize; left: 0; right: 0; opacity: 0.7; z-index: 5; }
.finish-handle:hover { opacity: 1; height: 6px; }
</style>
</head>
<body>
<div class="app">

<!-- LEFT SIDEBAR: Sketches + Assets -->
<div class="sidebar-left">
  <div class="section-header" onclick="toggleSection('sketchPanel')">
    <span>Sketch Reference</span><span class="arrow">▼</span>
  </div>
  <div id="sketchPanel" class="sketch-panel"></div>

  <div style="padding:6px 10px; flex-shrink:0; border-bottom:1px solid #334;">
    <label style="font-size:11px;color:#889;">Sketch Opacity</label>
    <input type="range" id="sketchOpacity" min="0" max="100" value="40" style="width:100%;" oninput="state.sketchOpacity=this.value/100; render();">
  </div>

  <div class="section-header" onclick="toggleSection('assetPanel')">
    <span>Assets</span><span class="arrow">▼</span>
  </div>
  <div id="assetPanel" class="asset-panel"></div>
</div>

<!-- CENTER: Toolbar + Canvas -->
<div class="canvas-area">
  <div class="toolbar">
    <button id="toolSelect" class="active" onclick="setTool('select')" title="Select & Move (V)">↖ Select</button>
    <button id="toolRect" onclick="setTool('rect')" title="Draw Obstacle Rectangle (R)">▭ Obstacle</button>
    <button id="toolFinish" onclick="setTool('finish')" title="Set Finish Line (F)">⚑ Finish</button>
    <button id="toolSpawn" onclick="setTool('spawn')" title="Set Spawn Point (S)">⊕ Spawn</button>
    <div class="sep"></div>
    <button onclick="deleteSelected()" title="Delete selected (Del)">✕ Delete</button>
    <button onclick="duplicateSelected()" title="Duplicate (Ctrl+D)">⊞ Clone</button>
    <div class="sep"></div>
    <button onclick="showSaveModal()" title="Save map (Ctrl+S)">💾 Save</button>
    <button onclick="showLoadModal()" title="Load map (Ctrl+O)">📂 Load</button>
    <button onclick="exportMapsPy()" title="Export maps.py data">📋 Export</button>
    <div class="sep"></div>
    <label>Snap:</label>
    <select id="snapSize" onchange="state.snapSize=parseInt(this.value)">
      <option value="1">Off</option>
      <option value="5">5px</option>
      <option value="10" selected>10px</option>
      <option value="25">25px</option>
      <option value="50">50px</option>
    </select>
    <div class="sep"></div>
    <label>Zoom:</label>
    <select id="zoomLevel" onchange="setZoom(parseFloat(this.value))">
      <option value="0.5">50%</option>
      <option value="0.75">75%</option>
      <option value="1" selected>100%</option>
      <option value="1.25">125%</option>
      <option value="1.5">150%</option>
    </select>
  </div>

  <div class="canvas-container" id="canvasContainer">
    <canvas id="mainCanvas" width="1250" height="650"></canvas>
  </div>

  <div class="statusbar">
    <span id="statusCoords">X: 0  Y: 0</span>
    <span id="statusTool">Tool: Select</span>
    <span id="statusItems">Obstacles: 0 | Assets: 0</span>
    <span id="statusMap">No map loaded</span>
  </div>
</div>

<!-- RIGHT SIDEBAR: Properties + Items -->
<div class="sidebar-right">
  <div class="section-header">Map Settings</div>
  <div class="prop-group">
    <label>Map Name</label>
    <input type="text" id="mapName" value="Untitled" oninput="state.mapName=this.value">
    <label>Season</label>
    <select id="mapSeason" onchange="state.mapSeason=this.value">
      <option value="forest">Forest</option>
      <option value="snow">Snow</option>
      <option value="desert">Desert</option>
      <option value="tropics">Tropics</option>
    </select>
    <label>Level #</label>
    <input type="text" id="mapLevel" value="1" oninput="state.mapLevel=parseInt(this.value)||1">
    <label>Time Limit (seconds)</label>
    <input type="text" id="mapTime" value="60" oninput="state.mapTimeLimit=parseInt(this.value)||60">
  </div>

  <div class="section-header" onclick="toggleSection('propPanel')">
    <span>Selection Properties</span><span class="arrow">▼</span>
  </div>
  <div id="propPanel" class="prop-group" style="min-height: 100px;">
    <p style="color:#667;font-size:11px;padding:20px 0;text-align:center;">Select an item to edit properties</p>
  </div>

  <div class="section-header">
    <span>Items</span>
    <span id="itemCount" style="font-size:10px;color:#889;">0</span>
  </div>
  <div id="itemsList" class="items-list"></div>
</div>

</div>

<!-- Save Modal -->
<div id="saveModal" class="modal-overlay" style="display:none;">
  <div class="modal">
    <h3>Save Map</h3>
    <label style="font-size:12px;color:#889;">Filename</label>
    <input type="text" id="saveFilename" placeholder="forest_1_closing_door">
    <div class="btn-row">
      <button class="btn-secondary" onclick="closeSaveModal()">Cancel</button>
      <button class="btn-primary" onclick="saveMap()">Save</button>
    </div>
  </div>
</div>

<!-- Load Modal -->
<div id="loadModal" class="modal-overlay" style="display:none;">
  <div class="modal">
    <h3>Load Map</h3>
    <select id="loadSelect" size="8" style="height:200px;"></select>
    <div class="btn-row">
      <button class="btn-secondary" onclick="closeLoadModal()">Cancel</button>
      <button class="btn-primary" onclick="loadMap()">Load</button>
    </div>
  </div>
</div>

<script>
// ===== STATE =====
const GAME_W = 1250, GAME_H = 650;
const state = {
  tool: 'select',
  snapSize: 10,
  zoom: 1,
  panX: 0, panY: 0,
  sketchOpacity: 0.4,
  sketchImage: null,
  sketchSrc: null,
  mapName: 'Untitled',
  mapSeason: 'forest',
  mapLevel: 1,
  mapTimeLimit: 60,
  obstacles: [],       // {id, x, y, w, h, color}
  assets: [],          // {id, src, x, y, w, h, rotation, origW, origH, name}
  finishY: 40,
  finishX1: 0,
  finishX2: GAME_W,
  spawnX: GAME_W / 2,
  spawnY: GAME_H - 50,
  selected: null,      // {type:'obstacle'|'asset'|'finish'|'spawn', id}
  dragging: false,
  dragStart: null,
  dragOffset: null,
  resizing: false,
  resizeHandle: null,
  drawingRect: null,
  nextId: 1,
  assetImages: {},     // cache: src -> Image
  selectedAssetSrc: null,
};

const canvas = document.getElementById('mainCanvas');
const ctx = canvas.getContext('2d');

// ===== ASSET CATALOG =====
let assetCatalog = {};
let sketchCatalog = {};

async function loadCatalogs() {
  const res = await fetch('/api/catalog');
  const data = await res.json();
  assetCatalog = data.assets;
  sketchCatalog = data.sketches;
  state.savedMaps = data.saved_maps;
  buildAssetPanel();
  buildSketchPanel();
}

function buildAssetPanel() {
  const panel = document.getElementById('assetPanel');
  let html = '';
  // Sort categories
  const cats = Object.keys(assetCatalog).sort();
  for (const cat of cats) {
    const files = assetCatalog[cat];
    const catName = cat.replace(/images[\\/\\\\]?/, '').replace(/[\\/\\\\]/g, ' › ') || 'root';
    html += '<div class="asset-category">';
    html += '<div class="asset-category-title">' + catName + ' (' + files.length + ')</div>';
    html += '<div class="asset-grid">';
    for (const f of files) {
      const name = f.split('/').pop().replace(/Pixel_art_|_202603281320/g, '').replace(/\\.\\w+$/, '');
      html += '<div class="asset-thumb" data-src="' + f + '" onclick="selectAssetForPlacement(this)" title="' + name + '">';
      html += '<img src="/file/' + encodeURIComponent(f) + '" loading="lazy">';
      html += '<div class="label">' + name + '</div>';
      html += '</div>';
    }
    html += '</div></div>';
  }
  panel.innerHTML = html;
}

function buildSketchPanel() {
  const panel = document.getElementById('sketchPanel');
  let html = '';
  const cats = Object.keys(sketchCatalog).sort();
  for (const cat of cats) {
    html += '<div style="padding:2px 6px;font-size:10px;color:#7a8;text-transform:uppercase;margin-top:4px;">' + cat + '</div>';
    for (const f of sketchCatalog[cat]) {
      const name = f.split('/').pop().replace('Screenshot ', '').replace('.png', '');
      html += '<div class="sketch-item" data-src="' + f + '" onclick="loadSketch(this)">';
      html += '<img class="sketch-thumb" src="/file/' + encodeURIComponent(f) + '" loading="lazy">';
      html += '<span style="font-size:11px;">' + cat + ' — ' + name + '</span>';
      html += '</div>';
    }
  }
  panel.innerHTML = html;
}

function loadSketch(el) {
  document.querySelectorAll('.sketch-item').forEach(e => e.classList.remove('active'));
  el.classList.add('active');
  const src = el.dataset.src;
  state.sketchSrc = src;
  const img = new Image();
  img.onload = () => { state.sketchImage = img; render(); };
  img.src = '/file/' + encodeURIComponent(src);
}

function selectAssetForPlacement(el) {
  document.querySelectorAll('.asset-thumb').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  state.selectedAssetSrc = el.dataset.src;
  setTool('select');
  canvas.style.cursor = 'copy';
  // Load image if not cached
  if (!state.assetImages[el.dataset.src]) {
    const img = new Image();
    img.onload = () => { state.assetImages[el.dataset.src] = img; };
    img.src = '/file/' + encodeURIComponent(el.dataset.src);
  }
}

// ===== TOOLS =====
function setTool(t) {
  state.tool = t;
  state.selected = null;
  if (t !== 'select' || !state.selectedAssetSrc) {
    state.selectedAssetSrc = null;
    document.querySelectorAll('.asset-thumb').forEach(e => e.classList.remove('selected'));
  }
  document.querySelectorAll('.toolbar button').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('tool' + t.charAt(0).toUpperCase() + t.slice(1));
  if (btn) btn.classList.add('active');
  canvas.style.cursor = t === 'rect' ? 'crosshair' : t === 'finish' ? 'row-resize' : t === 'spawn' ? 'cell' : 'default';
  document.getElementById('statusTool').textContent = 'Tool: ' + t.charAt(0).toUpperCase() + t.slice(1);
  updatePropertiesPanel();
  render();
}

function snap(v) {
  if (state.snapSize <= 1) return v;
  return Math.round(v / state.snapSize) * state.snapSize;
}

// ===== CANVAS MOUSE =====
function canvasCoords(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = GAME_W / rect.width;
  const scaleY = GAME_H / rect.height;
  return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY };
}

canvas.addEventListener('mousedown', (e) => {
  const pos = canvasCoords(e);
  const sx = snap(pos.x), sy = snap(pos.y);

  // Place asset if one is selected from panel
  if (state.selectedAssetSrc && state.tool === 'select') {
    placeAsset(sx, sy);
    return;
  }

  if (state.tool === 'rect') {
    state.drawingRect = { x: sx, y: sy, w: 0, h: 0 };
    return;
  }

  if (state.tool === 'finish') {
    state.finishY = snap(pos.y);
    render();
    return;
  }

  if (state.tool === 'spawn') {
    state.spawnX = snap(pos.x);
    state.spawnY = snap(pos.y);
    render();
    return;
  }

  if (state.tool === 'select') {
    // Check if clicking on resize handle of selected item
    const handle = getResizeHandle(pos);
    if (handle) {
      state.resizing = true;
      state.resizeHandle = handle;
      state.dragStart = pos;
      return;
    }

    // Check if clicking on an asset (top-down to get topmost)
    for (let i = state.assets.length - 1; i >= 0; i--) {
      const a = state.assets[i];
      if (pos.x >= a.x && pos.x <= a.x + a.w && pos.y >= a.y && pos.y <= a.y + a.h) {
        state.selected = { type: 'asset', id: a.id };
        state.dragging = true;
        state.dragOffset = { x: pos.x - a.x, y: pos.y - a.y };
        updatePropertiesPanel();
        updateItemsList();
        render();
        return;
      }
    }

    // Check obstacles
    for (let i = state.obstacles.length - 1; i >= 0; i--) {
      const o = state.obstacles[i];
      if (pos.x >= o.x && pos.x <= o.x + o.w && pos.y >= o.y && pos.y <= o.y + o.h) {
        state.selected = { type: 'obstacle', id: o.id };
        state.dragging = true;
        state.dragOffset = { x: pos.x - o.x, y: pos.y - o.y };
        updatePropertiesPanel();
        updateItemsList();
        render();
        return;
      }
    }

    // Deselect
    state.selected = null;
    updatePropertiesPanel();
    updateItemsList();
    render();
  }
});

canvas.addEventListener('mousemove', (e) => {
  const pos = canvasCoords(e);
  document.getElementById('statusCoords').textContent = 'X: ' + Math.round(pos.x) + '  Y: ' + Math.round(pos.y);

  if (state.drawingRect) {
    const sx = snap(pos.x), sy = snap(pos.y);
    state.drawingRect.w = sx - state.drawingRect.x;
    state.drawingRect.h = sy - state.drawingRect.y;
    render();
    return;
  }

  if (state.resizing && state.selected) {
    const item = getSelectedItem();
    if (!item) return;
    const dx = snap(pos.x) - snap(state.dragStart.x);
    const dy = snap(pos.y) - snap(state.dragStart.y);
    const h = state.resizeHandle;
    if (h.includes('e')) item.w = Math.max(10, item._origW + dx);
    if (h.includes('s')) item.h = Math.max(10, item._origH + dy);
    if (h.includes('w')) { item.x = item._origX + dx; item.w = Math.max(10, item._origW - dx); }
    if (h.includes('n')) { item.y = item._origY + dy; item.h = Math.max(10, item._origH - dy); }
    render();
    updatePropertiesPanel();
    return;
  }

  if (state.dragging && state.selected) {
    const item = getSelectedItem();
    if (item) {
      item.x = snap(pos.x - state.dragOffset.x);
      item.y = snap(pos.y - state.dragOffset.y);
      render();
      updatePropertiesPanel();
    }
    return;
  }

  // Update cursor for resize handles
  if (state.tool === 'select' && state.selected) {
    const handle = getResizeHandle(pos);
    if (handle) {
      const cursors = { 'nw': 'nw-resize', 'ne': 'ne-resize', 'sw': 'sw-resize', 'se': 'se-resize',
                        'n': 'n-resize', 's': 's-resize', 'w': 'w-resize', 'e': 'e-resize' };
      canvas.style.cursor = cursors[handle] || 'default';
    } else {
      canvas.style.cursor = state.selectedAssetSrc ? 'copy' : 'default';
    }
  }
});

canvas.addEventListener('mouseup', (e) => {
  if (state.drawingRect) {
    let { x, y, w, h } = state.drawingRect;
    // Normalize negative dimensions
    if (w < 0) { x += w; w = -w; }
    if (h < 0) { y += h; h = -h; }
    if (w >= 10 && h >= 10) {
      state.obstacles.push({
        id: state.nextId++,
        x, y, w: Math.round(w), h: Math.round(h),
        color: getSeasonColor(state.mapSeason)
      });
      state.selected = { type: 'obstacle', id: state.obstacles[state.obstacles.length - 1].id };
      updateItemsList();
      updatePropertiesPanel();
    }
    state.drawingRect = null;
    render();
    return;
  }

  if (state.resizing) {
    const item = getSelectedItem();
    if (item) { delete item._origW; delete item._origH; delete item._origX; delete item._origY; }
    state.resizing = false;
    state.resizeHandle = null;
  }

  state.dragging = false;
  state.dragOffset = null;
});

// ===== HELPERS =====
function getSelectedItem() {
  if (!state.selected) return null;
  const list = state.selected.type === 'obstacle' ? state.obstacles : state.assets;
  return list.find(i => i.id === state.selected.id);
}

function getResizeHandle(pos) {
  const item = getSelectedItem();
  if (!item) return null;
  const hs = 8; // handle size in game coords
  const { x, y, w, h } = item;
  // Store originals for resize
  if (!item._origW) { item._origW = w; item._origH = h; item._origX = x; item._origY = y; }

  const handles = {
    'nw': [x, y], 'n': [x + w/2, y], 'ne': [x + w, y],
    'w': [x, y + h/2], 'e': [x + w, y + h/2],
    'sw': [x, y + h], 's': [x + w/2, y + h], 'se': [x + w, y + h]
  };
  for (const [name, [hx, hy]] of Object.entries(handles)) {
    if (Math.abs(pos.x - hx) < hs && Math.abs(pos.y - hy) < hs) return name;
  }
  return null;
}

function getSeasonColor(season) {
  const colors = { forest: '#2d5a1e', snow: '#8899aa', desert: '#c4a35a', tropics: '#1a7a5a' };
  return colors[season] || '#555';
}

function placeAsset(x, y) {
  const src = state.selectedAssetSrc;
  const img = state.assetImages[src];
  if (!img) return;
  // Auto-crop logic: place at reasonable size
  const scale = Math.min(150 / img.naturalWidth, 150 / img.naturalHeight, 0.3);
  const w = Math.round(img.naturalWidth * scale);
  const h = Math.round(img.naturalHeight * scale);
  state.assets.push({
    id: state.nextId++,
    src: src,
    x: snap(x - w/2), y: snap(y - h/2),
    w, h,
    rotation: 0,
    origW: img.naturalWidth,
    origH: img.naturalHeight,
    name: src.split('/').pop().replace(/Pixel_art_|_202603281320/g, '').replace(/\\.\\w+$/, '')
  });
  state.selected = { type: 'asset', id: state.assets[state.assets.length - 1].id };
  // Don't deselect the asset from panel — allow placing multiple
  updateItemsList();
  updatePropertiesPanel();
  render();
}

function deleteSelected() {
  if (!state.selected) return;
  if (state.selected.type === 'obstacle') {
    state.obstacles = state.obstacles.filter(o => o.id !== state.selected.id);
  } else if (state.selected.type === 'asset') {
    state.assets = state.assets.filter(a => a.id !== state.selected.id);
  }
  state.selected = null;
  updateItemsList();
  updatePropertiesPanel();
  render();
}

function duplicateSelected() {
  const item = getSelectedItem();
  if (!item) return;
  const clone = { ...item, id: state.nextId++ };
  clone.x += 20;
  clone.y += 20;
  if (state.selected.type === 'obstacle') state.obstacles.push(clone);
  else state.assets.push(clone);
  state.selected = { type: state.selected.type, id: clone.id };
  updateItemsList();
  render();
}

// ===== RENDERING =====
function render() {
  ctx.clearRect(0, 0, GAME_W, GAME_H);

  // Water background
  ctx.fillStyle = '#1a6fc4';
  ctx.fillRect(0, 0, GAME_W, GAME_H);

  // Sketch reference
  if (state.sketchImage) {
    ctx.globalAlpha = state.sketchOpacity;
    ctx.drawImage(state.sketchImage, 0, 0, GAME_W, GAME_H);
    ctx.globalAlpha = 1;
  }

  // Grid (subtle)
  if (state.snapSize >= 25) {
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x < GAME_W; x += state.snapSize) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, GAME_H); ctx.stroke();
    }
    for (let y = 0; y < GAME_H; y += state.snapSize) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(GAME_W, y); ctx.stroke();
    }
  }

  // Obstacles
  for (const o of state.obstacles) {
    ctx.fillStyle = o.color || getSeasonColor(state.mapSeason);
    ctx.globalAlpha = 0.7;
    ctx.fillRect(o.x, o.y, o.w, o.h);
    ctx.globalAlpha = 1;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.strokeRect(o.x, o.y, o.w, o.h);
    // Label
    ctx.fillStyle = '#fff';
    ctx.font = '10px monospace';
    ctx.fillText(Math.round(o.w) + '×' + Math.round(o.h), o.x + 4, o.y + 14);
  }

  // Drawing rect preview
  if (state.drawingRect) {
    let { x, y, w, h } = state.drawingRect;
    ctx.fillStyle = getSeasonColor(state.mapSeason);
    ctx.globalAlpha = 0.5;
    ctx.fillRect(x, y, w, h);
    ctx.globalAlpha = 1;
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.strokeRect(x, y, w, h);
    ctx.setLineDash([]);
    // Show dimensions
    ctx.fillStyle = '#ff0';
    ctx.font = '12px monospace';
    ctx.fillText(Math.abs(Math.round(w)) + '×' + Math.abs(Math.round(h)), x + 4, y - 4);
  }

  // Assets
  for (const a of state.assets) {
    const img = state.assetImages[a.src];
    if (img) {
      ctx.save();
      if (a.rotation) {
        ctx.translate(a.x + a.w/2, a.y + a.h/2);
        ctx.rotate(a.rotation * Math.PI / 180);
        ctx.drawImage(img, -a.w/2, -a.h/2, a.w, a.h);
      } else {
        ctx.drawImage(img, a.x, a.y, a.w, a.h);
      }
      ctx.restore();
    } else {
      // Placeholder
      ctx.fillStyle = '#ff69b4';
      ctx.globalAlpha = 0.3;
      ctx.fillRect(a.x, a.y, a.w, a.h);
      ctx.globalAlpha = 1;
      // Load it
      const newImg = new Image();
      newImg.onload = () => { state.assetImages[a.src] = newImg; render(); };
      newImg.src = '/file/' + encodeURIComponent(a.src);
    }
  }

  // Finish line
  ctx.strokeStyle = '#0f0';
  ctx.lineWidth = 3;
  ctx.setLineDash([8, 6]);
  ctx.beginPath();
  ctx.moveTo(state.finishX1, state.finishY);
  ctx.lineTo(state.finishX2, state.finishY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#0f0';
  ctx.font = '11px monospace';
  ctx.fillText('FINISH (Y=' + Math.round(state.finishY) + ')', state.finishX1 + 10, state.finishY - 6);

  // Spawn point
  ctx.fillStyle = '#ff0';
  ctx.beginPath();
  ctx.arc(state.spawnX, state.spawnY, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#000';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = '#000';
  ctx.font = 'bold 10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('S', state.spawnX, state.spawnY + 4);
  ctx.textAlign = 'left';

  // Selection highlight
  if (state.selected) {
    const item = getSelectedItem();
    if (item) {
      ctx.strokeStyle = '#e94560';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.strokeRect(item.x - 2, item.y - 2, item.w + 4, item.h + 4);
      ctx.setLineDash([]);
      // Resize handles
      drawResizeHandles(item);
    }
  }

  // Update status
  document.getElementById('statusItems').textContent =
    'Obstacles: ' + state.obstacles.length + ' | Assets: ' + state.assets.length;
}

function drawResizeHandles(item) {
  const hs = 5;
  const { x, y, w, h } = item;
  const handles = [
    [x, y], [x + w/2, y], [x + w, y],
    [x, y + h/2], [x + w, y + h/2],
    [x, y + h], [x + w/2, y + h], [x + w, y + h]
  ];
  for (const [hx, hy] of handles) {
    ctx.fillStyle = '#fff';
    ctx.fillRect(hx - hs, hy - hs, hs * 2, hs * 2);
    ctx.strokeStyle = '#e94560';
    ctx.lineWidth = 1;
    ctx.strokeRect(hx - hs, hy - hs, hs * 2, hs * 2);
  }
}

// ===== PROPERTIES PANEL =====
function updatePropertiesPanel() {
  const panel = document.getElementById('propPanel');
  const item = getSelectedItem();
  if (!item) {
    panel.innerHTML = '<p style="color:#667;font-size:11px;padding:20px 0;text-align:center;">Select an item to edit properties</p>';
    return;
  }
  const isObs = state.selected.type === 'obstacle';
  let html = '<div class="prop-row"><div><label>X</label><input type="number" value="' + Math.round(item.x) + '" onchange="setProp(\'x\',+this.value)"></div>';
  html += '<div><label>Y</label><input type="number" value="' + Math.round(item.y) + '" onchange="setProp(\'y\',+this.value)"></div></div>';
  html += '<div class="prop-row"><div><label>Width</label><input type="number" value="' + Math.round(item.w) + '" onchange="setProp(\'w\',+this.value)"></div>';
  html += '<div><label>Height</label><input type="number" value="' + Math.round(item.h) + '" onchange="setProp(\'h\',+this.value)"></div></div>';
  if (!isObs) {
    html += '<label>Rotation (°)</label><input type="number" value="' + (item.rotation || 0) + '" onchange="setProp(\'rotation\',+this.value)">';
    html += '<label>Asset</label><input type="text" value="' + (item.name || '') + '" readonly style="opacity:0.6">';
    // Aspect ratio lock checkbox
    html += '<label><input type="checkbox" id="lockAspect" checked> Lock aspect ratio</label>';
  }
  if (isObs) {
    html += '<label>Color</label><input type="color" value="' + (item.color || getSeasonColor(state.mapSeason)) + '" onchange="setProp(\'color\',this.value)">';
  }
  panel.innerHTML = html;
}

function setProp(key, val) {
  const item = getSelectedItem();
  if (!item) return;
  // Aspect ratio for assets
  if ((key === 'w' || key === 'h') && state.selected.type === 'asset') {
    const lockEl = document.getElementById('lockAspect');
    if (lockEl && lockEl.checked && item.origW && item.origH) {
      const ratio = item.origW / item.origH;
      if (key === 'w') { item.w = val; item.h = Math.round(val / ratio); }
      else { item.h = val; item.w = Math.round(val * ratio); }
      updatePropertiesPanel();
      render();
      return;
    }
  }
  item[key] = val;
  render();
  updatePropertiesPanel();
}

// ===== ITEMS LIST =====
function updateItemsList() {
  const list = document.getElementById('itemsList');
  let html = '';
  // Obstacles
  for (const o of state.obstacles) {
    const sel = state.selected?.type === 'obstacle' && state.selected.id === o.id;
    html += '<div class="item-entry' + (sel ? ' selected' : '') + '" onclick="selectItem(\'obstacle\',' + o.id + ')">';
    html += '<span>▭ Obstacle (' + Math.round(o.w) + '×' + Math.round(o.h) + ')</span>';
    html += '<span class="delete-btn" onclick="event.stopPropagation();deleteItem(\'obstacle\',' + o.id + ')">✕</span>';
    html += '</div>';
  }
  // Assets
  for (const a of state.assets) {
    const sel = state.selected?.type === 'asset' && state.selected.id === a.id;
    html += '<div class="item-entry' + (sel ? ' selected' : '') + '" onclick="selectItem(\'asset\',' + a.id + ')">';
    html += '<span>🖼 ' + (a.name || 'Asset') + '</span>';
    html += '<span class="delete-btn" onclick="event.stopPropagation();deleteItem(\'asset\',' + a.id + ')">✕</span>';
    html += '</div>';
  }
  list.innerHTML = html || '<p style="color:#556;font-size:11px;padding:20px;text-align:center;">No items yet. Draw obstacles or place assets.</p>';
  document.getElementById('itemCount').textContent = state.obstacles.length + state.assets.length;
}

function selectItem(type, id) {
  state.selected = { type, id };
  updatePropertiesPanel();
  updateItemsList();
  render();
}

function deleteItem(type, id) {
  if (type === 'obstacle') state.obstacles = state.obstacles.filter(o => o.id !== id);
  else state.assets = state.assets.filter(a => a.id !== id);
  if (state.selected?.id === id) state.selected = null;
  updateItemsList();
  updatePropertiesPanel();
  render();
}

// ===== SAVE / LOAD =====
function showSaveModal() {
  const name = state.mapSeason + '_' + state.mapLevel + '_' + state.mapName.toLowerCase().replace(/[^a-z0-9]+/g, '_');
  document.getElementById('saveFilename').value = name;
  document.getElementById('saveModal').style.display = 'flex';
}

function closeSaveModal() {
  document.getElementById('saveModal').style.display = 'none';
}

async function saveMap() {
  const filename = document.getElementById('saveFilename').value.trim();
  if (!filename) return;
  const data = {
    name: state.mapName,
    season: state.mapSeason,
    level: state.mapLevel,
    time_limit: state.mapTimeLimit,
    finish_y: state.finishY,
    finish_x1: state.finishX1,
    finish_x2: state.finishX2,
    spawn_x: state.spawnX,
    spawn_y: state.spawnY,
    obstacles: state.obstacles.map(o => ({
      x: Math.round(o.x), y: Math.round(o.y),
      w: Math.round(o.w), h: Math.round(o.h)
    })),
    assets: state.assets.map(a => ({
      src: a.src,
      x: Math.round(a.x), y: Math.round(a.y),
      w: Math.round(a.w), h: Math.round(a.h),
      rotation: a.rotation || 0,
      name: a.name || ''
    }))
  };
  const res = await fetch('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: filename + '.json', data })
  });
  const result = await res.json();
  if (result.ok) {
    document.getElementById('statusMap').textContent = 'Saved: ' + filename;
    closeSaveModal();
  }
}

async function showLoadModal() {
  const res = await fetch('/api/catalog');
  const data = await res.json();
  const sel = document.getElementById('loadSelect');
  sel.innerHTML = '';
  for (const f of data.saved_maps) {
    sel.innerHTML += '<option value="' + f + '">' + f + '</option>';
  }
  document.getElementById('loadModal').style.display = 'flex';
}

function closeLoadModal() {
  document.getElementById('loadModal').style.display = 'none';
}

async function loadMap() {
  const sel = document.getElementById('loadSelect');
  const filename = sel.value;
  if (!filename) return;
  const res = await fetch('/api/load?file=' + encodeURIComponent(filename));
  const data = await res.json();
  if (data.error) { alert(data.error); return; }

  state.mapName = data.name || 'Untitled';
  state.mapSeason = data.season || 'forest';
  state.mapLevel = data.level || 1;
  state.mapTimeLimit = data.time_limit || 60;
  state.finishY = data.finish_y || 40;
  state.finishX1 = data.finish_x1 || 0;
  state.finishX2 = data.finish_x2 || GAME_W;
  state.spawnX = data.spawn_x || GAME_W / 2;
  state.spawnY = data.spawn_y || GAME_H - 50;

  state.obstacles = (data.obstacles || []).map(o => ({
    ...o, id: state.nextId++, color: getSeasonColor(state.mapSeason)
  }));
  state.assets = (data.assets || []).map(a => ({
    ...a, id: state.nextId++
  }));

  // Preload asset images
  for (const a of state.assets) {
    if (!state.assetImages[a.src]) {
      const img = new Image();
      img.onload = () => { state.assetImages[a.src] = img; render(); };
      img.src = '/file/' + encodeURIComponent(a.src);
    }
  }

  // Update UI
  document.getElementById('mapName').value = state.mapName;
  document.getElementById('mapSeason').value = state.mapSeason;
  document.getElementById('mapLevel').value = state.mapLevel;
  document.getElementById('mapTime').value = state.mapTimeLimit;
  document.getElementById('statusMap').textContent = 'Loaded: ' + filename;

  closeLoadModal();
  state.selected = null;
  updateItemsList();
  updatePropertiesPanel();
  render();
}

function exportMapsPy() {
  // Generate maps.py compatible dict
  const lines = [];
  lines.push('{');
  lines.push('    "name": "' + state.mapName + '",');
  lines.push('    "theme": "' + state.mapSeason + '",');
  lines.push('    "level": ' + state.mapLevel + ',');
  lines.push('    "season": "' + state.mapSeason + '",');
  lines.push('    "time_limit": ' + state.mapTimeLimit + ',');
  lines.push('    "finish_y": ' + Math.round(state.finishY) + ',');
  lines.push('    "finish_x1": ' + Math.round(state.finishX1) + ',');
  lines.push('    "finish_x2": ' + Math.round(state.finishX2) + ',');
  lines.push('    "obstacles": [');
  for (let i = 0; i < state.obstacles.length; i++) {
    const o = state.obstacles[i];
    const comma = i < state.obstacles.length - 1 ? ',' : '';
    lines.push('        (' + Math.round(o.x) + ', ' + Math.round(o.y) + ', ' + Math.round(o.w) + ', ' + Math.round(o.h) + ')' + comma);
  }
  lines.push('    ],');
  lines.push('    "assets": [');
  for (let i = 0; i < state.assets.length; i++) {
    const a = state.assets[i];
    const comma = i < state.assets.length - 1 ? ',' : '';
    lines.push('        {"src": "' + a.src + '", "x": ' + Math.round(a.x) + ', "y": ' + Math.round(a.y) + ', "w": ' + Math.round(a.w) + ', "h": ' + Math.round(a.h) + ', "rotation": ' + (a.rotation || 0) + '}' + comma);
  }
  lines.push('    ]');
  lines.push('}');

  const text = lines.join('\\n');
  navigator.clipboard.writeText(text).then(() => {
    document.getElementById('statusMap').textContent = 'Exported to clipboard!';
  });
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

  switch(e.key.toLowerCase()) {
    case 'v': setTool('select'); break;
    case 'r': setTool('rect'); break;
    case 'f': setTool('finish'); break;
    case 'delete': case 'backspace': deleteSelected(); break;
    case 'escape':
      state.selectedAssetSrc = null;
      document.querySelectorAll('.asset-thumb').forEach(e => e.classList.remove('selected'));
      canvas.style.cursor = 'default';
      state.selected = null;
      updatePropertiesPanel();
      updateItemsList();
      render();
      break;
    case 'd':
      if (e.ctrlKey || e.metaKey) { e.preventDefault(); duplicateSelected(); }
      break;
    case 's':
      if (e.ctrlKey || e.metaKey) { e.preventDefault(); showSaveModal(); }
      break;
    case 'o':
      if (e.ctrlKey || e.metaKey) { e.preventDefault(); showLoadModal(); }
      break;
    case '[':
      // Send selected backward
      if (state.selected?.type === 'asset') {
        const idx = state.assets.findIndex(a => a.id === state.selected.id);
        if (idx > 0) { [state.assets[idx-1], state.assets[idx]] = [state.assets[idx], state.assets[idx-1]]; render(); updateItemsList(); }
      }
      break;
    case ']':
      // Bring selected forward
      if (state.selected?.type === 'asset') {
        const idx = state.assets.findIndex(a => a.id === state.selected.id);
        if (idx < state.assets.length - 1) { [state.assets[idx], state.assets[idx+1]] = [state.assets[idx+1], state.assets[idx]]; render(); updateItemsList(); }
      }
      break;
  }
});

// ===== SECTION TOGGLE =====
function toggleSection(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'none' ? '' : 'none';
}

// ===== ZOOM =====
function setZoom(z) {
  state.zoom = z;
  canvas.style.width = (GAME_W * z) + 'px';
  canvas.style.height = (GAME_H * z) + 'px';
}

// ===== INIT =====
loadCatalogs().then(() => {
  render();
  updateItemsList();
});

</script>
</body>
</html>"""


class EditorHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress request logs

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())

        elif path == '/api/catalog':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = {
                'assets': get_asset_catalog(),
                'sketches': get_sketch_catalog(),
                'saved_maps': get_saved_maps()
            }
            self.wfile.write(json.dumps(data).encode())

        elif path.startswith('/api/load'):
            qs = urllib.parse.parse_qs(parsed.query)
            filename = qs.get('file', [None])[0]
            if filename:
                filepath = os.path.join(MAPS_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath) as f:
                        data = json.load(f)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode())
                    return
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

        elif path.startswith('/file/'):
            # Serve project files (assets, sketches)
            rel_path = urllib.parse.unquote(path[6:])
            full_path = os.path.join(PROJECT_DIR, rel_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                ext = os.path.splitext(full_path)[1].lower()
                mime = {
                    '.png': 'image/png', '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', '.gif': 'image/gif'
                }.get(ext, 'application/octet-stream')
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/save':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            filename = body.get('filename', 'untitled.json')
            # Sanitize filename
            filename = os.path.basename(filename)
            if not filename.endswith('.json'):
                filename += '.json'
            filepath = os.path.join(MAPS_DIR, filename)
            with open(filepath, 'w') as f:
                json.dump(body['data'], f, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'file': filename}).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), EditorHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"\\n╔══════════════════════════════════════════╗")
        print(f"║   CrossRiver Map Editor                   ║")
        print(f"║   Open: http://localhost:{PORT}             ║")
        print(f"║   Press Ctrl+C to stop                    ║")
        print(f"╚══════════════════════════════════════════╝\\n")
        print(f"Project dir: {PROJECT_DIR}")
        print(f"Assets: {len([f for c in get_asset_catalog().values() for f in c])} files")
        print(f"Sketches: {len([f for c in get_sketch_catalog().values() for f in c])} files")
        print(f"Saved maps: {len(get_saved_maps())} files\\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nEditor stopped.")
