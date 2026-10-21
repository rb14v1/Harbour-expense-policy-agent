def compare_receipt(
    new_receipt,
    previous_receipts
):
    matches = []

    for receipt in previous_receipts:

        if (
            new_receipt.merchant_name
            == receipt.merchant_name
            and
            new_receipt.total_amount
            == receipt.total_amount
            and
            new_receipt.transaction_date
            == receipt.transaction_date
        ):
            matches.append(receipt)

    return matches