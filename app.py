from flask import Flask, render_template
from sentiment_routes import sentiment_bp

# 템플릿/정적 경로는 repo 구조에 맞게 유지
app = Flask(__name__, template_folder="templates", static_folder="static")

# 블루프린트 등록
app.register_blueprint(sentiment_bp)

@app.route("/")
def home():
    # 임베드/직접접속 동일 템플릿
    # (sentiment.html이 이제 team 파라미터 없이도 기본팀을 불러온다)
    return render_template("sentiment.html")

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    # Railway 로컬 실행시 포트는 자유, 배포에선 플랫폼이 지정
    app.run(host="0.0.0.0", port=5051, debug=True, use_reloader=False)
