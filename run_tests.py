#!/usr/bin/env python
import sys
import os
import django
from django.conf import settings
from django.test.utils import get_runner

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=2)
failures = test_runner.run_tests(["receipts"])

print(f"\n{'='*70}")
print(f"Test Summary")
print(f"{'='*70}")
sys.exit(failures)
