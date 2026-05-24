import os, json
import time, threading
from datetime import datetime
from collections import defaultdict, deque
from flask import Flask, render_template, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def _deque5():
    return deque(maxlen=5)

def _deque60():
    return deque(maxlen=60)

def _inf():
    return float("inf")

state = {
    "running": False,
    "data": [],
    "base_data": {},
    "base_time": "",
    "base_est_bet": {},
    "prev_data": {},
    "prev_est_bet": {},
    "prev_flow": {},
    "prev_pool": 0.0,
    "prev_odds_drop": {},
    "trend_counter": defaultdict(int),
    "cum_drop": defaultdict(float),
    "cum_rise": defaultdict(float),
    "cum_flow": defaultdict(float),
    "update_count": 0,
    "last_update": "",
    "race_date": "",
    "venue": "",
    "venue_name": "",
    "race_no": "",
    "interval": 30,
    "url": "",
    "status": "等待設定...",
    "has_error": False,
    "top_down": [],
    "top_up": [],
    "top_suspicious": [],
    "top_steady": [],
    "top_rci": [],
    "alerts": [],
    "history": defaultdict(list),
    "bet_history": defaultdict(list),
    "flow_history": defaultdict(list),
    "absorb_history": defaultdict(list),
    "sms_history": defaultdict(list),
    "timestamps": [],
    "win_pool": "",
    "win_pool_history": [],
    "_accels": {},
    "_absorb": {},
    "_sms": {},
    "_alerts": {},
    "e_history": defaultdict(_deque5),
    "inflow_ts_history": defaultdict(_deque60),
    "min_odds": defaultdict(_inf),
    "alert_cooldown": defaultdict(dict),
    "steady_scores": {},
}

TREND_THRESHOLD = 2
ALERT_ABSORB_THRESH = 30.0
ACCEL_DROP_MIN = 2

selenium_driver = None
monitor_thread = None

VENUE_NAME_MAP = {
    "ST": "沙田",
    "HV": "跑馬地",
    **{f"S{i}": f"特別賽事 S{i}" for i in range(1, 9)}
}

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    )
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

def parse_pool(pool_str):
    try:
        return float(pool_str.replace("$","").replace(",","").strip())
    except:
        return 0.0

def calc_est_bets(data, pool_str):
    pool_num = parse_pool(pool_str)
    net_pool = pool_num * (1 - 0.175)
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
    a = abs(amt)
    if a >= 1_000_000:
        return f"${a/1_000_000:.2f}M"
    elif a >= 1_000:
        return f"${a/1_000:.1f}K"
    return f"${a:.0f}"

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
            if curr < state["min_odds"][no]:
                state["min_odds"][no] = curr
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

def calc_sms_v2(no, cum_flow_val, cum_drop_val):
    F = max(cum_flow_val / 10000.0, 0)
    if F == 0:
        return 0.0
    D = max(cum_drop_val, 0)
    e_hist = list(state["e_history"][no])
    pos_e  = [max(e, 0) for e in e_hist]
    E_eff  = sum(pos_e) / len(pos_e) if pos_e else 0
    now_ts = time.time()
    recent_inflow = sum(amt for ts, amt in state["inflow_ts_history"][no] if now_ts - ts <= 900)
    Wt = 1.5 if cum_flow_val > 0 and recent_inflow / cum_flow_val > 0.5 else 1.0
    recent_flows = list(state["flow_history"][no])[-3:]
    if len(recent_flows) >= 3 and all(f <= 0 for f in recent_flows):
        Wt *= 0.5
    return round((F ** 1.2) * (1 + D / 10) * (1 + E_eff / 10) * Wt, 2)

def calc_rci(no, cum_flow_val, cum_rise_val):
    if cum_flow_val < 300000 or cum_rise_val < 30:
        return 0.0
    F = cum_flow_val / 10000.0
    R = cum_rise_val / 10.0
    recent_flows = list(state["flow_history"][no])[-3:]
    if sum(1 for f in recent_flows if f > 0) < 1:
        return 0.0
    return round(F * R, 2)

def calc_flow_and_signals(est_bets, win_pool_str, data):
    prev_bets  = state["prev_est_bet"]
    prev_fl    = state["prev_flow"]
    prev_pool  = state["prev_pool"]
    prev_drop  = state["prev_odds_drop"]
    cum_flow   = state["cum_flow"]
    cum_drop_pct = state["cum_drop"]
    now_ts     = time.time()
    curr_pool_num = parse_pool(win_pool_str)
    pool_increase = max((curr_pool_num - prev_pool) * (1 - 0.175), 0)
    total_inv  = sum(1.0/float(r["win"]) for r in data if r["win"] not in ("","SCR"))
    flows={}; accels={}; absorbs={}; sms={}; alerts={}

    for r in data:
        no      = r["no"]
        win_str = r["win"]
        if win_str in ("","SCR"):
            continue
        try:
            curr_odds = float(win_str)
        except:
            continue

        amt       = est_bets.get(no, 0.0)
        prev_amt  = prev_bets.get(no, None)
        flow      = 0.0 if prev_amt is None else amt - prev_amt
        prev_flow_val = prev_fl.get(no, None)
        accel     = 0.0 if prev_flow_val is None else flow - prev_flow_val

        if prev_amt is not None and flow > 0:
            cum_flow[no] = cum_flow.get(no, 0.0) + flow
            state["inflow_ts_history"][no].append((now_ts, flow))

        try:
            share_pct = (1.0/curr_odds) / total_inv * 100 if total_inv > 0 else 0
        except:
            share_pct = 0.0

        absorb_pct = 0.0; excess = 0.0
        if pool_increase > 500 and prev_amt is not None:
            absorb_pct = (flow / pool_increase) * 100
            excess     = absorb_pct - share_pct
        state["e_history"][no].append(excess)

        prev_o = float(state["prev_data"].get(no, curr_odds) or curr_odds)
        try:
            odds_drop = (prev_o - curr_odds) / prev_o * 100 if prev_o > 0 else 0.0
        except:
            odds_drop = 0.0
        prev_drop_val = prev_drop.get(no, 0.0)
        odds_accel    = odds_drop - prev_drop_val

        sms_score = calc_sms_v2(no, cum_flow.get(no, 0.0), cum_drop_pct.get(no, 0.0))

        alert_flags = []
        if pool_increase > 500 and prev_amt is not None and absorb_pct >= ALERT_ABSORB_THRESH:
            alert_flags.append(f"🚨單次吸金{absorb_pct:.0f}%")

        tc_val = state["trend_counter"].get(no, 0)
        if tc_val >= ACCEL_DROP_MIN and odds_accel > 0.5:
            alert_flags.append(f"⚡賠率加速跌({odds_drop:.1f}%)")

        cum_in = cum_flow.get(no, 0.0)
        # ── 突發大注：只要該馬當次流入 >= 10000 即記錄，前端按金額分色 ──
        if flow >= 10000:
            alert_flags.append(f"💥突發大注{fmt_money(flow)}")

        try:
            min_o = state["min_odds"].get(no, curr_odds)
            rise_from_min = (curr_odds - min_o) / min_o * 100 if min_o > 0 else 0
            if rise_from_min > 50 and cum_in > 100000:
                alert_flags.append(f"🔔疑似洗碼受益(反彈{rise_from_min:.0f}%)")
        except:
            pass

        flows[no]=flow; accels[no]=accel
        absorbs[no] = {
            "flow": round(flow), "absorb_pct": round(absorb_pct,1),
            "share_pct": round(share_pct,1), "excess": round(excess,1),
            "pool_inc": round(pool_increase), "odds_drop": round(odds_drop,2),
            "odds_accel": round(odds_accel,2),
        }
        sms[no]=sms_score; alerts[no]=alert_flags

    return flows, accels, absorbs, sms, alerts

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
    data    = state["data"]
    base    = state["base_data"]
    sms_map = state["_sms"]
    absorbs = state["_absorb"]
    tc      = state["trend_counter"]
    cd      = state["cum_drop"]
    cr      = state["cum_rise"]
    cum_f   = state["cum_flow"]
    down, up, suspicious, steady_list, rci_list = [], [], [], [], []

    for r in data:
        no     = r["no"]
        sms    = sms_map.get(no, 0.0)
        ab     = absorbs.get(no, {})
        cum_in = cum_f.get(no, 0.0)

        streak_d = max(tc.get(no, 0), 0)
        drop     = cd.get(no, 0)
        if streak_d > 0 or drop > 0:
            down.append({"no":no,"name":r["name"],"win":r["win"],"base":base.get(no,"—"),
                         "streak":streak_d,"drop":drop,"cum_inflow":round(cum_in),
                         "sms":sms,"excess":ab.get("excess",0)})

        streak_u = max(-tc.get(no, 0), 0)
        rise     = cr.get(no, 0)
        if streak_u > 0 or rise > 0:
            up.append({"no":no,"name":r["name"],"win":r["win"],"base":base.get(no,"—"),
                       "streak":streak_u,"rise":rise})
        try:
            curr_o   = float(r["win"])
            min_o    = state["min_odds"].get(no, curr_o)
            rise_pct = (curr_o - min_o) / min_o * 100 if min_o > 0 else 0
            if rise_pct > 50 and cum_in > 100000:
                suspicious.append({"no":no,"name":r["name"],"win":r["win"],
                                   "min_odds":round(min_o,1),"rise_pct":round(rise_pct,1),
                                   "cum_inflow":round(cum_in)})
        except:
            pass
        try:
            curr_o2 = float(r["win"]); steady = 0.0
            if curr_o2 >= 15 and cum_in >= 200000:
                flow_hist = list(state["flow_history"].get(no, []))[-5:]
                if sum(1 for f in flow_hist if f > 0) >= 3:
                    steady = round(cum_in / 10000.0 * (curr_o2 / 20.0), 2)
                if steady > 0:
                    steady_list.append({"no":no,"name":r["name"],"win":r["win"],
                                        "base":base.get(no,"—"),"cum_inflow":round(cum_in),
                                        "steady":steady})
        except:
            pass
        try:
            rise_pct2 = cr.get(no, 0.0)
            rci_score = calc_rci(no, cum_in, rise_pct2)
            if rci_score > 0:
                rci_list.append({"no":no,"name":r["name"],"win":r["win"],
                                 "base":base.get(no,"—"),"cum_inflow":round(cum_in),
                                 "rise_pct":round(rise_pct2,1),"rci":rci_score})
        except:
            pass

    state["top_down"]      = sorted(down,        key=lambda x: x["sms"],      reverse=True)[:3]
    state["top_up"]        = sorted(up,           key=lambda x: x["rise"],     reverse=True)[:3]
    state["top_suspicious"]= sorted(suspicious,   key=lambda x: x["rise_pct"],reverse=True)[:3]
    state["top_steady"]    = sorted(steady_list,  key=lambda x: x["steady"],   reverse=True)[:3]
    state["top_rci"]       = sorted(rci_list,     key=lambda x: x["rci"],      reverse=True)[:3]

def update_global_alerts(alerts_map, now):
    now_ts   = time.time()
    cooldown = state["alert_cooldown"]
    for no, flags in alerts_map.items():
        if flags:
            name     = next((r["name"] for r in state["data"] if r["no"]==no), no)
            win      = next((r["win"]  for r in state["data"] if r["no"]==no), "—")
            ab       = state["_absorb"].get(no, {})
            flow_amt = ab.get("flow", 0)
            pool_inc = ab.get("pool_inc", 0)
            for f in flags:
                msg_type = f[:4]
                # ── 突發大注不設冷卻，每次都記錄；其他警報600秒冷卻 ──
                if msg_type != "💥突":
                    if now_ts - cooldown[no].get(msg_type, 0) < 600:
                        continue
                    cooldown[no][msg_type] = now_ts
                state["alerts"].insert(0, {
                    "time": now, "no": no, "name": name,
                    "win": win, "msg": f,
                    "flow_amt": flow_amt, "pool_inc": pool_inc
                })
    state["alerts"] = state["alerts"][:50]

def record_history(data, now, est_bets, flows, absorbs, sms):
    state["timestamps"].append(now)
    for r in data:
        no = r["no"]
        try:
            state["history"][no].append(float(r["win"]))
        except:
            state["history"][no].append(None)
        state["bet_history"][no].append(round(est_bets.get(no, 0)))
        state["flow_history"][no].append(round(flows.get(no, 0)))
        state["absorb_history"][no].append(absorbs[no]["excess"] if no in absorbs else 0)
        state["sms_history"][no].append(sms.get(no, 0))

def get_log_path():
    date_str = state["race_date"].replace("-", "")
    venue    = state["venue"]
    race_no  = state["race_no"].zfill(2)
    os.makedirs("logs", exist_ok=True)
    return f"logs/{date_str}_{venue}_R{race_no}_log.json"

def _load_log():
    path = get_log_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"meta": {}, "snapshots": [], "alerts": [], "summary": {}}

def _save_log(log_data):
    try:
        with open(get_log_path(), "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def append_snapshot(now, data, est_bets, flows, absorbs, sms, win_pool):
    log = _load_log()
    if not log["meta"]:
        log["meta"] = {
            "race_date":  state["race_date"],
            "venue":      state["venue"],
            "venue_name": state["venue_name"],
            "race_no":    state["race_no"],
            "base_time":  state["base_time"],
            "start_time": now,
        }
    snapshot = {"time": now, "win_pool": win_pool, "horses": []}
    for r in data:
        no  = r["no"]
        ab  = absorbs.get(no, {})
        rci_s = calc_rci(no, state["cum_flow"].get(no, 0.0), state["cum_rise"].get(no, 0.0))
        try:
            co = float(r["win"]); ci = state["cum_flow"].get(no, 0.0); st = 0.0
            if co >= 15 and ci >= 200000:
                fh = list(state["flow_history"].get(no, []))[-5:]
                if sum(1 for f in fh if f > 0) >= 3:
                    st = round(ci / 10000.0 * (co / 20.0), 2)
        except:
            st = 0.0
        snapshot["horses"].append({
            "no": r["no"], "name": r["name"],
            "win": r["win"], "place": r["place"],
            "base_win":    state["base_data"].get(no, "—"),
            "est_bet":     round(est_bets.get(no, 0)),
            "flow":        round(flows.get(no, 0)),
            "cum_flow":    round(state["cum_flow"].get(no, 0)),
            "absorb_pct":  ab.get("absorb_pct", 0),
            "excess":      ab.get("excess", 0),
            "pool_inc":    ab.get("pool_inc", 0),
            "odds_drop":   ab.get("odds_drop", 0),
            "cum_drop":    state["cum_drop"].get(no, 0),
            "cum_rise":    state["cum_rise"].get(no, 0),
            "sms":         sms.get(no, 0),
            "rci":         rci_s,
            "steady":      st,
            "alerts":      state["_alerts"].get(no, []),
        })
    log["snapshots"].append(snapshot)
    existing = {(a["time"], a["no"], a["msg"]) for a in log["alerts"]}
    for a in state["alerts"]:
        k = (a["time"], a["no"], a["msg"])
        if k not in existing:
            log["alerts"].append(a)
            existing.add(k)
    _save_log(log)

def finalize_log(now):
    log   = _load_log()
    cum_f = state["cum_flow"]
    horses = [
        {"no": no,
         "name":      next((r["name"] for r in state["data"] if r["no"]==no), no),
         "final_win": next((r["win"]  for r in state["data"] if r["no"]==no), "—"),
         "cum_flow":  round(v),
         "cum_drop":  state["cum_drop"].get(no, 0),
         "cum_rise":  state["cum_rise"].get(no, 0),
         "sms":       state["_sms"].get(no, 0),
         "rci":       calc_rci(no, v, state["cum_rise"].get(no, 0))}
        for no, v in cum_f.items() if v > 0
    ]
    log["summary"] = {
        "end_time":      now,
        "total_updates": state["update_count"],
        "base_time":     state["base_time"],
        "final_pool":    state["win_pool"],
        "total_alerts":  len(log["alerts"]),
        "top_sms":       sorted(horses, key=lambda x: x["sms"], reverse=True)[:5],
        "top_rci":       sorted(horses, key=lambda x: x["rci"], reverse=True)[:5],
        "horses_final":  horses,
    }
    _save_log(log)
    print(f"[LOG] 已儲存：{get_log_path()}")

def monitor_loop():
    global selenium_driver
    selenium_driver = init_driver()
    state["status"]    = "瀏覽器已啟動，正在抓取..."
    state["has_error"] = False
    while state["running"]:
        now = datetime.now().strftime("%H:%M:%S")
        data, win_pool = fetch_odds(selenium_driver, state["url"])
        if data:
            state["has_error"]  = False
            state["update_count"] += 1
            est_bets = calc_est_bets(data, win_pool)
            if not state["base_data"]:
                state["base_data"]     = {r["no"]: r["win"] for r in data}
                state["base_time"]     = now
                state["base_est_bet"]  = dict(est_bets)
            flows, accels, absorbs, sms, alerts_map = calc_flow_and_signals(est_bets, win_pool, data)
            calc_trends(data)
            record_history(data, now, est_bets, flows, absorbs, sms)
            append_snapshot(now, data, est_bets, flows, absorbs, sms, win_pool)
            update_global_alerts(alerts_map, now)
            state["data"]        = data
            state["prev_data"]   = {r["no"]: r["win"] for r in data}
            state["prev_odds_drop"] = {no: absorbs[no]["odds_drop"] for no in absorbs}
            state["last_update"] = now
            state["win_pool"]    = win_pool
            state["win_pool_history"].append({"time": now, "pool": win_pool})
            state["prev_flow"]   = flows
            state["prev_est_bet"]= dict(est_bets)
            state["prev_pool"]   = parse_pool(win_pool)
            state["_accels"]     = accels
            state["_absorb"]     = absorbs
            state["_sms"]        = sms
            state["_alerts"]     = alerts_map
            calc_top3()
            state["status"] = "正常監察中"
        else:
            state["has_error"] = True
            state["status"]    = f"[{now}] 未能取得賠率，重試中..."
        time.sleep(state["interval"])
    finalize_log(datetime.now().strftime("%H:%M:%S"))
    selenium_driver.quit()
    state["status"]    = "監察已停止"
    state["has_error"] = False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global monitor_thread
    if state["running"]:
        return jsonify({"ok": False, "msg": "已在監察中"})
    d = request.json
    state["race_date"]  = d.get("date", datetime.now().strftime("%Y-%m-%d"))
    state["venue"]      = d.get("venue", "ST")
    state["venue_name"] = VENUE_NAME_MAP.get(state["venue"], state["venue"])
    state["race_no"]    = d.get("race_no", "1")
    state["interval"]   = max(int(d.get("interval", 30)), 15)
    state["url"] = (f"https://bet.hkjc.com/ch/racing/wp/"
                    f"{state['race_date']}/{state['venue']}/{state['race_no']}")
    for k,v in [("running",True),("has_error",False),("data",[]),("base_data",{}),
                ("base_est_bet",{}),("prev_data",{}),("prev_est_bet",{}),("prev_flow",{}),
                ("prev_pool",0.0),("prev_odds_drop",{}),("update_count",0),
                ("top_down",[]),("top_up",[]),("top_suspicious",[]),("top_steady",[]),("top_rci",[]),
                ("alerts",[]),("timestamps",[]),("win_pool",""),("win_pool_history",[]),
                ("_accels",{}),("_absorb",{}),("_sms",{}),("_alerts",{}),
                ("steady_scores",{}),("status","正在啟動...")]:
        state[k] = v
    state["trend_counter"]      = defaultdict(int)
    state["cum_drop"]           = defaultdict(float)
    state["cum_rise"]           = defaultdict(float)
    state["cum_flow"]           = defaultdict(float)
    state["history"]            = defaultdict(list)
    state["bet_history"]        = defaultdict(list)
    state["flow_history"]       = defaultdict(list)
    state["absorb_history"]     = defaultdict(list)
    state["sms_history"]        = defaultdict(list)
    state["e_history"]          = defaultdict(_deque5)
    state["inflow_ts_history"]  = defaultdict(_deque60)
    state["min_odds"]           = defaultdict(_inf)
    state["alert_cooldown"]     = defaultdict(dict)
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    return jsonify({"ok": True})

@app.route("/stop", methods=["POST"])
def stop():
    state["running"] = False
    return jsonify({"ok": True})

@app.route("/data")
def get_data():
    pool_num  = parse_pool(state["win_pool"])
    net_pool  = pool_num * (1 - 0.175)
    total_inv = sum(1.0/float(r["win"]) for r in state["data"] if r["win"] not in ("","SCR"))
    rows = []
    for r in state["data"]:
        no = r["no"]
        label, css = get_trend_label(no)
        base_win   = state["base_data"].get(no, "—")
        prev_win   = state["prev_data"].get(no, "—")
        chg_str    = "—"
        try:
            diff    = float(r["win"]) - float(prev_win)
            pct     = diff / float(prev_win) * 100
            sign    = "+" if diff >= 0 else ""
            chg_str = f"{sign}{diff:.1f}({sign}{pct:.1f}%)"
        except:
            pass
        est_amt, est_bet, est_pct = 0.0, "—", "—"
        try:
            share   = (1.0/float(r["win"])) / total_inv if total_inv > 0 else 0
            est_amt = net_pool * share
            est_bet = fmt_money(est_amt)
            est_pct = f"{share*100:.1f}%"
        except:
            pass
        base_amt    = state["base_est_bet"].get(no, 0.0)
        base_bet_str= fmt_money(base_amt) if base_amt > 0 else "—"
        cum_diff_str, cum_diff_css, cum_diff_pct = "—", "neutral", ""
        try:
            if base_amt > 0:
                cd_val       = est_amt - base_amt
                sign         = "+" if cd_val >= 0 else "-"
                cum_diff_str = f"{sign}{fmt_money(abs(cd_val))}"
                cum_diff_css = "up" if cd_val >= 0 else "diluted"
                pv           = cd_val / base_amt * 100
                sign2        = "+" if pv >= 0 else ""
                cum_diff_pct = f"({sign2}{pv:.1f}%)"
        except:
            pass
        cum_in     = state["cum_flow"].get(no, 0.0)
        cum_in_str = ("+"+fmt_money(cum_in)) if cum_in > 0 else "—"
        ab         = state["_absorb"].get(no, {})
        flow       = ab.get("flow", 0)
        absorb_pct = ab.get("absorb_pct", 0.0)
        share_pct  = ab.get("share_pct", 0.0)
        excess     = ab.get("excess", 0.0)
        pool_inc   = ab.get("pool_inc", 0)
        odds_drop  = ab.get("odds_drop", 0.0)
        odds_accel = ab.get("odds_accel", 0.0)
        if flow > 0:   flow_str, flow_css = f"▲ +{fmt_money(flow)}", "up"
        elif flow < 0: flow_str, flow_css = f"～ {fmt_money(flow)}", "diluted"
        else:          flow_str, flow_css = "—", "neutral"
        accel = state["_accels"].get(no, 0.0)
        if accel > 2000:   accel_str, accel_css = f"🚀 +{fmt_money(accel)}", "hot"
        elif accel > 0:    accel_str, accel_css = f"↗ +{fmt_money(accel)}", "up"
        elif accel < 0:    accel_str, accel_css = f"↘ -{fmt_money(abs(accel))}", "diluted"
        else:              accel_str, accel_css = "→", "neutral"
        if pool_inc > 500 and absorb_pct != 0:
            if excess >= 15:   absorb_str, absorb_css = f"🔥 {absorb_pct:.1f}% (+{excess:.1f}%)", "hot"
            elif excess >= 5:  absorb_str, absorb_css = f"⬆ {absorb_pct:.1f}% (+{excess:.1f}%)", "up"
            elif excess >= 0:  absorb_str, absorb_css = f"= {absorb_pct:.1f}%", "neutral"
            else:              absorb_str, absorb_css = f"⬇ {absorb_pct:.1f}% ({excess:.1f}%)", "diluted"
        else:
            absorb_str, absorb_css = "—", "neutral"
        if odds_accel > 1 and odds_drop > 1: odrop_str, odrop_css = f"⚡加速 -{odds_drop:.1f}%", "hot"
        elif odds_drop > 0:                  odrop_str, odrop_css = f"↘ -{odds_drop:.1f}%", "up"
        elif odds_drop < 0:                  odrop_str, odrop_css = f"↗ +{abs(odds_drop):.1f}%", "diluted"
        else:                                odrop_str, odrop_css = "—", "neutral"
        sms_score = state["_sms"].get(no, 0.0)
        if sms_score >= 5:   sms_str, sms_css = f"🏆 {sms_score:.1f}", "hot"
        elif sms_score >= 1: sms_str, sms_css = f"⭐ {sms_score:.1f}", "up"
        elif sms_score > 0:  sms_str, sms_css = f"{sms_score:.1f}", "neutral"
        else:                sms_str, sms_css = "—", "neutral"
        try:
            curr_o       = float(r["win"])
            min_o        = state["min_odds"].get(no, curr_o)
            rise_from_min= (curr_o - min_o) / min_o * 100 if min_o > 0 else 0
        except:
            rise_from_min = 0
        is_suspicious = rise_from_min > 50 and cum_in > 100000
        try:
            curr_o2 = float(r["win"]); steady = 0.0
            if curr_o2 >= 15 and cum_in >= 200000:
                flow_hist2 = list(state["flow_history"].get(no, []))[-5:]
                if sum(1 for f in flow_hist2 if f > 0) >= 3:
                    steady = round(cum_in / 10000.0 * (curr_o2 / 20.0), 2)
        except:
            steady = 0.0
        rise_pct_val = state["cum_rise"].get(no, 0.0)
        rci_score    = calc_rci(no, cum_in, rise_pct_val)
        if rci_score >= 100:  rci_str, rci_css = f"🌊 {rci_score:.1f}", "hot"
        elif rci_score >= 30: rci_str, rci_css = f"↗ {rci_score:.1f}", "up"
        elif rci_score > 0:   rci_str, rci_css = f"{rci_score:.1f}", "neutral"
        else:                 rci_str, rci_css = "—", "neutral"
        alert_flags = state["_alerts"].get(no, [])
        alert_str   = " ".join(alert_flags) if alert_flags else ""
        rows.append({
            **r,
            "base_win": base_win, "prev_win": prev_win,
            "chg": chg_str, "trend": label, "trend_css": css,
            "est_bet": est_bet, "est_pct": est_pct, "base_bet": base_bet_str,
            "cum_diff": cum_diff_str, "cum_diff_css": cum_diff_css, "cum_diff_pct": cum_diff_pct,
            "cum_inflow": cum_in_str,
            "flow": flow_str, "flow_css": flow_css,
            "accel": accel_str, "accel_css": accel_css,
            "absorb": absorb_str, "absorb_css": absorb_css,
            "odrop": odrop_str, "odrop_css": odrop_css,
            "sms": sms_str, "sms_css": sms_css, "sms_raw": sms_score,
            "alert": alert_str,
            "is_suspicious": is_suspicious, "rise_from_min": round(rise_from_min,1),
            "steady": steady,
            "rci": rci_str, "rci_css": rci_css, "rci_raw": rci_score,
        })
    return jsonify({
        "rows": rows,
        "top_down": state["top_down"], "top_up": state["top_up"],
        "top_suspicious": state["top_suspicious"],
        "top_steady": state["top_steady"], "top_rci": state["top_rci"],
        "alerts": state["alerts"],
        "update_count": state["update_count"], "last_update": state["last_update"],
        "base_time": state["base_time"], "status": state["status"],
        "has_error": state["has_error"], "running": state["running"],
        "race_date": state["race_date"], "venue_name": state["venue_name"],
        "race_no": state["race_no"], "interval": state["interval"],
        "history":        {k:v for k,v in state["history"].items()},
        "bet_history":    {k:v for k,v in state["bet_history"].items()},
        "flow_history":   {k:v for k,v in state["flow_history"].items()},
        "absorb_history": {k:v for k,v in state["absorb_history"].items()},
        "sms_history":    {k:v for k,v in state["sms_history"].items()},
        "timestamps":     state["timestamps"],
        "horses":         {r["no"]:r["name"] for r in state["data"]},
        "win_pool":       state["win_pool"],
        "win_pool_history": state["win_pool_history"],
    })

from flask import send_file

@app.route("/download_log")
def download_log():
    path = get_log_path()
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "Log 不存在，請先開始監察"}), 404
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
