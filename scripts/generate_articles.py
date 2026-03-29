"""
商品データからHugo用のMarkdown記事を自動生成するモジュール
アダルトグッズ専門レビューサイト「大人のおもちゃ研究所」用
テンプレートのバリエーションを用意し、重複コンテンツを回避する
"""

import os
import re
import random
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from config import Config, GENRES

# 自サイトのURL（姉妹サイト相互リンク用）
CURRENT_SITE_URL = "https://musclelove-777.github.io/goods-lab/"


# ============================================================
# 記事テンプレート群（バリエーションで重複コンテンツを回避）
# ============================================================

ARTICLE_TEMPLATES = [
    # テンプレートA: ストレート紹介型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


## {{ hook_title }}

{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

### 商品情報

| 項目 | 内容 |
|------|------|
{% if price %}| 価格 | {{ price }} |
{% endif %}{% if maker %}| メーカー | {{ maker }} |
{% endif %}{% if series %}| シリーズ | {{ series }} |
{% endif %}

{{ body_text }}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートB: レビュー風型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


{{ intro_text }}

<!--more-->

## この商品の注目ポイント

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ body_text }}

{% if maker %}
> **{{ maker }}**から発売されたこの商品は、{{ category_name }}カテゴリで注目のアイテムです。
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートC: ピックアップ型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


## 本日の{{ category_name }}ピックアップ

{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

### この商品をおすすめする理由

{{ body_text }}

{% if price %}
**価格: {{ price }}** --- コスパも要チェック！
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートD: Q&A型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

### Q. どんな商品？

{{ body_text }}

### Q. 価格は？

{% if price %}{{ price }}で購入できます。{% else %}詳細はリンク先でご確認ください。{% endif %}

{% if maker %}
### Q. どこのメーカー？

{{ maker }}の商品です。品質に定評があります。
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),
]


# ============================================================
# グッズレビュー特化テキストバリエーション
# ============================================================

INTRO_VARIATIONS = [
    "使ってみた感想を正直にレビュー！**「{title}」**は{genre_text}好きにはたまらないアイテムです。",
    "{genre_text}を比較検討中なら注目！**「{title}」**、コスパ・使用感ともに高評価。",
    "初心者にもおすすめ！**「{title}」**は{genre_text}カテゴリの中でも特に人気のアイテム。",
    "話題のアダルトグッズ**「{title}」**をピックアップ。{genre_text}の定番商品です。",
    "**「{title}」**が気になっている人、正解です。{genre_text}ジャンルの中でもガチで満足度が高い商品。",
    "本日の厳選{category_name}は**「{title}」**。「買って正解」と話題の一品。",
    "新着から見つけた掘り出し物！**「{title}」**、{genre_text}好きなら即チェック。",
    "商品画像だけでも期待感MAX！**「{title}」**は{genre_text}の最高傑作かも。",
    "今週一番おすすめの{category_name}はコレ。**「{title}」**、見逃すな！",
    "大人のおもちゃ研究所が厳選！**「{title}」**は{genre_text}好きなら見逃せないアイテムです。",
    "研究所スタッフおすすめの**「{title}」**。{genre_text}カテゴリで今一番アツい商品。",
    "大人のおもちゃ研究所イチオシ！**「{title}」**、{genre_text}好きを唸らせる逸品が登場。",
]

BODY_VARIATIONS = [
    "素材の質感が非常に良く、手に持った瞬間から高品質さが伝わります。使用感もスムーズで、洗浄も簡単。価格以上の満足度を得られる一品です。",
    "パッケージから取り出した第一印象は「これは期待できる」。実際に使ってみると期待以上。リピート購入する人が多いのも納得のクオリティです。",
    "とにかく使いやすさが際立つ。初心者でも迷わず使えるデザインで、満足度も高い。メンテナンスも楽なので長く愛用できるアイテムです。",
    "完成度が高く、このカテゴリの中でもトップクラス。バリエーション豊富で飽きることなく楽しめます。コレクションに加えたい一品。",
    "見た目のクオリティが高く、細部までこだわりが感じられます。実用性とデザイン性を兼ね備えた満足度の高い商品です。",
    "このジャンルが好きなら間違いなく刺さるアイテム。素材感・機能性・コスパ、すべてが高水準でまとまっています。",
    "使い心地で言えば、間違いなく満足できる。パッケージの丁寧さと、使用時の快適さのバランスが絶妙です。",
]

HOOK_TITLES = [
    "今月のベストバイはコレで決まり",
    "初心者におすすめの注目アイテム",
    "見逃し厳禁！コスパ最強グッズ",
    "本日のおすすめアダルトグッズ",
    "ガチで満足度が高い厳選ピックアップ",
    "商品画像を今すぐチェック",
    "満足度MAXの注目商品",
    "話題のアダルトグッズを紹介",
    "大人のおもちゃ研究所のイチオシ",
    "研究所厳選！今日のおすすめ",
    "研究所が選ぶ注目アイテム",
]


def generate_articles(
    products: list[dict],
    output_dir: str = "",
    genre: str = "",
) -> list[str]:
    """
    商品データからHugo用Markdown記事を生成する

    Args:
        products: fetch_productsで取得した商品データリスト
        output_dir: 出力先ディレクトリ
        genre: ジャンルキー

    Returns:
        生成されたファイルパスのリスト
    """
    if not output_dir:
        output_dir = Config.CONTENT_DIR

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    generated_files = []

    for i, product in enumerate(products):
        try:
            filepath = _generate_single_article(product, output_dir, i, genre)
            if filepath:
                generated_files.append(filepath)
                print(f"[生成] {Path(filepath).name}")
        except Exception as e:
            print(f"[エラー] 記事生成に失敗: {product.get('title', '不明')} - {e}")

    print(f"\n[完了] {len(generated_files)}件の記事を生成しました → {output_dir}")
    return generated_files


def _generate_single_article(
    product: dict,
    output_dir: str,
    index: int,
    genre: str = "",
) -> str:
    """1商品分の記事を生成する"""
    title = product.get("title", "タイトル不明")
    image_url = product.get("image_url", "")
    affiliate_url = product.get("affiliate_url", "")
    price = product.get("price", "")
    genres = product.get("genres", [])
    maker = product.get("maker", "")
    series = product.get("series", "")
    sample_images = product.get("sample_images", [])

    # カテゴリ名の取得（category=URLスラッグ、category_label=表示用日本語名）
    genre_info = GENRES.get(genre, {}) if genre else {}
    category_name = genre_info.get("label", "おすすめ")
    category_slug = genre_info.get("category", "Recommended")

    # 日付の整形
    article_date = _format_date()

    # スラッグの生成
    slug = _make_slug(product.get("content_id", ""), index)

    # ファイル名
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    # 既存ファイルがあればスキップ
    if os.path.exists(filepath):
        print(f"[スキップ] 既に存在: {filename}")
        return ""

    # タグの生成
    tag_list = genres[:5] if genres else [category_name]
    tags = ", ".join(f'"{t}"' for t in tag_list)

    # ジャンルテキスト（導入文用）
    genre_text = "・".join(genres[:3]) if genres else category_name

    # テンプレート変数の準備
    intro_text = random.choice(INTRO_VARIATIONS).format(
        title=_truncate(title, 40),
        genre_text=genre_text,
        category_name=category_name,
    )
    body_text = random.choice(BODY_VARIATIONS)
    hook_title = random.choice(HOOK_TITLES)
    meta_description = _build_meta_description(title, genre_text, category_name, max_len=100)

    # 各セクション生成
    cta_section = _build_cta(affiliate_url, title)
    sample_gallery = _build_sample_gallery(sample_images, category_name)
    sns_section = _build_sns_section()
    footer_brand = _build_footer_brand()
    related_section = _build_related_section(category_name)
    alt_text = _build_alt_text(title, genre_text, category_name)

    # ランダムにテンプレートを選択
    template = random.choice(ARTICLE_TEMPLATES)

    # ジャンルタグをタイトル先頭に
    genre_prefix = f"【{category_name}】" if category_name else ""
    full_title = f"{genre_prefix}{_truncate(title, 55)}"

    # レンダリング
    content = template.render(
        title=full_title,
        date=article_date,
        tags=tags,
        category=category_slug,
        category_name=category_name,
        meta_description=meta_description,
        hook_title=hook_title,
        intro_text=intro_text,
        image_url=image_url,
        body_text=body_text,
        price=price,
        maker=maker,
        series=series,
        alt_text=alt_text,
        cta_section=cta_section,
        sample_gallery=sample_gallery,
        sns_section=sns_section,
        footer_brand=footer_brand,
        related_section=related_section,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

    return filepath


def _format_date() -> str:
    """今日の日付をHugo用のISO形式で返す"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _make_slug(content_id: str, index: int) -> str:
    """URLスラッグを生成する"""
    if content_id:
        slug = re.sub(r"[^a-zA-Z0-9]", "-", content_id).strip("-").lower()
        if slug:
            return slug
    return f"product-{index:03d}"


def _build_meta_description(title: str, genre_text: str, category_name: str, max_len: int = 155) -> str:
    """SEOキーワードを自然に含んだmeta descriptionを生成する"""
    desc_variations = [
        f"{title}のレビュー・使用感を紹介。{genre_text}系グッズの注目商品。",
        f"{category_name}好き必見の「{title}」を徹底レビュー。{genre_text}好きにおすすめ。",
        f"満足度MAX！{genre_text}グッズ「{title}」。商品画像付きで紹介。",
        f"{category_name}の注目商品「{title}」。{genre_text}アイテムを画像付きで紹介。",
    ]
    desc = random.choice(desc_variations)
    return _truncate(desc, max_len)


def _truncate(text: str, max_len: int) -> str:
    """テキストを指定文字数で切り詰める"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _build_alt_text(title: str, genre_text: str, category_name: str) -> str:
    """SEO向けの具体的なalt属性テキストを生成する"""
    alt_variations = [
        f"{category_name}「{title}」の商品画像",
        f"「{title}」{genre_text}系グッズのパッケージ画像",
        f"注目の「{title}」の商品写真",
    ]
    return _truncate(random.choice(alt_variations), 120)


def _build_cta(affiliate_url: str, title: str) -> str:
    """CTAボタンセクションを生成する"""
    if not affiliate_url:
        return ""

    cta_texts = [
        "購入ページへ",
        "FANZAで見る",
        "この商品をチェック",
        "詳細・購入はこちら",
        "商品ページへGO",
    ]
    cta_text = random.choice(cta_texts)

    return f"""
<div style="text-align: center; margin: 2em 0;">
  <a href="{affiliate_url}" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 15px 40px; background: #e63946; color: #fff; text-decoration: none; border-radius: 8px; font-size: 1.1em; font-weight: bold;">
    {cta_text}
  </a>
  <p style="margin-top: 0.5em; font-size: 0.85em; color: #888;">※外部サイト（FANZA）に移動します</p>
</div>
"""


def _build_sample_gallery(sample_images: list[str], category_name: str = "") -> str:
    """商品画像ギャラリーを生成する"""
    if not sample_images:
        return ""

    images = sample_images[:6]
    label = category_name if category_name else "アダルトグッズ"

    gallery_html = f"""
### 商品画像

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 1em 0;">
"""
    for idx, img_url in enumerate(images, 1):
        gallery_html += f'  <a href="{img_url}" target="_blank" rel="nofollow"><img src="{img_url}" alt="{label}の商品画像{idx}" style="width: 100%; border-radius: 4px;" loading="lazy" /></a>\n'

    gallery_html += "</div>\n"
    return gallery_html


def _build_sns_section() -> str:
    """SNSリンクセクションを生成する"""
    return """
### MuscleLove

<div style="display: flex; gap: 16px; flex-wrap: wrap; margin: 1.5em 0;">
  <a href="https://www.patreon.com/c/MuscleLove" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #FF424D; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on Patreon
  </a>
  <a href="https://x.com/MuscleGirlLove7" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #000; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on X
  </a>
  <a href="https://linktr.ee/ILoveMyCats" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #43e660; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove Links
  </a>
  <a href="https://musclelove.booth.pm/" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #fc4d50; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on BOOTH
  </a>
</div>
"""


def _build_footer_brand() -> str:
    """フッターのブランド表示を生成する"""
    return """
<p style="text-align: center; margin: 2em 0 0.5em; font-size: 0.9em; color: #888;">Presented by <strong>MuscleLove</strong></p>
"""


def _build_related_section(current_genre: str = "") -> str:
    """他ジャンルへの内部リンクでSEOを強化"""
    genres = {
        "オナホ": "/goods-lab/categories/onahole/",
        "バイブ": "/goods-lab/categories/vibrator/",
        "TENGA": "/goods-lab/categories/tenga/",
        "ローション": "/goods-lab/categories/lotion/",
        "コスプレ衣装": "/goods-lab/categories/cosplaygoods/",
        "SMグッズ": "/goods-lab/categories/smgoods/",
        "カップル": "/goods-lab/categories/couple/",
        "新商品": "/goods-lab/categories/newgoods/",
    }
    # 現在のジャンルを除外してランダム5つ選ぶ
    other = [(k, v) for k, v in genres.items() if k != current_genre]
    picks = random.sample(other, min(5, len(other)))

    links = " | ".join([f'[{name}を見る]({url})' for name, url in picks])

    sister = _build_sister_sites()

    return f"""
### 他のカテゴリも見る

{links}

[全カテゴリ一覧](/goods-lab/categories/) | [タグ一覧](/goods-lab/tags/)

### 動画レビューはこちら

[エロナビ | アダルト動画総合レビューサイト](https://musclelove-777.github.io/eronavi/)

{sister}
"""


def _build_sister_sites():
    """姉妹サイトへの相互リンク（SEOリンクジュース循環）"""
    sites = {
        "エロナビ（総合）": "https://musclelove-777.github.io/eronavi/",
        "アニメエロナビ": "https://musclelove-777.github.io/anime-navi/",
        "筋肉美女ナビ": "https://musclelove-777.github.io/fitness-affiliate-blog/",
        "NTRナビ": "https://musclelove-777.github.io/ntr-navi/",
        "没入エロスVR": "https://musclelove-777.github.io/vr-eros/",
        "艶妻コレクション": "https://musclelove-777.github.io/entsuma/",
        "シロウト発掘隊": "https://musclelove-777.github.io/shiroto-squad/",
        "おっぱいパラダイス": "https://musclelove-777.github.io/oppai-paradise/",
        "二次元嫁実写化計画": "https://musclelove-777.github.io/nijigen-realize/",
        "フェチの殿堂": "https://musclelove-777.github.io/fetish-dendo/",
        "大人のおもちゃ研究所": "https://musclelove-777.github.io/goods-lab/",
    }
    others = [(k, v) for k, v in sites.items() if v != CURRENT_SITE_URL]
    picks = random.sample(others, min(3, len(others)))
    links = "\n".join([f'- [{name}]({url})' for name, url in picks])
    return f"""### 姉妹サイト

{links}"""


if __name__ == "__main__":
    test_products = [
        {
            "title": "テスト商品",
            "image_url": "https://example.com/image.jpg",
            "affiliate_url": "https://example.com/affiliate",
            "price": "1,980円",
            "date": "2026-03-29 10:00:00",
            "content_id": "test001",
            "product_id": "test001",
            "genres": ["テスト"],
            "maker": "テストメーカー",
            "series": "",
            "sample_images": [],
        }
    ]
    files = generate_articles(test_products, genre="onahole")
    for f in files:
        print(f"  生成: {f}")
