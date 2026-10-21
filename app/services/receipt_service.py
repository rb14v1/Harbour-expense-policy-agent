def process_receipt(file_path):

    # 1. OCR
    text = extract_text(file_path)

    # 2. Convert extracted text into Receipt
    receipt = parse_receipt(text)

    # 3. Validate policy
    policy_result = validate_receipt(receipt)

    # 4. Get previous receipts
    previous_receipts = get_previous_receipts()

    # 5. Compare
    duplicate_matches = compare_receipt(
        receipt,
        previous_receipts
    )

    return {
        "receipt": receipt,
        "policy": policy_result,
        "duplicates": duplicate_matches
    }