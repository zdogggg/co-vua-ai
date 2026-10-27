"""
main.py - Giao diện đồ họa trò chơi Cờ Vua AI bằng Pygame.
Thiết kế cao cấp, sắc nét chuẩn 1:1 với Windows DPI Awareness:
- Kích hoạt DPI Awareness giúp bàn cờ, quân cờ và chữ không bao giờ bị mờ hay vỡ nét trên màn hình 125%/150%.
- Quân cờ vector Lichess cburnett chuẩn HD, tỷ lệ 85% thoáng đãng, không đè lên viền ô cờ.
- Bố cục Sidebar căn chỉnh theo tọa độ chuẩn (midleft/midright), các hàng và nhãn thẳng tắp.
- Loại bỏ icon con rắn mặc định ở góc trên bên trái cửa sổ.
- Đầy đủ tính năng: Minimax, Alpha-Beta, luồng phụ chống treo UI, Undo, Ván mới.
"""

import os
import sys
import threading
import time
from typing import Optional, List, Tuple
import pygame
import chess

# Bật chế độ DPI Awareness trên Windows để sửa triệt để lỗi mờ/vỡ hình do Windows scaling
if sys.platform == "win32":
    try:
        import ctypes
        # SetProcessDpiAwareness(1) = PROCESS_SYSTEM_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

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
QUAN_CO_SIZE = 68               # Tỷ lệ 85% giúp quân cờ thoáng và không chạm viền
QUAN_CO_OFFSET = (KICH_THUOC_O - QUAN_CO_SIZE) // 2

SIDEBAR_WIDTH = 340
CHIEU_RONG = BAN_CO_SIZE + SIDEBAR_WIDTH
CHIEU_CAO = BAN_CO_SIZE

# Bảng màu bàn cờ (Lichess Wood Theme)
MAU_O_SANG = (240, 217, 181)       # Màu kem gỗ
MAU_O_TOI = (181, 136, 99)         # Màu nâu gỗ
MAU_CHON_O = (205, 210, 106, 190)   # Highlight vàng xanh
MAU_NUOC_DI_CUOI = (205, 210, 106, 130)

# Bảng màu Sidebar Dark Mode
MAU_NEN_SIDEBAR = (22, 21, 18)     # Nền tối Obsidian
MAU_THE_CARD = (32, 30, 27)        # Nền card
MAU_VIEN_CARD = (48, 45, 40)       # Viền card mỏng
MAU_CHU_CHINH = (240, 240, 240)    # Trắng sáng
MAU_CHU_PHU = (150, 145, 138)      # Xám nhẹ
MAU_VANG_DIEM = (245, 195, 65)     # Vàng gold
MAU_XANH_LA = (98, 158, 42)        # Xanh lá active
MAU_XANH_HOVER = (112, 175, 52)
MAU_NUT_XAM = (46, 44, 40)
MAU_NUT_XAM_HOVER = (60, 57, 52)
MAU_CANH_BAO = (220, 60, 60)       # Đỏ cảnh báo


class NutBam:
    """Nút bấm tương tác trên giao diện."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        bg_color=MAU_NUT_XAM,
        hover_color=MAU_NUT_XAM_HOVER,
        active_color=MAU_XANH_LA,
        text_color=MAU_CHU_CHINH,
        border_radius=7,
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
    """Điều khiển logic và giao diện bàn cờ."""

    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Loại bỏ hoàn toàn icon con rắn ở góc trên cửa sổ bằng surface trong suốt
        icon_trong_suot = pygame.Surface((32, 32), pygame.SRCALPHA)
        icon_trong_suot.fill((0, 0, 0, 0))
        pygame.display.set_icon(icon_trong_suot)

        pygame.display.set_caption("Cờ Vua AI - Minimax & Alpha-Beta Pruning")

        self.screen = pygame.display.set_mode((CHIEU_RONG, CHIEU_CAO))
        self.clock = pygame.time.Clock()

        # Hệ thống font Segoe UI đồng nhất
        self.font_tieu_de = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_muc = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_chu = pygame.font.SysFont("segoeui", 13)
        self.font_chu_dam = pygame.font.SysFont("segoeui", 13, bold=True)
        self.font_nho_dam = pygame.font.SysFont("segoeui", 11, bold=True)
        self.font_toado = pygame.font.SysFont("segoeui", 11, bold=True)

        # Trạng thái bàn cờ
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

        # Khởi tạo nút bấm
        self.khoi_tao_nut_bam()

    def tai_hinh_anh_quan_co(self):
        """Nạp ảnh quân cờ vector cburnett và scale sắc nét về QUAN_CO_SIZE."""
        ten_cac_quan = ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP"]
        for ten in ten_cac_quan:
            path = os.path.join("assets", "pieces", f"{ten}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.quan_co_images[ten] = pygame.transform.smoothscale(img, (QUAN_CO_SIZE, QUAN_CO_SIZE))

    def khoi_tao_nut_bam(self):
        """Khởi tạo các nút bấm thẳng hàng tuyệt đối."""
        bx = BAN_CO_SIZE + 16
        bw = SIDEBAR_WIDTH - 32

        # Nút chọn thuật toán (Card cài đặt y=134)
        btn_w = (bw - 24 - 8) // 2
        self.btn_alphabeta = NutBam(
            pygame.Rect(bx + 12, 168, btn_w, 34),
            "Alpha-Beta",
            self.font_chu_dam,
        )
        self.btn_minimax = NutBam(
            pygame.Rect(bx + 12 + btn_w + 8, 168, btn_w, 34),
            "Minimax",
            self.font_chu_dam,
        )

        # Nút tăng giảm độ sâu (Cùng hàng y=232)
        y_stepper = 218
        self.btn_giam_depth = NutBam(
            pygame.Rect(bx + bw - 12 - 92, y_stepper, 28, 28),
            "\u2212",  # Dấu trừ Unicode chuẩn tâm
            self.font_muc,
            border_radius=5,
        )
        self.btn_tang_depth = NutBam(
            pygame.Rect(bx + bw - 12 - 28, y_stepper, 28, 28),
            "+",
            self.font_muc,
            border_radius=5,
        )

        # Nút Ván mới & Hoàn tác ở cuối Sidebar
        btn_action_w = (bw - 8) // 2
        self.btn_choi_moi = NutBam(
            pygame.Rect(bx, 560, btn_action_w, 44),
            "Ván Mới",
            self.font_muc,
            bg_color=(52, 122, 38),
            hover_color=(64, 142, 46),
        )
        self.btn_hoan_tac = NutBam(
            pygame.Rect(bx + btn_action_w + 8, 560, btn_action_w, 44),
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
        """Khởi chạy AI trong luồng phụ để giao diện không bị giật."""
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
        """Vẽ 64 ô cờ, tọa độ chuẩn a-h / 1-8 và quân cờ sắc nét."""
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

                # Tô sáng ô vừa đi
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

                # Tọa độ số hàng (1-8) ở mép trái
                if col == 0:
                    text_color = MAU_O_TOI if la_o_sang else MAU_O_SANG
                    rank_str = str(8 - row)
                    lbl = self.font_toado.render(rank_str, True, text_color)
                    self.screen.blit(lbl, (rect.x + 3, rect.y + 2))

                # Tọa độ chữ cột (a-h) ở mép dưới
                if row == 7:
                    text_color = MAU_O_TOI if la_o_sang else MAU_O_SANG
                    file_str = files[col]
                    lbl = self.font_toado.render(file_str, True, text_color)
                    self.screen.blit(lbl, (rect.right - 10, rect.bottom - 15))

        # Hiển thị gợi ý các ô đi hợp lệ
        for move in self.cac_nuoc_di_hop_le_o_chon:
            x, y = self.o_co_thanh_toa_do(move.to_square)
            target_piece = self.ban_co.board.piece_at(move.to_square)
            center = (x + KICH_THUOC_O // 2, y + KICH_THUOC_O // 2)

            if target_piece:
                pygame.draw.circle(
                    self.screen, (105, 115, 65), center, KICH_THUOC_O // 2 - 5, width=4
                )
            else:
                pygame.draw.circle(self.screen, (105, 115, 65), center, 10)

        # Vẽ quân cờ ở giữa ô cờ (padding 6px)
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
                self.screen.blit(img, (x + QUAN_CO_OFFSET, y + QUAN_CO_OFFSET))

    def ve_sidebar(self, mouse_pos: Tuple[int, int]):
        """Vẽ Sidebar bằng hệ thống căn giữa (midleft/midright) tuyệt đối."""
        bx = BAN_CO_SIZE + 16
        bw = SIDEBAR_WIDTH - 32

        # 1. Nền Sidebar
        pygame.draw.rect(
            self.screen, MAU_NEN_SIDEBAR, pygame.Rect(BAN_CO_SIZE, 0, SIDEBAR_WIDTH, CHIEU_CAO)
        )

        # 2. Tiêu đề chính
        title = self.font_tieu_de.render("CỜ VUA AI", True, MAU_VANG_DIEM)
        self.screen.blit(title, (bx, 18))

        subtitle = self.font_chu.render("Minimax & Alpha-Beta Pruning", True, MAU_CHU_PHU)
        self.screen.blit(subtitle, (bx, 48))

        # 3. Card trạng thái lượt đi
        status_box = pygame.Rect(bx, 76, bw, 46)
        pygame.draw.rect(self.screen, MAU_THE_CARD, status_box, border_radius=8)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, status_box, width=1, border_radius=8)

        cy_status = status_box.centery
        dot_center = (bx + 20, cy_status)

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

        rect_st = status_txt.get_rect(midleft=(bx + 36, cy_status))
        self.screen.blit(status_txt, rect_st)

        # 4. Card cài đặt (Thuật toán & Độ sâu)
        card_setting = pygame.Rect(bx, 134, bw, 128)
        pygame.draw.rect(self.screen, MAU_THE_CARD, card_setting, border_radius=8)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, card_setting, width=1, border_radius=8)

        lbl_algo = self.font_nho_dam.render("THUẬT TOÁN TÌM KIẾM", True, MAU_CHU_PHU)
        self.screen.blit(lbl_algo, (bx + 12, 147))

        self.btn_alphabeta.active = (self.thuat_toan_ai == "Alpha-Beta")
        self.btn_minimax.active = (self.thuat_toan_ai == "Minimax")
        self.btn_alphabeta.ve(self.screen, mouse_pos)
        self.btn_minimax.ve(self.screen, mouse_pos)

        # Căn chỉnh hàng độ sâu cùng trục ngang cy = 232
        cy_depth = 232
        lbl_depth = self.font_chu.render("Độ sâu tìm kiếm (Depth):", True, MAU_CHU_CHINH)
        rect_lbl_depth = lbl_depth.get_rect(midleft=(bx + 12, cy_depth))
        self.screen.blit(lbl_depth, rect_lbl_depth)

        self.btn_giam_depth.ve(self.screen, mouse_pos)
        self.btn_tang_depth.ve(self.screen, mouse_pos)

        depth_cx = (self.btn_giam_depth.rect.right + self.btn_tang_depth.rect.left) // 2
        txt_depth = self.font_muc.render(str(self.do_sau_ai), True, MAU_VANG_DIEM)
        rect_txt_depth = txt_depth.get_rect(center=(depth_cx, cy_depth))
        self.screen.blit(txt_depth, rect_txt_depth)

        # 5. Card báo cáo thống kê AI
        card_stats = pygame.Rect(bx, 274, bw, 272)
        pygame.draw.rect(self.screen, MAU_THE_CARD, card_stats, border_radius=8)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, card_stats, width=1, border_radius=8)

        lbl_stats_head = self.font_nho_dam.render("THỐNG KÊ NƯỚC ĐI AI", True, MAU_CHU_PHU)
        self.screen.blit(lbl_stats_head, (bx + 14, 286))

        items = [
            ("Nước AI vừa chọn", str(self.thong_ke_ai["nuoc_di"])),
            ("Thời gian suy nghĩ", f"{self.thong_ke_ai['thoi_gian_ms']:.1f} ms"),
            ("Số node duyệt", f"{self.thong_ke_ai['so_node']:,}"),
            ("Số lần cắt tỉa", f"{self.thong_ke_ai['so_cat_tia']:,}"),
            ("Điểm thế cờ", str(self.thong_ke_ai["diem_danh_gia"])),
            ("Thuật toán đang chọn", self.thuat_toan_ai),
            ("Độ sâu áp dụng", f"Depth {self.do_sau_ai}"),
        ]

        # Tọa độ các hàng phân bố đều đặn
        y_center_row = 318
        for i, (label, val) in enumerate(items):
            t_lbl = self.font_chu.render(label, True, MAU_CHU_PHU)
            t_val = self.font_chu_dam.render(val, True, MAU_CHU_CHINH)

            rect_lbl = t_lbl.get_rect(midleft=(bx + 14, y_center_row))
            rect_val = t_val.get_rect(midright=(bx + bw - 14, y_center_row))

            self.screen.blit(t_lbl, rect_lbl)
            self.screen.blit(t_val, rect_val)

            # Kẻ dòng gạch mờ ngăn cách
            if i < len(items) - 1:
                pygame.draw.line(
                    self.screen,
                    (42, 40, 36),
                    (bx + 14, y_center_row + 15),
                    (bx + bw - 14, y_center_row + 15),
                )
            y_center_row += 31

        # 6. Các nút Ván mới & Hoàn tác
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
                    # Click trên bàn cờ
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
