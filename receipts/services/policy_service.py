from django.conf import settings
from datetime import datetime, timezone, timedelta
from receipts.exceptions import PolicyValidationError


class PolicyService:
    @staticmethod
    def evaluate(receipt) -> dict:
        try:
            result = {
                "status": "APPROVED",
                "rules": [],
            }

            if receipt.transaction_date:
                receipt_age_check = PolicyService._check_receipt_age(receipt.transaction_date)
                result["rules"].append(receipt_age_check)

                if not receipt_age_check["passed"]:
                    result["status"] = "REJECTED"

            return result

        except Exception as e:
            raise PolicyValidationError(f"Policy evaluation failed: {str(e)}")

    @staticmethod
    def _check_receipt_age(transaction_date) -> dict:
        max_age_days = settings.RECEIPT_MAX_AGE_DAYS
        days_old = (datetime.now(timezone.utc).date() - transaction_date).days

        if days_old > max_age_days:
            return {
                "code": "RECEIPT_TOO_OLD",
                "passed": False,
                "message": f"Receipt is older than {max_age_days} days ({days_old} days old).",
            }

        return {
            "code": "RECEIPT_AGE_OK",
            "passed": True,
            "message": f"Receipt age is within policy ({days_old} days old).",
        }
