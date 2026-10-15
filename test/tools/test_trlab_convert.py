"""The converter of TrLab's datasets and results, on a small TrLab tree written here."""
import importlib.util
import json
import pathlib

import numpy as np
import pytest

from metagen.metaheuristics import TriGenResult
from metagen.triclustering import Cube

TOOL = pathlib.Path(__file__).resolve().parents[2] / "tools" / "trlab" / "convert.py"
spec = importlib.util.spec_from_file_location("trlab_convert", TOOL)
convert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert)

VALUES = np.round(np.random.default_rng(0).normal(5, 2, size=(6, 3, 4)), 4)
GENES = ["YAL001C", "March 1", "YAL003W", "Septin 2", "YAL005C", "YAL007C"]

RESOURCES = """<?xml version="1.0" encoding="UTF-8"?>
<resources>
  <dataset description="A small yeast experiment" geneSize="6" id="0001" maxC="3" maxG="5" maxT="4" minC="2" minG="2"
           minT="3" name="small" organism="Yeast" sampleSize="3" timeSize="4" type="b">
    <resources separator=";">
      <resource>small_t0.csv</resource><resource>small_t1.csv</resource>
      <resource>small_t2.csv</resource><resource>small_t3.csv</resource>
    </resources>
    <genes>small_genes.txt</genes><samples>small_samples.txt</samples><times>small_times.txt</times>
  </dataset>
  <dataset description="Another" geneSize="6" id="0002" maxC="3" maxG="6" maxT="4" minC="2" minG="2" minT="2"
           name="other" organism="None" sampleSize="3" timeSize="4" type="e">
    <resources separator=",">
      <resource>o_0.csv</resource><resource>o_1.csv</resource><resource>o_2.csv</resource><resource>o_3.csv</resource>
    </resources>
    <genes>o_genes.txt</genes><samples>o_samples.txt</samples><times>o_times.txt</times>
  </dataset>
</resources>
"""

SOL = """#
#Mon Dec 02 13:57:08 CET 2024
N=2
G=50
I=20
Sel=0.2
Mut=0.3
Ale=0.2
fitness=mslts
Wf=0.8
Wg=0.1
Wc=0.0
Wt=0.0
WOg=0.04
WOc=0.03
WOt=0.03
minG=2
maxG=5
minC=2
maxC=3
minT=3
maxT=4
dataset=small
solutions=0,1,2;0,1;0,1,2@3,4,5;1,2;1,2,3
"""


@pytest.fixture
def trlab(tmp_path):
    root = tmp_path / "resources"
    for folder, prefix, separator, ending in (("0001", "small_t", ";", "\r"), ("0002", "o_", ",", "\n")):
        directory = root / folder
        directory.mkdir(parents=True)
        for time in range(4):
            rows = []
            for gene in range(6):
                cells = [str(VALUES[gene, condition, time]) for condition in range(3)]
                if folder == "0002" and (gene, time) == (2, 1):
                    cells[0] = "NA"
                rows.append(separator.join(cells))
            (directory / f"{prefix}{time}.csv").write_bytes(ending.join(rows).encode())
        stem = "small" if folder == "0001" else "o"
        (directory / f"{stem}_genes.txt").write_text("\n".join(GENES))
        (directory / f"{stem}_samples.txt").write_text("alpha\ncdc15\ncdc28")
        (directory / f"{stem}_times.txt").write_text("0\n10\n20\n30")
    (root / "resources.xml").write_text(RESOURCES)
    (tmp_path / "small.sol").write_text(SOL)
    return tmp_path


def test_the_datasets_become_netcdf_files_with_their_names_and_their_sizes_apart(trlab):
    out = trlab / "out"
    rename = {"small": {"March 1": "MARCHF1", "Septin 2": "SEPTIN2"}}
    report = convert.convert_datasets(str(trlab / "resources"), str(out), rename=rename)
    assert report == ["small: (6, 3, 4), 0 missing values, 2 genes renamed",
                      "other: (6, 3, 4), 1 missing values, 0 genes renamed"]
    small = Cube.from_netcdf(str(out / "small.nc"))
    assert np.array_equal(small.values, VALUES)
    assert small.genes == ("YAL001C", "MARCHF1", "YAL003W", "SEPTIN2", "YAL005C", "YAL007C")
    assert small.conditions == ("alpha", "cdc15", "cdc28") and small.times == (0, 10, 20, 30)
    with pytest.raises(ValueError, match="1 missing cells"):
        Cube.from_netcdf(str(out / "other.nc"))
    assert Cube.from_netcdf(str(out / "other.nc"), drop_missing="genes").genes == tuple(g for g in GENES if g != "YAL003W")
    sizes = json.loads((out / "sizes.json").read_text())
    assert sizes["small"] == {"min_sizes": [2, 2, 3], "max_sizes": [5, 3, 4]}
    assert convert.convert_datasets(str(trlab / "resources"), str(trlab / "one"), only=["other"])[0].startswith("other")


def test_a_result_becomes_a_trigen_result_with_its_configuration_translated(trlab):
    out = trlab / "out"
    convert.convert_datasets(str(trlab / "resources"), str(out), only=["small"])
    result = convert.convert_sol(str(trlab / "small.sol"), str(out / "small.nc"), str(trlab / "small.json"))
    again = TriGenResult.load(str(trlab / "small.json"))
    cube = Cube.from_netcdf(str(out / "small.nc"))
    assert again.matches(cube) and again.triclusters == result.triclusters
    assert [t.size for t in again.triclusters] == [(3, 2, 3), (3, 2, 3)]
    assert again.names[1]["genes"] == ["Septin 2", "YAL005C", "YAL007C"]
    configuration = again.configuration
    assert (configuration["n_triclusters"], configuration["generations"], configuration["population_size"]) == (2, 50, 20)
    assert (configuration["measure"], configuration["views"], configuration["growth"]) == ("msl", "time", None)
    assert configuration["weights"]["quality"] == 0.8 and configuration["weights"]["overlap_times"] == 0.03
    assert again.provenance["converted_from"] == "TrLab" and again.provenance["trlab"]["fitness"] == "mslts"
    assert again.trigen(cube).n_triclusters == 2


def test_the_command_line_runs_both_conversions(trlab, capsys):
    out = trlab / "out"
    convert.main(["datasets", str(trlab / "resources"), str(out), "--only", "small"])
    convert.main(["sol", str(trlab / "small.sol"), str(out / "small.nc"), str(trlab / "r.json")])
    printed = capsys.readouterr().out
    assert "small: (6, 3, 4)" in printed and "2 triclusters" in printed
