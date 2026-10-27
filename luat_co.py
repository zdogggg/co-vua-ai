"""
luat_co.py - Quản lý bàn cờ và bọc các chức năng luật cờ từ thư viện python-chess.
Mục tiêu: Đóng gói các thao tác cơ bản về bàn cờ, nước đi hợp lệ, thực hiện/hoàn tác nước đi.
"""

import sys
from typing import List, Optional
import chess

# Đảm bảo in tiếng Việt có dấu mượt mà trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class BanCo:
    """
    Lớp đại diện cho bàn cờ và các quy tắc trò chơi cờ vua.
    Bọc quanh đối tượng chess.Board() của python-chess.
    """

    def __init__(self, fen: Optional[str] = None):
        """
        Khởi tạo bàn cờ. Nếu không truyền FEN, bàn cờ sẽ ở vị trí xuất phát chuẩn.
        """
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()

    def dat_lai(self):
        """Đặt lại bàn cờ về vị trí ban đầu."""
        self.board.reset()

    @property
    def luot_di(self) -> bool:
        """
        Trả về lượt đi hiện tại:
        chess.WHITE (True) nếu là lượt Trắng.
        chess.BLACK (False) nếu là lượt Đen.
        """
        return self.board.turn

    def lay_cac_nuoc_di_hop_le(self) -> List[chess.Move]:
        """Trả về danh sách tất cả các nước đi hợp lệ tại vị trí hiện tại."""
        return list(self.board.legal_moves)

    def thuc_hien_nuoc_di(self, move: chess.Move) -> bool:
        """
        Thực hiện một nước đi trên bàn cờ nếu hợp lệ.
        Trả về True nếu thành công, False nếu nước đi không hợp lệ.
        """
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False

    def thuc_hien_nuoc_di_uci(self, uci_str: str) -> bool:
        """Thực hiện nước đi theo chuỗi UCI (ví dụ: 'e2e4', 'g1f3')."""
        try:
            move = chess.Move.from_uci(uci_str)
            return self.thuc_hien_nuoc_di(move)
        except ValueError:
            return False

    def hoan_tac_nuoc_di(self) -> Optional[chess.Move]:
        """
        Hoàn tác nước đi gần nhất (pop khỏi stack).
        Rất quan trọng cho thuật toán tìm kiếm Minimax / Alpha-Beta.
        Trả về nước đi vừa được hoàn tác, hoặc None nếu bàn cờ chưa có nước đi nào.
        """
        if len(self.board.move_stack) > 0:
            return self.board.pop()
        return None

    def la_chieu_vua(self) -> bool:
        """Kiểm tra bên đang đến lượt có đang bị chiếu hay không."""
        return self.board.is_check()

    def la_chieu_het(self) -> bool:
        """Kiểm tra thế cờ có phải là chiếu hết (checkmate) hay không."""
        return self.board.is_checkmate()

    def la_hoa_co(self) -> bool:
        """
        Kiểm tra hòa cờ theo các luật:
        - Hết nước đi hợp lệ nhưng không bị chiếu (stalemate / pat).
        - Không đủ lực lượng để chiếu hết (insufficient material).
        - Lặp lại thế cờ 3 lần (threefold repetition).
        - Luật 50 nước không ăn quân, không đi tốt (fifty moves rule).
        """
        return (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.can_claim_threefold_repetition()
            or self.board.can_claim_fifty_moves()
        )

    def da_ket_thuc(self) -> bool:
        """Kiểm tra ván cờ đã kết thúc chưa (chiếu hết hoặc hòa cờ)."""
        return self.board.is_game_over()

    def ket_qua(self) -> str:
        """
        Trả về kết quả ván cờ:
        '1-0' (Trắng thắng), '0-1' (Đen thắng), '1/2-1/2' (Hòa), '*' (Đang tiếp tục).
        """
        return self.board.result()

    def in_ban_co(self):
        """In bàn cờ trực quan ra terminal."""
        print(self.board)


# Demo và tự kiểm tra khi chạy trực tiếp file này (Giai đoạn 1)
if __name__ == "__main__":
    print("=== GIAI ĐOẠN 1: KIỂM TRA LUẬT CỜ & HOÀN TÁC NƯỚC ĐI ===")
    ban_co = BanCo()

    print("\n1. Bàn cờ xuất phát:")
    ban_co.in_ban_co()

    print(f"\nLượt đi hiện tại: {'Trắng' if ban_co.luot_di == chess.WHITE else 'Đen'}")
    nuoc_di_hop_le = ban_co.lay_cac_nuoc_di_hop_le()
    print(f"Số nước đi hợp lệ của Trắng: {len(nuoc_di_hop_le)}")
    print(f"Một số nước đi mẫu: {[m.uci() for m in nuoc_di_hop_le[:5]]}")

    print("\n2. Thực hiện nước đi Trắng: e2e4")
    ban_co.thuc_hien_nuoc_di_uci("e2e4")
    ban_co.in_ban_co()

    print("\n3. Thực hiện nước đi Đen: e7e5")
    ban_co.thuc_hien_nuoc_di_uci("e7e5")
    ban_co.in_ban_co()

    print("\n4. Kiểm tra hoàn tác (Undo) nước đi e7e5:")
    nuoc_vua_hoan_tac = ban_co.hoan_tac_nuoc_di()
    print(f"Nước vừa hoàn tác: {nuoc_vua_hoan_tac.uci() if nuoc_vua_hoan_tac else 'Không có'}")
    ban_co.in_ban_co()

    print("\n5. Thử kịch bản Scholar's Mate (Chiếu hết 4 nước):")
    ban_co.dat_lai()
    nuoc_di_scholars_mate = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
    for uci in nuoc_di_scholars_mate:
        ban_co.thuc_hien_nuoc_di_uci(uci)

    ban_co.in_ban_co()
    print(f"Chiếu vua: {ban_co.la_chieu_vua()}")
    print(f"Chiếu hết: {ban_co.la_chieu_het()}")
    print(f"Kết quả ván cờ: {ban_co.ket_qua()}")
    print("\n=== HOÀN THÀNH GIAI ĐOẠN 1 THÀNH CÔNG ===")
