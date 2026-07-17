from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from models import Transaction


def daily_summary(db, vendor_id: int, date: datetime = None) -> dict:
    """Return total sales, total expenses, and net profit for a given day (defaults to today, UTC)."""
    if date is None:
        date = datetime.now(timezone.utc)

    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    return _summarize_range(db, vendor_id, start, end)


def weekly_summary(db, vendor_id: int) -> dict:
    """Return total sales, total expenses, and net profit for the last 7 days."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)

    return _summarize_range(db, vendor_id, start, end)


def _summarize_range(db, vendor_id: int, start: datetime, end: datetime) -> dict:
    rows = (
        db.query(Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.vendor_id == vendor_id)
        .filter(Transaction.created_at >= start)
        .filter(Transaction.created_at < end)
        .group_by(Transaction.type)
        .all()
    )

    totals = {"sale": 0, "expense": 0, "debt": 0}
    for tx_type, total in rows:
        totals[tx_type] = total or 0

    net_profit = totals["sale"] - totals["expense"]

    return {
        "total_sales": totals["sale"],
        "total_expenses": totals["expense"],
        "total_debt": totals["debt"],
        "net_profit": net_profit,
    }
