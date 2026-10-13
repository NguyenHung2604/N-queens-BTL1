import csv
from pathlib import Path

from main import solve_nqueens


def run_benchmark():
    # Thử quy trình với các kích thước vừa phải trước.
    sizes = [4, 8, 15, 30, 50]
    encodings = ["pairwise", "sequential"]
    repeats = 3

    # Lưu kết quả vào thư mục results cạnh file này.
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)

    output_file = results_dir / "sat_comparison.csv"

    fieldnames = [
        "n",
        "encoding",
        "run",
        "status",
        "board_variables",
        "aux_variables",
        "total_variables",
        "clauses",
        "encode_time",
        "load_time",
        "solve_time",
        "total_time",
        "valid",
    ]

    # "w": mỗi lần chạy chương trình sẽ ghi lại bảng kết quả.
    with output_file.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for n in sizes:
            for run in range(1, repeats + 1):
                # Đổi thứ tự hai encoding giữa các lượt.
                order = (
                    encodings
                    if run % 2 == 1
                    else encodings[::-1]
                )

                for encoding in order:
                    print(
                        f"\n--- N={n}, {encoding}, "
                        f"lượt {run}/{repeats} ---"
                    )

                    result = solve_nqueens(
                        n=n,
                        encoding=encoding,
                        show_board=False,
                    )

                    result["run"] = run
                    writer.writerow(result)

                    # Ghi ngay sau mỗi lượt chạy.
                    file.flush()

    print(f"\nĐã lưu kết quả tại: {output_file}")


if __name__ == "__main__":
    run_benchmark()