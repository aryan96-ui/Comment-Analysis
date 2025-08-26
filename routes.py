from flask import Blueprint, render_template, request
from .sentiment import analyze_video

main = Blueprint('main', __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    sentiment_data = None
    if request.method == "POST":
        video_url = request.form.get("video_url")
        max_comments = int(request.form.get("max_comments", 100))
        sentiment_data = analyze_video(video_url, max_comments)
    return render_template("index.html", sentiment_data=sentiment_data)
