"""
main.py - Giao diện đồ họa trò chơi Cờ Vua AI bằng Pygame.
Kích thước 1220x800: bàn cờ 800x800 + thanh lợi thế + sidebar điều khiển.
- Bật Windows DPI Awareness giúp hình ảnh sắc nét chuẩn 1:1, không bị mờ do tỉ lệ phóng to màn hình.
- Đi quân bằng click hoặc kéo-thả, có hiệu ứng trượt quân, chọn quân phong cấp.
- Chọn thuật toán (Minimax / Alpha-Beta), độ sâu, màu quân; xem thống kê và lịch sử nước đi.
- AI chạy trên luồng phụ với bản sao bàn cờ, luồng chính mới được phép thay đổi bàn cờ.
Phím tắt: Ctrl+Z / Backspace = Hoàn tác, N = Ván mới, Esc = Bỏ chọn.
"""

import math
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
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from luat_co import BanCo
from danh_gia import danh_gia_the_co, DIEM_CHIEU_HET
from minimax import tim_nuoc_di_minimax
from cat_tia_alpha_beta import tim_nuoc_di_alpha_beta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư mục chứa file main.py -> nạp ảnh đúng dù chạy game từ thư mục nào
THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))

# Kích thước chuẩn lớn, dễ nhìn
KICH_THUOC_O = 100
BAN_CO_SIZE = KICH_THUOC_O * 8  # 800 x 800
QUAN_CO_SIZE = 84               # Tỷ lệ 84% giúp quân cờ to rõ, thoáng đãng
QUAN_CO_OFFSET = (KICH_THUOC_O - QUAN_CO_SIZE) // 2

THANH_DANH_GIA_W = 16                        # Thanh lợi thế dọc cạnh bàn cờ
SIDEBAR_X = BAN_CO_SIZE + THANH_DANH_GIA_W   # 816
SIDEBAR_WIDTH = 404
CHIEU_RONG = SIDEBAR_X + SIDEBAR_WIDTH       # 1220 px
CHIEU_CAO = BAN_CO_SIZE                      # 800 px

DO_SAU_TOI_DA = {"Alpha-Beta": 5, "Minimax": 4}  # Minimax thuần depth 5 quá chậm
THOI_GIAN_HOAT_ANH = 0.18                        # Giây trượt quân

# Bảng màu bàn cờ (Lichess Wood Theme)
MAU_O_SANG = (240, 217, 181)       # Màu kem gỗ
MAU_O_TOI = (181, 136, 99)         # Màu nâu gỗ
MAU_CHON_O = (20, 85, 30, 110)      # Xanh lục mờ cho ô đang chọn
MAU_NUOC_DI_CUOI = (205, 210, 106, 140)
MAU_GOI_Y = (20, 85, 30, 90)        # Chấm gợi ý nước đi hợp lệ (trong suốt)
MAU_O_DICH_KEO = (255, 255, 255, 70)

# Bảng màu Sidebar Dark Mode
MAU_NEN_SIDEBAR = (22, 21, 18)     # Nền tối Obsidian
MAU_THE_CARD = (32, 30, 27)        # Nền card
MAU_O_THONG_KE = (40, 38, 34)      # Nền ô thống kê nhỏ
MAU_VIEN_CARD = (48, 45, 40)       # Viền card mỏng
MAU_CHU_CHINH = (240, 240, 240)    # Trắng sáng
MAU_CHU_PHU = (155, 150, 142)      # Xám nhẹ
MAU_CHU_MO = (95, 92, 86)          # Xám tối (nút bị khóa)
MAU_VANG_DIEM = (245, 195, 65)     # Vàng gold
MAU_XANH_LA = (98, 158, 42)        # Xanh lá active
MAU_XANH_HOVER = (112, 175, 52)
MAU_XANH_DUONG = (80, 185, 255)    # AI đang tính
MAU_NUT_XAM = (46, 44, 40)
MAU_NUT_XAM_HOVER = (60, 57, 52)
MAU_CANH_BAO = (220, 60, 60)       # Đỏ cảnh báo
MAU_CAM = (240, 140, 50)           # Cấu hình tìm kiếm chậm

TEN_QUAN = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
    chess.KING: "K",
}
CAC_QUAN_PHONG_CAP = [chess.QUEEN, chess.KNIGHT, chess.ROOK, chess.BISHOP]

LY_DO_KET_THUC = {
    chess.Termination.CHECKMATE: "Chiếu hết",
    chess.Termination.STALEMATE: "Hết nước đi hợp lệ (hòa pat)",
    chess.Termination.INSUFFICIENT_MATERIAL: "Không đủ lực lượng chiếu hết",
    chess.Termination.SEVENTYFIVE_MOVES: "Luật 75 nước",
    chess.Termination.FIVEFOLD_REPETITION: "Lặp lại thế cờ 5 lần",
    chess.Termination.FIFTY_MOVES: "Luật 50 nước",
    chess.Termination.THREEFOLD_REPETITION: "Lặp lại thế cờ 3 lần",
}


def ten_anh_quan(piece: chess.Piece) -> str:
    """Tên file ảnh của quân cờ, ví dụ: wK, bN."""
    return ("w" if piece.color == chess.WHITE else "b") + TEN_QUAN[piece.piece_type]


def dinh_dang_diem(diem: Optional[int]) -> str:
    """Định dạng điểm đánh giá (centipawn, góc nhìn Trắng) để hiển thị."""
    if diem is None:
        return "—"
    if diem >= DIEM_CHIEU_HET:
        return "Trắng thắng"
    if diem <= -DIEM_CHIEU_HET:
        return "Đen thắng"
    return f"{diem:+d}"


def dinh_dang_so_lon(so: float) -> str:
    """Rút gọn số lớn: 12345 -> 12.3k, 2500000 -> 2.5M."""
    if so >= 1_000_000:
        return f"{so / 1_000_000:.1f}M"
    if so >= 1_000:
        return f"{so / 1_000:.1f}k"
    return f"{so:.0f}"


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
        self.vo_hieu = False

    def dang_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        return not self.vo_hieu and self.rect.collidepoint(mouse_pos)

    def ve(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]):
        if self.active:
            color = self.active_color
        elif self.dang_hover(mouse_pos):
            color = self.hover_color
        else:
            color = self.bg_color

        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        if not self.active:
            pygame.draw.rect(surface, MAU_VIEN_CARD, self.rect, width=1, border_radius=self.border_radius)

        mau_chu = MAU_CHU_MO if self.vo_hieu else self.text_color
        txt_surf = self.font.render(self.text, True, mau_chu)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def duoc_bam(self, event: pygame.event.Event) -> bool:
        if self.vo_hieu:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class GameCoVuong:
    """Điều khiển logic và giao diện bàn cờ."""

    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Loại bỏ icon con rắn ở góc trên cửa sổ bằng surface trong suốt
        icon_trong_suot = pygame.Surface((32, 32), pygame.SRCALPHA)
        icon_trong_suot.fill((0, 0, 0, 0))
        pygame.display.set_icon(icon_trong_suot)

        pygame.display.set_caption("Cờ Vua AI - Minimax & Alpha-Beta Pruning")

        self.screen = pygame.display.set_mode((CHIEU_RONG, CHIEU_CAO))
        self.clock = pygame.time.Clock()

        # Hệ thống font Segoe UI cỡ lớn, rõ nét
        self.font_ket_thuc = pygame.font.SysFont("segoeui", 34, bold=True)
        self.font_tieu_de = pygame.font.SysFont("segoeui", 26, bold=True)
        self.font_muc = pygame.font.SysFont("segoeui", 17, bold=True)
        self.font_chu = pygame.font.SysFont("segoeui", 15)
        self.font_chu_dam = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_nho = pygame.font.SysFont("segoeui", 12)
        self.font_nho_dam = pygame.font.SysFont("segoeui", 13, bold=True)
        self.font_toado = pygame.font.SysFont("segoeui", 13, bold=True)

        # Trạng thái bàn cờ
        self.ban_co = BanCo()
        self.mau_nguoi_choi = chess.WHITE
        self.o_dang_chon: Optional[chess.Square] = None
        self.cac_nuoc_di_hop_le_o_chon: List[chess.Move] = []
        self.nuoc_di_cuoi: Optional[chess.Move] = None

        # Trạng thái tương tác chuột
        self.o_dang_keo: Optional[chess.Square] = None   # Ô của quân đang kéo
        self.vi_tri_keo: Tuple[int, int] = (0, 0)
        self.bo_chon_khi_tha = False                     # Click lần 2 vào ô đang chọn -> bỏ chọn
        self.cho_phong_cap: Optional[Tuple[chess.Square, chess.Square]] = None
        self.hoat_anh: Optional[dict] = None
        self.an_thong_bao_ket_thuc = False

        # Cài đặt AI
        self.thuat_toan_ai = "Alpha-Beta"
        self.do_sau_ai = 3
        self.ai_dang_tinh = False
        self.ai_bat_dau = 0.0
        self.phien_ai = 0                # Tăng lên để hủy kết quả của lượt tính cũ
        self.ket_qua_ai: Optional[tuple] = None
        self.khoa_ai = threading.Lock()
        self.thong_ke_ai = self.thong_ke_trong()

        # Thông tin tính sẵn mỗi khi bàn cờ thay đổi (tránh tính lại 60 lần/giây)
        self.ket_thuc: Optional[chess.Outcome] = None
        self.o_vua_bi_chieu: Optional[chess.Square] = None
        self.diem_hien_tai = 0
        self.lich_su_san: List[str] = []

        # Nạp ảnh quân cờ
        self.quan_co_images = {}
        self.tai_hinh_anh_quan_co()

        # Khởi tạo nút bấm
        self.khoi_tao_nut_bam()
        self.cap_nhat_trang_thai()

    @staticmethod
    def thong_ke_trong() -> dict:
        return {
            "nuoc_di": "—",
            "thoi_gian_ms": 0.0,
            "so_node": 0,
            "so_cat_tia": 0,
            "diem_danh_gia": None,
        }

    def tai_hinh_anh_quan_co(self):
        """Nạp ảnh quân cờ vector cburnett và scale sắc nét về QUAN_CO_SIZE (84x84)."""
        ten_cac_quan = ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP"]
        for ten in ten_cac_quan:
            path = os.path.join(THU_MUC_GOC, "assets", "pieces", f"{ten}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.quan_co_images[ten] = pygame.transform.smoothscale(img, (QUAN_CO_SIZE, QUAN_CO_SIZE))
            else:
                print(f"[CẢNH BÁO] Không tìm thấy ảnh quân cờ: {path}")

    def khoi_tao_nut_bam(self):
        """Khởi tạo các nút bấm kích thước lớn, thẳng hàng tuyệt đối."""
        bx = SIDEBAR_X + 20
        bw = SIDEBAR_WIDTH - 40

        # Nút chọn thuật toán (Card cài đặt)
        btn_w = (bw - 32 - 10) // 2
        self.btn_alphabeta = NutBam(pygame.Rect(bx + 16, 192, btn_w, 38), "Alpha-Beta", self.font_chu_dam)
        self.btn_minimax = NutBam(pygame.Rect(bx + 16 + btn_w + 10, 192, btn_w, 38), "Minimax", self.font_chu_dam)

        # Nút chọn màu quân (hàng cy = 256)
        self.btn_cam_trang = NutBam(
            pygame.Rect(bx + bw - 16 - 78 - 8 - 78, 240, 78, 32), "Trắng", self.font_chu_dam, border_radius=6
        )
        self.btn_cam_den = NutBam(
            pygame.Rect(bx + bw - 16 - 78, 240, 78, 32), "Đen", self.font_chu_dam, border_radius=6
        )

        # Nút tăng giảm độ sâu (hàng cy = 298)
        self.btn_giam_depth = NutBam(
            pygame.Rect(bx + bw - 16 - 110, 282, 32, 32),
            "−",  # Dấu trừ Unicode chuẩn tâm
            self.font_muc,
            border_radius=6,
        )
        self.btn_tang_depth = NutBam(
            pygame.Rect(bx + bw - 16 - 32, 282, 32, 32), "+", self.font_muc, border_radius=6
        )

        # Nút Ván mới & Hoàn tác ở cuối Sidebar
        btn_action_w = (bw - 12) // 2
        self.btn_choi_moi = NutBam(
            pygame.Rect(bx, 722, btn_action_w, 54),
            "Ván Mới",
            self.font_muc,
            bg_color=(52, 122, 38),
            hover_color=(64, 142, 46),
            border_radius=10,
        )
        self.btn_hoan_tac = NutBam(
            pygame.Rect(bx + btn_action_w + 12, 722, btn_action_w, 54),
            "Hoàn Tác",
            self.font_muc,
            border_radius=10,
        )
        self.tat_ca_nut = [
            self.btn_alphabeta, self.btn_minimax, self.btn_cam_trang, self.btn_cam_den,
            self.btn_giam_depth, self.btn_tang_depth, self.btn_choi_moi, self.btn_hoan_tac,
        ]

    # ------------------------------------------------------------------
    # Tọa độ (hỗ trợ lật bàn khi người chơi cầm quân Đen)
    # ------------------------------------------------------------------
    @property
    def lat_ban(self) -> bool:
        return self.mau_nguoi_choi == chess.BLACK

    def toa_do_thanh_o_co(self, x: int, y: int) -> Optional[chess.Square]:
        if 0 <= x < BAN_CO_SIZE and 0 <= y < BAN_CO_SIZE:
            col = x // KICH_THUOC_O
            row = y // KICH_THUOC_O
            if self.lat_ban:
                return chess.square(7 - col, row)
            return chess.square(col, 7 - row)
        return None

    def o_co_thanh_toa_do(self, square: chess.Square) -> Tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        if self.lat_ban:
            return (7 - file) * KICH_THUOC_O, rank * KICH_THUOC_O
        return file * KICH_THUOC_O, (7 - rank) * KICH_THUOC_O

    # ------------------------------------------------------------------
    # Trạng thái ván cờ
    # ------------------------------------------------------------------
    def la_luot_nguoi_choi(self) -> bool:
        return self.ban_co.luot_di == self.mau_nguoi_choi

    def cap_nhat_trang_thai(self):
        """Tính lại các thông tin phụ thuộc bàn cờ. Chỉ gọi khi bàn cờ thay đổi."""
        board = self.ban_co.board
        self.ket_thuc = self.ban_co.lay_ket_thuc()
        self.o_vua_bi_chieu = board.king(board.turn) if board.is_check() else None
        self.diem_hien_tai = danh_gia_the_co(board)
        self.an_thong_bao_ket_thuc = False

        # Lịch sử nước đi dạng SAN (e4, Nf3, O-O, ...) bằng cách đi lại từ thế cờ gốc
        ban_tam = board.root()
        self.lich_su_san = []
        for move in board.move_stack:
            self.lich_su_san.append(ban_tam.san(move))
            ban_tam.push(move)

    def bo_chon(self):
        self.o_dang_chon = None
        self.cac_nuoc_di_hop_le_o_chon = []
        self.o_dang_keo = None
        self.cho_phong_cap = None

    def chon_o(self, square: chess.Square):
        self.o_dang_chon = square
        self.cac_nuoc_di_hop_le_o_chon = [
            m for m in self.ban_co.lay_cac_nuoc_di_hop_le() if m.from_square == square
        ]

    def thuc_hien_nuoc(self, move: chess.Move, co_hoat_anh: bool = True):
        """Thực hiện nước đi (của người hoặc AI) và kích hoạt AI nếu đến lượt."""
        piece = self.ban_co.board.piece_at(move.from_square)
        if not self.ban_co.thuc_hien_nuoc_di(move):
            return

        if co_hoat_anh and piece:
            self.hoat_anh = {
                "o_den": move.to_square,
                "anh": ten_anh_quan(chess.Piece(move.promotion, piece.color) if move.promotion else piece),
                "tu": self.o_co_thanh_toa_do(move.from_square),
                "den": self.o_co_thanh_toa_do(move.to_square),
                "t0": time.perf_counter(),
            }
        else:
            self.hoat_anh = None

        self.nuoc_di_cuoi = move
        self.bo_chon()
        self.cap_nhat_trang_thai()

        if self.ket_thuc is None and not self.la_luot_nguoi_choi():
            self.kich_hoat_ai()

    def nguoi_choi_di(self, tu: chess.Square, den: chess.Square, co_hoat_anh: bool = True):
        """Người chơi đi từ ô `tu` tới ô `den`. Mở bảng chọn quân nếu là nước phong cấp."""
        cac_nuoc = [m for m in self.cac_nuoc_di_hop_le_o_chon if m.to_square == den]
        if not cac_nuoc:
            return
        if any(m.promotion for m in cac_nuoc):
            self.cho_phong_cap = (tu, den)
            self.o_dang_keo = None
            return
        self.thuc_hien_nuoc(cac_nuoc[0], co_hoat_anh)

    # ------------------------------------------------------------------
    # Xử lý chuột trên bàn cờ (click hoặc kéo-thả)
    # ------------------------------------------------------------------
    def co_the_tuong_tac(self) -> bool:
        return not self.ai_dang_tinh and self.ket_thuc is None and self.la_luot_nguoi_choi()

    def la_quan_cua_nguoi_choi(self, square: Optional[chess.Square]) -> bool:
        if square is None:
            return False
        piece = self.ban_co.board.piece_at(square)
        return piece is not None and piece.color == self.mau_nguoi_choi

    def xu_ly_nhan_ban_co(self, pos: Tuple[int, int]):
        # Bảng chọn quân phong cấp đang mở: chọn quân hoặc bấm ra ngoài để hủy
        if self.cho_phong_cap:
            loai_quan = self.quan_phong_cap_tai(pos)
            tu, den = self.cho_phong_cap
            self.cho_phong_cap = None
            if loai_quan:
                self.thuc_hien_nuoc(chess.Move(tu, den, promotion=loai_quan))
            return

        if self.ket_thuc is not None:
            self.an_thong_bao_ket_thuc = True
            return

        if not self.co_the_tuong_tac():
            return

        square = self.toa_do_thanh_o_co(*pos)
        if square is None:
            return

        if self.o_dang_chon is not None and any(
            m.to_square == square for m in self.cac_nuoc_di_hop_le_o_chon
        ):
            self.nguoi_choi_di(self.o_dang_chon, square)
        elif self.la_quan_cua_nguoi_choi(square):
            self.bo_chon_khi_tha = (square == self.o_dang_chon)
            self.chon_o(square)
            self.o_dang_keo = square
            self.vi_tri_keo = pos
        else:
            self.bo_chon()

    def xu_ly_tha_chuot(self, pos: Tuple[int, int]):
        if self.o_dang_keo is None:
            return
        o_goc = self.o_dang_keo
        self.o_dang_keo = None
        square = self.toa_do_thanh_o_co(*pos)

        if square is not None and square != o_goc:
            # Thả quân lên ô hợp lệ -> đi luôn, không cần hiệu ứng trượt
            self.nguoi_choi_di(o_goc, square, co_hoat_anh=False)
        elif square == o_goc and self.bo_chon_khi_tha:
            self.bo_chon()

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def kich_hoat_ai(self):
        """Khởi chạy AI trong luồng phụ để giao diện không bị treo.
        Luồng phụ chỉ tính trên BẢN SAO bàn cờ; luồng chính mới thực hiện nước đi."""
        self.ai_dang_tinh = True
        self.ai_bat_dau = time.perf_counter()
        phien = self.phien_ai
        board_copy = self.ban_co.board.copy()
        thuat_toan = self.thuat_toan_ai
        do_sau = self.do_sau_ai

        def ai_worker():
            t0 = time.perf_counter()
            if thuat_toan == "Alpha-Beta":
                mv, score, nodes, cuts = tim_nuoc_di_alpha_beta(board_copy, do_sau)
            else:
                mv, score, nodes = tim_nuoc_di_minimax(board_copy, do_sau)
                cuts = 0
            thoi_gian_ms = (time.perf_counter() - t0) * 1000
            with self.khoa_ai:
                self.ket_qua_ai = (phien, mv, score, nodes, cuts, thoi_gian_ms)

        threading.Thread(target=ai_worker, daemon=True).start()

    def huy_ai(self):
        """Bỏ qua kết quả của lượt AI đang tính (khi ván mới / hoàn tác)."""
        self.phien_ai += 1
        self.ai_dang_tinh = False
        with self.khoa_ai:
            self.ket_qua_ai = None

    def kiem_tra_ket_qua_ai(self):
        """Gọi mỗi khung hình ở luồng chính: áp dụng nước đi khi AI tính xong."""
        if self.hoat_anh is not None:
            return  # Chờ hiệu ứng nước đi của người chơi chạy xong
        with self.khoa_ai:
            ket_qua, self.ket_qua_ai = self.ket_qua_ai, None
        if ket_qua is None:
            return

        phien, mv, score, nodes, cuts, thoi_gian_ms = ket_qua
        if phien != self.phien_ai:
            return
        self.ai_dang_tinh = False
        if mv is None:
            return

        self.thong_ke_ai = {
            "nuoc_di": self.ban_co.board.san(mv),
            "thoi_gian_ms": thoi_gian_ms,
            "so_node": nodes,
            "so_cat_tia": cuts,
            "diem_danh_gia": score,
        }
        self.thuc_hien_nuoc(mv)

    # ------------------------------------------------------------------
    # Nút điều khiển
    # ------------------------------------------------------------------
    def xu_ly_hoan_tac(self):
        """Hoàn tác về lượt gần nhất của người chơi (bỏ cả nước của AI)."""
        self.huy_ai()
        self.bo_chon()
        self.hoat_anh = None
        stack = self.ban_co.board.move_stack
        so_nuoc = 2 if self.la_luot_nguoi_choi() else 1
        if len(stack) >= so_nuoc:
            for _ in range(so_nuoc):
                self.ban_co.hoan_tac_nuoc_di()
        self.nuoc_di_cuoi = stack[-1] if stack else None
        self.cap_nhat_trang_thai()

    def xu_ly_choi_moi(self):
        self.huy_ai()
        self.ban_co.dat_lai()
        self.bo_chon()
        self.hoat_anh = None
        self.nuoc_di_cuoi = None
        self.thong_ke_ai = self.thong_ke_trong()
        self.cap_nhat_trang_thai()
        # Người chơi cầm Đen -> AI (Trắng) đi trước
        if not self.la_luot_nguoi_choi():
            self.kich_hoat_ai()

    def doi_mau_quan(self, mau: bool):
        if mau != self.mau_nguoi_choi:
            self.mau_nguoi_choi = mau
            self.xu_ly_choi_moi()

    def doi_thuat_toan(self, ten: str):
        self.thuat_toan_ai = ten
        self.do_sau_ai = min(self.do_sau_ai, DO_SAU_TOI_DA[ten])

    def xu_ly_nut_bam(self, event: pygame.event.Event):
        if self.btn_alphabeta.duoc_bam(event):
            self.doi_thuat_toan("Alpha-Beta")
        elif self.btn_minimax.duoc_bam(event):
            self.doi_thuat_toan("Minimax")
        elif self.btn_cam_trang.duoc_bam(event):
            self.doi_mau_quan(chess.WHITE)
        elif self.btn_cam_den.duoc_bam(event):
            self.doi_mau_quan(chess.BLACK)
        elif self.btn_giam_depth.duoc_bam(event):
            self.do_sau_ai = max(1, self.do_sau_ai - 1)
        elif self.btn_tang_depth.duoc_bam(event):
            self.do_sau_ai = min(DO_SAU_TOI_DA[self.thuat_toan_ai], self.do_sau_ai + 1)
        elif self.btn_choi_moi.duoc_bam(event):
            self.xu_ly_choi_moi()
        elif self.btn_hoan_tac.duoc_bam(event):
            self.xu_ly_hoan_tac()

    # ------------------------------------------------------------------
    # Vẽ bàn cờ
    # ------------------------------------------------------------------
    def ve_o_trong_suot(self, square: chess.Square, mau: Tuple[int, int, int, int]):
        overlay = pygame.Surface((KICH_THUOC_O, KICH_THUOC_O), pygame.SRCALPHA)
        overlay.fill(mau)
        self.screen.blit(overlay, self.o_co_thanh_toa_do(square))

    def ve_ban_co(self, mouse_pos: Tuple[int, int]):
        """Vẽ 64 ô cờ, tọa độ a-h / 1-8, tô sáng, gợi ý nước đi và quân cờ."""
        for row in range(8):
            for col in range(8):
                la_o_sang = (row + col) % 2 == 0
                rect = pygame.Rect(col * KICH_THUOC_O, row * KICH_THUOC_O, KICH_THUOC_O, KICH_THUOC_O)
                pygame.draw.rect(self.screen, MAU_O_SANG if la_o_sang else MAU_O_TOI, rect)

                # Tọa độ ghi bằng màu của ô đối diện để luôn đọc được
                text_color = MAU_O_TOI if la_o_sang else MAU_O_SANG
                square = self.toa_do_thanh_o_co(rect.x, rect.y)
                if col == 0:
                    lbl = self.font_toado.render(str(chess.square_rank(square) + 1), True, text_color)
                    self.screen.blit(lbl, (rect.x + 4, rect.y + 3))
                if row == 7:
                    lbl = self.font_toado.render(chess.FILE_NAMES[chess.square_file(square)], True, text_color)
                    self.screen.blit(lbl, (rect.right - 14, rect.bottom - 18))

        # Tô sáng nước vừa đi
        if self.nuoc_di_cuoi:
            self.ve_o_trong_suot(self.nuoc_di_cuoi.from_square, MAU_NUOC_DI_CUOI)
            self.ve_o_trong_suot(self.nuoc_di_cuoi.to_square, MAU_NUOC_DI_CUOI)

        # Tô sáng ô đang chọn
        if self.o_dang_chon is not None:
            self.ve_o_trong_suot(self.o_dang_chon, MAU_CHON_O)

        # Vua đang bị chiếu: quầng đỏ tỏa tròn
        if self.o_vua_bi_chieu is not None:
            x, y = self.o_co_thanh_toa_do(self.o_vua_bi_chieu)
            quang = pygame.Surface((KICH_THUOC_O, KICH_THUOC_O), pygame.SRCALPHA)
            tam = KICH_THUOC_O // 2
            for r in range(tam, 0, -2):
                alpha = int(200 * (1 - r / tam) ** 0.6)
                pygame.draw.circle(quang, (230, 30, 30, alpha), (tam, tam), r)
            self.screen.blit(quang, (x, y))

        # Ô đích khi đang kéo quân
        if self.o_dang_keo is not None:
            o_hover = self.toa_do_thanh_o_co(*mouse_pos)
            if o_hover is not None and any(m.to_square == o_hover for m in self.cac_nuoc_di_hop_le_o_chon):
                self.ve_o_trong_suot(o_hover, MAU_O_DICH_KEO)

        # Gợi ý nước đi hợp lệ: chấm tròn (ô trống) hoặc vòng tròn (ô có quân bị ăn)
        goi_y = pygame.Surface((BAN_CO_SIZE, BAN_CO_SIZE), pygame.SRCALPHA)
        da_ve = set()
        for move in self.cac_nuoc_di_hop_le_o_chon:
            if move.to_square in da_ve:
                continue  # 4 nước phong cấp cùng ô đích
            da_ve.add(move.to_square)
            x, y = self.o_co_thanh_toa_do(move.to_square)
            center = (x + KICH_THUOC_O // 2, y + KICH_THUOC_O // 2)
            if self.ban_co.board.is_capture(move):
                pygame.draw.circle(goi_y, MAU_GOI_Y, center, KICH_THUOC_O // 2 - 2, width=8)
            else:
                pygame.draw.circle(goi_y, MAU_GOI_Y, center, 15)
        self.screen.blit(goi_y, (0, 0))

        self.ve_quan_co()

    def ve_quan_co(self):
        """Vẽ quân cờ, quân đang trượt (hiệu ứng) và quân đang được kéo."""
        anim_o_den = None
        if self.hoat_anh:
            tien_do = (time.perf_counter() - self.hoat_anh["t0"]) / THOI_GIAN_HOAT_ANH
            if tien_do >= 1:
                self.hoat_anh = None
            else:
                anim_o_den = self.hoat_anh["o_den"]

        for square, piece in self.ban_co.board.piece_map().items():
            if square == anim_o_den or square == self.o_dang_keo:
                continue
            img = self.quan_co_images.get(ten_anh_quan(piece))
            if img:
                x, y = self.o_co_thanh_toa_do(square)
                self.screen.blit(img, (x + QUAN_CO_OFFSET, y + QUAN_CO_OFFSET))

        if anim_o_den is not None:
            t = 1 - (1 - tien_do) ** 3  # ease-out cubic
            (x0, y0), (x1, y1) = self.hoat_anh["tu"], self.hoat_anh["den"]
            img = self.quan_co_images.get(self.hoat_anh["anh"])
            if img:
                self.screen.blit(
                    img, (x0 + (x1 - x0) * t + QUAN_CO_OFFSET, y0 + (y1 - y0) * t + QUAN_CO_OFFSET)
                )

        if self.o_dang_keo is not None:
            piece = self.ban_co.board.piece_at(self.o_dang_keo)
            img = self.quan_co_images.get(ten_anh_quan(piece)) if piece else None
            if img:
                self.screen.blit(img, img.get_rect(center=self.vi_tri_keo))

    def quan_phong_cap_tai(self, pos: Tuple[int, int]) -> Optional[chess.PieceType]:
        """Trả về loại quân được chọn trong bảng phong cấp tại vị trí chuột."""
        if not self.cho_phong_cap:
            return None
        x, _ = self.o_co_thanh_toa_do(self.cho_phong_cap[1])
        for i, loai_quan in enumerate(CAC_QUAN_PHONG_CAP):
            if pygame.Rect(x, i * KICH_THUOC_O, KICH_THUOC_O, KICH_THUOC_O).collidepoint(pos):
                return loai_quan
        return None

    def ve_bang_phong_cap(self, mouse_pos: Tuple[int, int]):
        """Bảng chọn quân phong cấp (Hậu, Mã, Xe, Tượng) mở dọc từ ô đích."""
        if not self.cho_phong_cap:
            return
        mo = pygame.Surface((BAN_CO_SIZE, BAN_CO_SIZE), pygame.SRCALPHA)
        mo.fill((0, 0, 0, 120))
        self.screen.blit(mo, (0, 0))

        x, _ = self.o_co_thanh_toa_do(self.cho_phong_cap[1])
        dang_chon = self.quan_phong_cap_tai(mouse_pos)
        for i, loai_quan in enumerate(CAC_QUAN_PHONG_CAP):
            center = (x + KICH_THUOC_O // 2, i * KICH_THUOC_O + KICH_THUOC_O // 2)
            mau_nen = (255, 255, 255) if loai_quan == dang_chon else (200, 200, 200)
            pygame.draw.circle(self.screen, mau_nen, center, KICH_THUOC_O // 2 - 4)
            img = self.quan_co_images.get(ten_anh_quan(chess.Piece(loai_quan, self.mau_nguoi_choi)))
            if img:
                self.screen.blit(img, img.get_rect(center=center))

    def ve_thong_bao_ket_thuc(self):
        """Lớp phủ thông báo kết quả ván cờ ở giữa bàn cờ."""
        if self.ket_thuc is None or self.an_thong_bao_ket_thuc or self.hoat_anh:
            return
        mo = pygame.Surface((BAN_CO_SIZE, BAN_CO_SIZE), pygame.SRCALPHA)
        mo.fill((0, 0, 0, 110))
        self.screen.blit(mo, (0, 0))

        if self.ket_thuc.winner is None:
            tieu_de, mau = "Hòa cờ", MAU_VANG_DIEM
        elif self.ket_thuc.winner == self.mau_nguoi_choi:
            tieu_de, mau = "Bạn thắng!", MAU_XANH_HOVER
        else:
            tieu_de, mau = "AI thắng!", MAU_CANH_BAO
        ly_do = LY_DO_KET_THUC.get(self.ket_thuc.termination, "Ván cờ kết thúc")

        the = pygame.Rect(0, 0, 420, 168)
        the.center = (BAN_CO_SIZE // 2, BAN_CO_SIZE // 2)
        pygame.draw.rect(self.screen, MAU_THE_CARD, the, border_radius=14)
        pygame.draw.rect(self.screen, mau, the, width=2, border_radius=14)

        dong = [
            (self.font_ket_thuc.render(tieu_de, True, mau), the.y + 46),
            (self.font_chu_dam.render(ly_do, True, MAU_CHU_CHINH), the.y + 92),
            (self.font_nho.render("Bấm “Ván Mới” để chơi lại  ·  Click bàn cờ để xem lại thế cờ",
                                  True, MAU_CHU_PHU), the.y + 132),
        ]
        for surf, cy in dong:
            self.screen.blit(surf, surf.get_rect(center=(the.centerx, cy)))

    def ve_thanh_danh_gia(self):
        """Thanh lợi thế dọc (giống Lichess): phần trắng lớn hơn khi Trắng có lợi."""
        rect = pygame.Rect(BAN_CO_SIZE, 0, THANH_DANH_GIA_W, CHIEU_CAO)
        if self.ket_thuc is not None and self.ket_thuc.winner is not None:
            ty_le_trang = 1.0 if self.ket_thuc.winner == chess.WHITE else 0.0
        elif self.ket_thuc is not None:
            ty_le_trang = 0.5
        else:
            ty_le_trang = 0.5 + 0.5 * math.tanh(self.diem_hien_tai / 700)

        cao_trang = int(CHIEU_CAO * ty_le_trang)
        pygame.draw.rect(self.screen, (60, 58, 54), rect)
        if self.lat_ban:
            phan_trang = pygame.Rect(rect.x, 0, rect.w, cao_trang)
        else:
            phan_trang = pygame.Rect(rect.x, CHIEU_CAO - cao_trang, rect.w, cao_trang)
        pygame.draw.rect(self.screen, (236, 236, 232), phan_trang)
        pygame.draw.line(self.screen, MAU_CAM, (rect.x, CHIEU_CAO // 2), (rect.right - 1, CHIEU_CAO // 2))

    # ------------------------------------------------------------------
    # Vẽ sidebar
    # ------------------------------------------------------------------
    def ve_card(self, rect: pygame.Rect, tieu_de: Optional[str] = None):
        pygame.draw.rect(self.screen, MAU_THE_CARD, rect, border_radius=10)
        pygame.draw.rect(self.screen, MAU_VIEN_CARD, rect, width=1, border_radius=10)
        if tieu_de:
            lbl = self.font_nho_dam.render(tieu_de, True, MAU_CHU_PHU)
            self.screen.blit(lbl, (rect.x + 16, rect.y + 13))

    def ve_trang_thai(self, rect: pygame.Rect):
        """Card trạng thái: lượt đi / AI đang tính / kết quả ván."""
        self.ve_card(rect)
        cy = rect.centery
        if self.ket_thuc is not None:
            if self.ket_thuc.winner is None:
                noi_dung, mau = "Hòa cờ!", MAU_VANG_DIEM
            elif self.ket_thuc.winner == self.mau_nguoi_choi:
                noi_dung, mau = "Chiếu hết! Bạn thắng", MAU_XANH_HOVER
            else:
                noi_dung, mau = "Chiếu hết! AI thắng", MAU_CANH_BAO
        elif self.ai_dang_tinh:
            giay = time.perf_counter() - self.ai_bat_dau
            so_cham = int(giay * 3) % 3 + 1
            noi_dung = f"AI đang suy nghĩ{'.' * so_cham:<3}  {giay:.1f}s"
            mau = MAU_XANH_DUONG
        elif self.la_luot_nguoi_choi():
            noi_dung = "Bạn đang bị chiếu!" if self.o_vua_bi_chieu is not None else "Lượt của bạn"
            mau = MAU_CANH_BAO if self.o_vua_bi_chieu is not None else MAU_CHU_CHINH
        else:
            noi_dung, mau = "Lượt của AI", (200, 190, 180)

        pygame.draw.circle(self.screen, mau, (rect.x + 26, cy), 7)
        txt = self.font_muc.render(noi_dung, True, mau)
        self.screen.blit(txt, txt.get_rect(midleft=(rect.x + 46, cy)))

        # Biểu tượng màu quân của người chơi ở góc phải
        ten_mau = "Trắng" if self.mau_nguoi_choi == chess.WHITE else "Đen"
        lbl = self.font_nho.render(f"Bạn: {ten_mau}", True, MAU_CHU_PHU)
        self.screen.blit(lbl, lbl.get_rect(midright=(rect.right - 16, cy)))

    def ve_cai_dat(self, rect: pygame.Rect, mouse_pos: Tuple[int, int]):
        self.ve_card(rect, "THUẬT TOÁN TÌM KIẾM")

        self.btn_alphabeta.active = (self.thuat_toan_ai == "Alpha-Beta")
        self.btn_minimax.active = (self.thuat_toan_ai == "Minimax")
        self.btn_cam_trang.active = (self.mau_nguoi_choi == chess.WHITE)
        self.btn_cam_den.active = (self.mau_nguoi_choi == chess.BLACK)
        self.btn_giam_depth.vo_hieu = self.do_sau_ai <= 1
        self.btn_tang_depth.vo_hieu = self.do_sau_ai >= DO_SAU_TOI_DA[self.thuat_toan_ai]
        for nut in (self.btn_alphabeta, self.btn_minimax, self.btn_cam_trang, self.btn_cam_den,
                    self.btn_giam_depth, self.btn_tang_depth):
            nut.ve(self.screen, mouse_pos)

        lbl_mau = self.font_chu.render("Bạn cầm quân", True, MAU_CHU_CHINH)
        self.screen.blit(lbl_mau, lbl_mau.get_rect(midleft=(rect.x + 16, self.btn_cam_den.rect.centery)))

        cy_depth = self.btn_giam_depth.rect.centery
        lbl_depth = self.font_chu.render("Độ sâu tìm kiếm (Depth)", True, MAU_CHU_CHINH)
        self.screen.blit(lbl_depth, lbl_depth.get_rect(midleft=(rect.x + 16, cy_depth)))

        # Độ sâu tốn nhiều thời gian được tô màu cam để cảnh báo
        cham = self.do_sau_ai >= 5 or (self.thuat_toan_ai == "Minimax" and self.do_sau_ai >= 4)
        depth_cx = (self.btn_giam_depth.rect.right + self.btn_tang_depth.rect.left) // 2
        txt_depth = self.font_muc.render(str(self.do_sau_ai), True, MAU_CAM if cham else MAU_VANG_DIEM)
        self.screen.blit(txt_depth, txt_depth.get_rect(center=(depth_cx, cy_depth)))
        if cham:
            canh_bao = self.font_nho.render("(chậm)", True, MAU_CAM)
            self.screen.blit(canh_bao, canh_bao.get_rect(midright=(self.btn_giam_depth.rect.x - 8, cy_depth)))

    def ve_thong_ke(self, rect: pygame.Rect):
        """Card thống kê lượt tìm kiếm gần nhất của AI dạng lưới 3x2."""
        self.ve_card(rect, "THỐNG KÊ NƯỚC ĐI AI")
        tk = self.thong_ke_ai
        node_moi_giay = tk["so_node"] / (tk["thoi_gian_ms"] / 1000) if tk["thoi_gian_ms"] > 0 else 0
        cac_o = [
            ("Nước vừa chọn", tk["nuoc_di"]),
            ("Thời gian", f"{tk['thoi_gian_ms']:,.0f} ms"),
            ("Số node duyệt", f"{tk['so_node']:,}"),
            ("Số lần cắt tỉa", f"{tk['so_cat_tia']:,}"),
            ("Điểm (góc nhìn Trắng)", dinh_dang_diem(tk["diem_danh_gia"])),
            ("Tốc độ", f"{dinh_dang_so_lon(node_moi_giay)} node/s"),
        ]
        o_w = (rect.w - 32 - 10) // 2
        o_h = 42
        for i, (nhan, gia_tri) in enumerate(cac_o):
            o = pygame.Rect(rect.x + 16 + (i % 2) * (o_w + 10), rect.y + 38 + (i // 2) * (o_h + 8), o_w, o_h)
            pygame.draw.rect(self.screen, MAU_O_THONG_KE, o, border_radius=7)
            lbl = self.font_nho.render(nhan, True, MAU_CHU_PHU)
            self.screen.blit(lbl, (o.x + 10, o.y + 3))
            val = self.font_chu_dam.render(gia_tri, True, MAU_CHU_CHINH)
            self.screen.blit(val, (o.x + 10, o.y + 19))

    def ve_lich_su(self, rect: pygame.Rect):
        """Card lịch sử nước đi (ký hiệu SAN), 2 cột x 6 hàng, luôn hiện các nước mới nhất."""
        self.ve_card(rect, "LỊCH SỬ NƯỚC ĐI")
        if not self.lich_su_san:
            txt = self.font_chu.render("Chưa có nước đi nào", True, MAU_CHU_MO)
            self.screen.blit(txt, txt.get_rect(center=(rect.centerx, rect.centery + 10)))
            return

        so_hang, so_cot = 6, 2
        cac_cap = [self.lich_su_san[i:i + 2] for i in range(0, len(self.lich_su_san), 2)]
        bat_dau = max(0, len(cac_cap) - so_hang * so_cot)
        cot_w = (rect.w - 32) // so_cot
        for k, cap in enumerate(cac_cap[bat_dau:]):
            stt = bat_dau + k
            x = rect.x + 16 + (k // so_hang) * cot_w
            cy = rect.y + 50 + (k % so_hang) * 21
            so = self.font_nho.render(f"{stt + 1}.", True, MAU_CHU_MO)
            self.screen.blit(so, so.get_rect(midleft=(x, cy)))
            for j, san in enumerate(cap):
                la_moi_nhat = (stt * 2 + j == len(self.lich_su_san) - 1)
                font = self.font_chu_dam if la_moi_nhat else self.font_chu
                mau = MAU_VANG_DIEM if la_moi_nhat else MAU_CHU_CHINH
                s = font.render(san, True, mau)
                self.screen.blit(s, s.get_rect(midleft=(x + 30 + j * 62, cy)))

    def ve_sidebar(self, mouse_pos: Tuple[int, int]):
        bx = SIDEBAR_X + 20
        bw = SIDEBAR_WIDTH - 40

        pygame.draw.rect(self.screen, MAU_NEN_SIDEBAR, pygame.Rect(SIDEBAR_X, 0, SIDEBAR_WIDTH, CHIEU_CAO))

        title = self.font_tieu_de.render("CỜ VUA AI", True, MAU_VANG_DIEM)
        self.screen.blit(title, (bx, 20))
        subtitle = self.font_chu.render("Minimax & Alpha-Beta Pruning", True, MAU_CHU_PHU)
        self.screen.blit(subtitle, (bx, 56))

        self.ve_trang_thai(pygame.Rect(bx, 92, bw, 52))
        self.ve_cai_dat(pygame.Rect(bx, 156, bw, 170), mouse_pos)
        self.ve_thong_ke(pygame.Rect(bx, 338, bw, 186))
        self.ve_lich_su(pygame.Rect(bx, 536, bw, 172))

        self.btn_hoan_tac.vo_hieu = len(self.ban_co.board.move_stack) == 0
        self.btn_choi_moi.ve(self.screen, mouse_pos)
        self.btn_hoan_tac.ve(self.screen, mouse_pos)

    def cap_nhat_con_tro(self, mouse_pos: Tuple[int, int]):
        """Đổi con trỏ thành bàn tay khi trỏ vào nút bấm hoặc quân có thể đi."""
        tro_tay = any(nut.dang_hover(mouse_pos) for nut in self.tat_ca_nut)
        if not tro_tay and mouse_pos[0] < BAN_CO_SIZE:
            if self.cho_phong_cap:
                tro_tay = self.quan_phong_cap_tai(mouse_pos) is not None
            elif self.co_the_tuong_tac():
                o = self.toa_do_thanh_o_co(*mouse_pos)
                tro_tay = self.o_dang_keo is not None or self.la_quan_cua_nguoi_choi(o) or any(
                    m.to_square == o for m in self.cac_nuoc_di_hop_le_o_chon
                )
        con_tro = pygame.SYSTEM_CURSOR_HAND if tro_tay else pygame.SYSTEM_CURSOR_ARROW
        if con_tro != getattr(self, "_con_tro", None):
            pygame.mouse.set_cursor(con_tro)
            self._con_tro = con_tro

    def chay(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[0] < BAN_CO_SIZE:
                        self.xu_ly_nhan_ban_co(event.pos)
                    else:
                        self.xu_ly_nut_bam(event)

                elif event.type == pygame.MOUSEMOTION and self.o_dang_keo is not None:
                    self.vi_tri_keo = event.pos

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.xu_ly_tha_chuot(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE or (
                        event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL
                    ):
                        if self.ban_co.board.move_stack:
                            self.xu_ly_hoan_tac()
                    elif event.key == pygame.K_n:
                        self.xu_ly_choi_moi()
                    elif event.key == pygame.K_ESCAPE:
                        self.bo_chon()

            self.kiem_tra_ket_qua_ai()

            # Render
            self.ve_ban_co(mouse_pos)
            self.ve_bang_phong_cap(mouse_pos)
            self.ve_thong_bao_ket_thuc()
            self.ve_thanh_danh_gia()
            self.ve_sidebar(mouse_pos)
            self.cap_nhat_con_tro(mouse_pos)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = GameCoVuong()
    game.chay()
