import argparse
import csv
import json
import os
import platform
import sys
import time
from datetime import datetime
from importlib import metadata
from pathlib import Path

from runner import ALL_METHODS, run_with_timeout

FIELDNAMES = [
    "n", "method", "run", "status",
    "build_time", "solve_time", "total_time", "valid",
    "encode_time", "load_time",
    "board_variables", "aux_variables", "total_variables", "clauses",
    "time_limit", "wall_time", "error",
]

# Thất bại "cứng": giới hạn license hoặc RAM, không thể khá hơn khi N tăng
# -> method đó dừng hẳn từ N này.
PERMANENT_FAILURES = {"LICENSE_ERROR", "SKIPPED_MEMORY"}

# Thất bại "mềm": hết giờ hoặc lỗi. Thời gian giải SAT có thể không tăng đều theo N,
# nên chỉ dừng method sau vài kích thước thất bại liên tiếp (xem --max-failed-sizes).
SOFT_FAILURES = {"TIMEOUT", "ERROR", "UNKNOWN"}

DEFAULT_SIZES = [8, 15, 30, 44, 64, 88, 120, 180, 256, 384, 512]


def package_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "không cài"


def collect_environment():
    ram_gb = None
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / 1024**3, 1)
    except ImportError:
        pass  # cài thêm bằng: python -m pip install psutil

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "ram_gb": ram_gb,
        "packages": {
            name: package_version(name)
            for name in ["python-sat", "ortools", "gurobipy", "cplex", "docplex"]
        },
    }


def normalize(result, run, time_limit, wall_time):
    row = dict(result)
    row["run"] = run
    row["time_limit"] = time_limit
    row["wall_time"] = wall_time

    # SAT: build_time = tạo CNF + nạp vào solver,
    # để cùng ý nghĩa với build_time của các solver khác.
    if row.get("encode_time") is not None and row.get("load_time") is not None:
        row["build_time"] = row["encode_time"] + row["load_time"]

    if (row.get("total_time") is None
            and row.get("build_time") is not None
            and row.get("solve_time") is not None):
        row["total_time"] = row["build_time"] + row["solve_time"]

    row["error"] = str(row.get("error", ""))[:300].replace("\n", " ")
    return row


def run_benchmark(sizes, methods, repeats, time_limit, max_failed_sizes, tag):
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Mỗi lần chạy ghi vào một file mới, không ghi đè dữ liệu cũ.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{tag}_{stamp}" if tag else stamp
    output_file = results_dir / f"full_{name}.csv"
    env_file = results_dir / f"environment_{name}.json"

    settings = {
        "sizes": sizes, "methods": methods, "repeats": repeats,
        "time_limit": time_limit, "max_failed_sizes": max_failed_sizes,
        "started": datetime.now().isoformat(timespec="seconds"),
    }
    env_file.write_text(
        json.dumps({"settings": settings, "environment": collect_environment()},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Kết quả:  {output_file}\nMôi trường: {env_file}\n", flush=True)

    dead = {}         # method -> lý do dừng hẳn
    consecutive = {}  # method -> số kích thước thất bại mềm liên tiếp

    def write_not_run(writer, file, n, method, run, reason):
        writer.writerow({
            "n": n, "method": method, "run": run, "status": "NOT_RUN",
            "time_limit": time_limit, "error": reason,
        })
        file.flush()

    with output_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()

        for n in sizes:
            soft_failed = {}  # method -> trạng thái thất bại mềm ở N này

            for run in range(1, repeats + 1):
                # Xoay vòng thứ tự các method giữa các lượt.
                shift = (run - 1) % len(methods)
                order = methods[shift:] + methods[:shift]

                for method in order:
                    if method in dead:
                        write_not_run(writer, file, n, method, run, dead[method])
                        continue
                    if method in soft_failed:
                        write_not_run(
                            writer, file, n, method, run,
                            f"Bỏ qua: {method} đã {soft_failed[method]} ở lượt trước của N={n}.",
                        )
                        continue

                    print(f"N={n} | {method} | lượt {run}/{repeats}", flush=True)
                    start = time.perf_counter()
                    result = run_with_timeout(method, n, time_limit=time_limit)
                    wall_time = time.perf_counter() - start

                    row = normalize(result, run, time_limit, wall_time)

                    # Ghi và flush ngay sau mỗi lượt để không mất dữ liệu.
                    writer.writerow(row)
                    file.flush()
                    print(f"  -> {row['status']}  (tổng {row.get('total_time')})",
                          flush=True)

                    if row["status"] in PERMANENT_FAILURES:
                        dead[method] = f"Bỏ qua: {method} đã {row['status']} ở N={n}."
                    elif row["status"] in SOFT_FAILURES:
                        soft_failed[method] = row["status"]

            # Cập nhật bộ đếm thất bại liên tiếp sau khi xong kích thước N.
            if max_failed_sizes > 0:
                for method in methods:
                    if method in dead:
                        continue
                    if method in soft_failed:
                        consecutive[method] = consecutive.get(method, 0) + 1
                        if consecutive[method] >= max_failed_sizes:
                            dead[method] = (
                                f"Bỏ qua: {method} thất bại {consecutive[method]} "
                                f"kích thước liên tiếp (đến N={n})."
                            )
                    else:
                        consecutive[method] = 0

    print(f"\nĐã lưu kết quả tại: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark N-Queens: SAT, CP, ILP.")
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES,
                        help="Danh sách N (nên tăng dần).")
    parser.add_argument("--methods", nargs="+", default=ALL_METHODS,
                        choices=ALL_METHODS, help="Các method cần chạy.")
    parser.add_argument("--repeats", type=int, default=3, help="Số lượt mỗi cấu hình.")
    parser.add_argument("--time-limit", type=float, default=60,
                        help="Giới hạn thời gian (giây) mỗi lượt.")
    parser.add_argument("--max-failed-sizes", type=int, default=2,
                        help="Dừng một method sau chừng ấy kích thước thất bại liên tiếp "
                             "(TIMEOUT/ERROR/UNKNOWN). Đặt 0 để không bao giờ dừng.")
    parser.add_argument("--tag", default="", help="Nhãn thêm vào tên file kết quả.")
    args = parser.parse_args()

    run_benchmark(
        sizes=sorted(args.sizes),
        methods=list(args.methods),
        repeats=args.repeats,
        time_limit=args.time_limit,
        max_failed_sizes=args.max_failed_sizes,
        tag=args.tag,
    )


if __name__ == "__main__":
    main()