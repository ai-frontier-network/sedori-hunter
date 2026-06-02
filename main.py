import os
import json
import re
import time
import random
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------
# 1. 相場データベース (data.json) の初期化・読み込み
# ---------------------------------------------------------------------
DEFAULT_DB = {
    "market_prices": {
        "フルラ 財布": {
            "condition_excellent": 11000,  # 未使用に近い
            "condition_good": 5500,        # やや傷や汚れあり
            "shipping_fee_est": 370
        },
        "エルメス シューズ": {
            "condition_excellent": 45000,
            "condition_good": 22000,
            "shipping_fee_est": 850
        },
        "オールドコーチ": {
            "condition_excellent": 18000,  # ヴィンテージ品のため良好品は高値
            "condition_good": 8500,
            "shipping_fee_est": 750
        },
        "ゲンテン カットワーク": {
            "condition_excellent": 25000,  # ファンが多く高値で取引される
            "condition_good": 12000,
            "shipping_fee_est": 750
        }
    }
}

def load_database():
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_DB

db = load_database()

# ---------------------------------------------------------------------
# 2. ヤフオク時間パース関数
# ---------------------------------------------------------------------
def parse_yahoo_time(time_text):
    if not time_text:
        return 9999
    minutes = 0
    days = re.search(r'(\d+)日', time_text)
    hours = re.search(r'(\d+)時間', time_text)
    mins = re.search(r'(\d+)分', time_text)
    if days:
        minutes += int(days.group(1)) * 1440
    if hours:
        minutes += int(hours.group(1)) * 60
    if mins:
        minutes += int(mins.group(1))
    if minutes == 0 and ("分" in time_text or "秒" in time_text or "すぐ" in time_text):
        return 1
    return minutes if minutes > 0 else 9999

# ---------------------------------------------------------------------
# 3. 利益計算ロジック（期待値算出エンジン）
# ---------------------------------------------------------------------
def calculate_profit(item, db_entry, keyword):
    title = item["title"]
    price = item["current_price"]
    
    # タイトルから状態を推測（擬似コンディション判定）
    is_excellent = any(word in title for word in ["未使用", "極美品", "新品", "デッドストック", "Sランク", "美品"])
    
    if is_excellent:
        m_price = db_entry["condition_excellent"]
        cond_label = "未使用に近い (想定)"
    else:
        m_price = db_entry["condition_good"]
        cond_label = "やや傷や汚れあり (想定)"
        
    # メルカリ販売手数料（10%）
    mercari_fee = int(m_price * 0.10)
    # メルカリ送料
    m_shipping = db_entry["shipping_fee_est"]
    # ヤフオクから自宅への送料（目安）
    y_shipping = 500 if "財布" in keyword else 1000
    
    net_revenue = m_price - mercari_fee - m_shipping
    total_cost = price + y_shipping
    expected_profit = net_revenue - total_cost
    
    if expected_profit >= 5000:
        stars = "★★★★★"
    elif expected_profit >= 3000:
        stars = "★★★★☆"
    elif expected_profit >= 1000:
        stars = "★★★☆☆"
    else:
        stars = "★★☆☆☆"
        
    return {
        "title": title,
        "url": item["url"],
        "price_formatted": f"{price:,}円",
        "profit_formatted": f"{expected_profit:,}円",
        "expected_profit": expected_profit,
        "stars": stars,
        "condition": cond_label,
        "remaining_time": item["remaining_time"],
        "img_url": item["img_url"],
        "target_m_price": f"{m_price:,}円",
        "time_m": item["time_m"]
    }

# ---------------------------------------------------------------------
# 4. メイン処理（Playwright 1起動で巡回するお行儀仕様）
# ---------------------------------------------------------------------
def main():
    all_bargains = []
    
    print("🚀 お行儀エチケット対応クローラーを起動します...")
    
    with sync_playwright() as p:
        # ブラウザは1回だけ立ち上げる
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # 各キーワードを同じブラウザで巡回
        for i, (kw, entry) in enumerate(db["market_prices"].items()):
            # 2つ目以降のキーワードの前に、人間らしいランダムな間隔（3〜7秒）を空ける
            if i > 0:
                sleep_time = random.uniform(3.0, 7.0)
                print(f"💤 サーバー負荷軽減のため、{sleep_time:.1f}秒待機します...")
                time.sleep(sleep_time)
                
            print(f"🔍 {kw} のヤフオクストア巡回を開始します...")
            
            encoded_kw = urllib.parse.quote(kw)
            url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_kw}&is_store=1&istatus=1&istatus=3&istatus=4&istatus=5&price_type=currentprice&s1=end&o1=a"
            
            try:
                page.goto(url, timeout=45000)
                page.wait_for_timeout(3000) # ページ読み込み後の余韻（3秒）
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                products = soup.select(".Product")
                
                scraped_count = 0
                for product in products[:30]:
                    try:
                        title_el = product.select_one(".Product__titleLink")
                        if not title_el:
                            continue
                        title = title_el.text.strip()
                        item_url = title_el.get("href")
                        
                        price_text = product.select_one(".Product__priceValue").text
                        price = int(re.sub(r'[^\d]', '', price_text))
                        
                        time_text = product.select_one(".Product__time").text.strip()
                        time_m = parse_yahoo_time(time_text)
                        
                        if time_m > 1440:  # 24時間以内
                            continue
                            
                        img_el = product.select_one(".Product__imageData")
                        img_url = img_el.get("src") if img_el else ""
                        
                        item_data = {
                            "title": title,
                            "url": item_url,
                            "current_price": price,
                            "remaining_time": time_text,
                            "img_url": img_url,
                            "time_m": time_m
                        }
                        
                        result = calculate_profit(item_data, entry, kw)
                        if result["expected_profit"] >= 1000:
                            result["keyword"] = kw
                            all_bargains.append(result)
                            scraped_count += 1
                            
                    except Exception:
                        continue
                        
                print(f"   -> 利益対象商品が {scraped_count} 件見つかりました")
                
            except Exception as e:
                print(f"❌ {kw} の検索中にエラーが発生しました: {e}")
                
        browser.close()

    # 利益順に並び替え
    all_bargains.sort(key=lambda x: x["expected_profit"], reverse=True)
    
    # JSONデータベースとして保存
    db["last_update"] = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    db["latest_results"] = all_bargains
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        
    # --- HTML 生成テンプレート ---
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Frontier Sedori OS - お宝自動検知</title>
    <style>
        :root {
            --bg-color: #fafaf9;
            --card-bg: #ffffff;
            --text-color: #1c1917;
            --text-muted: #78716c;
            --accent-color: #e11d48;
            --border-color: #e7e5e4;
            --star-color: #f59e0b;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }
        header {
            background-color: #0f172a;
            color: white;
            padding: 30px 20px;
            text-align: center;
            border-bottom: 3px solid var(--accent-color);
        }
        header h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 800;
        }
        header p {
            margin: 10px 0 0;
            font-size: 0.95rem;
            color: #cbd5e1;
        }
        .container {
            max-width: 1000px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .update-time {
            text-align: right;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 20px;
        }
        .filter-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .filter-btn {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 999px;
            cursor: pointer;
            font-weight: 700;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }
        .filter-btn.active, .filter-btn:hover {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05);
            display: flex;
            flex-direction: column;
            transition: transform 0.2s ease;
        }
        .card:hover {
            transform: translateY(-4px);
        }
        .card-img-wrapper {
            position: relative;
            background-color: #f5f5f4;
            height: 200px;
            text-align: center;
        }
        .card-img {
            max-height: 100%;
            max-width: 100%;
            object-fit: contain;
            margin: 0 auto;
        }
        .badge {
            position: absolute;
            top: 10px;
            left: 10px;
            background-color: var(--accent-color);
            color: white;
            padding: 4px 8px;
            font-size: 0.75rem;
            font-weight: 800;
            border-radius: 4px;
        }
        .card-body {
            padding: 20px;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
        }
        .stars {
            color: var(--star-color);
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }
        .title {
            font-size: 0.95rem;
            font-weight: 700;
            margin: 0 0 15px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 3rem;
        }
        .metrics {
            margin-top: auto;
            border-top: 1px dashed var(--border-color);
            padding-top: 15px;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            margin-bottom: 6px;
        }
        .metric-label {
            color: var(--text-muted);
        }
        .metric-val {
            font-weight: 700;
        }
        .profit {
            font-size: 1.2rem;
            color: var(--accent-color);
            font-weight: 800;
        }
        .btn-link {
            display: block;
            background-color: #0f172a;
            color: white;
            text-align: center;
            text-decoration: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: 700;
            margin-top: 15px;
            font-size: 0.9rem;
            transition: opacity 0.2s ease;
        }
        .btn-link:hover {
            opacity: 0.9;
        }
        .no-data {
            text-align: center;
            padding: 40px;
            color: var(--text-muted);
            grid-column: 1 / -1;
        }
        footer {
            text-align: center;
            padding: 40px 20px;
            font-size: 0.8rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            margin-top: 60px;
        }
    </style>
</head>
<body>
    <header>
        <h1>AI Frontier Sedori OS</h1>
        <p>生活防衛・自立支援のための、高利益期待お宝自動検知プラットフォーム</p>
    </header>
    
    <div class="container">
        <div class="update-time">最終更新: {{last_update}}</div>
        
        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterItems('all')">すべて表示</button>
            <button class="filter-btn" onclick="filterItems('フルラ 財布')">フルラ 財布</button>
            <button class="filter-btn" onclick="filterItems('エルメス シューズ')">エルメス シューズ</button>
            <button class="filter-btn" onclick="filterItems('オールドコーチ')">オールドコーチ</button>
            <button class="filter-btn" onclick="filterItems('ゲンテン カットワーク')">ゲンテン カットワーク</button>
        </div>
        
        <div class="grid" id="item-grid">
            {% if bargains %}
                {% for item in bargains %}
                <div class="card" data-keyword="{{item.keyword}}">
                    <div class="card-img-wrapper">
                        <span class="badge">{{item.keyword}}</span>
                        <img class="card-img" src="{{item.img_url}}" alt="商品画像" onerror="this.src='https://placehold.co/300x200?text=No+Image'">
                    </div>
                    <div class="card-body">
                        <div class="stars">{{item.stars}}</div>
                        <h3 class="title">{{item.title}}</h3>
                        
                        <div class="metrics">
                            <div class="metric-row">
                                <span class="metric-label">残り時間</span>
                                <span class="metric-val" style="color: #059669;">{{item.remaining_time}}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">ヤフオク現在価格</span>
                                <span class="metric-val">{{item.price_formatted}}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">メルカリ想定相場</span>
                                <span class="metric-val">{{item.target_m_price}}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">推測される状態</span>
                                <span class="metric-val">{{item.condition}}</span>
                            </div>
                            <div class="metric-row" style="margin-top: 10px; border-top: 1px solid var(--border-color); padding-top: 10px;">
                                <span class="metric-label" style="font-size: 1rem; font-weight: 800; color: var(--accent-color);">利益期待値</span>
                                <span class="profit">{{item.profit_formatted}}</span>
                            </div>
                        </div>
                        
                        <a href="{{item.url}}" target="_blank" class="btn-link">ヤフオクで商品を見る &rarr;</a>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-data">現在、基準を満たすお得な案件はありません。次回の巡回をお待ちください。</div>
            {% endif %}
        </div>
    </div>
    
    <footer>
        <p>© 2026 AI Frontier Sedori OS. Powered by cocoro-brand.</p>
    </footer>

    <script>
        function filterItems(keyword) {
            const cards = document.querySelectorAll('.card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // ボタンのアクティブ状態を切り替え
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            cards.forEach(card => {
                if (keyword === 'all' || card.getAttribute('data-keyword') === keyword) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>"""

    # Jinja2 を使ってデータを埋め込み、HTMLを生成
    from jinja2 import Template
    template = Template(html_template)
    rendered_html = template.render(
        last_update=db["last_update"],
        bargains=all_bargains
    )
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(rendered_html)
        
    print("✅ index.html のビルドが正常に完了しました！")

if __name__ == "__main__":
    main()
