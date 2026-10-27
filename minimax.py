"""
minimax.py - Thuật toán Minimax thuần (không có cắt tỉa).
Mục tiêu: Tìm kiếm toàn bộ cây trò chơi tới độ sâu giới hạn (depth)
và chọn ra nước đi tối ưu nhất theo nguyên lý đối kháng cực đại/cực tiểu.
"""

import sys
import time
from typing import Tuple, Optional
import chess

from danh_gia import danh_gia_the_co, DIEM_CHIEU_HET

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MinimaxSearcher:
    """Bộ tìm kiếm Minimax thuần và theo dõi thống kê số node."""

    def __init__(self):
        self.so_node_da_tham = 0

    def minimax(self, board: chess.Board, depth: int, maximizing: bool) -> int:
        """
        Duyệt cây trạng thái bằng thuật toán Minimax.
        - board: Bàn cờ chess.Board hiện tại.
        - depth: Độ sâu còn lại cần tìm kiếm.
        - maximizing: True nếu đang ở tầng MAX (lượt Trắng), False nếu ở tầng MIN (lượt Đen).
        """
        self.so_node_da_tham += 1

        # Điều kiện dừng: Ván cờ kết thúc (chiếu hết hoặc hòa)
        if board.is_checkmate():
            # Nếu người vừa đi tạo ra chiếu hết:
            # - Nếu đang ở lượt Trắng (tức Đen vừa đi và chiếu hết Trắng) -> Đen thắng
            # - Nếu đang ở lượt Đen (tức Trắng vừa đi và chiếu hết Đen) -> Trắng thắng
            # Bổ sung '+ depth' hoặc '- depth' để ưu tiên chiếu hết nhanh nhất và tránh bị chiếu hết lâu nhất
            if board.turn == chess.WHITE:
                return -DIEM_CHIEU_HET - depth
            else:
                return DIEM_CHIEU_HET + depth

        if board.is_game_over():  # Hòa cờ (stalemate, repetition, 50-move, ...)
            return 0

        # Đạt tới độ sâu tối đa: Dùng hàm đánh giá tĩnh
        if depth == 0:
            return danh_gia_the_co(board)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return danh_gia_the_co(board)

        if maximizing:
            best_score = -float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1, maximizing=False)
                board.pop()
                if score > best_score:
                    best_score = score
            return int(best_score)
        else:
            best_score = float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1, maximizing=True)
                board.pop()
                if score < best_score:
                    best_score = score
            return int(best_score)

    def tim_nuoc_di_tot_nhat(
        self, board: chess.Board, depth: int
    ) -> Tuple[Optional[chess.Move], int, int]:
        """
        Tìm nước đi tốt nhất tại node gốc cho người đang đến lượt.
        Trả về tuple: (nuoc_di_tot_nhat, diem_danh_gia, so_node_da_tham).
        """
        self.so_node_da_tham = 0
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None, 0, 0

        maximizing = (board.turn == chess.WHITE)
        best_move = legal_moves[0]

        if maximizing:
            best_score = -float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1, maximizing=False)
                board.pop()
                if score > best_score:
                    best_score = score
                    best_move = move
        else:
            best_score = float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1, maximizing=True)
                board.pop()
                if score < best_score:
                    best_score = score
                    best_move = move

        return best_move, int(best_score), self.so_node_da_tham


def tim_nuoc_di_minimax(
    board: chess.Board, depth: int
) -> Tuple[Optional[chess.Move], int, int]:
    """Hàm bọc tiện ích gọi Minimax."""
    searcher = MinimaxSearcher()
    return searcher.tim_nuoc_di_tot_nhat(board, depth)


if __name__ == "__main__":
    print("=== GIAI ĐOẠN 3: KIỂM TRA THUẬT TOÁN MINIMAX THUẦN ===")
    board = chess.Board()

    for d in [1, 2, 3]:
        t0 = time.perf_counter()
        best_move, score, nodes = tim_nuoc_di_minimax(board, depth=d)
        t1 = time.perf_counter()
        thoi_gian_ms = (t1 - t0) * 1000

        print(
            f"Độ sâu {d}: Nước đi={best_move.uci() if best_move else 'None'}, "
            f"Điểm={score}, Số node={nodes:,}, Thời gian={thoi_gian_ms:.2f} ms"
        )

    # Thử nghiệm với một bài toán chiếu hết 1 nước (Mate in 1)
    # Bàn cờ: Trắng có thể chiếu hết ngay bằng Hậu Qxf7#
    print("\nKiểm tra bài toán Mate in 1 (Scholar's Mate):")
    board_mate1 = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
    t0 = time.perf_counter()
    best_move, score, nodes = tim_nuoc_di_minimax(board_mate1, depth=1)
    t1 = time.perf_counter()
    print(
        f"Nước tìm được: {best_move.uci()} (kỳ vọng 'h5f7'), "
        f"Điểm={score}, Node={nodes}, Thời gian={(t1-t0)*1000:.2f} ms"
    )
    print("\n=== HOÀN THÀNH GIAI ĐOẠN 3 THÀNH CÔNG ===")
