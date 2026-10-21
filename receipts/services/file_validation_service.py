from django.conf import settings
from receipts.exceptions import UnsupportedFileTypeError, ReceiptTooLargeError
from PIL import Image
from pypdf import PdfReader
import io


ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'image/jpeg': '.jpg',
    'image/png': '.png',
}

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}

PDF_HEADER = b'%PDF'
JPEG_HEADER = bytes([0xFF, 0xD8, 0xFF])
PNG_HEADER = b'\x89PNG'


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

        if file_obj.size == 0:
            raise UnsupportedFileTypeError("File is empty.")

        file_obj.seek(0)
        file_header = file_obj.read(1024)
        file_obj.seek(0)

        if not file_header:
            raise UnsupportedFileTypeError("File is empty or unreadable.")

        if ext == '.pdf':
            _validate_pdf(file_obj, file_header)
        elif ext in {'.jpg', '.jpeg', '.png'}:
            _validate_image(file_obj, file_header, ext)


def _validate_pdf(file_obj, file_header: bytes) -> None:
    if not file_header.startswith(PDF_HEADER):
        raise UnsupportedFileTypeError(
            "File does not appear to be a valid PDF. "
            "PDF files must start with %PDF header."
        )

    file_obj.seek(0)
    try:
        reader = PdfReader(file_obj)

        if len(reader.pages) == 0:
            raise UnsupportedFileTypeError(
                "PDF contains zero pages. Cannot process empty PDF."
            )

        file_obj.seek(0)

    except UnsupportedFileTypeError:
        raise
    except Exception as e:
        raise UnsupportedFileTypeError(
            f"PDF is corrupted or malformed: {str(e)}"
        )


def _validate_image(file_obj, file_header: bytes, ext: str) -> None:
    if ext in {'.jpg', '.jpeg'}:
        if not file_header.startswith(JPEG_HEADER):
            raise UnsupportedFileTypeError(
                "File does not appear to be a valid JPEG image. "
                "JPEG files must start with FF D8 FF header."
            )
    elif ext == '.png':
        if not file_header.startswith(PNG_HEADER):
            raise UnsupportedFileTypeError(
                "File does not appear to be a valid PNG image. "
                "PNG files must start with 89 50 4E 47 header."
            )

    file_obj.seek(0)
    try:
        image = Image.open(file_obj)
        image.verify()

        file_obj.seek(0)
        image = Image.open(file_obj)

        if image.size == (0, 0):
            raise UnsupportedFileTypeError(
                "Image has invalid dimensions (0x0)."
            )

        if image.width < 10 or image.height < 10:
            raise UnsupportedFileTypeError(
                f"Image is too small ({image.width}x{image.height}). "
                "Minimum size is 10x10 pixels."
            )

        _check_blank_image(image)

    except Exception as e:
        if isinstance(e, UnsupportedFileTypeError):
            raise
        raise UnsupportedFileTypeError(
            f"Image is corrupted or invalid: {str(e)}"
        )


def _check_blank_image(image: Image.Image) -> None:
    try:
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode not in {'RGB', 'L'}:
            image = image.convert('RGB')

        pixels = image.getdata()
        if not pixels:
            raise UnsupportedFileTypeError("Image contains no pixel data.")

        pixel_list = list(pixels)

        if image.mode == 'RGB':
            white_pixels = sum(
                1 for p in pixel_list
                if isinstance(p, tuple) and p == (255, 255, 255)
            )
        else:
            white_pixels = sum(
                1 for p in pixel_list
                if p == 255
            )

        white_percent = (white_pixels / len(pixel_list)) * 100

        if white_percent > 95:
            raise UnsupportedFileTypeError(
                f"Image appears to be blank or mostly white ({white_percent:.1f}% white pixels)."
            )

    except UnsupportedFileTypeError:
        raise
    except Exception as e:
        raise UnsupportedFileTypeError(
            f"Could not analyze image content: {str(e)}"
        )


def _get_extension(filename: str) -> str:
    if '.' not in filename:
        return ''
    return '.' + filename.rsplit('.', 1)[1].lower()
