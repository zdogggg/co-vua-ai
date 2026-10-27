# PLAN.md --- Dự án Game Cờ Vua AI bằng Python

> **Mục tiêu:** Tự xây dựng game cờ vua có giao diện đồ họa, dùng
> `python-chess` xử lý luật cờ và tự cài đặt hai thuật toán **Minimax**
> và **Alpha-Beta Pruning**.\
> **Nguyên tắc:** Tự code từng giai đoạn, kiểm thử và hiểu kết quả trước
> khi chuyển bước tiếp theo.

------------------------------------------------------------------------

## 1. Tổng quan dự án

### 1.1. Sản phẩm cuối cùng

Một game cờ vua chạy trên máy tính, cho phép: - Chơi cờ với AI. - Chọn
thuật toán: Minimax hoặc Alpha-Beta Pruning. - Chọn độ sâu tìm kiếm. -
Xem lượt đi và trạng thái ván cờ. - So sánh số node tìm kiếm, số lần cắt
tỉa và thời gian chạy của hai thuật toán.

### 1.2. Công nghệ

-   **Python 3.11+** --- ngôn ngữ chính.
-   **Pygame** --- giao diện đồ họa.
-   **python-chess** --- luật cờ, nước đi hợp lệ, kiểm tra chiếu
    hết/hòa.
-   **Minimax và Alpha-Beta Pruning** --- tự cài đặt, không dùng
    Stockfish làm AI chính.
-   **pytest** --- kiểm thử (khuyến nghị).

### 1.3. Phạm vi

**Bắt buộc** - Bàn cờ 8×8 và quân cờ. - Người chơi đi bằng chuột. - AI
chọn nước đi hợp lệ. - Cài đặt Minimax thuần. - Cài đặt Alpha-Beta
Pruning. - Hàm đánh giá thế cờ. - Bộ đếm node tìm kiếm. - Benchmark hai
thuật toán ở cùng vị trí và độ sâu.

**Có thể bổ sung sau** - Chọn màu quân. - Hoàn tác nước đi. - Tô sáng
nước đi gần nhất và các nước hợp lệ. - Lưu ván cờ dạng PGN. - Biểu đồ so
sánh hiệu năng.

------------------------------------------------------------------------

## 2. Cấu trúc thư mục dự kiến

Tên file dùng **tiếng Việt không dấu** để dễ đọc và gõ lệnh. Các tên
chuẩn như `main.py`, `requirements.txt`, `README.md`, `PLAN.md` được giữ
nguyên để dễ nhận diện.

``` text
co_vua_ai/
├── main.py                  # Chương trình chính và giao diện Pygame
├── luat_co.py               # Bọc các chức năng luật cờ từ python-chess
├── danh_gia.py              # Hàm đánh giá thế cờ
├── minimax.py               # Thuật toán Minimax thuần
├── cat_tia_alpha_beta.py    # Minimax có cắt tỉa Alpha-Beta
├── so_sanh.py               # Benchmark hai thuật toán
├── kiem_thu/
│   ├── test_danh_gia.py
│   ├── test_minimax.py
│   └── test_alpha_beta.py
├── requirements.txt
├── README.md
└── PLAN.md
```

### Trách nhiệm từng file

  -----------------------------------------------------------------------
  File                                Trách nhiệm
  ----------------------------------- -----------------------------------
  `main.py`                           Khởi tạo cửa sổ, nhận thao tác
                                      chuột, vẽ bàn cờ, gọi AI khi đến
                                      lượt

  `luat_co.py`                        Quản lý bàn cờ, lấy nước đi hợp lệ,
                                      thực hiện/hoàn tác nước đi, kiểm
                                      tra kết thúc

  `danh_gia.py`                       Chấm điểm thế cờ theo quân và một
                                      số yếu tố vị trí

  `minimax.py`                        Tìm nước đi bằng Minimax không cắt
                                      tỉa

  `cat_tia_alpha_beta.py`             Tìm nước đi bằng Minimax kết hợp
                                      cắt tỉa Alpha-Beta

  `so_sanh.py`                        Chạy hai thuật toán trong điều kiện
                                      giống nhau và ghi số liệu

  `kiem_thu/`                         Kiểm thử các phần quan trọng độc
                                      lập với giao diện
  -----------------------------------------------------------------------

**Lưu ý:** Khi đổi tên file, phải cập nhật tất cả câu lệnh `import`
tương ứng. Ví dụ, dùng `from danh_gia import ...` thay vì
`from evaluation import ...`.

------------------------------------------------------------------------

## 3. Lộ trình triển khai

## Giai đoạn 0 --- Chuẩn bị môi trường

### Việc cần làm

-   [x] Cài Python và kiểm tra `python --version`.
-   [x] Tạo thư mục `co_vua_ai`.
-   [x] Tạo môi trường ảo.
-   [x] Cài `pygame`, `python-chess`, `pytest`.
-   [x] Tạo `requirements.txt`.
-   [x] (Tùy chọn) Khởi tạo Git để lưu lịch sử thay đổi.

### Lệnh tham khảo --- Windows PowerShell

``` powershell
mkdir co_vua_ai
cd co_vua_ai
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install pygame python-chess pytest
pip freeze > requirements.txt
```

### Điều kiện hoàn thành

-   [x] Python chạy được trong môi trường ảo.
-   [x] Có thể import `pygame` và `chess` không báo lỗi.

------------------------------------------------------------------------

## Giai đoạn 1 --- Làm quen với `python-chess`

### Mục tiêu

Hiểu cách thư viện biểu diễn bàn cờ, sinh nước đi hợp lệ và cập nhật
trạng thái ván cờ.

### File

`luat_co.py`

### Việc cần làm

-   [x] Tạo một bàn cờ ở vị trí bắt đầu.
-   [x] In bàn cờ ra terminal.
-   [x] Lấy danh sách nước đi hợp lệ.
-   [x] Thực hiện một nước đi, ví dụ `e2e4`.
-   [x] In bàn cờ sau nước đi.
-   [x] Kiểm tra lượt đi tiếp theo.
-   [x] Thử kiểm tra chiếu hết hoặc hòa cờ.
-   [x] Tìm hiểu cách hoàn tác nước đi khi tìm kiếm.

### Câu hỏi cần trả lời

1.  `chess.Board()` tạo ra đối tượng gì?
2.  `board.legal_moves` có ý nghĩa gì?
3.  `board.push(move)` và `board.pop()` dùng để làm gì?
4.  Vì sao nên dùng thư viện xử lý luật thay vì tự viết lại mọi luật cờ
    vua?

### Điều kiện hoàn thành

-   [x] Chạy được script terminal thực hiện vài nước đi hợp lệ.
-   [x] Biết cách thực hiện và hoàn tác nước đi.

------------------------------------------------------------------------

## Giai đoạn 2 --- Xây dựng hàm đánh giá thế cờ

### Mục tiêu

Tạo một hàm số ước lượng bên nào đang có lợi thế tại một vị trí.

### File

`danh_gia.py`

### Ý tưởng ban đầu

Có thể bắt đầu bằng giá trị quân tương đối: - Tốt: 100 - Mã: 320 -
Tượng: 330 - Xe: 500 - Hậu: 900 - Vua: xử lý riêng, đặc biệt đối với
trạng thái kết thúc

Tính tổng điểm quân Trắng và Đen, sau đó lấy hiệu. Ví dụ, thống nhất quy
ước **điểm dương có lợi cho Trắng, điểm âm có lợi cho Đen**.

### Việc cần làm

-   [x] Viết hàm tính giá trị quân của mỗi bên.
-   [x] Viết hàm trả về điểm chênh lệch.
-   [x] Xử lý riêng chiếu hết và hòa.
-   [x] Kiểm thử vị trí ban đầu có điểm gần cân bằng.
-   [x] Kiểm thử khi một bên mất hậu thì điểm thay đổi rõ rệt.
-   [x] (Tùy chọn) Thêm điểm vị trí như kiểm soát trung tâm hoặc tiến
    tốt.

### Lưu ý quan trọng

Phải thống nhất góc nhìn của điểm số. Nếu điểm luôn tính từ phía Trắng,
MAX sẽ tối đa hóa khi đến lượt Trắng và MIN sẽ tối thiểu hóa khi đến
lượt Đen. Giữ quy ước đó nhất quán trong cả hai thuật toán.

### Điều kiện hoàn thành

-   [x] Hàm đánh giá không làm thay đổi bàn cờ.
-   [x] Kết quả kiểm thử hợp lý.
-   [x] Giải thích được vì sao hàm đánh giá chỉ là ước lượng.

------------------------------------------------------------------------

## Giai đoạn 3 --- Cài đặt Minimax thuần

### Mục tiêu

Duyệt cây trạng thái đến độ sâu giới hạn, chưa dùng cắt tỉa.

### File

`minimax.py`

### Khái niệm cần hiểu

-   **Node:** trạng thái bàn cờ.
-   **Depth/Ply:** độ sâu tìm kiếm; cần định nghĩa rõ đang đếm nửa nước
    đi hay nước đi hoàn chỉnh.
-   **MAX:** chọn điểm lớn nhất.
-   **MIN:** chọn điểm nhỏ nhất.
-   **Node lá:** trạng thái kết thúc hoặc đã đạt độ sâu giới hạn.

### Pseudocode tham khảo

``` text
MINIMAX(position, depth, maximizing):
    nếu vị trí kết thúc hoặc depth = 0:
        trả về EVALUATE(position)

    nếu maximizing:
        best = -vô_cùng
        với mỗi nước đi hợp lệ:
            thực hiện nước đi
            score = MINIMAX(position, depth - 1, false)
            hoàn tác nước đi
            best = max(best, score)
        trả về best
    ngược lại:
        best = +vô_cùng
        với mỗi nước đi hợp lệ:
            thực hiện nước đi
            score = MINIMAX(position, depth - 1, true)
            hoàn tác nước đi
            best = min(best, score)
        trả về best
```

Đây là pseudocode định hướng, không phải mã hoàn chỉnh. Khi tự triển
khai, cần xử lý vị trí không có nước đi hợp lệ và bảo đảm
`push()`/`pop()` cân bằng.

### Việc cần làm

-   [x] Viết hàm tìm điểm tốt nhất cho một vị trí.
-   [x] Viết hàm chọn nước đi tốt nhất tại gốc cây.
-   [x] Đếm số node đã thăm.
-   [x] Bảo đảm mọi nước đi trong quá trình tìm kiếm được hoàn tác chính
    xác.
-   [x] Kiểm tra AI chọn nước đi hợp lệ khi ván chưa kết thúc.
-   [x] Thử độ sâu 1, 2 rồi 3.

### Điều kiện hoàn thành

-   [x] Minimax chạy độc lập trong terminal.
-   [x] Bàn cờ gốc không bị thay đổi sau tìm kiếm.
-   [x] Giải thích được vai trò MAX và MIN.
-   [x] Có thống kê node tìm kiếm.

------------------------------------------------------------------------

## Giai đoạn 4 --- Cài đặt Alpha-Beta Pruning

### Mục tiêu

Bổ sung cắt tỉa vào Minimax để bỏ qua nhánh không thể thay đổi quyết
định cuối cùng.

### File

`cat_tia_alpha_beta.py`

### Hai biến quan trọng

-   `alpha`: điểm tốt nhất MAX đã bảo đảm được trên đường tìm kiếm hiện
    tại.
-   `beta`: điểm tốt nhất MIN đã bảo đảm được trên đường tìm kiếm hiện
    tại.

### Quy tắc cắt tỉa

Khi `alpha >= beta`, dừng xét các nhánh còn lại tại node hiện tại vì
chúng không thể cải thiện kết quả mà node cha cần.

### Việc cần làm

-   [x] Bổ sung tham số `alpha`, `beta` vào cấu trúc tìm kiếm.
-   [x] Cập nhật `alpha` tại node MAX.
-   [x] Cập nhật `beta` tại node MIN.
-   [x] Cắt nhánh khi `alpha >= beta`.
-   [x] Đếm số lần cắt tỉa.
-   [x] Đếm số node đã thăm.
-   [x] So sánh với Minimax ở cùng vị trí và độ sâu.

### Kiểm thử bắt buộc

-   [x] Minimax và Alpha-Beta phải cho cùng điểm tốt nhất khi cùng dùng
    vị trí, độ sâu, hàm đánh giá và quy ước điểm.
-   [x] Nước đi có thể khác nhau nếu có nhiều nước đồng điểm.
-   [x] Alpha-Beta thường giảm số node phải xét, nhưng mức giảm phụ
    thuộc thứ tự duyệt nước đi.
-   [x] Bàn cờ được khôi phục nguyên trạng sau tìm kiếm.

### Điều kiện hoàn thành

-   [x] Alpha-Beta cho kết quả đúng theo Minimax.
-   [x] Có thống kê node và số lần cắt tỉa.
-   [x] Giải thích được `alpha`, `beta` và điều kiện `alpha >= beta`.

------------------------------------------------------------------------

## Giai đoạn 5 --- So sánh hiệu năng

### Mục tiêu

Đo thực nghiệm để so sánh chi phí tìm kiếm của hai thuật toán.

### File

`so_sanh.py`

### Việc cần làm

-   [x] Chọn một số vị trí cố định.
-   [x] Chạy cả hai thuật toán ở cùng vị trí và độ sâu.
-   [x] Đo thời gian bằng `time.perf_counter()`.
-   [x] Ghi điểm, số node, thời gian và số lần cắt tỉa.
-   [x] Thử độ sâu 1, 2, 3; chỉ tăng độ sâu nếu thời gian cho phép.
-   [x] In kết quả thành bảng.
-   [x] Ghi rõ môi trường chạy và giới hạn thử nghiệm.

### Bảng kết quả gợi ý

  ----------------------------------------------------------------------------
  Vị trí       Độ sâu Thuật toán         Điểm    Số node  Thời gian Số lần cắt
                                                               (ms)        tỉa
  -------- ---------- ------------ ---------- ---------- ---------- ----------
  Khai              2 Minimax             ...        ...        ...          0
  cuộc                                                              

  Khai              2 Alpha-Beta          ...        ...        ...        ...
  cuộc                                                              
  ----------------------------------------------------------------------------

Không điền số liệu giả. Chạy chương trình rồi ghi kết quả thực tế.

### Điều kiện hoàn thành

-   [x] So sánh trong điều kiện công bằng.
-   [x] Có thể chạy lại thử nghiệm.
-   [x] Giải thích được vì sao thứ tự nước đi ảnh hưởng hiệu quả cắt
    tỉa.

------------------------------------------------------------------------

## Giai đoạn 6 --- Xây dựng giao diện Pygame

### Mục tiêu

Tạo giao diện chơi cờ sau khi các thành phần luật và AI chạy đúng trong
terminal.

### File

`main.py`

### Việc cần làm theo thứ tự

-   [x] Tạo cửa sổ Pygame.
-   [x] Vẽ bàn cờ 8×8.
-   [x] Vẽ quân cờ bằng Unicode hoặc hình ảnh.
-   [x] Chuyển tọa độ chuột thành ô cờ.
-   [x] Cho phép chọn quân của người chơi.
-   [x] Chỉ chấp nhận nước đi hợp lệ từ `python-chess`.
-   [x] Sau nước đi người chơi, gọi AI.
-   [x] Vẽ lại bàn cờ sau mỗi nước.
-   [x] Hiển thị lượt đi và trạng thái kết thúc.
-   [x] Cho phép chọn Minimax/Alpha-Beta và độ sâu.
-   [x] Hiển thị thống kê AI nếu còn thời gian.

### Lưu ý

Không gọi AI liên tục ở mọi khung hình. Chỉ tìm nước đi khi người chơi
vừa đi xong và đến lượt AI. Nếu giao diện bị đứng ở độ sâu lớn, hãy giảm
độ sâu trước; xử lý AI trong luồng riêng là phần nâng cao.

### Điều kiện hoàn thành

-   [x] Chơi được một ván người-vs-AI.
-   [x] AI không đi khi ván đã kết thúc.
-   [x] Người chơi không thể đi quân đối phương hoặc đi sai luật.
-   [x] Các luật đặc biệt và trạng thái kết thúc được xử lý đúng.

------------------------------------------------------------------------

## Giai đoạn 7 --- Hoàn thiện và chuẩn bị bảo vệ

### Kiểm thử chức năng

-   [x] Đi một nước hợp lệ và thử một nước không hợp lệ.
-   [x] Thử nhập thành, bắt tốt qua đường và phong cấp.
-   [x] Thử chiếu hết và hòa cờ.
-   [x] Thử chơi cả hai màu.
-   [x] Thử đổi thuật toán và độ sâu.
-   [x] Thử khởi động lại ván.

### Kiểm thử thuật toán

-   [x] So sánh điểm Minimax và Alpha-Beta ở các vị trí cố định.
-   [x] Kiểm tra bàn cờ trước/sau tìm kiếm không đổi.
-   [x] Kiểm tra vị trí đã kết thúc ngay tại node gốc.
-   [x] Kiểm tra trường hợp không có nước đi hợp lệ.
-   [x] Ghi lại số liệu benchmark thực tế.

### Tài liệu đồ án

-   [x] Sơ đồ kiến trúc file.
-   [x] Giải thích hàm đánh giá.
-   [x] Minh họa cây Minimax ở độ sâu nhỏ.
-   [x] Minh họa một nhánh bị Alpha-Beta cắt tỉa.
-   [x] Bảng kết quả benchmark.
-   [x] Nêu ưu điểm, hạn chế và hướng phát triển.

------------------------------------------------------------------------

## 4. Quy ước kỹ thuật

1.  **Góc nhìn điểm số:** chọn một quy ước duy nhất và ghi rõ trong
    `danh_gia.py`.
2.  **Độ sâu:** định nghĩa rõ depth 1 đếm bao nhiêu nửa nước đi.
3.  **Nước đi hợp lệ:** lấy từ `python-chess`.
4.  **Hoàn tác:** mỗi nước đi được đẩy trong quá trình tìm kiếm phải
    được hoàn tác chính xác.
5.  **Trạng thái kết thúc:** xử lý chiếu hết/hòa trước khi dùng điểm
    đánh giá thông thường.
6.  **Tính công bằng:** cùng vị trí, độ sâu, hàm đánh giá và điều kiện
    chạy khi so sánh.
7.  **Thống kê:** ghi rõ đang đếm node thăm, node lá được đánh giá hay
    số lần cắt tỉa.
8.  **Tách biệt giao diện:** thuật toán phải chạy độc lập với Pygame.
9.  **Tên module:** dùng tên file đã thống nhất; cập nhật các câu lệnh
    `import` khi đổi tên.

------------------------------------------------------------------------

## 5. Câu hỏi tự kiểm tra kiến thức

1.  Minimax mô hình hóa đối thủ như thế nào?
2.  Vì sao MAX chọn điểm lớn nhất còn MIN chọn điểm nhỏ nhất?
3.  Hàm đánh giá ảnh hưởng thế nào đến chất lượng nước đi?
4.  Vì sao tăng độ sâu thường khiến tìm kiếm tốn nhiều thời gian hơn?
5.  Alpha và beta đại diện cho điều gì?
6.  Vì sao điều kiện `alpha >= beta` cho phép cắt tỉa?
7.  Vì sao Alpha-Beta vẫn có thể cho kết quả Minimax?
8.  Vì sao thứ tự duyệt nước đi ảnh hưởng hiệu quả cắt tỉa?
9.  Vì sao phải hoàn tác nước đi sau mỗi nhánh?
10. Vì sao không thể kết luận thuật toán nào tốt hơn chỉ từ một lần
    benchmark?

------------------------------------------------------------------------

## 6. Thứ tự làm khuyến nghị

1.  Chuẩn bị môi trường.
2.  Làm quen với `python-chess` trong `luat_co.py`.
3.  Viết hàm đánh giá trong `danh_gia.py`.
4.  Cài Minimax trong `minimax.py`.
5.  Cài Alpha-Beta trong `cat_tia_alpha_beta.py`.
6.  Kiểm thử hai thuật toán.
7.  Benchmark bằng `so_sanh.py`.
8.  Xây dựng giao diện trong `main.py`.
9.  Hoàn thiện tài liệu và chuẩn bị thuyết trình.

**Nguyên tắc:** Chỉ chuyển giai đoạn khi đạt các điều kiện hoàn thành.
Khi gặp lỗi, thu nhỏ bài toán và kiểm tra từng thành phần độc lập thay
vì sửa nhiều file cùng lúc.
