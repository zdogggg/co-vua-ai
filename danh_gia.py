"""
danh_gia.py - Hàm đánh giá thế cờ (Evaluation Function)
Mục tiêu: Ước lượng lợi thế của thế cờ hiện tại.
Quy ước điểm:
- Điểm DƯƠNG (+) có lợi cho bên TRẮNG (White).
- Điểm ÂM (-) có lợi cho bên ĐEN (Black).
- 0: Cân bằng hoặc hòa cờ.
"""

import sys
import chess

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Giá trị cơ bản của từng quân cờ (tính bằng centipawn: 1 tốt = 100 điểm)
GIA_TRI_QUAN = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

DIEM_CHIEU_HET = 100000  # Điểm cực lớn cho trạng thái chiếu hết

# Bảng điểm vị trí (Piece-Square Tables - PST) chuẩn đơn giản của Tomasz Michniewski.
# Góc nhìn từ phía quân Trắng (từ ô a1=0 đến h8=63).
# Với quân Đen, ta lấy đối xứng qua gương (mirror) trục ngang.
BANG_DIEM_TOT = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

BANG_DIEM_MA = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BANG_DIEM_TUONG = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  5,  0,  0,  5,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

BANG_DIEM_XE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

BANG_DIEM_HAU = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

# Vua ở trung cuộc: Cần ẩn nấp an toàn (ví dụ nhập thành ở g1/c1)
BANG_DIEM_VUA_TRUNG_CUOC = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

BANG_DIEM_VI_TRI = {
    chess.PAWN: BANG_DIEM_TOT,
    chess.KNIGHT: BANG_DIEM_MA,
    chess.BISHOP: BANG_DIEM_TUONG,
    chess.ROOK: BANG_DIEM_XE,
    chess.QUEEN: BANG_DIEM_HAU,
    chess.KING: BANG_DIEM_VUA_TRUNG_CUOC,
}


def tinh_diem_vi_tri(loai_quan: chess.PieceType, o_co: chess.Square, mau_quan: bool) -> int:
    """
    Lấy điểm vị trí của quân cờ tại ô cờ tương ứng.
    Với quân Đen, lật ngược chỉ số ô theo trục ngang (mirror).
    """
    table = BANG_DIEM_VI_TRI.get(loai_quan)
    if not table:
        return 0

    if mau_quan == chess.WHITE:
        # chess.square_mirror lật hàng (a1 -> a8) vì trong mảng trên hàng 0 tương ứng rank 8
        sq_index = chess.square_mirror(o_co)
        return table[sq_index]
    else:
        # Đối với quân Đen, vị trí gốc giữ nguyên chỉ số
        return table[o_co]


def danh_gia_the_co(board: chess.Board) -> int:
    """
    Đánh giá thế cờ hiện tại.
    Trả về điểm số nguyên (centipawn):
    - Dương: Trắng đang ưu thế.
    - Âm: Đen đang ưu thế.
    - 0: Cân bằng hoặc hòa.
    """
    # 1. Kiểm tra trạng thái kết thúc ván cờ
    if board.is_checkmate():
        # Nếu lượt đi hiện tại là Trắng mà bị chiếu hết -> Đen thắng -> Điểm âm cực lớn
        # Nếu lượt đi hiện tại là Đen mà bị chiếu hết -> Trắng thắng -> Điểm dương cực lớn
        return -DIEM_CHIEU_HET if board.turn == chess.WHITE else DIEM_CHIEU_HET

    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.can_claim_threefold_repetition()
        or board.can_claim_fifty_moves()
    ):
        return 0

    diem_trang = 0
    diem_den = 0

    # 2. Duyệt qua từng quân cờ trên bàn cờ
    piece_map = board.piece_map()
    for square, piece in piece_map.items():
        # Điểm cơ bản của loại quân
        gia_tri = GIA_TRI_QUAN.get(piece.piece_type, 0)
        # Điểm cộng thêm theo vị trí chiến lược
        diem_vi_tri = tinh_diem_vi_tri(piece.piece_type, square, piece.color)

        tong_diem_quan = gia_tri + diem_vi_tri

        if piece.color == chess.WHITE:
            diem_trang += tong_diem_quan
        else:
            diem_den += tong_diem_quan

    # Điểm tổng = Lực lượng Trắng - Lực lượng Đen
    return diem_trang - diem_den


if __name__ == "__main__":
    print("=== GIAI ĐOẠN 2: KIỂM TRA HÀM ĐÁNH GIÁ THẾ CỜ ===")
    board = chess.Board()
    print("1. Điểm thế cờ ban đầu:")
    diem_goc = danh_gia_the_co(board)
    print(f"Điểm ban đầu: {diem_goc} (gần 0 là cân bằng)")

    print("\n2. Thực hiện nước đi Trắng e2e4:")
    board.push_san("e4")
    diem_e4 = danh_gia_the_co(board)
    print(f"Điểm sau khi Trắng đi e4: {diem_e4} (Trắng chiếm trung tâm nên điểm dương)")

    print("\n3. Thử trường hợp Đen mất Hậu:")
    board.reset()
    # Loại bỏ quân hậu Đen (d8)
    board.remove_piece_at(chess.D8)
    diem_mat_hau = danh_gia_the_co(board)
    print(f"Điểm khi Đen mất Hậu: {diem_mat_hau} (Trắng dẫn điểm áp đảo)")

    print("\n4. Kiểm tra trường hợp Chiếu hết (Scholar's Mate):")
    board.reset()
    for move in ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"]:
        board.push_san(move)
    print(f"Bàn cờ chiếu hết:")
    print(board)
    print(f"Điểm chiếu hết: {danh_gia_the_co(board)} (Trắng thắng = +{DIEM_CHIEU_HET})")

    print("\n=== HOÀN THÀNH GIAI ĐOẠN 2 THÀNH CÔNG ===")
