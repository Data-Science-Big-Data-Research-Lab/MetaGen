"""The conventions the package declares for its source files, checked: every module of
``src/`` carries the GPLv3 header, as the license of the package says."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "src" / "metagen"


def test_every_module_carries_the_gpl_header():
    missing = [str(path.relative_to(SOURCE)) for path in sorted(SOURCE.rglob("*.py"))
               if "GNU General Public License" not in path.read_text(encoding="utf-8")]
    assert not missing, "modules without the GPLv3 header: " + ", ".join(missing)


def test_read_the_docs_installs_what_the_docs_extra_declares():
    # Read the Docs installs docs/requirements.txt and does not install the package; the docs
    # extra of pyproject.toml has to say the same, or one of the two drifts.
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10: pip brings it
        from pip._vendor import tomli as tomllib
    root = Path(__file__).resolve().parents[2]
    with open(root / "pyproject.toml", "rb") as handle:
        extra = tomllib.load(handle)["project"]["optional-dependencies"]["docs"]
    listed = [line.strip() for line in (root / "docs" / "requirements.txt").read_text().splitlines()
              if line.strip() and not line.lstrip().startswith("#")]
    assert sorted(listed) == sorted(extra)
