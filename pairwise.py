from itertools import combinations


def encode_amo(variables, pool):
    """Trả về các clause: tối đa một biến trong variables được True."""
    clauses = []

    for a, b in combinations(variables, 2):
        clauses.append([-a, -b])

    return clauses