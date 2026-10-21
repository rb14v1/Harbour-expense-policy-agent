from datetime import datetime, timedelta


MAX_RECEIPT_AGE_DAYS = 35


def validate_receipt_date(transaction_date: str) -> tuple[bool, str]:
    receipt_date = datetime.strptime(
        transaction_date,
        "%Y-%m-%d"
    )

    today = datetime.today()

    age = (today - receipt_date).days

    if age > MAX_RECEIPT_AGE_DAYS:
        return False, "Receipt is older than 35 days."

    if age < 0:
        return False, "Receipt date cannot be in the future."

    return True, "Receipt date is valid."