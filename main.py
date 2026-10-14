from itertools import combinations
from time import perf_counter

from pysat.formula import IDPool
from pysat.solvers import Glucose3

from pairwise import encode_amo as pairwise_amo
from sequential import encode_amo as sequential_amo
from binary import encode_amo as binary_amo
from product import encode_amo as product_amo
from utils import check_solution

def solve_nqueens(n, encoding, show_board = True):
    if n < 1:
        raise ValueError("Kích thước bàn cờ phải >= 1.")

    # Chọn hàm tạo AMO.
    if encoding == "pairwise":
        encode_amo = pairwise_amo
    elif encoding == "sequential":
        encode_amo = sequential_amo
    elif encoding == "binary":
        encode_amo = binary_amo
    elif encoding == "product":
        encode_amo = product_amo
    else:
        raise ValueError("Encoding phải là pairwise, sequential, binary hoặc product.")

    def var(r, c):
        return r * n + c + 1

    start_encode = perf_counter()

    # Mỗi lần giải tạo lại clauses và pool riêng.
    clauses = []
    pool = IDPool(start_from=n * n + 1)

    def AMO(variables):
        new_clauses = encode_amo(variables, pool)
        clauses.extend(new_clauses)

    def AMO_and_ALO(variables):
        clauses.append(variables)  # Ít nhất một ô có hậu.
        AMO(variables)             # Tối đa một ô có hậu.

    # Mỗi hàng có đúng một hậu.
    for r in range(n):
        row = [var(r, c) for c in range(n)]
        AMO_and_ALO(row)

    # Mỗi cột có đúng một hậu.
    for c in range(n):
        col = [var(r, c) for r in range(n)]
        AMO_and_ALO(col)

    # Gom các ô theo đường chéo.
    diagonal_minus = {}
    diagonal_plus = {}

    for r in range(n):
        for c in range(n):
            key_minus = r - c
            key_plus = r + c

            if key_minus not in diagonal_minus:
                diagonal_minus[key_minus] = []

            if key_plus not in diagonal_plus:
                diagonal_plus[key_plus] = []

            diagonal_minus[key_minus].append(var(r, c))
            diagonal_plus[key_plus].append(var(r, c))

    # Mỗi đường chéo có tối đa một hậu.
    for diagonal in diagonal_minus.values():
        AMO(diagonal)

    for diagonal in diagonal_plus.values():
        AMO(diagonal)

    encode_time = perf_counter() - start_encode
    total_variables = max(n * n, pool.top)

    print(f"\nN = {n} | Encoding: {encoding}")
    print("Số biến ô bàn cờ:", n * n)
    print("Số biến phụ:", total_variables - n * n)
    print("Tổng số biến:", total_variables)
    print("Số clause:", len(clauses))

    # chưa có nghiệm để kiểm tra
    valid = None
    start_load = perf_counter()

    with Glucose3(bootstrap_with=clauses) as solver:
        load_time = perf_counter() - start_load

        start_solve = perf_counter()
        satisfiable = solver.solve()
        solve_time = perf_counter() - start_solve

        print(f"Thời gian tạo CNF: {encode_time:.6f} giây")
        print(f"Thời gian nạp CNF: {load_time:.6f} giây")
        print(f"Thời gian giải:    {solve_time:.6f} giây")

        if satisfiable:
            model = solver.get_model()

            # Chỉ lấy biến ô bàn cờ, bỏ qua biến phụ.
            queen_cells = {
                x for x in model
                if 1 <= x <= n * n
            }

            valid = check_solution(queen_cells, n)
            print("Nghiệm hợp lệ:", valid)

            if not valid:
                raise RuntimeError("Nghiệm vi phạm luật N-Queens!")

            if show_board and n <= 20:
                for r in range(n):
                    row_display = [
                        "Q" if var(r, c) in queen_cells else "."
                        for c in range(n)
                    ]
                    print(" ".join(row_display))
        else:
            print("Bài toán không có nghiệm.")
    return {
        "n": n,
        "encoding": encoding,
        "status": "SAT" if satisfiable else "UNSAT",
        "board_variables": n * n,
        "aux_variables": total_variables - n * n,
        "total_variables": total_variables,
        "clauses": len(clauses),
        "encode_time": encode_time,
        "load_time": load_time,
        "solve_time": solve_time,
        "total_time": encode_time + load_time + solve_time,
        "valid": valid,
    }

if __name__ == "__main__":
    solve_nqueens(n=15, encoding="pairwise")
    solve_nqueens(n=15, encoding="sequential")