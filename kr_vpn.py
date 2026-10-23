# -*- coding: utf-8 -*-
import json
import os
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
from tkinter import ttk

APP_DIR = r"C:\Users\lengu\kr-vpn"
MIHOMO_EXE = os.path.join(APP_DIR, "mihomo-windows-amd64-compatible.exe")
API = "http://127.0.0.1:9090"
PROXY = "http://127.0.0.1:7890"
IP_URLS = [
    "https://ipinfo.io/json",
    "https://api.ip.sb/geoip",
    "http://ip-api.com/json/?fields=query,city,country,countryCode,isp",
]
DELAY_URL = "https://www.gstatic.com/generate_204"
TEN = "Le Nguyen Tat Thang"

BG = "#0f172a"
CARD = "#1e293b"
TXT = "#e2e8f0"
SUB = "#94a3b8"
GREEN = "#22c55e"
RED = "#ef4444"
BLUE = "#3b82f6"
AMBER = "#f59e0b"

_no_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with _no_proxy.open(req, timeout=10) as r:
        txt = r.read().decode("utf-8", "replace")
    return json.loads(txt) if txt.strip() else None


def mihomo_running():
    try:
        api("GET", "/version")
        return True
    except Exception:
        return False


def start_mihomo():
    if mihomo_running():
        return True
    if not os.path.exists(MIHOMO_EXE):
        return False
    subprocess.Popen(
        [MIHOMO_EXE, "-d", APP_DIR],
        cwd=APP_DIR,
        creationflags=0x08000000,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        time.sleep(0.5)
        if mihomo_running():
            return True
    return False


_SKIP_TYPES = {"Selector", "URLTest", "Fallback", "LoadBalance", "Pass", "Direct", "Reject", "Compatible"}
_SKIP_NAMES = ("GLOBAL", "PASS", "DIRECT", "REJECT")


def list_kr_nodes():
    data = api("GET", "/proxies")
    out = []
    for name, info in (data or {}).get("proxies", {}).items():
        if "KR" in name and info.get("type") not in _SKIP_TYPES and not name.startswith(_SKIP_NAMES):
            out.append(name)
    return sorted(out)


def test_delay(name, timeout=6):
    enc = urllib.parse.quote(name, safe="")
    url = urllib.parse.quote(DELAY_URL, safe="")
    try:
        d = api("GET", "/proxies/{}/delay?timeout={}&url={}".format(enc, timeout * 1000, url))
        return d.get("delay")
    except Exception:
        return None


def set_mode(mode):
    api("PATCH", "/configs", {"mode": mode})


def select_global(name):
    api("PUT", "/proxies/GLOBAL", {"name": name})


def get_ip(timeout=12):
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    )
    last = None
    for u in IP_URLS:
        try:
            with op.open(u, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            ip = data.get("ip") or data.get("query")
            cc = data.get("countryCode") or data.get("country_code") or data.get("country") or ""
            if cc in ("KR", "South Korea", "Korea (the Republic of)"):
                cc = "KR"
            return {
                "ip": ip,
                "city": data.get("city") or "",
                "country": cc,
                "org": data.get("org") or data.get("isp") or "",
            }
        except Exception as e:
            last = e
    raise RuntimeError("khong kiem tra duoc IP: {}".format(last))


class App:
    def __init__(self, root):
        self.root = root
        self.state_on = False
        self.busy = False
        root.title("KR VPN — " + TEN)
        root.configure(bg=BG)
        try:
            root.iconbitmap(os.path.join(APP_DIR, "kr.ico"))
        except Exception:
            pass
        w = 420
        h = root.winfo_screenheight()
        x = max(0, root.winfo_screenwidth() - w - 12)
        root.geometry("{}x{}+{}+0".format(w, h, x))
        root.minsize(420, 600)
        self._build()
        self.log("Sẵn sàng. Nhấn \"BẬT IP HÀN\" là chạy.")
        self.refresh_nodes()
        self.refresh_status()
        self.root.after(30000, self._tick)

    def _build(self):
        root = self.root
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=CARD, background=CARD,
                        foreground=TXT, arrowcolor=SUB, bordercolor=CARD)
        style.map("TCombobox", fieldbackground=[("readonly", CARD)],
                  foreground=[("readonly", TXT)])
        style.configure("TCheckbutton", background=BG, foreground=TXT)
        style.map("TCheckbutton", background=[("active", BG)])
        style.configure("Horizontal.TProgressbar",
                        troughcolor=CARD, background=GREEN, thickness=10)

        outer = tk.Frame(root, bg=BG)
        outer.pack(fill="both", expand=True, padx=14, pady=(12, 10))

        # header
        head = tk.Frame(outer, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="★  KR VPN  ★", font=("Segoe UI", 16, "bold"),
                 fg="#38bdf8", bg=BG).pack(side="left")
        tk.Label(head, text=TEN, font=("Segoe UI", 9, "italic"),
                 fg=SUB, bg=BG, pady=6).pack(side="right")

        # IP card
        card = tk.Frame(outer, bg=CARD, highlightbackground="#334155",
                        highlightthickness=1)
        card.pack(fill="x", pady=(14, 6))
        self.lbl_ip = tk.Label(card, text="IP: ...", font=("Segoe UI", 18, "bold"),
                               fg=TXT, bg=CARD, pady=14)
        self.lbl_ip.pack(fill="x")
        self.lbl_meta = tk.Label(card, text="", font=("Segoe UI", 9),
                                 fg=SUB, bg=CARD, wraplength=380, pady=10)
        self.lbl_meta.pack(fill="x", padx=10)

        # status + progress
        self.status_var = tk.StringVar(value="Sẵn sàng")
        tk.Label(outer, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg=SUB, bg=BG, anchor="w").pack(fill="x", pady=(8, 2))
        self.pb = ttk.Progressbar(outer, mode="indeterminate",
                                  style="Horizontal.TProgressbar")
        self.pb.pack(fill="x")

        # buttons
        bwrap = tk.Frame(outer, bg=BG)
        bwrap.pack(fill="x", pady=(12, 4))

        def mkbtn(parent, text, color, cmd, active=None):
            b = tk.Button(parent, text=text, font=("Segoe UI", 12, "bold"),
                          bg=color, fg="white", bd=0, relief="flat",
                          activebackground=active or color, activeforeground="white",
                          height=2, cursor="hand2", command=cmd)
            return b

        self.btn_on = mkbtn(bwrap, "▶   BẬT IP HÀN", GREEN, self.turn_on, "#16a34a")
        self.btn_on.pack(fill="x", pady=(0, 8))
        self.btn_off = mkbtn(bwrap, "■   TẮT (IP THƯỜNG)", RED, self.turn_off, "#dc2626")
        self.btn_off.pack(fill="x", pady=(0, 8))
        self.btn_check = mkbtn(bwrap, "⟳   KIỂM TRA IP", BLUE, self.refresh_status, "#2563eb")
        self.btn_check.pack(fill="x")

        # node card
        ncard = tk.Frame(outer, bg=CARD, highlightbackground="#334155",
                         highlightthickness=1)
        ncard.pack(fill="x", pady=(12, 4))
        tk.Label(ncard, text="Node Hàn Quốc", font=("Segoe UI", 10, "bold"),
                 fg=TXT, bg=CARD, anchor="w").pack(fill="x", padx=10, pady=(8, 2))
        row = tk.Frame(ncard, bg=CARD)
        row.pack(fill="x", padx=10, pady=(0, 6))
        self.node_var = tk.StringVar()
        self.cmb = ttk.Combobox(row, textvariable=self.node_var, state="readonly")
        self.cmb.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.btn_use = tk.Button(row, text="Dùng", font=("Segoe UI", 9, "bold"),
                                 bg="#475569", fg="white", bd=0, relief="flat",
                                 padx=14, cursor="hand2", command=self.use_selected)
        self.btn_use.pack(side="left")
        self.auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ncard, text="Tự đổi node khi node chết",
                        variable=self.auto_var).pack(anchor="w", padx=10, pady=(0, 8))

        # log
        lwrap = tk.Frame(outer, bg=BG)
        lwrap.pack(fill="both", expand=True, pady=(10, 0))
        tk.Label(lwrap, text="NHẬT KÝ", font=("Segoe UI", 9, "bold"),
                 fg=SUB, bg=BG, anchor="w").pack(fill="x")
        self.lst = tk.Listbox(lwrap, bg="#020617", fg=TXT, bd=0,
                              relief="flat", font=("Consolas", 9),
                              selectbackground=BLUE, highlightthickness=1,
                              highlightcolor="#334155")
        self.lst.pack(fill="both", expand=True, pady=(4, 0))

    def log(self, msg):
        self.lst.insert("end", time.strftime("[%H:%M:%S] ") + msg)
        self.lst.see("end")

    def _set_status(self, text):
        self.status_var.set(text)

    def _busy_ui(self, on):
        state = "disabled" if on else "normal"
        for b in (self.btn_on, self.btn_off, self.btn_check, self.btn_use):
            b.config(state=state)
        if on:
            self.pb.config(mode="indeterminate")
            self.pb.start(14)
        else:
            self.pb.stop()
            self.pb.config(mode="indeterminate")
            self.pb["value"] = 0

    def _set_prog(self, i, n):
        self.pb.stop()
        self.pb.config(mode="determinate", maximum=max(1, n), value=i)

    def async_task(self, fn, done=None):
        if self.busy:
            self.log("Đang bận, chờ chút...")
            return
        self.busy = True
        self._busy_ui(True)

        def wrap():
            try:
                res = fn()
                err = None
            except Exception as e:
                res, err = None, e
            self.root.after(0, lambda: self._finish(res, err, done))

        threading.Thread(target=wrap, daemon=True).start()

    def _finish(self, res, err, done):
        self.busy = False
        self._busy_ui(False)
        if err is not None:
            self._set_status("Có lỗi — xem nhật ký")
            self.log("LỖI: " + str(err))
            return
        if done:
            done(res)

    def _show_ip(self, ip, now):
        if ip:
            country = ip.get("country", "?")
            color = GREEN if country == "KR" else RED
            self.lbl_ip.config(
                text="IP:  {} — {}, {}".format(ip.get("ip"), ip.get("city", ""), country),
                fg=color,
            )
            self.lbl_meta.config(
                text="ISP: {}\nnode: {}".format(ip.get("org", ""), now)
            )
        else:
            self.lbl_ip.config(text="IP:  không kiểm tra được", fg=AMBER)
            self.lbl_meta.config(text="node: {}".format(now))

    def refresh_status(self, silent=False):
        self._set_status("Đang kiểm tra IP...")

        def work():
            running = mihomo_running()
            mode = now = ip = None
            if running:
                try:
                    mode = api("GET", "/configs").get("mode")
                    now = api("GET", "/proxies/GLOBAL").get("now")
                except Exception:
                    pass
                try:
                    ip = get_ip(timeout=10)
                except Exception:
                    ip = None
            return running, mode, now, ip

        def done(res):
            running, mode, now, ip = res
            if not running:
                self.lbl_ip.config(text="IP:  (đang tắt)", fg=SUB)
                self.lbl_meta.config(text="Core chưa chạy — nhấn BẬT IP HÀN")
                self._set_status("Core stopped")
                return
            self._show_ip(ip, now)
            if ip and ip.get("country") == "KR":
                self.state_on = True
                self._set_status("Đang bật IP Hàn ✓ (mode: {})".format(mode))
            elif self.state_on and self.auto_var.get():
                if not silent:
                    self.log("Mất IP Hàn — tự tìm node mới...")
                self._set_status("Mất IP Hàn — tự đổi node...")
                self.turn_on(silent=True)
            else:
                self._set_status("IP thường (mode: {})".format(mode))

        self.async_task(work, done)

    def turn_on(self, silent=False):
        self._set_status("Đang bật IP Hàn...")

        def work():
            if not start_mihomo():
                raise RuntimeError("Không khởi động được VPN core")
            nodes = list_kr_nodes()
            if not nodes:
                raise RuntimeError("Hết node Hàn trong subscription")
            random.shuffle(nodes)
            limit = nodes[:30]
            for i, n in enumerate(limit, 1):
                self.root.after(0, lambda i=i: self._set_prog(i, len(limit)))
                self.root.after(
                    0, lambda i=i: self._set_status("Đang thử node {}/{}...".format(i, len(limit)))
                )
                d = test_delay(n)
                if d:
                    self.root.after(0, lambda d=d: self._set_status("Node OK ({}ms) — kết nối...".format(d)))
                    set_mode("global")
                    select_global(n)
                    time.sleep(0.3)
                    try:
                        ip = get_ip(timeout=10)
                    except Exception:
                        ip = None
                    return n, d, ip
            raise RuntimeError("Không node Hàn nào chạy được")

        def done(res):
            n, d, ip = res
            self.state_on = True
            self.cmb.set(n)
            if ip and ip.get("country") == "KR":
                self.log(
                    "BẬT OK ✓ {} ({}ms) → IP {} {}, Hàn Quốc".format(
                        n, d, ip.get("ip"), ip.get("city", "")
                    )
                )
                self._set_status("ĐANG BẬT IP HÀN ✓")
            else:
                self.log("Đã chọn {} ({}ms), IP chưa phải Hàn".format(n, d))
                self._set_status("Đã chọn node nhưng IP chưa phải Hàn")
            self._show_ip(ip, n)

        self.async_task(work, done)

    def turn_off(self):
        self._set_status("Đang tắt...")

        def work():
            if not mihomo_running():
                return None
            set_mode("global")
            select_global("DIRECT")
            time.sleep(0.3)
            try:
                ip = get_ip(timeout=10)
            except Exception:
                ip = None
            return ip

        def done(ip):
            self.state_on = False
            self._show_ip(ip, "DIRECT (tắt)")
            self.log(
                "Đã tắt. IP hiện tại: "
                + (
                    "{} {}, {}".format(ip.get("ip"), ip.get("city", ""), ip.get("country"))
                    if ip
                    else "?"
                )
            )
            self._set_status("ĐÃ TẮT — IP thường")

        self.async_task(work, done)

    def use_selected(self):
        node = self.node_var.get()
        if not node:
            return
        self.log("Dùng node: " + node)
        self._set_status("Đang thử node đã chọn...")

        def work():
            d = test_delay(node)
            if not d:
                raise RuntimeError("Node này đã chết")
            set_mode("global")
            select_global(node)
            time.sleep(0.3)
            try:
                ip = get_ip(timeout=10)
            except Exception:
                ip = None
            return d, ip

        def done(res):
            d, ip = res
            self.state_on = True
            self.log("Đã chọn node ({}ms)".format(d))
            self._show_ip(ip, node)
            self._set_status("Đã chuyển node ✓ ({}ms)".format(d))

        self.async_task(work, done)

    def refresh_nodes(self):
        def work():
            if not start_mihomo():
                raise RuntimeError("Không chạy được VPN core")
            return list_kr_nodes()

        def done(nodes):
            self.cmb.config(values=nodes)
            self.log("Có {} node Hàn".format(len(nodes)))
            if nodes and not self.node_var.get():
                self.cmb.set(nodes[0])

        self.async_task(work, done)

    def _tick(self):
        if self.auto_var.get() and self.state_on and not self.busy:
            self.refresh_status(silent=True)
        self.root.after(30000, self._tick)


def selftest():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("mihomo running:", mihomo_running())
    if not start_mihomo():
        print("cannot start mihomo")
        return 1
    nodes = list_kr_nodes()
    print("KR nodes:", len(nodes))
    for n in nodes[:3]:
        print(" delay", n, test_delay(n))
    ip = get_ip()
    print("via proxy:", ip)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    root = tk.Tk()
    App(root)
    root.mainloop()
