#!/usr/bin/env python3
"""
CrossRiver Map Editor Server
Run: python map_editor_server.py
Open: http://localhost:8099
"""

import http.server
import json
import os
import urllib.parse
import socketserver
import threading
import webbrowser
import base64
import re

import gzip as gzip_mod

PORT = 8099
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
THUMB_DIR = os.path.join(ASSETS_DIR, "thumbnails")
SKETCHES_DIR = os.path.join(PROJECT_DIR, "sketches")
MAPS_DIR = os.path.join(PROJECT_DIR, "saved_maps")

os.makedirs(MAPS_DIR, exist_ok=True)


def get_asset_catalog():
    catalog = {}
    if not os.path.exists(ASSETS_DIR):
        return catalog
    for root, dirs, files in os.walk(ASSETS_DIR):
        for f in sorted(files):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, PROJECT_DIR).replace("\\", "/")
                cat = os.path.relpath(root, ASSETS_DIR).replace("\\", "/")
                if cat == ".":
                    cat = "root"
                if cat not in catalog:
                    catalog[cat] = []
                catalog[cat].append(rel)
    return catalog


def get_sketch_catalog():
    catalog = {}
    if not os.path.exists(SKETCHES_DIR):
        return catalog
    for root, dirs, files in os.walk(SKETCHES_DIR):
        for f in sorted(files):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, PROJECT_DIR).replace("\\", "/")
                cat = os.path.relpath(root, SKETCHES_DIR).replace("\\", "/")
                if cat == ".":
                    cat = "root"
                if cat not in catalog:
                    catalog[cat] = []
                catalog[cat].append(rel)
    return catalog


def get_saved_maps():
    maps = []
    if os.path.exists(MAPS_DIR):
        for f in sorted(os.listdir(MAPS_DIR)):
            if f.endswith('.json'):
                maps.append(f)
    return maps


class EditorHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Show errors only
        if args and '404' in str(args):
            print(f"  404: {args[0]}")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == '/' or path == '/index.html':
                html_path = os.path.join(PROJECT_DIR, 'map_editor.html')
                if os.path.exists(html_path):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    with open(html_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'map_editor.html not found')

            elif path == '/api/catalog':
                data = {
                    'assets': get_asset_catalog(),
                    'sketches': get_sketch_catalog(),
                    'saved_maps': get_saved_maps()
                }
                self.send_json(data)

            elif path.startswith('/api/load'):
                qs = urllib.parse.parse_qs(parsed.query)
                filename = qs.get('file', [None])[0]
                if filename:
                    filepath = os.path.join(MAPS_DIR, os.path.basename(filename))
                    if os.path.exists(filepath):
                        with open(filepath) as f:
                            data = json.load(f)
                        self.send_json(data)
                        return
                self.send_json({'error': 'Not found'}, 404)

            elif path.startswith('/thumb/'):
                # Serve thumbnail version of asset
                rel_path = urllib.parse.unquote(path[7:])
                # Strip leading "assets/" or "assets/images/" to get relative to images dir
                rel_clean = rel_path
                if rel_clean.startswith('assets/images/'):
                    rel_clean = rel_clean[len('assets/images/'):]
                elif rel_clean.startswith('assets/'):
                    rel_clean = rel_clean[len('assets/'):]
                thumb_path = os.path.join(THUMB_DIR, rel_clean)
                thumb_path = os.path.normpath(thumb_path)
                if not thumb_path.startswith(os.path.normpath(THUMB_DIR)):
                    self.send_response(403)
                    self.end_headers()
                    return
                if os.path.exists(thumb_path) and os.path.isfile(thumb_path):
                    ext = os.path.splitext(thumb_path)[1].lower()
                    mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(ext, 'image/png')
                    self.send_response(200)
                    self.send_header('Content-Type', mime)
                    self.send_header('Cache-Control', 'max-age=86400')
                    self.end_headers()
                    with open(thumb_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    # Fallback to full image
                    full_path = os.path.join(PROJECT_DIR, rel_path)
                    full_path = os.path.normpath(full_path)
                    if full_path.startswith(PROJECT_DIR) and os.path.exists(full_path):
                        ext = os.path.splitext(full_path)[1].lower()
                        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(ext, 'image/png')
                        self.send_response(200)
                        self.send_header('Content-Type', mime)
                        self.send_header('Cache-Control', 'max-age=3600')
                        self.end_headers()
                        with open(full_path, 'rb') as f:
                            self.wfile.write(f.read())
                    else:
                        self.send_response(404)
                        self.end_headers()

            elif path.startswith('/file/'):
                rel_path = urllib.parse.unquote(path[6:])
                full_path = os.path.join(PROJECT_DIR, rel_path)
                full_path = os.path.normpath(full_path)
                # Security: ensure within project
                if not full_path.startswith(PROJECT_DIR):
                    self.send_response(403)
                    self.end_headers()
                    return
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    ext = os.path.splitext(full_path)[1].lower()
                    mime = {
                        '.png': 'image/png', '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg', '.gif': 'image/gif',
                        '.svg': 'image/svg+xml'
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
                    print(f"  File not found: {full_path}")

            else:
                self.send_response(404)
                self.end_headers()

        except Exception as e:
            print(f"  ERROR in GET {path}: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_POST(self):
        try:
            if self.path == '/api/save':
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                filename = os.path.basename(body.get('filename', 'untitled.json'))
                if not filename.endswith('.json'):
                    filename += '.json'
                filepath = os.path.join(MAPS_DIR, filename)
                with open(filepath, 'w') as f:
                    json.dump(body['data'], f, indent=2)
                print(f"  Saved: {filepath}")
                self.send_json({'ok': True, 'file': filename})

            elif self.path == '/api/upload-asset':
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                # Expected: {category: "imports/username", filename: "tree.png", data: "base64..."}
                category = body.get('category', 'imports').strip()
                filename = os.path.basename(body.get('filename', 'asset.png'))
                data_b64 = body.get('data', '')

                # Sanitize category (allow letters, numbers, underscores, hyphens, slashes)
                category = re.sub(r'[^a-zA-Z0-9_/\-]', '_', category)

                # Create target directory
                target_dir = os.path.join(ASSETS_DIR, "images", category)
                os.makedirs(target_dir, exist_ok=True)

                # Decode and save image
                img_data = base64.b64decode(data_b64)
                filepath = os.path.join(target_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(img_data)

                rel_path = os.path.relpath(filepath, PROJECT_DIR).replace("\\", "/")
                print(f"  Uploaded asset: {rel_path} ({len(img_data)} bytes)")
                self.send_json({'ok': True, 'path': rel_path})

            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"  ERROR in POST: {e}")
            self.send_json({'error': str(e)}, 500)


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == '__main__':
    assets = get_asset_catalog()
    sketches = get_sketch_catalog()
    total_assets = sum(len(v) for v in assets.values())
    total_sketches = sum(len(v) for v in sketches.values())

    print(f"\n{'='*46}")
    print(f"  CrossRiver Map Editor")
    print(f"  Open: http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*46}")
    print(f"  Project: {PROJECT_DIR}")
    print(f"  Assets:  {total_assets} files in {len(assets)} categories")
    print(f"  Sketches: {total_sketches} files")
    print(f"  Saved maps: {len(get_saved_maps())} files\n")

    with ReusableTCPServer(("", PORT), EditorHandler) as httpd:
        # Auto-open browser
        threading.Timer(0.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nEditor stopped.")
