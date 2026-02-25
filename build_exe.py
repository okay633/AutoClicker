import shutil
import subprocess
import sys
from pathlib import Path


def run() -> int:
    project_root = Path(__file__).resolve().parent
    workspace_root = project_root.parent

    script_path = project_root / "Code" / "autoclicker.py"
    icon_path = project_root / "Assets" / "icon.ico"
    spec_path = workspace_root / "AutoClicker.spec"
    build_dir = workspace_root / "build"
    dist_dir = workspace_root / "dist"

    for path in (build_dir, dist_dir):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    if spec_path.exists():
        spec_path.unlink(missing_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "AutoClicker",
        "--icon",
        str(icon_path),
        str(script_path),
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(workspace_root))

    exe_path = dist_dir / "AutoClicker.exe"
    if result.returncode == 0 and exe_path.exists():
        print(f"\nBuild successful: {exe_path}")
        return 0

    print("\nBuild failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
