from collections import Counter
from typing import Optional, Any
import numpy as np
from scipy import stats as sp_stats


class StatisticsEngine:
    """Computes descriptive statistics for data columns."""

    # ─────────────────────────────────────────────
    # Helper Functions for External Use
    # ─────────────────────────────────────────────

    def format_tuple(v: Any) -> str:
        if v is None:
            return "—"

        if isinstance(v, tuple):
            return " | ".join(
                f"{x:.4f}" if isinstance(x, float) else str(x)
                for x in v
            )

        if isinstance(v, float):
            return f"{v:.4f}" if v != int(v) else str(int(v))

        return str(v)

    # ─────────────────────────────────────────────
    # Internal Utility
    # ─────────────────────────────────────────────

    @staticmethod
    def _to_array(values: list[float]) -> np.ndarray:
        """Converts a list of floats to a NumPy array."""
        return np.asarray(values, dtype=np.float64)

    # =========================
    # BASIC STATS
    # =========================

    @staticmethod
    def mean(values: list[float]) -> Optional[float]:
        if not values:
            return None
        return float(np.mean(StatisticsEngine._to_array(values)))

    @staticmethod
    def median(values: list[float]) -> Optional[float]:
        if not values:
            return None
        return float(np.median(StatisticsEngine._to_array(values)))

    @staticmethod
    def mode(values: list) -> Optional[Any]:
        if not values:
            return None

        counter = Counter(values)
        max_count = max(counter.values())
        modes = [k for k, v in counter.items() if v == max_count]

        if len(modes) == len(set(values)):
            return None

        return modes[0] if len(modes) == 1 else str(modes)

    @staticmethod
    def sum_values(values: list[float]) -> Optional[float]:
        if not values:
            return None
        return float(np.sum(StatisticsEngine._to_array(values)))

    @staticmethod
    def variance(values: list[float]) -> Optional[float]:
        if len(values) < 2:
            return None
        # ddof=1 → sample variance
        return float(np.var(StatisticsEngine._to_array(values), ddof=1))

    @staticmethod
    def stdv(values: list[float]) -> Optional[float]:
        if len(values) < 2:
            return None
        # ddof=1 → sample standard deviation
        return float(np.std(StatisticsEngine._to_array(values), ddof=1))

    @staticmethod
    def minimum(values: list[float]) -> Optional[float]:
        if not values:
            return None
        return float(np.min(StatisticsEngine._to_array(values)))

    @staticmethod
    def maximum(values: list[float]) -> Optional[float]:
        if not values:
            return None
        return float(np.max(StatisticsEngine._to_array(values)))

    @staticmethod
    def range_value(values: list[float]) -> Optional[float]:
        if not values:
            return None
        arr = StatisticsEngine._to_array(values)
        return float(np.ptp(arr))  # peak-to-peak = max - min

    @staticmethod
    def count(values: list) -> int:
        return len(values)

    # =========================
    # QUARTILES
    # =========================

    @staticmethod
    def quartiles(values: list[float]) -> tuple:
        if not values:
            return (None, None, None)

        arr = StatisticsEngine._to_array(values)

        # np.percentile with 'midpoint' matches the original manual method
        q1 = float(np.percentile(arr, 25, method="midpoint"))
        q2 = float(np.percentile(arr, 50, method="midpoint"))
        q3 = float(np.percentile(arr, 75, method="midpoint"))

        return (q1, q2, q3)

    @staticmethod
    def q1(values: list[float]):
        return StatisticsEngine.quartiles(values)[0]

    @staticmethod
    def q2(values: list[float]):
        return StatisticsEngine.quartiles(values)[1]

    @staticmethod
    def q3(values: list[float]):
        return StatisticsEngine.quartiles(values)[2]

    @staticmethod
    def iqr(values: list[float]):
        q1, _, q3 = StatisticsEngine.quartiles(values)

        if q1 is None or q3 is None:
            return None

        return q3 - q1

    # =========================
    # ROBUST STATS
    # =========================

    @staticmethod
    def mad(values: list[float]):
        """Median Absolute Deviation."""
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)
        med = np.median(arr)

        return float(np.median(np.abs(arr - med)))

    # =========================
    # DISTRIBUTION SHAPE
    # =========================

    @staticmethod
    def skew(values: list[float]):
        """Sample skewness (bias=False matches the original formula)."""
        if len(values) < 3:
            return None

        arr = StatisticsEngine._to_array(values)

        if np.std(arr) == 0:
            return 0

        # bias=False applies the sample correction; bias=True matches
        # the original population formula — keep bias=True for parity.
        return float(sp_stats.skew(arr, bias=True))

    @staticmethod
    def kurtosis(values: list[float]):
        """
        Excess kurtosis (Fisher definition, i.e. normal = 0).
        bias=True matches the original population formula.
        """
        if len(values) < 4:
            return None

        arr = StatisticsEngine._to_array(values)

        if np.std(arr) == 0:
            return 0

        return float(sp_stats.kurtosis(arr, fisher=True, bias=True))

    # =========================
    # CONFIDENCE INTERVAL
    # =========================

    @staticmethod
    def ci_95(values: list[float]):
        n = len(values)

        if n < 2:
            return None

        arr = StatisticsEngine._to_array(values)
        mean = float(np.mean(arr))
        std  = float(np.std(arr, ddof=1))

        margin = 1.96 * (std / np.sqrt(n))

        return (mean - margin, mean + margin)

    @staticmethod
    def mean_pm_std(values: list[float]):
        mean = StatisticsEngine.mean(values)
        std  = StatisticsEngine.stdv(values)

        if mean is None or std is None:
            return None

        return f"{mean:.4f} ± {std:.4f}"

    # =========================
    # COUNT & MISSING
    # =========================

    @staticmethod
    def count_unique(values: list) -> Optional[int]:
        """Counts the number of distinct values."""
        if not values:
            return None
        return int(len(np.unique(values)))

    @staticmethod
    def count_missing(values: list) -> int:
        """
        Counts missing/null/empty entries.
        Treats None, NaN floats, and whitespace-only strings as missing.
        """
        missing = 0

        for v in values:
            if v is None:
                missing += 1
            elif isinstance(v, float) and np.isnan(v):
                missing += 1
            elif isinstance(v, str) and v.strip() == "":
                missing += 1

        return missing

    @staticmethod
    def percentage_missing(values: list) -> Optional[float]:
        total = len(values)

        if total == 0:
            return None

        return (StatisticsEngine.count_missing(values) / total) * 100

    # =========================
    # SPREAD & POSITION
    # =========================

    @staticmethod
    def first_quartile_spread(values: list[float]) -> Optional[float]:
        if not values:
            return None

        q1 = StatisticsEngine.q1(values)
        mn = StatisticsEngine.minimum(values)

        if q1 is None or mn is None:
            return None

        return q1 - mn

    @staticmethod
    def third_quartile_spread(values: list[float]) -> Optional[float]:
        if not values:
            return None

        q3 = StatisticsEngine.q3(values)
        mx = StatisticsEngine.maximum(values)

        if q3 is None or mx is None:
            return None

        return mx - q3

    @staticmethod
    def median_difference(values: list[float]) -> Optional[float]:
        if not values:
            return None

        mean   = StatisticsEngine.mean(values)
        median = StatisticsEngine.median(values)

        if mean is None or median is None:
            return None

        return mean - median

    @staticmethod
    def midrange(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)

        return float((np.min(arr) + np.max(arr)) / 2)

    @staticmethod
    def quartile_deviation(values: list[float]) -> Optional[float]:
        iqr_val = StatisticsEngine.iqr(values)

        if iqr_val is None:
            return None

        return iqr_val / 2

    @staticmethod
    def central_50_range(values: list[float]) -> Optional[float]:
        return StatisticsEngine.iqr(values)

    @staticmethod
    def central_80_range(values: list[float]) -> Optional[float]:
        p10 = StatisticsEngine.percentile(values, 10)
        p90 = StatisticsEngine.percentile(values, 90)

        if p10 is None or p90 is None:
            return None

        return p90 - p10

    # =========================
    # FREQUENCY STATS
    # =========================

    @staticmethod
    def most_frequent_value_count(values: list) -> Optional[int]:
        if not values:
            return None

        return int(max(Counter(values).values()))

    @staticmethod
    def least_frequent_value(values: list) -> Optional[Any]:
        if not values:
            return None

        counter  = Counter(values)
        min_count = min(counter.values())
        least    = [k for k, v in counter.items() if v == min_count]

        return least[0] if len(least) == 1 else str(least)

    @staticmethod
    def value_frequency_table(values: list) -> Optional[dict]:
        if not values:
            return None

        return dict(Counter(values).most_common())

    @staticmethod
    def relative_frequency_table(values: list) -> Optional[dict]:
        if not values:
            return None

        total   = len(values)
        counter = Counter(values)

        return {
            k: round(v / total, 6)
            for k, v in counter.most_common()
        }

    @staticmethod
    def cumulative_count(values: list) -> Optional[dict]:
        if not values:
            return None

        counter = Counter(values)

        try:
            sorted_keys = sorted(counter.keys())
        except TypeError:
            sorted_keys = list(counter.keys())

        cumulative = {}
        running    = 0

        for k in sorted_keys:
            running += counter[k]
            cumulative[k] = running

        return cumulative

    @staticmethod
    def cumulative_percentage(values: list) -> Optional[dict]:
        if not values:
            return None

        total   = len(values)
        counter = Counter(values)

        try:
            sorted_keys = sorted(counter.keys())
        except TypeError:
            sorted_keys = list(counter.keys())

        cumulative = {}
        running    = 0

        for k in sorted_keys:
            running += counter[k]
            cumulative[k] = round((running / total) * 100, 4)

        return cumulative

    # =========================
    # PERCENTILES
    # =========================

    @staticmethod
    def percentile(values: list[float], p: float) -> Optional[float]:
        """
        p-th percentile using linear interpolation (matches original behaviour).
        """
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)

        # 'linear' interpolation is identical to the original manual method
        return float(np.percentile(arr, p, method="linear"))

    @staticmethod
    def percentile_10(values: list[float]) -> Optional[float]:
        return StatisticsEngine.percentile(values, 10)

    @staticmethod
    def percentile_90(values: list[float]) -> Optional[float]:
        return StatisticsEngine.percentile(values, 90)

    # =========================
    # OUTLIERS
    # =========================

    @staticmethod
    def lower_outlier_boundary(values: list[float]) -> Optional[float]:
        q1      = StatisticsEngine.q1(values)
        iqr_val = StatisticsEngine.iqr(values)

        if q1 is None or iqr_val is None:
            return None

        return q1 - 1.5 * iqr_val

    @staticmethod
    def upper_outlier_boundary(values: list[float]) -> Optional[float]:
        q3      = StatisticsEngine.q3(values)
        iqr_val = StatisticsEngine.iqr(values)

        if q3 is None or iqr_val is None:
            return None

        return q3 + 1.5 * iqr_val

    @staticmethod
    def outlier_values(values: list[float]) -> Optional[list[float]]:
        if not values:
            return None

        arr   = StatisticsEngine._to_array(values)
        lower = StatisticsEngine.lower_outlier_boundary(values)
        upper = StatisticsEngine.upper_outlier_boundary(values)

        if lower is None or upper is None:
            return None

        mask = (arr < lower) | (arr > upper)

        return sorted(arr[mask].tolist())

    @staticmethod
    def outlier_count(values: list[float]) -> Optional[int]:
        outliers = StatisticsEngine.outlier_values(values)

        if outliers is None:
            return None

        return len(outliers)

    # =========================
    # VARIABILITY & DISPERSION
    # =========================

    @staticmethod
    def coefficient_of_variation(values: list[float]) -> Optional[float]:
        mean = StatisticsEngine.mean(values)
        std  = StatisticsEngine.stdv(values)

        if mean is None or std is None or mean == 0:
            return None

        return (std / abs(mean)) * 100

    @staticmethod
    def mean_absolute_deviation(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)

        return float(np.mean(np.abs(arr - np.mean(arr))))

    @staticmethod
    def trimmed_mean(values: list[float], trim: float = 0.1) -> Optional[float]:
        if not values:
            return None

        # sp_stats.trim_mean removes `trim` fraction from each tail
        arr = StatisticsEngine._to_array(values)

        return float(sp_stats.trim_mean(arr, trim))

    @staticmethod
    def spread_score(values: list[float]) -> Optional[float]:
        std = StatisticsEngine.stdv(values)
        r   = StatisticsEngine.range_value(values)

        if std is None or r is None or r == 0:
            return None

        return std / r

    @staticmethod
    def range_percentage(values: list[float]) -> Optional[float]:
        r    = StatisticsEngine.range_value(values)
        mean = StatisticsEngine.mean(values)

        if r is None or mean is None or mean == 0:
            return None

        return (r / abs(mean)) * 100

    # =========================
    # HISTOGRAM HELPERS
    # =========================

    @staticmethod
    def interval_width(values: list[float]) -> Optional[float]:
        """Freedman–Diaconis rule; falls back to Sturges' rule."""
        if not values:
            return None

        n = len(values)

        if n < 2:
            return None

        arr     = StatisticsEngine._to_array(values)
        iqr_val = StatisticsEngine.iqr(values)
        r       = float(np.ptp(arr))

        if r == 0:
            return None

        if iqr_val and iqr_val > 0:
            return 2 * iqr_val * (n ** (-1 / 3))

        # Sturges' fallback
        bins = 1 + np.log2(n)

        return float(r / bins)

    @staticmethod
    def bin_count(values: list[float]) -> Optional[int]:
        n = len(values)

        if n < 2:
            return None

        return int(np.ceil(1 + np.log2(n)))

    # =========================
    # DATA PROPERTIES
    # =========================

    @staticmethod
    def data_span(values: list[float]) -> Optional[float]:
        return StatisticsEngine.range_value(values)

    @staticmethod
    def duplicate_count(values: list) -> Optional[int]:
        if not values:
            return None

        return len(values) - len(np.unique(values))

    @staticmethod
    def data_density(values: list[float]) -> Optional[float]:
        n = len(values)

        if n == 0:
            return None

        r = StatisticsEngine.range_value(values)

        if r is None or r == 0:
            return None

        return n / r

    # =========================
    # VALUE SIGN COUNTS
    # =========================

    @staticmethod
    def positive_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)

        return int(np.sum(arr > 0))

    @staticmethod
    def negative_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)

        return int(np.sum(arr < 0))

    @staticmethod
    def zero_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)

        return int(np.sum(arr == 0))

    @staticmethod
    def even_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr       = StatisticsEngine._to_array(values)
        is_int    = arr == np.floor(arr)
        is_even   = (arr.astype(np.int64) % 2 == 0)

        return int(np.sum(is_int & is_even))

    @staticmethod
    def odd_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr     = StatisticsEngine._to_array(values)
        is_int  = arr == np.floor(arr)
        is_odd  = (arr.astype(np.int64) % 2 != 0)

        return int(np.sum(is_int & is_odd))

    # =========================
    # MEAN COMPARISONS
    # =========================

    @staticmethod
    def above_mean_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr  = StatisticsEngine._to_array(values)
        mean = np.mean(arr)

        return int(np.sum(arr > mean))

    @staticmethod
    def below_mean_count(values: list[float]) -> Optional[int]:
        if not values:
            return None

        arr  = StatisticsEngine._to_array(values)
        mean = np.mean(arr)

        return int(np.sum(arr < mean))

    @staticmethod
    def closest_to_mean(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr  = StatisticsEngine._to_array(values)
        mean = np.mean(arr)

        return float(arr[np.argmin(np.abs(arr - mean))])

    @staticmethod
    def farthest_from_mean(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr  = StatisticsEngine._to_array(values)
        mean = np.mean(arr)

        return float(arr[np.argmax(np.abs(arr - mean))])

    @staticmethod
    def lower_half_mean(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)
        med = np.median(arr)
        lower = arr[arr < med]

        return float(np.mean(lower)) if lower.size > 0 else None

    @staticmethod
    def upper_half_mean(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)
        med = np.median(arr)
        upper = arr[arr > med]

        return float(np.mean(upper)) if upper.size > 0 else None

    # =========================
    # BALANCE & SYMMETRY
    # =========================

    @staticmethod
    def data_balance(values: list[float]) -> Optional[str]:
        if not values:
            return None

        pos = StatisticsEngine.positive_count(values)
        neg = StatisticsEngine.negative_count(values)

        if pos == 0 and neg == 0:
            return "all zero"

        if neg == 0:
            return "all positive"

        if pos == 0:
            return "all negative"

        ratio = pos / neg

        if abs(ratio - 1.0) < 0.05:
            direction = "balanced"
        elif ratio > 1:
            direction = "positive-leaning"
        else:
            direction = "negative-leaning"

        return f"{ratio:.2f}:1 ({direction})"

    @staticmethod
    def symmetry_score(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr    = StatisticsEngine._to_array(values)
        mean   = float(np.mean(arr))
        median = float(np.median(arr))
        std    = float(np.std(arr, ddof=1))

        if std == 0:
            return 0.0

        return 3 * (mean - median) / std

    # =========================
    # NORMALIZATION
    # =========================

    @staticmethod
    def normalized_mean(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)
        mn  = float(np.min(arr))
        mx  = float(np.max(arr))

        if mx == mn:
            return None

        return float((np.mean(arr) - mn) / (mx - mn))

    @staticmethod
    def normalized_stdv(values: list[float]) -> Optional[float]:
        if not values:
            return None

        arr = StatisticsEngine._to_array(values)
        mn  = float(np.min(arr))
        mx  = float(np.max(arr))

        if mx == mn:
            return None

        normalized = (arr - mn) / (mx - mn)

        return float(np.std(normalized, ddof=1))

    # =========================
    # DISTRIBUTION CHARACTERISTICS
    # =========================

    @staticmethod
    def peak_density(values: list[float]) -> Optional[float]:
        if not values:
            return None

        mode_val = StatisticsEngine.mode(values)

        if mode_val is None:
            return None

        n = len(values)

        if isinstance(mode_val, str):
            try:
                import ast
                modes      = ast.literal_eval(mode_val)
                mode_count = sum(values.count(m) for m in modes)
            except Exception:
                return None
        else:
            mode_count = values.count(mode_val)

        return mode_count / n

    @staticmethod
    def data_uniformity(values: list[float]) -> Optional[float]:
        if not values:
            return None

        cv = StatisticsEngine.coefficient_of_variation(values)

        if cv is None:
            return None

        return 1 / (1 + (cv / 100))

    @staticmethod
    def value_concentration(values: list[float]) -> Optional[float]:
        if not values:
            return None

        mad_val = StatisticsEngine.mad(values)
        r       = StatisticsEngine.range_value(values)

        if mad_val is None or r is None or r == 0:
            return None

        return 1 - (mad_val / r)

    # =========================
    # DYNAMIC STAT REGISTRY
    # =========================
    
    # TODO: Add tooltip
    METRIC_STATS = {
        "Mean": mean.__func__,
        "Median": median.__func__,
        "Mode": mode.__func__,
        "Sum": sum_values.__func__,
        "Variance": variance.__func__,
        "STDV": stdv.__func__,
        "Minimum": minimum.__func__,
        "Maximum": maximum.__func__,
        "Range": range_value.__func__,
        "Quartile 1": q1.__func__,
        "Quartile 2": q2.__func__,
        "Quartile 3": q3.__func__,
        "IQR": iqr.__func__,
        "Median Absolute Deviation": mad.__func__,
        "Skew": skew.__func__,
        "Kurtosis": kurtosis.__func__,
        "n": count.__func__,
        "95% CI": ci_95.__func__,
        "Mean +- Std.": mean_pm_std.__func__,

        # Count & Missing
        "Count Unique": count_unique.__func__,
        "Count Missing": count_missing.__func__,
        "Percentage Missing": percentage_missing.__func__,

        # Spread & Position
        "First Quartile Spread": first_quartile_spread.__func__,
        "Third Quartile Spread": third_quartile_spread.__func__,
        "Median Difference": median_difference.__func__,
        "Midrange": midrange.__func__,
        "Quartile Deviation": quartile_deviation.__func__,
        "Central 50% Range": central_50_range.__func__,
        "Central 80% Range": central_80_range.__func__,

        # Frequency
        "Most Frequent Value Count": most_frequent_value_count.__func__,
        "Least Frequent Value": least_frequent_value.__func__,
        "Value Frequency Table": value_frequency_table.__func__,
        "Relative Frequency Table": relative_frequency_table.__func__,
        "Cumulative Count": cumulative_count.__func__,
        "Cumulative Percentage": cumulative_percentage.__func__,

        # Percentiles
        "Percentile 10": percentile_10.__func__,
        "Percentile 90": percentile_90.__func__,

        # Outliers
        "Lower Outlier Boundary": lower_outlier_boundary.__func__,
        "Upper Outlier Boundary": upper_outlier_boundary.__func__,
        "Outlier Values": outlier_values.__func__,
        "Outlier Count": outlier_count.__func__,

        # Variability
        "Coefficient of Variation": coefficient_of_variation.__func__,
        "Mean Absolute Deviation": mean_absolute_deviation.__func__,
        "Trimmed Mean": trimmed_mean.__func__,
        "Spread Score": spread_score.__func__,
        "Range Percentage": range_percentage.__func__,

        # Histogram helpers
        "Interval Width": interval_width.__func__,
        "Bin Count": bin_count.__func__,

        # Data properties
        "Data Span": data_span.__func__,
        "Duplicate Count": duplicate_count.__func__,
        "Data Density": data_density.__func__,

        # Value sign counts
        "Positive Count": positive_count.__func__,
        "Negative Count": negative_count.__func__,
        "Zero Count": zero_count.__func__,
        "Even Count": even_count.__func__,
        "Odd Count": odd_count.__func__,

        # Mean comparisons
        "Above Mean Count": above_mean_count.__func__,
        "Below Mean Count": below_mean_count.__func__,
        "Closest to Mean": closest_to_mean.__func__,
        "Farthest from Mean": farthest_from_mean.__func__,
        "Lower Half Mean": lower_half_mean.__func__,
        "Upper Half Mean": upper_half_mean.__func__,

        # Balance & Symmetry
        "Data Balance": data_balance.__func__,
        "Symmetry Score": symmetry_score.__func__,

        # Normalization
        "Normalized Mean": normalized_mean.__func__,
        "Normalized STDV": normalized_stdv.__func__,

        # Distribution characteristics
        "Peak Density": peak_density.__func__,
        "Data Uniformity": data_uniformity.__func__,
        "Value Concentration": value_concentration.__func__,
    }

    @classmethod
    def compute_metric_stats(
        cls,
        values: list[float],
        selected_stats: list[str]
    ) -> dict[str, Any]:

        results = {}

        for stat in selected_stats:
            func = cls.METRIC_STATS.get(stat)

            if func:
                results[stat] = func(values)

        return results

    @classmethod
    def compute_ordinal_stats(
        cls,
        values: list,
        selected_stats: list[str]
    ) -> dict[str, Any]:

        numeric_values = []

        for v in values:
            try:
                numeric_values.append(float(v))
            except Exception:
                pass

        return cls.compute_metric_stats(numeric_values, selected_stats)

    @classmethod
    def compute_nominal_stats(
        cls,
        values: list,
        selected_stats: list[str]
    ) -> dict[str, Any]:

        results = {}

        nominal_dispatch = {
            "Mode":                     lambda v: cls.mode(v),
            "n":                        lambda v: len(v),
            "Count Unique":             lambda v: cls.count_unique(v),
            "Count Missing":            lambda v: cls.count_missing(v),
            "Percentage Missing":       lambda v: cls.percentage_missing(v),
            "Most Frequent Value Count":lambda v: cls.most_frequent_value_count(v),
            "Least Frequent Value":     lambda v: cls.least_frequent_value(v),
            "Value Frequency Table":    lambda v: cls.value_frequency_table(v),
            "Relative Frequency Table": lambda v: cls.relative_frequency_table(v),
            "Cumulative Count":         lambda v: cls.cumulative_count(v),
            "Cumulative Percentage":    lambda v: cls.cumulative_percentage(v),
            "Duplicate Count":          lambda v: cls.duplicate_count(v),
        }

        for stat in selected_stats:
            handler = nominal_dispatch.get(stat)
            results[stat] = handler(values) if handler else "N/A"

        return results

    @staticmethod
    def frequency_table(values: list) -> dict[str, int]:
        return dict(Counter(values).most_common())
