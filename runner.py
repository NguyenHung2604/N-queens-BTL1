import contextlib
import io
import multiprocessing as mp
from queue import Empty

ALL_METHODS = [
    "sat_pairwise",
    "sat_sequential",
    "sat_binary",
    "sat_product",
    "cp_sat",
    "gurobi",
    "cplex_cp",
    "cplex_mip",
]

def _worker(method, n, time_limit, queue):
    # Chạy trong tiến trình con. Import ở đây để tiến trình con tự nạp thư viện.
    try:
        # Tắt các dòng print của solver để benchmark không bị rối.
        with contextlib.redirect_stdout(io.StringIO()):
            if method == "sat_pairwise":
                from main import solve_nqueens
                result = solve_nqueens(n, "pairwise", show_board=False)
            elif method == "sat_sequential":
                from main import solve_nqueens
                result = solve_nqueens(n, "sequential", show_board=False)
            elif method == "sat_binary":
                from main import solve_nqueens
                result = solve_nqueens(n, "binary", show_board=False)
            elif method == "sat_product":
                from main import solve_nqueens
                result = solve_nqueens(n, "product", show_board=False)
            elif method == "cp_sat":
                from cp_sat_solver import solve_cp_sat
                result = solve_cp_sat(n, show_board=False, time_limit=time_limit)
            elif method == "gurobi":
                from gurobi_solver import solve_gurobi
                result = solve_gurobi(n, show_board=False, time_limit=time_limit)
            elif method == "cplex_cp":
                from cplex_cp_solver import solve_cplex_cp
                result = solve_cplex_cp(n, show_board=False, time_limit=time_limit)
            elif method == "cplex_mip":
                from clpex_mip_solver import solve_cplex_mip
                result = solve_cplex_mip(n, show_board=False, time_limit=time_limit)
            else:
                raise ValueError(f"Method không hợp lệ: {method}")
        queue.put(result)
    except Exception as e:
        queue.put({"n": n, "status": "ERROR", "error": str(e)})


def run_with_timeout(method, n, time_limit=60, grace=10):
    """Chạy một lượt giải trong tiến trình con, bị giết sau time_limit + grace giây."""
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    process = ctx.Process(target=_worker, args=(method, n, time_limit, queue))

    process.start()
    process.join(timeout=time_limit + grace)

    if process.is_alive():
        process.terminate()
        process.join()
        return {"n": n, "method": method, "status": "TIMEOUT", "error": ""}

    try:
        result = queue.get(timeout=2)
    except Empty:
        return {"n": n, "method": method, "status": "ERROR",
                "error": "Tiến trình con kết thúc nhưng không trả kết quả."}

    result["method"] = method
    return result


if __name__ == "__main__":
    print(run_with_timeout("sat_pairwise", 15, 30))
    print(run_with_timeout("cp_sat", 15, 30))
    print(run_with_timeout("gurobi", 15, 30))
    # Cố ý đặt giới hạn rất nhỏ để thấy TIMEOUT.
    print(run_with_timeout("sat_pairwise", 50, time_limit=0.05, grace=0))