"""
Standardized test runner for auth-service.
Runs pytest with coverage reporting to /reports folder.
Usage: python run_tests.py [--html] [--verbose]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_pytest(reports_dir: Path | None = None, verbose: bool = False, html: bool = False) -> int:
    """Run pytest with coverage and JUnit reports."""
    if reports_dir is None:
        reports_dir = Path(__file__).parent / "reports"

    reports_dir.mkdir(parents=True, exist_ok=True)

    junit_xml = reports_dir / "junit.xml"
    coverage_xml = reports_dir / "coverage.xml"
    coverage_html = reports_dir / "htmlcov"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        f"--junitxml={junit_xml}",
        "--asyncio-mode=auto",
        "--cov=app",
        "--cov=main",
        f"--cov-report=xml:{coverage_xml}",
        "--cov-report=term-missing",
    ]

    if html:
        cmd.append(f"--cov-report=html:{coverage_html}")

    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-q")

    print(f"Running tests from: {Path(__file__).parent / 'tests'}")
    print(f"Reports directory: {reports_dir}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    if result.returncode == 0:
        print("\n✓ Tests passed")
        print(f"  - JUnit report: {junit_xml}")
        print(f"  - Coverage XML: {coverage_xml}")
        if html:
            print(f"  - HTML report: {coverage_html}/index.html")
    else:
        print(f"\n✗ Tests failed with code {result.returncode}")

    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run auth-service tests with coverage")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--reports-dir", type=Path, default=None, help="Custom reports directory")

    args = parser.parse_args()

    return run_pytest(
        reports_dir=args.reports_dir,
        verbose=args.verbose,
        html=args.html,
    )


if __name__ == "__main__":
    sys.exit(main())
