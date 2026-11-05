# Dự Án Game Cờ Vua AI (Minimax & Alpha-Beta Pruning)

Dự án cờ vua AI phục vụ học tập và nghiên cứu môn Trí tuệ Nhân tạo (AI). Dự án tự cài đặt hai thuật toán tìm kiếm đối kháng kinh điển: **Minimax thuần** và **Alpha-Beta Pruning**, đi kèm hệ thống đánh giá thế cờ theo Piece-Square Tables (PST) và giao diện đồ họa trực quan bằng Pygame.

---

## 1. Cấu Trúc Dự Án

```text
co_vua_ai/
├── assets/
│   └── pieces/               # Hình ảnh 12 quân cờ chuẩn 2D
├── kiem_thu/
│   ├── test_danh_gia.py      # Kiểm thử hàm đánh giá thế cờ
│   ├── test_minimax.py       # Kiểm thử thuật toán Minimax
│   └── test_alpha_beta.py    # Kiểm thử cắt tỉa Alpha-Beta
├── luat_co.py                # Bọc các chức năng luật cờ từ python-chess
├── danh_gia.py               # Hàm đánh giá thế cờ (Material + Piece-Square Tables)
├── minimax.py                # Thuật toán Minimax duyệt toàn bộ cây
├── cat_tia_alpha_beta.py     # Minimax kết hợp cắt tỉa Alpha-Beta & Move Ordering
├── so_sanh.py                # Benchmark định lượng hiệu năng 2 thuật toán
├── main.py                   # Giao diện đồ họa Pygame hoàn chỉnh
├── requirements.txt          # Danh sách thư viện phụ thuộc
├── conftest.py               # Cấu hình đường dẫn cho pytest
├── PLAN.md                   # Kế hoạch chi tiết từng giai đoạn
└── README.md                 # Tài liệu hướng dẫn sử dụng
```

---

## 2. Hướng Dẫn Cài Đặt & Chạy

### Yêu cầu môi trường
- Python 3.10 trở lên.
- Hệ điều hành: Windows, macOS hoặc Linux.

### Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Chạy game với giao diện Pygame
```bash
python main.py
```

### Chạy benchmark so sánh 2 thuật toán
```bash
python so_sanh.py
```

### Chạy bộ kiểm thử tự động (Unit Test)
```bash
pytest -v
```

---

## 3. Các Tính Năng Nổi Bật

1. **Giao diện Pygame hiện đại**:
   - Bàn cờ 8×8 theo tông gỗ, quân cờ HD, **thanh lợi thế** dọc cạnh bàn cờ (giống Lichess).
   - Đi quân bằng **click** hoặc **kéo-thả**, có **hiệu ứng trượt quân**.
   - Tô sáng ô đang chọn, nước đi vừa thực hiện, **quầng đỏ khi Vua bị chiếu**; gợi ý nước hợp lệ dạng chấm (ô trống) / vòng tròn (ô ăn quân).
   - Hỗ trợ đầy đủ luật đặc biệt: **Phong cấp tốt (có bảng chọn Hậu/Mã/Xe/Tượng)**, **Nhập thành**, **Bắt tốt qua đường**, hòa do **lặp 3 lần / luật 50 nước / pat / thiếu quân**.
   - **Chọn màu quân** (cầm Đen thì bàn cờ tự lật và AI đi trước).
   - Bảng **lịch sử nước đi** (ký hiệu SAN), thông báo kết quả ván cờ kèm lý do.
   - Nút **Hoàn tác** và **Ván Mới** (dùng được cả khi AI đang suy nghĩ).
   - Phím tắt: `Ctrl+Z` / `Backspace` = Hoàn tác, `N` = Ván mới, `Esc` = Bỏ chọn.
2. **AI không làm đơ giao diện**:
   - AI tính toán trên **bản sao** bàn cờ ở luồng phụ (`threading.Thread`); chỉ luồng chính mới thay đổi bàn cờ nên không xảy ra xung đột dữ liệu giữa 2 luồng.
   - Thanh trạng thái hiển thị thời gian AI đang suy nghĩ theo thời gian thực.
3. **Thống kê chi tiết theo thời gian thực**:
   - Nước AI vừa chọn, thời gian suy nghĩ, số node duyệt, số lần cắt tỉa, điểm đánh giá, tốc độ (node/giây).
4. **Tối ưu hóa Alpha-Beta Pruning**:
   - **Move Ordering** theo **MVV-LVA** (ăn quân giá trị cao bằng quân giá trị thấp trước), phong cấp và nước chiếu.
   - Giảm tới **96% số node** và **tăng tốc khoảng 20 lần** so với Minimax thuần ở cùng độ sâu.
5. **Hàm đánh giá**: Giá trị quân + Piece-Square Tables, **bảng điểm Vua riêng cho tàn cuộc** (Vua tiến ra trung tâm để hỗ trợ chiếu hết).

---

## 4. Kết Quả Thực Nghiệm (Benchmark)

Bảng trích xuất từ `so_sanh.py` trên thế cờ trung cuộc (*Italian Game*):

| Độ sâu | Thuật toán | Điểm đánh giá | Số node đã duyệt | Số lần cắt tỉa | Thời gian (ms) | Hiệu quả tăng tốc |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Depth 1** | Minimax | +130 | 33 | 0 | 1.7 ms | 1.0x (gốc) |
| **Depth 1** | Alpha-Beta | +130 | 33 | 0 | 1.9 ms | 0.9x |
| **Depth 2** | Minimax | -60 | 1,183 | 0 | 55.1 ms | 1.0x (gốc) |
| **Depth 2** | Alpha-Beta | -60 | 210 | 28 | 18.3 ms | **3.0x** (giảm 82.2% node) |
| **Depth 3** | Minimax | +140 | 38,322 | 0 | 1,754.3 ms | 1.0x (gốc) |
| **Depth 3** | Alpha-Beta | +140 | 1,458 | 78 | 87.0 ms | **20.2x** (giảm 96.2% node) |

> **Nhận xét quan trọng để bảo vệ đồ án:**
> - Điểm số đánh giá của Minimax và Alpha-Beta **hoàn toàn giống nhau** ở mọi độ sâu, chứng minh thuật toán cắt tỉa được cài đặt hoàn toàn chính xác theo lý thuyết toán học (không bị cắt tỉa nhầm nhánh tối ưu).
> - Ở depth 1, Alpha-Beta không thể cắt tỉa (chỉ có 1 tầng) nên chậm hơn một chút do tốn chi phí sắp xếp nước đi.
> - Càng tăng độ sâu tìm kiếm, hiệu quả của cắt tỉa Alpha-Beta càng vượt trội theo hàm mũ.
