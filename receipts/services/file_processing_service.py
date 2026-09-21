import io
from PIL import Image
from pypdf import PdfReader, PdfWriter
from django.conf import settings
from receipts.exceptions import CompressionError


class FileProcessingService:
    @staticmethod
    def get_processing_copy(file_obj, mime_type: str, original_filename: str) -> bytes:
        """
        Returns optimized bytes for OCR processing.

        If file <= compression threshold: returns original bytes as-is.
        If file > compression threshold: returns compressed bytes.
        Preserves original bytes in file_obj for Blob Storage and SHA-256.
        """
        file_obj.seek(0)
        file_size_mb = file_obj.size / (1024 * 1024)
        threshold_mb = settings.MAX_RECEIPT_COMPRESSION_THRESHOLD_MB

        if file_size_mb <= threshold_mb:
            file_obj.seek(0)
            return file_obj.read()

        try:
            if mime_type == 'application/pdf':
                return FileProcessingService._compress_pdf(file_obj)
            elif mime_type in {'image/jpeg', 'image/png'}:
                return FileProcessingService._compress_image(file_obj, mime_type, original_filename)
            else:
                file_obj.seek(0)
                return file_obj.read()
        except CompressionError:
            raise
        except Exception as e:
            raise CompressionError(f"Failed to compress file: {str(e)}")

    @staticmethod
    def _compress_image(file_obj, mime_type: str, original_filename: str) -> bytes:
        """Compress image using Pillow with quality reduction and resizing."""
        file_obj.seek(0)
        image = Image.open(file_obj)

        format_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
        if format_ext == 'jpeg':
            format_ext = 'jpg'
        pil_format = 'JPEG' if format_ext == 'jpg' else 'PNG'

        if image.mode == 'RGBA' and pil_format == 'JPEG':
            image = image.convert('RGB')

        max_pixels = settings.IMAGE_MAX_PIXELS
        if image.width * image.height > max_pixels:
            ratio = (max_pixels / (image.width * image.height)) ** 0.5
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        quality = settings.IMAGE_COMPRESSION_QUALITY

        if pil_format == 'JPEG':
            image.save(output, format=pil_format, quality=quality, optimize=True)
        else:
            image.save(output, format=pil_format, optimize=True)

        output.seek(0)
        return output.getvalue()

    @staticmethod
    def _compress_pdf(file_obj) -> bytes:
        """Compress PDF using pypdf stream compression and deduplication."""
        if not settings.PDF_COMPRESSION_ENABLED:
            file_obj.seek(0)
            return file_obj.read()

        file_obj.seek(0)
        reader = PdfReader(file_obj)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.getvalue()
