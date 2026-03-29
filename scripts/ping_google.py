"""Google にサイトマップ更新を通知する"""

import requests

SITEMAP = "https://musclelove-777.github.io/goods-lab/sitemap.xml"

r = requests.get(f"https://www.google.com/ping?sitemap={SITEMAP}", timeout=10)
print(f"Google Ping: {r.status_code}")
