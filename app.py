import os
from flask import Flask, render_template, send_from_directory

# フォルダ構成を明示
app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

# アイコン設定ファイルを読み込むためのルート
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

if __name__ == "__main__":
    # Renderが指定するポート番号を取得して起動する設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)