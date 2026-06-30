from datetime import datetime, timedelta
from calendar import monthrange

from app.models.reservation import RecurrenceRule

MAX_OCCURRENCES = 365


def generate_occurrences(
    starts_at: datetime,
    ends_at: datetime,
    rule: RecurrenceRule,
    end_date: datetime,
) -> list[tuple[datetime, datetime]]:
    """
    Gera a lista de pares (starts_at, ends_at) para cada ocorrência
    da série recorrente, EXCLUINDO a primeira (que é a reserva original).

    Retorna lista vazia se rule == RecurrenceRule.NONE.
    Limita a MAX_OCCURRENCES para evitar loops infinitos.
    """
    if rule == RecurrenceRule.NONE:
        return []

    duration = ends_at - starts_at
    occurrences: list[tuple[datetime, datetime]] = []
    current_start = _next_occurrence(starts_at, rule)

    while current_start <= end_date and len(occurrences) < MAX_OCCURRENCES:
        current_end = current_start + duration
        occurrences.append((current_start, current_end))
        current_start = _next_occurrence(current_start, rule)

    return occurrences


def _next_occurrence(dt: datetime, rule: RecurrenceRule) -> datetime:
    """Avança a data para a próxima ocorrência conforme a regra."""
    if rule == RecurrenceRule.DAILY:
        return dt + timedelta(days=1)

    if rule == RecurrenceRule.WEEKLY:
        return dt + timedelta(weeks=1)

    if rule == RecurrenceRule.MONTHLY:
        # Avança um mês respeitando o número de dias do mês destino.
        # Ex: 31/jan → 28/fev (não 03/mar).
        month = dt.month + 1
        year = dt.year
        if month > 12:
            month = 1
            year += 1
        day = min(dt.day, monthrange(year, month)[1])
        return dt.replace(year=year, month=month, day=day)

    raise ValueError(f"Unknown recurrence rule: {rule}")
