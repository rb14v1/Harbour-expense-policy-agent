from django.conf import settings
from receipts.exceptions import UnsupportedFileTypeError, ReceiptTooLargeError


ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'image/jpeg': '.jpg',
    'image/png': '.png',
}

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}


class FileValidationService:
    @staticmethod
    def validate(file_obj, filename: str) -> None:
        ext = _get_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
            )

        file_size_mb = file_obj.size / (1024 * 1024)
        max_size_mb = settings.MAX_RECEIPT_UPLOAD_MB
        if file_size_mb > max_size_mb:
            raise ReceiptTooLargeError(
                f"File too large: {file_size_mb:.2f}MB. Maximum: {max_size_mb}MB"
            )


def _get_extension(filename: str) -> str:
    if '.' not in filename:
        return ''
    return '.' + filename.rsplit('.', 1)[1].lower()
