class ReceiptAppException(Exception):
    pass


class UnsupportedFileTypeError(ReceiptAppException):
    pass


class ReceiptTooLargeError(ReceiptAppException):
    pass


class BlobUploadError(ReceiptAppException):
    pass


class DocumentExtractionError(ReceiptAppException):
    pass


class ReceiptNormalizationError(ReceiptAppException):
    pass


class DuplicateReceiptError(ReceiptAppException):
    pass


class HashingError(ReceiptAppException):
    pass


class PolicyValidationError(ReceiptAppException):
    pass


class CompressionError(ReceiptAppException):
    pass
