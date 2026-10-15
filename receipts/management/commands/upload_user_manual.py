"""
Django management command to upload the User Manual to Azure Blob Storage.

Usage:
    python manage.py upload_user_manual
    python manage.py upload_user_manual --local-only  # Test with local file only
    python manage.py upload_user_manual --blob-path custom/path/manual.html
"""

import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from receipts.services.blob_service import BlobService
from receipts.exceptions import BlobUploadError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Upload the User Manual HTML document to Azure Blob Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-only',
            action='store_true',
            help='Verify local file exists without uploading to Blob Storage',
        )
        parser.add_argument(
            '--blob-path',
            type=str,
            default=None,
            help='Custom Blob Storage path (e.g., "docs/manual.html")',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force upload even if file already exists in Blob Storage',
        )

    def handle(self, *args, **options):
        # Determine paths
        base_dir = settings.BASE_DIR
        manual_file = base_dir / 'expense_policy_agent_user_manual.html'
        blob_path = options.get('blob_path') or getattr(
            settings,
            'MANUAL_BLOB_PATH',
            'documentation/expense_policy_agent_user_manual.html'
        )
        local_only = options.get('local_only', False)
        force_upload = options.get('force', False)

        # Step 1: Verify local file exists
        self.stdout.write(f"Checking for user manual at: {manual_file}")

        if not manual_file.exists():
            raise CommandError(f"User manual file not found: {manual_file}")

        file_size = manual_file.stat().st_size
        self.stdout.write(
            self.style.SUCCESS(f"✓ Found user manual ({file_size:,} bytes)")
        )

        # Step 2: Local-only mode
        if local_only:
            self.stdout.write(self.style.SUCCESS("✓ Local file verification successful"))
            self.stdout.write("Skipping Blob Storage upload (--local-only mode)")
            return

        # Step 3: Upload to Blob Storage
        self.stdout.write(f"\nUploading to Blob Storage...")
        self.stdout.write(f"Destination: {blob_path}")

        try:
            blob_service = BlobService()

            # Verify connection
            try:
                # Try to list blobs to verify connection
                list(blob_service.container_client.list_blobs(results_per_page=1))
            except Exception as e:
                raise CommandError(
                    f"Cannot connect to Azure Blob Storage: {str(e)}\n"
                    f"Verify AZURE_STORAGE_CONNECTION_STRING is configured."
                )

            # Check if blob already exists
            try:
                existing_blob = blob_service.container_client.get_blob_client(blob_path)
                existing_props = existing_blob.get_blob_properties()
                existing_size = existing_props.size

                if not force_upload:
                    self.stdout.write(
                        self.style.WARNING(
                            f"ℹ Blob already exists ({existing_size:,} bytes)"
                        )
                    )
                    self.stdout.write("Use --force to overwrite")
                    return
                else:
                    self.stdout.write(f"ℹ Overwriting existing blob ({existing_size:,} bytes)")
            except:
                # Blob doesn't exist yet, that's fine
                pass

            # Upload
            blob_service.upload_file(
                str(manual_file),
                blob_path,
                content_type='text/html; charset=utf-8'
            )

            self.stdout.write(
                self.style.SUCCESS(f"✓ Successfully uploaded to Blob Storage")
            )

            # Verify upload
            try:
                uploaded_blob = blob_service.container_client.get_blob_client(blob_path)
                uploaded_props = uploaded_blob.get_blob_properties()
                uploaded_size = uploaded_props.size
                uploaded_time = uploaded_props.last_modified

                self.stdout.write(f"\nVerification:")
                self.stdout.write(f"  Blob path: {blob_path}")
                self.stdout.write(f"  Size: {uploaded_size:,} bytes")
                self.stdout.write(f"  Last modified: {uploaded_time}")
                self.stdout.write(f"  Content-Type: {uploaded_props.content_settings.content_type}")

                self.stdout.write(
                    self.style.SUCCESS("\n✓ User manual upload complete and verified")
                )
                logger.info(f"[UPLOAD_USER_MANUAL] Successfully uploaded {blob_path} ({uploaded_size} bytes)")

            except Exception as e:
                logger.warning(f"[UPLOAD_USER_MANUAL] Could not verify upload: {str(e)}")
                self.stdout.write(
                    self.style.WARNING("⚠ Upload completed but verification failed")
                )

        except BlobUploadError as e:
            raise CommandError(f"Failed to upload user manual: {str(e)}")
        except CommandError:
            raise
        except Exception as e:
            logger.error(f"[UPLOAD_USER_MANUAL] Unexpected error: {str(e)}", exc_info=True)
            raise CommandError(f"Unexpected error: {str(e)}")
