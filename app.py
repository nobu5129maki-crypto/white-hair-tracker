import os
import io
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

app = Flask(__name__, static_folder='static', template_folder='templates')

def _generate_icon_png():
    """512x512のアプリアイコンを生成（スプラッシュ・アイコン用）"""
    size = 512
    img = np.full((size, size, 3), (30, 30, 30), dtype=np.uint8)
    pts = np.array([[100, 350], [150, 280], [256, 320], [362, 220], [412, 180]], np.int32)
    cv2.polylines(img, [pts], False, (197, 209, 79), 24)
    cv2.circle(img, (100, 350), 12, (197, 209, 79), -1)
    cv2.circle(img, (412, 180), 12, (197, 209, 79), -1)
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

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
    """PWAアイコン用の512x512 PNGを返す"""
    return send_file(
        io.BytesIO(_generate_icon_png()),
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