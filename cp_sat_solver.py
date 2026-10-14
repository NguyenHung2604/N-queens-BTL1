import time

from ortools.sat.python import cp_model

from utils import check_solution


def solve_cp_sat(n, show_board=True, time_limit=60):
    # --- Xây dựng mô hình ---
    build_start = time.perf_counter()
    model = cp_model.CpModel()
    queens = [
        model.new_int_var(0, n - 1, f"queen_{r}")
        for r in range(n)
    ]
    model.add_all_different(queens)
    model.add_all_different([r + queens[r] for r in range(n)])
    model.add_all_different([r - queens[r] for r in range(n)])
    build_time = time.perf_counter() - build_start

    # --- Cấu hình solver ---
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42
    solver.parameters.max_time_in_seconds = time_limit

    # --- Giải ---
    solve_start = time.perf_counter()
    status_code = solver.solve(model)
    solve_time = time.perf_counter() - solve_start

    # --- Quy đổi trạng thái ---
    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        status = "SAT"
    elif status_code == cp_model.INFEASIBLE:
        status = "UNSAT"
    elif status_code == cp_model.MODEL_INVALID:
        status = "ERROR"
    else:
        status = "UNKNOWN"

    # --- Kiểm tra nghiệm độc lập (không tính vào thời gian) ---
    valid = None
    if status == "SAT":
        columns = [solver.value(queens[r]) for r in range(n)]
        queen_cells = {r * n + columns[r] + 1 for r in range(n)}
        valid = check_solution(queen_cells, n)

        if show_board and n <= 20:
            for r in range(n):
                print(" ".join("Q" if columns[r] == c else "." for c in range(n)))

    return {
        "n": n,
        "method": "cp_sat",
        "status": status,
        "build_time": build_time,
        "solve_time": solve_time,
        "total_time": build_time + solve_time,
        "valid": valid,
    }


if __name__ == "__main__":
    for n in [1,2,3,8,44,88,120,300,512]:
        print(solve_cp_sat(n,show_board=False))