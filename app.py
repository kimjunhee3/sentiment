from flask import Flask, redirect, url_for
from flask_cors import CORS
from sentiment_routes import sentiment_bp
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

# 블루프린트 등록 (/sentiment, /api/*)
app.register_blueprint(sentiment_bp)

@app.route("/")
def index():
    # 루트로 접근하면 /sentiment로 리다이렉트
    return redirect(url_for("sentiment.sentiment_page"))

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
