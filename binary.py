from pysat.card import CardEnc, EncType


def encode_amo(variables, pool):
    """AMO bằng binary (bitwise) encoding, gọi qua PySAT.

    Mỗi biến được gán một mã nhị phân gồm ceil(log2 m) bit phụ; hai biến khác nhau
    luôn có mã khác nhau ở ít nhất một bit nên không thể cùng đúng.
    """
    if len(variables) <= 1:
        return []

    encoded = CardEnc.atmost(
        lits=variables,
        bound=1,
        encoding=EncType.bitwise,
        vpool=pool,
    )
    return encoded.clauses