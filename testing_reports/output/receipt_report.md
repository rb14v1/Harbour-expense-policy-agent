============================================================
EXPENSE POLICY AGENT - RECEIPT TEST REPORT
============================================================

Report Generated: 2026-10-01 14:04:43

## 1. EXECUTIVE SUMMARY

- **Total receipts:** 68
- **Approved by Finance:** 4
- **Rejected by Finance:** 13
- **Pending Finance review:** 20
- **Approved by Policy:** 27
- **Rejected by Policy:** 10
- **Duplicate receipts:** 16
- **Processing failures:** 14

## 2. RECEIPT-BY-RECEIPT DETAILS

------------------------------------------------------------
Receipt #1
------------------------------------------------------------

**Receipt ID:** a6d0dc41-6f55-4ef4-aafc-d44209352256
**Filename:** Conference Expense Receipt.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 08:11:37
**SHA-256 Hash:** 2b02ce7522be66e2fe099c40a25d3d1e23d2bce27833f6965874f105d2de5096

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** TechCon Events Group LLC
**Transaction Date:** 2026-10-01
**Amount:** 949.38 USD
**Currency:** USD
**Payment Method:** N/A
**Invoice Number:** TechCon

### CLASSIFICATION
**Category:** Training
**Category Confidence:** 85.0%
**Category Reason:** Matched 'workshop' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (0 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-10-01 08:11:46

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #2
------------------------------------------------------------

**Receipt ID:** 3a9a6b96-8c34-487d-ab8f-2cfac2babe88
**Filename:** EXPENSE POLICY AGENT — CORRECT DEMONSTRATION REPORT.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 06:43:11
**SHA-256 Hash:** 8ddee4b12fa2647e9846cc5f28095a94abbe6b2c299a7c753ea5095d777e5a9f

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** c939d34c-c17d-4d10-9937-66de349bd74f
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-10-01 06:43:11

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #3
------------------------------------------------------------

**Receipt ID:** 604abf65-f3f0-4697-bc52-0063cc4d2a14
**Filename:** Invoice_20252405_1205.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 06:39:06
**SHA-256 Hash:** 650a1c68bfb7b2c270db498434888d4ce6ed5a33a877b5c9de6839971bb99047

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-10-01 06:39:19

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #4
------------------------------------------------------------

**Receipt ID:** c939d34c-c17d-4d10-9937-66de349bd74f
**Filename:** EXPENSE POLICY AGENT — CORRECT DEMONSTRATION REPORT.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 06:38:18
**SHA-256 Hash:** 8ddee4b12fa2647e9846cc5f28095a94abbe6b2c299a7c753ea5095d777e5a9f

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** coffee"
**Transaction Date:** 2026-09-05
**Amount:** 5.50 USD
**Currency:** USD
**Payment Method:** N/A
**Invoice Number:** management

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (26 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-10-01 06:39:27

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #5
------------------------------------------------------------

**Receipt ID:** b573ba92-7b1d-4fb9-bb51-9841b50b2127
**Filename:** Invoice_20252405_1205.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 06:36:25
**SHA-256 Hash:** 650a1c68bfb7b2c270db498434888d4ce6ed5a33a877b5c9de6839971bb99047

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-10-01 06:36:33

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #6
------------------------------------------------------------

**Receipt ID:** 1bcb186a-8179-4e9d-8c73-c4ce5b86f55c
**Filename:** Screenshot 2026-10-01 105335.png
**Owner:** default-user
**Upload Date:** 2026-10-01 05:24:20
**SHA-256 Hash:** dd7dcd703ce0718730ef9a60b89c62ea59801d645ae078e6edc3d059b75bd786

### PROCESSING
**Status:** SEMANTIC_DUPLICATE
**Processing Message:** This receipt appears to duplicate a previously uploaded receipt.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-01
**Amount:** 56.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Matched 'uber' in merchant name

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Semantic duplicate
**Semantic Duplicate Of:** 27c551b1-49ab-4e15-92b4-4eeb1025d08d
**Duplicate Score:** 95
**Duplicate Reason:** Matched with receipt 27c551b1-49ab-4e15-92b4-4eeb1025d08d (score: 95)

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-10-01 05:24:29

### FINAL RESULT
**Final Receipt Status:** SEMANTIC_DUPLICATE
**Final Explanation:** This receipt appears to duplicate a previously uploaded receipt.

------------------------------------------------------------
Receipt #7
------------------------------------------------------------

**Receipt ID:** 13411d49-0432-4904-a238-ea5150dfbe14
**Filename:** Receipt_01Sep2026_084654.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 05:23:12
**SHA-256 Hash:** d606ee07dbbfb589e013d5a636a617b8326a575db535394e8177eaf5fa2f6190

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** 27c551b1-49ab-4e15-92b4-4eeb1025d08d
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-10-01 05:23:12

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #8
------------------------------------------------------------

**Receipt ID:** 27c551b1-49ab-4e15-92b4-4eeb1025d08d
**Filename:** Receipt_01Sep2026_084654.pdf
**Owner:** default-user
**Upload Date:** 2026-10-01 05:22:30
**SHA-256 Hash:** d606ee07dbbfb589e013d5a636a617b8326a575db535394e8177eaf5fa2f6190

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-01
**Amount:** 56.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Matched 'uber' in merchant name

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (30 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-10-01 05:22:45

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #9
------------------------------------------------------------

**Receipt ID:** 6d4c6627-f138-4e74-ae21-b3e49810f705
**Filename:** cab.png
**Owner:** default-user
**Upload Date:** 2026-09-30 17:21:40
**SHA-256 Hash:** a8c15766c2493f4574aab2f4923abeb53e3562d73a52a9f5f15a6a56a90c97a6

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-08-29
**Amount:** 59.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Matched 'uber' in merchant name

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (32 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-30 17:21:49

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #10
------------------------------------------------------------

**Receipt ID:** 9ef07791-34e2-41e3-9762-1df5aacf6478
**Filename:** CRN11305964499.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 15:55:10
**SHA-256 Hash:** 2c40ff0c84c2c8d4224ffe6488d0d002273267e51d8b32a444eb3d6282238f9f

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** ANI Technologies Private Limited,
**Transaction Date:** 2026-09-11
**Amount:** 103.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** OLA

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (19 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-30 15:55:44

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #11
------------------------------------------------------------

**Receipt ID:** b7a4b5f9-7ad7-42c5-8d56-619c23aa61d8
**Filename:** Gemini_Generated_Image_omjh6lomjh6lomjh.png
**Owner:** default-user
**Upload Date:** 2026-09-30 11:21:02
**SHA-256 Hash:** b7693d25270ecaa90844ae24a9f5250661080758e278d7c8cee7c7e347722608

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 11:21:18

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #12
------------------------------------------------------------

**Receipt ID:** f3cb53ce-1f8e-42df-805f-372193e9e11c
**Filename:** Gemini_Generated_Image_omjh6lomjh6lomjh.png
**Owner:** default-user
**Upload Date:** 2026-09-30 11:18:40
**SHA-256 Hash:** b7693d25270ecaa90844ae24a9f5250661080758e278d7c8cee7c7e347722608

### PROCESSING
**Status:** FAILED
**Processing Message:** We couldn't read the receipt. The document may be blurry, unclear, or contain unreadable content. Please upload a clearer image or PDF.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document extraction failed: Failed to analyze receipt: (<HTTPSConnection(host='prompt.cognitiveservices.azure.com', port=443) at 0x1e915af56d0>, 'Connection to prompt.cognitiveservices.azure.com timed out. (connect timeout=300)')

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 11:20:24

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** We couldn't read the receipt. The document may be blurry, unclear, or contain unreadable content. Please upload a clearer image or PDF.

------------------------------------------------------------
Receipt #13
------------------------------------------------------------

**Receipt ID:** f46c1ea5-5c94-40fb-8add-0bef1d5f988e
**Filename:** ChatGPT Image Sep 20, 2026, 10_26_02 PM.png
**Owner:** default-user
**Upload Date:** 2026-09-30 11:14:21
**SHA-256 Hash:** a2d1f714595759c0fee027d77aecc560cebd0e16094f20beb41729179a125f16

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** WHOLE FOODS
**Transaction Date:** 2026-09-20
**Amount:** 103.53 USD
**Currency:** USD
**Payment Method:** CARD
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (10 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-30 11:16:56

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #14
------------------------------------------------------------

**Receipt ID:** 5d0c9875-0ce1-4bdd-a614-4348fb0f9bc8
**Filename:** Electronic Ticket Receipt 12NOV For JOMEL C GARCIA _ PDF _ Airlines____.png
**Owner:** default-user
**Upload Date:** 2026-09-30 11:11:45
**SHA-256 Hash:** 11376df9ba83ed6f9bf14ebb5665b42ca7c15d15716507c32cfd3af88956ae88

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (2539 days old).

### EXTRACTED INFORMATION
**Vendor:** Philippine Airlines
**Transaction Date:** 2019-10-18
**Amount:** 4497.00 PHP
**Currency:** PHP
**Payment Method:** CASH
**Invoice Number:** At

### CLASSIFICATION
**Category:** Prepaid Flights
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (2539 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 11:12:43

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (2539 days old).

------------------------------------------------------------
Receipt #15
------------------------------------------------------------

**Receipt ID:** f23f3590-b1f9-40a0-85de-d1c944d6735d
**Filename:** WhatsApp Image 2026-09-25 at 1.39.54 PM (1).jpeg
**Owner:** default-user
**Upload Date:** 2026-09-30 10:57:50
**SHA-256 Hash:** 40147e7ad377dff49300dd4342d5a607b302b01f58109bda5056ec15743f43b4

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 10:57:58

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #16
------------------------------------------------------------

**Receipt ID:** ef2ccec1-2774-43ef-a6c1-6b389eed75d6
**Filename:** 7sepimg.png
**Owner:** default-user
**Upload Date:** 2026-09-30 10:44:10
**SHA-256 Hash:** 914fe02b0d3770b789caf160a5214cf0a48c987c615995ceee04e7ce029d3ff6

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** f7828812-011f-4983-876c-d6ccc88493b8
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 10:44:10

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #17
------------------------------------------------------------

**Receipt ID:** 69f3a045-abb9-49fc-8604-b3892d26d7d5
**Filename:** WhatsApp Image 2026-09-29 at 11.02.25 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-30 10:34:05
**SHA-256 Hash:** 0abb2ac2ce020bf2e59fffb00e8b7fdf76474beee766e4dbeb8edc77c017643f

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** 5e29035a-90b8-4b5f-8b4e-f88bc77fdb4b
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 10:34:06

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #18
------------------------------------------------------------

**Receipt ID:** 5e29035a-90b8-4b5f-8b4e-f88bc77fdb4b
**Filename:** WhatsApp Image 2026-09-29 at 11.02.25 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-30 10:32:54
**SHA-256 Hash:** 0abb2ac2ce020bf2e59fffb00e8b7fdf76474beee766e4dbeb8edc77c017643f

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (50 days old).

### EXTRACTED INFORMATION
**Vendor:** ANI Technologies Private Limited,
**Transaction Date:** 2026-08-11
**Amount:** 74.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (50 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 10:33:22

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (50 days old).

------------------------------------------------------------
Receipt #19
------------------------------------------------------------

**Receipt ID:** d6a55250-a698-4e72-9cd4-b089ff9ca496
**Filename:** WhatsApp Image 2026-09-29 at 11.00.55 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-30 10:32:05
**SHA-256 Hash:** 6b01ff8b10a92768fc54d569985673fe8cf8aecf7a9bff4834c0bdf0433af214

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 10:32:18

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #20
------------------------------------------------------------

**Receipt ID:** 7d407423-0474-482e-824d-c666efd5b6a0
**Filename:** R005_Food__Breakfast_or_Lunch.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 10:30:33
**SHA-256 Hash:** e70e57d8f6f598ef0b7cbbb9843b22461db1170afdadd0e676806dfccfe3ce68

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (56 days old).

### EXTRACTED INFORMATION
**Vendor:** Green Spoon Café
**Transaction Date:** 2026-08-05
**Amount:** 682.50 USD
**Currency:** USD
**Payment Method:** Corporate Card | Card ending: **** 4821
**Invoice Number:** Pune

### CLASSIFICATION
**Category:** Food: Breakfast or Lunch - Max Claim: €/$/AUD 15 / INR700
**Category Confidence:** 80.0%
**Category Reason:** Matched 'lunch' in receipt details

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (56 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 10:30:40

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (56 days old).

------------------------------------------------------------
Receipt #21
------------------------------------------------------------

**Receipt ID:** bbfd6a71-7716-4f5c-a163-73bce2f40a0e
**Filename:** receiptt.jpg
**Owner:** default-user
**Upload Date:** 2026-09-30 07:00:11
**SHA-256 Hash:** da1994a5e72f863563a0c38b0b21899d6a0c7be2667fd0c1d56ff6e1a237222b

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded receipt appears to be blank. Please upload a receipt with visible content.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Receipt appears to be blank. No meaningful content was extracted.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 07:00:19

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded receipt appears to be blank. Please upload a receipt with visible content.

------------------------------------------------------------
Receipt #22
------------------------------------------------------------

**Receipt ID:** 8187258e-158c-4263-820a-6ca79efc5a6c
**Filename:** blur.png
**Owner:** default-user
**Upload Date:** 2026-09-30 06:46:53
**SHA-256 Hash:** c10b42fbc4a53672a91f305e7f4e91b7522e107e0110ee6938091d2d6b0147bc

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 06:47:06

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #23
------------------------------------------------------------

**Receipt ID:** 7587f277-58ba-4d46-b836-6919231249fb
**Filename:** Receipt_23Aug2026_210640.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 06:44:54
**SHA-256 Hash:** 89dfab81168f1fdab403acd3af0d1f450a6bd17671af10b261c4ac94ec1e2557

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (38 days old).

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-08-23
**Amount:** 4.93 USD
**Currency:** USD
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Matched 'uber' in merchant name

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (38 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 06:45:09

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (38 days old).

------------------------------------------------------------
Receipt #24
------------------------------------------------------------

**Receipt ID:** f3be344e-d1fa-4698-87f0-c518ba491724
**Filename:** old_uber_receipt.pdf
**Owner:** test-user
**Upload Date:** 2026-09-30 06:25:51
**SHA-256 Hash:** test_hash_123

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (53 days old).

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-08-08
**Amount:** 156.05 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Matched 'uber' in merchant name

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (53 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 06:25:51

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (53 days old).

------------------------------------------------------------
Receipt #25
------------------------------------------------------------

**Receipt ID:** 08a7b7ba-75b2-4d2a-a2fe-efbbe7c31ff6
**Filename:** aug8.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 06:17:41
**SHA-256 Hash:** 2237c5d3c79b76db05c4f022155db3366db3a87f7c09ca7f9bfa81f553c1b550

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (53 days old).

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-08-08
**Amount:** 156.05 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Matched 'uber' in merchant name

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (53 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 06:17:56

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (53 days old).

------------------------------------------------------------
Receipt #26
------------------------------------------------------------

**Receipt ID:** da9712e5-95ff-4983-82e8-c05b88f466c4
**Filename:** Invoice_20252405_1205.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 06:13:19
**SHA-256 Hash:** 650a1c68bfb7b2c270db498434888d4ce6ed5a33a877b5c9de6839971bb99047

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 06:13:38

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #27
------------------------------------------------------------

**Receipt ID:** b16cb97d-3cc8-4355-a3b7-ccbcf4595506
**Filename:** RECEIPT_RD17898016429158037.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 06:11:10
**SHA-256 Hash:** 7c677e3e138b5794552cf81398e62665a5ed8480d07377d8594aaf64f0aa5f47

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-19
**Amount:** 142.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (11 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-30 06:11:31

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #28
------------------------------------------------------------

**Receipt ID:** dcdaba6e-c0e8-4906-a4c4-3cf7ca290b6f
**Filename:** Receipt_18Mar2026.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 05:03:20
**SHA-256 Hash:** 918f849f0d43dbc68708ec4ac7f882884ac29c9545c054c6c97a50ce028932d1

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (196 days old).

### EXTRACTED INFORMATION
**Vendor:** Bengaluru
**Transaction Date:** 2026-03-18
**Amount:** 243.20 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Prepaid Flights
**Category Confidence:** 85.0%
**Category Reason:** Matched keyword 'booking' in receipt details

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (196 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 05:03:57

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (196 days old).

------------------------------------------------------------
Receipt #29
------------------------------------------------------------

**Receipt ID:** f7828812-011f-4983-876c-d6ccc88493b8
**Filename:** 7sepimg.png
**Owner:** default-user
**Upload Date:** 2026-09-30 05:02:16
**SHA-256 Hash:** 914fe02b0d3770b789caf160a5214cf0a48c987c615995ceee04e7ce029d3ff6

### PROCESSING
**Status:** SEMANTIC_DUPLICATE
**Processing Message:** This receipt appears to duplicate a previously uploaded receipt.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-07
**Amount:** 60.50 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Semantic duplicate
**Semantic Duplicate Of:** c2a01a6c-2f4f-4ba7-8e9b-9d18a74bf236
**Duplicate Score:** 95
**Duplicate Reason:** Matched with receipt c2a01a6c-2f4f-4ba7-8e9b-9d18a74bf236 (score: 95)

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 05:03:02

### FINAL RESULT
**Final Receipt Status:** SEMANTIC_DUPLICATE
**Final Explanation:** This receipt appears to duplicate a previously uploaded receipt.

------------------------------------------------------------
Receipt #30
------------------------------------------------------------

**Receipt ID:** 05299d0b-a306-4258-9f0a-7c64a7ef50fc
**Filename:** Receipt_07Sep2026.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 05:01:59
**SHA-256 Hash:** af11e6f761cefb7464dcc4ff090b33da73a6b5a05e6f46e93ea72670fcb1b2f9

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** c2a01a6c-2f4f-4ba7-8e9b-9d18a74bf236
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-30 05:02:00

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #31
------------------------------------------------------------

**Receipt ID:** c2a01a6c-2f4f-4ba7-8e9b-9d18a74bf236
**Filename:** Receipt_07Sep2026.pdf
**Owner:** default-user
**Upload Date:** 2026-09-30 05:00:21
**SHA-256 Hash:** af11e6f761cefb7464dcc4ff090b33da73a6b5a05e6f46e93ea72670fcb1b2f9

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-07
**Amount:** 60.50 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (23 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-30 05:00:57

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #32
------------------------------------------------------------

**Receipt ID:** c2b09c73-1e98-45e1-964a-0e8804d936e8
**Filename:** 1.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-29 18:55:50
**SHA-256 Hash:** 5f2d7bbe6e2c84af632b64572f93c0a2807b0aa595cb643421cfd197e32dc569

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** 14383b12-e1ae-45a1-ba28-77ada62efa40
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 18:55:50

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #33
------------------------------------------------------------

**Receipt ID:** 14383b12-e1ae-45a1-ba28-77ada62efa40
**Filename:** WhatsApp Image 2026-09-29 at 11.00.42 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-29 18:31:40
**SHA-256 Hash:** 5f2d7bbe6e2c84af632b64572f93c0a2807b0aa595cb643421cfd197e32dc569

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Auto
**Transaction Date:** 2026-09-25
**Amount:** 54.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** via

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (4 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-29 18:32:26

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #34
------------------------------------------------------------

**Receipt ID:** 89a77613-510e-4264-9d1b-a7bd2f7ec7f8
**Filename:** 15mb (1).pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 18:08:32
**SHA-256 Hash:** e8bd8d2dcf71cc04e5eebff315258c531b03e385e934757b047766dd3784d20a

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 18:17:27

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #35
------------------------------------------------------------

**Receipt ID:** 4f619c4a-dd95-45c2-9164-1b87a513a2d6
**Filename:** receipt.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 16:07:22
**SHA-256 Hash:** 2b7e1f810f0fd915836b00eaf3314aa4083db2ee3194b40e2c516d2af5a92e3b

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Apex Tech Solutions
**Transaction Date:** 2026-09-29
**Amount:** 246.30 USD
**Currency:** USD
**Payment Method:** CARD
**Invoice Number:** 100

### CLASSIFICATION
**Category:** Software
**Category Confidence:** 85.0%
**Category Reason:** Matched keyword 'cloud' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (0 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-29 16:07:31

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #36
------------------------------------------------------------

**Receipt ID:** 7ab9fd65-ee23-4f5a-82ee-9e2c85d38054
**Filename:** trial.png
**Owner:** default-user
**Upload Date:** 2026-09-29 15:52:15
**SHA-256 Hash:** e553a5df6646b7ebde4b5008a837b13c35be0cffe1639774f48844b46db2c199

### PROCESSING
**Status:** SEMANTIC_DUPLICATE
**Processing Message:** This receipt appears to duplicate a previously uploaded receipt.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-24
**Amount:** 111.01 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Semantic duplicate
**Semantic Duplicate Of:** 55513ea0-aca3-4da7-9a34-9d97d844b3e1
**Duplicate Score:** 95
**Duplicate Reason:** Matched with receipt 55513ea0-aca3-4da7-9a34-9d97d844b3e1 (score: 95)

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:52:24

### FINAL RESULT
**Final Receipt Status:** SEMANTIC_DUPLICATE
**Final Explanation:** This receipt appears to duplicate a previously uploaded receipt.

------------------------------------------------------------
Receipt #37
------------------------------------------------------------

**Receipt ID:** 55513ea0-aca3-4da7-9a34-9d97d844b3e1
**Filename:** Receipt_24Sep2026_190439.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:37:07
**SHA-256 Hash:** 71ebd442577c573d25f9a262e0fbef3502962f0269abfdc08c969b2a053f5fb4

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-24
**Amount:** 111.01 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (5 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-29 15:37:24

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #38
------------------------------------------------------------

**Receipt ID:** b848ef44-4d97-4267-a006-127ef19e95b6
**Filename:** RECEIPT_RD17906582084065857.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:34:48
**SHA-256 Hash:** 05bec11a114d146b24526394ce38b8fe2568551fbea8cc20576e41c3e27cb46b

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-29
**Amount:** 50.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (0 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-29 15:35:24

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #39
------------------------------------------------------------

**Receipt ID:** c3d521fa-5882-4668-ae94-c6a3c4b9317c
**Filename:** Invoice_20252405_1205.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:34:39
**SHA-256 Hash:** 650a1c68bfb7b2c270db498434888d4ce6ed5a33a877b5c9de6839971bb99047

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:34:48

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #40
------------------------------------------------------------

**Receipt ID:** 46f733e8-d292-49e7-9494-f2b64972057e
**Filename:** olddeadline.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:33:10
**SHA-256 Hash:** a7e0b44539f72fdf3707843d2b8d6c23b1faab97ed92c0fd439f4c9538158e92

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (38 days old).

### EXTRACTED INFORMATION
**Vendor:** KANAKAPURA
**Transaction Date:** 2026-08-22
**Amount:** 154.81 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Prepaid Flights
**Category Confidence:** 85.0%
**Category Reason:** Matched keyword 'booking' in receipt details

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (38 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:33:27

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (38 days old).

------------------------------------------------------------
Receipt #41
------------------------------------------------------------

**Receipt ID:** e9a11b8a-bd91-4414-9a50-6bb25b8bfdcf
**Filename:** Receipt_05Sep2026_213603.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:32:18
**SHA-256 Hash:** d30c8cf8d693b3d05ffc8c94ad8a774cb8659ebf8ac5ce62c6a9a20519991c69

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** 3ace154c-af47-431c-b0af-fab63ee1c1f9
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:32:18

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #42
------------------------------------------------------------

**Receipt ID:** 3ace154c-af47-431c-b0af-fab63ee1c1f9
**Filename:** Receipt_05Sep2026_213603.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:09:47
**SHA-256 Hash:** d30c8cf8d693b3d05ffc8c94ad8a774cb8659ebf8ac5ce62c6a9a20519991c69

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (143 days old).

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-05-09
**Amount:** 90.23 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (143 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:10:04

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (143 days old).

------------------------------------------------------------
Receipt #43
------------------------------------------------------------

**Receipt ID:** 816da791-69d4-4985-b037-b7db7861b54e
**Filename:** Receipt_05Sep2026_200331.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:06:23
**SHA-256 Hash:** c8adc120d5cbd35cc4af6185e9037507ee0cbeb74979c276a9d28fca26241436

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt rejected because: Receipt is older than 35 days (143 days old).

### EXTRACTED INFORMATION
**Vendor:** MAHADEVPURA
**Transaction Date:** 2026-05-09
**Amount:** 90.74 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** REJECTED
**Policy Result:** {
  "status": "REJECTED",
  "rules": [
    {
      "code": "RECEIPT_TOO_OLD",
      "passed": false,
      "message": "Receipt is older than 35 days (143 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:07:15

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt rejected because: Receipt is older than 35 days (143 days old).

------------------------------------------------------------
Receipt #44
------------------------------------------------------------

**Receipt ID:** 7540b658-6c2b-4544-b8cf-d11af6cad9c4
**Filename:** RECEIPT_RD17903996379390687.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:06:13
**SHA-256 Hash:** 40858ae50ca63817841953e41e2cb947cc1a6244ef8944b311dd11786e76c3d3

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-26
**Amount:** 43.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (3 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Rejected
**Finance Updated:** 2026-10-01 04:47:24

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #45
------------------------------------------------------------

**Receipt ID:** 0134b34b-830d-4011-8d29-004add7d54dc
**Filename:** Invoice_20252205_1105.pdf
**Owner:** default-user
**Upload Date:** 2026-09-29 15:06:04
**SHA-256 Hash:** 6795b22ba1d4b62db50b7673c2c1eb1811811763af8880f2401cb914c9899cdf

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-29 15:06:13

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #46
------------------------------------------------------------

**Receipt ID:** 0e5f018d-57ad-4150-b903-59ec3c78997d
**Filename:** WhatsApp Image 2026-09-29 at 8.14.21 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-29 15:03:10
**SHA-256 Hash:** a1449357ef551e55514c3d71f6d7810abdabb7ebf1569e791e452ecc29cf6f3f

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Green House
**Transaction Date:** 2026-09-29
**Amount:** 88.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (0 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-29 15:04:08

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #47
------------------------------------------------------------

**Receipt ID:** 476c4f3e-10f4-4dd1-8b15-c37fb30048d9
**Filename:** Receipt_12Sep2026_165553.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 17:17:36
**SHA-256 Hash:** d60dd98530ed55f0f116441f9904d34ad981fb679ff9bb44512d87f5c82dadb7

### PROCESSING
**Status:** APPROVED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-12
**Amount:** 58.73 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (13 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Approved
**Finance Updated:** 2026-09-29 15:55:59

### FINAL RESULT
**Final Receipt Status:** APPROVED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #48
------------------------------------------------------------

**Receipt ID:** 2f117466-785c-4b59-8dc0-0f02ae9c3e3e
**Filename:** Receipt_12Sep2026_200455.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 17:04:44
**SHA-256 Hash:** a838e25cd0a8ff1dd77a0443a90a332b7ed4e60aebfec89ef4afe21c6830525c

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-12
**Amount:** 4.97 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (13 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 17:05:00

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #49
------------------------------------------------------------

**Receipt ID:** aacb7e51-e639-4c37-9beb-a87ffee0a13b
**Filename:** Receipt_18Sep2026_192131.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 16:57:29
**SHA-256 Hash:** 8d4dee7b3d38a959f6eca3727c71324d96ee3f0dca8100a3c00ed133d7354510

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-18
**Amount:** 52.25 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (7 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 16:57:48

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #50
------------------------------------------------------------

**Receipt ID:** e7190c60-1075-42e9-80ae-91e34586cbe2
**Filename:** RECEIPT_RD17894575277841120.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 16:52:22
**SHA-256 Hash:** d6bf39c62f9d5a8199cef565a7eecea8059d4b9c82a9f3de9dd0a0eebc40a71f

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-15
**Amount:** 49.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 50.0%
**Category Reason:** No reliable category match found

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (10 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 16:52:32

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #51
------------------------------------------------------------

**Receipt ID:** e7bfc0ae-d474-4abc-9015-cb4b08bbad62
**Filename:** RECEIPT_RD17903409658288172.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 16:50:20
**SHA-256 Hash:** e5917d9405cd770a81e8f1a125811c9b240dd6111c305cff2145589d4b28150c

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-25
**Amount:** 65.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (0 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 16:50:45

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #52
------------------------------------------------------------

**Receipt ID:** b299ec90-d4b5-4ae6-ac41-b34c4a119837
**Filename:** test.pdf
**Owner:** test-user
**Upload Date:** 2026-09-25 15:47:05
**SHA-256 Hash:** test123

### PROCESSING
**Status:** UPLOADED
**Processing Message:** N/A

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 15:47:05

### FINAL RESULT
**Final Receipt Status:** UPLOADED
**Final Explanation:** Processing in progress

------------------------------------------------------------
Receipt #53
------------------------------------------------------------

**Receipt ID:** a38ae377-3266-40e4-8e9a-69ed2cfafb88
**Filename:** 12.png
**Owner:** default-user
**Upload Date:** 2026-09-25 08:56:20
**SHA-256 Hash:** 374df2948a9bbef2d171800b66153b4d45d5cf9981f1bbcb18d11abae198f68a

### PROCESSING
**Status:** SEMANTIC_DUPLICATE
**Processing Message:** This receipt appears to duplicate a previously uploaded receipt.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-11
**Amount:** 87.64 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Semantic duplicate
**Semantic Duplicate Of:** 84921621-09b7-473d-9316-23ba1f49a5f1
**Duplicate Score:** 95
**Duplicate Reason:** Matched with receipt 84921621-09b7-473d-9316-23ba1f49a5f1 (score: 95)

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 08:56:28

### FINAL RESULT
**Final Receipt Status:** SEMANTIC_DUPLICATE
**Final Explanation:** This receipt appears to duplicate a previously uploaded receipt.

------------------------------------------------------------
Receipt #54
------------------------------------------------------------

**Receipt ID:** 84921621-09b7-473d-9316-23ba1f49a5f1
**Filename:** Receipt_11Sep2026_175049.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 08:42:09
**SHA-256 Hash:** 334260756099925a34f2bd2e7045c2bf610aab63b4bdcb3bc4505c9438cafb7f

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-11
**Amount:** 87.64 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (14 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 08:42:25

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #55
------------------------------------------------------------

**Receipt ID:** 8f0ce26b-bb03-4275-82cd-0b1bbd9f8ece
**Filename:** Receipt_11Sep2026_175049.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 08:26:31
**SHA-256 Hash:** 334260756099925a34f2bd2e7045c2bf610aab63b4bdcb3bc4505c9438cafb7f

### PROCESSING
**Status:** FAILED
**Processing Message:** Unable to store the receipt file. Please try uploading again.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Blob upload failed: Failed to upload blob: HTTPSConnection(host='promptblob.blob.core.windows.net', port=443): Failed to resolve 'promptblob.blob.core.windows.net' ([Errno 11001] getaddrinfo failed)

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 08:31:28

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** Unable to store the receipt file. Please try uploading again.

------------------------------------------------------------
Receipt #56
------------------------------------------------------------

**Receipt ID:** 3c96ddcc-7ac9-44f4-8da1-7fc13a0cf75d
**Filename:** WhatsApp Image 2026-09-25 at 1.39.54 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-25 08:25:16
**SHA-256 Hash:** 40147e7ad377dff49300dd4342d5a607b302b01f58109bda5056ec15743f43b4

### PROCESSING
**Status:** FAILED
**Processing Message:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** Document does not appear to be a receipt. Required receipt information is missing.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 08:25:25

### FINAL RESULT
**Final Receipt Status:** FAILED
**Final Explanation:** The uploaded document does not appear to be a valid receipt. A valid receipt must contain a vendor name, total amount, and at least one additional receipt indicator such as date, invoice number, payment method, or line items.

------------------------------------------------------------
Receipt #57
------------------------------------------------------------

**Receipt ID:** ceeae0e9-8e28-4c59-b206-ba59f06a02b0
**Filename:** Receipt_16Sep2026_201356.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 08:20:19
**SHA-256 Hash:** 58a8a1f1009e4e162bf73f071f5074fad48c8278aea0007506ea0d3c160c4c61

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** aec17325-1955-4db1-8c94-f24e010d8d2f
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 08:20:19

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #58
------------------------------------------------------------

**Receipt ID:** d9ff83ab-f903-4ed7-96bf-9663b29e64c9
**Filename:** WhatsApp Image 2026-09-25 at 1.41.15 PM.jpeg
**Owner:** default-user
**Upload Date:** 2026-09-25 08:19:19
**SHA-256 Hash:** a92bee8de4409e65bd4cb2442744e0ac3e9c32325f2c9f8207be9a539f347a15

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Compact Plus
**Transaction Date:** N/A
**Amount:** 130.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** copy

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": []
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 08:19:37

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #59
------------------------------------------------------------

**Receipt ID:** aec17325-1955-4db1-8c94-f24e010d8d2f
**Filename:** Receipt_16Sep2026_201356.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 08:08:57
**SHA-256 Hash:** 58a8a1f1009e4e162bf73f071f5074fad48c8278aea0007506ea0d3c160c4c61

### PROCESSING
**Status:** NEEDS_REVIEW
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** Uber
**Transaction Date:** 2026-09-16
**Amount:** 67.03 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** reflects

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 90.0%
**Category Reason:** Matched keyword 'uber' in receipt details

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (9 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Pending
**Finance Updated:** 2026-09-25 08:09:13

### FINAL RESULT
**Final Receipt Status:** NEEDS_REVIEW
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #60
------------------------------------------------------------

**Receipt ID:** 35fc5f95-5caa-44d5-b045-ce680c93e055
**Filename:** AUTO_RECEIPT_RD17899909794942053.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 07:59:34
**SHA-256 Hash:** bc40806db8dafc77f4708ea25f4f987274fed76aca9d890c33db05c4fc76e703

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** d2e3ea7f-2ba3-4053-a1f4-caa39cdc8747
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 07:59:34

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #61
------------------------------------------------------------

**Receipt ID:** d2e3ea7f-2ba3-4053-a1f4-caa39cdc8747
**Filename:** AUTO_RECEIPT_RD17899909794942053.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 07:58:47
**SHA-256 Hash:** bc40806db8dafc77f4708ea25f4f987274fed76aca9d890c33db05c4fc76e703

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-21
**Amount:** 90.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 50.0%
**Category Reason:** No reliable category match found

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (4 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Rejected
**Finance Updated:** 2026-09-29 15:56:41

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #62
------------------------------------------------------------

**Receipt ID:** 54316958-5096-43b5-9973-14aaa0918598
**Filename:** AUTO_RECEIPT_RD17887887992562243.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 07:58:37
**SHA-256 Hash:** 81409529cd880f59188f7dfdceaca901ad9ad83b8c159049287ec4d159a06aa5

### PROCESSING
**Status:** REJECTED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-07
**Amount:** 121.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (18 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Rejected
**Finance Updated:** 2026-10-01 04:23:52

### FINAL RESULT
**Final Receipt Status:** REJECTED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #63
------------------------------------------------------------

**Receipt ID:** 98b46704-dba7-499b-897d-1d727610a9fc
**Filename:** RECEIPT_RD17894757721795022.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 07:58:00
**SHA-256 Hash:** 23cbb351ac50a99acd8be98f07e0e981bec088a863e8c911a91c709b389e8b1e

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** 4bd9c058-0f87-40a9-a6bb-026bc6364c98
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 07:58:00

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #64
------------------------------------------------------------

**Receipt ID:** 4bd9c058-0f87-40a9-a6bb-026bc6364c98
**Filename:** RECEIPT_RD17894757721795022.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 07:01:27
**SHA-256 Hash:** 23cbb351ac50a99acd8be98f07e0e981bec088a863e8c911a91c709b389e8b1e

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** 735de375-cf23-487a-9084-70ab60294c72
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 07:01:27

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #65
------------------------------------------------------------

**Receipt ID:** 735de375-cf23-487a-9084-70ab60294c72
**Filename:** RECEIPT_RD17894757721795022.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 07:00:13
**SHA-256 Hash:** 23cbb351ac50a99acd8be98f07e0e981bec088a863e8c911a91c709b389e8b1e

### PROCESSING
**Status:** APPROVED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-15
**Amount:** 50.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (10 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Approved
**Finance Updated:** 2026-10-01 05:25:54

### FINAL RESULT
**Final Receipt Status:** APPROVED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #66
------------------------------------------------------------

**Receipt ID:** 63ee89e1-eab9-4047-8459-d275e5b19992
**Filename:** RECEIPT_RD17894587258082759 (2).pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 06:59:45
**SHA-256 Hash:** 5aed989f731e8cba086eea40dedcaa50d16b4eacda4f4de510ea82179e4a75f2

### PROCESSING
**Status:** EXACT_DUPLICATE
**Processing Message:** This receipt has already been uploaded.

### EXTRACTED INFORMATION
**Vendor:** N/A
**Transaction Date:** N/A
**Amount:** N/A
**Currency:** N/A
**Payment Method:** N/A
**Invoice Number:** N/A

### CLASSIFICATION
**Category:** Other
**Category Confidence:** 0.0%
**Category Reason:** N/A

### POLICY VALIDATION
**Policy Status:** N/A
**Policy Result:** N/A

### DUPLICATE CHECK
**Duplicate Status:** Exact duplicate
**Exact Duplicate Of:** a404a9d0-4603-4f70-bf18-ab008a7b90c8
**Duplicate Reason:** Same file content was already uploaded.

### FINANCE REVIEW
**Finance Status:** Not reviewed
**Finance Updated:** 2026-09-25 06:59:45

### FINAL RESULT
**Final Receipt Status:** EXACT_DUPLICATE
**Final Explanation:** This receipt has already been uploaded.

------------------------------------------------------------
Receipt #67
------------------------------------------------------------

**Receipt ID:** a404a9d0-4603-4f70-bf18-ab008a7b90c8
**Filename:** RECEIPT_RD17894587258082759.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 06:17:12
**SHA-256 Hash:** 5aed989f731e8cba086eea40dedcaa50d16b4eacda4f4de510ea82179e4a75f2

### PROCESSING
**Status:** APPROVED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-15
**Amount:** 61.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (10 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Approved
**Finance Updated:** 2026-09-25 06:18:27

### FINAL RESULT
**Final Receipt Status:** APPROVED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

------------------------------------------------------------
Receipt #68
------------------------------------------------------------

**Receipt ID:** 1220601d-4735-4701-b828-8be70d8ccef3
**Filename:** RECEIPT_RD17896113703974859.pdf
**Owner:** default-user
**Upload Date:** 2026-09-25 06:15:30
**SHA-256 Hash:** a3e9194d630f96da53a4f294965628cc22912aef1960d24d9e6ffb856ae7df08

### PROCESSING
**Status:** APPROVED
**Processing Message:** Receipt has been validated and approved by policy. Awaiting Finance review.

### EXTRACTED INFORMATION
**Vendor:** rapido
**Transaction Date:** 2026-09-17
**Amount:** 43.00 INR
**Currency:** INR
**Payment Method:** N/A
**Invoice Number:** s

### CLASSIFICATION
**Category:** Transport: Taxis/Cab/Uber
**Category Confidence:** 100.0%
**Category Reason:** Manually selected by user

### POLICY VALIDATION
**Policy Status:** APPROVED
**Policy Result:** {
  "status": "APPROVED",
  "rules": [
    {
      "code": "RECEIPT_AGE_OK",
      "passed": true,
      "message": "Receipt age is within policy (8 days old)."
    }
  ]
}

### DUPLICATE CHECK
**Duplicate Status:** Not a duplicate
**Duplicate Reason:** N/A

### FINANCE REVIEW
**Finance Status:** Approved
**Finance Updated:** 2026-09-25 08:59:31

### FINAL RESULT
**Final Receipt Status:** APPROVED
**Final Explanation:** Receipt has been validated and approved by policy. Awaiting Finance review.

## 3. POLICY/SCORING EXPLANATION

### Category Confidence Scoring
**Implementation:** `receipts/services/receipt_service.py`
**Function:** `ReceiptService.determine_category()`
**Purpose:** Classify receipt expense category with confidence score

**Scoring Method:**
- Keyword matching in merchant name (highest priority, +0.15 confidence boost)
- Keyword matching in line items and payment method
- Base confidence per category (0.80-0.95)

**Confidence Threshold:** 0.75
- Confidence ≥ 0.75: Automatic category assignment
- Confidence < 0.75: Requires user confirmation

### Duplicate Detection Scoring
**Implementation:** `receipts/services/duplicate_service.py`
**Class:** `DuplicateService`
**Function:** `evaluate_semantic_duplicate()` and `_calculate_duplicate_score()`
**Purpose:** Detect business duplicates using normalized receipt data

**Scoring Model (100-point scale):**
| Factor | Points |
|--------|--------|
| Invoice number exact match | 40 |
| Vendor normalized match | 20 |
| Transaction date match | 15 |
| Total amount match | 15 |
| Tax amount match | 5 |
| Currency match | 5 |

**Thresholds (from settings):**
- DUPLICATE_SCORE_THRESHOLD: 90 (receipt marked as duplicate)
- REVIEW_SCORE_THRESHOLD: 75 (flagged for review)
- Below 75: Receipt treated as unique

### Policy Validation Scoring
**Implementation:** `receipts/services/policy_service.py`
**Class:** `PolicyService`
**Function:** `evaluate()`
**Purpose:** Validate receipt against business policy rules

**Current Rules:**
- **Receipt Age:** Maximum 35 days old
  - Implementation: `_check_receipt_age()`
  - If receipt is > 35 days old, policy status = REJECTED

## 4. WORKFLOW SUMMARY

### Processing Flow

```
Upload (POST /api/v1/receipts/)
  ↓
File Validation (file_validation_service.py)
  - Check MIME type
  - Check file size (max 50 MB)
  - Validate PDF/JPG/PNG headers
  ↓
SHA-256 Hashing (hashing_service.py)
  - Generate hash from file bytes
  - Store in Receipt.sha256_hash
  ↓
Exact Duplicate Check (duplicate_service.py)
  - Query Receipt.objects.filter(sha256_hash=hash)
  - If found → status = EXACT_DUPLICATE
  ↓
Blob Storage (blob_service.py)
  - Upload original file to Azure Blob Storage
  - Store reference in Receipt.blob_name
  ↓
Queue for OCR (tasks.py)
  - Enqueue process_receipt_task via Celery
  ↓
OCR & Extraction (document_intelligence_service.py)
  - Send to Azure AI Document Intelligence
  - Extract merchant, amounts, dates, invoice numbers
  - Store raw result in raw_document_intelligence_json
  ↓
Normalization (normalization_service.py)
  - Convert to internal JSON contract
  - Normalize vendor names, invoice numbers, dates
  - Store in normalized_json
  ↓
Category Classification (receipt_service.py)
  - Determine category from merchant/items
  - Calculate confidence (0.0-1.0)
  - Store in category, category_confidence, category_reason
  ↓
Semantic Duplicate Check (duplicate_service.py)
  - Compare normalized data against existing receipts
  - Calculate similarity score (0-100)
  - If score ≥ DUPLICATE_SCORE_THRESHOLD → SEMANTIC_DUPLICATE
  ↓
Policy Validation (policy_service.py)
  - Check receipt age ≤ RECEIPT_MAX_AGE_DAYS
  - Set policy_status and policy_result_json
  - If policy passes → status = NEEDS_REVIEW
  - If policy fails → status = REJECTED
  ↓
Finance Review (finance/views.py)
  - Finance department reviews NEEDS_REVIEW receipts
  - Finance decision: APPROVED or REJECTED
  - Update status, updated_at, processing_message
```

## 5. TEST OBSERVATIONS

### Processing Status Distribution
- APPROVED: 4 receipt(s)
- EXACT_DUPLICATE: 12 receipt(s)
- FAILED: 14 receipt(s)
- NEEDS_REVIEW: 20 receipt(s)
- REJECTED: 13 receipt(s)
- SEMANTIC_DUPLICATE: 4 receipt(s)
- UPLOADED: 1 receipt(s)

### Category Confidence
- Receipts with confidence < 0.75 (needs user confirmation): 29
  - These would prompt user for category selection

### Duplicate Detection
- Exact duplicates (same file bytes): 12
- Semantic duplicates (different files, same expense): 4
  - Score range: 95-95

### Policy Validation
- Approved by policy: 27
- Rejected by policy: 10
- Receipts rejected for being too old: 10

### Finance Review Status
- Approved by Finance: 4
- Rejected by Finance: 3
- Pending Finance review: 20

### Processing Failures
- Failed to process: 14
  - Reasons:
    - Document does not appear to be a receipt. Required receipt i...
    - Document does not appear to be a receipt. Required receipt i...
    - Document does not appear to be a receipt. Required receipt i...
    - Document extraction failed: Failed to analyze receipt: (<HTT...
    - Document does not appear to be a receipt. Required receipt i...

## 6. TECHNICAL IMPLEMENTATION MAP

| Feature | File | Function/Class | Purpose |
|---------|------|----------------|---------|
| File Validation | `receipts/services/file_validation_service.py` | `FileValidationService.validate()` | Validate file type, size, format |
| SHA-256 Hashing | `receipts/services/hashing_service.py` | `HashingService.sha256()` | Generate hash for exact duplicate detection |
| Blob Upload | `receipts/services/blob_service.py` | `BlobService.upload()` | Store original file in Azure Blob Storage |
| Exact Duplicate Check | `receipts/services/duplicate_service.py` | `DuplicateService.find_exact_duplicate()` | Query by SHA-256 hash |
| OCR & Extraction | `receipts/services/document_intelligence_service.py` | `DocumentIntelligenceService.analyze_receipt()` | Call Azure AI Document Intelligence |
| Normalization | `receipts/services/normalization_service.py` | `ReceiptNormalizationService.normalize()` | Convert to internal JSON contract |
| Category Classification | `receipts/services/receipt_service.py` | `ReceiptService.determine_category()` | Keyword-based category detection with confidence |
| Semantic Duplicate Check | `receipts/services/duplicate_service.py` | `DuplicateService.evaluate_semantic_duplicate()` | Score-based duplicate detection |
| Policy Validation | `receipts/services/policy_service.py` | `PolicyService.evaluate()` | Validate against business rules |
| Receipt Age Check | `receipts/services/policy_service.py` | `PolicyService._check_receipt_age()` | Verify receipt ≤ 35 days old |
| Finance Decision | `finance/views.py` | `finance_receipt_decision()` | Accept Finance approval/rejection |
| Receipt Filtering | `receipts/views.py` | `ReceiptViewSet` | Filter by status, category, vendor, date, amount |
