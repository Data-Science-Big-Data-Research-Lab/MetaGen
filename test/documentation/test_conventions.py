"""The conventions the package declares for its source files, checked: every module of
``src/`` carries the GPLv3 header, as the license of the package says."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "src" / "metagen"


def test_every_module_carries_the_gpl_header():
    missing = [str(path.relative_to(SOURCE)) for path in sorted(SOURCE.rglob("*.py"))
               if "GNU General Public License" not in path.read_text(encoding="utf-8")]
    assert not missing, "modules without the GPLv3 header: " + ", ".join(missing)
