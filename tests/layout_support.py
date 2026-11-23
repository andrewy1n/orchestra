from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_map(packages: dict[str, str]) -> dict[str, list[str]]:
    return {package: modules.split() for package, modules in packages.items()}


def layout_problems(component: str, packages: dict[str, list[str]]) -> list[str]:
    base = ROOT / "orchestra" / component
    problems: list[str] = []
    for package, modules in packages.items():
        package_dir = base.joinpath(*package.split("."))
        parts = package.split(".")
        for depth in range(1, len(parts) + 1):
            init = base.joinpath(*parts[:depth]) / "__init__.py"
            if not init.is_file():
                problems.append(f"missing {init.relative_to(ROOT)}")
        for module in modules:
            new = package_dir / f"{module}.py"
            if not new.is_file():
                problems.append(f"missing {new.relative_to(ROOT)}")
            old = base / f"{module}.py"
            if old.exists():
                problems.append(f"remains {old.relative_to(ROOT)}")
    return problems
