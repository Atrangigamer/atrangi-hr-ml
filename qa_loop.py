"""Repeat the regression suite and save an auditable, fail-fast JSON report."""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    """Run independent pytest processes so lifecycle/global state resets each round."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--report", type=Path, default=Path("qa_results.json"))
    args = parser.parse_args()
    if not 1 <= args.rounds <= 100:
        parser.error("--rounds must be between 1 and 100")
    records = []
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "scope": "CPU regression tests and real local HTTP; native models are doubled",
        "requested_rounds": args.rounds,
        "rounds": records,
    }
    for index in range(1, args.rounds + 1):
        started = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests", "-q", "--tb=short"],
                cwd=Path(__file__).resolve().parent,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
            record = {
                "round": index,
                "exit_code": result.returncode,
                "seconds": round(time.monotonic() - started, 3),
                "output": result.stdout + result.stderr,
            }
        except subprocess.TimeoutExpired:
            record = {
                "round": index,
                "exit_code": 124,
                "seconds": 120,
                "output": "Test round exceeded 120 seconds",
            }
        records.append(record)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(
            f"Round {index}/{args.rounds}: {'PASS' if record['exit_code'] == 0 else 'FAIL'} ({record['seconds']}s)",
            flush=True,
        )
        if record["exit_code"]:
            print(record["output"])
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
