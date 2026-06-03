import os
import json
import re
import time
import random
import urllib.parse
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# =====================================================================
# 👑 Google AdSense 設定（デグレ防止）
# =====================================================================
ADSENSE_PUBLISHER_ID = "ca-pub-2908004621823900"  # ちゃろさんのパブリッシャーID
ADSENSE_SLOT_ID = "3799886389"                    # インフィード広告等のスロットID

# ---------------------------------------------------------------------
# 1. 究極せどり相場・カテゴリデータベース (自動修復機能付き)
# ---------------------------------------------------------------------
DEFAULT_DB = {
    "market_prices": {
        # --- ミドルブランド & 財布・バッグ系 ---
        "フルラ 財布": {
            "category": "wallet",
            "condition_excellent": 11000,
            "condition_good": 5500,
            "shipping_fee_est": 370
        },
        "フルラ バッグ": {
            "category": "bag",
            "condition_excellent": 14000,
            "condition_good": 7500,
            "shipping_fee_est": 850
        },
        "オールドコーチ": {
            "category": "bag",
            "condition_excellent": 18000,
            "condition_good": 9500,
            "shipping_fee_est": 850
        },
        "ゲンテン カットワーク": {
            "category": "bag",
            "condition_excellent": 25000,
            "condition_good": 12000,
            "shipping_fee_est": 850
        },
        "坂本これくしょん": {
            "category": "bag",
            "condition_excellent": 15000,
            "condition_good": 9000,
            "shipping_fee_est": 850
        },
        "コーチ 財布": {
            "category": "wallet",
            "condition_excellent": 8000,
            "condition_good": 4000,
            "shipping_fee_est": 370
        },
        "ポールスミス 財布": {
            "category": "wallet",
            "condition_excellent": 12000,
            "condition_good": 6000,
            "shipping_fee_est": 370
        },
        "マイケルコース バッグ": {
            "category": "bag",
            "condition_excellent": 12000,
            "condition_good": 6000,
            "shipping_fee_est": 850
        },
        "ケイトスペード バッグ": {
            "category": "bag",
            "condition_excellent": 10000,
            "condition_good": 5000,
            "shipping_fee_est": 850
        },
        "トリーバーチ バッグ": {
            "category": "bag",
            "condition_excellent": 18000,
            "condition_good": 9500,
            "shipping_fee_est": 850
        },
        "マークジェイコブス バッグ": {
            "category": "bag",
            "condition_excellent": 15000,
            "condition_good": 8000,
            "shipping_fee_est": 850
        },
        "アニエスベー がま口": {
            "category": "wallet",
            "condition_excellent": 9500,
            "condition_good": 5000,
            "shipping_fee_est": 370
        },
        
        # --- 👠 レディース靴ブランド（目標サイズ: 22.5cm〜24.5cm） ---
        "シャネル サンダル パンプス": {
            "category": "shoes_ladies",
            "condition_excellent": 48000,
            "condition_good": 25000,
            "shipping_fee_est": 850
        },
        "エルメス シューズ サンダル": {
            "category": "shoes_ladies",
            "condition_excellent": 55000,
            "condition_good": 28000,
            "shipping_fee_est": 850
        },
        "ルイヴィトン スニーカー サンダル": {
            "category": "shoes_ladies",
            "condition_excellent": 65000,
            "condition_good": 32000,
            "shipping_fee_est": 850
        },
        "グッチ スニーカー シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 42000,
            "condition_good": 20000,
            "shipping_fee_est": 850
        },
        "フェラガモ パンプス シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 15000,
            "condition_good": 8000,
            "shipping_fee_est": 850
        },
        "ダイアナ パンプス ブーツ": {
            "category": "shoes_ladies",
            "condition_excellent": 8000,
            "condition_good": 4000,
            "shipping_fee_est": 850
        },
        "プラダ スニーカー シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 55000,
            "condition_good": 28000,
            "shipping_fee_est": 850
        },
        "ディオール スニーカー シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 70000,
            "condition_good": 35000,
            "shipping_fee_est": 850
        },
        "ボッテガヴェネタ シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 60000,
            "condition_good": 30000,
            "shipping_fee_est": 850
        },
        "クリスチャンルブタン シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 65000,
            "condition_good": 32000,
            "shipping_fee_est": 850
        },
        "ロエベ シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 55000,
            "condition_good": 28000,
            "shipping_fee_est": 850
        },
        "サンローラン シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 50000,
            "condition_good": 25000,
            "shipping_fee_est": 850
        },
        "ミュウミュウ シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 45000,
            "condition_good": 22000,
            "shipping_fee_est": 850
        },
        "セリーヌ シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 48000,
            "condition_good": 24000,
            "shipping_fee_est": 850
        },
        "バレンシアガ スニーカー": {
            "category": "shoes_ladies",
            "condition_excellent": 52000,
            "condition_good": 26000,
            "shipping_fee_est": 850
        },
        "ペリーコ シューズ パンプス": {
            "category": "shoes_ladies",
            "condition_excellent": 12000,
            "condition_good": 6000,
            "shipping_fee_est": 850
        },
        "ドルチェガッバーナ シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 20000,
            "condition_good": 10000,
            "shipping_fee_est": 850
        },
        "マイケルコース シューズ": {
            "category": "shoes_ladies",
            "condition_excellent": 10000,
            "condition_good": 5000,
            "shipping_fee_est": 850
        },

        # --- 👞 メンズ靴ブランド（目標サイズ: 27.0cm〜28.5cm） ---
        "リーガル ローファー ビジネス": {
            "category": "shoes_mens",
            "condition_excellent": 12000,
            "condition_good": 6500,
            "shipping_fee_est": 850
        },
        "ドクターマーチン ブーツ 3ホール": {
            "category": "shoes_mens",
            "condition_excellent": 14000,
            "condition_good": 7500,
            "shipping_fee_est": 850
        },
        "レッドウィング ブーツ": {
            "category": "shoes_mens",
            "condition_excellent": 28000,
            "condition_good": 15000,
            "shipping_fee_est": 850
        },
        "コールハーン シューズ": {
            "category": "shoes_mens",
            "condition_excellent": 15000,
            "condition_good": 8000,
            "shipping_fee_est": 850
        },
        "ティンバーランド ブーツ": {
            "category": "shoes_mens",
            "condition_excellent": 12000,
            "condition_good": 6500,
            "shipping_fee_est": 850
        },
        "ナイキ スニーカー": {
            "category": "shoes_mens",
            "condition_excellent": 10000,
            "condition_good": 5500,
            "shipping_fee_est": 850
        },
        "アディダス スニーカー": {
            "category": "shoes_mens",
            "condition_excellent": 9000,
            "condition_good": 5000,
            "shipping_fee_est": 850
        },
        "ニューバランス スニーカー": {
            "category": "shoes_mens",
            "condition_excellent": 10000,
            "condition_good": 5500,
            "shipping_fee_est": 850
        },
        "コンバース スニーカー": {
            "category": "shoes_mens",
            "condition_excellent": 8000,
            "condition_good": 4500,
            "shipping_fee_est": 850
        }
    }
}

# 致命的な状態を示す除外NGパターン（修理品・補修はバッジ警告運用のため削除）
NG_PATTERNS = [
    r'部品', r'空箱', r'箱のみ', r'保存袋', r'確認用',
    r'replica', r'レプリカ', r'コピー', r'非売品',
    r'ソール.*破れ', r'ソール.*穴', r'ソール.*亀裂',
    r'穴あり', r'破れあり', r'亀裂あり',
    r'ドライビングシューズ', r'ジャンク', r'難あり',
    r'インソール.*型崩れ', r'踵.*型崩れ', r'かかと.*型崩れ',
    r'黄ばみ.*ひどい', r'カビ',
    r'型崩れ'  # 致命的な型崩れはNGに残します
]

def load_database():
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            # データ構造の安全検査と自己修復
            if "market_prices" in loaded:
                for kw, entry in DEFAULT_DB["market_prices"].items():
                    if kw in loaded["market_prices"]:
                        if "category" not in loaded["market_prices"][kw]:
                            loaded["market_prices"][kw]["category"] = entry["category"]
                        for key in ["condition_excellent", "condition_good", "shipping_fee_est"]:
                            if key not in loaded["market_prices"][kw]:
                                loaded["market_prices"][kw][key] = entry[key]
                    else:
                        loaded["market_prices"][kw] = entry
            else:
                loaded["market_prices"] = DEFAULT_DB["market_prices"]
                
            return loaded
        except Exception as e:
            print(f"⚠️ データベース修復警告: {e}")
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
# 3. 👠 高度なサイズ判定エンジン
# ---------------------------------------------------------------------
def check_shoe_size_ok(title, category):
    if category not in ["shoes_ladies", "shoes_mens"]:
        return True, "判定不要"
        
    # 🔴 センチ表記（cm、センチ）が明示されている場合のみマッチ（年号や価格の誤除外防止）(新問題②対策)
    size_cm = re.search(r'(\d{2}(?:\.\d)?)\s*(?:cm|センチ)', title)
    size_eu = re.search(r'(?:サイズ|EU|US|UK)\s*(\d{2}(?:\.\d)?)', title, re.IGNORECASE)
    
    detected_size = None
    if size_cm:
        detected_size = float(size_cm.group(1))
    elif size_eu:
        eu_val = float(size_eu.group(1))
        if eu_val >= 35 and eu_val <= 45:
            if eu_val < 40:
                detected_size = eu_val - 13.5
            else:
                detected_size = eu_val - 15.0

    if not detected_size:
        return True, "サイズ未検出（要目視）"
        
    if category == "shoes_ladies":
        if 22.5 <= detected_size <= 24.5:
            return True, f"{detected_size}cm (L判OK)"
        else:
            return False, f"{detected_size}cm (L判対象外)"
            
    elif category == "shoes_mens":
        if 27.0 <= detected_size <= 28.5:
            return True, f"{detected_size}cm (M判OK)"
        else:
            return False, f"{detected_size}cm (M判対象外)"
            
    return True, "判定保留"

# ---------------------------------------------------------------------
# 4. 🕵️ 2段階潜入調査ロジック（100%ストア確定 ＆ 正確な状態取得）
# ---------------------------------------------------------------------
def verify_store_and_get_condition(page, product_url):
    try:
        page.goto(product_url, timeout=20000, wait_until="domcontentloaded")
        time.sleep(1.0)  # 🔴 wait_for_timeoutを安全な time.sleep(1.0) に全置換 (バグ①対策)
        
        content = page.content()
        
        # 検証A: ストア確定の厳格検証
        is_store = False
        if '"isStore":"1"' in content or '"isStore":true' in content or '"isStore":1' in content:
            is_store = True
        elif 'data-seller-type="store"' in content or 'StoreLabel' in content or 'gv-Label--trust' in content or 'ストアアカウント' in content or 'store.shopping.yahoo.co.jp' in content:
            is_store = True
            
        if not is_store:
            return False, None, None
            
        # 検証B: 正確な「商品の状態」を判別
        exact_condition = "やや傷や汚れあり"
        condition_type = "good"
        
        # 🔴 長い文字列である「未使用に近い」を最優先で探索するように順番を修正 (潜在問題①対策)
        if any(x in content for x in ["未使用に近い", "未使用", "新品", "Sランク", "展示品"]):
            exact_condition = "未使用に近い"
            condition_type = "excellent"
        elif "目立った傷や汚れなし" in content:
            exact_condition = "目立った傷や汚れなし"
            condition_type = "good"
        elif "やや傷や汚れあり" in content:
            exact_condition = "やや傷や汚れあり"
            condition_type = "good"
        elif "傷や汚れあり" in content:
            exact_condition = "傷や汚れあり"
            condition_type = "good"
            
        return True, exact_condition, condition_type
        
    except Exception as e:
        print(f"個別ページ検証エラー ({product_url}): {e}")
        return False, None, None

# ---------------------------------------------------------------------
# 5. 📈 【深夜限定】落札相場の実勢自動更新エンジン (closedsearch完全対応)
# ---------------------------------------------------------------------
def update_market_prices_from_sold(page, db_obj):
    print("📈 落札相場の自動更新を開始します...")
    
    for kw, entry in db_obj["market_prices"].items():
        try:
            encoded_kw = urllib.parse.quote(kw)
            # 🔴 落札結果専用の closedsearch URL へ完全置換 (バグ③対策)
            url = f"https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_kw}&is_store=1&s1=end&o1=d&n=20"
            
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            time.sleep(2.0)  # 🔴 time.sleep に統一
            
            soup = BeautifulSoup(page.content(), "html.parser")
            prices = []
            for product in soup.select(".Product"):
                price_el = product.select_one(".Product__priceValue")
                if price_el:
                    price = int(re.sub(r'[^\d]', '', price_el.text))
                    if price > 500:  # 異常安値を除外
                        prices.append(price)
            
            if len(prices) >= 5:
                prices.sort()
                trim = max(1, len(prices) // 5)
                trimmed = prices[trim:-trim]
                if len(trimmed) > 0:
                    median_price = int(sum(trimmed) / len(trimmed))
                    current = entry["condition_good"]
                    # 相場の急激な暴走を防ぐ±50%安全弁
                    if 0.5 <= median_price / current <= 2.0:
                        db_obj["market_prices"][kw]["condition_good"] = median_price
                        db_obj["market_prices"][kw]["condition_excellent"] = int(median_price * 1.8)
                        print(f"   ✅ {kw}: {current:,}円 → {median_price:,}円 に自動学習更新しました")
                    else:
                        print(f"   ⚠️ {kw}: データ乖離過大のためスキップ（取得値: {median_price:,}円）")
            
            time.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            print(f"   ❌ {kw} の相場データ取得に失敗: {e}")
            continue
            
    db_obj["price_last_update"] = datetime.now(timezone(timedelta(hours=9))).strftime("%Y年%m月%d日 %H:%M")
    print("📈 相場データの自己学習更新が正常完了しました！")
    return db_obj

# ---------------------------------------------------------------------
# 6. 📊 利益計算ロジック（ダブル送料・手数料・ホワイトスニーカー対応）
# ---------------------------------------------------------------------
def calculate_profit(item, db_entry, keyword, condition_type, condition_label):
    title = item["title"]
    price = item["current_price"]
    category = db_entry["category"]
    
    if condition_type == "excellent":
        m_price = db_entry["condition_excellent"]
    else:
        m_price = db_entry["condition_good"]
        
    # 🔴 「白」の誤検知フィルター搭載（面白い・告白等の無関係な単語を完全除外） (潜在問題②対策)
    WHITE_NOISE_WORDS = ["面白い", "面白", "告白", "白木屋", "白川", "白紙", "余白", "白黒"]
    is_white_sneaker = any(w in title for w in ["ホワイト", "WHITE", "white", "オールホワイト", "白色"])
    if not is_white_sneaker and "白" in title:
        # ノイズワードが含まれない場合のみ安全にTrueにする (新バグ①対策)
        if not any(noise in title for noise in WHITE_NOISE_WORDS):
            is_white_sneaker = True
        
    if is_white_sneaker and ("スニーカー" in keyword or "シューズ" in keyword or "靴" in keyword):
        m_price = int(m_price * 1.1)
        
    mercari_fee = int(m_price * 0.10)
    m_shipping = db_entry["shipping_fee_est"]
    y_shipping = 500 if category == "wallet" else 1000
    
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
        
    # 「やや傷や汚れあり」「傷や汚れあり」は、目視確認を促すフラグを立てる
    needs_photo_check = condition_label in ["やや傷や汚れあり", "傷や汚れあり"]
    
    # 🔴 【改善4】「ソール修復・裏張り・リペア・補修・修理品」バッジ警告運用（新問題①対策・マージ）
    needs_sole_warning = any(w in title for w in ["ソール張り替え", "裏張り", "ソールリペア", "リペア", "補修", "修理品", "ハーフソール"])
    
    return {
        "title": title,
        "url": item["url"],
        "price_formatted": f"{price:,}円",
        "profit_formatted": f"{expected_profit:,}円",
        "expected_profit": expected_profit,
        "stars": stars,
        "condition": condition_label,
        "remaining_time": item["remaining_time"],
        "img_url": item["img_url"],
        "target_m_price": f"{m_price:,}円",
        "time_m": item["time_m"],
        "needs_photo_check": needs_photo_check,
        "is_white_sneaker": is_white_sneaker,
        "needs_sole_warning": needs_sole_warning
    }

# ---------------------------------------------------------------------
# 7. メイン巡回処理（2段階検証・お行儀＆高速化ハイブリッド仕様）
# ---------------------------------------------------------------------
def main():
    global db
    all_bargains = []
    
    print("🚀 【せどりAI OS 究極完全版】お宝検知エンジンを起動します...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # 🔴 UTC基準による確実な深夜判定へ修正 (バグ②対策)
        # JST 23:30 (夜間巡回) ＝ UTC 14:30 
        now_utc = datetime.now(timezone.utc)
        current_hour_utc = now_utc.hour
        print(f"⏰ 現在のUTC時刻: {now_utc.strftime('%H:%M:%S')} (Hour UTC: {current_hour_utc})")
        if 14 <= current_hour_utc <= 16:
            db = update_market_prices_from_sold(page, db)
        
        for i, (kw, entry) in enumerate(db["market_prices"].items()):
            if i > 0:
                sleep_time = random.uniform(2.0, 4.0)
                print(f"💤 サーバー負荷軽減のため、{sleep_time:.1f}秒待機します...")
                time.sleep(sleep_time)
                
            print(f"🔍 {kw} のヤフオク巡回を開始します...")
            
            encoded_kw = urllib.parse.quote(kw)
            url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_kw}&is_store=1&store=1&istatus=1&istatus=3&istatus=4&istatus=5&price_type=currentprice&s1=end&o1=a"
            
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(1.5)  # 🔴 wait_for_timeoutを安全な time.sleep(1.5) に置換 (バグ①対策)
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                products = soup.select(".Product")
                
                initial_candidates = []
                for product in products[:15]:
                    try:
                        title_el = product.select_one(".Product__titleLink")
                        if not title_el:
                            continue
                        title = title_el.text.strip()
                        
                        # 1次フィルター: NGワードの排除
                        if any(re.search(p, title, re.IGNORECASE) for p in NG_PATTERNS):
                            continue
                            
                        # 2次フィルター: 靴サイズフィルターの事前審査
                        size_ok, size_info = check_shoe_size_ok(title, entry["category"])
                        if not size_ok:
                            continue
                            
                        item_url = title_el.get("href")
                        price_text = product.select_one(".Product__priceValue").text
                        price = int(re.sub(r'[^\d]', '', price_text))
                        
                        time_text = product.select_one(".Product__time").text.strip()
                        time_m = parse_yahoo_time(time_text)
                        
                        if time_m > 1440:  # 24時間以内
                            continue
                            
                        img_el = product.select_one(".Product__imageData")
                        img_url = img_el.get("src") if img_el else ""
                        
                        initial_candidates.append({
                            "title": title,
                            "url": item_url,
                            "current_price": price,
                            "remaining_time": time_text,
                            "img_url": img_url,
                            "time_m": time_m,
                            "size_info": size_info
                        })
                    except Exception:
                        continue
                
                # 🔍 【個別ページ詳細潜入調査】
                scraped_count = 0
                for item in initial_candidates:
                    is_valid_store, exact_condition, cond_type = verify_store_and_get_condition(page, item["url"])
                    
                    if not is_valid_store:
                        continue
                        
                    result = calculate_profit(item, entry, kw, cond_type, exact_condition)
                    
                    if result["expected_profit"] >= 1500:
                        result["keyword"] = kw
                        if "判" in item["size_info"]:
                            result["condition"] += f" / サイズ: {item['size_info']}"
                        all_bargains.append(result)
                        scraped_count += 1
                        
                    time.sleep(0.5)
                    
                print(f"   -> ストア確定 ＆ 基準合致商品を {scraped_count} 件検知しました")
                
            except Exception as e:
                print(f"❌ {kw} の検索中にエラーが発生しました: {e}")
                
        browser.close()

    # 利益額順に並び替え
    all_bargains.sort(key=lambda x: x["expected_profit"], reverse=True)
    
    # JSONデータベースとして保存
    db["last_update"] = datetime.now(timezone(timedelta(hours=9))).strftime("%Y年%m月%d日 %H:%M")
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
    
    <!-- 👑 Google AdSense 自動広告 -->
    {% if adsense_id %}
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{adsense_id}}" crossorigin="anonymous"></script>
    {% endif %}

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
        .adsense-container {
            grid-column: 1 / -1;
            text-align: center;
            margin: 20px 0;
            min-height: 100px;
            width: 100%;
        }

        /* 👑 イントロダクション（説明文）カードのデザイン */
        .intro-box {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        }
        .intro-box h2 {
            margin-top: 0;
            font-size: 1.3rem;
            color: #0f172a;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 8px;
            font-weight: 800;
        }
        .intro-box p {
            font-size: 0.95rem;
            color: var(--text-color);
            margin-bottom: 20px;
            text-align: justify;
        }
        .intro-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        @media (max-width: 768px) {
            .intro-grid {
                grid-template-columns: 1fr;
            }
        }
        .intro-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px;
        }
        .intro-card h3 {
            margin-top: 0;
            font-size: 1.05rem;
            color: #0f172a;
            font-weight: 700;
        }
        .intro-card ul, .intro-card ol {
            margin: 0;
            padding-left: 20px;
            font-size: 0.88rem;
            color: #334155;
            line-height: 1.7;
        }
        .intro-card li {
            margin-bottom: 8px;
        }
        .intro-card li:last-child {
            margin-bottom: 0;
        }
        
    </style>
</head>
<body>
    <header>
        <h1>AI Frontier Sedori OS</h1>
        <p>高利益期待お宝自動検知プラットフォーム</p>
    </header>
    
    <div class="container">
        <div class="update-time">最終更新: {{last_update}}</div>

        <!-- 👑 イントロダクション（説明文）ブロック -->
        <div class="intro-box">
            <h2>✨ AI Frontier Sedori OS へようこそ！</h2>
            <p>このサイトは、24時間完全自動のお宝検知サイトです。維持費0円の最強インフラ（GHC × 独自ロジック）で稼働しています。</p>
            
            <div class="intro-grid">
                <div class="intro-card">
                    <h3>💡 このサイトのメリット</h3>
                    <ul>
                        <li><strong>ストア限定：</strong> トラブルや偽物のリスクが多い個人出品を完璧に排除。安全な「ストアアカウント」の優良案件のみを厳選。</li>
                        <li><strong>ダブル送料＆手数料を自動計算：</strong> メルカリ手数料（10%）と、ダブル送料（ヤフオク仕入れ送料＋メルカリ発送送料）をあらかじめ自動で差し引いて、純粋な「手取り期待利益」を算出しています！</li>
                        <li><strong>サイズ＆致命的欠陥の除外：</strong> 最も売れやすい「ゴールデンサイズ」のみを自動判定。ソール破れやカビなどのジャンク品は1次フィルターで徹底除外します。</li>
                        <li><strong>お助け警告バッジ：</strong> 「📸要写真確認」「⭐ホワイト人気」「⚠️ソール補修/裏張」を自動解析して表示します。</li>
                    </ul>
                </div>
                
                <div class="intro-card">
                    <h3>⚠️ ご利用時の注意点</h3>
                    <ul>
                        <li><strong>相場は「目安」です：</strong> 表示されているメルカリ想定相場は、ヤフオクの過去の落札履歴（closedsearch）から実勢データを深夜に自動取得して補正した「目安の相場」です。実際の仕入れ時はリンク先からメルカリの現状もお確かめください。</li>
                        <li><strong>最後は人の目で！：</strong> ヤフオクストアはクレーム防止のために状態を低く（やや汚れあり等）申告することが多いです。「📸要写真確認」バッジを目印に、実物が綺麗な状態であれば大チャンスです！</li>
                    </ul>
                </div>
            </div>

            <div class="intro-card" style="margin-top: 15px; background: #0f172a; color: white;">
                <h3 style="color: white; margin-top:0; margin-bottom: 10px;">🎯 かんたん3ステップの使い方</h3>
                <ol style="margin-bottom:0; padding-left:20px; color: #cbd5e1;">
                    <li>下の<strong>「フィルターボタン」</strong>を押して、得意なブランドを絞り込みます。</li>
                    <li>利益期待値が高く、星マーク（★★★★★）が多いお宝商品を探します。</li>
                    <li>「ヤフオクで商品を見る」ボタンを押し、写真を確認して綺麗な状態であれば仕入れを行い、メルカリで販売します！</li>
                </ol>
            </div>
        </div>
      
        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterItems('all')">すべて表示</button>
            <button class="filter-btn" onclick="filterItems('フルラ 財布')">フルラ 財布</button>
            <button class="filter-btn" onclick="filterItems('フルラ バッグ')">フルラ バッグ</button>
            <button class="filter-btn" onclick="filterItems('オールドコーチ')">オールドコーチ</button>
            <button class="filter-btn" onclick="filterItems('ゲンテン カットワーク')">ゲンテン</button>
            <button class="filter-btn" onclick="filterItems('坂本これくしょん')">坂本これくしょん</button>
            <button class="filter-btn" onclick="filterItems('エルメス シューズ サンダル')">エルメス靴</button>
            <button class="filter-btn" onclick="filterItems('シャネル サンダル パンプス')">シャネル靴</button>
            <button class="filter-btn" onclick="filterItems('ルイヴィトン スニーカー サンダル')">ヴィトン靴</button>
            <button class="filter-btn" onclick="filterItems('グッチ スニーカー シューズ')">グッチ靴</button>
            <button class="filter-btn" onclick="filterItems('プラダ スニーカー シューズ')">プラダ靴</button>
            <button class="filter-btn" onclick="filterItems('ディオール スニーカー シューズ')">ディオール靴</button>
            <button class="filter-btn" onclick="filterItems('ボッテガヴェネタ シューズ')">ボッテガ靴</button>
            <button class="filter-btn" onclick="filterItems('クリスチャンルブタン シューズ')">ルブタン靴</button>
            <button class="filter-btn" onclick="filterItems('ロエベ シューズ')">ロエベ靴</button>
            <button class="filter-btn" onclick="filterItems('サンローラン シューズ')">サンローラン靴</button>
            <button class="filter-btn" onclick="filterItems('ミュウミュウ シューズ')">ミュウミュウ靴</button>
            <button class="filter-btn" onclick="filterItems('セリーヌ シューズ')">セリーヌ靴</button>
            <button class="filter-btn" onclick="filterItems('バレンシアガ スニーカー')">バレンシアガ靴</button>
            <button class="filter-btn" onclick="filterItems('ペリーコ シューズ パンプス')">ペリーコ</button>
            <button class="filter-btn" onclick="filterItems('ドルチェガッバーナ シューズ')">D&G靴</button>
            <button class="filter-btn" onclick="filterItems('マイケルコース シューズ')">MK靴</button>
            <button class="filter-btn" onclick="filterItems('リーガル ローファー ビジネス')">リーガル</button>
            <button class="filter-btn" onclick="filterItems('ドクターマーチン ブーツ 3ホール')">マーチン</button>
            <button class="filter-btn" onclick="filterItems('レッドウィング ブーツ')">レッドウィング</button>
            <button class="filter-btn" onclick="filterItems('コールハーン シューズ')">コールハーン</button>
            <button class="filter-btn" onclick="filterItems('ティンバーランド ブーツ')">ティンバー</button>
            <button class="filter-btn" onclick="filterItems('ナイキ スニーカー')">ナイキ</button>
            <button class="filter-btn" onclick="filterItems('アディダス スニーカー')">アディダス</button>
            <button class="filter-btn" onclick="filterItems('ニューバランス スニーカー')">ニューバランス</button>
            <button class="filter-btn" onclick="filterItems('コンバース スニーカー')">コンバース</button>
        </div>
        
        <div class="grid" id="item-grid">
            {% if bargains %}
                {% for item in bargains %}
                <div class="card" data-keyword="{{item.keyword}}">
                    <div class="card-img-wrapper">
                        <span class="badge">{{item.keyword}}</span>
                        
                        <!-- 👑 【改善1】やや汚れあり＝綺麗かも バッジの表示 -->
                        {% if item.needs_photo_check %}
                        <span class="badge" style="top:40px; background-color:#d97706;">📸 要写真確認</span>
                        {% endif %}
                        
                        <!-- 👑 【改善3】ホワイト人気 バッジの表示 -->
                        {% if item.is_white_sneaker %}
                        <span class="badge" style="top:70px; background-color:#6366f1;">⭐ ホワイト人気</span>
                        {% endif %}
                        
                        <!-- 👑 【改善4】ソール修復・裏張り警戒 バッジの表示 -->
                        {% if item.needs_sole_warning %}
                        <span class="badge" style="top:100px; background-color:#10b981;">⚠️ ソール補修/裏張</span>
                        {% endif %}
                        
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
                                <span class="metric-label">商品の状態</span>
                                <span class="metric-val" style="color: var(--accent-color); font-weight: 700;">{{item.condition}}</span>
                            </div>
                            <div class="metric-row" style="margin-top: 10px; border-top: 1px solid var(--border-color); padding-top: 10px;">
                                <span class="metric-label" style="font-size: 1rem; font-weight: 800; color: var(--accent-color);">利益期待値（ダブル送料引込）</span>
                                <span class="profit">{{item.profit_formatted}}</span>
                            </div>
                        </div>
                        
                        <a href="{{item.url}}" target="_blank" class="btn-link">ヤフオクで商品を見る &rarr;</a>
                    </div>
                </div>
                
                <!-- 👑 インフィード広告を3番目のカードの直後に自動挿入 -->
                {% if loop.index == 3 and adsense_id and adsense_slot %}
                <div class="adsense-container">
                    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{adsense_id}}" crossorigin="anonymous"></script>
                    <ins class="adsbygoogle"
                         style="display:block"
                         data-ad-format="fluid"
                         data-ad-layout-key="-fb+5w+4e-db+86"
                         data-ad-client="{{adsense_id}}"
                         data-ad-slot="{{adsense_slot}}"></ins>
                    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
                </div>
                {% endif %}
                
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
        bargains=all_bargains,
        adsense_id=ADSENSE_PUBLISHER_ID if ADSENSE_PUBLISHER_ID else None,
        adsense_slot=ADSENSE_SLOT_ID if ADSENSE_SLOT_ID else None
    )
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(rendered_html)
        
    print("✅ index.html のビルドが正常に完了しました！")

if __name__ == "__main__":
    main()
