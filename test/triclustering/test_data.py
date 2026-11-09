"""Reading and writing a cube: NetCDF, the standard format for labeled multidimensional data."""
import numpy as np
import pytest
from scipy.io import netcdf_file

from metagen.triclustering import Cube
from metagen.triclustering.data import netcdf_attributes, read_netcdf, write_netcdf

VALUES = np.random.default_rng(0).normal(size=(6, 3, 4))


def _cube(**names):
    return Cube(VALUES, **names)


def test_a_cube_comes_back_from_netcdf_as_it_was(tmp_path):
    cube = _cube(genes=[f"gene{index}" for index in range(6)], conditions=["wild", "rd1", "ctl"], times=[2, 4, 6, 8])
    path = str(tmp_path / "cube.nc")
    cube.to_netcdf(path, attributes={"description": "retina", "replicates": 4})
    again = Cube.from_netcdf(path)
    assert again.fingerprint == cube.fingerprint and np.array_equal(again.values, cube.values)
    assert (again.genes, again.conditions, again.times) == (cube.genes, cube.conditions, cube.times)
    assert all(isinstance(time, int) for time in again.times)
    assert netcdf_attributes(path) == {"Conventions": "CF-1.8", "description": "retina", "replicates": 4}


@pytest.mark.parametrize("names, expected", [
    (None, (0, 1, 2)),                                         # positions, as integers
    ([0.5, 1.0, 2.5], (0.5, 1.0, 2.5)),                         # reals
    ([1, 2.5, 3], (1.0, 2.5, 3.0)),                             # integers and reals: reals
    (["a", 2, None], ("a", "2", "None")),                       # anything else: text
    (["MARCHF1", "Gene ñ", ""], ("MARCHF1", "Gene ñ", "")),     # any text, empty included
    ([2 ** 40, 1, 2], (2.0 ** 40, 1.0, 2.0)),                   # too large for a 32-bit integer
])
def test_the_names_are_kept_as_numbers_when_they_all_are_and_as_text_otherwise(tmp_path, names, expected):
    path = str(tmp_path / "cube.nc")
    _cube(conditions=names).to_netcdf(path)
    assert Cube.from_netcdf(path).conditions == expected


def _foreign(path, values, dimensions, coordinates=None, fill=None):
    """A NetCDF file written by someone else: other names, another order of the dimensions."""
    with netcdf_file(path, "w", version=2) as handle:
        for name, size in zip(dimensions, values.shape):
            handle.createDimension(name, size)
        for name, labels in (coordinates or {}).items():
            variable = handle.createVariable(name, "d", (name,))
            variable[:] = labels
        data = handle.createVariable("expression", "d", dimensions)
        if fill is not None:
            data._FillValue = fill
        data[:] = values


def test_a_file_with_other_dimensions_in_another_order_is_read_by_naming_them(tmp_path):
    path = str(tmp_path / "foreign.nc")
    _foreign(path, np.transpose(VALUES, (2, 0, 1)), ("hour", "probe", "sample"), {"hour": [0.0, 6.0, 12.0, 18.0]})
    cube = read_netcdf(path, variable="expression", dimensions=("probe", "sample", "hour"))
    assert np.array_equal(cube.values, VALUES)
    assert cube.times == (0.0, 6.0, 12.0, 18.0) and cube.genes == tuple(range(6))
    with pytest.raises(ValueError, match="dimensions"):
        read_netcdf(path, variable="expression")
    with pytest.raises(ValueError, match="no variable"):
        read_netcdf(path)


def test_missing_cells_are_an_error_unless_their_positions_are_dropped(tmp_path):
    values = VALUES.copy()
    values[1, 0, 0] = -999.0
    values[4, 2, 3] = np.nan
    path = str(tmp_path / "gaps.nc")
    _foreign(path, values, ("gene", "condition", "time"), fill=-999.0)
    with pytest.raises(ValueError, match="2 missing cells"):
        read_netcdf(path, variable="expression")
    cube = read_netcdf(path, variable="expression", drop_missing="genes")
    assert cube.shape == (4, 3, 4) and cube.genes == (0, 2, 3, 5)
    with pytest.raises(ValueError, match="drop_missing"):
        read_netcdf(path, variable="expression", drop_missing="rows")


def test_what_cannot_be_written_or_read_says_so(tmp_path):
    cube = _cube()
    with pytest.raises(ValueError, match="attribute"):
        cube.to_netcdf(str(tmp_path / "a.nc"), attributes={"flag": True})
    with pytest.raises(ValueError, match="attribute"):
        cube.to_netcdf(str(tmp_path / "a.nc"), attributes={"list": [1, 2]})
    with pytest.raises(ValueError, match="format"):
        write_netcdf(cube, str(tmp_path / "a.nc"), format="HDF5")
    text = tmp_path / "text.nc"
    text.write_text("gene,condition,time,value\n")
    with pytest.raises(ValueError, match="not a NetCDF file"):
        Cube.from_netcdf(str(text))
    with pytest.raises(ValueError, match="three different"):
        Cube.from_netcdf(str(tmp_path / "a.nc"), dimensions=("gene", "gene", "time"))


def test_other_programs_read_the_file_and_netcdf4_works_with_the_extra(tmp_path):
    xarray = pytest.importorskip("xarray")
    pytest.importorskip("netCDF4")
    cube = _cube(genes=[f"g{index}" for index in range(6)], conditions=["a", "b", "c"], times=[0, 1, 2, 4])
    classic = str(tmp_path / "classic.nc")
    cube.to_netcdf(classic)
    with xarray.open_dataset(classic) as dataset:
        assert list(dataset["gene"].values) == list(cube.genes)
        assert np.array_equal(dataset["values"].values, cube.values)
    modern = str(tmp_path / "modern.nc")
    cube.to_netcdf(modern, attributes={"source": "test"}, format="NETCDF4")
    again = Cube.from_netcdf(modern)
    assert again.fingerprint == cube.fingerprint and again.genes == cube.genes and again.times == cube.times
    assert netcdf_attributes(modern)["source"] == "test"


# --- text files --------------------------------------------------------------------------

from metagen.triclustering.data import read_long, read_slices  # noqa: E402


def _long(tmp_path, rows, name="long.csv", header="gene,condition,time,value", ending="\n", sep=","):
    path = tmp_path / name
    lines = [header] + [sep.join(str(cell) for cell in row) for row in rows]
    path.write_bytes(ending.join(lines).encode("utf-8") + ending.encode())
    return str(path)


ROWS = [(f"g{g}", c, t, g * 100 + ("ab".index(c)) * 10 + t) for g in range(3) for c in ("a", "b") for t in (0, 6, 12)]


def test_a_long_table_is_read_whatever_its_separator_and_line_endings(tmp_path):
    for name, sep, ending in (("a.csv", ",", "\n"), ("b.csv", ";", "\r"), ("c.tsv", "\t", "\r\n"), ("d.txt", "\t", "\n")):
        header = sep.join(["gene", "condition", "time", "value"])
        cube = read_long(_long(tmp_path, ROWS, name=name, header=header, ending=ending, sep=sep))
        assert cube.shape == (3, 2, 3) and cube.genes == ("g0", "g1", "g2") and cube.conditions == ("a", "b")
        assert cube.times == (0, 6, 12) and cube.values[2, 1, 2] == 222.0


def test_the_columns_can_have_other_names_and_be_among_others(tmp_path):
    rows = [(value, "x", gene, time, condition) for gene, condition, time, value in ROWS]
    path = _long(tmp_path, rows, header="expression,note,probe,hour,sample")
    cube = read_long(path, gene="probe", condition="sample", time="hour", value="expression")
    assert cube.values[1, 0, 1] == 106.0
    with pytest.raises(ValueError, match="no column 'gene'"):
        read_long(path)


def test_the_order_of_the_genes_conditions_and_times_can_be_given(tmp_path):
    path = _long(tmp_path, list(reversed(ROWS)))
    cube = read_long(path)
    assert cube.genes == ("g2", "g1", "g0") and cube.times == (12, 6, 0)
    ordered = read_long(path, genes=["g0", "g1", "g2"], conditions=["a", "b"], times=[0, 6.0, 12])
    assert ordered.times == (0, 6.0, 12) and ordered.values[2, 1, 2] == 222.0
    selected = read_long(path, genes=["g1", "g0"])
    assert selected.shape == (2, 2, 3)
    with pytest.raises(ValueError, match="'g9' is not in the file"):
        read_long(path, genes=["g0", "g9"])


def test_missing_values_and_missing_rows_are_an_error_unless_dropped(tmp_path):
    rows = [row if row[:3] != ("g1", "b", 6) else ("g1", "b", 6, "NA") for row in ROWS]
    with pytest.raises(ValueError, match="1 cells missing"):
        read_long(_long(tmp_path, rows))
    assert read_long(_long(tmp_path, rows), drop_missing="genes").genes == ("g0", "g2")
    absent = [row for row in ROWS if row[:3] != ("g2", "a", 0)]
    with pytest.raises(ValueError, match="1 cells missing"):
        read_long(_long(tmp_path, absent, name="absent.csv"))
    assert read_long(_long(tmp_path, absent, name="absent.csv"), drop_missing="times").times == (6, 12)
    assert read_long(_long(tmp_path, [r if r[3] != 0 else r[:3] + ("-1",) for r in ROWS], name="m.csv"),
                     missing=("-1",), drop_missing="genes").genes == ("g1", "g2")


def test_a_repeated_cell_or_a_value_that_is_not_a_number_says_where(tmp_path):
    with pytest.raises(ValueError, match="Line 3 .* repeats"):
        read_long(_long(tmp_path, [ROWS[0], ROWS[0]] + ROWS[1:]))
    with pytest.raises(ValueError, match="Line 2 .* 'high'"):
        read_long(_long(tmp_path, [("g0", "a", 0, "high")] + ROWS[1:]))


def _slice(tmp_path, name, header, rows, sep=","):
    path = tmp_path / name
    lines = ([sep.join(header)] if header is not None else []) + [sep.join(str(cell) for cell in row) for row in rows]
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def test_a_matrix_per_time_becomes_a_cube(tmp_path):
    files = {hour: _slice(tmp_path, f"t{hour}.csv", ["gene", "wild", "rd1"], [[f"g{g}", g + hour, g - hour] for g in range(4)])
             for hour in (2, 4, 6)}
    cube = read_slices(files)
    assert cube.shape == (4, 2, 3) and cube.conditions == ("wild", "rd1") and cube.times == (2, 4, 6)
    assert cube.values[3, 1].tolist() == [1.0, -1.0, -3.0]
    in_order = read_slices(list(files.values()))
    assert in_order.times == (0, 1, 2) and np.array_equal(in_order.values, cube.values)


def test_a_matrix_per_time_without_names_takes_them_from_the_call(tmp_path):
    files = [_slice(tmp_path, f"t{t}.csv", None, [[g + t, g * t] for g in range(3)], sep=";") for t in range(3)]
    cube = read_slices(files, header=False, gene_column=False, genes=["x", "y", "z"], conditions=["p", "q"])
    assert cube.genes == ("x", "y", "z") and cube.conditions == ("p", "q") and cube.values[2, 1, 2] == 4.0
    no_corner = [_slice(tmp_path, f"n{t}.csv", ["p", "q"], [[f"g{g}", g, t] for g in range(3)]) for t in range(2)]
    assert read_slices(no_corner).conditions == ("p", "q")


def test_matrices_that_disagree_or_hold_gaps_say_so(tmp_path):
    good = _slice(tmp_path, "a.csv", ["gene", "p", "q"], [["g0", 1, 2], ["g1", 3, 4]])
    other_genes = _slice(tmp_path, "b.csv", ["gene", "p", "q"], [["g0", 1, 2], ["g9", 3, 4]])
    other_shape = _slice(tmp_path, "c.csv", ["gene", "p", "q"], [["g0", 1, 2], ["g1", 3, 4], ["g2", 5, 6]])
    gap = _slice(tmp_path, "d.csv", ["gene", "p", "q"], [["g0", 1, "NA"], ["g1", 3, 4]])
    with pytest.raises(ValueError, match="same genes"):
        read_slices([good, other_genes])
    with pytest.raises(ValueError, match="same genes|has 3 genes"):
        read_slices([good, other_shape])
    with pytest.raises(ValueError, match="1 cells missing"):
        read_slices([good, gap])
    with pytest.raises(ValueError, match="at least two times"):
        read_slices([good])
    with pytest.raises(ValueError, match="mapping"):
        read_slices(good)


# --- preparing ---------------------------------------------------------------------------

from metagen.triclustering.data import collapse_genes, drop_genes, rename_genes  # noqa: E402


def test_dropping_genes_by_name_and_by_pattern_keeps_the_others_in_order():
    cube = Cube(VALUES, genes=["YAL001C", "EMPTY", "NORF", "YAL002W", "GENOMIC 50NG/UL", "YAL003W"])
    kept = drop_genes(cube, names=["EMPTY", "absent"], pattern=r"^(NORF|GENOMIC)")
    assert kept.genes == ("YAL001C", "YAL002W", "YAL003W")
    assert np.array_equal(kept.values, VALUES[[0, 3, 5]])
    assert drop_genes(cube).genes == cube.genes
    with pytest.raises(ValueError):
        drop_genes(cube, pattern=r"^Y|E|N|G")


def test_collapsing_makes_one_row_per_name_by_its_mean_or_its_most_variable_row():
    values = VALUES.copy()
    values[3] = values[0] * 10.0                 # the second row of "A" varies most
    cube = Cube(values, genes=["A", "B", "C", "A", "B", "D"])
    mean = collapse_genes(cube)
    assert mean.genes == ("A", "B", "C", "D")
    assert np.allclose(mean.values[0], (values[0] + values[3]) / 2) and np.allclose(mean.values[1], (values[1] + values[4]) / 2)
    most = collapse_genes(cube, how="variance")
    assert np.array_equal(most.values[0], values[3]) and np.array_equal(most.values[2], values[2])
    with pytest.raises(ValueError, match="mean' or 'variance"):
        collapse_genes(cube, how="max")


def test_renaming_through_a_table_says_what_it_did_not_rename():
    cube = Cube(VALUES, genes=["p1", "p2", "p3", "p4", "p5", "p6"])
    renamed, unmapped = rename_genes(cube, {"p1": "DDR1", "p2": "RFC2", "p4": "DDR1"})
    assert renamed.genes == ("DDR1", "RFC2", "p3", "DDR1", "p5", "p6") and unmapped == ["p3", "p5", "p6"]
    only, _ = rename_genes(cube, {"p1": "DDR1", "p2": "RFC2", "p4": "DDR1"}, drop_unmapped=True)
    assert only.genes == ("DDR1", "RFC2", "DDR1") and np.array_equal(only.values, VALUES[[0, 1, 3]])
    assert collapse_genes(only).genes == ("DDR1", "RFC2")


# --- checking ----------------------------------------------------------------------------

from metagen.triclustering import plant  # noqa: E402
from metagen.triclustering.data import check  # noqa: E402

RNG = np.random.default_rng(3)
SOUND = RNG.normal(size=(40, 4, 6))


def _names(count, prefix="g"):
    return [f"{prefix}{index}" for index in RNG.permutation(count)]


def test_sound_data_bring_no_warning():
    assert check(Cube(SOUND, genes=_names(40))) == []
    for seed in range(3):
        assert check(plant((120, 6, 8), [(20, 3, 5)], noise=0.05, seed=seed)[0]) == []


@pytest.mark.parametrize("values, start", [
    (np.exp(SOUND * 3 + 7), "The values may need a transform"),        # raw intensities
    (SOUND * 0.001, "The values may need scaling"),                     # almost flat
])
def test_a_scale_where_msl_tells_little_apart_is_reported(values, start):
    warnings = check(Cube(values, genes=_names(40)))
    assert len(warnings) == 1 and warnings[0].startswith(start)


def test_columns_of_a_single_measurement_are_told_from_conditions():
    values = SOUND.copy()
    values[:, 1] = values[:, 0] * 2 + 0.01 * RNG.normal(size=(40, 6))    # the same column, rescaled
    values[:, 3] = -values[:, 2]                                         # one the reverse of the other
    warnings = check(Cube(values, genes=_names(40), conditions=["CH1I", "CH1D", "RAT1", "RAT2"]))
    assert len(warnings) == 1 and warnings[0].startswith("2 pairs of conditions")
    assert "'CH1I' and 'CH1D'" in warnings[0] and "'RAT1' and 'RAT2' (-1.000)" in warnings[0]
    # Replicates differ by more than the differences between genes: no warning.
    genes = RNG.normal(scale=5, size=(40, 1, 1))
    replicates = genes + RNG.normal(size=(40, 4, 6))
    assert check(Cube(replicates, genes=_names(40))) == []


def test_names_that_repeat_look_like_dates_or_like_control_spots_are_reported():
    names = _names(32) + ["g1", "g2", "1-Mar", "Sep 2", "1552563_a_at", "AF086181", "EMPTY", "--Control"]
    warnings = check(Cube(SOUND, genes=names))
    assert [warning.split(" ")[:3] for warning in warnings] == [["2", "names", "repeat,"], ["2", "names", "look"],
                                                                ["2", "names", "look"], ["2", "rows", "look"]]
    assert "'1-Mar', 'Sep 2'" in warnings[1] and "'1552563_a_at', 'AF086181'" in warnings[2]
    assert "'EMPTY', '--Control'" in warnings[3]
    for gene in ("CTRL", "MARCHF1", "SEPTIN2", "LAMB1", "NEGR1", "Empty1", "Gm12345", "A2M"):   # genes
        assert check(Cube(SOUND, genes=_names(39) + [gene])) == []


def test_constant_rows_zeros_and_alphabetical_order_are_reported():
    values = SOUND.copy()
    values[5] = 1.0
    values[10:14, :, :3] = 0.0
    warnings = check(Cube(values, genes=_names(40)))
    assert len(warnings) == 2 and warnings[0].startswith("1 rows never change") and "exactly zero" in warnings[1]
    integers = np.round(np.abs(SOUND) * 3)
    assert not any("zero" in warning for warning in check(Cube(integers, genes=_names(40))))
    ordered = sorted(f"G{index:03d}" for index in range(40))
    assert check(Cube(SOUND, genes=ordered))[0].startswith("The genes are in alphabetical order")


# --- GEO ---------------------------------------------------------------------------------

import gzip  # noqa: E402

from metagen.triclustering.data import read_gds  # noqa: E402


def _gds(path, values=None, extra_column=True, zipped=False):
    """A GDS in miniature: two protocols, three hours, two series of the first protocol and
    one of the second (as GDS4472, with its series as another factor)."""
    samples = [f"GSM{index}" for index in range(9)]
    hours = {0: "hour 0", 1: "hour 8", 2: "hour 16"}
    lines = ["^DATABASE = Geo", "^DATASET = GDS0"]
    subsets = [("protocol", "silencing", samples[:6]), ("protocol", "control", samples[6:]),
               ("other", "TC 1", samples[0:6:2]), ("other", "TC 2", samples[1:6:2]), ("other", "TC n/a", samples[6:])]
    # hours appear in the file out of order: 16, 0, 8
    for order, hour in ((2, "hour 16"), (0, "hour 0"), (1, "hour 8")):
        subsets.append(("time", hour, [s for i, s in enumerate(samples) if (i // 2 if i < 6 else i - 6) == order]))
    for index, (kind, description, members) in enumerate(subsets):
        lines += [f"^SUBSET = GDS0_{index}", f"!subset_description = {description}",
                  "!subset_sample_id = " + ",".join(members), f"!subset_type = {kind}"]
    lines.append("!dataset_table_begin")
    lines.append("\t".join(["ID_REF", "IDENTIFIER"] + samples + (["Gene title"] if extra_column else [])))
    for gene in range(4):
        row = [str(gene * 100 + column) for column in range(9)] if values is None else values[gene]
        lines.append("\t".join([f"{gene}_at", f"GENE{gene}"] + row + (["a title"] if extra_column else [])))
    lines.append("!dataset_table_end")
    content = ("\n".join(lines) + "\n").encode()
    (gzip.open if zipped else open)(path, "wb").write(content)
    return str(path)


def test_a_gds_becomes_a_cube_with_its_factors_as_conditions_and_times(tmp_path):
    path = _gds(tmp_path / "GDS0.soft")
    cube = read_gds(path, time="time")
    assert cube.times == ("hour 0", "hour 8", "hour 16")
    assert cube.conditions == ("silencing / TC 1", "silencing / TC 2", "control / TC n/a")
    assert cube.genes == ("GENE0", "GENE1", "GENE2", "GENE3")
    # GSM0, GSM2, GSM4 are the first series of the silencing at hours 0, 8 and 16
    assert cube.values[1, 0].tolist() == [100.0, 102.0, 104.0] and cube.values[1, 2].tolist() == [106.0, 107.0, 108.0]
    probes = read_gds(_gds(tmp_path / "GDS0.soft.gz", zipped=True), time="time", genes="ID_REF")
    assert probes.genes == ("0_at", "1_at", "2_at", "3_at") and np.array_equal(probes.values, cube.values)


def test_replicates_are_split_or_averaged(tmp_path):
    samples = [f"GSM{index}" for index in range(8)]
    lines = ["^DATASET = GDS1"]
    for index, (kind, description, members) in enumerate((
            ("genotype", "wild", samples[:4]), ("genotype", "rd1", samples[4:]),
            ("age", "day 2", ["GSM0", "GSM1", "GSM4", "GSM5"]), ("age", "day 8", ["GSM2", "GSM3", "GSM6", "GSM7"]))):
        lines += [f"^SUBSET = GDS1_{index}", f"!subset_description = {description}",
                  "!subset_sample_id = " + ",".join(members), f"!subset_type = {kind}"]
    lines += ["!dataset_table_begin", "\t".join(["ID_REF", "IDENTIFIER"] + samples)]
    lines += ["\t".join([f"p{g}", f"G{g}"] + [str(g * 10 + s) for s in range(8)]) for g in range(3)]
    path = tmp_path / "GDS1.soft"
    path.write_text("\n".join(lines + ["!dataset_table_end"]) + "\n")
    split = read_gds(str(path), time="age")
    assert split.conditions == ("wild #1", "wild #2", "rd1 #1", "rd1 #2") and split.times == ("day 2", "day 8")
    assert split.values[1, 1].tolist() == [11.0, 13.0] and split.values[1, 2].tolist() == [14.0, 16.0]
    mean = read_gds(str(path), time="age", replicates="mean")
    assert mean.conditions == ("wild", "rd1") and mean.values[1, 0].tolist() == [10.5, 12.5]


def test_what_does_not_fit_says_so(tmp_path):
    path = _gds(tmp_path / "GDS0.soft")
    with pytest.raises(ValueError, match="no factor 'age'"):
        read_gds(path, time="age")
    with pytest.raises(ValueError, match="as many replicates"):
        read_gds(path, time="time", conditions=["protocol"])      # the control has one series, the silencing two
    with pytest.raises(ValueError, match="'split' or 'mean'"):
        read_gds(path, time="time", replicates="median")
    with pytest.raises(ValueError, match="IDENTIFIER"):
        read_gds(path, time="time", genes="symbol")
    text = tmp_path / "text.soft"
    text.write_text("gene,value\n")
    with pytest.raises(ValueError, match="not the SOFT file"):
        read_gds(str(text), time="time")
    gaps = [[str(gene * 10 + column) for column in range(9)] for gene in range(4)]
    gaps[2][3] = "null"
    with pytest.raises(ValueError, match="1 cells missing"):
        read_gds(_gds(tmp_path / "gaps.soft", values=gaps), time="time")
    assert read_gds(_gds(tmp_path / "gaps.soft", values=gaps), time="time", drop_missing="genes").genes == \
        ("GENE0", "GENE1", "GENE3")


from metagen.triclustering import data as data_module  # noqa: E402
from metagen.triclustering.data import fetch_gds  # noqa: E402


def test_fetching_a_gds_downloads_it_once_from_its_place_in_geo(tmp_path, monkeypatch):
    asked = []

    def download(url, path, timeout):
        asked.append(url)
        _gds(path, zipped=True)

    monkeypatch.setattr(data_module, "_download", download)
    path = fetch_gds("GDS4510", folder=str(tmp_path / "geo"))
    assert path == str(tmp_path / "geo" / "GDS4510_full.soft.gz")
    assert asked == ["https://ftp.ncbi.nlm.nih.gov/geo/datasets/GDS4nnn/GDS4510/soft/GDS4510_full.soft.gz"]
    assert read_gds(path, time="time").shape == (4, 3, 3)
    assert fetch_gds("GDS4510", folder=str(tmp_path / "geo")) == path and len(asked) == 1
    fetch_gds("GDS12", folder=str(tmp_path / "geo"), full=False)
    assert asked[-1] == "https://ftp.ncbi.nlm.nih.gov/geo/datasets/GDSnnn/GDS12/soft/GDS12.soft.gz"


def test_fetching_what_geo_does_not_have_or_cannot_serve_says_so_and_leaves_nothing(tmp_path, monkeypatch):
    import urllib.error

    def missing(url, path, timeout):
        open(path, "wb").write(b"half")
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)

    def offline(url, path, timeout):
        raise urllib.error.URLError("no route to host")

    folder = tmp_path / "geo"
    monkeypatch.setattr(data_module, "_download", missing)
    with pytest.raises(ValueError, match="GEO has no DataSet GDS9999999"):
        fetch_gds("GDS9999999", folder=str(folder))
    monkeypatch.setattr(data_module, "_download", offline)
    with pytest.raises(RuntimeError, match="could not be reached"):
        fetch_gds("GDS1", folder=str(folder))
    assert list(folder.iterdir()) == []
    with pytest.raises(ValueError, match="GDS followed by digits"):
        fetch_gds("GSE112660")
