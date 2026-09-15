import hashlib
from receipts.exceptions import HashingError


class HashingService:
    CHUNK_SIZE = 1024 * 1024

    @staticmethod
    def sha256(file_obj) -> str:
        try:
            file_obj.seek(0)
            digest = hashlib.sha256()
            while True:
                chunk = file_obj.read(HashingService.CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
            file_obj.seek(0)
            return digest.hexdigest()
        except Exception as e:
            raise HashingError(f"Failed to calculate SHA-256: {str(e)}")
