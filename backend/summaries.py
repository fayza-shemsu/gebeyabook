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


def debts_summary(db, vendor_id: int) -> list:
    """Return a list of {customer_name, total_owed} for everyone who currently owes this vendor money."""
    from models import Transaction as Tx
    rows = (
        db.query(Tx.customer_name, func.sum(Tx.amount))
        .filter(Tx.vendor_id == vendor_id)
        .filter(Tx.type == "debt")
        .filter(Tx.customer_name.isnot(None))
        .group_by(Tx.customer_name)
        .all()
    )
    return [{"customer_name": name, "total_owed": total} for name, total in rows]


def get_last_transaction(db, vendor_id: int):
    from models import Transaction as Tx
    return (
        db.query(Tx)
        .filter(Tx.vendor_id == vendor_id)
        .order_by(Tx.id.desc())
        .first()
    )


def daily_breakdown_last_7_days(db, vendor_id: int) -> list:
    """Return a list of {date, total_sales, total_expenses} for each of the last 7 days, oldest first."""
    from datetime import datetime, timedelta, timezone
    results = []
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        summary = daily_summary(db, vendor_id, day)
        results.append({
            "date": day.strftime("%Y-%m-%d"),
            "total_sales": summary["total_sales"],
            "total_expenses": summary["total_expenses"],
        })
    return results


    return results
