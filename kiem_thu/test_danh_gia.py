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
