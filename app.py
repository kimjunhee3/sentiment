from flask import Flask, render_template
from flask_cors import CORS   # ✅ 추가
from sentiment_routes import sentiment_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)   # ✅ 모든 라우트에 CORS 허용

# 블루프린트 등록
app.register_blueprint(sentiment_bp)

@app.route("/")
def home():
    return render_template("sentiment.html")

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True, use_reloader=False)
