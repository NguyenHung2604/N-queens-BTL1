from itertools import combinations

def check_solution(queen_cells, n):
    if len(queen_cells) != n:
        return False

    if any(cell < 1 or cell > n * n for cell in queen_cells):
        return False

    positions = [
        ((cell - 1) // n, (cell - 1) % n)
        for cell in queen_cells
    ]

    for (r1, c1), (r2, c2) in combinations(positions, 2):
        if r1 == r2 or c1 == c2:
            return False

        if abs(r1 - r2) == abs(c1 - c2):
            return False

    return True
