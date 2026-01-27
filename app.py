import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

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