from itertools import combinations
from math import ceil, sqrt


def encode_amo(variables, pool):
    """AMO bằng product encoding (Chen), tự cài đặt.

    PySAT không có sẵn encoding này nên các mệnh đề được sinh trực tiếp.
    Xếp m biến vào lưới p x q; mỗi hàng và mỗi cột có một biến phụ,
    rồi áp AMO (đệ quy) lên các biến hàng và các biến cột.
    """
    variables = list(variables)
    if len(variables) <= 1:
        return []
    return _product(variables, pool)


def _pairwise(variables):
    return [[-a, -b] for a, b in combinations(variables, 2)]


def _product(variables, pool):
    m = len(variables)

    # Nhóm nhỏ: dùng pairwise.
    if m <= 4:
        return _pairwise(variables)

    p = ceil(sqrt(m))      # số hàng tối đa
    q = ceil(m / p)        # số cột
    num_rows = ceil(m / q) # số hàng thực sự có biến

    rows = [pool.id() for _ in range(num_rows)]
    cols = [pool.id() for _ in range(q)]

    clauses = []
    for k, x in enumerate(variables):
        i, j = divmod(k, q)          # vị trí của biến trong lưới
        clauses.append([-x, rows[i]])  # x đúng -> biến hàng i đúng
        clauses.append([-x, cols[j]])  # x đúng -> biến cột j đúng

    clauses.extend(_product(rows, pool))
    clauses.extend(_product(cols, pool))
    return clauses