# 白髪トラッカー (White Hair Tracker)

AI画像解析を用いて、カメラで撮影した髪の毛から白髪率を算出・記録するWebアプリです。

## 特徴
- **画像解析**: OpenCVを使用した適応型しきい値処理による白髪検出。
- **履歴管理**: 解析結果をブラウザのLocalStorageに保存し、推移をグラフ表示。
- **レスポンシブ**: PC・スマホの両方に対応。

## 使い方
1. Python 3.x をインストール
2. `pip install flask opencv-python numpy` でライブラリをインストール
3. `python app.py` を実行
4. ブラウザで `http://localhost:5000` にアクセス