# 白髪トラッカー

**https://nobu5129maki-crypto.github.io/white-hair-tracker/** にアクセスするだけで使えます。

## GitHub Pages の設定（重要）

アクセス時にアプリが表示されるには、**Folder を `/(root)` に設定**してください。

1. リポジトリの **Settings** → **Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main`
4. **Folder**: `/(root)` を選択（`/docs` ではない）
5. **Save**

## ローカルで動かす（Flask版）

```bash
pip install -r requirements.txt
python app.py
```

`http://localhost:10000` にアクセス
