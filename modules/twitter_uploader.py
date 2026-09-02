import os
import tweepy


def post_tweet(script: dict, video_path: str) -> str:
    """動画をTwitter/Xに直接アップロードして投稿する。投稿IDを返す。"""
    api_key       = os.environ.get("TWITTER_API_KEY", "")
    api_secret    = os.environ.get("TWITTER_API_SECRET", "")
    access_token  = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

    # v1.1 API（動画アップロード用）
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)

    print("[twitter] 動画をアップロード中...")
    media = api.media_upload(
        filename=video_path,
        media_type="video/mp4",
        chunked=True,
        wait_for_async_finalize=True,
    )
    media_id = media.media_id_string
    print(f"[twitter] media_id={media_id}")

    title    = script.get("title", "")
    tags     = script.get("tags", [])
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:3])

    max_title = 280 - len(hashtags) - 2
    if len(title) > max_title:
        title = title[:max_title - 1] + "…"

    tweet_text = f"{title}\n\n{hashtags}"

    # v2 API（ツイート投稿用）
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )
    response = client.create_tweet(text=tweet_text, media_ids=[media_id])
    tweet_id = response.data["id"]
    print(f"[twitter] 投稿成功！ tweet_id={tweet_id}")
    return tweet_id
