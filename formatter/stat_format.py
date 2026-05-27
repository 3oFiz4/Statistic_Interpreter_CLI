from assets.widgets.utils.formatter import (
    apply_rules,
    RuleContext,
    FormatRule,          # only needed if rules added at runtime
    TableFormattingConfig,
    ColumnConfig
)

def BuildStatFormat() -> TableFormattingConfig:
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
