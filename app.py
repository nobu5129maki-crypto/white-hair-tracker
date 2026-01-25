from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np

app = Flask(__name__)

def analyze_gray_hair_advanced(img_array):
    # 画像の読み込み
    nparr = np.frombuffer(img_array, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: return 0

    # 1. 前処理：リサイズとノイズ除去
    img = cv2.resize(img, (600, 600))
    # 表面の細かなノイズを消しつつ、エッジ（髪の線）を残すフィルター
    denoised = cv2.bilateralFilter(img, 9, 75, 75)

    # 2. グレースケール（白黒）変換
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

    # 3. AI的アプローチ：適応型しきい値（明るさに合わせた自動調整）
    # 周囲の明るさに合わせて「白」を判定するため、影があっても正しく検出しやすくなります
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)

    # 4. 「毛髪」らしい細い線だけを残し、小さな点（ノイズ）を消す
    kernel = np.ones((2,2), np.uint8)
    refined = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # 5. 白髪ピクセルのカウント（反転させて白の部分を数える）
    # 背景が暗いことを想定し、高輝度な部分を抽出
    white_pixels = cv2.countNonZero(refined)
    total_pixels = 600 * 600
    
    # 計算結果の調整（感度調整）
    ratio = (white_pixels / total_pixels) * 100
    # あまりに低すぎる/高すぎる場合の補正
    final_ratio = round(min(max(ratio * 0.5, 0), 100), 2)
    
    return final_ratio

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image"}), 400
    
    file = request.files['image'].read()
    ratio = analyze_gray_hair_advanced(file)
    
    # 判定コメントの動的生成
    if ratio < 5:
        advice = "素晴らしい！白髪はほとんど見当たりません。"
    elif ratio < 15:
        advice = "少し目立ち始めています。頭皮マッサージが効果的です。"
    else:
        advice = "全体的に増えていますね。美容室でのケアを検討しましょう。"
    
    return jsonify({"ratio": ratio, "advice": advice})

if __name__ == '__main__':
    # 外部からのアクセスを許可
    app.run(debug=True, host='0.0.0.0', port=5000)

    # app.py に追加
import os
from flask import send_from_directory

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')