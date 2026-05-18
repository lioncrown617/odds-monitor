import time, threading
from datetime import datetime
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

state = {
    "running":          False,
    "data":             [],
    "base_data":        {},
    "base_time":        "",
    "base_est_bet":     {},
    "prev_data":        {},
    "prev_est_bet":     {},   # ★ 上次估算投注額
    "prev_flow":        {},   # ★ 上次流入金額
    "flow_streak":      defaultdict(int),  # ★ 連續流入次數
    "trend_counter":    defaultdict(int),
    "cum_drop":         defaultdict(float),
    "cum_rise":         defaultdict(float),
    "update_count":     0,
    "last_update":      "",
    "race_date":        "",
    "venue":            "",
    "venue_name":       "",
    "race_no":          "",
    "interval":         30,
    "url":              "",
    "status":           "等待設定...",
    "top_down":         [],
    "top_up":           [],
    "history":          defaultdict(list),
    "bet_history":      defaultdict(list),
    "flow_history":     defaultdict(list),  # ★ 每次流入金額歷史
    "timestamps":       [],
    "win_pool":         "",
    "win_pool_history": [],
}

TREND_THRESHOLD = 2

# requirements.txt 移除 webdriver-manager，加入：
# selenium
# flask

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Railway 的 Chromium 路徑
    options.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(options=options)
def fetch_odds(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr.rc-odds-row"))
        )
        time.sleep(3)
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.rc-odds-row")
        results = []
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 9:
                continue
            results.append({
                "no":      tds[0].text.strip(),
                "name":    tds[2].text.strip(),
                "draw":    tds[3].text.strip(),
                "jockey":  tds[5].text.strip(),
                "trainer": tds[6].text.strip(),
                "win":     tds[7].text.strip(),
                "place":   tds[8].text.strip(),
            })
        win_pool = ""
        try:
            pool_row = driver.find_element(By.ID, "poolInvWIN")
            ptds = pool_row.find_elements(By.TAG_NAME, "td")
            if len(ptds) >= 2:
                win_pool = ptds[1].text.strip()
        except:
            pass
        return (results if results else None), win_pool
    except:
        return None, ""

def calc_est_bets(data, pool_str):
    pool_num = 0.0
    try:
        pool_num = float(pool_str.replace("$","").replace(",","").strip())
    except:
        pass
    net_pool  = pool_num * (1 - 0.175)
    total_inv = sum(1.0/float(r["win"]) for r in data if r["win"] not in ("","SCR"))
    result = {}
    for r in data:
        try:
            share = (1.0/float(r["win"])) / total_inv if total_inv > 0 else 0
            result[r["no"]] = net_pool * share
        except:
            result[r["no"]] = 0.0
    return result

def fmt_money(amt):
    if amt >= 1_000_000:
        return f"${amt/1_000_000:.2f}M"
    elif amt >= 1_000:
        return f"${amt/1_000:.0f}K"
    return f"${amt:.0f}"

def fmt_diff(diff):
    if diff > 0:
        return f"+{fmt_money(diff)}", "up"
    elif diff < 0:
        return f"-{fmt_money(abs(diff))}", "down"
    return "—", "neutral"

def calc_trends(data):
    prev = state["prev_data"]
    base = state["base_data"]
    tc   = state["trend_counter"]
    cd   = state["cum_drop"]
    cr   = state["cum_rise"]
    for r in data:
        no = r["no"]
        try:
            curr = float(r["win"])
            if no in prev:
                diff = curr - float(prev[no])
                if diff < 0:
                    tc[no] = tc[no] + 1 if tc[no] > 0 else 1
                elif diff > 0:
                    tc[no] = tc[no] - 1 if tc[no] < 0 else -1
            if no in base:
                base_w = float(base[no])
                pct = (base_w - curr) / base_w * 100
                if pct > 0:
                    cd[no] = round(pct, 1)
                    cr[no] = 0.0
                else:
                    cr[no] = round(abs(pct), 1)
                    cd[no] = 0.0
        except:
            pass

def calc_flow(est_bets):
    """計算每匹馬本次流入、加速度、連續流入次數"""
    prev     = state["prev_est_bet"]
    prev_fl  = state["prev_flow"]
    streak   = state["flow_streak"]
    flows    = {}
    accels   = {}

    for no, amt in est_bets.items():
        prev_amt  = prev.get(no, amt)
        flow      = amt - prev_amt          # 本次流入（正=流入，負=流出）
        prev_flow = prev_fl.get(no, 0.0)
        accel     = flow - prev_flow        # 加速度（正=加速，負=減速）

        # 連續流入次數
        if flow > 0:
            streak[no] = streak[no] + 1 if streak[no] >= 0 else 1
        elif flow < 0:
            streak[no] = streak[no] - 1 if streak[no] <= 0 else -1
        else:
            streak[no] = 0

        flows[no]  = flow
        accels[no] = accel

    return flows, accels

def get_trend_label(no):
    tc        = state["trend_counter"]
    prev      = state["prev_data"]
    data_dict = {r["no"]: r for r in state["data"]}
    count     = tc.get(no, 0)
    try:
        curr = float(data_dict[no]["win"])
        p    = float(prev[no]) if no in prev else curr
        pct  = (p - curr) / p * 100 if p > 0 else 0
    except:
        pct = 0
    if count >= TREND_THRESHOLD and pct >= 10:
        return "急跌", "hot"
    elif count >= TREND_THRESHOLD and pct > 0:
        return "持跌", "warm"
    elif count <= -TREND_THRESHOLD:
        return "持升", "rise"
    elif pct < 0:
        return "回升", "rise"
    return "—", "neutral"

def calc_top3():
    data = state["data"]
    tc   = state["trend_counter"]
    cd   = state["cum_drop"]
    cr   = state["cum_rise"]
    base = state["base_data"]
    down, up = [], []
    for r in data:
        no       = r["no"]
        streak_d = max(tc.get(no, 0), 0)
        drop     = max(cd.get(no, 0), 0)
        score_d  = streak_d * 3 + drop
        if score_d > 0:
            down.append({"no": no, "name": r["name"], "win": r["win"],
                         "base": base.get(no,"—"), "streak": streak_d,
                         "drop": drop, "score": score_d})
        streak_u = max(-tc.get(no, 0), 0)
        rise     = max(cr.get(no, 0), 0)
        score_u  = streak_u * 3 + rise
        if score_u > 0:
            up.append({"no": no, "name": r["name"], "win": r["win"],
                       "base": base.get(no,"—"), "streak": streak_u,
                       "rise": rise, "score": score_u})
    state["top_down"] = sorted(down, key=lambda x: x["score"], reverse=True)[:3]
    state["top_up"]   = sorted(up,   key=lambda x: x["score"], reverse=True)[:3]

def record_history(data, now, est_bets, flows):
    state["timestamps"].append(now)
    for r in data:
        no = r["no"]
        try:
            state["history"][no].append(float(r["win"]))
        except:
            state["history"][no].append(None)
        state["bet_history"][no].append(round(est_bets.get(no, 0)))
        state["flow_history"][no].append(round(flows.get(no, 0)))

def monitor_loop():
    global selenium_driver
    selenium_driver = init_driver()
    state["status"] = "瀏覽器已啟動，正在抓取..."

    while state["running"]:
        now = datetime.now().strftime("%H:%M:%S")
        data, win_pool = fetch_odds(selenium_driver, state["url"])

        if data:
            state["update_count"] += 1
            est_bets = calc_est_bets(data, win_pool)

            if not state["base_data"]:
                state["base_data"]    = {r["no"]: r["win"] for r in data}
                state["base_time"]    = now
                state["base_est_bet"] = dict(est_bets)

            flows, accels = calc_flow(est_bets)

            calc_trends(data)
            record_history(data, now, est_bets, flows)

            state["data"]              = data
            state["prev_data"]         = {r["no"]: r["win"] for r in data}
            state["last_update"]       = now
            state["win_pool"]          = win_pool
            state["win_pool_history"].append({"time": now, "pool": win_pool})

            # ★ 更新流入狀態
            state["prev_flow"]    = flows
            state["prev_est_bet"] = dict(est_bets)
            state["_accels"]      = accels   # 暫存加速度

            calc_top3()
            state["status"] = "正常監察中"
        else:
            state["status"] = f"[{now}] 未能取得賠率，重試中..."

        time.sleep(state["interval"])

    selenium_driver.quit()
    state["status"] = "監察已停止"

selenium_driver = None
monitor_thread  = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global monitor_thread
    if state["running"]:
        return jsonify({"ok": False, "msg": "已在監察中"})
    d = request.json
    state["race_date"]       = d.get("date",    datetime.now().strftime("%Y-%m-%d"))
    state["venue"]           = d.get("venue",   "ST")
    state["venue_name"]      = "沙田" if state["venue"] == "ST" else "跑馬地"
    state["race_no"]         = d.get("race_no", "1")
    state["interval"]        = max(int(d.get("interval", 30)), 15)
    state["url"]             = (f"https://bet.hkjc.com/ch/racing/wp/"
                                f"{state['race_date']}/{state['venue']}/{state['race_no']}")
    state["running"]         = True
    state["data"]            = []
    state["base_data"]       = {}
    state["base_est_bet"]    = {}
    state["prev_data"]       = {}
    state["prev_est_bet"]    = {}
    state["prev_flow"]       = {}
    state["flow_streak"]     = defaultdict(int)
    state["trend_counter"]   = defaultdict(int)
    state["cum_drop"]        = defaultdict(float)
    state["cum_rise"]        = defaultdict(float)
    state["update_count"]    = 0
    state["top_down"]        = []
    state["top_up"]          = []
    state["history"]         = defaultdict(list)
    state["bet_history"]     = defaultdict(list)
    state["flow_history"]    = defaultdict(list)
    state["timestamps"]      = []
    state["win_pool"]        = ""
    state["win_pool_history"]= []
    state["_accels"]         = {}
    state["status"]          = "正在啟動..."
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    return jsonify({"ok": True})

@app.route("/stop", methods=["POST"])
def stop():
    state["running"] = False
    return jsonify({"ok": True})

@app.route("/data")
def get_data():
    pool_num = 0.0
    try:
        pool_num = float(state["win_pool"].replace("$","").replace(",","").strip())
    except:
        pass
    net_pool  = pool_num * (1 - 0.175)
    total_inv = sum(1.0/float(r["win"]) for r in state["data"] if r["win"] not in ("","SCR"))

    rows = []
    for r in state["data"]:
        no         = r["no"]
        label, css = get_trend_label(no)
        base_win   = state["base_data"].get(no, "—")
        prev_win   = state["prev_data"].get(no, "—")

        chg_str = "—"
        try:
            diff = float(r["win"]) - float(prev_win)
            pct  = diff / float(prev_win) * 100
            sign = "+" if diff >= 0 else ""
            chg_str = f"{sign}{diff:.1f}({sign}{pct:.1f}%)"
        except:
            pass

        # 現時估算投注額
        est_amt = 0.0
        est_bet = "—"
        est_pct = "—"
        try:
            share   = (1.0/float(r["win"])) / total_inv if total_inv > 0 else 0
            est_amt = net_pool * share
            est_bet = fmt_money(est_amt)
            est_pct = f"{share*100:.1f}%"
        except:
            pass

        # 基準投注額
        base_amt     = state["base_est_bet"].get(no, 0.0)
        base_bet_str = fmt_money(base_amt) if base_amt > 0 else "—"

        # 累積增減（現時 vs 基準）
        cum_diff     = est_amt - base_amt
        cum_diff_str, cum_diff_css = fmt_diff(cum_diff) if base_amt > 0 and est_amt > 0 else ("—","neutral")
        cum_diff_pct = ""
        try:
            if base_amt > 0:
                pv = (est_amt - base_amt) / base_amt * 100
                cum_diff_pct = f"({'+'if pv>=0 else''}{pv:.1f}%)"
        except:
            pass

        # ★ 本次流入
        flow      = state["prev_flow"].get(no, 0.0)
        flow_str, flow_css = fmt_diff(flow)

        # ★ 流入加速度
        accel     = state.get("_accels", {}).get(no, 0.0)
        if accel > 500:
            accel_str = f"🚀 +{fmt_money(accel)}"
            accel_css = "up"
        elif accel > 0:
            accel_str = f"↗ +{fmt_money(accel)}"
            accel_css = "up"
        elif accel < -500:
            accel_str = f"🔻 -{fmt_money(abs(accel))}"
            accel_css = "down"
        elif accel < 0:
            accel_str = f"↘ -{fmt_money(abs(accel))}"
            accel_css = "down"
        else:
            accel_str = "→ 穩定"
            accel_css = "neutral"

        # ★ 連續流入次數
        streak    = state["flow_streak"].get(no, 0)
        if streak >= 3:
            streak_str = f"🔥 +{streak}次"
            streak_css = "up"
        elif streak > 0:
            streak_str = f"▲ {streak}次"
            streak_css = "up"
        elif streak <= -3:
            streak_str = f"❄️ {streak}次"
            streak_css = "down"
        elif streak < 0:
            streak_str = f"▼ {abs(streak)}次"
            streak_css = "down"
        else:
            streak_str = "—"
            streak_css = "neutral"

        rows.append({
            **r,
            "base_win":      base_win,
            "prev_win":      prev_win,
            "chg":           chg_str,
            "trend":         label,
            "trend_css":     css,
            "cum_drop":      state["cum_drop"].get(no, 0),
            "cum_rise":      state["cum_rise"].get(no, 0),
            "est_bet":       est_bet,
            "est_pct":       est_pct,
            "base_bet":      base_bet_str,
            "cum_diff":      cum_diff_str,
            "cum_diff_css":  cum_diff_css,
            "cum_diff_pct":  cum_diff_pct,
            "flow":          flow_str,       # ★ 本次流入
            "flow_css":      flow_css,
            "accel":         accel_str,      # ★ 加速度
            "accel_css":     accel_css,
            "streak":        streak_str,     # ★ 連續次數
            "streak_css":    streak_css,
        })

    return jsonify({
        "rows":             rows,
        "top_down":         state["top_down"],
        "top_up":           state["top_up"],
        "update_count":     state["update_count"],
        "last_update":      state["last_update"],
        "base_time":        state["base_time"],
        "status":           state["status"],
        "running":          state["running"],
        "race_date":        state["race_date"],
        "venue_name":       state["venue_name"],
        "race_no":          state["race_no"],
        "interval":         state["interval"],
        "history":          {k: v for k, v in state["history"].items()},
        "bet_history":      {k: v for k, v in state["bet_history"].items()},
        "flow_history":     {k: v for k, v in state["flow_history"].items()},
        "timestamps":       state["timestamps"],
        "horses":           {r["no"]: r["name"] for r in state["data"]},
        "win_pool":         state["win_pool"],
        "win_pool_history": state["win_pool_history"],
    })
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
