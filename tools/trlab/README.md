# Converting from TrLab

`convert.py` turns the datasets and the results of TrLab, the Java application TriGen comes
from, into the formats of MetaGen. It only reads what it converts.

```bash
# Every dataset of a resources.xml, to a NetCDF file each, and their search sizes to sizes.json
python tools/trlab/convert.py datasets ~/TrLab/resources converted/

# Some of them, renaming genes (for instance, gene names a spreadsheet turned into dates)
python tools/trlab/convert.py datasets ~/TrLab/resources converted/ --only gse112660 --rename names.json

# A result, on the dataset it was found in
python tools/trlab/convert.py sol dev_0/dev_0.sol converted/gse112660.nc dev_0.json
```

`names.json` maps, for each dataset, a gene name to the one it should have:
`{"gse112660": {"March 1": "MARCHF1", "Septin 2": "SEPTIN2"}}`.

A converted dataset keeps every row, column and value TrLab read. The values TrLab read as
`NA` are missing in the file: `Cube.from_netcdf(path, drop_missing="genes")` drops the genes
that hold them. The smallest and largest sizes of each dataset go to `sizes.json`, since they
belong to a search and not to the data; they are the `min_sizes` and `max_sizes` of `TriGen`.

A converted result is a `TriGenResult` with the triclusters of the `.sol` file, the
configuration translated to the arguments of `TriGen` as closely as they go (the number of
triclusters, the generations, the population, the rates, the sizes, the fitness and its
weights), and every original property under `provenance["trlab"]`. `TriGenResult.trigen(cube)`
builds a MetaGen TriGen with that configuration, which is not the TrLab one: the operators of
the two differ.
