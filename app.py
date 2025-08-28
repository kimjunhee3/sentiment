from flask import Flask, render_template
from sentiment_routes import sentiment_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(sentiment_bp)

@app.route("/")
def home():
    return render_template("sentiment.html")

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True, use_reloader=False)
