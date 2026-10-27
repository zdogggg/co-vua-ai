"""
Kiểm thử cho module cat_tia_alpha_beta.py
"""

import chess
from minimax import tim_nuoc_di_minimax
from cat_tia_alpha_beta import tim_nuoc_di_alpha_beta


def test_alpha_beta_dong_nhat_diem_voi_minimax():
    """
    Quy tắc quan trọng: Điểm của Alpha-Beta PHẢI bằng điểm của Minimax
    ở cùng vị trí và cùng độ sâu!
    """
    board = chess.Board()
    for d in [1, 2]:
        _, score_minimax, nodes_minimax = tim_nuoc_di_minimax(board, depth=d)
        _, score_ab, nodes_ab, cuts = tim_nuoc_di_alpha_beta(board, depth=d, su_dung_sap_xep=False)

        assert score_minimax == score_ab, f"Điểm không khớp ở depth {d}"
        if d >= 2:
            # Alpha-Beta phải duyệt ít hơn hoặc bằng số node của Minimax
            assert nodes_ab <= nodes_minimax


def test_alpha_beta_tim_duoc_chieu_het():
    board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
    best_move, score, nodes, cuts = tim_nuoc_di_alpha_beta(board, depth=2)

    assert best_move == chess.Move.from_uci("h5f7")
    assert score >= 100000
