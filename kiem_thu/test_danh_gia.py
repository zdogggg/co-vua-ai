"""
Kiểm thử cho module danh_gia.py
"""

import chess
from danh_gia import danh_gia_the_co, DIEM_CHIEU_HET


def test_vi_tri_ban_dau():
    board = chess.Board()
    # Ở vị trí bắt đầu, lực lượng 2 bên bằng nhau và đối xứng -> điểm phải bằng 0
    assert danh_gia_the_co(board) == 0


def test_trang_thai_chieu_het():
    board = chess.Board()
    # Scholar's mate: 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
    for m in ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"]:
        board.push_san(m)

    assert board.is_checkmate()
    # Lượt hiện tại là Đen, Đen bị chiếu hết -> Trắng thắng -> Điểm dương cực đại
    assert danh_gia_the_co(board) == DIEM_CHIEU_HET


def test_trang_thai_hoa():
    # Thế cờ hòa Stalemate kinh điển (Vua Đen ở a8, Vua Trắng ở a6, Hậu Trắng ở c7)
    board = chess.Board("k7/2Q5/K7/8/8/8/8/8 b - - 0 1")
    assert board.is_stalemate()
    assert danh_gia_the_co(board) == 0


def test_uu_the_quan_so():
    board = chess.Board()
    # Bỏ quân Hậu của Đen
    board.remove_piece_at(chess.D8)
    # Trắng phải có điểm dương cao
    assert danh_gia_the_co(board) > 800


def test_hoa_do_lap_lai_3_lan():
    board = chess.Board()
    for m in ["Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1", "Ng8"]:
        board.push_san(m)
    assert board.is_repetition(3)
    assert danh_gia_the_co(board) == 0


def test_nhan_dien_tan_cuoc():
    from danh_gia import la_tan_cuoc
    # Khai cuộc đủ quân -> chưa phải tàn cuộc
    assert not la_tan_cuoc(chess.Board())
    # Chỉ còn Vua + Xe + Tốt -> tàn cuộc
    assert la_tan_cuoc(chess.Board("8/5pk1/4p3/R7/8/8/5K2/7r w - - 0 1"))


def test_vua_tan_cuoc_uu_tien_trung_tam():
    # Tàn cuộc: Vua Trắng ở trung tâm phải được chấm cao hơn Vua Trắng ở góc
    vua_trung_tam = chess.Board("7k/8/8/8/4K3/8/P7/8 w - - 0 1")
    vua_o_goc = chess.Board("7k/8/8/8/8/8/P7/K7 w - - 0 1")
    assert danh_gia_the_co(vua_trung_tam) > danh_gia_the_co(vua_o_goc)
