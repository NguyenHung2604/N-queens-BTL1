import time

import gurobipy as gp
from gurobipy import GRB

from utils import check_solution

# Mã lỗi Gurobi liên quan license: 10009 = không có license,
# 10010 = mô hình vượt giới hạn kích thước của license.
LICENSE_ERRORS = {10009, 10010}


def solve_gurobi(n, show_board=True, time_limit=60):
    if n < 1:
        raise ValueError("Kích thước bàn cờ phải >= 1.")

    status = "ERROR"
    build_time = None
    solve_time = None
    valid = None
    error = ""

    try:
        # Khởi tạo model (gồm kiểm tra license) nằm ngoài thời gian đo.
        model = gp.Model("nqueens")
        model.Params.OutputFlag = 0
        model.Params.Threads = 1
        model.Params.Seed = 42
        model.Params.TimeLimit = time_limit

        # --- Xây dựng mô hình ---
        build_start = time.perf_counter()

        # x[r, c] = 1 nếu ô (r, c) có hậu.
        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

        # Mỗi hàng đúng một hậu.
        for r in range(n):
            model.addConstr(gp.quicksum(x[r, c] for c in range(n)) == 1)

        # Mỗi cột đúng một hậu.
        for c in range(n):
            model.addConstr(gp.quicksum(x[r, c] for r in range(n)) == 1)

        # Gom các ô theo đường chéo.
        diagonal_minus = {}
        diagonal_plus = {}
        for r in range(n):
            for c in range(n):
                diagonal_minus.setdefault(r - c, []).append(x[r, c])
                diagonal_plus.setdefault(r + c, []).append(x[r, c])

        # Mỗi đường chéo tối đa một hậu (nhóm 1 ô thì không cần ràng buộc).
        for cells in diagonal_minus.values():
            if len(cells) > 1:
                model.addConstr(gp.quicksum(cells) <= 1)
        for cells in diagonal_plus.values():
            if len(cells) > 1:
                model.addConstr(gp.quicksum(cells) <= 1)

        model.update()
        build_time = time.perf_counter() - build_start

        # --- Giải ---
        solve_start = time.perf_counter()
        model.optimize()
        solve_time = time.perf_counter() - solve_start

        # --- Quy đổi trạng thái ---
        if model.Status == GRB.OPTIMAL:
            status = "SAT"
        elif model.Status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
            # Mô hình không có hàm mục tiêu nên không thể unbounded.
            status = "UNSAT"
        elif model.Status == GRB.TIME_LIMIT:
            status = "SAT" if model.SolCount > 0 else "TIMEOUT"
        else:
            status = "UNKNOWN"

        # --- Kiểm tra nghiệm độc lập (không tính vào thời gian) ---
        if status == "SAT":
            values = model.getAttr("X", x)  # lấy toàn bộ giá trị một lần
            queen_cells = {
                r * n + c + 1
                for r in range(n)
                for c in range(n)
                if values[r, c] > 0.5
            }
            valid = check_solution(queen_cells, n)

            if show_board and n <= 20:
                for r in range(n):
                    print(" ".join(
                        "Q" if (r * n + c + 1) in queen_cells else "."
                        for c in range(n)
                    ))

    except gp.GurobiError as e:
        status = "LICENSE_ERROR" if e.errno in LICENSE_ERRORS else "ERROR"
        error = str(e)

    total_time = None
    if build_time is not None and solve_time is not None:
        total_time = build_time + solve_time

    return {
        "n": n,
        "method": "gurobi",
        "status": status,
        "build_time": build_time,
        "solve_time": solve_time,
        "total_time": total_time,
        "valid": valid,
        "error": error,
    }


if __name__ == "__main__":
    for n in [1,2,3,8,44,88,120,300,512]:
        print(solve_gurobi(n, show_board=False))