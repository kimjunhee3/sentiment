from flask import Flask, render_template
from sentiment_routes import sentiment_bp

app = Flask(__name__, template_folder="templates", static_folder="static")

# 블루프린트 등록
app.register_blueprint(sentiment_bp)

@app.route("/")
def home():
    # 임베드 환경이든 직접 열든 동일한 템플릿 사용
    return render_template("sentiment.html")

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True, use_reloader=False)
