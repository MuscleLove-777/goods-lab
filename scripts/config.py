"""
設定管理モジュール
環境変数または.envファイルから設定を読み込む
アダルトグッズ専門レビューサイト「大人のおもちゃ研究所」用（mono/goods 8ジャンル）
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを読み込む
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


# ジャンル定義（検索キーワード・カテゴリ名）
GENRES = {
    "onahole": {"keywords": ["オナホ", "オナホール", "名器"], "category": "Onahole", "label": "オナホ", "service": "mono", "floor": "goods"},
    "vibrator": {"keywords": ["バイブ", "バイブレーター", "ローター"], "category": "Vibrator", "label": "バイブ", "service": "mono", "floor": "goods"},
    "tenga": {"keywords": ["TENGA", "テンガ", "EGG"], "category": "TENGA", "label": "TENGA", "service": "mono", "floor": "goods"},
    "lotion": {"keywords": ["ローション", "潤滑", "オイル"], "category": "Lotion", "label": "ローション", "service": "mono", "floor": "goods"},
    "cosplay_goods": {"keywords": ["コスプレ衣装", "セクシーランジェリー", "コスチューム"], "category": "CosplayGoods", "label": "コスプレ衣装", "service": "mono", "floor": "goods"},
    "sm_goods": {"keywords": ["SM", "拘束", "手錠", "目隠し"], "category": "SMGoods", "label": "SMグッズ", "service": "mono", "floor": "goods"},
    "couple": {"keywords": ["カップル", "ペア", "二人用"], "category": "Couple", "label": "カップル", "service": "mono", "floor": "goods"},
    "new_goods": {"keywords": ["新商品", "新作", "話題"], "category": "NewGoods", "label": "新商品", "service": "mono", "floor": "goods"},
}


class Config:
    """アプリケーション設定クラス"""

    # DMM API認証情報
    API_ID: str = os.getenv("API_ID", "")
    AFFILIATE_ID: str = os.getenv("AFFILIATE_ID", "")
    SITE_NAME: str = os.getenv("SITE_NAME", "goods-lab")

    # APIエンドポイント
    API_BASE_URL: str = "https://api.dmm.com/affiliate/v3/ItemList"

    # Hugo出力設定
    CONTENT_DIR: str = str(_project_root / "content" / "posts")

    # 記事生成のデフォルト設定
    DEFAULT_HITS: int = 5
    DEFAULT_SERVICE: str = "mono"
    DEFAULT_FLOOR: str = "goods"
    DEFAULT_SORT: str = "date"

    @classmethod
    def validate(cls) -> bool:
        """必須設定が存在するか検証する"""
        missing = []
        if not cls.API_ID:
            missing.append("API_ID")
        if not cls.AFFILIATE_ID:
            missing.append("AFFILIATE_ID")
        if missing:
            print(f"[エラー] 以下の環境変数が未設定です: {', '.join(missing)}")
            print("  .envファイルを作成するか、環境変数を設定してください。")
            return False
        return True
