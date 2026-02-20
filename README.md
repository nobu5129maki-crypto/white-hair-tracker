# 白髪トラッカー (White Hair Tracker)

カメラで撮影した髪の毛から白髪率を算出・記録するWebアプリです。

## オンラインで使う（GitHub Pages）

**https://nobu5129maki-crypto.github.io/white-hair-tracker/** にアクセスするだけですぐ使えます。

- サーバー不要・ブラウザだけで動作
- スマホのホーム画面に追加してアプリのように利用可能

## ローカルで動かす（Flask版）

1. Python 3.x をインストール
2. `pip install -r requirements.txt`
3. `python app.py` を実行
4. ブラウザで `http://localhost:10000` にアクセス

## GitHub Pages へのデプロイ

1. **アイコンを生成**（初回のみ）:
   ```bash
   pip install opencv-python-headless numpy
   python create_gh_icon.py
   ```
2. このリポジトリをGitHubにプッシュ
3. リポジトリの **Settings** → **Pages**
4. **Source** で `Deploy from a branch` を選択
5. **Branch** で `main`、**Folder** で `/docs` を選択
6. **Save** で保存

数分後に https://nobu5129maki-crypto.github.io/white-hair-tracker/ で公開されます。
