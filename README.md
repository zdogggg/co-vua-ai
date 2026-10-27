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
   - Bàn cờ 8×8 màu sắc trang nhã, quân cờ sắc nét.
   - Tô sáng ô đang chọn, các nước đi hợp lệ và nước đi vừa thực hiện.
   - Hỗ trợ đầy đủ các luật đặc biệt: **Phong cấp tốt (Promotion)**, **Nhập thành (Castling)**, **Bắt tốt qua đường (En Passant)**.
   - Nút **Hoàn tác (Undo)** và **Ván Mới (New Game)**.
2. **AI không làm đơ giao diện**:
   - Sử dụng đa luồng (`threading.Thread`) để AI tính toán ở background, giao diện người dùng luôn mượt mà.
3. **Thống kê chi tiết theo thời gian thực**:
   - Hiển thị trực tiếp trên màn hình: Điểm thế cờ, Số node duyệt, Số lần cắt tỉa, Thời gian suy nghĩ (ms).
4. **Tối ưu hóa Alpha-Beta Pruning**:
   - Tích hợp kỹ thuật **Move Ordering** (ưu tiên duyệt nước bắt quân và nước chiếu trước).
   - Giúp giảm tới **96% số node** và **tăng tốc tới 27 lần** so với Minimax thuần ở cùng độ sâu.

---

## 4. Kết Quả Thực Nghiệm (Benchmark)

Bảng trích xuất từ `so_sanh.py` trên thế cờ trung cuộc (*Italian Game*):

| Độ sâu | Thuật toán | Điểm đánh giá | Số node đã duyệt | Số lần cắt tỉa | Thời gian (ms) | Hiệu quả tăng tốc |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Depth 1** | Minimax | +130 | 33 | 0 | 19.4 ms | 1.0x (gốc) |
| **Depth 1** | Alpha-Beta | +130 | 33 | 0 | 17.3 ms | 1.1x |
| **Depth 2** | Minimax | -60 | 1,183 | 0 | 445.7 ms | 1.0x (gốc) |
| **Depth 2** | Alpha-Beta | -60 | 210 | 28 | 74.4 ms | **6.0x** (giảm 82.2% node) |
| **Depth 3** | Minimax | +140 | 38,322 | 0 | 14,431.9 ms | 1.0x (gốc) |
| **Depth 3** | Alpha-Beta | +140 | 1,502 | 79 | 518.1 ms | **27.9x** (giảm 96.1% node) |

> **Nhận xét quan trọng để bảo vệ đồ án:**
> - Điểm số đánh giá của Minimax và Alpha-Beta **hoàn toàn giống nhau** ở mọi độ sâu, chứng minh thuật toán cắt tỉa được cài đặt hoàn toàn chính xác theo lý thuyết toán học (không bị cắt tỉa nhầm nhánh tối ưu).
> - Càng tăng độ sâu tìm kiếm, hiệu quả của cắt tỉa Alpha-Beta càng vượt trội theo hàm mũ.
