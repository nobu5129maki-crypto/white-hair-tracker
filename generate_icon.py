#!/usr/bin/env python3
"""icon.svg を icon-512.png に変換するスクリプト"""
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(base_dir, 'static', 'icon.svg')
    png_path = os.path.join(base_dir, 'static', 'icon-512.png')

    if not os.path.exists(svg_path):
        print(f"エラー: {svg_path} が見つかりません")
        sys.exit(1)

    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
    except ImportError as e:
        print(f"エラー: 必要なライブラリをインストールしてください: pip install svglib reportlab Pillow")
        print(str(e))
        sys.exit(1)

    drawing = svg2rlg(svg_path)
    if drawing is None:
        print("エラー: SVGの読み込みに失敗しました")
        sys.exit(1)

    # 512x512で出力（SVGは既に512x512）
    renderPM.drawToFile(drawing, png_path, fmt="PNG")
    print(f"完了: {png_path} を生成しました")

if __name__ == "__main__":
    main()
