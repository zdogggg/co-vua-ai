"""
main.py - Giao diện đồ họa trò chơi Cờ Vua AI bằng Pygame.
Thiết kế hiện đại, tỉ mỉ theo phong cách Lichess / Chess.com:
- Quân cờ vector cburnett chính thức từ Lichess, hiển thị sắc nét chuẩn HD.
- Bàn cờ gỗ cao cấp có tọa độ a-h, 1-8 tinh tế.
- Bỏ icon con rắn mặc định ở thanh tiêu đề cửa sổ.
- Bảng điều khiển (Sidebar) cân đối, phân bố khoa học, không bị xộc xệch.
- Hỗ trợ đầy đủ: Minimax, Alpha-Beta Pruning, Đa luồng (không đơ UI), Phong cấp, Undo, New Game.
"""

import os
import sys
import threading
import time
from typing import Optional, List, Tuple
import pygame
import chess

from luat_co import BanCo
from minimax import tim_nuoc_di_minimax
from cat_tia_alpha_beta import tim_nuoc_di_alpha_beta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Kích thước chuẩn
KICH_THUOC_O = 80
BAN_CO_SIZE = KICH_THUOC_O * 8  # 640 x 640
SIDEBAR_WIDTH = 340
CHIEU_RONG = BAN_CO_SIZE + SIDEBAR_WIDTH
CHIEU_CAO = BAN_CO_SIZE

# Bảng màu cao cấp (Lichess Dark Theme)
MAU_O_SANG = (240, 217, 181)       # Kem gỗ sáng
MAU_O_TOI = (181, 136, 99)         # Nâu gỗ ấm
MAU_CHON_O = (205, 210, 106, 190)   # Highlight vàng xanh
MAU_NUOC_DI_CUOI = (205, 210, 106, 130)
MAU_GOI_Y = (100, 110, 64, 160)     # Chấm gợi ý di chuyển

# Màu giao diện Sidebar
MAU_NEN_SIDEBAR = (22, 21, 18)     # Nền thanh điều khiển
MAU_THE_CARD = (33, 31, 28)        # Nền card chức năng
MAU_VIEN_CARD = (48, 45, 41)       # Viền card
MAU_CHU_CHINH = (240, 240, 240)    # Chữ trắng sáng
MAU_CHU_PHU = (155, 150, 142)      # Chữ xám nhạt
MAU_VANG_DIEM = (245, 195, 65)     # Vàng kim
MAU_XANH_LA = (102, 168, 48)       # Xanh lá active
MAU_XANH_HOVER = (118, 185, 60)
MAU_NUT_XAM = (50, 48, 44)
MAU_NUT_XAM_HOVER = (68, 65, 60)
MAU_CANH_BAO = (220, 60, 60)       # Đỏ kết thúc / chiếu hết


class NutBam:
    """Nút bấm tương tác trên giao diện với hiệu ứng hover và active."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        bg_color=MAU_NUT_XAM,
        hover_color=MAU_NUT_XAM_HOVER,
        active_color=MAU_XANH_LA,
        text_color=MAU_CHU_CHINH,
        border_radius=8,
    ):
        self.rect = rect
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.active_color = active_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.active = False

    def ve(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]):
        if self.active:
            color = self.active_color
        elif self.rect.collidepoint(mouse_pos):
            color = self.hover_color
        else:
            color = self.bg_color

        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, MAU_VIEN_CARD, self.rect, width=1, border_radius=self.border_radius)

        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def duoc_bam(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class GameCoVuong:
    """Lớp điều khiển chính của trò chơi Cờ Vua AI."""

    def __init__(self):
        pygame.init()
        pygame.font.init()

        # 1. Bỏ icon con rắn mặc định ở thanh tiêu đề bằng surface trong suốt
        icon_trong_suot = pygame.Surface((32, 32), pygame.SRCALPHA)
        icon_trong_suot.fill((0, 0, 0, 0))
        pygame.display.set_icon(icon_trong_suot)

        pygame.display.set_caption("Cờ Vua AI - Minimax & Alpha-Beta Pruning")

        self.screen = pygame.display.set_mode((CHIEU_RONG, CHIEU_CAO))
        self.clock = pygame.time.Clock()

        # Hệ thống Font chữ gọn gàng, sắc nét
        self.font_tieu_de = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_muc = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_chu = pygame.font.SysFont("segoeui", 13)
        self.font_chu_dam = pygame.font.SysFont("segoeui", 13, bold=True)
        self.font_nho = pygame.font.SysFont("segoeui", 11, bold=True)
        self.font_toado = pygame.font.SysFont("segoeui", 12, bold=True)

        # Trạng thái ván cờ
        self.ban_co = BanCo()
        self.o_dang_chon: Optional[chess.Square] = None
        self.cac_nuoc_di_hop_le_o_chon: List[chess.Move] = []
        self.nuoc_di_cuoi: Optional[chess.Move] = None

        # Cài đặt AI
        self.thuat_toan_ai = "Alpha-Beta"
        self.do_sau_ai = 3
        self.ai_dang_tinh = False
        self.thong_ke_ai = {
            "nuoc_di": "Chưa có",
            "thoi_gian_ms": 0.0,
            "so_node": 0,
            "so_cat_tia": 0,
            "diem_danh_gia": 0,
        }

        # Nạp ảnh quân cờ
        self.quan_co_images = {}
        self.tai_hinh_anh_quan_co()

        # Khởi tạo các nút bấm
        self.khoi_tao_nut_bam()

    def tai_hinh_anh_quan_co(self):
        """Nạp ảnh quân cờ chính thức từ thư mục assets/pieces."""
        ten_cac_quan = ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP"]
        for ten in ten_cac_quan:
            path = os.path.join("assets", "pieces", f"{ten}.png")
            if os.path.exists(path):
                img = pygame.image.load(path)
                self.quan_co_images[ten] = pygame.transform.smoothscale(img, (KICH_THUOC_O, KICH_THUOC_O))

    def khoi_tao_nut_bam(self):
        """Bố cục các nút bấm thẳng hàng, chuẩn kích thước."""
        bx = BAN_CO_SIZE + 18
        bw = SIDEBAR_WIDTH - 36

        # Segmented Buttons: Thuật toán AI
        btn_w = (bw - 8) // 2
        self.btn_alphabeta = NutBam(
            pygame.Rect(bx, 172, btn_w, 34),
            "Alpha-Beta",
            self.font_chu_dam,
            active_color=MAU_XANH_LA,
        )
        self.btn_minimax = NutBam(
            pygame.Rect(bx + btn_w + 8, 172, btn_w, 34),
            "Minimax",
            self.font_chu_dam,
            active_color=MAU_XANH_LA,
        )

        # Nút tăng giảm độ sâu (Căn phải thẳng hàng)
        step_x = bx + bw - 110
        self.btn_giam_depth = NutBam(
            pygame.Rect(step_x, 218, 32, 28), "-", self.font_chu_dam, border_radius=6
        )
        self.btn_tang_depth = NutBam(
            pygame.Rect(step_x + 78, 218, 32, 28), "+", self.font_chu_dam, border_radius=6
        )

        # Nút Ván mới & Hoàn tác ở cuối Sidebar
        self.btn_choi_moi = NutBam(
            pygame.Rect(bx, 565, btn_w, 42),
            "Ván Mới",
            self.font_muc,
            bg_color=(56, 128, 40),
            hover_color=(68, 148, 48),
        )
        self.btn_hoan_tac = NutBam(
            pygame.Rect(bx + btn_w + 8, 565, btn_w, 42),
            "Hoàn Tác",
            self.font_muc,
            bg_color=MAU_NUT_XAM,
            hover_color=MAU_NUT_XAM_HOVER,
        )

    def toan_do_thanh_o_co(self, x: int, y: int) -> Optional[chess.Square]:
        if 0 <= x < BAN_CO_SIZE and 0 <= y < BAN_CO_SIZE:
            col = x // KICH_THUOC_O
            row = y // KICH_THUOC_O
            rank = 7 - row
            file = col
            return chess.square(file, rank)
        return None

    def o_co_thanh_toa_do(self, square: chess.Square) -> Tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        x = file * KICH_THUOC_O
        y = (7 - rank) * KICH_THUOC_O
        return x, y

    def xu_ly_click_ban_co(self, square: chess.Square):
        if self.ai_dang_tinh or self.ban_co.da_ket_thuc():
            return

        piece = self.ban_co.board.piece_at(square)

        if self.o_dang_chon is not None:
            nuoc_di_tiem_nang = None
            for move in self.cac_nuoc_di_hop_le_o_chon:
                if move.to_square == square:
                    nuoc_di_tiem_nang = move
                    break

            if nuoc_di_tiem_nang:
                # Tự động phong Hậu khi tốt tới hàng cuối
                piece_chon = self.ban_co.board.piece_at(self.o_dang_chon)
                if piece_chon and piece_chon.piece_type == chess.PAWN:
                    rank_den = chess.square_rank(square)
                    if (piece_chon.color == chess.WHITE and rank_den == 7) or (
                        piece_chon.color == chess.BLACK and rank_den == 0
                    ):
                        nuoc_di_tiem_nang = chess.Move(
                            self.o_dang_chon, square, promotion=chess.QUEEN
                        )

                self.ban_co.thuc_hien_nuoc_di(nuoc_di_tiem_nang)
                self.nuoc_di_cuoi = nuoc_di_tiem_nang
                self.o_dang_chon = None
                self.cac_nuoc_di_hop_le_o_chon = []

                if not self.ban_co.da_ket_thuc() and self.ban_co.luot_di == chess.BLACK:
                    self.kich_hoat_ai()
                return
            else:
                if piece and piece.color == chess.WHITE:
                    self.o_dang_chon = square
                    self.cac_nuoc_di_hop_le_o_chon = [
                        m
                        for m in self.ban_co.lay_cac_nuoc_di_hop_le()
                        if m.from_square == square
                    ]
                    return
                else:
                    self.o_dang_chon = None
                    self.cac_nuoc_di_hop_le_o_chon = []
        else:
            if piece and piece.color == chess.WHITE:
                self.o_dang_chon = square
                self.cac_nuoc_di_hop_le_o_chon = [
                    m
                    for m in self.ban_co.lay_cac_nuoc_di_hop_le()
                    if m.from_square == square
                ]

    def kich_hoat_ai(self):
        """Khởi chạy AI trong luồng phụ để giao diện không bị giật/đơ."""
        self.ai_dang_tinh = True

        def ai_worker():
            t0 = time.perf_counter()
            board_copy = self.ban_co.board.copy()

            if self.thuat_toan_ai == "Alpha-Beta":
                mv, score, nodes, cuts = tim_nuoc_di_alpha_beta(board_copy, self.do_sau_ai)
            else:
                mv, score, nodes = tim_nuoc_di_minimax(board_copy, self.do_sau_ai)
                cuts = 0

            t1 = time.perf_counter()
            thoi_gian_ms = (t1 - t0) * 1000

            if mv:
                self.ban_co.thuc_hien_nuoc_di(mv)
                self.nuoc_di_cuoi = mv
                self.thong_ke_ai = {
                    "nuoc_di": mv.uci(),
                    "thoi_gian_ms": thoi_gian_ms,
                    "so_node": nodes,
                    "so_cat_tia": cuts,
                    "diem_danh_gia": score,
                }
            self.ai_dang_tinh = False

        thread = threading.Thread(target=ai_worker, daemon=True)
        thread.start()

    def xu_ly_hoan_tac(self):
        if self.ai_dang_tinh:
            return
        if self.ban_co.hoan_tac_nuoc_di():
            self.ban_co.hoan_tac_nuoc_di()
        self.o_dang_chon = None
        self.cac_nuoc_di_hop_le_o_chon = []
        self.nuoc_di_cuoi = (
            self.ban_co.board.peek() if len(self.ban_co.board.move_stack) > 0 else None
        )

    def xu_ly_choi_moi(self):
        if self.ai_dang_tinh:
            return
        self.ban_co.dat_lai()
        self.o_dang_chon = None
        self.cac_nuoc_di_hop_le_o_chon = []
        self.nuoc_di_cuoi = None
        self.thong_ke_ai = {
            "nuoc_di": "Chưa có",
            "thoi_gian_ms": 0.0,
            "so_node": 0,
            "so_cat_tia": 0,
            "diem_danh_gia": 0,
        }

    def ve_ban_co(self):
        """Vẽ 64 ô cờ, tọa độ chuẩn a-h / 1-8 và các hiệu ứng trực quan."""
        files = ["a", "b", "c", "d", "e", "f", "g", "h"]

        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                la_o_sang = (row + col) % 2 == 0
                color = MAU_O_SANG if la_o_sang else MAU_O_TOI
                rect = pygame.Rect(
                    col * KICH_THUOC_O, row * KICH_THUOC_O, KICH_THUOC_O, KICH_THUOC_O
                )
                pygame.draw.rect(self.screen, color, rect)

                # Tô sáng ô nước đi cuối
                if self.nuoc_di_cuoi and square in (
                    self.nuoc_di_cuoi.from_square,
                    self.nuoc_di_cuoi.to_square,
                ):
                    overlay = pygame.Surface((KICH_THUOC_O, KICH_THUOC_O), pygame.SRCALPHA)
                    overlay.fill(MAU_NUOC_DI_CUOI)
                    self.screen.blit(overlay, rect.topleft)

                # Tô sáng ô đang chọn
                if self.o_dang_chon == square:
                    overlay = pygame.Surface((KICH_THUOC_O, KICH_THUOC_O), pygame.SRCALPHA)
                    overlay.fill(MAU_CHON_O)
                    self.screen.blit(overlay, rect.topleft)

                # Tọa độ số hàng (1-8) ở cột a (col == 0)
                if col == 0:
                    text_color = MAU_O_TOI if la_o_sang else MAU_O_SANG
                    rank_str = str(8 - row)
                    lbl = self.font_toado.render(rank_str, True, text_color)
                    self.screen.blit(lbl, (rect.x + 4, rect.y + 3))

                # Tọa độ chữ cột (a-h) ở hàng 1 (row == 7)
                if row == 7:
                    text_color = MAU_O_TOI if la_o_sang else MAU_O_SANG
                    file_str = files[col]
                    lbl = self.font_toado.render(file_str, True, text_color)
                    self.screen.blit(lbl, (rect.right - 12, rect.bottom - 16))

        # Hiển thị gợi ý các ô đi hợp lệ
        for move in self.cac_nuoc_di_hop_le_o_chon:
            x, y = self.o_co_thanh_toa_do(move.to_square)
            target_piece = self.ban_co.board.piece_at(move.to_square)
            center = (x + KICH_THUOC_O // 2, y + KICH_THUOC_O // 2)

            if target_piece:
                # Nước ăn quân: vòng tròn rỗng viền dày
                pygame.draw.circle(
                    self.screen, (105, 115, 65), center, KICH_THUOC_O // 2 - 4, width=5
                )
            else:
                # Nước đi trống: chấm tròn nhỏ
                pygame.draw.circle(self.screen, (105, 115, 65), center, 11)

        # Vẽ quân cờ (cburnett)
        for square, piece in self.ban_co.board.piece_map().items():
            color_prefix = "w" if piece.color == chess.WHITE else "b"
            piece_type_map = {
                chess.PAWN: "P",
                chess.KNIGHT: "N",
                chess.BISHOP: "B",
                chess.ROOK: "R",
                chess.QUEEN: "Q",
                chess.KING: "K",
            }
            key = f"{color_prefix}{piece_type_map[piece.piece_type]}"
            img = self.quan_co_images.get(key)
            if img:
                x, y = self.o_co_thanh_toa_do(square)
                self.screen.blit(img, (x, y))

    def ve_sidebar(self, mouse_pos: Tuple[int, int]):
        """Vẽ toàn bộ bảng điều khiển bên phải một cách chỉn chu, ngăn nắp."""
        bx = BAN_CO_SIZE + 18
        bw = SIDEBAR_WIDTH - 36

        # Nền chính Sidebar
        sidebar_bg = pygame.Rect(BAN_CO_SIZE, 0, SIDEBAR_WIDTH, CHIEU_CAO)
        pygame.draw.rect(self.screen, MAU_NEN_SIDEBAR, sidebar_bg)

        # 1. TIÊU ĐỀ
        title = self.font_tieu_de.render("CỜ VUA AI", True, MAU_VANG_DIEM)
        self.screen.blit(title, (bx, 18))

        subtitle = self.font_chu.render("Minimax & Alpha-Beta Pruning", True, MAU_CHU_PHU)
        self.screen.blit(subtitle, (bx, 48))

        # 2. KHUNG TRẠNG THÁI VÁN CỜ
        status_box = pygame.Rect(bx, 75, bw, 46)
        pygame.draw.rect(self.screen, MAU_THE_CARD, status_box, border_radius=8)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, status_box, width=1, border_radius=8)

        # Điểm chấm tròn báo lượt
        dot_center = (bx + 20, status_box.centery)
        if self.ban_co.la_chieu_het():
            nguoi_thang = "AI (Đen) Thắng" if self.ban_co.luot_di == chess.WHITE else "Bạn (Trắng) Thắng"
            status_txt = self.font_muc.render(f"Chiếu hết! {nguoi_thang}", True, MAU_CANH_BAO)
            pygame.draw.circle(self.screen, MAU_CANH_BAO, dot_center, 6)
        elif self.ban_co.la_hoa_co():
            status_txt = self.font_muc.render("Hòa cờ!", True, MAU_VANG_DIEM)
            pygame.draw.circle(self.screen, MAU_VANG_DIEM, dot_center, 6)
        elif self.ai_dang_tinh:
            status_txt = self.font_muc.render("AI đang tính toán...", True, (80, 185, 255))
            pygame.draw.circle(self.screen, (80, 185, 255), dot_center, 6)
        else:
            if self.ban_co.luot_di == chess.WHITE:
                status_txt = self.font_muc.render("Lượt của bạn (Quân Trắng)", True, MAU_CHU_CHINH)
                pygame.draw.circle(self.screen, (240, 240, 240), dot_center, 6)
            else:
                status_txt = self.font_muc.render("Lượt của AI (Quân Đen)", True, (200, 190, 180))
                pygame.draw.circle(self.screen, (100, 100, 100), dot_center, 6)

        self.screen.blit(status_txt, (bx + 35, status_box.centery - status_txt.get_height() // 2))

        # 3. CARD CÀI ĐẶT
        card_setting = pygame.Rect(bx, 134, bw, 126)
        pygame.draw.rect(self.screen, MAU_THE_CARD, card_setting, border_radius=8)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, card_setting, width=1, border_radius=8)

        lbl_algo = self.font_nho.render("THUẬT TOÁN TÌM KIẾM", True, MAU_CHU_PHU)
        self.screen.blit(lbl_algo, (bx + 12, 148))

        # Cập nhật trạng thái nút thuật toán
        self.btn_alphabeta.active = (self.thuat_toan_ai == "Alpha-Beta")
        self.btn_minimax.active = (self.thuat_toan_ai == "Minimax")
        self.btn_alphabeta.ve(self.screen, mouse_pos)
        self.btn_minimax.ve(self.screen, mouse_pos)

        # Hàng chọn độ sâu (Depth)
        lbl_depth = self.font_chu.render("Độ sâu tìm kiếm (Depth):", True, MAU_CHU_CHINH)
        self.screen.blit(lbl_depth, (bx + 12, 223))

        self.btn_giam_depth.ve(self.screen, mouse_pos)
        self.btn_tang_depth.ve(self.screen, mouse_pos)

        # Hiển thị số depth ở giữa hai nút
        depth_str = str(self.do_sau_ai)
        txt_depth = self.font_muc.render(depth_str, True, MAU_VANG_DIEM)
        depth_center_x = (self.btn_giam_depth.rect.right + self.btn_tang_depth.rect.left) // 2
        self.screen.blit(txt_depth, txt_depth.get_rect(center=(depth_center_x, self.btn_giam_depth.rect.centery)))

        # 4. CARD BÁO CÁO THỐNG KÊ AI
        card_stats = pygame.Rect(bx, 272, bw, 275)
        pygame.draw.rect(self.screen, MAU_THE_CARD, card_stats, border_radius=8)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, card_stats, width=1, border_radius=8)

        lbl_stats_head = self.font_nho.render("THỐNG KÊ NƯỚC ĐI AI", True, MAU_CHU_PHU)
        self.screen.blit(lbl_stats_head, (bx + 14, 286))

        # Bảng chỉ số dạng Label - Value cân xứng
        items = [
            ("Nước AI vừa chọn", str(self.thong_ke_ai["nuoc_di"])),
            ("Thời gian suy nghĩ", f"{self.thong_ke_ai['thoi_gian_ms']:.1f} ms"),
            ("Số node duyệt", f"{self.thong_ke_ai['so_node']:,}"),
            ("Số lần cắt tỉa", f"{self.thong_ke_ai['so_cat_tia']:,}"),
            ("Điểm thế cờ", str(self.thong_ke_ai["diem_danh_gia"])),
            ("Thuật toán đang chọn", self.thuat_toan_ai),
            ("Độ sâu áp dụng", f"Depth {self.do_sau_ai}"),
        ]

        y_item = 316
        for label, val in items:
            t_lbl = self.font_chu.render(label, True, MAU_CHU_PHU)
            t_val = self.font_chu_dam.render(val, True, MAU_CHU_CHINH)

            self.screen.blit(t_lbl, (bx + 14, y_item))
            self.screen.blit(t_val, (bx + bw - 14 - t_val.get_width(), y_item))

            # Đường gạch mờ ngăn cách giữa các dòng
            pygame.draw.line(
                self.screen,
                (42, 40, 36),
                (bx + 14, y_item + 22),
                (bx + bw - 14, y_item + 22),
            )
            y_item += 32

        # 5. CÁC NÚT ĐIỀU KHIỂN DƯỚI CÙNG
        self.btn_choi_moi.ve(self.screen, mouse_pos)
        self.btn_hoan_tac.ve(self.screen, mouse_pos)

    def chay(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    x, y = event.pos
                    # Click bàn cờ
                    if x < BAN_CO_SIZE:
                        sq = self.toan_do_thanh_o_co(x, y)
                        if sq is not None:
                            self.xu_ly_click_ban_co(sq)

                    # Chọn thuật toán
                    elif self.btn_alphabeta.duoc_bam(event):
                        self.thuat_toan_ai = "Alpha-Beta"
                    elif self.btn_minimax.duoc_bam(event):
                        self.thuat_toan_ai = "Minimax"

                    # Tăng/giảm độ sâu
                    elif self.btn_giam_depth.duoc_bam(event):
                        if self.do_sau_ai > 1:
                            self.do_sau_ai -= 1
                    elif self.btn_tang_depth.duoc_bam(event):
                        if self.do_sau_ai < 4:
                            self.do_sau_ai += 1

                    # Ván mới / Hoàn tác
                    elif self.btn_choi_moi.duoc_bam(event):
                        self.xu_ly_choi_moi()
                    elif self.btn_hoan_tac.duoc_bam(event):
                        self.xu_ly_hoan_tac()

            # Render
            self.ve_ban_co()
            self.ve_sidebar(mouse_pos)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = GameCoVuong()
    game.chay()
