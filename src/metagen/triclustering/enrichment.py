"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import functools
import hashlib
import json
import math
import os
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Protocol, Sequence, Set, Tuple

from scipy.stats import hypergeom

if TYPE_CHECKING:
    from metagen.triclustering.cube import Cube
    from metagen.triclustering.tricluster import Tricluster


@dataclass(frozen=True)
class Term:
    """
    A term of an enrichment analysis.

    :param id: The identifier, such as ``"GO:0006955"``.
    :param name: The name.
    :param p_adjusted: The p-value corrected for the number of terms tested.
    :param p: The p-value before the correction, None if the engine does not give it.
    :param study_count: How many genes of the study the term annotates.
    :param population_count: How many genes of the population the term annotates.
    """

    id: str
    name: str
    p_adjusted: float
    p: Optional[float] = None
    study_count: Optional[int] = None
    population_count: Optional[int] = None


@dataclass(frozen=True)
class Enrichment:
    """
    The result of an enrichment analysis: every term tested, that is, every term that
    annotates at least one gene of the study, and where it comes from.

    :param terms: The terms, most significant first.
    :param engine: The engine that computed it.
    :param version: The version of the annotations it used.
    :param study_size: The genes of the study.
    :param population_size: The genes of the population.
    """

    terms: Tuple[Term, ...]
    engine: str
    version: str
    study_size: int
    population_size: int

    def significant(self, alpha: float = 0.05) -> Tuple[Term, ...]:
        """
        The terms whose adjusted p-value is below ``alpha``.

        :param alpha: The threshold, defaults to 0.05.
        :type alpha: float, optional
        :return: Those terms, most significant first.
        :rtype: Tuple[Term, ...]
        """
        return tuple(term for term in self.terms if term.p_adjusted < alpha)


class EnrichmentProvider(Protocol):
    """What computes an enrichment analysis: anything with this method, such as
    :py:class:`GProfiler` and :py:class:`LocalGO`."""

    def enrich(self, genes: Sequence[str], population: Sequence[str]) -> Enrichment:
        """
        The enrichment of some genes, the study, against a population that holds them.

        :param genes: The genes of the study.
        :type genes: Sequence[str]
        :param population: The genes of the population.
        :type population: Sequence[str]
        :return: The enrichment.
        :rtype: Enrichment
        """
        ...


def enrich(cube: Cube, tricluster: Tricluster, provider: EnrichmentProvider) -> Enrichment:
    """
    The enrichment of the genes of a tricluster against all the genes of its cube; with
    :py:func:`bioq`, its biological quality. The documentation of the triclustering
    package has an example.

    :param cube: The data, with the names of its genes.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param provider: What computes the enrichment, such as :py:class:`GProfiler`.
    :type provider: EnrichmentProvider
    :return: The enrichment of its genes.
    :rtype: Enrichment
    :raises ValueError: if the genes of the cube have no names.
    """
    tricluster.check(cube)
    if not all(isinstance(name, str) for name in cube.genes):
        raise ValueError("An enrichment needs the names of the genes: build the cube with Cube(values, genes=...).")
    return provider.enrich([cube.genes[position] for position in tricluster.genes], list(cube.genes))


def _study_and_population(genes: Sequence[str], population: Sequence[str]) -> Tuple[list, list]:
    """The genes of the study and of the population, each once and in the order given."""
    for name, given in (("genes", genes), ("population", population)):
        if isinstance(given, str) or not all(isinstance(gene, str) for gene in given):
            raise ValueError(f"The {name} must be a sequence of gene names.")
    study, background = list(dict.fromkeys(genes)), list(dict.fromkeys(population))
    if not background:
        raise ValueError("The population holds no genes.")
    outside = sorted(set(study) - set(background))
    if outside:
        raise ValueError(f"{len(outside)} genes of the study are not in the population, such as {outside[:3]}: "
                         f"the population has to hold them.")
    return study, background


def _by_significance(term: Term) -> Tuple[float, float, str]:
    """Most significant first, and the identifier to break ties, so the order is the same
    in every run."""
    return term.p_adjusted, 1.0 if term.p is None else term.p, term.id


# --- BIOQ ----------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def _lower_bounds(threshold: float, base: float, step: float) -> Tuple[float, ...]:
    """The lower bound of each level but the last (TRIQ, BioData Mining 2018, Eqs. 8a-8e),
    built as TrLab builds them (GoSignificance.java): step / base**l while it is not below
    the threshold. Level l holds the p-values in (bound l, bound l - 1], the first up to 1,
    and one more level those from 0 to the last bound. Computed this way, for ten of the
    forty powers of ten the bound differs from the literal 1e-l in the last bit, which
    only matters for a p-value exactly on a bound."""
    bounds = []
    level = 1
    bound = step / base ** level
    while bound >= threshold:
        bounds.append(bound)
        level += 1
        bound = step / base ** level
    return tuple(bounds)


def _level(p: float, bounds: Tuple[float, ...]) -> int:
    """The level of a p-value in [0, 1]: the first whose lower bound it is above."""
    for level, bound in enumerate(bounds, start=1):
        if p > bound:
            return level
    return len(bounds) + 1


def bioq(enrichment: Enrichment, bonus: float = 10.0, adjusted: bool = True, threshold: float = 1e-40,
         base: float = 10.0, step: float = 1.0, difference: float = 10.0, alpha: Optional[float] = None) -> float:
    """
    The biological quality of a tricluster (BIOQ), from the enrichment of its genes: the
    p-values of its terms are scored by levels, the more significant the higher, and the
    score is divided by the largest possible, so BIOQ lies in [0, 1].

    .. math::

        BIOQ = \\frac{\\sum_l \\kappa_l\\, w_l\\, l + l_b + V_{bonus}}{w_L\\, L + L + V_{bonus}}

    where level :math:`l` holds the p-values in :math:`(s / b^l, s / b^{l-1}]` while
    :math:`s / b^l` is not below the threshold, and the last level, :math:`L`, those down
    to 0; :math:`w_l = 1 + d\\,(l - 1)`; :math:`\\kappa_l` is the share of the terms in
    level :math:`l`; and :math:`l_b` is the level of the most significant term. With the
    defaults, :math:`s = 1`, :math:`b = 10`, :math:`d = 10`, a threshold of
    :math:`10^{-40}` and :math:`V_{bonus} = 10`, there are 41 levels, the last for the
    p-values up to :math:`10^{-40}`.

    Since most terms of an analysis are not significant, BIOQ is usually small, between
    :math:`10^{-5}` and :math:`10^{-3}`. Two options make it use more of its range: a
    larger ``threshold``, for fewer levels, and ``alpha``, to score only the terms below
    that significance, so that those that are not significant do not dilute the rest.

    .. code-block:: python

        from metagen.triclustering import Enrichment, Term, bioq

        terms = (Term("GO:1", "a", 1e-12), Term("GO:2", "b", 0.03), Term("GO:3", "c", 0.6))
        enrichment = Enrichment(terms, engine="example", version="", study_size=20, population_size=5000)
        print(round(bioq(enrichment), 6))                                    # 0.033653
        print(round(bioq(enrichment, threshold=1e-20, alpha=0.05), 6))       # 0.192968

    :param enrichment: The enrichment of the genes of the tricluster.
    :type enrichment: Enrichment
    :param bonus: :math:`V_{bonus}`, not negative, defaults to 10.
    :type bonus: float, optional
    :param adjusted: Whether to score the adjusted p-values, defaults to True; False scores
        those before the correction, when the engine gives them.
    :type adjusted: bool, optional
    :param threshold: The p-value below which every term falls in the last level, defaults
        to 1e-40.
    :type threshold: float, optional
    :param base: :math:`b`, how many times narrower each level is than the one before,
        greater than 1, defaults to 10.
    :type base: float, optional
    :param step: :math:`s`, the upper bound of the second level times the base, in (0, 1],
        defaults to 1.
    :type step: float, optional
    :param difference: :math:`d`, how much more each level weighs than the one before, not
        negative, defaults to 10.
    :type difference: float, optional
    :param alpha: If given, only the terms with a p-value below it are scored; None, the
        default, scores them all.
    :type alpha: float, optional
    :return: BIOQ; NaN if the enrichment has no terms, and 0 if it has terms but none is
        below ``alpha``.
    :rtype: float
    :raises ValueError: if ``adjusted=False`` and the engine gives no p-values before the
        correction, if a p-value is not in [0, 1], or if a parameter is out of its range.
    """
    # The bonus is 10, as TrLab scored (BIOQ.java) and as the values published with TRIQ
    # were computed: its smallest, 0.000728, is (1 + 1 + 10) / 16492 (metagen-auditoria/
    # trigen/fase5/informe_decision_bioq.md, section 4). With it, bioq reproduces the BIOQ
    # of TrLab exactly from its Ontologizer tables (fase5/informe_5a.md). TrLab's threshold,
    # base, step and difference were read from a file but had no effect, the levels being
    # built once before.
    # A p-value of 0 counts in the last level and can be the best term. TrLab dropped it
    # from the levels, and the bonus with it when it was the best (T-15, metagen-auditoria/
    # trigen/HALLAZGOS.md); none of its historical tables holds one.
    # threshold and alpha: measured in phase 5b-bis (fase5/informe_5b_bis.md). On 40 real
    # triclusters the median goes from 0.003 to 0.09 with threshold=1e-20 and alpha=0.05;
    # the score still grows with the number of genes, as any score of p-values does.
    if not bonus >= 0:
        raise ValueError(f"The bonus must not be negative: {bonus}.")
    if not (base > 1 and 0 < step <= 1 and difference >= 0 and 0 < threshold <= step / base):
        raise ValueError(f"The levels need base > 1, 0 < step <= 1, difference >= 0 and 0 < threshold <= step / base, "
                         f"not base={base}, step={step}, difference={difference}, threshold={threshold}.")
    if alpha is not None and not 0 < alpha <= 1:
        raise ValueError(f"alpha must lie in (0, 1], not {alpha}.")
    if adjusted:
        values = [term.p_adjusted for term in enrichment.terms]
    else:
        if any(term.p is None for term in enrichment.terms):
            raise ValueError(f"The engine {enrichment.engine} gives no p-values before the correction.")
        values = [float(term.p) for term in enrichment.terms if term.p is not None]
    if not all(0.0 <= value <= 1.0 for value in values):
        raise ValueError("The p-values of an enrichment must lie in [0, 1].")
    if not values:
        return math.nan
    if alpha is not None:
        values = [value for value in values if value < alpha]
        if not values:
            return 0.0
    bounds = _lower_bounds(float(threshold), float(base), float(step))
    last = len(bounds) + 1
    counts: Dict[int, int] = defaultdict(int)
    for value in values:
        if value <= step:                     # above the step a p-value falls in no level, but counts
            counts[_level(value, bounds)] += 1
    score = sum(count / len(values) * (1 + (level - 1) * difference) * level for level, count in counts.items())
    if min(values) <= step:
        score += _level(min(values), bounds)
    return (score + bonus) / ((1 + (last - 1) * difference) * last + last + bonus)


# --- purity --------------------------------------------------------------------------------

def purity(enrichment: Enrichment, alpha: float = 0.05) -> float:
    """
    The functional purity of a tricluster, from the enrichment of its genes: the largest
    share of its genes that a significant term annotates, beyond the share of the genes of
    the population it annotates,

    .. math::

        purity = \\max_{t:\\ p_t < \\alpha} \\left( \\frac{k_t}{n} - \\frac{K_t}{N} \\right)

    with :math:`k_t` of the :math:`n` genes of the tricluster and :math:`K_t` of the
    :math:`N` genes of the population annotated to the term :math:`t`. It estimates what
    share of the genes of the tricluster have a function in common, between 0, for genes
    with no significant term in common, and nearly 1, when all of them share a specific
    one. A term that annotates most genes counts for little even if all the genes of the
    tricluster have it. The p-value only decides which terms count, so the purity does not
    grow with the number of genes of the tricluster, and it reads the same from one
    organism or dataset to another.

    .. code-block:: python

        from metagen.triclustering import Enrichment, Term, purity

        terms = (Term("GO:1", "specific", 1e-9, study_count=12, population_count=40),
                 Term("GO:2", "general", 0.01, study_count=18, population_count=2500),
                 Term("GO:3", "not significant", 0.6, study_count=3, population_count=300))
        enrichment = Enrichment(terms, engine="example", version="", study_size=20, population_size=5000)
        print(purity(enrichment))                                  # 0.592

    :param enrichment: The enrichment of the genes of the tricluster.
    :type enrichment: Enrichment
    :param alpha: The significance below which a term counts, defaults to 0.05.
    :type alpha: float, optional
    :return: The purity; NaN if the enrichment has no terms, and 0 if none is significant.
    :rtype: float
    :raises ValueError: if the engine does not give how many genes each term annotates, or
        alpha is not in (0, 1].
    """
    # Reasoned and measured in phase 5b-bis (metagen-auditoria/trigen/fase5/
    # informe_5b_bis.md), not taken from the literature; its closest documented relative is
    # the Biological Homogeneity Index (Datta and Datta, BMC Bioinformatics 2006). On gene
    # sets built with a share f of the genes of one GO term and the rest at random, it
    # returns f whatever the size (0.22-0.24 for 0.25, 0.49-0.55 for 0.5, 0.73-0.75 for
    # 0.75, with 15, 50 and 150 genes), 0 for random sets, and the same for human, mouse
    # and yeast; BIOQ and any score of p-values grow with the number of genes.
    # The artificial root of LocalGO and of Ontologizer is not a function: left out.
    if not 0 < alpha <= 1:
        raise ValueError(f"alpha must lie in (0, 1], not {alpha}.")
    if not enrichment.terms:
        return math.nan
    if enrichment.study_size < 1 or enrichment.population_size < 1:
        raise ValueError("The purity needs the sizes of the study and of the population.")
    best = 0.0
    for term in enrichment.significant(alpha):
        if term.id == _ROOT:
            continue
        if term.study_count is None or term.population_count is None:
            raise ValueError(f"The engine {enrichment.engine} does not give how many genes each term annotates.")
        best = max(best, term.study_count / enrichment.study_size - term.population_count / enrichment.population_size)
    return best


# --- g:Profiler ----------------------------------------------------------------------------

_GPROFILER = "https://biit.cs.ut.ee/gprofiler/api/gost/profile/"


class GProfiler:
    """
    Enrichment with g:Profiler (https://biit.cs.ut.ee/gprofiler), a web service kept up to
    date with Ensembl and the Gene Ontology: every term that annotates a gene of the study,
    tested against the population given, with the correction of g:Profiler for the number
    of terms tested (``"g_SCS"``) or Bonferroni. The version of the annotations comes with
    every result. It needs a connection to the internet; :py:class:`LocalGO` computes
    without one.

    g:Profiler counts as the population only the genes of the population it can annotate,
    so its p-values differ from those of an engine that counts all of them.

    :param organism: The organism, in g:Profiler's names, such as ``"hsapiens"``,
        ``"mmusculus"`` or ``"scerevisiae"``; defaults to ``"hsapiens"``.
    :type organism: str, optional
    :param sources: The ontologies, defaults to the three of GO.
    :type sources: Sequence[str], optional
    :param correction: ``"bonferroni"``, the default, or g:Profiler's ``"g_SCS"``.
    :type correction: str, optional
    :param cache_dir: A folder to keep each answer in, so the same analysis is not asked
        again; None, the default, keeps nothing.
    :type cache_dir: str, optional
    :param timeout: Seconds to wait for an answer, defaults to 300.
    :type timeout: float, optional
    """

    def __init__(self, organism: str = "hsapiens", sources: Sequence[str] = ("GO:BP", "GO:MF", "GO:CC"),
                 correction: str = "bonferroni", cache_dir: Optional[str] = None, timeout: float = 300.0) -> None:
        if correction not in ("bonferroni", "g_SCS"):
            raise ValueError(f"correction must be 'bonferroni' or 'g_SCS', not {correction!r}.")
        if isinstance(sources, str):
            raise ValueError(f"sources must be a sequence of sources, such as ['GO:BP'], not the string {sources!r}.")
        self.organism = organism
        self.sources = tuple(sources)
        self.correction = correction
        self.cache_dir = cache_dir
        self.timeout = timeout

    def enrich(self, genes: Sequence[str], population: Sequence[str]) -> Enrichment:
        """
        The enrichment of some genes against a population.

        :param genes: The genes of the study.
        :type genes: Sequence[str]
        :param population: The genes of the population, such as all the genes of the data.
        :type population: Sequence[str]
        :return: The enrichment. Its sizes are those of the genes given; g:Profiler may
            recognize fewer.
        :rtype: Enrichment
        :raises ValueError: if a gene of the study is not in the population.
        :raises RuntimeError: if g:Profiler cannot be reached, rejects the request or
            answers something else than an analysis.
        """
        study, background = _study_and_population(genes, population)
        if not study:
            return Enrichment((), engine="g:Profiler", version="", study_size=0, population_size=len(background))
        # Sorted, so the same analysis is the same request whatever the order of the genes.
        request = {"organism": self.organism, "query": sorted(study), "sources": list(self.sources),
                   "user_threshold": 1.0, "all_results": True, "domain_scope": "custom",
                   "background": sorted(background), "significance_threshold_method": self.correction,
                   "no_evidences": True}
        answer = self._ask(request)
        terms = [Term(id=str(result["native"]), name=str(result["name"]), p_adjusted=float(result["p_value"]),
                      study_count=int(result["intersection_size"]), population_count=int(result["term_size"]))
                 for result in answer["result"] if result["intersection_size"] >= 1]
        terms.sort(key=_by_significance)
        return Enrichment(tuple(terms), engine="g:Profiler", version=str(answer["meta"]["version"]),
                          study_size=len(study), population_size=len(background))

    def _ask(self, request: Dict) -> Dict:
        body = json.dumps(request, sort_keys=True).encode("utf-8")
        path = None
        if self.cache_dir is not None:
            os.makedirs(self.cache_dir, exist_ok=True)
            path = os.path.join(self.cache_dir, f"gprofiler-{hashlib.sha256(body).hexdigest()}.json")
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as handle:
                        return _analysis(json.load(handle))
                except (ValueError, RuntimeError):
                    pass                      # an answer cut short or damaged: asked again below
        try:
            answer = _analysis(_post(_GPROFILER, body, self.timeout))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"g:Profiler rejected the request ({error.code} {error.reason}): {detail}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise RuntimeError(f"g:Profiler could not be reached: {error}. LocalGO computes without "
                               f"a connection.") from error
        except ValueError as error:           # an answer that is not JSON
            raise RuntimeError(f"g:Profiler answered something that is not an analysis: {error}") from error
        if path is not None:
            temporary = path + ".tmp"
            with open(temporary, "w", encoding="utf-8") as handle:
                json.dump(answer, handle)
            os.replace(temporary, path)
        return answer


def _analysis(answer: object) -> Dict:
    """The answer of g:Profiler, checked to be an analysis before it is used or kept."""
    try:
        if not isinstance(answer, dict):
            raise TypeError("the answer is not an object")
        results, version = answer["result"], answer["meta"]["version"]
        if not isinstance(results, list) or version is None:
            raise TypeError("the answer holds no results or no version")
        for result in results:
            float(result["p_value"]), int(result["intersection_size"]), int(result["term_size"])
            result["native"], result["name"]
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(f"g:Profiler answered something that is not an analysis: {error!r}") from error
    return answer


def _post(url: str, body: bytes, timeout: float) -> Dict:
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


# --- local --------------------------------------------------------------------------------

_ROOT = "GO:0000000"


class LocalGO:
    """
    Enrichment computed locally, without a connection, from an ontology file (``.obo``)
    and an annotation file (``.gaf``) of the organism, following Ontologizer's
    term-for-term analysis: the population is every gene given, annotated or not; each
    gene takes the terms annotated to it, by its symbol, and every term above them in the
    ontology, through any relation; every term that annotates a gene of the study is
    tested with a one-sided hypergeometric test; and Bonferroni multiplies by the number
    of terms tested, an artificial root over the three ontologies among them.

    The files have to be kept up to date by hand, since the Gene Ontology and its
    annotations change every month, and an analysis changes with them. The current ones
    are at https://current.geneontology.org: the ontology in ``ontology/go-basic.obo``
    and the annotations of each organism in ``annotations/``, for instance
    ``goa_human.gaf.gz``, to unzip before use. :py:class:`GProfiler` is kept up to date
    by its maintainers.

    :param obo: The ontology file.
    :type obo: str
    :param gaf: The annotation file, unzipped.
    :type gaf: str
    :param synonyms: Whether a gene that is not the symbol of any gene of the annotation
        file is also looked up by its identifier and by its synonyms, taking the gene only
        when a single one answers to the name; defaults to False. Datasets that name their
        genes by systematic names, such as those of yeast (``YAL001C``), need it.
    :type synonyms: bool, optional
    :raises ValueError: if the ontology file holds no terms, or the annotation file no
        annotation to them.
    """
    # The Ontologizer of TrLab also counted the NOT annotations as annotations, which the
    # current Ontologizer leaves out, as here; with them, and each name cut at its first
    # space, its 40 historical tables come out exact (T-16, metagen-auditoria/trigen/
    # HALLAZGOS.md). ontologizer_table reads those tables as they are.
    # How much an analysis changes with the files, measured on the 40 triclusters of phase
    # 5a (metagen-auditoria/trigen/fase5/informe_5a.md): from the files of 2024 to those of
    # 2026, the significant terms of the same analysis agree by 0.81 (Jaccard, median).

    def __init__(self, obo: str, gaf: str, synonyms: bool = False) -> None:
        self.obo = obo
        self.gaf = gaf
        self.synonyms = synonyms
        self._names, self._parents, alternatives, ontology_version = _read_obo(obo)
        if not self._parents:
            raise ValueError(f"{obo} holds no terms: is it an ontology in the OBO format?")
        self._annotations, self._other_names, annotation_version = _read_gaf(gaf, self._parents, alternatives)
        if not self._annotations:
            raise ValueError(f"{gaf} holds no annotation to the terms of {obo}: is it an annotation file in "
                             f"the GAF format, of that ontology?")
        self.version = f"{ontology_version}; {annotation_version}".strip("; ")
        self._above: Dict[str, Set[str]] = {}
        self._closure: Dict[str, Set[str]] = {}

    def enrich(self, genes: Sequence[str], population: Sequence[str]) -> Enrichment:
        """
        The enrichment of some genes against a population.

        :param genes: The genes of the study.
        :type genes: Sequence[str]
        :param population: The genes of the population, such as all the genes of the data.
        :type population: Sequence[str]
        :return: The enrichment.
        :rtype: Enrichment
        :raises ValueError: if a gene of the study is not in the population.
        """
        study, background = _study_and_population(genes, population)
        population_count: Dict[str, int] = defaultdict(int)
        for gene in background:
            for term in self._terms(gene):
                population_count[term] += 1
        study_count: Dict[str, int] = defaultdict(int)
        for gene in study:
            for term in self._terms(gene):
                study_count[term] += 1
        size, drawn = len(background), len(study)
        tested = len(study_count)
        terms = []
        for term, k in study_count.items():
            p = float(hypergeom.sf(k - 1, size, population_count[term], drawn))
            terms.append(Term(id=term, name=self._names.get(term, "root" if term == _ROOT else term),
                              p_adjusted=min(1.0, p * tested), p=p, study_count=k,
                              population_count=population_count[term]))
        terms.sort(key=_by_significance)
        return Enrichment(tuple(terms), engine="LocalGO", version=self.version, study_size=drawn,
                          population_size=size)

    def _terms(self, gene: str) -> Set[str]:
        if gene not in self._closure:
            closure: Set[str] = set()
            symbol = gene
            if self.synonyms and gene not in self._annotations:
                answering = self._other_names.get(gene, ())
                if len(answering) == 1:
                    symbol = next(iter(answering))
            for term in self._annotations.get(symbol, ()):
                closure |= self._upwards(term)
            if closure:
                closure.add(_ROOT)
            self._closure[gene] = closure
        return self._closure[gene]

    def _upwards(self, term: str) -> Set[str]:
        """The term and every term above it. Searched afresh for each term: with relations
        such as has_part the ontology holds cycles, and a closure kept halfway through one
        would be short."""
        if term not in self._above:
            found = {term}
            pending = [term]
            while pending:
                for parent in self._parents.get(pending.pop(), ()):
                    if parent not in found:
                        found.add(parent)
                        pending.append(parent)
            self._above[term] = found
        return self._above[term]


def _open_text(path: str):
    """A text file, read whatever its encoding; a zipped one is told apart first."""
    with open(path, "rb") as handle:
        if handle.read(2) == b"\x1f\x8b":
            raise ValueError(f"{path} is zipped: unzip it first.")
    return open(path, encoding="utf-8-sig", errors="replace")


def _read_obo(path: str) -> Tuple[Dict[str, str], Dict[str, Set[str]], Dict[str, str], str]:
    """The names of the terms, the terms right above each one, by any relation, the term
    each alternative identifier stands for, and the version. Obsolete terms are left out,
    and so is what a term names above it that the file does not hold."""
    names: Dict[str, str] = {}
    identifiers: Set[str] = set()
    parents: Dict[str, Set[str]] = defaultdict(set)
    alternatives: Dict[str, str] = {}
    obsolete: Set[str] = set()
    version = ""
    current: Optional[str] = None
    in_term = seen_stanza = False
    with _open_text(path) as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("["):
                in_term, seen_stanza, current = line == "[Term]", True, None
                continue
            key, separator, value = line.partition(":")
            if not separator:
                continue
            key, value = key.strip(), value.strip()
            if not in_term:
                if key == "data-version" and not seen_stanza:
                    version = "GO " + value
                continue
            if key == "id":
                current = value
                identifiers.add(value)
            elif current is None:
                continue
            elif key == "name":
                names[current] = value
            else:
                reference = value.split(" ! ")[0].split()       # without the trailing comment
                if key == "alt_id" and reference:
                    alternatives[reference[0]] = current
                elif key == "is_obsolete" and value.startswith("true"):
                    obsolete.add(current)
                elif key == "is_a" and reference:
                    parents[current].add(reference[0])
                elif key == "relationship" and len(reference) >= 2:
                    parents[current].add(reference[1])
    known = identifiers - obsolete
    above = {term: {parent for parent in parents.get(term, ()) if parent in known} for term in known}
    stand_for = {alternative: term for alternative, term in alternatives.items()
                 if term in known and alternative not in known}
    return names, above, stand_for, version


def _read_gaf(path: str, known: Dict[str, Set[str]],
              alternatives: Dict[str, str]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], str]:
    """The terms annotated to each gene symbol, leaving out NOT annotations and terms the
    ontology does not hold; the symbols that answer to each identifier and synonym; and
    the date of the file. An annotation to an alternative identifier is one to its term."""
    annotations: Dict[str, Set[str]] = defaultdict(set)
    other_names: Dict[str, Set[str]] = defaultdict(set)
    version = ""
    with _open_text(path) as handle:
        for line in handle:
            if line.startswith("!"):
                if not version and line.lower().startswith("!date-generated:"):
                    version = "annotations " + line.split(":", 1)[1].strip()
                continue
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) < 5 or "NOT" in fields[3].upper().split("|"):
                continue
            term = alternatives.get(fields[4], fields[4])
            if term in known:
                annotations[fields[2]].add(term)
                other_names[fields[1]].add(fields[2])
                if len(fields) > 10:
                    for synonym in fields[10].split("|"):
                        if synonym:
                            other_names[synonym].add(fields[2])
    return dict(annotations), dict(other_names), version


# --- Ontologizer tables ----------------------------------------------------------------------

def ontologizer_table(path: str) -> Enrichment:
    """
    Read a term-for-term table written by Ontologizer, such as those TrLab kept for each
    tricluster.

    :param path: The table.
    :type path: str
    :return: The enrichment it holds.
    :rtype: Enrichment
    :raises ValueError: if the file is not an Ontologizer table.
    """
    with open(path, encoding="utf-8", errors="replace") as handle:
        rows = [line.rstrip("\r\n").split("\t") for line in handle if line.strip()]
    header = rows[0] if rows else []
    expected = ["ID", "Pop.total", "Pop.term", "Study.total", "Study.term", "p", "p.adjusted"]
    if header[:7] != expected:
        raise ValueError(f"{path} is not an Ontologizer term-for-term table: its header is {header[:7]}.")
    name_column = header.index("name") if "name" in header else None
    terms = []
    try:
        for row in rows[1:]:
            name = row[name_column].strip('"') if name_column is not None and name_column < len(row) else row[0]
            terms.append(Term(id=row[0], name=name, p_adjusted=float(row[6]), p=float(row[5]),
                              study_count=int(row[4]), population_count=int(row[2])))
        study_size, population_size = (int(rows[1][3]), int(rows[1][1])) if len(rows) > 1 else (0, 0)
    except (IndexError, ValueError) as error:
        raise ValueError(f"{path} is not an Ontologizer term-for-term table: {error}") from None
    terms.sort(key=_by_significance)
    return Enrichment(tuple(terms), engine="Ontologizer", version=os.path.basename(path),
                      study_size=study_size, population_size=population_size)
