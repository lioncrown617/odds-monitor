import os
import json
import time
import threading
from datetime import datetime
from collections import defaultdict, deque

import requests
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

NODE_API = os.environ.get("NODE_API", "http://localhost:3000/odds")

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
    "interval": 3,
    "current_interval": 3,
    "url": "",
    "status": "等待設定...",
    "has_error": False,
    "top_down": [],
    "top_up": [],
    "top_acc": [],
    "alerts": [],
    "history": defaultdict(list),
    "bet_history": defaultdict(list),
    "flow_history": defaultdict(list),
    "absorb_history": defaultdict(list),
    "sms_history": defaultdict(list),
    "acc_history": defaultdict(list),
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
    "last_error_detail": "",
    "race_info": {},
}

TREND_THRESHOLD = 2
ACCEL_DROP_MIN = 2

monitor_thread = None

VENUE_NAME_MAP = {
    "ST": "沙田",
    "HV": "跑馬地",
    **{f"S{i}": f"特別賽事 S{i}" for i in range(1, 9)},
}

def parse_pool(pool_str):
    try:
        return float(str(pool_str).replace("$", "").replace(",", "").strip())
    except:
        return 0.0

def fmt_money(amt):
    a = abs(amt)
    if a >= 1_000_000:
        return f"${a/1_000_000:.2f}M"
    elif a >= 1_000:
        return f"${a/1_000:.1f}K"
    return f"${a:.0f}"

def fetch_odds_api(date_str, venue, race_no):
    try:
        resp = requests.get(NODE_API, params={
            "date": date_str,
            "venue": venue,
            "raceno": race_no,
        }, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            state["last_error_detail"] = data.get("error", "Node API 錯誤")
            return None, "", {}
        results = data.get("results", [])
        win_pool = data.get("win_pool", "")
        race_info = {
            "race_time": data.get("race_time", ""),
            "distance": data.get("distance", ""),
            "track": data.get("track", ""),
            "course": data.get("course", ""),
            "race_class": data.get("race_class", ""),
            "going": data.get("going", ""),
            "prize": data.get("prize", ""),
            "race_name": data.get("race_name", ""),
        }
        if not results:
            state["last_error_detail"] = "無賽馬數據"
            return None, "", {}
        return results, win_pool, race_info
    except Exception as e:
        state["last_error_detail"] = str(e)
        return None, "", {}

def calc_est_bets(data, pool_str):
    real_map = {}
    has_real = False
    for r in data:
        amt = float(r.get("win_investment", 0) or 0)
        real_map[r["no"]] = amt
        if amt > 0:
            has_real = True
    if has_real:
        return real_map

    pool_num = parse_pool(pool_str)
    net_pool = pool_num * (1 - 0.175)
    total_inv = sum(1.0 / float(r["win"]) for r in data if r["win"] not in ("", "SCR"))

    result = {}
    for r in data:
        try:
            share = (1.0 / float(r["win"])) / total_inv if total_inv > 0 else 0
            result[r["no"]] = net_pool * share
        except:
            result[r["no"]] = 0.0
    return result

def calc_trends(data):
    prev = state["prev_data"]
    base = state["base_data"]
    tc = state["trend_counter"]
    cd = state["cum_drop"]
    cr = state["cum_rise"]

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
    pos_e = [max(e, 0) for e in e_hist]
    E_eff = sum(pos_e) / len(pos_e) if pos_e else 0

    now_ts = time.time()
    hist = list(state["inflow_ts_history"][no])
    w_5min  = sum(amt for ts, amt in hist if now_ts - ts <= 300)
    w_15min = sum(amt for ts, amt in hist if now_ts - ts <= 900)
    w_30min = sum(amt for ts, amt in hist if now_ts - ts <= 1800)

    if cum_flow_val > 0 and w_5min / cum_flow_val > 0.4:
        Wt = 1.5    # 臨門集中型
    elif cum_flow_val > 0 and w_15min / cum_flow_val > 0.4:
        Wt = 1.35   # 中期持續型
    elif cum_flow_val > 0 and w_30min / cum_flow_val > 0.35:
        Wt = 1.2    # 分批累積型
    else:
        Wt = 1.0

    recent_flows = list(state["flow_history"][no])[-3:]
    if len(recent_flows) >= 3 and all(f <= 0 for f in recent_flows):
        Wt *= 0.5

    if len(recent_flows) >= 3:
        accels_local = [recent_flows[i] - recent_flows[i - 1] for i in range(1, len(recent_flows))]
        if all(f < 0 for f in recent_flows) and all(a < 0 for a in accels_local):
            Wt *= 0.7

    return round((F ** 1.2) * (1 + D / 10) * (1 + E_eff / 10) * Wt, 2)


def calc_acc_score(no, cum_flow_val):
    """分批累積型大戶識別"""
    inflow_hist = list(state["inflow_ts_history"][no])
    if len(inflow_hist) < 2:
        return 0.0

    big_entries = [(ts, amt) for ts, amt in inflow_hist if amt >= 10000]
    if len(big_entries) < 2:
        return 0.0

    time_span = (big_entries[-1][0] - big_entries[0][0]) / 60
    if time_span < 1.0:
        return 0.0

    consistency = len(big_entries) / max(len(inflow_hist), 1)
    F = cum_flow_val / 10000.0
    batch_bonus = min(len(big_entries) / 3.0, 2.0)

    return round(F ** 1.1 * consistency * batch_bonus, 2)


def calc_flow_and_signals(est_bets, win_pool_str, data):
    prev_bets = state["prev_est_bet"]
    prev_fl = state["prev_flow"]
    prev_pool = state["prev_pool"]
    prev_drop = state["prev_odds_drop"]
    cum_flow = state["cum_flow"]
    cum_drop_pct = state["cum_drop"]
    now_ts = time.time()

    curr_pool_num = parse_pool(win_pool_str)
    pool_increase = max((curr_pool_num - prev_pool) * (1 - 0.175), 0)
    total_inv = sum(1.0 / float(r["win"]) for r in data if r["win"] not in ("", "SCR"))

    flows = {}
    accels = {}
    absorbs = {}
    sms = {}
    alerts = {}

    for r in data:
        no = r["no"]
        win_str = r["win"]
        if win_str in ("", "SCR"):
            continue

        try:
            curr_odds = float(win_str)
        except:
            continue

        amt = est_bets.get(no, 0.0)
        prev_amt = prev_bets.get(no, None)
        flow = 0.0 if prev_amt is None else amt - prev_amt

        prev_flow_val = prev_fl.get(no, None)
        accel = 0.0 if prev_flow_val is None else flow - prev_flow_val

        if prev_amt is not None and flow > 0:
            cum_flow[no] = cum_flow.get(no, 0.0) + flow
            state["inflow_ts_history"][no].append((now_ts, flow))

        try:
            share_pct = (1.0 / curr_odds) / total_inv * 100 if total_inv > 0 else 0
        except:
            share_pct = 0.0

        absorb_pct = 0.0
        excess = 0.0
        if pool_increase > 500 and prev_amt is not None:
            absorb_pct = (flow / pool_increase) * 100
            excess = absorb_pct - share_pct
            state["e_history"][no].append(excess)

        prev_o_val = float(state["prev_data"].get(no, curr_odds) or curr_odds)
        try:
            odds_drop = (prev_o_val - curr_odds) / prev_o_val * 100 if prev_o_val > 0 else 0.0
        except:
            odds_drop = 0.0

        odds_accel = odds_drop - prev_drop.get(no, 0.0)
        sms_score = calc_sms_v2(no, cum_flow.get(no, 0.0), cum_drop_pct.get(no, 0.0))
        acc_score = calc_acc_score(no, cum_flow.get(no, 0.0))
        alert_flags = []

        tc_val = state["trend_counter"].get(no, 0)
        if tc_val >= ACCEL_DROP_MIN and odds_accel > 0.5:
            alert_flags.append(f"⚡賠率加速跌({odds_drop:.1f}%)")

        if flow >= 10000:
            alert_flags.append(f"💥突發大注{fmt_money(flow)}")

        try:
            min_o = state["min_odds"].get(no, curr_odds)
            rise_from_min = (curr_odds - min_o) / min_o * 100 if min_o > 0 else 0
            if rise_from_min > 50 and cum_flow.get(no, 0) > 100000:
                alert_flags.append(f"🔔疑似洗碼受益(反彈{rise_from_min:.0f}%)")
        except:
            pass

        recent_flows = list(state["flow_history"][no])[-3:]
        if len(recent_flows) >= 3:
            accels_local = [recent_flows[i] - recent_flows[i - 1] for i in range(1, len(recent_flows))]
            if all(f < 0 for f in recent_flows) and all(a < 0 for a in accels_local):
                alert_flags.append("🌊資金退潮警告")

        flows[no] = flow
        accels[no] = accel
        absorbs[no] = {
            "flow": round(flow),
            "absorb_pct": round(absorb_pct, 1),
            "share_pct": round(share_pct, 1),
            "excess": round(excess, 1),
            "pool_inc": round(pool_increase),
            "odds_drop": round(odds_drop, 2),
            "odds_accel": round(odds_accel, 2),
            "is_rescue": False,
        }

        sms[no] = sms_score
        sms[f"acc_{no}"] = acc_score
        alerts[no] = alert_flags

    return flows, accels, absorbs, sms, alerts


def get_trend_label(no):
    tc = state["trend_counter"]
    prev = state["prev_data"]
    data_dict = {r["no"]: r for r in state["data"]}
    count = tc.get(no, 0)

    try:
        curr = float(data_dict[no]["win"])
        p = float(prev[no]) if no in prev else curr
        pct = (p - curr) / p * 100 if p > 0 else 0
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
    base = state["base_data"]
    sms_map = state["_sms"]
    absorbs = state["_absorb"]
    tc = state["trend_counter"]
    cd = state["cum_drop"]
    cum_f = state["cum_flow"]

    sms_all = []

    for r in data:
        no = r["no"]
        sms_score = sms_map.get(no, 0.0)
        ab = absorbs.get(no, {})
        cum_in = cum_f.get(no, 0.0)

        if sms_score > 0:
            sms_all.append({
                "no": no,
                "name": r["name"],
                "win": r["win"],
                "base": base.get(no, "—"),
                "streak": max(tc.get(no, 0), 0),
                "drop": cd.get(no, 0),
                "cum_inflow": round(cum_in),
                "sms": sms_score,
                "excess": ab.get("excess", 0),
            })

    state["top_down"] = sorted(sms_all, key=lambda x: x["sms"], reverse=True)[:5]
    state["top_up"] = []

    # ★ 累積大戶 top3
    acc_list = []
    for r in data:
        no = r["no"]
        cum_in = cum_f.get(no, 0.0)
        acc_s = calc_acc_score(no, cum_in)
        if acc_s > 0:
            inflow_hist = list(state["inflow_ts_history"][no])
            big_entries = [(ts, amt) for ts, amt in inflow_hist if amt >= 10000]
            if len(big_entries) >= 2:
                time_span = round((big_entries[-1][0] - big_entries[0][0]) / 60, 1)
                acc_list.append({
                    "no": no,
                    "name": r["name"],
                    "win": r["win"],
                    "base": base.get(no, "—"),
                    "cum_inflow": round(cum_in),
                    "batch_count": len(big_entries),
                    "time_span": time_span,
                    "acc": acc_s,
                })
    state["top_acc"] = sorted(acc_list, key=lambda x: x["acc"], reverse=True)[:3]


def update_global_alerts(alerts_map, now):
    pass

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
        state["acc_history"][no].append(sms.get(f"acc_{no}", 0))

def get_log_path():
    date_str = state["race_date"].replace("-", "")
    venue = state["venue"]
    race_no = state["race_no"].zfill(2)
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
            "race_date": state["race_date"],
            "venue": state["venue"],
            "venue_name": state["venue_name"],
            "race_no": state["race_no"],
            "base_time": state["base_time"],
            "start_time": now,
            "race_info": state.get("race_info", {}),
        }

    snapshot = {"time": now, "win_pool": win_pool, "horses": []}

    for r in data:
        no = r["no"]
        ab = absorbs.get(no, {})

        snapshot["horses"].append({
            "no": r["no"],
            "name": r["name"],
            "win": r["win"],
            "place": r.get("place", ""),
            "base_win": state["base_data"].get(no, "—"),
            "est_bet": round(est_bets.get(no, 0)),
            "flow": round(flows.get(no, 0)),
            "cum_flow": round(state["cum_flow"].get(no, 0)),
            "absorb_pct": ab.get("absorb_pct", 0),
            "excess": ab.get("excess", 0),
            "pool_inc": ab.get("pool_inc", 0),
            "odds_drop": ab.get("odds_drop", 0),
            "cum_drop": state["cum_drop"].get(no, 0),
            "cum_rise": state["cum_rise"].get(no, 0),
            "sms": sms.get(no, 0),
            "acc": sms.get(f"acc_{no}", 0),
            "alerts": state["_alerts"].get(no, []),
        })

    log["snapshots"].append(snapshot)
    _save_log(log)

def finalize_log(now):
    log = _load_log()
    cum_f = state["cum_flow"]

    horses = [{
        "no": no,
        "name": next((r["name"] for r in state["data"] if r["no"] == no), no),
        "final_win": next((r["win"] for r in state["data"] if r["no"] == no), "—"),
        "cum_flow": round(v),
        "cum_drop": state["cum_drop"].get(no, 0),
        "cum_rise": state["cum_rise"].get(no, 0),
        "sms": state["_sms"].get(no, 0),
        "acc": calc_acc_score(no, v),
    } for no, v in cum_f.items() if v > 0]

    log["summary"] = {
        "end_time": now,
        "total_updates": state["update_count"],
        "base_time": state["base_time"],
        "final_pool": state["win_pool"],
        "total_alerts": 0,
        "top_sms": sorted(horses, key=lambda x: x["sms"], reverse=True)[:5],
        "top_acc": sorted(horses, key=lambda x: x["acc"], reverse=True)[:5],
        "horses_final": horses,
    }

    _save_log(log)
    print(f"[LOG] 已儲存：{get_log_path()}")

def monitor_loop():
    state["status"] = "連接 Node.js API 中..."
    state["has_error"] = False

    while state["running"]:
        now = datetime.now().strftime("%H:%M:%S")
        data, win_pool, race_info = fetch_odds_api(
            state["race_date"], state["venue"], state["race_no"]
        )

        if data:
            state["has_error"] = False
            state["update_count"] += 1
            if race_info:
                state["race_info"] = race_info

            est_bets = calc_est_bets(data, win_pool)

            if not state["base_data"]:
                state["base_data"] = {r["no"]: r["win"] for r in data}
                state["base_time"] = now
                state["base_est_bet"] = dict(est_bets)

            flows, accels, absorbs, sms, alerts_map = calc_flow_and_signals(
                est_bets, win_pool, data
            )

            calc_trends(data)
            record_history(data, now, est_bets, flows, absorbs, sms)
            append_snapshot(now, data, est_bets, flows, absorbs, sms, win_pool)
            update_global_alerts(alerts_map, now)

            state["data"] = data
            state["prev_data"] = {r["no"]: r["win"] for r in data}
            state["prev_odds_drop"] = {no: absorbs[no]["odds_drop"] for no in absorbs}
            state["last_update"] = now
            state["win_pool"] = win_pool
            state["win_pool_history"].append({"time": now, "pool": win_pool})
            state["prev_flow"] = flows
            state["prev_est_bet"] = dict(est_bets)
            state["prev_pool"] = parse_pool(win_pool)
            state["_accels"] = accels
            state["_absorb"] = absorbs
            state["_sms"] = sms
            state["_alerts"] = alerts_map

            calc_top3()
            iv = state["interval"]
            state["current_interval"] = iv
            state["status"] = f"✅ 正常監察中 · hkjc-api · {iv}s"

        else:
            state["has_error"] = True
            detail = state.get("last_error_detail", "")
            state["status"] = f"[{now}] 連接失敗 | {detail[:80]}"

        time.sleep(state["interval"])

    finalize_log(datetime.now().strftime("%H:%M:%S"))
    state["status"] = "監察已停止"
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
    state["race_date"] = d.get("date", datetime.now().strftime("%Y-%m-%d"))
    state["venue"] = d.get("venue", "ST")
    state["venue_name"] = VENUE_NAME_MAP.get(state["venue"], state["venue"])
    state["race_no"] = d.get("race_no", "1")
    state["interval"] = max(int(d.get("interval", 3)), 2)
    state["url"] = (
        f"https://bet.hkjc.com/ch/racing/wp/"
        f"{state['race_date']}/{state['venue']}/{state['race_no']}"
    )

    for k, v in [
        ("running", True), ("has_error", False), ("data", []),
        ("base_data", {}), ("base_est_bet", {}), ("prev_data", {}),
        ("prev_est_bet", {}), ("prev_flow", {}), ("prev_pool", 0.0),
        ("prev_odds_drop", {}), ("update_count", 0),
        ("top_down", []), ("top_up", []), ("top_acc", []), ("alerts", []),
        ("timestamps", []), ("win_pool", ""), ("win_pool_history", []),
        ("_accels", {}), ("_absorb", {}), ("_sms", {}), ("_alerts", {}),
        ("steady_scores", {}), ("current_interval", 3),
        ("status", "正在啟動..."), ("last_error_detail", ""),
        ("race_info", {}),
    ]:
        state[k] = v

    state["trend_counter"] = defaultdict(int)
    state["cum_drop"] = defaultdict(float)
    state["cum_rise"] = defaultdict(float)
    state["cum_flow"] = defaultdict(float)
    state["history"] = defaultdict(list)
    state["bet_history"] = defaultdict(list)
    state["flow_history"] = defaultdict(list)
    state["absorb_history"] = defaultdict(list)
    state["sms_history"] = defaultdict(list)
    state["acc_history"] = defaultdict(list)
    state["e_history"] = defaultdict(_deque5)
    state["inflow_ts_history"] = defaultdict(_deque60)
    state["min_odds"] = defaultdict(_inf)
    state["alert_cooldown"] = defaultdict(dict)

    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    return jsonify({"ok": True})

@app.route("/stop", methods=["POST"])
def stop():
    state["running"] = False
    return jsonify({"ok": True})

@app.route("/data")
def get_data():
    pool_num = parse_pool(state["win_pool"])
    net_pool = pool_num * (1 - 0.175)

    total_inv = sum(
        1.0 / float(r["win"])
        for r in state["data"] if r["win"] not in ("", "SCR")
    )

    rows = []

    for r in state["data"]:
        no = r["no"]
        label, css = get_trend_label(no)
        base_win = state["base_data"].get(no, "—")
        prev_win = state["prev_data"].get(no, "—")

        chg_str = "—"
        try:
            diff = float(r["win"]) - float(prev_win)
            pct = diff / float(prev_win) * 100
            sign = "+" if diff >= 0 else ""
            chg_str = f"{sign}{diff:.1f}({sign}{pct:.1f}%)"
        except:
            pass

        est_amt, est_bet, est_pct = 0.0, "—", "—"
        try:
            real_amt = float(r.get("win_investment", 0) or 0)
            if real_amt > 0:
                est_amt = real_amt
                est_bet = fmt_money(est_amt)
                est_pct = "真實"
            else:
                share = (1.0 / float(r["win"])) / total_inv if total_inv > 0 else 0
                est_amt = net_pool * share
                est_bet = fmt_money(est_amt)
                est_pct = f"{share * 100:.1f}%"
        except:
            pass

        base_amt = state["base_est_bet"].get(no, 0.0)
        base_bet_str = fmt_money(base_amt) if base_amt > 0 else "—"

        cum_diff_str, cum_diff_css, cum_diff_pct = "—", "neutral", ""
        try:
            if base_amt > 0:
                cd_val = est_amt - base_amt
                sign = "+" if cd_val >= 0 else "-"
                cum_diff_str = f"{sign}{fmt_money(abs(cd_val))}"
                cum_diff_css = "up" if cd_val >= 0 else "diluted"
                pv = cd_val / base_amt * 100
                sign2 = "+" if pv >= 0 else ""
                cum_diff_pct = f"({sign2}{pv:.1f}%)"
        except:
            pass

        cum_in = state["cum_flow"].get(no, 0.0)
        cum_in_str = ("+" + fmt_money(cum_in)) if cum_in > 0 else "—"

        ab = state["_absorb"].get(no, {})
        flow = ab.get("flow", 0)
        absorb_pct = ab.get("absorb_pct", 0.0)
        share_pct = ab.get("share_pct", 0.0)
        excess = ab.get("excess", 0.0)
        pool_inc = ab.get("pool_inc", 0)
        odds_drop = ab.get("odds_drop", 0.0)
        odds_accel = ab.get("odds_accel", 0.0)
        is_rescue = ab.get("is_rescue", False)

        if flow > 0:
            rescue_tag = "❄️" if is_rescue else ""
            flow_str, flow_css = f"▲ +{fmt_money(flow)}{rescue_tag}", "up"
        elif flow < 0:
            flow_str, flow_css = f"～ {fmt_money(flow)}", "diluted"
        else:
            flow_str, flow_css = "—", "neutral"

        accel = state["_accels"].get(no, 0.0)
        if accel > 2000:
            accel_str, accel_css = f"🚀 +{fmt_money(accel)}", "hot"
        elif accel > 0:
            accel_str, accel_css = f"↗ +{fmt_money(accel)}", "up"
        elif accel < 0:
            accel_str, accel_css = f"↘ -{fmt_money(abs(accel))}", "diluted"
        else:
            accel_str, accel_css = "→", "neutral"

        if pool_inc > 500 and absorb_pct != 0:
            if excess >= 15:
                absorb_str, absorb_css = f"🔥 {absorb_pct:.1f}% (+{excess:.1f}%)", "hot"
            elif excess >= 5:
                absorb_str, absorb_css = f"⬆ {absorb_pct:.1f}% (+{excess:.1f}%)", "up"
            elif excess >= 0:
                absorb_str, absorb_css = f"= {absorb_pct:.1f}%", "neutral"
            else:
                absorb_str, absorb_css = f"⬇ {absorb_pct:.1f}% ({excess:.1f}%)", "diluted"
        else:
            absorb_str, absorb_css = "—", "neutral"

        if odds_accel > 1 and odds_drop > 1:
            odrop_str, odrop_css = f"⚡加速 -{odds_drop:.1f}%", "hot"
        elif odds_drop > 0:
            odrop_str, odrop_css = f"↘ -{odds_drop:.1f}%", "up"
        elif odds_drop < 0:
            odrop_str, odrop_css = f"↗ +{abs(odds_drop):.1f}%", "diluted"
        else:
            odrop_str, odrop_css = "—", "neutral"

        sms_score = state["_sms"].get(no, 0.0)
        acc_score = state["_sms"].get(f"acc_{no}", 0.0)

        if sms_score >= 5:
            sms_str, sms_css = f"🏆 {sms_score:.1f}", "hot"
        elif sms_score >= 1:
            sms_str, sms_css = f"⭐ {sms_score:.1f}", "up"
        elif sms_score > 0:
            sms_str, sms_css = f"{sms_score:.1f}", "neutral"
        else:
            sms_str, sms_css = "—", "neutral"

        try:
            curr_o = float(r["win"])
            min_o = state["min_odds"].get(no, curr_o)
            rise_from_min = (curr_o - min_o) / min_o * 100 if min_o > 0 else 0
        except:
            rise_from_min = 0

        alert_str = " ".join(state["_alerts"].get(no, []))

        rows.append({
            **r,
            "base_win": base_win,
            "prev_win": prev_win,
            "chg": chg_str,
            "trend": label,
            "trend_css": css,
            "est_bet": est_bet,
            "est_pct": est_pct,
            "base_bet": base_bet_str,
            "cum_diff": cum_diff_str,
            "cum_diff_css": cum_diff_css,
            "cum_diff_pct": cum_diff_pct,
            "cum_inflow": cum_in_str,
            "flow": flow_str,
            "flow_css": flow_css,
            "flow_raw": round(flow),
            "accel": accel_str,
            "accel_css": accel_css,
            "absorb": absorb_str,
            "absorb_css": absorb_css,
            "odrop": odrop_str,
            "odrop_css": odrop_css,
            "sms": sms_str,
            "sms_css": sms_css,
            "sms_raw": sms_score,
            "acc_raw": acc_score,
            "alert": alert_str,
            "is_suspicious": False,
            "rise_from_min": round(rise_from_min, 1),
        })

    return jsonify({
        "rows": rows,
        "top_down": state["top_down"],
        "top_up": state["top_up"],
        "top_acc": state["top_acc"],
        "alerts": [],
        "update_count": state["update_count"],
        "last_update": state["last_update"],
        "base_time": state["base_time"],
        "status": state["status"],
        "has_error": state["has_error"],
        "running": state["running"],
        "race_date": state["race_date"],
        "venue_name": state["venue_name"],
        "race_no": state["race_no"],
        "interval": state["interval"],
        "current_interval": state["current_interval"],
        "history": {k: v for k, v in state["history"].items()},
        "bet_history": {k: v for k, v in state["bet_history"].items()},
        "flow_history": {k: v for k, v in state["flow_history"].items()},
        "absorb_history": {k: v for k, v in state["absorb_history"].items()},
        "sms_history": {k: v for k, v in state["sms_history"].items()},
        "acc_history": {k: v for k, v in state["acc_history"].items()},
        "timestamps": state["timestamps"],
        "horses": {r["no"]: r["name"] for r in state["data"]},
        "win_pool": state["win_pool"],
        "win_pool_history": state["win_pool_history"],
        "error_detail": state.get("last_error_detail", ""),
        "race_info": state.get("race_info", {}),
    })

@app.route("/download_log")
def download_log():
    path = get_log_path()
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "Log 不存在，請先開始監察"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
