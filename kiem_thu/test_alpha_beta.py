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


def test_alpha_beta_co_sap_xep_van_dong_nhat_diem_voi_minimax():
    # Sắp xếp nước đi chỉ thay đổi thứ tự duyệt, KHÔNG được làm thay đổi điểm số
    board = chess.Board("r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    _, score_minimax, nodes_minimax = tim_nuoc_di_minimax(board, depth=3)
    _, score_ab, nodes_ab, _ = tim_nuoc_di_alpha_beta(board, depth=3, su_dung_sap_xep=True)

    assert score_minimax == score_ab
    assert nodes_ab < nodes_minimax


def test_alpha_beta_uu_tien_chieu_het_nhanh_nhat():
    # Mate hàng cuối: Rxd8# chiếu hết ngay. Ở depth 3 AI phải chọn mate 1 nước
    # (điểm DIEM_CHIEU_HET + depth còn lại = 100002) thay vì đường chiếu hết dài hơn.
    board = chess.Board("3r2k1/5ppp/8/8/8/8/5PPP/3RQ1K1 w - - 0 1")
    best_move, score, _, _ = tim_nuoc_di_alpha_beta(board, depth=3)
    assert best_move == chess.Move.from_uci("d1d8")
    assert score == 100002
