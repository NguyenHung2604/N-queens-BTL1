from docplex.cp.model import CpoModel
import time, csv

def solve_n_queens_cp(n, timeout=60):
    model = CpoModel(name="NQueen")
    queens = model.integer_var_list(n, 0, n-1, "Q")

    model.add(model.all_diff(queens))                          # cột
    model.add(model.all_diff(queens[i] + i for i in range(n))) # chéo xuôi
    model.add(model.all_diff(queens[i] - i for i in range(n))) # chéo ngược

    start = time.perf_counter()
    sol = model.solve(TimeLimit=timeout, LogVerbosity="Quiet")
    elapsed = time.perf_counter() - start

    if sol:
        board = [sol[queens[i]] for i in range(n)]
        return {"N": n, "solver": "CPLEX_CP",
                "status": str(sol.get_solve_status()),
                "time_seconds": elapsed, "valid": True, "board": board}
    return {"N": n, "solver": "CPLEX_CP",
            "status": "INFEASIBLE_OR_UNKNOWN",
            "time_seconds": elapsed, "valid": False, "board": []}

if __name__ == "__main__":
    rows = []
    for n in [8, 15, 30, 44]:
        for rep in range(3):
            r = solve_n_queens_cp(n)
            r["rep"] = rep
            rows.append(r)
            print(r)

    with open("results/cplex_cp_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)