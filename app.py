from flask import Flask
from flask_cors import CORS
from sentiment_routes import sentiment_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

# 블루프린트 등록
app.register_blueprint(sentiment_bp)

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    # Railway 등에서 PORT 환경변수 설정 시 자동 사용됨 (gunicorn 사용 시 무시)
    import os
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
