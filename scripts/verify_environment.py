"""Prove the pinned environment can actually be rebuilt from the files in this repo.

Card #1's acceptance test. It builds a throwaway environment from `environment.lock.yml`
plus `requirements-lock.txt` and imports the packages the pipeline cannot run without.

Recreation is two stages, and the reason is not stylistic: the pip half must be installed
with `--no-deps`, because these 208 pins accreted incrementally and pip's resolver cannot
prove them consistent. A lockfile is already the resolved closure, so re-deriving it is
both unnecessary and, here, impossible. `--no-deps` is not a valid directive inside a
requirements file, so it cannot live in conda's `pip:` block — hence two files and two
commands. See docs/ENVIRONMENT.md for the full diagnosis.

This is deliberately NOT wired into CI: it needs ~8 GB and ~20 minutes, which is the slow
lane's job, not the fast lane's. Run it by hand after touching any environment file.

Usage:
    python scripts/verify_environment.py            # build, check, then delete the env
    python scripts/verify_environment.py --keep     # leave it behind for inspection
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONDA_LOCK = REPO / "environment.lock.yml"
PIP_LOCK = REPO / "requirements-lock.txt"

# The packages that decide whether the pipeline can run at all. CBFV computes every
# descriptor; without it nothing downstream has inputs.
MUST_IMPORT = "import CBFV, catboost, sklearn, numpy, pandas"


def run(stage: str, args: list[str]) -> bool:
    print(f"\n=== {stage} ===\n$ {' '.join(args)}", flush=True)
    started = time.monotonic()
    result = subprocess.run(args)
    elapsed = time.monotonic() - started
    ok = result.returncode == 0
    print(f"--- {stage}: {'OK' if ok else 'FAILED'} (exit {result.returncode}, {elapsed:.0f}s)")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", default="hydms-verify", help="throwaway environment name")
    parser.add_argument("--keep", action="store_true", help="do not delete the environment afterwards")
    args = parser.parse_args()

    conda = shutil.which("conda")
    if not conda:
        print("FAIL  conda is not on PATH. Open a shell where `conda` resolves and retry.")
        return 1

    for path in (CONDA_LOCK, PIP_LOCK):
        if not path.exists():
            print(f"FAIL  missing {path.name}. Both lock files are required.")
            return 1

    name = args.name
    print(f"Rebuilding '{name}' from {CONDA_LOCK.name} + {PIP_LOCK.name}.")
    print("Expect roughly 8 GB and 15-20 minutes.")

    # A leftover environment from an earlier run would make a failure look like a pass.
    subprocess.run([conda, "env", "remove", "-n", name, "-y"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    stages = [
        ("STAGE 1  conda env create", [conda, "env", "create", "-f", str(CONDA_LOCK), "-n", name]),
        ("STAGE 2  pip install --no-deps",
         [conda, "run", "-n", name, "python", "-m", "pip", "install", "--no-deps", "-q",
          "-r", str(PIP_LOCK)]),
        ("STAGE 3  import check",
         [conda, "run", "-n", name, "python", "-c",
          f"{MUST_IMPORT}; print('numpy', numpy.__version__, '| pandas', pandas.__version__,"
          f" '| sklearn', sklearn.__version__)"]),
    ]

    failed = None
    for stage, argv in stages:
        if not run(stage, argv):
            failed = stage
            break

    if args.keep:
        print(f"\nLeaving environment '{name}' in place (--keep).")
    else:
        print(f"\nRemoving '{name}'...")
        subprocess.run([conda, "env", "remove", "-n", name, "-y"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if failed:
        print(f"\nFAIL  {failed} failed. The environment does not rebuild from these files.")
        print("      Do not mark the environment card done until this passes.")
        return 1

    print("\nOK    environment rebuilds from the lock files and imports cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
