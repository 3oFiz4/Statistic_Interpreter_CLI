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

# 5.  Pre-built config  (edit / extend freely)
def build_default_config() -> TableFormattingConfig:
    cfg = TableFormattingConfig(
        stripe_even="",
        stripe_odd ="",
    )

    # ── Column display settings ──────────────────────────────────────────────
    cfg.columns = {
        "TICKER": ColumnConfig("TICKER", width=10),
        "PRICE" : ColumnConfig("PRICE",  width=12, align="right"),
        "CHANGE": ColumnConfig("CHANGE", width=10, align="right"),
        "VOLUME": ColumnConfig("VOLUME", width=14, align="right"),
        "SECTOR": ColumnConfig("SECTOR", width=16),
        "PE"    : ColumnConfig("PE",     width=8,  align="right"),
        "DIV"   : ColumnConfig("DIV",    width=8,  align="right",
                               default_fmt=lambda ctx: f"[cyan]{ctx.display}[/cyan]"),
        "NOTES" : ColumnConfig("NOTES",  width=22,
                               default_fmt=lambda ctx: f"[dim italic]{ctx.display}[/dim italic]"),
        "HIDDEN": ColumnConfig("HIDDEN", hidden=True),
    }

    # ── Optional callable row filter ─────────────────────────────────────────
    # Show only rows where PRICE > 0  (hides delisted / null entries)
    cfg.row_filter = lambda idx, row, data: float(row.get("PRICE") or 0) >= 0

    # ── Rules ────────────────────────────────────────────────────────────────
    cfg.rules = [
        ### this is my market stock color.. this is an example how its used. """
         FormatRule(
             name      = "Empty cell placeholder",
             condition = lambda ctx: ctx.cell in (None, "", "N/A"),
             action    = lambda ctx: "[dim #555555]—[/dim #555555]",
             target    = "self",
             priority  = 5,
         ),

         # value that changes by itself

         FormatRule(
             name      = "Self: negative number",
             condition = lambda ctx: ctx.numeric() < 0,
             action    = lambda ctx: f"[italic red]{ctx.display}[/italic red]",
             priority  = 10,
         ),
         FormatRule(
             name      = "Self: zero",
             condition = lambda ctx: ctx.numeric() == 0 and str(ctx.cell).strip() not in ("", "N/A"),
             action    = lambda ctx: f"[dim #888888]{ctx.display}[/dim #888888]",
             priority  = 11,
         ),
         FormatRule(
             name      = "Self: URL in cell",
             condition = lambda ctx: str(ctx.cell or "").startswith("http"),
             action    = lambda ctx: f"[underline blue]{ctx.display}[/underline blue]",
             priority  = 12,
         ),
         FormatRule(
             name      = "Self: percentage string",
             condition = lambda ctx: str(ctx.cell or "").endswith("%"),
             action    = lambda ctx: f"[#00cfff]{ctx.display}[/#00cfff]",
             priority  = 13,
         ),
         FormatRule(
             name      = "Self: very large number (>=1 M)",
             condition = lambda ctx: ctx.numeric() >= 10_000_000_000,
             action    = lambda ctx: f"[bold #00ff00]{ctx.display}[/bold #00ff00]",
             priority  = 14,
         ),

         # column wide format

         FormatRule(
             name      = "PRICE: penny stock (<5)",
             condition = lambda ctx: ctx.numeric("PRICE") < 5,
             action    = lambda ctx: f"[dim red]{ctx.display}[/dim red]",
             target    = "col.PRICE",
             priority  = 20,
         ),
         FormatRule(
             name      = "PRICE: mid-range (5–499)",
             condition = lambda ctx: 5 <= ctx.numeric("PRICE") < 500,
             action    = lambda ctx: f"[#00cfff]{ctx.display}[/#00cfff]",
             target    = "col.PRICE",
             priority  = 21,
         ),
         FormatRule(
             name      = "PRICE: blue-chip (>=500)",
             condition = lambda ctx: ctx.numeric("PRICE") >= 50000000,
             action    = lambda ctx: f"[bold #ffd700]{ctx.display}[/bold #ffd700]",
             target    = "col.PRICE",
             priority  = 22,
         ),
         FormatRule(
             name      = "PE: value (<10)",
             condition = lambda ctx: 0 < ctx.numeric("PE") < 10,
             action    = lambda ctx: f"[bold cyan]{ctx.display}[/bold cyan]",
             target    = "col.PE",
             priority  = 25,
         ),
         FormatRule(
             name      = "PE: fair (10–40)",
             condition = lambda ctx: 10 <= ctx.numeric("PE") <= 40,
             action    = lambda ctx: f"[green]{ctx.display}[/green]",
             target    = "col.PE",
             priority  = 26,
         ),
         FormatRule(
             name      = "PE: overvalued (>40)",
             condition = lambda ctx: ctx.numeric("PE") > 40,
             action    = lambda ctx: f"[bold red]{ctx.display}[/bold red]",
             target    = "col.PE",
             priority  = 27,
         ),
         FormatRule(
             name      = "VOLUME: heatmap by rank",
             condition = lambda ctx: True,
             action    = lambda ctx: (
                 f"[bold bright_white]{ctx.display}[/bold bright_white]" if ctx.rank("VOLUME") >= 0.9 else
                 f"[white]{ctx.display}[/white]"                          if ctx.rank("VOLUME") >= 0.6 else
                 f"[#888888]{ctx.display}[/#888888]"
             ),
             target    = "col.VOLUME",
             priority  = 30,
         ),
         FormatRule(
             name      = "SECTOR: keyword colouring",
             condition = lambda ctx: True,
             action    = lambda ctx: (
                 f"[bold #7b68ee]{ctx.display}[/bold #7b68ee]" if "Tech"    in str(ctx.cell) else
                 f"[bold #ff8c00]{ctx.display}[/bold #ff8c00]" if "Energy"  in str(ctx.cell) else
                 f"[bold #3cb371]{ctx.display}[/bold #3cb371]" if "Health"  in str(ctx.cell) else
                 f"[bold #cd853f]{ctx.display}[/bold #cd853f]" if "Finance" in str(ctx.cell) else
                 ctx.display
             ),
             target    = "col.SECTOR",
             priority  = 35,
         ),

         # ── ROW-column cross rules (condition reads sibling, rewrites another) ─

         FormatRule(
             name      = "CHANGE+: green TICKER",
             condition = lambda ctx: ctx.numeric("CHANGE") > 0,
             action    = lambda ctx: f"[bold green]{ctx.display}[/bold green]",
             target    = "row.TICKER",
             priority  = 40,
         ),
         FormatRule(
             name      = "CHANGE-: red TICKER",
             condition = lambda ctx: ctx.numeric("CHANGE") < 0,
             action    = lambda ctx: f"[bold red]{ctx.display}[/bold red]",
             target    = "row.TICKER",
             priority  = 41,
         ),
         FormatRule(
             name      = "CHANGE==0: dim TICKER",
             condition = lambda ctx: ctx.numeric("CHANGE") == 0,
             action    = lambda ctx: f"[dim]{ctx.display}[/dim]",
             target    = "row.TICKER",
             priority  = 42,
         ),
         FormatRule(
             name      = "CHANGE cell: prefix + / − and colour",
             condition = lambda ctx: True,
             action    = lambda ctx: (
                 f"[green]+{ctx.display}[/green]" if ctx.numeric("CHANGE") > 0 else
                 f"[red]{ctx.display}[/red]"       if ctx.numeric("CHANGE") < 0 else
                 f"[dim]{ctx.display}[/dim]"
             ),
             target    = "row.CHANGE",
             priority  = 43,
         ),

         # ── ROW-WIDE rules ───────────────────────────────────────────────────

         FormatRule(
             name      = "HALTED: dim entire row",
             condition = lambda ctx: str(ctx.row.get("NOTES", "")).startswith("HALTED"),
             action    = lambda ctx: f"[dim #666666]{ctx.display}[/dim #666666]",
             target    = "row.*",
             priority  = 50,
             stop_on_hit=True,
         ),
         FormatRule(
             name      = "Crash day: CHANGE<=-10 → red row",
             condition = lambda ctx: ctx.numeric("CHANGE") <= -10,
             action    = lambda ctx: f"[bold red]{ctx.display}[/bold red]",
             target    = "row.*",
             priority  = 51,
             stop_on_hit=True,
         ),
         FormatRule(
             name      = "Big mover: CHANGE>=10 → green row",
             condition = lambda ctx: ctx.numeric("CHANGE") >= 10,
             action    = lambda ctx: f"[bold green on #001a00]{ctx.display}[/bold green on #001a00]",
             target    = "row.*",
             priority  = 52,
             stop_on_hit=True,
         ),

         # ── Multi-column compound conditions ─────────────────────────────────

         FormatRule(
             name      = "High volume + big gain → gold TICKER",
             condition = lambda ctx: (
                 ctx.numeric("VOLUME") > 200_000 and
                 ctx.numeric("CHANGE") > 5
             ),
             action    = lambda ctx: (
                 f"[bold #ffd700 on #1a3300]{ctx.display}[/bold #ffd700 on #1a3300]"
             ),
             target    = "row.TICKER",
             priority  = 45,
             stop_on_hit=True,
         ),
         FormatRule(
             name      = "WATCHLIST underline",
             condition = lambda ctx: "WATCH" in str(ctx.row.get("NOTES", "")),
             action    = lambda ctx: f"[bold cyan underline]{ctx.display}[/bold cyan underline]",
             target    = "row.TICKER",
             priority  = 60,
         ),
         FormatRule(
             name      = "Earnings week: highlight NOTES",
             condition = lambda ctx: "EARNINGS" in str(ctx.row.get("NOTES", "")),
             action    = lambda ctx: f"[bold yellow italic]{ctx.display}[/bold yellow italic]",
             target    = "row.NOTES",
             priority  = 61,
         ),

         # ── Fully custom callable target  (multi-column lambda) ──────────────

         FormatRule(
             name      = "Top 10% VOLUME: highlight VOLUME + TICKER both",
             condition = lambda ctx: ctx.rank("VOLUME") >= 0.90,
             action    = lambda ctx: f"[bold bright_white underline]{ctx.display}[/bold bright_white underline]",
             # target is a callable — applies to TICKER and VOLUME columns only
             target    = lambda ctx: ctx.col in ("TICKER", "VOLUME"),
             priority  = 70,
         ),
         FormatRule(
             name      = "Odd row + low PE: teal PRICE",
             condition = lambda ctx: ctx.idx % 2 != 0 and 0 < ctx.numeric("PE") < 15,
             action    = lambda ctx: f"[bold #20b2aa]{ctx.display}[/bold #20b2aa]",
             target    = lambda ctx: ctx.col == "PRICE",
             priority  = 75,
         ),

         # ── Regex-based ──────────────────────────────────────────────────────

         FormatRule(
             name      = "TICKER: matches known index components",
             condition = lambda ctx: ctx.matches(r"^(AAPL|MSFT|GOOG|AMZN|NVDA)$", "TICKER"),
             action    = lambda ctx: f"[bold #e0e0ff]{ctx.display}[/bold #e0e0ff]",
             target    = "row.TICKER",
             priority  = 80,
         ),
         FormatRule(
             name      = "NOTES: flag any risk keywords",
             condition = lambda ctx: ctx.matches(
                 r"\b(RISK|ALERT|WARN|MARGIN CALL|DELISTED)\b",
                 "NOTES",
                 flags=re.IGNORECASE,
             ),
             action    = lambda ctx: f"[bold red blink]{ctx.display}[/bold red blink]",
             target    = "row.NOTES",
             priority  = 85,
         ),

         # ── Dataset-aware: colour by deviation from column mean ───────────────

         FormatRule(
             name      = "PRICE: above dataset mean → bright",
             condition = lambda ctx: (
                 (vals := [float(v) for v in ctx.col_values("PRICE") if v is not None])
                 and ctx.numeric("PRICE") > (sum(vals) / len(vals))
             ),
             action    = lambda ctx: f"[bright_white]{ctx.display}[/bright_white]",
             target    = "col.PRICE",
             priority  = 23,
         ),
    ]

    return cfg

def build_stats_config() -> TableFormattingConfig:
    """
    Formatting config tailored for the statistics results table.

    Row dict shape the rule engine sees:
        {
            "key"   : "column_name",
            "level" : "Metric" | "Ordinal" | "Nominal",
            <stat>  : raw Python value (int / float / None),
            ...     : one key per selected stat
        }
    """
    cfg = TableFormattingConfig(
        # Incase needed..
        stripe_even="",
        stripe_odd ="",
    )

    cfg.columns = {
        "key"   : ColumnConfig("key",   width=24, align="left"),
        "level" : ColumnConfig("level", width=10, align="center"),
    }

    cfg.rules = [

        # ── KEY column ───────────────────────────────────────────────────────

        FormatRule(
            name      = "Key: bold white",
            condition = lambda ctx: True,
            action    = lambda ctx: f"[bold white]{ctx.display}[/bold white]",
            target    = "col.key",
            priority  = 10,
        ),

        # ── LEVEL column: colour by measurement type ─────────────────────────

        FormatRule(
            name      = "Level: Metric → blue",
            condition = lambda ctx: ctx.row.get("level") == "Metric",
            action    = lambda ctx: f"[bold #4fc3f7]{ctx.display}[/bold #4fc3f7]",
            target    = "col.level",
            priority  = 20,
        ),
        FormatRule(
            name      = "Level: Ordinal → amber",
            condition = lambda ctx: ctx.row.get("level") == "Ordinal",
            action    = lambda ctx: f"[bold #ffb74d]{ctx.display}[/bold #ffb74d]",
            target    = "col.level",
            priority  = 21,
        ),
        FormatRule(
            name      = "Level: Nominal → green",
            condition = lambda ctx: ctx.row.get("level") == "Nominal",
            action    = lambda ctx: f"[bold #81c784]{ctx.display}[/bold #81c784]",
            target    = "col.level",
            priority  = 22,
        ),

        # ── NULL / missing values ─────────────────────────────────────────────

        FormatRule(
            name      = "Null placeholder",
            condition = lambda ctx: ctx.cell is None,
            action    = lambda ctx: "[dim #555555]—[/dim #555555]",
            priority  = 5,
        ),

        # ── Generic numeric stat cells ────────────────────────────────────────

        FormatRule(
            name      = "Stat: zero",
            condition = lambda ctx: ctx.cell not in (None, "") and ctx.numeric() == 0,
            action    = lambda ctx: f"[dim #888888]{ctx.display}[/dim #888888]",
            priority  = 30,
        ),
        FormatRule(
            name      = "Stat: negative value",
            condition = lambda ctx: ctx.cell not in (None, "") and ctx.numeric() < 0,
            action    = lambda ctx: f"[italic red]{ctx.display}[/italic red]",
            priority  = 31,
        ),
        FormatRule(
            name      = "Stat: very large (>= 1 M)",
            condition = lambda ctx: ctx.cell not in (None, "") and ctx.numeric() >= 1_000_000,
            action    = lambda ctx: f"[bold #ffd700]{ctx.display}[/bold #ffd700]",
            priority  = 32,
        ),

        # ── P-value specific (column key must be named "p_value" or "p-value") ─

        FormatRule(
            name      = "P-value: significant (< 0.05)",
            condition = lambda ctx: (
                ctx.col.lower().replace("-", "_") == "p_value"
                and ctx.cell is not None
                and ctx.numeric() < 0.05
            ),
            action    = lambda ctx: f"[bold green]{ctx.display}[/bold green]",
            priority  = 40,
        ),
        FormatRule(
            name      = "P-value: marginal (0.05 – 0.10)",
            condition = lambda ctx: (
                ctx.col.lower().replace("-", "_") == "p_value"
                and ctx.cell is not None
                and 0.05 <= ctx.numeric() < 0.10
            ),
            action    = lambda ctx: f"[yellow]{ctx.display}[/yellow]",
            priority  = 41,
        ),
        FormatRule(
            name      = "P-value: not significant (>= 0.10)",
            condition = lambda ctx: (
                ctx.col.lower().replace("-", "_") == "p_value"
                and ctx.cell is not None
                and ctx.numeric() >= 0.10
            ),
            action    = lambda ctx: f"[dim red]{ctx.display}[/dim red]",
            priority  = 42,
        ),

        # ── Rank-based heatmap: top 10% of any numeric stat → bright ─────────

        FormatRule(
            name      = "Stat: top 10% in column → bright white",
            condition = lambda ctx: (
                ctx.col not in ("key", "level")
                and ctx.cell is not None
                and ctx.rank(ctx.col) >= 0.90
            ),
            action    = lambda ctx: f"[bold bright_white]{ctx.display}[/bold bright_white]",
            priority  = 50,
        ),

        # ── Entire row dim if key starts with underscore (internal/hidden key) ─

        FormatRule(
            name      = "Internal key: dim entire row",
            condition = lambda ctx: str(ctx.row.get("key", "")).startswith("_"),
            action    = lambda ctx: f"[dim #666666]{ctx.display}[/dim #666666]",
            target    = "row.*",
            priority  = 60,
            stop_on_hit=True,
        ),

        # ── Metric rows: colour count / mean / std differently ────────────────

        FormatRule(
            name      = "Mean: blue tint on Metric rows",
            condition = lambda ctx: (
                ctx.col.lower() == "mean"
                and ctx.row.get("level") == "Metric"
                and ctx.cell is not None
            ),
            action    = lambda ctx: f"[#80cbc4]{ctx.display}[/#80cbc4]",
            priority  = 70,
        ),
        FormatRule(
            name      = "Std: orange tint on Metric rows",
            condition = lambda ctx: (
                ctx.col.lower() in ("std", "std_dev", "std dev")
                and ctx.row.get("level") == "Metric"
                and ctx.cell is not None
            ),
            action    = lambda ctx: f"[#ffcc80]{ctx.display}[/#ffcc80]",
            priority  = 71,
        ),
        FormatRule(
            name      = "Count: always dim grey",
            condition = lambda ctx: ctx.col.lower() == "count" and ctx.cell is not None,
            action    = lambda ctx: f"[#aaaaaa]{ctx.display}[/#aaaaaa]",
            priority  = 72,
        ),
    ]

    return cfg

# 6.  Drop-in _populate_table
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
