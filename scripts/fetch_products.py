"""
DMM/FANZAアフィリエイトAPIから商品データを取得するモジュール
アダルトグッズ（mono/goods）特化版
"""

import time
import random
import requests
from typing import Optional
from config import Config, GENRES


# ジャンルごとの関連キーワード（タイトル・ジャンルフィルタリング用）
GENRE_KEYWORDS = {
    "onahole": ["オナホ", "オナホール", "名器", "ホール", "挿入", "リアル", "二層構造", "吸引", "振動", "非貫通"],
    "vibrator": ["バイブ", "バイブレーター", "ローター", "電マ", "振動", "リモコン", "防水", "USB充電", "吸引", "クリ"],
    "tenga": ["TENGA", "テンガ", "EGG", "カップ", "フリップ", "エアテック", "スピナー", "ディープスロート", "使い捨て", "繰り返し"],
    "lotion": ["ローション", "潤滑", "オイル", "ジェル", "マッサージ", "温感", "冷感", "ぬるぬる", "水溶性", "シリコン"],
    "cosplay_goods": ["コスプレ", "ランジェリー", "コスチューム", "セクシー", "下着", "ベビードール", "メイド服", "ナース", "制服", "網タイツ"],
    "sm_goods": ["SM", "拘束", "手錠", "目隠し", "首輪", "鞭", "ロープ", "ボンデージ", "ボールギャグ", "調教"],
    "couple": ["カップル", "ペア", "二人用", "リモート", "遠隔", "ワイヤレス", "パートナー", "夫婦", "プレゼント", "初心者"],
    "new_goods": ["新商品", "新作", "話題", "人気", "おすすめ", "ランキング", "売れ筋", "限定", "コラボ", "最新"],
}


def fetch_products(
    keyword: str = "",
    hits: int = Config.DEFAULT_HITS,
    service: str = "",
    floor: str = "",
    sort: str = Config.DEFAULT_SORT,
    genre: str = "",
) -> list[dict]:
    """
    DMM Affiliate API v3から商品一覧を取得する

    Args:
        keyword: 検索キーワード
        hits: 取得件数（最大100）
        service: サービス種別（mono等）
        floor: フロアID（goods等）
        sort: ソート順（date, rank, price等）
        genre: ジャンルキー（onahole, vibrator, tenga等）

    Returns:
        商品情報の辞書リスト
    """
    if not Config.validate():
        return []

    # ジャンルからservice/floorを取得
    genre_info = GENRES.get(genre, {}) if genre else {}
    if not service:
        service = genre_info.get("service", Config.DEFAULT_SERVICE)
    if not floor:
        floor = genre_info.get("floor", Config.DEFAULT_FLOOR)

    # キーワード未指定時はジャンルからランダムに選択
    if not keyword:
        if genre and genre in GENRES:
            keyword = random.choice(GENRES[genre]["keywords"])
        else:
            # ランダムなジャンルから選択
            random_genre = random.choice(list(GENRES.values()))
            keyword = random.choice(random_genre["keywords"])

    # APIリクエストパラメータの構築
    params = {
        "api_id": Config.API_ID,
        "affiliate_id": Config.AFFILIATE_ID,
        "site": "FANZA",
        "service": service,
        "hits": min(hits, 100),
        "sort": sort,
        "keyword": keyword,
        "output": "json",
    }

    if floor:
        params["floor"] = floor

    print(f"[取得中] キーワード「{keyword}」で{hits}件の商品を検索（{service}/{floor}）...")

    try:
        response = requests.get(Config.API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("[エラー] APIリクエストがタイムアウトしました")
        return []
    except requests.exceptions.ConnectionError:
        print("[エラー] APIサーバーに接続できません")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[エラー] APIがHTTPエラーを返しました: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[エラー] リクエスト中に予期せぬエラーが発生: {e}")
        return []

    try:
        data = response.json()
    except ValueError:
        print("[エラー] APIレスポンスのJSONパースに失敗しました")
        return []

    result = data.get("result", {})
    status = result.get("status", 0)
    if status != 200:
        message = result.get("message", "不明なエラー")
        print(f"[エラー] API応答エラー: {message}")
        return []

    items = result.get("items", [])
    if not items:
        print(f"[情報] キーワード「{keyword}」に該当する商品が見つかりませんでした")
        return []

    # フィルタリング用キーワードを決定
    relevant_kws = GENRE_KEYWORDS.get(genre, []) if genre else []

    products = []
    for item in items:
        product = _parse_item(item, service)
        if product:
            if relevant_kws:
                if _is_relevant(product, keyword, relevant_kws):
                    products.append(product)
                else:
                    print(f"[除外] 関連度低: {product['title'][:40]}...")
            else:
                products.append(product)

    print(f"[完了] {len(products)}件の関連商品データを取得しました")
    return products


def _is_relevant(product: dict, keyword: str, relevant_keywords: list[str]) -> bool:
    """
    商品がテーマに関連するかチェックする
    """
    title = product.get("title", "").lower()
    genres = " ".join(product.get("genres", [])).lower()
    check_text = f"{title} {genres}"

    if keyword.lower() in check_text:
        return True

    for kw in relevant_keywords:
        if kw.lower() in check_text:
            return True

    return False


def _build_affiliate_url(item: dict, affiliate_id: str, service: str = "mono") -> str:
    """商品のアフィリエイトURLを構築する（mono/goods用）"""
    content_id = item.get("content_id", "")
    direct_url = item.get("URL", "")

    if content_id:
        base_url = f"https://www.dmm.co.jp/mono/goods/-/detail/=/cid={content_id}/"
        return f"{base_url}?af_id={affiliate_id}"

    if direct_url:
        separator = "&" if "?" in direct_url else "?"
        return f"{direct_url}{separator}af_id={affiliate_id}"

    return item.get("affiliateURL", "")


def _parse_item(item: dict, service: str = "mono") -> Optional[dict]:
    """APIレスポンスの1商品をパースして整形する"""
    try:
        image_url = ""
        image_data = item.get("imageURL", {})
        if image_data:
            image_url = image_data.get("large", image_data.get("small", ""))

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
            genre_list = item_info.get("genre", [])
            genres = [g.get("name", "") for g in genre_list if g.get("name")]

        # グッズには女優情報がないので、メーカー情報を重視
        maker = ""
        if item_info and item_info.get("maker"):
            maker = item_info.get("maker", [{}])[0].get("name", "")

        series = ""
        if item_info and item_info.get("series"):
            series = item_info.get("series", [{}])[0].get("name", "")

        # 商品画像（サンプル画像）
        sample_images = []
        sample_image_data = item.get("sampleImageURL", {})
        if sample_image_data:
            sample_l = sample_image_data.get("sample_l", {})
            if sample_l:
                sample_images = sample_l.get("image", [])
            else:
                sample_s = sample_image_data.get("sample_s", {})
                if sample_s:
                    small_images = sample_s.get("image", [])
                    import re as _re
                    for img in small_images:
                        large_img = _re.sub(r'(\w+)-(\d+\.jpg)$', r'\1jp-\2', img)
                        sample_images.append(large_img)

        return {
            "title": item.get("title", "タイトル不明"),
            "description": item.get("title", ""),
            "image_url": image_url,
            "affiliate_url": _build_affiliate_url(item, Config.AFFILIATE_ID, service),
            "price": price,
            "date": item.get("date", ""),
            "content_id": item.get("content_id", ""),
            "product_id": item.get("product_id", ""),
            "genres": genres,
            "maker": maker,
            "series": series,
            "sample_images": sample_images,
        }
    except (KeyError, IndexError, TypeError) as e:
        print(f"[警告] 商品データのパースに失敗しました: {e}")
        return None


def fetch_multiple_keywords(
    keywords: Optional[list[str]] = None,
    hits_per_keyword: int = 3,
    genre: str = "",
) -> list[dict]:
    """複数キーワードで商品を一括取得する"""
    if keywords is None:
        if genre and genre in GENRES:
            keywords = GENRES[genre]["keywords"]
        else:
            keywords = []
            for g in GENRES.values():
                keywords.extend(g["keywords"])

    all_products = []
    seen_ids = set()

    for kw in keywords:
        products = fetch_products(keyword=kw, hits=hits_per_keyword, genre=genre)
        for p in products:
            pid = p.get("content_id", "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_products.append(p)
        time.sleep(1)

    print(f"[合計] {len(all_products)}件のユニークな商品を取得しました")
    return all_products


if __name__ == "__main__":
    products = fetch_products(keyword="オナホ", hits=3, genre="onahole")
    for p in products:
        print(f"  - {p['title']} ({p['price']})")
