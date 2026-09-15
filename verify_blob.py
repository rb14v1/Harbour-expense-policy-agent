#!/usr/bin/env python
"""
Azure Blob Storage Verification Script

This script checks whether a specific blob exists in Azure Blob Storage
using the existing project .env configuration (no Django required).

Usage:
    python verify_blob.py <blob_name>

Example:
    python verify_blob.py "receipts/test-user/289e266d-a833-497c-8e09-4c5ac8911980/test_receipt.pdf"
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import traceback

# Load .env from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Read Azure configuration from .env
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'receipts')


def verify_blob(blob_name: str):
    """Check if blob exists in Azure Blob Storage."""

    print("\n" + "=" * 70)
    print("AZURE BLOB STORAGE VERIFICATION")
    print("=" * 70)

    # Verify configuration
    if not connection_string or connection_string.startswith("DefaultEndpointsProtocol=https;AccountName=..."):
        print("\n❌ ERROR: Azure Storage connection string not configured.")
        print("   Please set AZURE_STORAGE_CONNECTION_STRING in .env")
        print("\n" + "=" * 70)
        return 1

    print(f"\n✓ Container:              {container_name}")
    print(f"✓ Blob name:              {blob_name}")

    try:
        # Connect to Azure Blob Storage
        client = BlobServiceClient.from_connection_string(connection_string)
        container_client = client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)

        # Check if blob exists
        blob_properties = blob_client.get_blob_properties()

        print(f"\n✅ Blob exists:           YES")
        print(f"   Size:                  {blob_properties.size} bytes")
        print(f"   Content type:          {blob_properties.content_settings.content_type}")
        print(f"   Last modified:         {blob_properties.last_modified}")
        print(f"   Created:               {blob_properties.creation_time}")

        print("\n" + "=" * 70)
        return 0

    except ResourceNotFoundError:
        print(f"\n❌ Blob exists:           NO")
        print(f"   The blob '{blob_name}' was not found in container '{container_name}'")
        print("\n" + "=" * 70)
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        print(f"\n📍 Full Traceback:")
        print("-" * 70)
        traceback.print_exc()
        print("-" * 70)
        print("\n" + "=" * 70)
        return 1


def main():
    if len(sys.argv) < 2:
        print("\n❌ ERROR: blob_name argument required")
        print("\nUsage:")
        print("    python verify_blob.py <blob_name>")
        print("\nExample:")
        print("    python verify_blob.py 'receipts/test-user/289e266d-a833-497c-8e09-4c5ac8911980/test_receipt.pdf'")
        return 1

    blob_name = sys.argv[1]
    return verify_blob(blob_name)


if __name__ == '__main__':
    sys.exit(main())
