import os
import re
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from googleapiclient.discovery import build

def clean_text(text):
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"[^A-Za-z\s]", "", text)
    return text.strip()

def extract_video_id(video_url: str) -> str:
    """Extract YouTube video ID from different link formats."""
    if "watch?v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("/")[-1].split("?")[0]
    return video_url  # fallback, maybe user already passed the ID

def get_comments(video_url, max_comments=100):
    api_key = os.getenv("YOUTUBE_API_KEY")
    video_id = extract_video_id(video_url)

    youtube = build("youtube", "v3", developerKey=api_key)

    comments = []
    request = youtube.commentThreads().list(
        part="snippet", videoId=video_id, maxResults=100, textFormat="plainText"
    )
    response = request.execute()

    while response and len(comments) < max_comments:
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(clean_text(comment))
            if len(comments) >= max_comments:
                break
        if "nextPageToken" in response:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                pageToken=response["nextPageToken"],
                maxResults=100,
                textFormat="plainText",
            ).execute()
        else:
            break

    return comments

def analyze_video(video_url, max_comments=100):
    comments = get_comments(video_url, max_comments)
    sentiments = {"positive": 0, "negative": 0, "neutral": 0}
    polarity_scores = []

    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity # type: ignore
        polarity_scores.append(polarity)
        if polarity > 0:
            sentiments["positive"] += 1
        elif polarity < 0:
            sentiments["negative"] += 1
        else:
            sentiments["neutral"] += 1

    # Word cloud
    if comments:  # avoid crash if no comments
        text = " ".join(comments)
        wc = WordCloud(width=800, height=400, background_color="white").generate(text)
        os.makedirs("app/static/images", exist_ok=True)  # ensure path exists
        wc.to_file("app/static/images/wordcloud.png")

    return {
        "sentiments": sentiments,
        "total_comments": len(comments),
        "avg_polarity": sum(polarity_scores)/len(polarity_scores) if polarity_scores else 0
    }
