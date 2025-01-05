from flask import Flask, request, redirect
from article_tracker import ArticleTracker

app = Flask(__name__)
tracker = ArticleTracker()

@app.route('/track')
def track_click():
    article_url = request.args.get('url')
    if article_url:
        tracker.record_click(article_url)
    return redirect(article_url)

if __name__ == '__main__':
    app.run(port=5000) 