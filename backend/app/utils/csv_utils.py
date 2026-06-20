"""Utilidades para generación de CSV seguro (C-08).

Incluye escapado de fórmulas para prevenir CSV injection.
"""


def escape_csv(value: str) -> str:
    """Escapa celdas CSV que empiecen con caracteres de fórmula (=, +, -, @)."""
    if value and value[0] in ("=", "+", "-", "@"):
        return f"'{value}"
    return value
