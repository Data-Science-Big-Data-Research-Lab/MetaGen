from typing import Final

REAL: Final = "REAL"
INTEGER: Final = "INTEGER"
CATEGORICAL: Final = "CATEGORICAL"
LAYER: Final = "LAYER"
VECTOR: Final = "VECTOR"
BASIC: Final = [INTEGER, REAL, CATEGORICAL]
NUMERICAL: Final = [INTEGER, REAL]

def valid_type(check_type):
    if check_type not in BASIC and check_type is not LAYER and check_type is not VECTOR:
        raise ValueError(check_type + " is not a valid type")
