# KR VPN

Ứng dụng Windows (giao diện tkinter) bật IP Hàn Quốc chỉ với **1 cú bấm**.
Dùng core **mihomo** (Clash.Meta) chạy ngầm, tự thử node Hàn nào sống rồi kết nối,
tự đổi node khi node chết, hiện IP/ISP trực tiếp trên giao diện.

Tác giả: **Le Nguyen Tat Thang**

---

## Tính năng

- **BẬT IP HÀN** — tự khởi động core, test độ trễ các node Hàn, chọn node sống nhất rồi bật IP Hàn
- **TẮT** — chuyển về IP thường (DIRECT) và trả proxy hệ thống về như cũ, core vẫn chạy sẵn để bật lại nhanh
- **Tự bật proxy hệ thống Windows** (`127.0.0.1:7890`) khi bật IP Hàn — Chrome/Edge/Cốc Cốc và app dùng proxy hệ thống sẽ ra IP Hàn ngay, không cần chỉnh tay
- **KIỂM TRA IP** — hiển thị IP / thành phố / quốc gia / ISP hiện tại (ipinfo.io, api.ip.sb, ip-api.com)
- **MỞ YES.SKBROADBAND** — mở thẳng `https://yes.skbroadband.com/` sau khi đã bật IP Hàn
- **Chọn node thủ công** — dropdown danh sách node Hàn + nút `Dùng`
- **Tự đổi node khi node chết** (mặc định bật) — kiểm tra mỗi 30 giây, mất IP Hàn là tự tìm node khác
- Nhật ký sự kiện ngay trên giao diện
- IP hiện **xanh** nếu là Hàn Quốc, **đỏ** nếu không

---

## Yêu cầu

| Thành phần | Ghi chú |
|---|---|
| Windows 10/11 (64-bit) | core mihomo trong repo là bản `windows-amd64` |
| Python 3.10+ | cài ở https://www.python.org/downloads/ — **tick chọn `Add python.exe to PATH`** (tkinter đã kèm sẵn) |
| Git (tuỳ chọn) | không có thì tải ZIP về cũng được |

Không cần cài thêm thư viện nào (`pip install` gì cũng không cần) — chỉ dùng thư viện chuẩn của Python.

---

## Cài đặt & Chạy

### Cách 1 — clone bằng git (khuyến nghị)

```bat
git clone https://github.com/LeNguyenTatThang/KR-VPN.git
cd KR-VPN
KR-VPN.bat
```

### Cách 2 — tải ZIP

1. Vào https://github.com/LeNguyenTatThang/KR-VPN → **Code → Download ZIP**
2. Giải nén ra bất kỳ thư mục nào (vd: `D:\KR-VPN`)
3. Bấm đúp `KR-VPN.bat`

Lần đầu Windows Firewall có thể hỏi — chọn **Allow access**.

### Cách 3 — chạy tay bằng lệnh

```bat
python kr_vpn.py
```

Kiểm tra nhanh core + node (chạy trong terminal, không mở GUI):

```bat
python kr_vpn.py --selftest
```

---

## Cách dùng

1. Bấm **▶ BẬT IP HÀN** — app tự thử node, kiểm tra IP Hàn và mở được `yes.skbroadband.com`, rồi **tự bật proxy hệ thống Windows**
2. Ô IP chuyển sang **xanh** + ghi `KR` là thành công
3. Bấm **🌐 MỞ YES.SKBROADBAND** để vào site (hoặc mở trình duyệt bình thường)
4. Muốn đổi node: chọn trong dropdown → bấm **Dùng**
5. Bật/tick ô **Tự đổi node khi node chết** nếu muốn giữ IP Hàn suốt
6. Bấm **■ TẮT (IP THƯỜNG)** để trở về IP thật và trả proxy hệ thống về như cũ

Sau khi bật, Chrome / Edge / Cốc Cốc và mọi app dùng proxy hệ thống đều ra IP Hàn. Firefox mặc định dùng proxy riêng — vào Settings → Network Settings → chọn **Use system proxy settings** (hoặc cài extension proxy trỏ `127.0.0.1:7890`).

---

## Tạo shortcut ra Desktop

### Cách 1 — dùng script có sẵn (nhanh)

Bấm đúp **`Tao Shortcut.bat`** → shortcut `KR VPN` tự hiện trên Desktop với icon, trỏ đúng thư mục app (di chuyển thư mục app vẫn chạy được).

### Cách 2 — tạo tay

1. Chuột phải `KR-VPN.bat` → **Send to → Desktop (create shortcut)**
2. Đổi tên shortcut thành `KR VPN`
3. Chuột phải shortcut → **Properties → Change Icon** → chọn `kr.ico`

> Không tạo shortcut trỏ thẳng vào `pythonw.exe` như trước —shortcut phải trỏ vào `KR-VPN.bat` để app chạy đúng thư mục chứa nó, copy sang máy khác vẫn chạy.

---

## Cấu trúc thư mục

```
KR-VPN/
├── kr_vpn.py                         # giao diện + điều khiển core (nguồn chính)
├── KR-VPN.bat                        # bấm đúp để chạy app
├── Tao Shortcut.bat                  # bấm đúp để tạo shortcut Desktop
├── tao-shortcut.ps1                  # script tạo shortcut (được bat gọi)
├── gen_icon.py                       # script tạo file icon kr.ico
├── kr.ico                            # icon ứng dụng
├── config.yaml                       # cấu hình mihomo + danh sách node
├── mihomo-windows-amd64-compatible.exe  # VPN core (Clash.Meta)
├── GeoSite.dat / geoip.metadb        # dữ liệu địa lý cho rule
├── cache.db                          # cache runtime (tự tạo)
└── *.log                             # log runtime (tự tạo)
```

---

## Cấu hình

Tất cả nằm trong `config.yaml`:

- **proxies** — danh sách node (hiện là node Hàn free từ sub public)
- **port: 7890** / **socks-port: 7891** — proxy HTTP/SOCKS local
- **external-controller: 127.0.0.1:9090** — API điều khiển (app dùng để bật/tắt/chọn node)
- **mode / rules** — chế độ rule mặc định của mihomo

### Đổi danh sách node (quan trọng)

Node free đổi rất nhanh. Khi node chết hàng loạt:

1. Tải subscription mới dạng Clash/Meta (vd: từ nguồn free bạn tin tưởng)
2. Ghi đè nội dung vào `config.yaml` (giữ nguyên phần `port`, `external-controller`, `dns` nếu không chắc)
3. Bật lại app — node mới sẽ tự hiển thị

> Lưu ý: repo chỉ chứa node free công khai từ sub public, **không** phải node riêng tư.
> Muốn ổn định hơn thì tự mua subscription và thay `config.yaml`.

---

## Sự cố thường gặp

| Triệu chứng | Cách xử lý |
|---|---|
| Bấm `KR-VPN.bat` không hiện gì | Cài lại Python và **tick `Add python.exe to PATH`**. Thử chạy `python kr_vpn.py` trong CMD để xem lỗi |
| `Không khởi động được VPN core` | Kiểm tra file `mihomo-windows-amd64-compatible.exe` còn nằm cùng thư mục với `kr_vpn.py` không; tắt antivirus đang chặn |
| `Hết node Hàn trong subscription` / `Không node Hàn nào chạy được` | Node free đã chết — thay `config.yaml` bằng subscription mới (xem mục Đổi danh sách node) |
| Đã chọn node nhưng IP chưa phải Hàn | Bấm **KIỂM TRA IP** lại; nếu vẫn sai, tick **Tự đổi node** rồi bấm **BẬT IP HÀN** |
| Check IP trên web vẫn ra Việt Nam | App đã tự bật proxy hệ thống; kiểm tra Windows **Settings → Network & Internet → Proxy** thấy `127.0.0.1:7890`. Mở tab mới hoặc khởi động lại trình duyệt. Firefox phải chọn **Use system proxy settings**. App nào tự bỏ qua proxy hệ thống thì phải cấu hình proxy thủ công |
| `yes.skbroadband.com` báo lỗi/không mở | Site chỉ cho IP Hàn. Bấm **KIỂM TRA IP** chắc chắn ra `KR`, rồi bấm **🌐 MỞ YES.SKBROADBAND**. Nếu vẫn lỗi, bấm **BẬT IP HÀN** để app đổi node khác |
| Firewall/antivirus chặn | Cho phép `mihomo-windows-amd64-compatible.exe` và `pythonw.exe` qua firewall |
| Port 7890 / 9090 bị chiếm | Đổi `port` và `external-controller` trong `config.yaml` |

---

## Gỡ bỏ

Xoá thư mục app là xong. Nếu core đang chạy, mở Task Manager kết thúc `mihomo-windows-amd64-compatible.exe`, hoặc bấm **TẮT** trong app rồi xoá.

---

## Pháp lý & lưu ý

- Node Hàn trong repo là node **free công khai** từ các subscription chia sẻ miễn phí — chất lượng không ổn định, không phù hợp công việc quan trọng
- Chỉ dùng vào mục đích hợp pháp. Người dùng tự chịu trách nhiệm về việc sử dụng
- Không thu thập, không gửi dữ liệu người dùng đi đâu — app chỉ gọi API local `127.0.0.1:9090` và vài trang tra IP công khai

---

## License

Free to use for personal purposes.
