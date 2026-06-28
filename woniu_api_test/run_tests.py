#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Woniu API Test Runner

Usage:
    cd woniu_api_test
    python run_tests.py                          # Run all tests + generate allure report
    python run_tests.py --level unit             # Run unit tests only
    python run_tests.py --level integration      # Run integration tests only
    python run_tests.py --level scenario         # Run scenario tests only
    python run_tests.py --no-report              # Run without allure report
    python run_tests.py --serve                  # Start allure server to view report
"""
import sys
import os
import subprocess
import shutil
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
ALLURE_RESULTS = os.path.join(REPORTS_DIR, "allure-results")
ALLURE_REPORT = os.path.join(REPORTS_DIR, "allure-report")

LEVEL_MAP = {
    "unit": "testcases/unit/",
    "integration": "testcases/integration/",
    "scenario": "testcases/scenario/",
}


def check_allure_installed():
    """Check if allure CLI is installed."""
    return shutil.which("allure") is not None


def clean_reports():
    """Clean old report directories to ensure only one report exists."""
    if os.path.exists(ALLURE_RESULTS):
        shutil.rmtree(ALLURE_RESULTS)
        print("Cleaned: " + ALLURE_RESULTS)

    if os.path.exists(ALLURE_REPORT):
        shutil.rmtree(ALLURE_REPORT)
        print("Cleaned: " + ALLURE_REPORT)

    os.makedirs(REPORTS_DIR, exist_ok=True)


def run_pytest(test_path, generate_report=True):
    """Run pytest tests."""
    cmd = [
        sys.executable, "-m", "pytest", test_path,
        "-v", "--tb=short",
        "--alluredir=" + ALLURE_RESULTS,
        "--reruns=2", "--reruns-delay=5",
    ]
    print("\n" + "=" * 60)
    print("Running: " + " ".join(cmd))
    print("=" * 60 + "\n")

    result = subprocess.run(cmd, cwd=BASE_DIR)

    if generate_report:
        generate_allure_report()

    return result.returncode


def generate_allure_report():
    """Generate allure HTML report (overwrites old report)."""
    if not check_allure_installed():
        print("\nWarning: allure CLI not found!")
        print("   Install: brew install allure (macOS)")
        print("   Results saved to: " + ALLURE_RESULTS)
        print("   View with: allure serve " + ALLURE_RESULTS)
        return

    print("\n" + "=" * 60)
    print("Generating Allure report (overwriting old report)...")
    print("=" * 60)

    cmd = ["allure", "generate", ALLURE_RESULTS, "-o", ALLURE_REPORT, "--clean"]
    subprocess.run(cmd)

    print("\nAllure report generated: " + ALLURE_REPORT)
    open_allure_report()


def open_allure_report():
    """自动打开 Allure 报告"""
    report_path = os.path.join(ALLURE_REPORT, "index.html")
    if os.path.exists(report_path):
        report_url = "file://" + report_path
        print("Opening report: " + report_url)
        webbrowser.open(report_url)
    else:
        print("Report not found: " + report_path)


def serve_allure():
    """Start allure local server to view report."""
    if not check_allure_installed():
        print("Warning: allure CLI not found! Install with: brew install allure")
        return

    print("\nStarting Allure server...")
    print("Data directory: " + ALLURE_RESULTS)
    cmd = ["allure", "serve", ALLURE_RESULTS]
    subprocess.run(cmd)


def main():
    level = None
    no_report = False
    serve_mode = False

    args = sys.argv[1:]
    if "--level" in args:
        idx = args.index("--level")
        level = args[idx + 1] if idx + 1 < len(args) else None
        args.pop(idx + 1)
        args.pop(idx)

    if "--no-report" in args:
        no_report = True
        args.remove("--no-report")

    if "--serve" in args:
        serve_mode = True
        args.remove("--serve")

    if serve_mode:
        serve_allure()
        return

    if not no_report:
        clean_reports()

    if level and level in LEVEL_MAP:
        test_path = LEVEL_MAP[level]
    else:
        test_path = "testcases/"

    exit_code = run_pytest(test_path, generate_report=not no_report)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
