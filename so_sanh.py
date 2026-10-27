"""
so_sanh.py - Benchmark và so sánh hiệu năng giữa Minimax thuần và Alpha-Beta Pruning.
Mục tiêu: Đưa ra số liệu thực nghiệm định lượng (Node, Thời gian, Số lần cắt tỉa, Speedup)
để phục vụ báo cáo và bảo vệ đồ án.
"""

import sys
import time
from typing import Dict, Any, List
import chess

from minimax import tim_nuoc_di_minimax
from cat_tia_alpha_beta import tim_nuoc_di_alpha_beta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


CAC_THE_CO_THU_NGHIEM = [
    {
        "ten": "Khai cuộc (Vị trí bắt đầu)",
        "fen": chess.STARTING_FEN,
        "mo_ta": "Bàn cờ chuẩn 32 quân"
    },
    {
        "ten": "Trung cuộc (Italian Game)",
        "fen": "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        "mo_ta": "Nhiều lựa chọn chiến thuật, trung tâm mở"
    },
    {
        "ten": "Tàn cuộc (Vua + Xe vs Vua + Xe + Tốt)",
        "fen": "8/5pk1/4p3/R7/8/8/5K2/7r w - - 0 1",
        "mo_ta": "Ít quân cờ, cây tìm kiếm sâu hơn"
    }
]


def chay_benchmark(do_sau_toi_da: int = 3):
    """
    Chạy thử nghiệm trên các thế cờ khác nhau với các độ sâu từ 1 đến do_sau_toi_da.
    In ra bảng kết quả chi tiết.
    """
    print("=" * 95)
    print("               BÁO CÁO BENCHMARK: MINIMAX THUẦN VS ALPHA-BETA PRUNING")
    print("=" * 95)

    for item in CAC_THE_CO_THU_NGHIEM:
        ten_the_co = item["ten"]
        fen = item["fen"]
        board = chess.Board(fen)

        print(f"\n▶ Thế cờ: {ten_the_co}")
        print(f"  FEN: {fen}")
        print("-" * 95)
        print(
            f"{'Độ sâu':<7} | {'Thuật toán':<18} | {'Nước đi':<8} | {'Điểm':<7} | "
            f"{'Số node':<10} | {'Cắt tỉa':<8} | {'Thời gian (ms)':<15} | {'Tăng tốc'}"
        )
        print("-" * 95)

        for depth in range(1, do_sau_toi_da + 1):
            # 1. Chạy Minimax
            t0 = time.perf_counter()
            mv_mm, score_mm, nodes_mm = tim_nuoc_di_minimax(board, depth)
            t1 = time.perf_counter()
            time_mm = (t1 - t0) * 1000

            # 2. Chạy Alpha-Beta
            t2 = time.perf_counter()
            mv_ab, score_ab, nodes_ab, cuts_ab = tim_nuoc_di_alpha_beta(board, depth)
            t3 = time.perf_counter()
            time_ab = (t3 - t2) * 1000

            # Tính tỷ lệ giảm node và tăng tốc độ
            giam_node_pct = ((nodes_mm - nodes_ab) / nodes_mm * 100) if nodes_mm > 0 else 0
            speedup = (time_mm / time_ab) if time_ab > 0 else 1.0

            # In dòng Minimax
            print(
                f"{depth:<7} | {'Minimax thuần':<18} | {mv_mm.uci() if mv_mm else 'None':<8} | "
                f"{score_mm:<7} | {nodes_mm:<10,} | {'0':<8} | {time_mm:<15.2f} | 1.0x (gốc)"
            )
            # In dòng Alpha-Beta
            print(
                f"{depth:<7} | {'Alpha-Beta':<18} | {mv_ab.uci() if mv_ab else 'None':<8} | "
                f"{score_ab:<7} | {nodes_ab:<10,} | {cuts_ab:<8,} | {time_ab:<15.2f} | "
                f"{speedup:.1f}x (Giảm {giam_node_pct:.1f}% node)"
            )
            print("." * 95)


if __name__ == "__main__":
    chay_benchmark(do_sau_toi_da=3)
