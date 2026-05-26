import json
import re
import random
from pathlib import Path
import anthropic
import config

TOPIC_POOL = [
    {"word": "λόγος", "romanji": "logos", "theme": "言葉・理性・論理"},
    {"word": "ἀρετή", "romanji": "arete", "theme": "徳・卓越性"},
    {"word": "καλοκἀγαθία", "romanji": "kalokagathia", "theme": "美と善の合一"},
    {"word": "φιλοσοφία", "romanji": "philosophia", "theme": "知を愛すること"},
    {"word": "ἀλήθεια", "romanji": "aletheia", "theme": "真理・隠れなさ"},
    {"word": "κόσμος", "romanji": "kosmos", "theme": "秩序・宇宙の美"},
    {"word": "ψυχή", "romanji": "psyche", "theme": "魂・生命の息吹"},
    {"word": "νοῦς", "romanji": "nous", "theme": "知性・精神"},
    {"word": "εἰρήνη", "romanji": "eirene", "theme": "平和・静寂"},
    {"word": "ἔρως", "romanji": "eros", "theme": "愛・欲求・創造力"},
    {"word": "φιλία", "romanji": "philia", "theme": "友情・愛着"},
    {"word": "ἀγάπη", "romanji": "agape", "theme": "無条件の愛"},
    {"word": "σοφία", "romanji": "sophia", "theme": "知恵"},
    {"word": "δικαιοσύνη", "romanji": "dikaiosyne", "theme": "正義"},
    {"word": "ἐλευθερία", "romanji": "eleutheria", "theme": "自由"},
    {"word": "δημοκρατία", "romanji": "demokratia", "theme": "民主主義"},
    {"word": "πόλις", "romanji": "polis", "theme": "都市国家・共同体"},
    {"word": "θεωρία", "romanji": "theoria", "theme": "観照・理論"},
    {"word": "κάθαρσις", "romanji": "katharsis", "theme": "浄化・解放"},
    {"word": "μίμησις", "romanji": "mimesis", "theme": "模倣・表現"},
    {"word": "ποίησις", "romanji": "poiesis", "theme": "創造・詩作"},
    {"word": "τέχνη", "romanji": "techne", "theme": "技術・技芸"},
    {"word": "φύσις", "romanji": "physis", "theme": "自然・本性"},
    {"word": "ἀρχή", "romanji": "arche", "theme": "始原・根本原理"},
    {"word": "ἁρμονία", "romanji": "harmonia", "theme": "調和"},
    {"word": "συμπόσιον", "romanji": "symposion", "theme": "饗宴・対話の場"},
    {"word": "παιδεία", "romanji": "paideia", "theme": "教育・文化的陶冶"},
    {"word": "εὐδαιμονία", "romanji": "eudaimonia", "theme": "幸福・繁栄"},
    {"word": "ἀτάραξια", "romanji": "ataraxia", "theme": "心の平静"},
    {"word": "μέτρον", "romanji": "metron", "theme": "節度・測定"},
    {"word": "χάρις", "romanji": "charis", "theme": "優雅・感謝"},
    {"word": "μνήμη", "romanji": "mneme", "theme": "記憶"},
    {"word": "ὄνειρος", "romanji": "oneiros", "theme": "夢"},
    {"word": "χρόνος", "romanji": "chronos", "theme": "時間の流れ"},
    {"word": "καιρός", "romanji": "kairos", "theme": "好機・最良の瞬間"},
    {"word": "ἀνάγκη", "romanji": "ananke", "theme": "必然性・運命"},
    {"word": "τύχη", "romanji": "tyche", "theme": "運・偶然"},
    {"word": "μοῖρα", "romanji": "moira", "theme": "定め・運命"},
    {"word": "ἀθανασία", "romanji": "athanasia", "theme": "不死・永遠性"},
    {"word": "ὄλβος", "romanji": "olbos", "theme": "至福・繁栄"},
    {"word": "θυμός", "romanji": "thymos", "theme": "気概・魂の情熱"},
    {"word": "αἰών", "romanji": "aion", "theme": "永遠・時代"},
    {"word": "εἶδος", "romanji": "eidos", "theme": "形相・イデア"},
]

SYSTEM_PROMPT = """あなたは古典ギリシャ語を専門とする学者であり、YouTube Shorts向け教育コンテンツの脚本家です。
与えられたギリシャ語の単語について、日本語で神秘的で美しい短編動画の脚本をJSON形式で生成してください。

必ずJSON形式のみで返答し、マークダウンのコードブロック（```json など）は使わないでください。
返答はそのままJSONとしてパースできるものにしてください。"""

USER_PROMPT_TEMPLATE = """以下のギリシャ語単語について、YouTube Shorts（約55秒）の脚本を生成してください。

単語: {word}
ローマ字: {romanji}
テーマ: {theme}

【重要ルール】
1. narration（ナレーション）フィールドは必ず純粋な日本語のみで書いてください。ギリシャ文字（αβγなど）を絶対に含めないでください。ギリシャ語に言及する場合はカタカナ読みを使ってください（例：χρόνος → クロノス）。
2. 各ナレーションは読み上げ時間が指定秒数に収まるよう、文字数を守ってください。
- intro: 60〜80文字（約8秒）
- word: 50〜70文字（約9秒）
- meaning: 150〜180文字（約25秒）
- outro: 固定テキストを使用（下記参照）
3. ナレーションは必ず話し言葉で書いてください。以下を守ってください：
- 短い文を組み合わせる（一文は30文字以内を目安に）
- 読点（、）を使って自然な間を作る
- 「〜なのです」「〜でしょう」など語りかける口調を使う
- 難しい書き言葉・漢語表現は避ける
- 聴いて自然に聞こえる文章にする

以下のJSON構造で脚本を返してください:

{{
  "title": "【古典ギリシャ語】{word}（{romanji}）― {theme}",
  "description": "YouTube概要欄テキスト（150文字程度）",
  "tags": ["古典ギリシャ語", "哲学", "語源", "{romanji}", "Shorts"],
  "greek_word": "{word}",
  "romanji": "{romanji}",
  "scenes": [
    {{
      "type": "intro",
      "narration": "古代ギリシャ人が生み出した言葉には、現代語では表せない深みがあります。今日の言葉は――"
    }},
    {{
      "type": "word",
      "greek_text": "{word}",
      "romanji": "{romanji}",
      "reading": "日本語での読み方（カタカナ）",
      "narration": "単語の発音と基本的な意味を一文で紹介するナレーション"
    }},
    {{
      "type": "meaning",
      "subtitle": "このシーンの小見出し（10文字以内）",
      "greek_quote": "関連するギリシャ語の短い引用句（任意）",
      "quote_source": "出典（例：プラトン）",
      "narration": "単語の深い意味・哲学的背景・現代への影響を語るナレーション（150〜180文字）"
    }},
    {{
      "type": "outro",
      "narration": "ぜひチャンネル登録をして、次の言葉もお聞きください。"
    }}
  ]
}}"""


def load_used_topics() -> list:
    if config.USED_TOPICS_FILE.exists():
        with open(config.USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_used_topics(used: list):
    with open(config.USED_TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def pick_topic() -> dict:
    used = load_used_topics()
    available = [t for t in TOPIC_POOL if t["word"] not in used]
    if not available:
        save_used_topics([])
        available = TOPIC_POOL[:]
    topic = random.choice(available)
    used.append(topic["word"])
    save_used_topics(used)
    return topic


def generate_script(topic: dict | None = None) -> dict:
    if topic is None:
        topic = pick_topic()

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        word=topic["word"],
        romanji=topic["romanji"],
        theme=topic["theme"],
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    script = json.loads(raw)
    script["_topic"] = topic

    # 〆の言葉を強制固定
    for scene in script.get("scenes", []):
        if scene.get("type") == "outro":
            scene["narration"] = "ぜひチャンネル登録をして、次の言葉もお聞きください。"
    return script
