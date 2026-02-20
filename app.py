import os
import io
import tempfile
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

app = Flask(__name__, static_folder='static', template_folder='templates')

# アイコンPNGのキャッシュ（icon.svgから変換したデザイン）
_icon_png_cache = None

def _bezier_quad(p0, p1, p2, n=20):
    """2次ベジェ曲線の点列を生成"""
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        pts.append([int(x), int(y)])
    return np.array(pts, np.int32)

def _get_icon_png():
    """icon.svgのデザインを再現した512x512 PNGを取得"""
    global _icon_png_cache
    if _icon_png_cache is not None:
        return _icon_png_cache

    # 1. 静的ファイルが既に存在する場合はそれを使用
    static_icon = os.path.join(app.static_folder, 'icon-512.png')
    if os.path.exists(static_icon):
        with open(static_icon, 'rb') as f:
            _icon_png_cache = f.read()
        return _icon_png_cache

    # 2. icon.svgから変換を試行（svglib + reportlab）
    svg_path = os.path.join(app.static_folder, 'icon.svg')
    if os.path.exists(svg_path):
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            drawing = svg2rlg(svg_path)
            if drawing:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    renderPM.drawToFile(drawing, tmp.name, fmt='PNG')
                    with open(tmp.name, 'rb') as f:
                        _icon_png_cache = f.read()
                    os.unlink(tmp.name)
                return _icon_png_cache
        except Exception:
            pass

    # 3. OpenCVでicon.svgのデザインを再現
    size = 512
    img = np.full((size, size, 3), (30, 30, 30), dtype=np.uint8)  # #1e1e1e
    # 髪の毛（白）: M150 350 Q150 150 200 150 T250 350
    pts1 = _bezier_quad((150, 350), (150, 150), (200, 150))
    pts2 = _bezier_quad((200, 150), (250, 150), (250, 350))
    cv2.polylines(img, [pts1, pts2], False, (255, 255, 255), 15)
    # 髪の毛（グレー）: M260 350 Q260 180 310 180 T360 350
    pts3 = _bezier_quad((260, 350), (260, 180), (310, 180))
    pts4 = _bezier_quad((310, 180), (360, 180), (360, 350))
    cv2.polylines(img, [pts3, pts4], False, (204, 204, 204), 15)  # #cccccc
    # グラフ線（ティール）: 120,400 180,320 250,360 320,280 400,220
    pts5 = np.array([[120, 400], [180, 320], [250, 360], [320, 280], [400, 220]], np.int32)
    cv2.polylines(img, [pts5], False, (197, 209, 79), 12)  # #4fd1c5
    for cx, cy in [(120, 400), (180, 320), (250, 360), (320, 280), (400, 220)]:
        cv2.circle(img, (cx, cy), 10, (197, 209, 79), -1)
    _, buffer = cv2.imencode('.png', img)
    _icon_png_cache = buffer.tobytes()
    return _icon_png_cache

def _generate_splash_png():
    """縦長スプラッシュ（390x844）アプリ起動画面風"""
    w, h = 390, 844
    img = np.full((h, w, 3), (18, 18, 18), dtype=np.uint8)  # #121212
    # 中央にカード風の矩形
    card = np.full((400, 340, 3), (30, 30, 30), dtype=np.uint8)
    y_offset = (h - 400) // 2
    x_offset = (w - 340) // 2
    img[y_offset:y_offset+400, x_offset:x_offset+340] = card
    # ティールのアクセント線
    pts = np.array([[x_offset+50, y_offset+320], [x_offset+120, y_offset+250],
                    [x_offset+170, y_offset+280], [x_offset+220, y_offset+200],
                    [x_offset+290, y_offset+150]], np.int32)
    cv2.polylines(img, [pts], False, (197, 209, 79), 8)
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/icon-512.png')
def icon_png():
    """PWAアイコン用の512x512 PNGを返す（icon.svgのデザイン）"""
    return send_file(
        io.BytesIO(_get_icon_png()),
        mimetype='image/png',
        max_age=86400
    )

@app.route('/splash.png')
def splash_png():
    """iOS用スプラッシュ画像（アプリ起動画面に近いデザイン）"""
    return send_file(
        io.BytesIO(_generate_splash_png()),
        mimetype='image/png',
        max_age=86400
    )

# ★ここが重要！判定処理の受け皿を作ります
@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': '画像がありません'}), 400
    
    file = request.files['image']
    nparr = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 【通信エラー対策】メモリ節約のため画像をリサイズ
    img = cv2.resize(img, (640, 480))

    # 簡単な白髪判定ロジック（例）
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, white_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    white_pixels = cv2.countNonZero(white_mask)
    total_pixels = img.shape[0] * img.shape[1]
    ratio = round((white_pixels / total_pixels) * 100, 1)

    return jsonify({'ratio': ratio})

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)