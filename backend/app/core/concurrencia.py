"""Cambios sin pisar los de otra persona (HU-08-003, RP-08-03).

El formulario envía, junto con los valores nuevos, los valores que leyó al abrirse. Solo se
guardan los campos que la persona cambió. Si otra persona cambió ese mismo campo mientras
tanto hay conflicto y no se guarda nada. Los cambios ajenos en otros campos se respetan
sin conflicto. El repositorio actualiza cada campo con un UPDATE condicional
(WHERE campo IS :leido), así que tampoco se pisan dos confirmaciones simultáneas.
"""
from datetime import date
from typing import Optional


def _normal(valor):
    return valor.isoformat() if isinstance(valor, date) else valor


def cambios_a_aplicar(actual: dict, nuevos: dict, leidos: Optional[dict]) -> tuple[list, list]:
    """Devuelve ([(campo, leido, nuevo)], [campos en conflicto]).

    Sin `leidos` (clientes anteriores) se toma como leído el valor actual: se guarda lo que
    difiera y solo hay conflicto si otra confirmación gana la carrera en el UPDATE."""
    leidos = {c: _normal(v) for c, v in (leidos or {c: actual[c] for c in nuevos}).items()}
    cambios = [(c, leidos[c], v) for c, v in nuevos.items() if leidos[c] != v and actual[c] != v]
    en_conflicto = [c for c, leido, _ in cambios if actual[c] != leido]
    return cambios, en_conflicto


def mensaje(campos: list, nombres: dict) -> str:
    lista = ", ".join(nombres.get(c, c) for c in campos)
    return (f"Otra persona cambió {lista} mientras editabas. Tu cambio no se guardó: "
            "revisa el valor vigente y vuelve a guardar si quieres aplicarlo")
