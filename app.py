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
    app.run(host="0.0.0.0", port=8000, debug=False)
