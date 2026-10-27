"""
Kiểm thử cho module minimax.py
"""

import chess
from minimax import tim_nuoc_di_minimax


def test_minimax_khong_lam_thay_doi_ban_co():
    board = chess.Board()
    fen_truoc = board.fen()
    best_move, score, nodes = tim_nuoc_di_minimax(board, depth=2)
    fen_sau = board.fen()

    # Bàn cờ trước và sau tìm kiếm phải giữ nguyên
    assert fen_truoc == fen_sau
    assert best_move in board.legal_moves
    assert nodes > 0


def test_minimax_tim_duoc_chieu_het_1_nuoc():
    # Scholar's mate: Trắng có thể chiếu hết ngay bằng Qh5xf7#
    board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
    best_move, score, nodes = tim_nuoc_di_minimax(board, depth=1)

    assert best_move == chess.Move.from_uci("h5f7")
    assert score >= 100000
