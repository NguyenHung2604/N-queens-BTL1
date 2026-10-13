from pysat.card import CardEnc, EncType


def encode_amo(variables, pool):
    """Trả về các clause AMO bằng sequential counter."""
    if len(variables) <= 1:
        return []

    encoded = CardEnc.atmost(
        lits=variables,
        bound=1,
        encoding=EncType.seqcounter,
        vpool=pool,
    )

    return encoded.clauses