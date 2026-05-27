from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Context object passed into every callable
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RuleContext:
    """
    Everything a rule could ever need.

    Attributes
    ----------
    row         Full row dict  {"TICKER": "AAPL", "VOLUME": 312000, ...}
    col         Column key of the cell currently being rendered  "TICKER"
    cell        Raw Python value from self.data  (int / float / str / None)
    display     Rich-markup string so far (mutated by previous rules)
    idx         Zero-based row index into self.data
    display_idx 1-based label shown in the entry column
    all_data    Reference to the full self.data list (read-only intended)
    col_keys    Ordered list of visible column keys
    """
    row         : dict
    col         : str
    cell        : Any
    display     : str
    idx         : int
    display_idx : int
    all_data    : list
    col_keys    : list[str]

    # ── Convenience helpers callable authors can use inside lambdas ──────────
    def get(self, col: str, default: Any = "") -> Any:
        """Shorthand for ctx.row.get(col, default)."""
        return self.row.get(col, default)

    def numeric(self, col: str | None = None, default: float = 0.0) -> float:
        """
        Safely coerce a column value (or the current cell) to float.
        Returns `default` if conversion fails.
        """
        raw = self.row.get(col, "") if col else self.cell
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    def matches(self, pattern: str, col: str | None = None, flags: int = 0) -> bool:
        """Regex match against a column value or the current cell."""
        raw = str(self.row.get(col, "") if col else (self.cell or ""))
        return bool(re.search(pattern, raw, flags))

    def cell_str(self) -> str:
        """Current cell as a plain string (strips Rich markup from display)."""
        return re.sub(r"\[.*?\]", "", self.display)

    def col_values(self, col: str) -> list[Any]:
        """All values in a column across the whole dataset (for ranking etc.)."""
        return [row.get(col) for row in self.all_data if isinstance(row, dict)]

    def rank(self, col: str) -> float:
        """
        Percentile rank of this row's value in `col` (0.0 = lowest, 1.0 = highest).
        Useful for heatmap-style colouring.
        """
        vals = [v for v in self.col_values(col) if v is not None]
        try:
            nums  = sorted(float(v) for v in vals)
            mine  = float(self.row.get(col, 0))
            below = sum(1 for v in nums if v < mine)
            return below / len(nums) if nums else 0.0
        except (TypeError, ValueError):
            return 0.0


# 2.  Data structures
ConditionFn = Callable[[RuleContext], bool]
ActionFn    = Callable[[RuleContext], str]
TargetFn    = Callable[[RuleContext], bool]
@dataclass
class FormatRule:
    """
    One formatting rule.

    Parameters
    ----------
    name        Human-readable label (shown in config panels / debug logs).
    condition   Callable  (ctx) -> bool   — any Python expression.
    action      Callable  (ctx) -> str    — returns the final Rich markup string.
    target      WHERE to apply the action.
                  str shorthand  : "self" | "row.*" | "row.COL" | "col.COL"
                  callable       : (ctx) -> bool   — full control
    enabled     Toggle without deleting.
    priority    Lower = applied first.  Later rules receive already-mutated ctx.display.
    stop_on_hit No further rules evaluated for this cell after this fires.
    """
    name        : str
    condition   : ConditionFn
    action      : ActionFn
    target      : str | TargetFn = "self"
    enabled     : bool           = True
    priority    : int            = 100
    stop_on_hit : bool           = False


@dataclass
class ColumnConfig:
    """Static per-column display settings."""
    key        : str
    label      : str  | None          = None
    width      : int  | None          = None
    hidden     : bool                 = False
    align      : str                  = "left"
    # Always-on transform — receives ctx, returns Rich string
    default_fmt: ActionFn | None      = None


@dataclass
class TableFormattingConfig:
    rules              : list[FormatRule]        = field(default_factory=list)
    columns            : dict[str, ColumnConfig] = field(default_factory=dict)
    hidden_row_indices : set[int]                = field(default_factory=set)
    # Callable row filter: (idx, row_dict, all_data) -> bool  (True = show)
    row_filter         : Callable[[int, dict, list], bool] | None = None
    stripe_even        : str | None              = None
    stripe_odd         : str | None              = None

# 3.  Target resolver
def _target_applies(target: str | TargetFn, ctx: RuleContext) -> bool:
    """Return True if the rule's action should be applied to this cell."""

    if callable(target):
        return target(ctx)

    if target in ("self", "cell"):
        return True

    if target == "row.*":
        return True

    if target.startswith("row."):
        return ctx.col == target[4:]

    if target.startswith("col."):
        return ctx.col == target[4:]

    return False

# 4.  Rule engine
def apply_rules(
    rules      : list[FormatRule],
    row        : dict,
    col        : str,
    cell       : Any,
    idx        : int,
    display_idx: int,
    all_data   : list,
    col_keys   : list[str],
) -> str:
    """
    Run every enabled rule (sorted by priority) against a single cell.
    Returns the final Rich-markup string.
    """
    display = str(cell) if cell is not None else ""

    for rule in sorted(rules, key=lambda r: r.priority):
        if not rule.enabled:
            continue

        ctx = RuleContext(
            row=row, col=col, cell=cell, display=display,
            idx=idx, display_idx=display_idx,
            all_data=all_data, col_keys=col_keys,
        )

        # ── Condition gate ────────────────────────────────────────────────────
        try:
            fired = rule.condition(ctx)
        except Exception:
            fired = False

        if not fired:
            continue

        # ── Target gate ───────────────────────────────────────────────────────
        if not _target_applies(rule.target, ctx):
            if rule.stop_on_hit:
                break
            continue

        # ── Apply action ──────────────────────────────────────────────────────
        try:
            display = rule.action(ctx)
        except Exception:
            pass                          # bad action → keep current display

        if rule.stop_on_hit:
            break

    return display

# 5.  Drop-in _populate_table
def make_populate_table(cfg: TableFormattingConfig):
    """
    Returns a _populate_table method wired to *cfg*.

    Bind it in your App/Screen:
        self._populate_table = make_populate_table(cfg).__get__(self, type(self))
    """
    def _populate_table(self) -> None:
        from rich.text import Text
        from textual.widgets import DataTable

        table = self.query_one("#json-table", DataTable)
        table.clear(columns=True)

        if not self.data:
            self._update_status("No data to display")
            return

        # ── Column list ──────────────────────────────────────────────────────
        if not self.columns:
            self.columns = ["entry"]
            for item in self.data:
                if isinstance(item, dict):
                    for key in item.keys():
                        if key not in self.columns:
                            self.columns.append(key)

        cfg_hidden   = {k for k, v in cfg.columns.items() if v.hidden}
        all_hidden   = self.hidden_columns | cfg_hidden
        visible_cols = [c for c in self.columns if c not in all_hidden or c == "entry"]

        # ── Add columns ──────────────────────────────────────────────────────
        for col in visible_cols:
            if col in all_hidden:
                continue
            col_cfg = cfg.columns.get(col)
            label   = col_cfg.label if col_cfg and col_cfg.label else col.upper()
            width   = self.column_widths.get(col) or (col_cfg.width if col_cfg else None)
            table.add_column(label, key=col, **({"width": width} if width else {}))

        sorted_rules = sorted(cfg.rules, key=lambda r: r.priority)

        # ── Add rows ─────────────────────────────────────────────────────────
        for idx, item in enumerate(self.data):
            if idx in self.hidden_rows:
                continue
            if idx in cfg.hidden_row_indices:
                continue

            row_dict = item if isinstance(item, dict) else {}

            # Callable row filter
            if cfg.row_filter and not cfg.row_filter(idx, row_dict, self.data):
                continue

            display_idx = idx + 1

            # Zebra stripe
            stripe = (
                cfg.stripe_even if display_idx % 2 == 0 and cfg.stripe_even else
                cfg.stripe_odd  if display_idx % 2 != 0 and cfg.stripe_odd  else
                ""
            )

            entry = Text(str(display_idx), style="#888888")
            if stripe:
                entry.stylize(stripe)
            row_data = [entry]

            for col in visible_cols[1:]:
                raw   = row_dict.get(col) if row_dict else None
                start = str(raw) if raw is not None else ""

                # Always-on column default format
                col_cfg = cfg.columns.get(col)
                if col_cfg and col_cfg.default_fmt:
                    seed_ctx = RuleContext(
                        row=row_dict, col=col, cell=raw, display=start,
                        idx=idx, display_idx=display_idx,
                        all_data=self.data, col_keys=visible_cols,
                    )
                    try:
                        start = col_cfg.default_fmt(seed_ctx)
                    except Exception:
                        pass

                # Rule engine
                final = apply_rules(
                    rules=sorted_rules, row=row_dict, col=col, cell=raw,
                    idx=idx, display_idx=display_idx,
                    all_data=self.data, col_keys=visible_cols,
                )

                # Prefer rule output when it differs from the raw value
                display_str = final if final != str(raw or "") else start

                # Zebra stripe background if no explicit background in markup
# ✅ AFTER — build Text first, then stylize the background separately
                cell_text = Text.from_markup(display_str)
                entry = Text(str(display_idx), style="#888888")
                if stripe:
                    entry.stylize(stripe)
                    row_data = [entry]
                    cell_text.stylize(stripe)
                row_data.append(cell_text)

            table.add_row(*row_data, key=str(display_idx))

        table.focus()

    return _populate_table
