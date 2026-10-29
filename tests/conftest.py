import os
import sys

import pytest

# Let tests import the project modules from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory):
    """The fake blood report from generate_sample_report.py, built fresh for the test run."""
    from generate_sample_report import generate_blood_report

    path = tmp_path_factory.mktemp("reports") / "sample_blood_report.pdf"
    generate_blood_report(str(path))
    return str(path)


@pytest.fixture(scope="session")
def medicines():
    from medicine_db import load_medicines

    return load_medicines()
