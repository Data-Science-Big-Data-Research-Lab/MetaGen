.. include:: ../aliases.rst

Triclustering
=============

.. autoclass:: metagen.triclustering.Cube
    :members:

.. autofunction:: metagen.triclustering.data.read_netcdf

.. autofunction:: metagen.triclustering.data.write_netcdf

.. autofunction:: metagen.triclustering.data.netcdf_attributes

.. autofunction:: metagen.triclustering.data.read_long

.. autofunction:: metagen.triclustering.data.read_slices

.. autofunction:: metagen.triclustering.data.read_gds

.. autofunction:: metagen.triclustering.data.fetch_gds

.. autofunction:: metagen.triclustering.data.drop_genes

.. autofunction:: metagen.triclustering.data.collapse_genes

.. autofunction:: metagen.triclustering.data.rename_genes

.. autofunction:: metagen.triclustering.data.check

.. autoclass:: metagen.triclustering.Tricluster
    :members: size, check, labels, from_solution

.. autofunction:: metagen.triclustering.msr3d

.. autofunction:: metagen.triclustering.msl

.. autofunction:: metagen.triclustering.lsl

.. autofunction:: metagen.triclustering.grq

.. autofunction:: metagen.triclustering.peq

.. autofunction:: metagen.triclustering.spq

.. autofunction:: metagen.triclustering.triq

.. autofunction:: metagen.triclustering.bioq

.. autofunction:: metagen.triclustering.purity

.. autofunction:: metagen.triclustering.enrich

.. autoclass:: metagen.triclustering.GProfiler
    :members: enrich

.. autoclass:: metagen.triclustering.LocalGO
    :members: enrich

.. autofunction:: metagen.triclustering.ontologizer_table

.. autoclass:: metagen.triclustering.Enrichment
    :members: significant

.. autoclass:: metagen.triclustering.Term

.. autoclass:: metagen.triclustering.EnrichmentProvider
    :members: enrich

.. autofunction:: metagen.triclustering.plant

.. autofunction:: metagen.triclustering.cell_jaccard

.. autofunction:: metagen.triclustering.cell_recall

.. autofunction:: metagen.triclustering.cell_precision

.. autofunction:: metagen.triclustering.coordinate_jaccard

.. autofunction:: metagen.triclustering.coordinate_recall

.. autofunction:: metagen.triclustering.recovery

.. autofunction:: metagen.triclustering.relevance
