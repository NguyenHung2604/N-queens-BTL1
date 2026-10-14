import time

from docplex.cp.model import CpoModel

from utils import check_solution


def _is_license_message(message):
    text = message.lower()
    return ("community edition" in text
            or "size limit" in text
            or "limits exceeded" in text
            or "license" in text
            or "promotional version" in text)


def solve_cplex_cp(n, show_board=True, time_limit=60):
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
        mdl = CpoModel(name="nqueens")
        queens = [mdl.integer_var(0, n - 1, f"q{r}") for r in range(n)]
        mdl.add(mdl.all_diff(queens))
        mdl.add(mdl.all_diff([queens[r] + r for r in range(n)]))
        mdl.add(mdl.all_diff([queens[r] - r for r in range(n)]))
        build_time = time.perf_counter() - build_start

        # --- Giải ---
        solve_start = time.perf_counter()
        solution = mdl.solve(
            TimeLimit=time_limit,
            Workers=1,
            RandomSeed=42,
            LogVerbosity="Quiet",
        )
        solve_time = time.perf_counter() - solve_start

        solve_status = solution.get_solve_status()
        if solution.is_solution():
            status = "SAT"
        elif solve_status == "Infeasible":
            status = "UNSAT"
        elif solve_status == "Unknown" and solve_time >= 0.95 * time_limit:
            status = "TIMEOUT"
        else:
            status = "UNKNOWN"
            error = str(solve_status)

        # --- Kiểm tra nghiệm độc lập (không tính vào thời gian) ---
        if status == "SAT":
            columns = [solution.get_value(queens[r]) for r in range(n)]
            queen_cells = {r * n + columns[r] + 1 for r in range(n)}
            valid = check_solution(queen_cells, n)

            if show_board and n <= 20:
                for r in range(n):
                    print(" ".join(
                        "Q" if columns[r] == c else "." for c in range(n)
                    ))

    except Exception as e:  # lỗi engine, license hoặc cài đặt
        status = "LICENSE_ERROR" if _is_license_message(str(e)) else "ERROR"
        error = str(e)

    total_time = None
    if build_time is not None and solve_time is not None:
        total_time = build_time + solve_time

    return {
        "n": n,
        "method": "cplex_cp",
        "status": status,
        "build_time": build_time,
        "solve_time": solve_time,
        "total_time": total_time,
        "valid": valid,
        "error": error,
    }


if __name__ == "__main__":
    for n in [1,2,3,8,44,88,120,300,512]:
        print(solve_cplex_cp(n, show_board=False))