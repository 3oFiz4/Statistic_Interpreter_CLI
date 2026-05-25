from typing import Any, Dict, List, Optional, Set, Tuple, Union
import copy

#> Clipboard & undo helpers
class Clipboard:
    """Clipboard process, holds one cell, one row, or many rows"""

    def __init__(self) -> None:
        self.cell_value: Optional[str]          = None
        self.row_data:   Optional[Dict]         = None
        self.rows_data:  Optional[List[Dict]]   = None
        self.mode:       str                    = "empty"   # "cell" | "row" | "rows" | "cut_row"
        self._cut_index: Optional[int]          = None      # row index that was "cut"

    # ------------------------------------------------------------------
    def copy_cell(self, value: str) -> None:
        self.cell_value = value
        self.mode       = "cell"

    def copy_row(self, row: Dict, cut: bool = False, index: int | None = None) -> None:
        self.row_data   = copy.deepcopy(row)
        self.mode       = "cut_row" if cut else "row"
        self._cut_index = index if cut else None

    def copy_rows(self, rows: List[Dict]) -> None:
        self.rows_data = copy.deepcopy(rows)
        self.mode      = "rows"

    #> attribute. access via Clipboard.has_cell/has_row...
    @property
    def has_cell(self)  -> bool: return self.mode == "cell"
    @property
    def has_row(self)   -> bool: return self.mode in ("row", "cut_row")
    @property
    def has_cut_row(self) -> bool: return self.mode == "cut_row"
    @property
    def cut_index(self) -> int | None: return self._cut_index

    def clear(self) -> None:
        self.__init__()
