import os
import io
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, send_file

app = Flask(__name__, static_folder='static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _create_icon_png():
    """アイコンをOpenCVで生成（髪＋グラフのデザイン）"""
    def bezier(p0, p1, p2, n=30):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
            y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
            pts.append([int(x), int(y)])
        return np.array(pts, np.int32)
    img = np.full((512, 512, 3), (30, 30, 30), dtype=np.uint8)
    pts1 = bezier((150, 350), (150, 150), (200, 150))
    pts2 = bezier((200, 150), (250, 150), (250, 350))
    cv2.polylines(img, [pts1, pts2], False, (255, 255, 255), 15)
    pts3 = bezier((260, 350), (260, 180), (310, 180))
    pts4 = bezier((310, 180), (360, 180), (360, 350))
    cv2.polylines(img, [pts3, pts4], False, (204, 204, 204), 15)
    pts5 = np.array([[120, 400], [180, 320], [250, 360], [320, 280], [400, 220]], np.int32)
    cv2.polylines(img, [pts5], False, (197, 209, 79), 12)
    for c in [(120, 400), (180, 320), (250, 360), (320, 280), (400, 220)]:
        cv2.circle(img, c, 10, (197, 209, 79), -1)
    _, buf = cv2.imencode('.png', img)
    return buf.tobytes()

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/icon-512.png')
def icon_png():
    """PWAアイコン"""
    root_icon = os.path.join(BASE_DIR, 'icon-512.png')
    if os.path.exists(root_icon):
        return send_from_directory(BASE_DIR, 'icon-512.png')
    png_data = _create_icon_png()
    return send_file(io.BytesIO(png_data), mimetype='image/png', max_age=86400)

@app.route('/splash.png')
def splash_png():
    """スプラッシュ画像"""
    return icon_png()

# ★ここが重要！判定処理の受け皿を作ります
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '画像がありません'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '画像が選択されていません'}), 400
        
        data = file.read()
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            # HEIC（iPhone）対応
            try:
                import pillow_heif
                from PIL import Image
                pillow_heif.register_heif_opener()
                pil_img = Image.open(io.BytesIO(data))
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                nparr = np.array(pil_img)
                img = cv2.cvtColor(nparr, cv2.COLOR_RGB2BGR)
            except Exception:
                pass

        if img is None:
            return jsonify({'error': '画像を読み込めません。JPEGまたはPNG形式で撮影してください'}), 400

        img = cv2.resize(img, (640, 480))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, white_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        white_pixels = cv2.countNonZero(white_mask)
        total_pixels = img.shape[0] * img.shape[1]
        ratio = round((white_pixels / total_pixels) * 100, 1)

        return jsonify({'ratio': ratio})
    except Exception as e:
        return jsonify({'error': f'処理中にエラーが発生しました: {str(e)}'}), 500

@app.route('/manifest.json')
def manifest():
    return send_from_directory(BASE_DIR, 'manifest.json')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
