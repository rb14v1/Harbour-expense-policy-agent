#!/usr/bin/env python
"""Check data in PostgreSQL Expense-Policy-Agent database."""

import os
from dotenv import load_dotenv
import psycopg

# Load .env
load_dotenv()

# Get DB credentials
host = os.getenv('POSTGRES_HOST')
port = os.getenv('POSTGRES_PORT')
database = os.getenv('POSTGRES_DB')
user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')

print("=" * 80)
print("POSTGRESQL DATABASE CHECK")
print("=" * 80)
print(f"\nDatabase: {database}")
print(f"Host: {host}")
print(f"User: {user}")
print(f"Port: {port}")

try:
    # Connect to PostgreSQL
    print("\n🔌 Connecting to PostgreSQL...")
    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
        sslmode="require"
    )
    print("✅ Connected successfully!\n")

    with conn.cursor() as cur:
        # Check if receipts table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'receipts_receipt'
            );
        """)
        table_exists = cur.fetchone()[0]

        if not table_exists:
            print("⚠️  receipts_receipt table does not exist.")
            conn.close()
            exit(0)

        # Get row count
        cur.execute("SELECT COUNT(*) FROM receipts_receipt;")
        count = cur.fetchone()[0]
        print(f"📊 Total receipts: {count}\n")

        if count == 0:
            print("No receipts found in database.")
        else:
            # Get all receipt data
            cur.execute("""
                SELECT
                    id,
                    owner,
                    original_filename,
                    status,
                    sha256_hash,
                    vendor_name,
                    invoice_number,
                    transaction_date,
                    total_amount,
                    currency,
                    created_at,
                    updated_at
                FROM receipts_receipt
                ORDER BY created_at DESC;
            """)

            print("=" * 150)
            print("RECEIPTS IN DATABASE")
            print("=" * 150)

            for row in cur.fetchall():
                rec_id, owner, filename, status, sha256, vendor, invoice, trans_date, total, currency, created, updated = row

                print(f"\n📄 Receipt ID: {rec_id}")
                print(f"   Owner:           {owner}")
                print(f"   Filename:        {filename}")
                print(f"   Status:          {status}")
                print(f"   SHA-256:         {sha256[:32]}..." if sha256 else "   SHA-256:         None")
                print(f"   Vendor:          {vendor}")
                print(f"   Invoice:         {invoice}")
                print(f"   Date:            {trans_date}")
                print(f"   Total:           {total} {currency}")
                print(f"   Created:         {created}")
                print(f"   Updated:         {updated}")

            print("\n" + "=" * 150)

            # Get duplicate info
            cur.execute("""
                SELECT
                    id,
                    status,
                    exact_duplicate_of_id,
                    semantic_duplicate_of_id,
                    duplicate_score,
                    duplicate_reason
                FROM receipts_receipt
                WHERE exact_duplicate_of_id IS NOT NULL
                   OR semantic_duplicate_of_id IS NOT NULL
                ORDER BY created_at DESC;
            """)

            dups = cur.fetchall()
            if dups:
                print(f"\n🔗 DUPLICATES FOUND: {len(dups)}")
                print("=" * 150)
                for rec_id, status, exact_dup_id, semantic_dup_id, score, reason in dups:
                    print(f"\n Receipt ID: {rec_id}")
                    print(f"   Status: {status}")
                    if exact_dup_id:
                        print(f"   Exact duplicate of: {exact_dup_id}")
                    if semantic_dup_id:
                        print(f"   Semantic duplicate of: {semantic_dup_id}")
                        print(f"   Score: {score}")
                    print(f"   Reason: {reason}")
            else:
                print("\nNo duplicates found.")

    conn.close()

except psycopg.OperationalError as e:
    print(f"\n❌ CONNECTION FAILED: {str(e)}")
    print("\n⚠️  Environment Limitation:")
    print("   The PostgreSQL server is not reachable from this machine.")
    print("   This is a network/firewall issue, not a database configuration issue.")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 80)
