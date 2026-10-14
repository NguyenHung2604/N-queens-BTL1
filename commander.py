from itertools import combinations


def encode_amo(variables, pool, group_size=3):
    """AMO bằng commander encoding (Klieber & Kwon), tự cài đặt.

    PySAT không có sẵn encoding này nên các mệnh đề được sinh trực tiếp.
    """
    variables = list(variables)
    if len(variables) <= 1:
        return []
    return _commander(variables, pool, group_size)


def _pairwise(variables):
    return [[-a, -b] for a, b in combinations(variables, 2)]


def _commander(variables, pool, group_size):
    # Nhóm nhỏ: dùng pairwise, không cần biến phụ.
    if len(variables) <= group_size + 1:
        return _pairwise(variables)

    clauses = []
    commanders = []

    for start in range(0, len(variables), group_size):
        group = variables[start:start + group_size]

        # Nhóm chỉ có một biến: chính biến đó làm commander.
        if len(group) == 1:
            commanders.append(group[0])
            continue

        commander = pool.id()  # biến phụ mới của nhóm
        clauses.extend(_pairwise(group))                 # trong nhóm: tối đa một
        clauses.extend([-x, commander] for x in group)   # x đúng -> commander đúng
        commanders.append(commander)

    # Giữa các nhóm: tối đa một commander đúng (đệ quy).
    clauses.extend(_commander(commanders, pool, group_size))
    return clauses