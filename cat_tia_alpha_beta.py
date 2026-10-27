"""
cat_tia_alpha_beta.py - Thuật toán Minimax kết hợp Cắt tỉa Alpha-Beta (Alpha-Beta Pruning).
Mục tiêu: Tối ưu hóa không gian tìm kiếm bằng cách loại bỏ các nhánh không ảnh hưởng đến
kết quả cuối cùng, giúp tăng đáng kể tốc độ và độ sâu tìm kiếm.
"""

import sys
import time
from typing import Tuple, Optional, List
import chess

from danh_gia import danh_gia_the_co, DIEM_CHIEU_HET

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def sap_xep_nuoc_di(board: chess.Board, legal_moves: List[chess.Move]) -> List[chess.Move]:
    """
    Sắp xếp các nước đi ưu tiên để tối ưu hóa hiệu quả cắt tỉa Alpha-Beta:
    - Nước bắt quân (capture) và nước phong cấp (promotion) xét đầu tiên.
    - Nước chiếu vua (check) xét tiếp theo.
    - Các nước đi thông thường xét sau.
    Việc kiểm tra nước đi tốt trước giúp cập nhật alpha/beta nhanh hơn và cắt tỉa nhiều hơn.
    """
    def diem_uu_tien(move: chess.Move) -> int:
        diem = 0
        if board.is_capture(move):
            # Nước ăn quân: ưu tiên quân ăn có giá trị thấp ăn quân giá trị cao (MVV-LVA sơ bộ)
            victim = board.piece_at(move.to_square)
            if victim:
                diem += 1000 + victim.piece_type * 10
            else:
                diem += 1000  # En passant
        if move.promotion:
            diem += 900
        if board.gives_check(move):
            diem += 500
        return diem

    return sorted(legal_moves, key=diem_uu_tien, reverse=True)


class AlphaBetaSearcher:
    """Bộ tìm kiếm Alpha-Beta Pruning và theo dõi số node, số lần cắt tỉa."""

    def __init__(self, su_dung_sap_xep: bool = True):
        self.so_node_da_tham = 0
        self.so_lan_cat_tia = 0
        self.su_dung_sap_xep = su_dung_sap_xep

    def alphabeta(
        self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool
    ) -> int:
        """
        Duyệt cây trò chơi với cắt tỉa Alpha-Beta.
        - alpha: Giá trị tốt nhất mà MAX đảm bảo được trên đường đi.
        - beta: Giá trị tốt nhất mà MIN đảm bảo được trên đường đi.
        """
        self.so_node_da_tham += 1

        # Điều kiện kết thúc ván cờ
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -DIEM_CHIEU_HET - depth
            else:
                return DIEM_CHIEU_HET + depth

        if board.is_game_over():
            return 0

        # Đạt tới độ sâu tối đa
        if depth == 0:
            return danh_gia_the_co(board)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return danh_gia_the_co(board)

        if self.su_dung_sap_xep:
            legal_moves = sap_xep_nuoc_di(board, legal_moves)

        if maximizing:
            best_score = -float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.alphabeta(board, depth - 1, alpha, beta, maximizing=False)
                board.pop()

                if score > best_score:
                    best_score = score
                if best_score > alpha:
                    alpha = best_score

                # Cắt tỉa: Nếu MAX tìm thấy nước tốt hơn hoặc bằng giới hạn MIN chấp nhận
                if alpha >= beta:
                    self.so_lan_cat_tia += 1
                    break

            return int(best_score)
        else:
            best_score = float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.alphabeta(board, depth - 1, alpha, beta, maximizing=True)
                board.pop()

                if score < best_score:
                    best_score = score
                if best_score < beta:
                    beta = best_score

                # Cắt tỉa: Nếu MIN tìm thấy nước thấp hơn hoặc bằng giới hạn MAX chấp nhận
                if alpha >= beta:
                    self.so_lan_cat_tia += 1
                    break

            return int(best_score)

    def tim_nuoc_di_tot_nhat(
        self, board: chess.Board, depth: int
    ) -> Tuple[Optional[chess.Move], int, int, int]:
        """
        Tìm nước đi tốt nhất tại node gốc.
        Trả về tuple: (nuoc_di_tot_nhat, diem_danh_gia, so_node_da_tham, so_lan_cat_tia).
        """
        self.so_node_da_tham = 0
        self.so_lan_cat_tia = 0

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None, 0, 0, 0

        if self.su_dung_sap_xep:
            legal_moves = sap_xep_nuoc_di(board, legal_moves)

        maximizing = (board.turn == chess.WHITE)
        best_move = legal_moves[0]
        alpha = -float("inf")
        beta = float("inf")

        if maximizing:
            best_score = -float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.alphabeta(board, depth - 1, alpha, beta, maximizing=False)
                board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move
                if best_score > alpha:
                    alpha = best_score

                if alpha >= beta:
                    self.so_lan_cat_tia += 1
                    break
        else:
            best_score = float("inf")
            for move in legal_moves:
                board.push(move)
                score = self.alphabeta(board, depth - 1, alpha, beta, maximizing=True)
                board.pop()

                if score < best_score:
                    best_score = score
                    best_move = move
                if best_score < beta:
                    beta = best_score

                if alpha >= beta:
                    self.so_lan_cat_tia += 1
                    break

        return best_move, int(best_score), self.so_node_da_tham, self.so_lan_cat_tia


def tim_nuoc_di_alpha_beta(
    board: chess.Board, depth: int, su_dung_sap_xep: bool = True
) -> Tuple[Optional[chess.Move], int, int, int]:
    """Hàm bọc tiện ích gọi Alpha-Beta Pruning."""
    searcher = AlphaBetaSearcher(su_dung_sap_xep=su_dung_sap_xep)
    return searcher.tim_nuoc_di_tot_nhat(board, depth)


if __name__ == "__main__":
    print("=== GIAI ĐOẠN 4: KIỂM TRA THUẬT TOÁN ALPHA-BETA PRUNING ===")
    board = chess.Board()

    for d in [1, 2, 3, 4]:
        t0 = time.perf_counter()
        best_move, score, nodes, cuts = tim_nuoc_di_alpha_beta(board, depth=d)
        t1 = time.perf_counter()
        thoi_gian_ms = (t1 - t0) * 1000

        print(
            f"Độ sâu {d}: Nước đi={best_move.uci() if best_move else 'None'}, "
            f"Điểm={score}, Node={nodes:,}, Cắt tỉa={cuts:,}, Thời gian={thoi_gian_ms:.2f} ms"
        )

    # Thử nghiệm với bài toán Mate in 1
    print("\nKiểm tra bài toán Mate in 1 (Scholar's Mate):")
    board_mate1 = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
    t0 = time.perf_counter()
    best_move, score, nodes, cuts = tim_nuoc_di_alpha_beta(board_mate1, depth=1)
    t1 = time.perf_counter()
    print(
        f"Nước tìm được: {best_move.uci()} (kỳ vọng 'h5f7'), "
        f"Điểm={score}, Node={nodes}, Cắt tỉa={cuts}, Thời gian={(t1-t0)*1000:.2f} ms"
    )
    print("\n=== HOÀN THÀNH GIAI ĐOẠN 4 THÀNH CÔNG ===")
