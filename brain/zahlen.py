"""Numbers in German notation for texts to Marvin: decimal comma, no trailing zeros."""


def zahl(value, digits=None):
    """`zahl(21.5)` gives "21,5"; with `digits` the value is rounded first."""
    if digits is not None:
        value = round(value, digits)
    return f"{value:g}".replace(".", ",")
