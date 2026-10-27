"""
main.py - Giao diện đồ họa trò chơi Cờ Vua AI bằng Pygame.
Hỗ trợ:
- Người chơi vs AI (chơi quân Trắng, AI cầm quân Đen).
- Lựa chọn thuật toán: Minimax hoặc Alpha-Beta Pruning.
- Lựa chọn độ sâu tìm kiếm (Depth 1 - 4).
- Hiển thị nước đi hợp lệ, tô sáng ô chọn, ô vừa đi.
- Hỗ trợ phong cấp Tốt (Pawn Promotion).
- Hỗ trợ Hoàn tác (Undo) và Chơi lại ván mới (New Game).
- Tính toán AI trên luồng riêng (Threading) giúp giao diện luôn mượt mà.
- Hiển thị thống kê chi tiết: Điểm đánh giá, Số node đã duyệt, Số lần cắt tỉa, Thời gian suy nghĩ.
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

# Kích thước giao diện
KICH_THUOC_O = 80
BAN_CO_SIZE = KICH_THUOC_O * 8  # 640 x 640
SIDEBAR_WIDTH = 340
CHIEU_RONG = BAN_CO_SIZE + SIDEBAR_WIDTH
CHIEU_CAO = BAN_CO_SIZE

# Màu sắc giao diện (Tone Lichess / Chess.com hiện đại)
MAU_O_SANG = (240, 217, 181)       # Màu kem
MAU_O_TOI = (181, 136, 99)         # Màu nâu gỗ
MAU_CHON_O = (205, 210, 106, 180)   # Vàng xanh nhạt
MAU_NUOC_DI_CUOI = (205, 210, 106, 140)
MAU_GOI_Y = (100, 110, 64, 160)     # Chấm tròn gợi ý
MAU_BACKGROUND = (38, 36, 33)       # Màu nền thanh điều khiển
MAU_CARD = (49, 46, 42)             # Màu card thông tin
MAU_CHU_CHINH = (240, 240, 240)
MAU_CHU_PHU = (160, 160, 160)
MAU_NUT_BAM = (70, 68, 64)
MAU_NUT_HOVER = (90, 88, 84)
MAU_NUT_ACTIVE = (95, 145, 60)      # Xanh lá cây
MAU_CANH_BAO = (200, 70, 70)


class NutBam:
    """Nút bấm tương tác trên thanh công cụ."""

    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.font = font
        self.active = False

    def ve(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]):
        if self.active:
            color = MAU_NUT_ACTIVE
        elif self.rect.collidepoint(mouse_pos):
            color = MAU_NUT_HOVER
        else:
            color = MAU_NUT_BAM

        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, width=1, border_radius=6)

        txt_surf = self.font.render(self.text, True, MAU_CHU_CHINH)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def duoc_bam(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class GameCoVuong:
    """Quản lý trạng thái trò chơi và giao diện Pygame."""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Cờ Vua AI - Minimax & Alpha-Beta Pruning")

        self.screen = pygame.display.set_mode((CHIEU_RONG, CHIEU_CAO))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_lon = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_vua = pygame.font.SysFont("segoeui", 16, bold=True)
        self.font_nho = pygame.font.SysFont("segoeui", 14)

        # Quản lý bàn cờ
        self.ban_co = BanCo()
        self.o_dang_chon: Optional[chess.Square] = None
        self.cac_nuoc_di_hop_le_o_chon: List[chess.Move] = []
        self.nuoc_di_cuoi: Optional[chess.Move] = None

        # Cài đặt AI
        self.thuat_toan_ai = "Alpha-Beta"  # "Alpha-Beta" hoặc "Minimax"
        self.do_sau_ai = 3                 # Mặc định depth 3
        self.ai_dang_tinh = False
        self.thong_ke_ai = {
            "nuoc_di": "Chưa có",
            "thoi_gian_ms": 0.0,
            "so_node": 0,
            "so_cat_tia": 0,
            "diem_danh_gia": 0,
        }

        # Nạp hình ảnh quân cờ
        self.quan_co_images = {}
        self.tai_hinh_anh_quan_co()

        # Khởi tạo các nút bấm điều khiển
        self.khoi_tao_nut_bam()

    def tai_hinh_anh_quan_co(self):
        """Nạp ảnh quân cờ từ thư mục assets/pieces."""
        ten_cac_quan = ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP"]
        for ten in ten_cac_quan:
            path = os.path.join("assets", "pieces", f"{ten}.png")
            if os.path.exists(path):
                img = pygame.image.load(path)
                self.quan_co_images[ten] = pygame.transform.smoothscale(img, (KICH_THUOC_O, KICH_THUOC_O))

    def khoi_tao_nut_bam(self):
        """Tạo các nút tương tác trên thanh bên phải."""
        bx = BAN_CO_SIZE + 20
        bw = SIDEBAR_WIDTH - 40

        # Nút chọn thuật toán
        self.btn_alphabeta = NutBam(pygame.Rect(bx, 150, (bw - 10) // 2, 36), "Alpha-Beta", self.font_nho)
        self.btn_minimax = NutBam(pygame.Rect(bx + (bw - 10) // 2 + 10, 150, (bw - 10) // 2, 36), "Minimax", self.font_nho)

        # Nút tăng giảm độ sâu
        self.btn_giam_depth = NutBam(pygame.Rect(bx + 160, 200, 36, 32), "-", self.font_vua)
        self.btn_tang_depth = NutBam(pygame.Rect(bx + 240, 200, 36, 32), "+", self.font_vua)

        # Nút Chơi mới và Hoàn tác
        self.btn_choi_moi = NutBam(pygame.Rect(bx, 540, (bw - 10) // 2, 40), "Ván Mới", self.font_vua)
        self.btn_hoan_tac = NutBam(pygame.Rect(bx + (bw - 10) // 2 + 10, 540, (bw - 10) // 2, 40), "Hoàn Tác", self.font_vua)

    def toan_do_thanh_o_co(self, x: int, y: int) -> Optional[chess.Square]:
        """Chuyển tọa độ pixel chuột thành ô cờ chess.Square (0 đến 63)."""
        if 0 <= x < BAN_CO_SIZE and 0 <= y < BAN_CO_SIZE:
            col = x // KICH_THUOC_O
            row = y // KICH_THUOC_O
            # Hàng 0 trong Pygame là rank 8 (hàng trên cùng của bàn cờ)
            rank = 7 - row
            file = col
            return chess.square(file, rank)
        return None

    def o_co_thanh_toa_do(self, square: chess.Square) -> Tuple[int, int]:
        """Chuyển ô cờ chess.Square thành tọa độ pixel góc trên trái."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        x = file * KICH_THUOC_O
        y = (7 - rank) * KICH_THUOC_O
        return x, y

    def xu_ly_click_ban_co(self, square: chess.Square):
        """Xử lý khi người chơi bấm chuột vào một ô trên bàn cờ."""
        if self.ai_dang_tinh or self.ban_co.da_ket_thuc():
            return

        piece = self.ban_co.board.piece_at(square)

        # Nếu đã có ô được chọn trước đó
        if self.o_dang_chon is not None:
            # Kiểm tra xem ô click mới có phải là nước đi hợp lệ không
            nuoc_di_tiem_nang = None
            for move in self.cac_nuoc_di_hop_le_o_chon:
                if move.to_square == square:
                    nuoc_di_tiem_nang = move
                    break

            if nuoc_di_tiem_nang:
                # Xử lý phong cấp tốt tự động thành Hậu nếu tốt đến hàng cuối
                piece_chon = self.ban_co.board.piece_at(self.o_dang_chon)
                if piece_chon and piece_chon.piece_type == chess.PAWN:
                    rank_den = chess.square_rank(square)
                    if (piece_chon.color == chess.WHITE and rank_den == 7) or (piece_chon.color == chess.BLACK and rank_den == 0):
                        nuoc_di_tiem_nang = chess.Move(self.o_dang_chon, square, promotion=chess.QUEEN)

                # Thực hiện nước đi của người chơi
                self.ban_co.thuc_hien_nuoc_di(nuoc_di_tiem_nang)
                self.nuoc_di_cuoi = nuoc_di_tiem_nang
                self.o_dang_chon = None
                self.cac_nuoc_di_hop_le_o_chon = []

                # Kích hoạt AI suy nghĩ nếu ván chưa kết thúc
                if not self.ban_co.da_ket_thuc() and self.ban_co.luot_di == chess.BLACK:
                    self.kich_hoat_ai()
                return
            else:
                # Nếu click vào quân cờ khác của mình -> đổi ô chọn
                if piece and piece.color == chess.WHITE:
                    self.o_dang_chon = square
                    self.cac_nuoc_di_hop_le_o_chon = [
                        m for m in self.ban_co.lay_cac_nuoc_di_hop_le() if m.from_square == square
                    ]
                    return
                else:
                    self.o_dang_chon = None
                    self.cac_nuoc_di_hop_le_o_chon = []
        else:
            # Chọn quân cờ của người chơi (Trắng)
            if piece and piece.color == chess.WHITE:
                self.o_dang_chon = square
                self.cac_nuoc_di_hop_le_o_chon = [
                    m for m in self.ban_co.lay_cac_nuoc_di_hop_le() if m.from_square == square
                ]

    def kich_hoat_ai(self):
        """Khởi chạy AI tính toán trên một Thread nền riêng biệt."""
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
        """Hoàn tác lại 2 nước (1 của AI và 1 của người chơi)."""
        if self.ai_dang_tinh:
            return
        # Lùi nước AI
        if self.ban_co.hoan_tac_nuoc_di():
            # Lùi nước người chơi
            self.ban_co.hoan_tac_nuoc_di()
        self.o_dang_chon = None
        self.cac_nuoc_di_hop_le_o_chon = []
        self.nuoc_di_cuoi = self.ban_co.board.peek() if len(self.ban_co.board.move_stack) > 0 else None

    def xu_ly_choi_moi(self):
        """Đặt lại ván cờ mới từ đầu."""
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
        """Vẽ 64 ô cờ và các hiệu ứng tô sáng."""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                color = MAU_O_SANG if (row + col) % 2 == 0 else MAU_O_TOI
                rect = pygame.Rect(col * KICH_THUOC_O, row * KICH_THUOC_O, KICH_THUOC_O, KICH_THUOC_O)
                pygame.draw.rect(self.screen, color, rect)

                # Tô sáng ô của nước đi cuối cùng
                if self.nuoc_di_cuoi and square in (self.nuoc_di_cuoi.from_square, self.nuoc_di_cuoi.to_square):
                    overlay = pygame.Surface((KICH_THUOC_O, KICH_THUOC_O), pygame.SRCALPHA)
                    overlay.fill(MAU_NUOC_DI_CUOI)
                    self.screen.blit(overlay, rect.topleft)

                # Tô sáng ô đang chọn
                if self.o_dang_chon == square:
                    overlay = pygame.Surface((KICH_THUOC_O, KICH_THUOC_O), pygame.SRCALPHA)
                    overlay.fill(MAU_CHON_O)
                    self.screen.blit(overlay, rect.topleft)

        # Vẽ gợi ý các nước đi hợp lệ
        for move in self.cac_nuoc_di_hop_le_o_chon:
            x, y = self.o_co_thanh_toa_do(move.to_square)
            target_piece = self.ban_co.board.piece_at(move.to_square)

            center = (x + KICH_THUOC_O // 2, y + KICH_THUOC_O // 2)
            if target_piece:
                # Nếu là ô ăn quân: vẽ vòng tròn rỗng bao quanh ô
                pygame.draw.circle(self.screen, (120, 130, 80), center, KICH_THUOC_O // 2 - 4, width=5)
            else:
                # Nếu là ô di chuyển thông thường: vẽ chấm tròn nhỏ ở giữa
                pygame.draw.circle(self.screen, (120, 130, 80), center, 12)

        # Vẽ quân cờ
        for square, piece in self.ban_co.board.piece_map().items():
            color_prefix = "w" if piece.color == chess.WHITE else "b"
            piece_type_map = {
                chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B",
                chess.ROOK: "R", chess.QUEEN: "Q", chess.KING: "K"
            }
            key = f"{color_prefix}{piece_type_map[piece.piece_type]}"
            img = self.quan_co_images.get(key)
            if img:
                x, y = self.o_co_thanh_toa_do(square)
                self.screen.blit(img, (x, y))

    def ve_sidebar(self, mouse_pos: Tuple[int, int]):
        """Vẽ thanh công cụ, bảng điều khiển và thông số benchmark."""
        sidebar_rect = pygame.Rect(BAN_CO_SIZE, 0, SIDEBAR_WIDTH, CHIEU_CAO)
        pygame.draw.rect(self.screen, MAU_BACKGROUND, sidebar_rect)

        # Tiêu đề
        title = self.font_lon.render("CỜ VUA AI", True, (255, 215, 0))
        self.screen.blit(title, (BAN_CO_SIZE + 20, 20))

        subtitle = self.font_nho.render("Minimax & Alpha-Beta Pruning", True, MAU_CHU_PHU)
        self.screen.blit(subtitle, (BAN_CO_SIZE + 20, 50))

        # Trạng thái ván cờ
        status_box = pygame.Rect(BAN_CO_SIZE + 20, 80, SIDEBAR_WIDTH - 40, 48)
        pygame.draw.rect(self.screen, MAU_CARD, status_box, border_radius=6)

        if self.ban_co.la_chieu_het():
            nguoi_thang = "ĐEN (AI) THẮNG" if self.ban_co.luot_di == chess.WHITE else "TRẮNG THẮNG"
            status_txt = self.font_vua.render(f"CHIẾU HẾT! {nguoi_thang}", True, MAU_CANH_BAO)
        elif self.ban_co.la_hoa_co():
            status_txt = self.font_vua.render("HÒA CỜ!", True, (230, 180, 50))
        elif self.ai_dang_tinh:
            status_txt = self.font_vua.render("AI ĐANG SUY NGHĨ...", True, (100, 200, 255))
        else:
            turn_str = "Lượt Trắng (Bạn)" if self.ban_co.luot_di == chess.WHITE else "Lượt Đen (AI)"
            status_txt = self.font_vua.render(turn_str, True, MAU_CHU_CHINH)

        self.screen.blit(status_txt, status_txt.get_rect(center=status_box.center))

        # Lựa chọn Thuật toán
        lbl_algo = self.font_nho.render("Thuật toán AI:", True, MAU_CHU_PHU)
        self.screen.blit(lbl_algo, (BAN_CO_SIZE + 20, 132))
        self.btn_alphabeta.active = (self.thuat_toan_ai == "Alpha-Beta")
        self.btn_minimax.active = (self.thuat_toan_ai == "Minimax")
        self.btn_alphabeta.ve(self.screen, mouse_pos)
        self.btn_minimax.ve(self.screen, mouse_pos)

        # Lựa chọn Độ sâu (Depth)
        lbl_depth = self.font_nho.render("Độ sâu tìm kiếm (Depth):", True, MAU_CHU_PHU)
        self.screen.blit(lbl_depth, (BAN_CO_SIZE + 20, 208))
        self.btn_giam_depth.ve(self.screen, mouse_pos)
        self.btn_tang_depth.ve(self.screen, mouse_pos)

        txt_depth_val = self.font_vua.render(str(self.do_sau_ai), True, (255, 215, 0))
        rect_depth_val = txt_depth_val.get_rect(center=(BAN_CO_SIZE + 218, 216))
        self.screen.blit(txt_depth_val, rect_depth_val)

        # Bảng thống kê hiệu năng AI
        stats_card = pygame.Rect(BAN_CO_SIZE + 20, 250, SIDEBAR_WIDTH - 40, 270)
        pygame.draw.rect(self.screen, MAU_CARD, stats_card, border_radius=8)
        pygame.draw.rect(self.screen, (70, 68, 64), stats_card, width=1, border_radius=8)

        lbl_stats_title = self.font_vua.render("THỐNG KÊ NƯỚC ĐI AI", True, (200, 200, 200))
        self.screen.blit(lbl_stats_title, (BAN_CO_SIZE + 35, 265))

        lines = [
            f"Nước AI vừa đi: {self.thong_ke_ai['nuoc_di']}",
            f"Thời gian tính: {self.thong_ke_ai['thoi_gian_ms']:.1f} ms",
            f"Số node duyệt: {self.thong_ke_ai['so_node']:,}",
            f"Số lần cắt tỉa: {self.thong_ke_ai['so_cat_tia']:,}",
            f"Điểm thế cờ: {self.thong_ke_ai['diem_danh_gia']}",
            f"Thuật toán: {self.thuat_toan_ai}",
            f"Độ sâu áp dụng: Depth {self.do_sau_ai}"
        ]

        y_offset = 300
        for line in lines:
            t = self.font_nho.render(line, True, MAU_CHU_CHINH)
            self.screen.blit(t, (BAN_CO_SIZE + 35, y_offset))
            y_offset += 28

        # Nút Chơi mới & Hoàn tác
        self.btn_choi_moi.ve(self.screen, mouse_pos)
        self.btn_hoan_tac.ve(self.screen, mouse_pos)

        # Bản quyền / Tác giả
        author_txt = self.font_nho.render("Đồ án Cờ Vua AI - Python & Pygame", True, (100, 100, 100))
        self.screen.blit(author_txt, (BAN_CO_SIZE + 40, 615))

    def chay(self):
        """Vòng lặp chính của trò chơi."""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    x, y = event.pos
                    # 1. Click trên bàn cờ
                    if x < BAN_CO_SIZE:
                        sq = self.toan_do_thanh_o_co(x, y)
                        if sq is not None:
                            self.xu_ly_click_ban_co(sq)

                    # 2. Click nút chọn thuật toán
                    elif self.btn_alphabeta.duoc_bam(event):
                        self.thuat_toan_ai = "Alpha-Beta"
                    elif self.btn_minimax.duoc_bam(event):
                        self.thuat_toan_ai = "Minimax"

                    # 3. Click nút tăng giảm độ sâu
                    elif self.btn_giam_depth.duoc_bam(event):
                        if self.do_sau_ai > 1:
                            self.do_sau_ai -= 1
                    elif self.btn_tang_depth.duoc_bam(event):
                        if self.do_sau_ai < 4:
                            self.do_sau_ai += 1

                    # 4. Click nút Ván mới / Hoàn tác
                    elif self.btn_choi_moi.duoc_bam(event):
                        self.xu_ly_choi_moi()
                    elif self.btn_hoan_tac.duoc_bam(event):
                        self.xu_ly_hoan_tac()

            # Vẽ màn hình
            self.ve_ban_co()
            self.ve_sidebar(mouse_pos)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = GameCoVuong()
    game.chay()
