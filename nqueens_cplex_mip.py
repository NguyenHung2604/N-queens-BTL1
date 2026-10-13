
import time
from docplex.mp.model import Model


def solve_n_queens(n: int, time_limit: int = 60):
    model = Model(name=f"NQueens_MIP_{n}")

    x = {
        (i, j): model.binary_var(name=f"x_{i}_{j}")
        for i in range(n)
        for j in range(n)
    }

    # Mỗi hàng có đúng một quân hậu
    for i in range(n):
        model.add_constraint(
            model.sum(x[i, j] for j in range(n)) == 1
        )

    # Mỗi cột có đúng một quân hậu
    for j in range(n):
        model.add_constraint(
            model.sum(x[i, j] for i in range(n)) == 1
        )

    # Mỗi đường chéo chính có nhiều nhất một quân hậu
    for d in range(-(n - 1), n):
        cells = [
            x[i, j]
            for i in range(n)
            for j in range(n)
            if i - j == d
        ]
        if len(cells) > 1:
            model.add_constraint(model.sum(cells) <= 1)

    # Mỗi đường chéo phụ có nhiều nhất một quân hậu
    for s in range(2 * n - 1):
        cells = [
            x[i, j]
            for i in range(n)
            for j in range(n)
            if i + j == s
        ]
        if len(cells) > 1:
            model.add_constraint(model.sum(cells) <= 1)

    # Chỉ cần tìm một nghiệm khả thi, không tối ưu hàm mục tiêu
    model.parameters.threads = 1
    model.parameters.timelimit = time_limit

    start = time.perf_counter()
    solution = model.solve(log_output=False)
    elapsed = time.perf_counter() - start

    status = model.solve_details.status

    if solution is None:
        print(f"N={n} | Status={status} | Time={elapsed:.6f}s")
        model.end()
        return {
            "n": n,
            "solver": "CPLEX_MIP",
            "status": status,
            "time_seconds": elapsed,
            "valid": False,
        }

    # Lấy chỉ số cột của quân hậu ở từng hàng
    board = [
        next(
            j for j in range(n)
            if x[i, j].solution_value > 0.5
        )
        for i in range(n)
    ]

    # Kiểm tra nghiệm độc lập
    valid = (
        len(set(board)) == n
        and len({board[i] - i for i in range(n)}) == n
        and len({board[i] + i for i in range(n)}) == n
    )

    print(f"N             : {n}")
    print(f"Solver        : CPLEX_MIP")
    print(f"Status        : {status}")
    print(f"Time (seconds): {elapsed:.6f}")
    print(f"Valid solution: {valid}")
    print(f"Board         : {board}")

    result = {
        "n": n,
        "solver": "CPLEX_MIP",
        "status": status,
        "time_seconds": elapsed,
        "valid": valid,
    }

    model.end()
    return result


if __name__ == "__main__":
    for n in [8, 15, 30, 44]:
        solve_n_queens(n)