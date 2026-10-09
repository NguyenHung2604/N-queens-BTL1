from itertools import combinations
from pysat.solvers import Glucose3 # type: ignore
N = 15

def var(r,c):
    """Index cua bien Sat o hang r, cot c"""
    return r*N + c + 1


for r in range(N):
    print([var(r,c) for c in range(N)])


# Điều kiện cho hàng đầu tiên
clauses = []
                               
# Điều kiện cho từng hàng, cột, đường chéo

def AMO(variables):
    for a, b in combinations(variables, 2):
        clauses.append([-a, -b])

# Exactly one
def AMO_and_ALO(variables): 
    clauses.append(variables) # ALO 1 v 2 v 3 v 4
    AMO(variables)

# Apply for all cols and rows

# Each row
for r in range(N):
    row = [var(r,c) for c in range(N)]
    AMO_and_ALO(row)

# Each column
for c in range(N):
    col = [var(r, c) for r in range(N)]
    AMO_and_ALO(col)

# Each diagonal: have the same r - c or r + c
diagonal_minus = {}
diagonal_plus = {}

for i in range(N):
    for c in range(N):
        key_minus = i - c
        key_plus = i + c

        if key_minus not in diagonal_minus:
            diagonal_minus[key_minus] = [] # tao them danh sach trong neu chua co

        if key_plus not in diagonal_plus:
            diagonal_plus[key_plus] = [] # tao them danh sach trong neu chua co

        diagonal_minus[key_minus].append(var(i, c))
        diagonal_plus[key_plus].append(var(i, c))

# ap dung at most one cho moi duong cheo (khong phai duong cheo nao cung co hau)

for d in diagonal_minus.values():
    AMO(d)

for d in diagonal_plus.values():
    AMO(d)


# thuc hanh solver va goi ban co

print("Số biến:", N * N)
print("Số clause:", len(clauses))

print("N =", N)
print("Số clause:", len(clauses))  # N=5: phải là 170
print("Có ràng buộc cấm ô 1 và 6:", [-1, -6] in clauses)

# Đưa toàn bộ các clause vào SAT solver.
with Glucose3(bootstrap_with=clauses) as solver:
    if solver.solve():
        model = solver.get_model()
        queen_cells = {x for x in model if x > 0}

        print("Model:", model)
        print("Các ô có hậu:", sorted(queen_cells))

        # Kiểm tra phép gán có thỏa mọi clause đã tạo không.
        true_literals = set(model)
        assert all(
            any(literal in true_literals for literal in clause)
            for clause in clauses
        ), "Phép gán không thỏa các clause!"

        for r in range(N):
            row_display = []

            for c in range(N):
                cell_id = var(r, c)
                row_display.append(
                    "Q" if cell_id in queen_cells else "."
                )

            print(" ".join(row_display))
    else:
        print("Bài toán không có nghiệm.")