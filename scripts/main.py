"""
メインスクリプト: 商品取得 → 記事生成 → (任意) Git push の一連のフローを実行する
アダルトグッズ専門レビューサイト「大人のおもちゃ研究所」用
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from config import Config, GENRES
from fetch_products import fetch_products, fetch_multiple_keywords
from generate_articles import generate_articles


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="FANZAアダルトグッズ商品データを取得してHugoブログ記事を自動生成する（8ジャンル対応）",
    )
    parser.add_argument(
        "--genre",
        type=str,
        default="",
        help="ジャンルキー（onahole, vibrator, tenga, lotion, cosplay_goods, sm_goods, couple, new_goods, all）",
    )
    parser.add_argument(
        "--keyword",
        type=str,
        default="",
        help="検索キーワード（--genre指定時は無視）",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="ジャンルあたりの取得商品数（デフォルト: 5）",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="生成後にgit add/commit/pushを自動実行する",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="全デフォルトキーワードで一括取得する（--genre allと同等）",
    )
    return parser.parse_args()


def git_push(files: list[str]) -> bool:
    """生成した記事ファイルをGitでコミット・プッシュする"""
    if not files:
        print("[Git] コミットする記事がありません")
        return False

    project_root = Path(__file__).resolve().parent.parent

    try:
        print("[Git] ファイルをステージング中...")
        subprocess.run(
            ["git", "add"] + files,
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )

        count = len(files)
        message = f"記事自動生成: {count}件の新規記事を追加"
        print(f"[Git] コミット中... ({message})")
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )

        print("[Git] プッシュ中...")
        subprocess.run(
            ["git", "push"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        print("[Git] プッシュ完了！")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[Git エラー] {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print("[Git エラー] gitコマンドが見つかりません")
        return False


def print_summary(products: list[dict], files: list[str], genre: str = "") -> None:
    """実行結果のサマリーを表示する"""
    print("\n" + "=" * 60)
    print("  実行結果サマリー")
    print("=" * 60)
    if genre:
        print(f"  ジャンル          : {genre}")
    print(f"  取得した商品数    : {len(products)}件")
    print(f"  生成した記事数    : {len(files)}件")
    print(f"  出力先            : {Config.CONTENT_DIR}")
    print("-" * 60)

    if files:
        print("  生成されたファイル:")
        for f in files:
            print(f"    - {Path(f).name}")
    else:
        print("  ※ 新規生成された記事はありませんでした")

    print("=" * 60 + "\n")


def run_genre(genre_key: str, count: int) -> tuple[list[dict], list[str]]:
    """1ジャンル分の記事を取得・生成する"""
    genre_info = GENRES.get(genre_key, {})
    category_name = genre_info.get("category", genre_key)
    keywords = genre_info.get("keywords", [])

    print(f"\n{'='*40}")
    print(f"  ジャンル: {category_name} ({genre_key})")
    print(f"{'='*40}")

    all_products = []
    seen_ids = set()

    for kw in keywords:
        products = fetch_products(
            keyword=kw,
            hits=min(count * 4, 100),
            genre=genre_key,
        )
        for p in products:
            pid = p.get("content_id", "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_products.append(p)
        time.sleep(1)

    # 必要件数に絞る
    all_products = all_products[:count]

    if not all_products:
        print(f"[{category_name}] 取得できた商品がないため、スキップします")
        return [], []

    generated_files = generate_articles(all_products, genre=genre_key)
    return all_products, generated_files


def main() -> None:
    """メイン処理"""
    args = parse_args()

    print("\n[開始] 大人のおもちゃ研究所 記事自動生成システム\n")
    if not Config.validate():
        sys.exit(1)

    all_products = []
    all_files = []

    if args.genre == "all" or args.multi:
        # 全ジャンル実行
        for genre_key in GENRES:
            products, files = run_genre(genre_key, args.count)
            all_products.extend(products)
            all_files.extend(files)

        print_summary(all_products, all_files, genre="全ジャンル")

    elif args.genre and args.genre in GENRES:
        # 指定ジャンルのみ
        products, files = run_genre(args.genre, args.count)
        all_products = products
        all_files = files

        print_summary(all_products, all_files, genre=args.genre)

    else:
        # キーワード指定 or デフォルト
        if args.keyword:
            products = fetch_products(
                keyword=args.keyword,
                hits=min(args.count * 4, 100),
            )
            products = products[:args.count]
        else:
            products = fetch_multiple_keywords(
                hits_per_keyword=max(1, args.count),
            )

        if not products:
            print("[終了] 取得できた商品がないため、記事生成をスキップします")
            sys.exit(0)

        all_products = products
        all_files = generate_articles(products)
        print_summary(all_products, all_files)

    # Git push
    if args.push and all_files:
        print("[Git] 自動プッシュを実行します...")
        success = git_push(all_files)
        if success:
            print("[Git] 正常に完了しました")
        else:
            print("[Git] プッシュに失敗しました。手動で確認してください")


if __name__ == "__main__":
    main()
