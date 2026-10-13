"""The biological quality: the enrichment of the genes of a tricluster, from g:Profiler,
from local ontology and annotation files, or from an Ontologizer table, and BIOQ, the
score by levels of its p-values. Nothing here uses the network: g:Profiler is answered
from within the test."""
import gzip
import io
import json
import math
import urllib.error

import numpy as np
import pytest
from scipy.stats import hypergeom

import metagen.triclustering.enrichment as module
from metagen.triclustering import (Cube, Enrichment, GProfiler, LocalGO, Term, Tricluster, bioq, enrich,
                                   ontologizer_table, purity, triq)

OBO = """format-version: 1.2
data-version: releases/2026-01-01

[Term]
id: GO:0000001
name: process

[Term]
id: GO:0000002
name: metabolism
is_a: GO:0000001 ! process

[Term]
id: GO:0000003
name: sugar metabolism
is_a: GO:0000002 ! metabolism

[Term]
id: GO:0000004
name: transport
is_a: GO:0000001 ! process

[Term]
id: GO:0000005
name: complex
relationship: has_part GO:0000006 ! subunit

[Term]
id: GO:0000006
name: subunit
relationship: part_of GO:0000005 ! complex

[Term]
id: GO:0000007
name: an obsolete term
is_obsolete: true

[Term]
id: GO:0000008
name: regulation of sugar metabolism
alt_id: GO:0000099
is_a: GO:0000001 ! process
relationship: regulates GO:0000003 ! sugar metabolism

[Term]
id: GO:0000010
is_a: GO:7777777 ! a term this file does not hold

[Typedef]
id: part_of
name: part of
"""


def _gaf_line(symbol, term, qualifier="involved_in", synonyms=""):
    return "\t".join(["DB", "ID_" + symbol, symbol, qualifier, term, "REF", "IEA", "", "P", "", synonyms, "protein",
                      "taxon:1", "20260101", "DB"]) + "\n"


GAF = ("!gaf-version: 2.2\n!date-generated: 2026-01-02\n"
       + "".join(_gaf_line(f"g{i}", "GO:0000003") for i in (1, 2, 3, 4))
       + _gaf_line("g5", "GO:0000004", synonyms="g15|g16") + _gaf_line("g6", "GO:0000006")
       + _gaf_line("g7", "GO:0000005") + _gaf_line("g8", "GO:0000003", qualifier="NOT|involved_in")
       + _gaf_line("g9", "GO:0000099") + _gaf_line("g10", "GO:0000007") + _gaf_line("g11", "GO:9999999")
       + _gaf_line("g12", "GO:0000010") + _gaf_line("g13", "GO:0000003", qualifier="not|involved_in"))
POPULATION = [f"g{i}" for i in range(1, 21)]


@pytest.fixture
def local(tmp_path):
    (tmp_path / "go.obo").write_text(OBO)
    (tmp_path / "genes.gaf").write_text(GAF)
    return LocalGO(str(tmp_path / "go.obo"), str(tmp_path / "genes.gaf"))


def _by_id(enrichment):
    return {term.id: term for term in enrichment.terms}


# --- BIOQ ----------------------------------------------------------------------------------

BOUNDS = module._lower_bounds(1e-40, 10.0, 1.0)      # the levels of the defaults


def _enrichment(*p_values, raw=None):
    terms = tuple(Term(f"GO:{index}", f"term {index}", p, None if raw is None else raw[index])
                  for index, p in enumerate(p_values))
    return Enrichment(terms, engine="test", version="v", study_size=10, population_size=100)


@pytest.mark.parametrize("p, level", [(1.0, 1), (0.5, 1), (0.1000001, 1), (0.1, 2), (0.05, 2), (0.01, 3), (1e-5, 6),
                                      (1.0000001e-5, 5), (1e-39, 40), (1.0000001e-40, 40), (1e-40, 41), (1e-300, 41),
                                      (0.0, 41)])
def test_a_p_value_falls_in_the_level_whose_upper_bound_it_reaches(p, level):
    assert module._level(p, BOUNDS) == level


def test_the_bounds_of_the_levels_are_one_over_a_power_of_ten():
    """As TrLab computes them: 1 / 10**25 is not the float 1e-25, and a p-value on the bound
    belongs to the level above it."""
    bound = 1.0 / 10 ** 25
    assert module._level(bound, BOUNDS) == 26 and module._level(math.nextafter(bound, 1.0), BOUNDS) == 25
    assert len(BOUNDS) == 40
    for level in range(1, 41):
        assert module._level(1.0 / 10 ** level, BOUNDS) == level + 1


@pytest.mark.parametrize("p_values, bonus", [((-0.1, 0.5), 0), ((1.5,), 0), ((math.nan, 0.5), 0), ((math.inf,), 0),
                                             ((0.5,), -1), ((0.5,), math.nan)])
def test_p_values_out_of_range_and_a_negative_bonus_are_rejected(p_values, bonus):
    with pytest.raises(ValueError):
        bioq(_enrichment(*p_values), bonus=bonus)


def test_bioq_is_the_score_by_levels_over_the_largest_possible():
    """Three terms in levels 13, 2 and 1, with weights 121, 11 and 1; the best is in level 13,
    and the bonus is 10 unless said otherwise."""
    expected = ((121 * 13 + 11 * 2 + 1 * 1) / 3 + 13 + 10) / (401 * 41 + 41 + 10)
    assert bioq(_enrichment(1e-12, 0.03, 0.6)) == pytest.approx(expected, rel=1e-12)
    without_bonus = ((121 * 13 + 11 * 2 + 1 * 1) / 3 + 13) / (401 * 41 + 41)
    assert bioq(_enrichment(1e-12, 0.03, 0.6), bonus=0) == pytest.approx(without_bonus, rel=1e-12)


def test_bioq_ranges_from_nearly_zero_to_one():
    assert bioq(_enrichment(1e-50, 1e-45, 0.0)) == 1.0 == bioq(_enrichment(1e-50, 1e-45, 0.0), bonus=0)
    # Every term in level 1: 1, plus the level of the best, plus the bonus.
    assert bioq(_enrichment(1.0, 0.9, 0.5)) == pytest.approx(12 / (401 * 41 + 41 + 10))
    assert bioq(_enrichment(1.0, 0.9, 0.5), bonus=0) == pytest.approx(2 / (401 * 41 + 41))
    assert math.isnan(bioq(_enrichment()))


def test_a_p_value_of_zero_is_the_most_significant_there_is():
    assert bioq(_enrichment(0.0, 0.5)) == bioq(_enrichment(1e-60, 0.5)) > bioq(_enrichment(1e-30, 0.5))


def test_bioq_scores_the_p_values_before_the_correction_when_asked_and_given():
    enrichment = _enrichment(0.5, 0.9, raw=[1e-3, 0.2])
    assert bioq(enrichment, adjusted=False) == bioq(_enrichment(1e-3, 0.2)) > bioq(enrichment)
    with pytest.raises(ValueError):
        bioq(_enrichment(0.5, 0.9), adjusted=False)


def test_fewer_levels_and_only_the_significant_terms_use_more_of_the_range():
    """Three terms, in levels 13, 2 and 1 of the defaults. With a threshold of 1e-10 there are
    11 levels, the last from 1e-10 down, with weight 101; with alpha, the term that is not
    significant is not scored."""
    enrichment = _enrichment(1e-12, 0.03, 0.6)
    fewer = ((101 * 11 + 11 * 2 + 1 * 1) / 3 + 11 + 10) / (101 * 11 + 11 + 10)
    assert bioq(enrichment, threshold=1e-10) == pytest.approx(fewer, rel=1e-12)
    significant = ((121 * 13 + 11 * 2) / 2 + 13 + 10) / (401 * 41 + 41 + 10)
    assert bioq(enrichment, alpha=0.05) == pytest.approx(significant, rel=1e-12)
    assert bioq(enrichment, threshold=1e-20, alpha=0.05) > bioq(enrichment, alpha=0.05) > bioq(enrichment)
    assert bioq(_enrichment(0.3, 0.6), alpha=0.05) == 0.0 and math.isnan(bioq(_enrichment(), alpha=0.05))
    assert bioq(_enrichment(1e-50, 1e-45), threshold=1e-20, alpha=0.05) == 1.0


def test_the_levels_follow_their_base_step_and_difference():
    """Base 2 and step 1: level 1 holds (0.5, 1], level 2 (0.25, 0.5], level 3 (0.125, 0.25]
    and, with a threshold of 0.125, level 4 the rest. A difference of 2: weights 1, 3, 5, 7."""
    enrichment = _enrichment(0.6, 0.5, 0.2, 0.125, 0.01)
    expected = ((1 * 1 + 3 * 2 + 5 * 3 + 7 * 4 + 7 * 4) / 5 + 4) / (7 * 4 + 4)
    assert bioq(enrichment, base=2, threshold=0.125, difference=2, bonus=0) == pytest.approx(expected, rel=1e-12)
    # A step of 0.5 leaves the p-values above it in no level, though they still count.
    halved = ((1 * 1 + 1 * 1 + 3 * 2 + 3 * 2) / 5 + 2) / (3 * 2 + 2)
    assert bioq(_enrichment(0.6, 0.5, 0.4, 0.25, 0.01), base=2, step=0.5, threshold=0.25, difference=2,
                bonus=0) == pytest.approx(halved, rel=1e-12)


@pytest.mark.parametrize("options", [{"base": 1}, {"step": 0}, {"step": 1.5}, {"difference": -1}, {"threshold": 0},
                                     {"threshold": 0.5}, {"alpha": 0}, {"alpha": 1.5}])
def test_levels_out_of_range_are_rejected(options):
    with pytest.raises(ValueError):
        bioq(_enrichment(0.01, 0.5), **options)


# --- purity --------------------------------------------------------------------------------

def _counted(*terms, study=20, population=5000):
    return Enrichment(tuple(Term(f"GO:{index}", f"term {index}", p, None, k, K) for index, (p, k, K) in enumerate(terms)),
                      engine="test", version="v", study_size=study, population_size=population)


def test_the_purity_is_the_largest_share_of_the_genes_beyond_that_of_the_population():
    """A specific term with 12 of the 20 genes and 40 of the 5000; a general one with 18 of
    the 20 and half the population; one that is not significant with all 20."""
    enrichment = _counted((1e-9, 12, 40), (0.01, 18, 2500), (0.6, 20, 100))
    assert purity(enrichment) == pytest.approx(12 / 20 - 40 / 5000)
    assert purity(enrichment, alpha=0.7) == pytest.approx(20 / 20 - 100 / 5000)
    assert purity(_counted((0.01, 18, 2500))) == pytest.approx(18 / 20 - 0.5)


def test_the_purity_does_not_depend_on_how_many_genes_or_how_small_the_p_value():
    small = _counted((1e-4, 8, 50), study=16)
    large = _counted((1e-60, 80, 50 * 10), study=160, population=50000)
    assert purity(small) == pytest.approx(purity(large))
    assert bioq(large) > 10 * bioq(small)


def test_the_purity_is_zero_without_a_significant_term_and_not_defined_without_terms():
    assert purity(_counted((0.2, 15, 30), (0.9, 3, 300))) == 0.0
    assert math.isnan(purity(_counted()))
    # A significant term that annotates fewer genes than expected does not count below 0.
    assert purity(_counted((0.01, 2, 2500))) == 0.0


def test_the_artificial_root_is_not_a_function(local):
    """Every annotated gene has the root: with four annotated genes of four against nine of
    twenty it would give 0.55; the purity is that of the best real term."""
    enrichment = local.enrich(["g1", "g2", "g3", "g4"], POPULATION)
    assert purity(enrichment, alpha=1.0) == pytest.approx(4 / 4 - 5 / 20)
    root = Enrichment((Term("GO:0000000", "root", 0.001, None, 4, 9),), "LocalGO", "v", 4, 20)
    assert purity(root) == 0.0


def test_the_purity_needs_the_counts_of_each_term():
    with pytest.raises(ValueError, match="how many genes"):
        purity(_enrichment(1e-6, 0.5))
    with pytest.raises(ValueError):
        purity(_counted((0.01, 5, 50)), alpha=0)


def test_more_significant_terms_give_a_higher_bioq_and_a_higher_triq():
    cube = Cube(np.random.default_rng(0).normal(size=(10, 3, 4)))
    tricluster = Tricluster(range(5), range(3), range(4))
    weak, strong = bioq(_enrichment(0.04, 0.5, 0.9)), bioq(_enrichment(1e-20, 1e-8, 0.9))
    assert strong > weak
    assert triq(cube, tricluster, bioq=strong) > triq(cube, tricluster, bioq=weak)


def test_the_significant_terms_are_those_below_alpha():
    enrichment = _enrichment(1e-6, 0.04, 0.05, 0.3)
    assert [term.p_adjusted for term in enrichment.significant()] == [1e-6, 0.04]
    assert len(enrichment.significant(alpha=0.5)) == 4


# --- the local engine ------------------------------------------------------------------------

def test_a_gene_takes_its_terms_and_every_term_above_them_by_any_relation(local):
    terms = _by_id(local.enrich(["g1", "g2", "g3", "g9"], POPULATION))
    # g1-g3: sugar metabolism and above; g9: its term by an alternative identifier, the
    # process above it, and what it regulates and above; all of them the artificial root.
    assert set(terms) == {"GO:0000001", "GO:0000002", "GO:0000003", "GO:0000008", "GO:0000000"}
    assert {term.id: term.study_count for term in terms.values()} == {
        "GO:0000001": 4, "GO:0000002": 4, "GO:0000003": 4, "GO:0000008": 1, "GO:0000000": 4}
    assert terms["GO:0000008"].name == "regulation of sugar metabolism" and terms["GO:0000000"].name == "root"


def test_the_population_counts_every_gene_and_leaves_out_what_does_not_annotate(local):
    """Twenty genes in the population, annotated or not. g8 and g13 are annotated with NOT,
    g10 to an obsolete term and g11 to one the ontology does not hold: none of them counts."""
    enrichment = local.enrich(["g1", "g2", "g3", "g9"], POPULATION)
    terms = _by_id(enrichment)
    assert enrichment.population_size == 20 and enrichment.study_size == 4
    assert terms["GO:0000003"].population_count == 5          # g1-g4 and g9
    assert terms["GO:0000001"].population_count == 6          # those and g5
    assert terms["GO:0000000"].population_count == 9          # every annotated gene: g1-g7, g9 and g12


def test_the_test_is_hypergeometric_and_bonferroni_counts_every_term_tested(local):
    terms = _by_id(local.enrich(["g1", "g2", "g3", "g9"], POPULATION))
    p = hypergeom.sf(3, 20, 5, 4)                              # the four of the study among the five
    assert terms["GO:0000003"].p == pytest.approx(p) == pytest.approx(5 / math.comb(20, 4))
    assert terms["GO:0000003"].p_adjusted == pytest.approx(5 * p)   # five terms tested, the root among them
    # The root: the four of the study among the nine annotated genes of the twenty.
    assert terms["GO:0000000"].p_adjusted == pytest.approx(5 * math.comb(9, 4) / math.comb(20, 4))
    # One gene of the six of the process, drawn once: p = 0.3, times four terms, capped at 1.
    assert _by_id(local.enrich(["g1"], POPULATION))["GO:0000001"].p_adjusted == 1.0


def test_the_terms_come_most_significant_first_and_ties_by_identifier(local):
    """Metabolism and sugar metabolism annotate the same genes, so they tie."""
    enrichment = local.enrich(["g9", "g3", "g2", "g1"], POPULATION)
    assert [term.id for term in enrichment.terms] == ["GO:0000002", "GO:0000003", "GO:0000001", "GO:0000000",
                                                      "GO:0000008"]


def test_a_term_without_a_name_is_a_term_and_what_the_file_does_not_hold_is_not(local):
    terms = _by_id(local.enrich(["g12"], POPULATION))
    assert set(terms) == {"GO:0000010", "GO:0000000"} and terms["GO:0000010"].name == "GO:0000010"


def test_the_synonyms_of_a_gene_do_not_annotate(local):
    """g15 and g16 are synonyms of g5 in the annotation file; only the symbol counts."""
    assert local.enrich(["g15", "g16"], POPULATION).terms == ()


def test_with_synonyms_a_gene_is_also_found_by_its_identifier_and_its_synonyms(tmp_path):
    """g15 and g16 are synonyms of g5, and ID_g6 the identifier of g6. "shared" is a synonym
    of two genes: it answers to neither."""
    (tmp_path / "go.obo").write_text(OBO)
    (tmp_path / "genes.gaf").write_text(GAF + _gaf_line("g1", "GO:0000003", synonyms="shared")
                                        + _gaf_line("g7", "GO:0000005", synonyms="shared"))
    population = POPULATION + ["ID_g6", "shared"]
    engine = LocalGO(str(tmp_path / "go.obo"), str(tmp_path / "genes.gaf"), synonyms=True)
    terms = _by_id(engine.enrich(["g15", "g16", "ID_g6"], population))
    assert terms["GO:0000004"].study_count == 2 and terms["GO:0000006"].study_count == 1
    # In the population: g5 and its two synonyms; a symbol keeps its own annotations.
    assert terms["GO:0000004"].population_count == 3
    assert engine.enrich(["shared", "g17"], population).terms == ()
    assert _by_id(engine.enrich(["g1"], population))["GO:0000003"].population_count == 5
    plain = LocalGO(str(tmp_path / "go.obo"), str(tmp_path / "genes.gaf"))
    assert plain.enrich(["g15", "g16", "ID_g6"], population).terms == ()


def test_the_study_has_to_be_within_the_population(local):
    with pytest.raises(ValueError, match="not in the population"):
        local.enrich(["g1", "elsewhere"], POPULATION)
    with pytest.raises(ValueError):
        local.enrich(["g1"], [])
    with pytest.raises(ValueError):
        local.enrich([1, 2], POPULATION)
    with pytest.raises(ValueError):
        local.enrich("g1", POPULATION)
    assert local.enrich([], POPULATION).terms == ()


def test_files_that_are_not_an_ontology_and_its_annotations_are_rejected(tmp_path):
    obo, gaf, zipped = tmp_path / "go.obo", tmp_path / "genes.gaf", tmp_path / "genes.gaf.gz"
    obo.write_text(OBO)
    gaf.write_text(GAF)
    zipped.write_bytes(gzip.compress(GAF.encode()))
    with pytest.raises(ValueError, match="unzip"):
        LocalGO(str(obo), str(zipped))
    with pytest.raises(ValueError, match="OBO"):
        LocalGO(str(gaf), str(obo))
    with pytest.raises(ValueError, match="GAF"):
        LocalGO(str(obo), str(obo))
    (tmp_path / "windows.obo").write_bytes(b"\xef\xbb\xbf" + OBO.replace("\n", "\r\n").encode())
    assert LocalGO(str(tmp_path / "windows.obo"), str(gaf)).enrich(["g1"], POPULATION).terms


def test_relations_that_form_a_cycle_reach_every_term_on_it(local):
    """complex has_part subunit, subunit part_of complex: a gene of either holds both, in
    whatever order they are asked for."""
    for study in (["g6", "g7"], ["g7", "g6"], ["g6"], ["g7"]):
        terms = _by_id(local.enrich(study, POPULATION))
        assert set(terms) == {"GO:0000005", "GO:0000006", "GO:0000000"}
        assert terms["GO:0000005"].population_count == terms["GO:0000006"].population_count == 2


def test_genes_given_twice_count_once_and_unannotated_ones_give_no_terms(local):
    twice = local.enrich(["g1", "g1", "g2"], POPULATION + ["g1"])
    assert twice.study_size == 2 and twice.population_size == 20
    assert _by_id(twice)["GO:0000003"].study_count == 2 and _by_id(twice)["GO:0000003"].population_count == 5
    nothing = local.enrich(["g17", "g18"], POPULATION)
    assert nothing.terms == () and math.isnan(bioq(nothing))


def test_the_version_tells_the_ontology_and_the_annotations(local):
    assert local.version == "GO releases/2026-01-01; annotations 2026-01-02"
    assert local.enrich(["g1"], POPULATION).engine == "LocalGO"


# --- Ontologizer tables ----------------------------------------------------------------------

TABLE = ("ID\tPop.total\tPop.term\tStudy.total\tStudy.term\tp\tp.adjusted\tp.min\tname\n"
         'GO:0000000\t16908\t14017\t15\t14\t0.24\t1.0\t0.0\t"root"\n'
         'GO:0042611\t16908\t21\t15\t11\t1.0E-33\t7.2E-31\t0.0\t"MHC protein complex"\n'
         'GO:0032774\t16908\t3472\t15\t6\t0.068\t1.0\t0.0\t"RNA biosynthetic process"\n')


def test_an_ontologizer_table_reads_as_an_enrichment(tmp_path):
    path = tmp_path / "table-genes_1-Term-For-Term-Bonferroni.txt"
    path.write_text(TABLE)
    enrichment = ontologizer_table(str(path))
    assert enrichment.engine == "Ontologizer" and enrichment.study_size == 15 and enrichment.population_size == 16908
    best = enrichment.terms[0]
    assert (best.id, best.name, best.p, best.p_adjusted, best.study_count, best.population_count) == (
        "GO:0042611", "MHC protein complex", 1e-33, 7.2e-31, 11, 21)
    assert len(enrichment.terms) == 3
    # Levels 31, 1 and 1; the weight of level 31 is 301.
    assert bioq(enrichment) == pytest.approx(((301 * 31 + 1 + 1) / 3 + 31 + 10) / (401 * 41 + 41 + 10))


def test_a_file_that_is_not_an_ontologizer_table_is_rejected(tmp_path):
    path = tmp_path / "other.txt"
    for content in ("gene\tvalue\nA\t1\n", TABLE + "GO:0000001\t16908\n", TABLE + "GO:1\t1\tx\t1\t1\t0.5\t1.0\n", ""):
        path.write_text(content)
        with pytest.raises(ValueError, match="Ontologizer"):
            ontologizer_table(str(path))


# --- g:Profiler ------------------------------------------------------------------------------

ANSWER = {"result": [
    {"native": "GO:2", "name": "second", "p_value": 0.2, "intersection_size": 1, "term_size": 40},
    {"native": "GO:1", "name": "first", "p_value": 1e-9, "intersection_size": 3, "term_size": 12},
    {"native": "GO:3", "name": "no gene of the study", "p_value": 1.0, "intersection_size": 0, "term_size": 7}],
    "meta": {"version": "e999_test"}}


@pytest.fixture
def asked(monkeypatch):
    requests = []

    def post(url, body, timeout):
        requests.append((url, json.loads(body), timeout))
        return json.loads(json.dumps(ANSWER))

    monkeypatch.setattr(module, "_post", post)
    return requests


def test_gprofiler_is_asked_for_every_term_against_the_population_given(asked):
    enrichment = GProfiler(organism="scerevisiae", timeout=7).enrich(["A", "B", "B", "C"], ["A", "B", "C", "D", "D"])
    (url, request, timeout), = asked
    assert url.startswith("https://biit.cs.ut.ee/gprofiler") and timeout == 7
    assert request["organism"] == "scerevisiae" and request["query"] == ["A", "B", "C"]
    assert request["background"] == ["A", "B", "C", "D"] and request["domain_scope"] == "custom"
    assert request["all_results"] is True and request["user_threshold"] == 1.0
    assert request["significance_threshold_method"] == "bonferroni"
    assert request["sources"] == ["GO:BP", "GO:MF", "GO:CC"]
    assert enrichment.engine == "g:Profiler" and enrichment.version == "e999_test"
    assert enrichment.study_size == 3 and enrichment.population_size == 4
    assert [(term.id, term.p_adjusted, term.study_count, term.population_count) for term in enrichment.terms] == [
        ("GO:1", 1e-9, 3, 12), ("GO:2", 0.2, 1, 40)]
    assert enrichment.terms[0].p is None


def test_gprofiler_keeps_nothing_on_disk_unless_asked_and_then_asks_once(asked, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    GProfiler().enrich(["A", "B"], ["A", "B", "C"])
    GProfiler().enrich(["A", "B"], ["A", "B", "C"])
    assert len(asked) == 2 and list(tmp_path.iterdir()) == []
    cache = tmp_path / "cache"
    first = GProfiler(cache_dir=str(cache)).enrich(["A", "B"], ["A", "B", "C"])
    again = GProfiler(cache_dir=str(cache)).enrich(["A", "B"], ["A", "B", "C"])
    assert len(asked) == 3 and first == again and len(list(cache.iterdir())) == 1
    GProfiler(cache_dir=str(cache)).enrich(["A", "C"], ["A", "B", "C"])
    GProfiler(cache_dir=str(cache), organism="mmusculus").enrich(["A", "B"], ["A", "B", "C"])
    assert len(asked) == 5 and len(list(cache.iterdir())) == 3


def test_the_same_analysis_is_the_same_request_and_a_different_one_is_not(asked, tmp_path):
    cache = tmp_path / "cache"
    GProfiler(cache_dir=str(cache)).enrich(["A", "B"], ["A", "B", "C"])
    GProfiler(cache_dir=str(cache)).enrich(["B", "A"], ["C", "B", "A"])
    assert len(asked) == 1
    GProfiler(cache_dir=str(cache)).enrich(["A", "B"], ["A", "B", "C", "D"])
    GProfiler(cache_dir=str(cache), sources=["GO:BP"]).enrich(["A", "B"], ["A", "B", "C"])
    GProfiler(cache_dir=str(cache), correction="g_SCS").enrich(["A", "B"], ["A", "B", "C"])
    assert len(asked) == 4 and len(list(cache.iterdir())) == 4


def test_gprofiler_is_not_asked_about_no_genes_and_checks_the_study(asked):
    assert GProfiler().enrich([], ["A", "B"]).terms == () and asked == []
    with pytest.raises(ValueError, match="not in the population"):
        GProfiler().enrich(["A", "Z"], ["A", "B"])
    assert asked == []


@pytest.mark.parametrize("failure", [urllib.error.URLError("no route to host"), TimeoutError("timed out"),
                                     ConnectionResetError("reset")])
def test_gprofiler_out_of_reach_says_so(monkeypatch, failure):
    def unreachable(url, body, timeout):
        raise failure

    monkeypatch.setattr(module, "_post", unreachable)
    with pytest.raises(RuntimeError, match="could not be reached.*LocalGO"):
        GProfiler().enrich(["A"], ["A", "B"])


def test_a_request_gprofiler_rejects_says_why(monkeypatch):
    def rejected(url, body, timeout):
        raise urllib.error.HTTPError(url, 400, "Bad Request", {}, io.BytesIO(b'{"message": "Invalid organism: human"}'))

    monkeypatch.setattr(module, "_post", rejected)
    with pytest.raises(RuntimeError, match="rejected.*400.*Invalid organism"):
        GProfiler(organism="human").enrich(["A"], ["A", "B"])


@pytest.mark.parametrize("answer", [{"meta": {"version": "v"}}, {"result": []}, [],
                                    {"result": [{"native": "GO:1", "name": "n", "p_value": None,
                                                 "intersection_size": 1, "term_size": 2}], "meta": {"version": "v"}}])
def test_an_answer_that_is_not_an_analysis_is_an_error_and_is_not_kept(monkeypatch, tmp_path, answer):
    monkeypatch.setattr(module, "_post", lambda url, body, timeout: answer)
    with pytest.raises(RuntimeError, match="not an analysis"):
        GProfiler(cache_dir=str(tmp_path)).enrich(["A"], ["A", "B"])
    assert list(tmp_path.iterdir()) == []

    def not_json(url, body, timeout):
        return json.loads("<html>")

    monkeypatch.setattr(module, "_post", not_json)
    with pytest.raises(RuntimeError, match="not an analysis"):
        GProfiler().enrich(["A"], ["A", "B"])


def test_a_damaged_answer_on_disk_is_asked_again(asked, tmp_path):
    GProfiler(cache_dir=str(tmp_path)).enrich(["A"], ["A", "B"])
    kept, = tmp_path.iterdir()
    kept.write_text('{"result": [')
    enrichment = GProfiler(cache_dir=str(tmp_path)).enrich(["A"], ["A", "B"])
    assert len(asked) == 2 and len(enrichment.terms) == 2 and json.loads(kept.read_text())["meta"]


def test_options_out_of_range_are_rejected():
    with pytest.raises(ValueError):
        GProfiler(correction="fdr")
    with pytest.raises(ValueError):
        GProfiler(sources="GO:BP")


# --- from a cube -----------------------------------------------------------------------------

class _Recorder:
    def __init__(self):
        self.calls = []

    def enrich(self, genes, population):
        self.calls.append((list(genes), list(population)))
        return _enrichment(1e-6, 0.5)


def test_the_enrichment_of_a_tricluster_is_that_of_its_genes_against_those_of_the_cube():
    names = [f"gene{i}" for i in range(10)]
    cube = Cube(np.random.default_rng(1).normal(size=(10, 3, 4)), genes=names)
    provider = _Recorder()
    enrichment = enrich(cube, Tricluster([7, 2, 5], range(3), range(4)), provider)
    assert provider.calls == [(["gene2", "gene5", "gene7"], names)]
    assert bioq(enrichment) > 0


def test_a_cube_without_gene_names_cannot_be_enriched():
    cube = Cube(np.random.default_rng(1).normal(size=(10, 3, 4)))
    with pytest.raises(ValueError, match="names"):
        enrich(cube, Tricluster(range(3), range(3), range(4)), _Recorder())
