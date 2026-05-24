import os, time, json, random, requests, threading, warnings, sys
from datetime import datetime, timedelta, timezone

warnings.filterwarnings("ignore")

# Cấu hình file
CONFIG_FILE = "config_run.json"
ACCOUNTS_FILE = "accounts.json"
API_BASE = "https://gateway.golike.net/api"

# Màu sắc chuyên dụng cho Termux
R = "\033[1;31m"; G = "\033[1;32m"; Y = "\033[1;33m"; B = "\033[1;34m"
P = "\033[1;35m"; C = "\033[1;36m"; W = "\033[1;37m"; X = "\033[0m"
M = "\033[1;35m"

# Danh sách 14 User-Agent đa dạng thiết bị
U_AGENTS = [
    "Mozilla/5.0 (Linux; Android 9; SM-A705F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-X906C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2012K11AC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; V2183A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; OPPO CPH2185) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Sony XQ-DQ72) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; moto g(9) plus) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; ASUS_I005D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Nokia 7.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36"
]

print_lock = threading.Lock()
account_pool = []
pool_lock = threading.Lock()

def save_run_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f)

def load_run_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return None

def get_vn_time():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S')

def rq(m, u, headers, **k):
    local_session = requests.Session()
    headers["User-Agent"] = random.choice(U_AGENTS)
    for _ in range(3):
        try:
            r = local_session.request(m, u, headers=headers, timeout=15, **k)
            if r.status_code == 200: return r.json()
            if r.status_code == 429: time.sleep(10)
            if r.status_code == 400: return r.json()
        except: pass
        time.sleep(2)
    return None

def get_user_info(h):
    res = rq("GET", f"{API_BASE}/user", headers=h)
    if res and res.get("status") == 200:
        return res.get("data", {}).get("name", "Người dùng")
    return "Tài khoản"

def hien_thi_banner():
    os.system('clear')
    banner = f"""
{B}  __________ _   __ __  __             {B}       ______     
{M} /_  __/  / / | / // / / /             {M}     .-.  .-.     
{P}  / /  / / /  |/ // /_/ /              {P}    |   \/   |    
{Y} / / _/ / / /|  // __  /               {Y}   \        /    
{G}/_/ /___//_/ |_//_/ /_/                {G}    ` - . - `  ☠  {X}
{Y}───────────────────────────────────────────────────────────────────────────{X}
{G} ▶ Tác giả:   {W}TINH89 {X}
{G} ▶ Phiên bản: {W}V.2026 {X}
{G} ▶ Thời gian: {W}{get_vn_time()}{X}
{Y}───────────────────────────────────────────────────────────────────────────{X}
"""
    print(banner)

def draw_thread_box(thread_idx, name, job_type, status, countdown, done, maxj, xu, total_xu):
    line_pos = 14 + (thread_idx * 2)
    with print_lock:
        sys.stdout.write(f"\033[{line_pos};1H\033[K")
        sys.stdout.write(f"{B}[L{thread_idx+1}]{X} {P}{name:10.10}{X} {job_type} -> {status}\n")
        sys.stdout.write(f"\033[{line_pos+1};1H\033[K")
        sys.stdout.write(f"   {C}Tiến độ:{X} {W}{done}/{maxj}{X} | {C}Đợi:{X} {Y}{countdown:>2}s{X} | {C}Tổng:{X} {G}{total_xu} xu{X}")
        sys.stdout.flush()

def worker(thread_idx, config, h):
    global account_pool
    total_luong_xu = 0
    while True:
        acc_data = None
        with pool_lock:
            if account_pool: acc_data = account_pool.pop(0)
        if not acc_data:
            lbl_wait_job = f"{Y}WAIT{X}"
            lbl_wait_status = f"{R}Đang đợi acc...{X}"
            draw_thread_box(thread_idx, "HẾT ACC", lbl_wait_job, lbl_wait_status, "0", 0, 0, 0, total_luong_xu)
            time.sleep(5); continue

        acc_id = str(acc_data['id'])
        name = acc_data.get('unique_username') or acc_data.get('nickname') or "TikTok"
        job_filter = ["follow", "like"] if config['choice'] == "3" else ["follow"] if config['choice'] == "1" else ["like"]
        done_acc = 0
        fail_count = 0
        start_scan_time = time.time()

        while done_acc < config['maxj']:
            elapsed_time = int(time.time() - start_scan_time)
            if elapsed_time >= 300:
                lbl_tout = f"{R}T.OUT{X}"
                for i in range(10, 0, -1):
                    status_tout = f"{R}QUÁ 5 PHÚT -> ĐỔI {i}S{X}"
                    draw_thread_box(thread_idx, name, lbl_tout, status_tout, str(i), done_acc, config['maxj'], 0, total_luong_xu)
                    time.sleep(1)
                break

            lbl_scan = f"{Y}Đang Quét.{elapsed_time}s{X}"
            status_scan = f"{C}Tìm job...{X}"
            draw_thread_box(thread_idx, name, lbl_scan, status_scan, "--", done_acc, config['maxj'], 0, total_luong_xu)
            
            job = rq("GET", f"{API_BASE}/advertising/publishers/tiktok/jobs", h, params={"account_id": acc_id})
            if not job or not job.get("data") or job.get("data") == []:
                time.sleep(3); continue

            d = job["data"]
            raw_type = d.get("type", "").lower()
            if not any(x in raw_type for x in job_filter):
                rq("POST", f"{API_BASE}/advertising/publishers/tiktok/skip-jobs", h, json={"ads_id": d.get("id"), "account_id": acc_id, "type": raw_type})
                continue

            start_scan_time = time.time()
            lbl_job = f"{G}{raw_type.upper()[:4]}{X}"
            delay = random.randint(config['dmin'], config['dmax'])
            for i in range(delay, 0, -1):
                status_run = f"{P}Làm job...{X}"
                draw_thread_box(thread_idx, name, lbl_job, status_run, str(i), done_acc, config['maxj'], 0, total_luong_xu)
                time.sleep(1)

            status_get = f"{Y}Nhận xu...{X}"
            draw_thread_box(thread_idx, name, lbl_job, status_get, "0", done_acc, config['maxj'], 0, total_luong_xu)
            res = rq("POST", f"{API_BASE}/advertising/publishers/tiktok/complete-jobs", h, json={"ads_id": d["id"], "account_id": acc_id})
            
            if res and res.get("status") == 200:
                xu_nhan = res.get("data", {}).get("prices", 0)
                if xu_nhan == 0:
                    status_text = f"{R}Lỗi 0 xu{X}"; fail_count += 1
                else:
                    status_text = f"{G}Thành công{X}"; total_luong_xu += xu_nhan; done_acc += 1; fail_count = 0
                draw_thread_box(thread_idx, name, lbl_job, status_text, "OK", done_acc, config['maxj'], xu_nhan, total_luong_xu)
                time.sleep(2)
            else:
                fail_count += 1
                rq("POST", f"{API_BASE}/advertising/publishers/tiktok/skip-jobs", h, json={"ads_id": d.get("id"), "account_id": acc_id, "type": raw_type})
                if fail_count >= config['max_fail']: break
        with pool_lock: account_pool.append(acc_data)
        time.sleep(2)

def main():
    global account_pool
    hien_thi_banner()

    # Sửa lỗi đọc file JSON an toàn
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f: 
                accounts = json.load(f)
        except: 
            accounts = [] # Nếu file lỗi thì tạo mới
    else: 
        accounts = []

    if accounts:
        print(f"{Y}DANH SÁCH TÀI KHOẢN ĐÃ LƯU:{X}")
        for i, acc in enumerate(accounts):
            # Dùng .get() để tránh lỗi nếu thiếu khóa 'name'
            print(f"{G}{i+1}.{X} {acc.get('name', 'Tài khoản ' + str(i+1))}")
        
        chon = input(f"{W}Chọn số tài khoản (hoặc Enter để nhập mới): {X}")
        if chon.isdigit() and int(chon) <= len(accounts):
            selected = accounts[int(chon)-1]
            a, t = selected['a'], selected['t']
        else:
            a = input(f"{W}Nhập Authorization mới: {X}"); t = input(f"{W}Nhập Token mới: {X}")
            name = get_user_info({"Authorization": a, "t": t})
            accounts.append({"name": name, "a": a, "t": t})
            with open(ACCOUNTS_FILE, "w") as f: json.dump(accounts, f, indent=4)
    else:
        a = input(f"{W}Authorization: {X}"); t = input(f"{W}Token: {X}")
        name = get_user_info({"Authorization": a, "t": t})
        accounts.append({"name": name, "a": a, "t": t})
        with open(ACCOUNTS_FILE, "w") as f: json.dump(accounts, f, indent=4)


    h = {"Authorization": a, "t": t}
    res = rq("GET", f"{API_BASE}/tiktok-account", headers=h)
    if not res or "data" not in res: print(f"{R}Lỗi Token/Auth!{X}"); return
    account_pool = res["data"]

    config = load_run_config()
    if config:
        print(f"\n⚙️ Cấu hình cũ: {config['choice']}, {config['dmin']}-{config['dmax']}s, {config['maxj']} Job/Acc")
        if input("Dùng cấu hình cũ? (Enter=Có, n=Mới): ").lower() == 'n': config = None

    if not config:
        config = {
            'choice': input(f"{W}1.Follow, 2.Like, 3.Cả 2: {X}"),
            'dmin': int(input(f"{W}Delay Min: {X}")),
            'dmax': int(input(f"{W}Delay Max: {X}")),
            'maxj': int(input(f"{W}Số Job mỗi acc: {X}")),
            'max_fail': 3,
        }
        save_run_config(config)

    try:
        num_threads = int(input(f"{W}Nhập số luồng (Mặc định=2): {X}") or 2)
    except: num_threads = 2

    hien_thi_banner()
    print(f"{Y}🚀 HỆ THỐNG ĐANG CHẠY {num_threads} LUỒNG SONG SONG...{X}\n")
    
    threads = []
    for i in range(num_threads):
        if i > 0: time.sleep(3)
        t = threading.Thread(target=worker, args=(i, config, h))
        t.daemon = True; t.start(); threads.append(t)

    try:
        while True: time.sleep(10)
    except KeyboardInterrupt: sys.exit()

if __name__ == "__main__":
    main()
