import csv
from datetime import datetime
from pathlib import Path

from runner import run_with_timeout

METHODS = ["sat_pairwise", "sat_sequential", "cp_sat", "gurobi"]

FIELDNAMES = [
    "n", "method", "run", "status",
    "build_time", "solve_time", "total_time", "valid",
    "encode_time", "load_time",
    "board_variables", "aux_variables", "total_variables", "clauses",
    "time_limit", "error",
]


def normalize(result, run, time_limit):
    row = dict(result)
    row["run"] = run
    row["time_limit"] = time_limit

    # SAT: build_time = tạo CNF + nạp vào solver,
    # để cùng ý nghĩa với build_time của CP-SAT và Gurobi.
    if row.get("encode_time") is not None and row.get("load_time") is not None:
        row["build_time"] = row["encode_time"] + row["load_time"]
    return row


def run_benchmark(sizes, repeats=3, time_limit=30):
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Mỗi lần chạy ghi vào một file mới, không ghi đè dữ liệu cũ.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"exploratory_{stamp}.csv"

    with output_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file, fieldnames=FIELDNAMES, extrasaction="ignore"
        )
        writer.writeheader()

        for n in sizes:
            for run in range(1, repeats + 1):
                # Xoay vòng thứ tự các solver giữa các lượt.
                shift = (run - 1) % len(METHODS)
                order = METHODS[shift:] + METHODS[:shift]

                for method in order:
                    print(f"N={n} | {method} | lượt {run}/{repeats}", flush=True)
                    result = run_with_timeout(method, n, time_limit=time_limit)
                    row = normalize(result, run, time_limit)

                    # Ghi và flush ngay sau mỗi lượt để không mất dữ liệu.
                    writer.writerow(row)
                    file.flush()
                    print(f"  -> {row['status']}", flush=True)

    print(f"\nĐã lưu kết quả tại: {output_file}")


if __name__ == "__main__":
    run_benchmark(sizes=[8, 15, 30, 44, 88, 120, 512], repeats=3, time_limit=30)