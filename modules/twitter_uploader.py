import os
import tweepy
import config


def post_tweet(script: dict, youtube_url: str) -> str:
    """YouTube動画のURLとスクリプトからツイートを投稿する。投稿IDを返す。"""
    api_key        = os.environ.get("TWITTER_API_KEY", "")
    api_secret     = os.environ.get("TWITTER_API_SECRET", "")
    access_token   = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_secret  = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )

    title = script.get("title", "")
    tags  = script.get("tags", [])

    # タグからハッシュタグを生成（最大3個）
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:3])

    # 280文字制限に合わせてタイトルをトリム
    url_len  = len(youtube_url) + 1  # スペース込み
    tag_len  = len(hashtags) + 1
    max_title = 280 - url_len - tag_len - 2
    if len(title) > max_title:
        title = title[:max_title - 1] + "…"

    tweet_text = f"{title}\n\n{hashtags}\n{youtube_url}"

    response = client.create_tweet(text=tweet_text)
    tweet_id = response.data["id"]
    print(f"[twitter] 投稿成功！ tweet_id={tweet_id}")
    return tweet_id
