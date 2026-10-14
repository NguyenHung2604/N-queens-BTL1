import time

from docplex.mp.model import Model
from docplex.mp.utils import DOcplexLimitsExceeded

from utils import check_solution


def _is_license_message(message):
    text = message.lower()
    return ("community edition" in text
            or "size limit" in text
            or "limits exceeded" in text
            or "promotional version" in text)


def solve_cplex_mip(n, show_board=True, time_limit=60):
    if n < 1:
        raise ValueError("Kích thước bàn cờ phải >= 1.")

    status = "ERROR"
    build_time = None
    solve_time = None
    valid = None
    error = ""

    try:
        # --- Xây dựng mô hình ---
        build_start = time.perf_counter()
        mdl = Model(name="nqueens")
        mdl.parameters.threads = 1
        mdl.parameters.randomseed = 42
        mdl.set_time_limit(time_limit)

        # x[r, c] = 1 nếu ô (r, c) có hậu.
        x = mdl.binary_var_matrix(n, n, name="x")

        # Mỗi hàng và mỗi cột đúng một hậu.
        for r in range(n):
            mdl.add_constraint(mdl.sum(x[r, c] for c in range(n)) == 1)
        for c in range(n):
            mdl.add_constraint(mdl.sum(x[r, c] for r in range(n)) == 1)

        # Mỗi đường chéo tối đa một hậu (nhóm 1 ô thì không cần ràng buộc).
        diagonal_minus = {}
        diagonal_plus = {}
        for r in range(n):
            for c in range(n):
                diagonal_minus.setdefault(r - c, []).append(x[r, c])
                diagonal_plus.setdefault(r + c, []).append(x[r, c])
        for cells in list(diagonal_minus.values()) + list(diagonal_plus.values()):
            if len(cells) > 1:
                mdl.add_constraint(mdl.sum(cells) <= 1)
        build_time = time.perf_counter() - build_start

        # --- Giải (gồm cả bước chuyển mô hình sang CPLEX) ---
        solve_start = time.perf_counter()
        solution = mdl.solve(log_output=False)
        solve_time = time.perf_counter() - solve_start

        detail = (mdl.solve_details.status or "").lower()
        if solution is not None:
            status = "SAT"
        elif "infeasible" in detail:
            status = "UNSAT"
        elif "time limit" in detail:
            status = "TIMEOUT"
        else:
            status = "UNKNOWN"
            error = detail

        # --- Kiểm tra nghiệm độc lập (không tính vào thời gian) ---
        if status == "SAT":
            queen_cells = {
                r * n + c + 1
                for r in range(n)
                for c in range(n)
                if solution.get_value(x[r, c]) > 0.5
            }
            valid = check_solution(queen_cells, n)

            if show_board and n <= 20:
                for r in range(n):
                    print(" ".join(
                        "Q" if (r * n + c + 1) in queen_cells else "."
                        for c in range(n)
                    ))

    except DOcplexLimitsExceeded as e:
        status = "LICENSE_ERROR"
        error = str(e)
    except Exception as e:  # lỗi khác của docplex/cplex
        status = "LICENSE_ERROR" if _is_license_message(str(e)) else "ERROR"
        error = str(e)

    total_time = None
    if build_time is not None and solve_time is not None:
        total_time = build_time + solve_time

    return {
        "n": n,
        "method": "cplex_mip",
        "status": status,
        "build_time": build_time,
        "solve_time": solve_time,
        "total_time": total_time,
        "valid": valid,
        "error": error,
    }


if __name__ == "__main__":
    for n in [1,2,3,8,44,88,120,300,512]:
        print(solve_cplex_mip(n, show_board=False))