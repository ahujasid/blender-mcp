import subprocess
import sys
from pathlib import Path


def main() -> None:
    base = Path(__file__).resolve().parent
    scripts = [
        "01_test_lambda.py",
        "02_test_shape_generation.py",
        "03_test_generation_all.py",
        "04_test_modes.py",
        "05_test_export_click.py",
    ]

    for script in scripts:
        script_path = base / script
        print(f"\n===== RUN {script} =====")
        subprocess.run([sys.executable, str(script_path)], check=False)


if __name__ == "__main__":
    main()
