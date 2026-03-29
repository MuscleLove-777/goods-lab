"""ランキングページ自動生成スクリプト（アダルトグッズ版）"""
import os
import requests
from datetime import datetime
from config import Config


def fetch_ranking(keyword="", hits=20, service="mono", floor="goods"):
    """APIからランキングデータを取得（sort=rankで人気順）"""
    params = {
        "api_id": Config.API_ID,
        "affiliate_id": Config.AFFILIATE_ID,
        "site": "FANZA",
        "service": service,
        "hits": min(hits, 100),
        "sort": "rank",  # ランキング順
        "output": "json",
    }
    if floor:
        params["floor"] = floor
    if keyword:
        params["keyword"] = keyword

    r = requests.get(Config.API_BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    items = data.get("result", {}).get("items", [])

    results = []
    for i, item in enumerate(items):
        image_url = ""
        img_data = item.get("imageURL", {})
        if img_data:
            image_url = img_data.get("large", img_data.get("small", ""))

        content_id = item.get("content_id", "")
        affiliate_url = (
            f"https://www.dmm.co.jp/mono/goods/-/detail/=/cid={content_id}/?af_id={Config.AFFILIATE_ID}"
            if content_id
            else ""
        )

        prices = item.get("prices", {})
        price = ""
        if prices:
            price_info = prices.get("price", prices.get("deliveries", {}).get("delivery", [{}]))
            if isinstance(price_info, str):
                price = price_info
            elif isinstance(price_info, list) and price_info:
                price = price_info[0].get("price", "")

        genres = []
        item_info = item.get("iteminfo", {})
        if item_info:
            genres = [g.get("name", "") for g in item_info.get("genre", []) if g.get("name")]

        maker = ""
        if item_info and item_info.get("maker"):
            maker = item_info.get("maker", [{}])[0].get("name", "")

        # サンプル画像
        sample_images = []
        sample_data = item.get("sampleImageURL", {})
        if sample_data:
            sl = sample_data.get("sample_l", {})
            if sl:
                sample_images = sl.get("image", [])[:3]

        results.append(
            {
                "rank": i + 1,
                "title": item.get("title", ""),
                "image_url": image_url,
                "affiliate_url": affiliate_url,
                "price": price,
                "content_id": content_id,
                "maker": maker,
                "genres": genres[:5],
                "sample_images": sample_images,
            }
        )

    return results


def generate_ranking_page(ranking_type="daily", genre_name="総合", genre_key=""):
    """ランキングページのMarkdownを生成"""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")

    type_labels = {
        "daily": "デイリー",
        "weekly": "週間",
        "monthly": "月間",
    }
    type_label = type_labels.get(ranking_type, "デイリー")

    # ジャンルキーワードでランキング取得
    keyword = genre_key if genre_key else ""
    items = fetch_ranking(keyword=keyword, hits=20)

    if not items:
        print(f"[スキップ] {genre_name} {type_label}ランキング: データなし")
        return None

    # front matter
    title = f"【{date_str}】{genre_name} {type_label}ランキングTOP20"
    slug = f"ranking-{ranking_type}-{genre_name.lower().replace(' ', '-')}-{date_str}"

    md = f"""---
title: "{title}"
date: {today.strftime("%Y-%m-%dT%H:%M:%S+09:00")}
tags: ["ランキング", "{genre_name}", "{type_label}"]
categories: ["Ranking"]
draft: false
description: "{date_str}更新の{genre_name}アダルトグッズ{type_label}ランキングTOP20。FANZAの売れ筋商品を画像付きで紹介。"
cover:
  image: "{items[0]['image_url']}"
  alt: "{genre_name}{type_label}ランキング1位"
  hidden: false
---

## {genre_name} アダルトグッズ {type_label}ランキング TOP20

**{date_str} 更新** | FANZAの売れ筋データに基づくランキング

"""

    for item in items:
        rank = item["rank"]
        # ランクアイコン
        if rank == 1:
            rank_icon = "\U0001f947"
        elif rank == 2:
            rank_icon = "\U0001f948"
        elif rank == 3:
            rank_icon = "\U0001f949"
        else:
            rank_icon = f"**{rank}位**"

        maker_text = item.get("maker", "")
        genre_text = " / ".join(item["genres"][:3]) if item["genres"] else ""

        md += f"""### {rank_icon} {item["title"][:50]}{"…" if len(item["title"]) > 50 else ""}

<div style="display: flex; gap: 16px; margin: 1em 0; flex-wrap: wrap;">
  <div style="flex: 0 0 200px;">
    <a href="{item['affiliate_url']}" target="_blank" rel="nofollow">
      <img src="{item['image_url']}" alt="ランキング{rank}位" style="width: 200px; border-radius: 8px;" loading="lazy" />
    </a>
  </div>
  <div style="flex: 1; min-width: 200px;">
"""
        if maker_text:
            md += f"    <p><strong>メーカー:</strong> {maker_text}</p>\n"
        if genre_text:
            md += f"    <p><strong>ジャンル:</strong> {genre_text}</p>\n"
        if item["price"]:
            md += f"    <p><strong>価格:</strong> {item['price']}</p>\n"

        md += f"""    <a href="{item['affiliate_url']}" target="_blank" rel="nofollow"
       style="display: inline-block; padding: 8px 20px; background: #e63946; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 8px;">
      FANZAで見る
    </a>
  </div>
</div>

"""
        # サンプル画像（あれば）
        if item["sample_images"]:
            md += '<div style="display: flex; gap: 8px; margin: 0.5em 0 1.5em;">\n'
            for img in item["sample_images"]:
                md += f'  <a href="{img}" target="_blank"><img src="{img}" style="width: 120px; border-radius: 4px;" loading="lazy" /></a>\n'
            md += "</div>\n\n"

        md += "---\n\n"

    # フッター
    md += """
### 動画レビューはこちら

[エロナビ | アダルト動画総合レビューサイト](https://musclelove-777.github.io/eronavi/)

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
</div>

<p style="text-align: center; margin: 2em 0 0.5em; font-size: 0.9em; color: #888;">Presented by <strong>MuscleLove</strong></p>
"""

    # ファイル保存
    output_dir = Config.CONTENT_DIR
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{date_str}-ranking-{ranking_type}-{genre_name}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"[生成] {filepath}")
    return filepath


def generate_all_rankings():
    """全ジャンルのランキングを生成"""
    # 総合ランキング
    generate_ranking_page("daily", "総合", "")

    # ジャンル別ランキング（主要ジャンルのみ）
    genre_rankings = [
        ("オナホ", "オナホ"),
        ("バイブ", "バイブ"),
        ("TENGA", "TENGA"),
    ]
    for name, keyword in genre_rankings:
        generate_ranking_page("daily", name, keyword)


if __name__ == "__main__":
    generate_all_rankings()
