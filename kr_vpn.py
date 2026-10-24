# -*- coding: utf-8 -*-
import ctypes
import json
import os
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from tkinter import ttk

try:
    import winreg
except ImportError:
    winreg = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MIHOMO_EXE = os.path.join(APP_DIR, "mihomo-windows-amd64-compatible.exe")
API = "http://127.0.0.1:9090"
PROXY = "http://127.0.0.1:7890"
SYSTEM_PROXY = "127.0.0.1:7890"
SYSTEM_BYPASS = "localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;192.168.*;<local>"
SITE_URL = "https://yes.skbroadband.com/"
PROXY_BACKUP = os.path.join(APP_DIR, ".proxy_backup.json")
LAST_NODE = os.path.join(APP_DIR, ".last_node.txt")
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


def _notify_proxy_change():
    try:
        wininet = ctypes.windll.Wininet
        wininet.InternetSetOptionW(0, 39, 0, 0)
        wininet.InternetSetOptionW(0, 37, 0, 0)
    except Exception:
        pass


def _reg_read(key, name):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except FileNotFoundError:
        return None
    except OSError:
        return None


def system_proxy_on():
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        ) as key:
            return bool(_reg_read(key, "ProxyEnable")) and _reg_read(key, "ProxyServer") == SYSTEM_PROXY
    except OSError:
        return False


def enable_system_proxy():
    if winreg is None:
        return False
    path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            old = {
                "ProxyEnable": _reg_read(key, "ProxyEnable"),
                "ProxyServer": _reg_read(key, "ProxyServer"),
                "ProxyOverride": _reg_read(key, "ProxyOverride"),
                "AutoConfigURL": _reg_read(key, "AutoConfigURL"),
            }
        if not os.path.exists(PROXY_BACKUP):
            with open(PROXY_BACKUP, "w", encoding="utf-8") as f:
                json.dump(old, f)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, SYSTEM_PROXY)
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, SYSTEM_BYPASS)
            try:
                winreg.DeleteValue(key, "AutoConfigURL")
            except FileNotFoundError:
                pass
        _notify_proxy_change()
        return True
    except OSError:
        return False


def disable_system_proxy():
    if winreg is None:
        return False
    path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            if os.path.exists(PROXY_BACKUP):
                with open(PROXY_BACKUP, "r", encoding="utf-8") as f:
                    old = json.load(f)
                for name, reg_type in (
                    ("ProxyServer", winreg.REG_SZ),
                    ("ProxyOverride", winreg.REG_SZ),
                    ("AutoConfigURL", winreg.REG_SZ),
                ):
                    val = old.get(name)
                    if val:
                        winreg.SetValueEx(key, name, 0, reg_type, val)
                    else:
                        try:
                            winreg.DeleteValue(key, name)
                        except FileNotFoundError:
                            pass
                if old.get("ProxyEnable") is not None:
                    winreg.SetValueEx(
                        key, "ProxyEnable", 0, winreg.REG_DWORD, int(old["ProxyEnable"])
                    )
                os.remove(PROXY_BACKUP)
        _notify_proxy_change()
        return True
    except OSError:
        return False


def site_ok(timeout=15):
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    )
    req = urllib.request.Request(
        SITE_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"},
    )
    try:
        with op.open(req, timeout=timeout) as r:
            return 200 <= r.status < 400
    except urllib.error.HTTPError as e:
        return 200 <= e.code < 400
    except Exception:
        return False


def saved_last_node():
    try:
        with open(LAST_NODE, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


def save_last_node(name):
    try:
        with open(LAST_NODE, "w", encoding="utf-8") as f:
            f.write(name)
    except OSError:
        pass


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
        self.btn_check.pack(fill="x", pady=(0, 8))
        self.btn_site = mkbtn(bwrap, "🌐   MỞ YES.SKBROADBAND", "#0284c7", self.open_site, "#0369a1")
        self.btn_site.pack(fill="x")

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
        proxy_state = "BẬT" if system_proxy_on() else "TẮT"
        if ip:
            country = ip.get("country", "?")
            color = GREEN if country == "KR" else RED
            self.lbl_ip.config(
                text="IP:  {} — {}, {}".format(ip.get("ip"), ip.get("city", ""), country),
                fg=color,
            )
            self.lbl_meta.config(
                text="ISP: {}\nnode: {}\nproxy hệ thống: {}".format(
                    ip.get("org", ""), now, proxy_state
                )
            )
        else:
            self.lbl_ip.config(text="IP:  không kiểm tra được", fg=AMBER)
            self.lbl_meta.config(
                text="node: {}\nproxy hệ thống: {}".format(now, proxy_state)
            )

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
                if not system_proxy_on() and enable_system_proxy():
                    self.log("Đã bật lại proxy hệ thống → " + SYSTEM_PROXY)
                    self._show_ip(ip, now)
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
            last = saved_last_node()
            if last in nodes:
                nodes.remove(last)
                nodes.insert(0, last)
            rest = [n for n in nodes if n != last]
            random.shuffle(rest)
            limit = ([last] if last in nodes else []) + rest
            first_kr = None
            for i, n in enumerate(limit, 1):
                self.root.after(0, lambda i=i: self._set_prog(i, len(limit)))
                self.root.after(
                    0, lambda i=i: self._set_status("Đang thử node {}/{}...".format(i, len(limit)))
                )
                d = test_delay(n, timeout=4)
                if not d:
                    continue
                self.root.after(0, lambda d=d: self._set_status("Node OK ({}ms) — kiểm tra IP...".format(d)))
                set_mode("global")
                select_global(n)
                time.sleep(0.3)
                try:
                    ip = get_ip(timeout=8)
                except Exception:
                    ip = None
                if not ip or ip.get("country") != "KR":
                    continue
                self.root.after(0, lambda n=n: self._set_status("IP Hàn OK — kiểm tra website..."))
                if site_ok(timeout=15):
                    return n, d, ip, True
                if first_kr is None:
                    first_kr = (n, d, ip)
            if first_kr is not None:
                n, d, ip = first_kr
                set_mode("global")
                select_global(n)
                time.sleep(0.3)
                return n, d, ip, False
            raise RuntimeError("Không node Hàn nào chạy được")

        def done(res):
            n, d, ip, site = res
            self.state_on = True
            self.cmb.set(n)
            save_last_node(n)
            self.log(
                "BẬT OK ✓ {} ({}ms) → IP {} {}, Hàn Quốc".format(
                    n, d, ip.get("ip"), ip.get("city", "")
                )
            )
            if site:
                self.log("yes.skbroadband.com: truy cập được ✓")
            else:
                self.log("Cảnh báo: chưa mở được yes.skbroadband.com bằng node này")
            if enable_system_proxy():
                self.log("Proxy hệ thống → {} (trình duyệt giờ đi qua Hàn)".format(SYSTEM_PROXY))
            else:
                self.log("Không bật được proxy hệ thống — kiểm tra quyền registry")
            self._set_status("ĐANG BẬT IP HÀN ✓" if site else "IP Hàn OK — website chưa chắc mở được")
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
            if disable_system_proxy():
                self.log("Đã trả proxy hệ thống về như cũ")
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
            if ip and ip.get("country") == "KR":
                self.state_on = True
                save_last_node(node)
                enable_system_proxy()
                self.log("Đã chọn node ({}ms) → IP Hàn, proxy hệ thống BẬT".format(d))
                self._set_status("Đã chuyển node ✓ ({}ms)".format(d))
            else:
                self.state_on = False
                self.log("Đã chọn node ({}ms) nhưng IP không phải Hàn".format(d))
                self._set_status("Node này không cho IP Hàn")
            self._show_ip(ip, node)

        self.async_task(work, done)

    def open_site(self):
        if not self.state_on or not system_proxy_on():
            self.log("Cần bật IP Hàn trước (proxy hệ thống chưa bật)")
            self._set_status("Hãy bấm BẬT IP HÀN trước")
            return
        webbrowser.open(SITE_URL)
        self.log("Đã mở " + SITE_URL)

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
