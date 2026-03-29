"""記事投稿時にX(Twitter)で自動ツイートするスクリプト"""
import os
import glob
import re


def get_latest_posts(content_dir, count=3):
    """直近の記事を取得"""
    posts = sorted(glob.glob(os.path.join(content_dir, "*.md")), reverse=True)
    results = []
    for post in posts[:count]:
        with open(post, "r", encoding="utf-8") as f:
            content = f.read()
        # front matterからtitleを抽出
        title_match = re.search(r'title:\s*"(.+?)"', content)
        cover_match = re.search(r'image:\s*"(.+?)"', content)
        if title_match:
            results.append({
                "title": title_match.group(1),
                "image": cover_match.group(1) if cover_match else "",
                "filename": os.path.basename(post),
            })
    return results


def compose_tweet(post, site_url):
    """ツイート文を作成"""
    title = post["title"][:80]
    url = f"{site_url}posts/{post['filename'].replace('.md', '/')}"

    hashtags = "#アダルトグッズ #FANZA #オナホ #おすすめ"
    tweet = f"\U0001f525 新着レビュー\n\n{title}\n\n\U0001f449 {url}\n\n{hashtags}"
    return tweet[:280]  # Xの文字数制限


def post_to_x(tweet_text):
    """Xに投稿（APIキー設定後に有効化）"""
    # Twitter API v2
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("[スキップ] X APIキーが未設定です")
        return False

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        client.create_tweet(text=tweet_text)
        print(f"[投稿成功] {tweet_text[:50]}...")
        return True
    except Exception as e:
        print(f"[エラー] X投稿失敗: {e}")
        return False


if __name__ == "__main__":
    from config import Config
    site_url = "https://musclelove-777.github.io/goods-lab/"
    posts = get_latest_posts(Config.CONTENT_DIR, count=1)
    for post in posts:
        tweet = compose_tweet(post, site_url)
        print(f"[ツイート案]\n{tweet}\n")
        post_to_x(tweet)
