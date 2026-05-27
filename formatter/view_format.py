from assets.widgets.utils.formatter import (
    apply_rules,
    RuleContext,
    FormatRule,          # only needed if rules added at runtime
    TableFormattingConfig,
    ColumnConfig
)

def BuildViewFormat() -> TableFormattingConfig:
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
        ### this is my market stock color.. this is an example how its used! idk how yours look like, but put it in here before using"""
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
