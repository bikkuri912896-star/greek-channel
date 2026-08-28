import json
import re
import random
from pathlib import Path
import anthropic
import config

TOPIC_POOL = [
    {"word": "λόγος",         "romanji": "logos",        "theme": "言葉・理性・論理",   "modern_hook": "logic・biology・psychologyなど英語の「-logy」系の単語"},
    {"word": "ἀρετή",         "romanji": "arete",        "theme": "徳・卓越性",         "modern_hook": "スポーツや自己啓発でよく使われる「卓越さ（excellence）」という概念"},
    {"word": "καλοκἀγαθία",   "romanji": "kalokagathia", "theme": "美と善の合一",        "modern_hook": "「美しく、そして善い」という古代ギリシャの理想の人間像"},
    {"word": "φιλοσοφία",     "romanji": "philosophia",  "theme": "知を愛すること",      "modern_hook": "「哲学（philosophy）」という言葉そのもの"},
    {"word": "ἀλήθεια",       "romanji": "aletheia",     "theme": "真理・隠れなさ",      "modern_hook": "映画『黄金の羅針盤』に登場する真実測定器「アリシオメーター」の語源"},
    {"word": "κόσμος",        "romanji": "kosmos",       "theme": "秩序・宇宙の美",      "modern_hook": "「コスメ（cosmetic）」と「コスモス（cosmos）」が同じ語源である事実"},
    {"word": "ψυχή",          "romanji": "psyche",       "theme": "魂・生命の息吹",      "modern_hook": "psychology（心理学）・psychic・精神科の「psych-」すべての語源"},
    {"word": "νοῦς",          "romanji": "nous",         "theme": "知性・精神",          "modern_hook": "現代のAI企業や哲学書に頻出する「Nous（知性）」という概念"},
    {"word": "εἰρήνη",        "romanji": "eirene",       "theme": "平和・静寂",          "modern_hook": "女性名「アイリーン（Irene）」の語源"},
    {"word": "ἔρως",          "romanji": "eros",         "theme": "愛・欲求・創造力",    "modern_hook": "「エロス」と呼ばれる愛の神の名前と、その本来の意味"},
    {"word": "φιλία",         "romanji": "philia",       "theme": "友情・愛着",          "modern_hook": "アメリカの都市「Philadelphia（フィラデルフィア）」の意味"},
    {"word": "ἀγάπη",         "romanji": "agape",        "theme": "無条件の愛",          "modern_hook": "「好き」「恋」「愛」―古代ギリシャ語には愛の種類ごとに別の単語があった"},
    {"word": "σοφία",         "romanji": "sophia",       "theme": "知恵",               "modern_hook": "女性名「ソフィア（Sophia）」と「philosophy」に共通する語源"},
    {"word": "δικαιοσύνη",    "romanji": "dikaiosyne",   "theme": "正義",               "modern_hook": "プラトンが2400年前に「正義とは何か」を問い、今も答えが出ていない問い"},
    {"word": "ἐλευθερία",     "romanji": "eleutheria",   "theme": "自由",               "modern_hook": "古代アテネで生まれた「自由」の概念が現代民主主義の基盤になった経緯"},
    {"word": "δημοκρατία",    "romanji": "demokratia",   "theme": "民主主義",            "modern_hook": "「democracy」はギリシャ語がほぼそのまま英語になった言葉"},
    {"word": "πόλις",         "romanji": "polis",        "theme": "都市国家・共同体",    "modern_hook": "politics・police・metropolis―すべての語源"},
    {"word": "θεωρία",        "romanji": "theoria",      "theme": "観照・理論",          "modern_hook": "「セオリー（theory）」の語源は「眺めること・見ること」だった"},
    {"word": "κάθαρσις",      "romanji": "katharsis",    "theme": "浄化・解放",          "modern_hook": "映画や小説を見終わった後の「すっきり感」を表す「カタルシス」の語源"},
    {"word": "μίμησις",       "romanji": "mimesis",      "theme": "模倣・表現",          "modern_hook": "アリストテレスが「すべての芸術は模倣から始まる」と言った概念"},
    {"word": "ποίησις",       "romanji": "poiesis",      "theme": "創造・詩作",          "modern_hook": "「poetry（詩）」の語源は「創ること」という意味だった"},
    {"word": "τέχνη",         "romanji": "techne",       "theme": "技術・技芸",          "modern_hook": "「technology（テクノロジー）」の語源は「技術・技芸」だった"},
    {"word": "φύσις",         "romanji": "physis",       "theme": "自然・本性",          "modern_hook": "「physics（物理学）」「physio（理学療法）」すべての語源"},
    {"word": "ἀρχή",          "romanji": "arche",        "theme": "始原・根本原理",      "modern_hook": "「archive（アーカイブ）」「anarchist（アナーキスト）」の語源"},
    {"word": "ἁρμονία",       "romanji": "harmonia",     "theme": "調和",               "modern_hook": "「harmony（ハーモニー）」の語源は古代ギリシャの女神の名前だった"},
    {"word": "συμπόσιον",     "romanji": "symposion",    "theme": "饗宴・対話の場",      "modern_hook": "「symposium（シンポジウム）」の語源は「一緒にお酒を飲む会」だった"},
    {"word": "παιδεία",       "romanji": "paideia",      "theme": "教育・文化的陶冶",    "modern_hook": "「encyclopedia（百科事典）」に隠れた古代の教育哲学"},
    {"word": "εὐδαιμονία",    "romanji": "eudaimonia",   "theme": "幸福・繁栄",          "modern_hook": "現代の幸福研究（ポジティブ心理学）が注目するギリシャ語の概念"},
    {"word": "ἀτάραξια",      "romanji": "ataraxia",     "theme": "心の平静",            "modern_hook": "ストア哲学とエピクロス哲学が共に追い求めた「揺れない心」の概念"},
    {"word": "μέτρον",        "romanji": "metron",       "theme": "節度・測定",          "modern_hook": "「meter（メートル）」「thermometer」すべての語源"},
    {"word": "χάρις",         "romanji": "charis",       "theme": "優雅・感謝",          "modern_hook": "「カリスマ（charisma）」の語源は「優雅さ・神の贈り物」だった"},
    {"word": "μνήμη",         "romanji": "mneme",        "theme": "記憶",               "modern_hook": "「amnesia（記憶喪失）」「mnemonic（記憶術）」の語源"},
    {"word": "ὄνειρος",       "romanji": "oneiros",      "theme": "夢",                 "modern_hook": "古代ギリシャ人は夢を神からのメッセージとして解読していた"},
    {"word": "χρόνος",        "romanji": "chronos",      "theme": "時間の流れ",          "modern_hook": "「chronicle（年代記）」「chronic（慢性的）」「synchronize」の語源"},
    {"word": "καιρός",        "romanji": "kairos",       "theme": "好機・最良の瞬間",    "modern_hook": "「Carpe Diem（今を生きよ）」と対になる古代の時間哲学"},
    {"word": "ἀνάγκη",        "romanji": "ananke",       "theme": "必然性・運命",        "modern_hook": "なぜ人は運命に抗えないのか―古代ギリシャの「必然性の女神」"},
    {"word": "τύχη",          "romanji": "tyche",        "theme": "運・偶然",            "modern_hook": "「チャンス」と「運命」の違い―ギリシャ語には別々の女神がいた"},
    {"word": "μοῖρα",         "romanji": "moira",        "theme": "定め・運命",          "modern_hook": "神さえも逆らえない「モイラ（運命の三女神）」とは何か"},
    {"word": "ἀθανασία",      "romanji": "athanasia",    "theme": "不死・永遠性",        "modern_hook": "古代ギリシャ人はなぜ魂の不死を信じたのか―プラトンの証明"},
    {"word": "ὄλβος",         "romanji": "olbos",        "theme": "至福・繁栄",          "modern_hook": "「お金があれば幸せか」を2500年前に問い続けたギリシャ哲学"},
    {"word": "θυμός",         "romanji": "thymos",       "theme": "気概・魂の情熱",      "modern_hook": "プラトンが魂を三つに分けたとき、その一つが「怒り・誇り・気概」だった"},
    {"word": "αἰών",          "romanji": "aion",         "theme": "永遠・時代"},
    {"word": "εἶδος",         "romanji": "eidos",        "theme": "形相・イデア",        "modern_hook": "プラトンの「イデア論」―すべての物には完全な型（form）が存在するという思想"},
]

SYSTEM_PROMPT = """あなたは古典ギリシャ語を専門とする学者であり、YouTube Shorts向け教育コンテンツの脚本家です。
与えられたギリシャ語の単語について、日本語で視聴者を引き込む短編動画の脚本をJSON形式で生成してください。

【脚本の構成原則】
「視聴者が知っているもの（英単語・ブランド・映画・日常語）→ 実はギリシャ語が語源だったと明かす → 元の意味を深掘り」
という順番で構成してください。ギリシャ語そのものを主役にするのではなく、
現代との意外なつながりを「驚き」として先に提示することで、ギリシャ語に興味がない人にも刺さる動画を作ります。

必ずJSON形式のみで返答し、マークダウンのコードブロック（```json など）は使わないでください。
返答はそのままJSONとしてパースできるものにしてください。"""

USER_PROMPT_TEMPLATE = """以下のギリシャ語単語について、YouTube Shorts（約55秒）の脚本を生成してください。

単語: {word}
ローマ字: {romanji}
テーマ: {theme}
現代との接点（イントロのフックに使うこと）: {modern_hook}

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
4. タイトルは「○○の語源」「○○はギリシャ語で〜という意味だった」など、検索されやすい日本語を先頭に置いてください。ギリシャ文字や英単語から始めないでください。

以下のJSON構造で脚本を返してください:

{{
  "title": "日本語で検索されやすいフック型タイトル（例：「psychology の語源は『魂』という意味だった」）",
  "description": "YouTube概要欄テキスト（150文字程度、語源・英単語・現代との関連を含める）",
  "tags": ["古典ギリシャ語", "語源", "英単語", "{romanji}", "Shorts", "雑学"],
  "greek_word": "{word}",
  "romanji": "{romanji}",
  "scenes": [
    {{
      "type": "intro",
      "narration": "「現代との接点」を提示して視聴者を引き込む問いかけ（例：「『psychology』という英単語の語源、知っていますか？」）"
    }},
    {{
      "type": "word",
      "greek_text": "{word}",
      "romanji": "{romanji}",
      "reading": "日本語での読み方（カタカナ）",
      "narration": "「実はギリシャ語の○○という言葉から来ています」と種明かしするナレーション"
    }},
    {{
      "type": "meaning",
      "subtitle": "このシーンの小見出し（10文字以内）",
      "greek_quote": "関連するギリシャ語の短い引用句（任意）",
      "quote_source": "出典（例：プラトン）",
      "narration": "元のギリシャ語の深い意味・哲学的背景・なぜ現代語に受け継がれたかを語るナレーション（150〜180文字）"
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
        modern_hook=topic.get("modern_hook", "現代語への影響・語源としての役割"),
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
