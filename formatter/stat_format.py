from assets.widgets.utils.formatter import (
    apply_rules,
    RuleContext,
    FormatRule,  # only needed if rules added at runtime
    TableFormattingConfig,
    ColumnConfig,
)
from assets.services.statistics.statistics_engine import StatisticsEngine
import ast, math


# reads format_mean
def fMean(ctx) -> str:
    # everytime a variable is init, ensure they are in FLOAT type first..
    # feel free to round it too.
    value = round(float(ctx.display), 3)
    std_dev = float(ctx.numeric("stdv"))
    skewness = float(ctx.numeric("skew"))
    if not std_dev or std_dev == 0:
        return f"[green]{value}[/]"
    if skewness > 1.0:
        # Highly skewed (Massive outliers / Heavy distortion)
        return f"[red]{value}[/]"
    elif skewness > 0.5:
        # Moderately skewed (Slight skew)
        return f"[yellow]{value} [/]"
    else:
        # Fairly symmetrical (Evenly distributed)
        return f"[green]{value}[/]"


# TODO: Find a way to communicatet between DataTable (already processed by StatEngine) to communicate with Format
# TODO: Doing ctx.numeric("ABC") when ABC does not shown in DataTable resulting in 0
# TODO: this is an ez task... i just dont have more time to do it today.
def fMedian(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        value = round(float(ctx.display), 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("n")))
    except (TypeError, ValueError):
        count = None

    try:
        stdv = float(ctx.numeric("stdv"))
    except (TypeError, ValueError):
        stdv = None

    try:
        skew = abs(float(ctx.numeric("skew")))
    except (TypeError, ValueError):
        skew = None

    try:
        outlier_count = int(float(ctx.numeric("outlier count")))
    except (TypeError, ValueError):
        outlier_count = None

    if stdv == 0:
        color = "red"
    elif count is not None and count % 2 == 0:
        color = "yellow"
    elif (skew is not None and skew > 1.0) or (
        outlier_count is not None and outlier_count > 0
    ):
        color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fMode(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    value = ctx.display

    try:
        count = int(float(ctx.numeric("n")))
    except (TypeError, ValueError):
        count = None

    try:
        count_unique = int(float(ctx.numeric("Count Unique")))
    except (TypeError, ValueError):
        count_unique = None

    try:
        most_frequent_value_count = int(float(ctx.numeric("most_frequent_value_count")))
    except (TypeError, ValueError):
        most_frequent_value_count = None

    frequency_table = ctx.row.get("value_frequency_table")
    if frequency_table is None:
        frequency_table = ctx.row.get("frequency_table")

    if isinstance(frequency_table, str):
        try:
            frequency_table = ast.literal_eval(frequency_table)
        except (ValueError, SyntaxError):
            frequency_table = None

    if (most_frequent_value_count is not None and most_frequent_value_count <= 1) or (
        count is not None and count_unique is not None and count == count_unique
    ):
        color = "red"
    elif isinstance(frequency_table, dict) and frequency_table:
        freqs = list(frequency_table.values())
        top = max(freqs)
        if top > 1 and freqs.count(top) > 1:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fSumValues(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        skew = abs(float(ctx.numeric("skew")))
    except (TypeError, ValueError):
        skew = None

    try:
        outlier_count = int(float(ctx.numeric("outlier_count")))
    except (TypeError, ValueError):
        outlier_count = None

    try:
        coefficient_of_variation = abs(float(ctx.numeric("coefficient_of_variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    if not math.isfinite(raw_value) or raw_value == 0:
        color = "red"
    elif (
        (skew is not None and skew > 1.0)
        or (outlier_count is not None and outlier_count > 0)
        or (coefficient_of_variation is not None and coefficient_of_variation > 1.0)
    ):
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fVariance(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    try:
        coefficient_of_variation = abs(float(ctx.numeric("coefficient_of_variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    if not math.isfinite(raw_value):
        color = "red"
    elif count is not None and count < 2:
        color = "red"
    elif raw_value == 0:
        color = "green"
    elif coefficient_of_variation is None:
        color = "yellow"
    elif coefficient_of_variation > 1.0:
        color = "red"
    elif coefficient_of_variation > 0.5:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fSTDV(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("n")))
    except (TypeError, ValueError):
        count = None

    try:
        coefficient_of_variation = abs(float(ctx.numeric("Coefficient of Variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    if not math.isfinite(raw_value):
        color = "red"
    elif count is not None and count < 2:
        color = "red"
    elif raw_value == 0:
        color = "green"
    elif coefficient_of_variation is None:
        color = "yellow"
    elif coefficient_of_variation > 1.0:
        color = "red"
    elif coefficient_of_variation > 0.5:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fMinimum(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        lower_outlier_boundary = float(ctx.numeric("Lower Outlier Boundary"))
    except (TypeError, ValueError):
        lower_outlier_boundary = None

    try:
        percentile_10 = float(ctx.numeric("percentile_10"))
    except (TypeError, ValueError):
        percentile_10 = None

    try:
        q1 = float(ctx.numeric("q1"))
    except (TypeError, ValueError):
        q1 = None

    if lower_outlier_boundary is not None and raw_value < lower_outlier_boundary:
        color = "red"
    elif raw_value == 0:
        color = "yellow"
    elif (
        q1 is not None
        and percentile_10 is not None
        and raw_value < percentile_10
        and raw_value < q1
    ):
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fMaximum(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        upper_outlier_boundary = float(ctx.numeric("upper_outlier_boundary"))
    except (TypeError, ValueError):
        upper_outlier_boundary = None

    try:
        percentile_90 = float(ctx.numeric("percentile_90"))
    except (TypeError, ValueError):
        percentile_90 = None

    try:
        q3 = float(ctx.numeric("q3"))
    except (TypeError, ValueError):
        q3 = None

    if upper_outlier_boundary is not None and raw_value > upper_outlier_boundary:
        color = "red"
    elif (
        q3 is not None
        and percentile_90 is not None
        and raw_value > percentile_90
        and raw_value > q3 * 1.5
    ):
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fRangeValue(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        outlier_count = int(float(ctx.numeric("outlier_count")))
    except (TypeError, ValueError):
        outlier_count = None

    try:
        iqr = float(ctx.numeric("iqr"))
    except (TypeError, ValueError):
        iqr = None

    try:
        coefficient_of_variation = abs(float(ctx.numeric("coefficient_of_variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    if outlier_count is not None and outlier_count >= 2:
        color = "red"
    elif iqr is not None and iqr > 0 and raw_value > iqr * 4:
        color = "red"
    elif coefficient_of_variation is not None and coefficient_of_variation > 1.0:
        color = "yellow"
    elif outlier_count is not None and outlier_count > 0:
        color = "yellow"
    elif iqr is not None and iqr > 0 and raw_value > iqr * 2:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fQ1(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    try:
        minimum = float(ctx.numeric("minimum"))
    except (TypeError, ValueError):
        minimum = None

    try:
        median = float(ctx.numeric("median"))
    except (TypeError, ValueError):
        median = None

    if count is not None and count < 4:
        color = "red"
    elif minimum is not None and median is not None and median != minimum:
        compression = (raw_value - minimum) / (median - minimum)
        if compression < 0.1:
            color = "yellow"
        else:
            color = "green"
    elif raw_value == 0:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fQ2(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    try:
        mean = float(ctx.numeric("mean"))
    except (TypeError, ValueError):
        mean = None

    try:
        stdv = float(ctx.numeric("STDV"))
    except (TypeError, ValueError):
        stdv = None

    if count is not None and count < 2:
        color = "red"
    elif mean is not None and stdv is not None and stdv > 0:
        deviation = abs(raw_value - mean) / stdv
        if deviation > 0.5:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fQ3(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    try:
        maximum = float(ctx.numeric("maximum"))
    except (TypeError, ValueError):
        maximum = None

    try:
        median = float(ctx.numeric("median"))
    except (TypeError, ValueError):
        median = None

    if count is not None and count < 4:
        color = "red"
    elif maximum is not None and median is not None and maximum != median:
        elevation = (raw_value - median) / (maximum - median)
        if elevation > 0.9:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fIQR(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        stdv = float(ctx.numeric("STDV"))
    except (TypeError, ValueError):
        stdv = None

    try:
        coefficient_of_variation = abs(float(ctx.numeric("coefficient_of_variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    if raw_value == 0:
        color = "red"
    elif coefficient_of_variation is not None and coefficient_of_variation > 0.5:
        color = "yellow"
    elif stdv is not None and stdv > 0 and raw_value > stdv * 1.5:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fMAD(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        median = abs(float(ctx.numeric("median")))
    except (TypeError, ValueError):
        median = None

    try:
        stdv = float(ctx.numeric("STDV"))
    except (TypeError, ValueError):
        stdv = None

    if median is not None and median > 0:
        ratio = raw_value / median
        if ratio > 0.5:
            color = "yellow"
        else:
            color = "green"
    elif stdv is not None and stdv > 0:
        ratio = raw_value / stdv
        if ratio > 0.75:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fSkew(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    abs_skew = abs(raw_value)

    if count is not None and count < 3:
        color = "red"
    elif abs_skew > 2.0:
        color = "red"
    elif abs_skew > 0.5:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fKurtosis(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    abs_kurtosis = abs(raw_value)

    if count is not None and count < 4:
        color = "red"
    elif abs_kurtosis > 7.0:
        color = "red"
    elif abs_kurtosis > 1.0:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fCI95(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    value = ctx.display

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    try:
        stdv = float(ctx.numeric("STDV"))
    except (TypeError, ValueError):
        stdv = None

    try:
        mean = float(ctx.numeric("mean"))
    except (TypeError, ValueError):
        mean = None

    if count is not None and count < 2:
        color = "red"
    elif stdv is not None and mean is not None and abs(mean) > 0:
        se_ratio = (stdv / (count**0.5)) / abs(mean) if count else 0
        if se_ratio > 0.25:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fMeanPmStd(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    value = ctx.display

    try:
        coefficient_of_variation = abs(float(ctx.numeric("coefficient_of_variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    try:
        skew = abs(float(ctx.numeric("skew")))
    except (TypeError, ValueError):
        skew = None

    if coefficient_of_variation is not None and coefficient_of_variation > 1.0:
        color = "yellow"
    elif skew is not None and skew > 1.0:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fCountUnique(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = int(float(ctx.display))
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    if raw_value == 0:
        color = "red"
    elif count is not None and count > 0:
        ratio = raw_value / count
        if ratio < 0.05:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{raw_value}[/]"


def fCountMissing(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = int(float(ctx.display))
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        count = int(float(ctx.numeric("count")))
    except (TypeError, ValueError):
        count = None

    if raw_value == 0:
        color = "green"
    elif count is not None and count > 0:
        pct = (raw_value / (count + raw_value)) * 100
        if pct > 20:
            color = "red"
        else:
            color = "yellow"
    else:
        color = "yellow"

    return f"[{color}]{raw_value}[/]"


def fPercentageMissing(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    if raw_value < 5.0:
        color = "green"
    elif raw_value <= 20.0:
        color = "yellow"
    else:
        color = "red"

    return f"[{color}]{value}[/]"


def fFirstQuartileSpread(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        iqr = float(ctx.numeric("iqr"))
    except (TypeError, ValueError):
        iqr = None

    try:
        outlier_count = int(float(ctx.numeric("outlier_count")))
    except (TypeError, ValueError):
        outlier_count = None

    try:
        lower_outlier_boundary = float(ctx.numeric("lower_outlier_boundary"))
    except (TypeError, ValueError):
        lower_outlier_boundary = None

    try:
        minimum = float(ctx.numeric("minimum"))
    except (TypeError, ValueError):
        minimum = None

    if (
        minimum is not None
        and lower_outlier_boundary is not None
        and minimum < lower_outlier_boundary
    ):
        color = "red"
    elif (
        outlier_count is not None
        and outlier_count > 0
        and iqr is not None
        and iqr > 0
        and raw_value > iqr
    ):
        color = "red"
    elif iqr is not None and iqr > 0 and raw_value > iqr * 0.75:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fThirdQuartileSpread(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        iqr = float(ctx.numeric("iqr"))
    except (TypeError, ValueError):
        iqr = None

    try:
        outlier_count = int(float(ctx.numeric("outlier_count")))
    except (TypeError, ValueError):
        outlier_count = None

    try:
        upper_outlier_boundary = float(ctx.numeric("upper_outlier_boundary"))
    except (TypeError, ValueError):
        upper_outlier_boundary = None

    try:
        maximum = float(ctx.numeric("maximum"))
    except (TypeError, ValueError):
        maximum = None

    if (
        maximum is not None
        and upper_outlier_boundary is not None
        and maximum > upper_outlier_boundary
    ):
        color = "red"
    elif (
        outlier_count is not None
        and outlier_count > 0
        and iqr is not None
        and iqr > 0
        and raw_value > iqr
    ):
        color = "red"
    elif iqr is not None and iqr > 0 and raw_value > iqr * 0.75:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fMedianDifference(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        stdv = float(ctx.numeric("STDV"))
    except (TypeError, ValueError):
        stdv = None

    abs_diff = abs(raw_value)

    if stdv is not None and stdv > 0:
        ratio = abs_diff / stdv
        if ratio > 1.0:
            color = "red"
        elif ratio > 0.3:
            color = "yellow"
        else:
            color = "green"
    else:
        if abs_diff == 0:
            color = "green"
        else:
            color = "yellow"

    return f"[{color}]{value}[/]"


def fMidrange(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        mean = float(ctx.numeric("mean"))
    except (TypeError, ValueError):
        mean = None

    try:
        median = float(ctx.numeric("median"))
    except (TypeError, ValueError):
        median = None

    try:
        outlier_count = int(float(ctx.numeric("outlier_count")))
    except (TypeError, ValueError):
        outlier_count = None

    try:
        stdv = float(ctx.numeric("STDV"))
    except (TypeError, ValueError):
        stdv = None

    if outlier_count is not None and outlier_count >= 2:
        color = "red"
    elif mean is not None and stdv is not None and stdv > 0:
        deviation = abs(raw_value - mean) / stdv
        if deviation > 1.5:
            color = "red"
        elif deviation > 0.5:
            color = "yellow"
        else:
            color = "green"
    elif median is not None and stdv is not None and stdv > 0:
        deviation = abs(raw_value - median) / stdv
        if deviation > 1.5:
            color = "red"
        elif deviation > 0.5:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


def fQuartileDeviation(ctx) -> str:
    if ctx.cell is None:
        return f"[red]{ctx.display}[/]"

    try:
        raw_value = float(ctx.display)
        value = round(raw_value, 3)
    except (TypeError, ValueError):
        return f"[red]{ctx.display}[/]"

    try:
        median = abs(float(ctx.numeric("median")))
    except (TypeError, ValueError):
        median = None

    try:
        coefficient_of_variation = abs(float(ctx.numeric("coefficient_of_variation")))
    except (TypeError, ValueError):
        coefficient_of_variation = None

    if raw_value == 0:
        color = "red"
    elif coefficient_of_variation is not None:
        if coefficient_of_variation > 1.0:
            color = "yellow"
        else:
            color = "green"
    elif median is not None and median > 0:
        ratio = raw_value / median
        if ratio > 0.5:
            color = "yellow"
        else:
            color = "green"
    else:
        color = "green"

    return f"[{color}]{value}[/]"


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
        stripe_odd="",
    )

    cfg.columns = {
        "key": ColumnConfig("key", width=24, align="left"),
        "level": ColumnConfig("level", width=10, align="center"),
    }

    cfg.rules = [
        # ── KEY column ───────────────────────────────────────────────────────
        FormatRule(
            name="Key: bold white",
            condition=lambda ctx: True,
            action=lambda ctx: f"[bold white]{ctx.display}[/bold white]",
            target="col.key",
            priority=10,
        ),
        # ── LEVEL column: colour by measurement type ─────────────────────────
        FormatRule(
            name="Level: Metric → blue",
            condition=lambda ctx: ctx.row.get("level") == "Metric",
            action=lambda ctx: f"[bold #4fc3f7]{ctx.display}[/bold #4fc3f7]",
            target="col.level",
            priority=10,
        ),
        FormatRule(
            name="Level: Ordinal → amber",
            condition=lambda ctx: ctx.row.get("level") == "Ordinal",
            action=lambda ctx: f"[bold #ffb74d]{ctx.display}[/bold #ffb74d]",
            target="col.level",
            priority=10,
        ),
        FormatRule(
            name="Level: Nominal → green",
            condition=lambda ctx: ctx.row.get("level") == "Nominal",
            action=lambda ctx: f"[bold #81c784]{ctx.display}[/bold #81c784]",
            target="col.level",
            priority=10,
        ),
        # ── Entire row dim if key starts with underscore (internal/hidden key) ─
        FormatRule(
            name="Internal key: dim entire row",
            condition=lambda ctx: str(ctx.row.get("key", "")).startswith("_"),
            action=lambda ctx: f"[dim #666666]{ctx.display}[/dim #666666]",
            target="row.*",
            priority=60,
            stop_on_hit=True,
        ),
        # ── Metric rows: colour count / mean / std differently ────────────────
        FormatRule(
            name="Mean: blue tint on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "mean"
                and ctx.row.get("level") == "Metric"
                and ctx.cell is not None
            ),
            action=fMean,
            priority=70,
        ),
        FormatRule(
            name="Median: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "median" and ctx.row.get("level") == "Metric"
            ),
            action=fMedian,
            priority=70,
        ),
        FormatRule(
            name="Mode: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "mode" and ctx.row.get("level") == "Metric"
            ),
            action=fMode,
            priority=70,
        ),
        FormatRule(
            name="Sum: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() in {"sum", "sum_values"}
                and ctx.row.get("level") == "Metric"
            ),
            action=fSumValues,
            priority=70,
        ),
        FormatRule(
            name="Variance: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "variance" and ctx.row.get("level") == "Metric"
            ),
            action=fVariance,
            priority=70,
        ),
        FormatRule(
            name="Stdv: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "STDV" and ctx.row.get("level") == "Metric"
            ),
            action=fSTDV,
            priority=70,
        ),
        FormatRule(
            name="Minimum: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "minimum" and ctx.row.get("level") == "Metric"
            ),
            action=fMinimum,
            priority=70,
        ),
        FormatRule(
            name="Maximum: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "maximum" and ctx.row.get("level") == "Metric"
            ),
            action=fMaximum,
            priority=70,
        ),
        FormatRule(
            name="Range Value: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "range_value" and ctx.row.get("level") == "Metric"
            ),
            action=fRangeValue,
            priority=70,
        ),
        FormatRule(
            name="Q1: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "q1" and ctx.row.get("level") == "Metric"
            ),
            action=fQ1,
            priority=70,
        ),
        FormatRule(
            name="Q2: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "q2" and ctx.row.get("level") == "Metric"
            ),
            action=fQ2,
            priority=70,
        ),
        FormatRule(
            name="Q3: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "q3" and ctx.row.get("level") == "Metric"
            ),
            action=fQ3,
            priority=70,
        ),
        FormatRule(
            name="IQR: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "iqr" and ctx.row.get("level") == "Metric"
            ),
            action=fIQR,
            priority=70,
        ),
        FormatRule(
            name="MAD: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "mad" and ctx.row.get("level") == "Metric"
            ),
            action=fMAD,
            priority=70,
        ),
        FormatRule(
            name="Skew: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "skew" and ctx.row.get("level") == "Metric"
            ),
            action=fSkew,
            priority=70,
        ),
        FormatRule(
            name="Kurtosis: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "kurtosis" and ctx.row.get("level") == "Metric"
            ),
            action=fKurtosis,
            priority=70,
        ),
        FormatRule(
            name="CI 95: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "ci_95" and ctx.row.get("level") == "Metric"
            ),
            action=fCI95,
            priority=70,
        ),
        FormatRule(
            name="Mean ± Std: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "mean_pm_std" and ctx.row.get("level") == "Metric"
            ),
            action=fMeanPmStd,
            priority=70,
        ),
        FormatRule(
            name="Count Unique: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "count_unique" and ctx.row.get("level") == "Metric"
            ),
            action=fCountUnique,
            priority=70,
        ),
        FormatRule(
            name="Count Missing: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "count_missing" and ctx.row.get("level") == "Metric"
            ),
            action=fCountMissing,
            priority=70,
        ),
        FormatRule(
            name="Percentage Missing: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "percentage_missing"
                and ctx.row.get("level") == "Metric"
            ),
            action=fPercentageMissing,
            priority=70,
        ),
        FormatRule(
            name="First Quartile Spread: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "first_quartile_spread"
                and ctx.row.get("level") == "Metric"
            ),
            action=fFirstQuartileSpread,
            priority=70,
        ),
        FormatRule(
            name="Third Quartile Spread: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "third_quartile_spread"
                and ctx.row.get("level") == "Metric"
            ),
            action=fThirdQuartileSpread,
            priority=70,
        ),
        FormatRule(
            name="Median Difference: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "median_difference"
                and ctx.row.get("level") == "Metric"
            ),
            action=fMedianDifference,
            priority=70,
        ),
        FormatRule(
            name="Midrange: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "midrange" and ctx.row.get("level") == "Metric"
            ),
            action=fMidrange,
            priority=70,
        ),
        FormatRule(
            name="Quartile Deviation: color on Metric rows",
            condition=lambda ctx: (
                ctx.col.lower() == "quartile_deviation"
                and ctx.row.get("level") == "Metric"
            ),
            action=fQuartileDeviation,
            priority=70,
        ),
    ]

    return cfg
