from collections import Counter
from typing import Optional, Any
import numpy as np
from scipy import stats as sp_stats


class StatisticsEngine:
    """Computes descriptive statistics for data columns."""

    # Helper Functions for External Use
    @staticmethod
    def format_tuple(v: Any) -> str:
        if v is None:
            return "—"
        if isinstance(v, tuple):
            return " | ".join(f"{x:.4f}" if isinstance(x, float) else str(x) for x in v)
        if isinstance(v, float):
            return f"{v:.4f}" if v != int(v) else str(int(v))
        return str(v)

    # Internal Utility
    @staticmethod
    def _to_array(values: list[float]) -> np.ndarray:
        return np.asarray(values, dtype=np.float64)

    # ───────────────────────────────────────────────────────────────────
    # Every stat method now returns {"return_value": ..., "desc": ...}
    # ───────────────────────────────────────────────────────────────────

    @staticmethod
    def mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The sum of all values divided by the total count of values.\n"
            "Purpose: Finds the 'balance point' or general center of your dataset.\n"
            "ELI5: If you and your friends pooled all your candy together and shared it completely equally, this is how much candy everyone gets.\n"
            "Example: Mean of [2, 4, 6, 8] is (2+4+6+8)/4 = 5.0\n"
            "Constraint: Highly sensitive to outliers (extreme wild values). If 4 friends have $10 and 1 friend is a billionaire, the Mean says everyone is a multi-millionaire, which is a lie.\n"
            "Alternative: Use the [bold]MEDIAN[/] instead if your data has crazy highs or lows.\n"
            "Format:\n"
            "  [green][✓] Data is evenly distributed; the mean can be fully trusted.[/]\n"
            "  [yellow][!] Data is skewed slightly; do not rely on it blindly, analyze further.[/]\n"
            "  [red][✗] Massive outliers exist; the mean is heavily distorted, do not trust it.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(np.mean(StatisticsEngine._to_array(values))),
            "desc": desc,
        }

    @staticmethod
    def median(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The exact middle value when your dataset is ordered from smallest to largest.\n"
            "Purpose: Finds the literal center-point of the data, slicing it perfectly into two halves.\n"
            "ELI5: Line up all your friends by height from shortest to tallest. The person standing exactly in the middle of the line is the median height.\n"
            "Example: Median of [1, 3, 99] is 3 (99 doesn't mess it up like it would the mean).\n"
            "Constraint: Ignores the actual numeric weight of extreme values. It also might require calculating an average of the two middle numbers if the total count is even.\n"
            "Alternative: Use the [bold]MEAN[/] instead if you actually care about the total accumulated value or if the data distribution is uniform.\n"
            "Format:\n"
            "  [green][✓] Clear middle value found in data with high skew/outliers.[/]\n"
            "  [yellow][!] Even number of elements; the middle two values were averaged to get this number.[/]\n"
            "  [red][✗] Empty dataset or flat data where median doesn't provide helpful insight.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(np.median(StatisticsEngine._to_array(values))),
            "desc": desc,
        }

    @staticmethod
    def mode(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The value or values that appear most frequently in a dataset.\n"
            "Purpose: Identifies the most popular, trendy, or common choice in your data.\n"
            "ELI5: Voting for a class president. The kid who gets the highest number of hands raised is the mode.\n"
            "Example: Mode of [1, 2, 2, 3, 4] is 2 (it shows up twice, others only once).\n"
            "Constraint: Completely useless if every value appears exactly once. It also ignores all other data values entirely except the most frequent one.\n"
            "Alternative: Use [bold]MEAN[/] or [bold]MEDIAN[/] if your data is purely continuous numeric data with no repeating numbers.\n"
            "Format:\n"
            "  [green][✓] A clear, singular dominant value exists in the data.[/]\n"
            "  [yellow][!] Multiple modes found (bimodal/multimodal); displaying only the first one.[/]\n"
            "  [red][✗] No mode exists (every value appears exactly once, or dataset is empty).[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        counts = Counter(values)
        most_common = counts.most_common()
        if most_common[0][1] == 1:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": most_common[0][0],
            "desc": desc,
        }

    @staticmethod
    def sum_values(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total combined value of adding all numbers together.\n"
            "Purpose: Measures the aggregate or grand total scale of the dataset.\n"
            "ELI5: Emptying everyone's pockets and putting all the money into a single bucket to see how much cash you have altogether.\n"
            "Example: Sum of [10, 20, 30] is 10 + 20 + 30 = 60.\n"
            "Constraint: Doesn't tell you anything about individual behavior or averages. A huge sum could be from one massive number or thousands of tiny ones.\n"
            "Alternative: Use [bold]MEAN[/] if you need to know what a typical single data point looks like instead of the grand total.\n"
            "Format:\n"
            "  [green][✓] Total successfully calculated and reflects accurate raw accumulation.[/]\n"
            "  [yellow][!] Extreme total values that might mask internal structural variations or data imbalances.[/]\n"
            "  [red][✗] Accumulation is zero, null, or suffering from a numeric overflow limit.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(np.sum(StatisticsEngine._to_array(values))),
            "desc": desc,
        }

    @staticmethod
    def variance(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The average of the squared differences from the Mean (calculated as a sample here).\n"
            "Purpose: Measures how spread out or 'scattered' the numbers are from the center.\n"
            "ELI5: If you throw darts at a target, variance measures how far away your darts are scattered from the bullseye. Low variance means tight grouping; high variance means chaotic misses.\n"
            "Example: Variance of [2, 4, 6] (mean=4) is ((2-4)² + (4-4)² + (6-4)²) / (3-1) = 4.0\n"
            "Constraint: The output is in 'squared units' (e.g., if data is $ dollars, variance is $² dollars squared), making it weird to interpret directly.\n"
            "Alternative: Take the square root of variance to get the [bold]STANDARD DEVIATION[/] for real-world units.\n"
            "Format:\n"
            "  [green][✓] Low variance; data points are tightly packed and highly predictable around the average.[/]\n"
            "  [yellow][!] Moderate variance; some data points wander a fair distance from the average.[/]\n"
            "  [red][✗] High variance; data is extremely chaotic, wildly erratic, or sample size is too tiny (< 2 items) to calculate.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(np.var(StatisticsEngine._to_array(values), ddof=1)),
            "desc": desc,
        }

    @staticmethod
    def stdv(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The square root of the sample variance, measuring the average distance of data points from the mean.\n"
            "Purpose: Quantifies how much your data 'stretches' or clusters around the average using the original, real-world unit of measurement.\n"
            "ELI5: Imagine a dog on a leash walking down a sidewalk. The sidewalk center is the mean. Standard Deviation tells you how many feet the dog typically wanders to the left or right of that center line.\n"
            "Example: If values are [2, 4, 4, 4, 6], the mean is 4.0, the variance is 2.0, and the Standard Deviation is the square root of 2, which equals roughly 1.41.\n"
            "Constraint: Because it relies directly on the mean, a single massive outlier can heavily inflate the standard deviation, falsely implying the entire dataset is wildly unstable.\n"
            "Alternative: Use the Interquartile Range ([bold]IQR[/]) or Median Absolute Deviation ([bold]MAD[/]) if your data contains severe outliers.\n"
            "Format:\n"
            "  [green][✓] Low deviation; data points sit tightly and predictably next to the average.[/]\n"
            "  [yellow][!] Moderate deviation; the data is spread out, meaning individual points vary noticeably from the average.[/]\n"
            "  [red][✗] Massive deviation or sample size < 2; data points are exploding in completely opposite directions, or calculation is mathematically impossible.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(np.std(StatisticsEngine._to_array(values), ddof=1)),
            "desc": desc,
        }

    @staticmethod
    def minimum(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The absolute lowest, smallest, or most negative value contained within the dataset.\n"
            "Purpose: Establishes the bottom floor or lower boundary limit of your data universe.\n"
            "ELI5: Looking at a group of students and finding the youngest kid in the room, or checking a thermometer to see the coldest temperature recorded all day.\n"
            "Example: Minimum of [15, 42, 3, 99, 21] is 3.\n"
            "Constraint: Highly prone to capturing data entry errors, bugs, or extreme anomalies (e.g., a sensor glitching and registering a temperature of -999 degrees).\n"
            "Alternative: Use the 1st or 5th percentile ([bold]Q1[/]) to find a realistic 'low end' that filters out accidental zero or negative glitches.\n"
            "Format:\n"
            "  [green][✓] Valid minimum found within expected, realistic logical bounds.[/]\n"
            "  [yellow][!] Minimum is unusually low or zero; verify it represents a real measurement and not missing data.[/]\n"
            "  [red][✗] Extreme negative anomaly or empty dataset; value is highly suspicious or impossible to extract.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(np.min(StatisticsEngine._to_array(values))),
            "desc": desc,
        }

    @staticmethod
    def maximum(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The absolute highest, largest, or most positive value contained within the dataset.\n"
            "Purpose: Establishes the ceiling, peak performance, or absolute upper boundary limit of your data universe.\n"
            "ELI5: Checking a high-score leaderboard for a video game to find the single player who scored the most points out of everyone.\n"
            "Example: Maximum of [15, 42, 3, 99, 21] is 99.\n"
            "Constraint: Vulnerable to freak spikes, errors, or exceptional cases that do not accurately represent how the rest of the data behaves.\n"
            "Alternative: Use the 95th or 99th percentile to capture a realistic 'high cap' without letting a single fluke score distort your vision.\n"
            "Format:\n"
            "  [green][✓] Valid maximum found within normal, healthy operational expectations.[/]\n"
            "  [yellow][!] Maximum is remarkably high; check if it represents a rare breakthrough spike or a corrupted data entry.[/]\n"
            "  [red][✗] Out-of-bounds explosion or empty list; value has overshot safe thresholds or cannot be computed.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(np.max(StatisticsEngine._to_array(values))),
            "desc": desc,
        }

    @staticmethod
    def range_value(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total distance span calculated by subtracting the absolute minimum value from the absolute maximum value.\n"
            "Purpose: Provides a quick, rough snapshot of the total domain scale covered by your data from end to end.\n"
            "ELI5: Measuring the distance between the floor and the ceiling of a room to figure out how tall of a ladder can fit inside.\n"
            "Example: Range of [10, 20, 50, 100] is Max(100) - Min(10) = 90.\n"
            "Constraint: It is wildly untrustworthy if either the single lowest or single highest number is an error or fluke, as it only looks at those two outer endpoints.\n"
            "Alternative: Use the Interquartile Range ([bold]IQR[/]) to see the span of the middle 50% of your data, cutting out both outer edges completely.\n"
            "Format:\n"
            "  [green][✓] Stable range; data limits feel consistent and standard for this type of metric.[/]\n"
            "  [yellow][!] Wide range span; the gap between your best and worst case is quite large, implying high data volatility.[/]\n"
            "  [red][✗] Massive, distorted range or empty data; likely caused by combined extreme outlier points stretching the map artificially.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.max(arr) - np.min(arr)),
            "desc": desc,
        }

    @staticmethod
    def q1(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The 25th percentile of the dataset; the point below which exactly 25% of the sorted data falls.\n"
            "Purpose: Marks the boundary separating the lowest quarter of your data from the upper 75%.\n"
            "ELI5: Imagine a long line of people sorted by wealth. If you start walking from the poorest person and stop exactly 1/4 of the way through the line, that person's wealth is Quartile 1.\n"
            "Example: For a sorted list of [10, 20, 30, 40, 50, 60, 70, 80], Q1 sits roughly between 20 and 30 (around 27.5 depends on interpolation method).\n"
            "Constraint: It only focuses on the lower cut-off marker, meaning it tells you absolutely nothing about how high or extreme the upper values of the data go.\n"
            "Alternative: Combine it with [bold]Q3 (75th Percentile)[/] and [bold]Median (50th Percentile)[/] to build a complete Box Plot overview of the entire structure.\n"
            "Format:\n"
            "  [green][✓] Q1 baseline established; lower tier values are normal and healthy.[/]\n"
            "  [yellow][!] Q1 is heavily compressed near zero; indicating a massive clustering of very low values at the bottom of your dataset.[/]\n"
            "  [red][✗] Calculation failed due to an empty array or lack of sufficient data distribution points.[/]"
        )
        if not values:
            return {
                "return_value": None,
                "desc": desc,
            }
        return {
            "return_value": float(
                np.percentile(StatisticsEngine._to_array(values), 25)
            ),
            "desc": desc,
        }

    @staticmethod
    def q2(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The 50th percentile of the dataset, dividing the sorted numbers into two equal halves.\n"
            "Purpose: Locates the exact statistical midpoint where half of the entries are below and half are above.\n"
            "ELI5: Think of a marathon finish line. Quartile 2 represents the exact time clocked by the runner who finished right in the middle of the pack.\n"
            "Example: For the dataset [10, 20, 30, 40, 50], Q2 is 30.0 (exactly 50% of values are smaller or equal, and 50% are greater or equal).\n"
            "Constraint: While it provides an accurate split point, it ignores the extreme scale of values on either side of the tail (whether the largest value is 60 or 1,000,000, Q2 stays exactly the same).\n"
            "Alternative: Use the [bold]MEAN[/] if you need a value that responds dynamically to changes in every single data point.\n"
            "Format:\n"
            "  [green][✓] Middle point sits firmly within realistic, well-centered operational limits.[/]\n"
            "  [yellow][!] Data is slightly asymmetric, meaning Q2 is shifting away from the mean value.[/]\n"
            "  [red][✗] Empty array or degenerate data where a center cut cannot be calculated.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(
                np.percentile(StatisticsEngine._to_array(values), 50)
            ),
            "desc": desc,
        }

    @staticmethod
    def q3(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The 75th percentile of the dataset; the point below which exactly 75% of the sorted data falls.\n"
            "Purpose: Marks the boundary separating the lowest three-quarters of your data from the top 25% highest values.\n"
            "ELI5: If you score in Quartile 3 on a test, it means your grade was higher than 75% of the students in the class. You are in the top quarter!\n"
            "Example: For a sorted list of [10, 20, 30, 40, 50, 60, 70, 80], Q3 sits between 60 and 70 (around 62.5 depends on internal interpolation).\n"
            "Constraint: It focuses entirely on isolating the top tier, meaning it tells you absolutely nothing about how bad the lowest values are.\n"
            "Alternative: Use [bold]Q1 (25th Percentile)[/] if you need to evaluate the lower bounds of your distribution instead.\n"
            "Format:\n"
            "  [green][✓] Q3 threshold established; upper tier bounds are behaving predictably.[/]\n"
            "  [yellow][!] Q3 is heavily elevated; indicating that the top 25% of your data is rapidly ballooning outward.[/]\n"
            "  [red][✗] Insufficient sample size or empty list; upper boundary cannot be calculated.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(
                np.percentile(StatisticsEngine._to_array(values), 75)
            ),
            "desc": desc,
        }

    @staticmethod
    def iqr(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The Interquartile Range, calculated by subtracting Quartile 1 from Quartile 3 (Q3 - Q1).\n"
            "Purpose: Measures the spread or variation of the middle 50% of the dataset, effectively slicing off the extremes.\n"
            "ELI5: Imagine a school bus filled with kids. The IQR ignores the super short kindergartners at the front and the super tall teenagers at the back, measuring only the height difference among the normal kids sitting in the middle rows.\n"
            "Example: If Q3 is 70 and Q1 is 30, the IQR is 70 - 30 = 40.0.\n"
            "Constraint: Completely discards outliers. If you actually *want* to track extreme spikes or system failures, IQR will hide them from you.\n"
            "Alternative: Use [bold]STANDARD DEVIATION[/] or [bold]RANGE[/] if you need a measurement that actively includes and accounts for extreme values.\n"
            "Format:\n"
            "  [green][✓] Tight, reliable middle spread; the core body of data points are highly consistent.[/]\n"
            "  [yellow][!] Expanding core spread; the middle half of your data is drifting apart, indicating growing volatility.[/]\n"
            "  [red][✗] Data is completely flat (IQR = 0) or empty; no variation exists within the middle core.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            "desc": desc,
        }

    @staticmethod
    def mad(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The Median Absolute Deviation, which is the median of the absolute distances of all data points from the dataset's median.\n"
            "Purpose: Provides a robust, bulletproof metric of data variation that completely ignores crazy outliers.\n"
            "ELI5: You calculate how far away each house on a street is from the exact middle house, drop any negative signs, and find the middle distance. If one neighbor lives 50 miles away in a castle, MAD ignores that crazy outlier.\n"
            "Example: For [2, 3, 4, 5, 100], the median is 4. The absolute distances from 4 are [2, 1, 0, 1, 96]. Sorting these distances gives [0, 1, 1, 2, 96]. The median of these distances (MAD) is 1.0.\n"
            "Constraint: It is mathematically harder to use in advanced calculus/algebraic proofs compared to Standard Deviation, and it under-reports true chaos if that chaos is what you want to study.\n"
            "Alternative: Use [bold]STANDARD DEVIATION[/] if your data follows a smooth, normal curve without any bad data glitches.\n"
            "Format:\n"
            "  [green][✓] Solid, stable variation; the core dispersion remains highly consistent despite any rogue outliers.[/]\n"
            "  [yellow][!] Moderate deviation; the typical distance from the median is widening across standard data points.[/]\n"
            "  [red][✗] Error or empty list; unable to find absolute deviations due to a lack of data values.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        med = np.median(arr)
        return {
            "return_value": float(np.median(np.abs(arr - med))),
            "desc": desc,
        }

    @staticmethod
    def skew(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: A statistical metric that quantifies the asymmetry or lopsidedness of a data distribution around its mean.\n"
            "Purpose: Tells you whether your data values are trailing off heavily to the left side, trailing to the right side, or perfectly balanced.\n"
            "ELI5: Imagine a smooth hill. If the hill peaks right in the middle, skew is zero. If the hill has a long, slow slope dragging out far to the right side, it has a positive skew.\n"
            "Example: A perfectly balanced normal distribution has a skew of 0.0. Data with a long tail of rare, massive values on the right yields a positive skew (> 0).\n"
            "Constraint: Requires a reasonable sample size to be meaningful. A small handful of numbers can give a highly erratic skew value that changes drastically with one new entry.\n"
            "Alternative: Simply compare the visual distance between the [bold]MEAN[/] and the [bold]MEDIAN[/] to get a quick intuitive feel for data imbalance.\n"
            "Format:\n"
            "  [green][✓] Skew is near 0; the data distribution is symmetric, beautifully balanced, and highly predictable.[/]\n"
            "  [yellow][!] Moderate skewing; data has a noticeable tail pulling to one side. Mean and Median are separating.[/]\n"
            "  [red][✗] Extreme distortion; distribution is wildly lopsided, or sample size is too small to analyze shape.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(sp_stats.skew(StatisticsEngine._to_array(values))),
            "desc": desc,
        }

    @staticmethod
    def kurtosis(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: A statistical measure that quantifies the 'tailedness' and peak sharpness of a data distribution compared to a normal distribution.\n"
            "Purpose: Identifies whether your data is prone to extreme, freak outliers (heavy tails) or if it behaves in a safe, predictable manner (light tails).\n"
            "ELI5: Imagine a trampoline. If everyone jumps safely near the center, it's a standard shape. If one person jumps so hard they stretch the center down into a sharp point while sending others flying way off the edges, that extreme spike and wide splash represents high kurtosis.\n"
            "Example: A perfect normal distribution has a Fisher kurtosis of 0.0. A dataset with a massive spike and crazy long tails (like financial market shocks) returns a high positive kurtosis (> 0).\n"
            "Constraint: Requires large datasets to be meaningful. In a small dataset, a single typo or freak data point can make your kurtosis value explode or collapse completely.\n"
            "Alternative: Look at the raw [bold]RANGE[/] or calculate percentiles (like the 1st and 99th) to manually spot extreme tail behavior.\n"
            "Format:\n"
            "  [green][✓] Kurtosis is near 0; tail behavior is normal, standard, and highly predictable.[/]\n"
            "  [yellow][!] High or low kurtosis; your data has an abnormal peak and tail thickness. Outlier risks are altered.[/]\n"
            "  [red][✗] Extreme kurtosis distortion or empty list; the data profile is completely chaotic or impossible to calculate.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(
                sp_stats.kurtosis(StatisticsEngine._to_array(values))
            ),
            "desc": desc,
        }

    @staticmethod
    def count(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The total number of records, elements, or observations present inside the dataset.\n"
            "Purpose: Establishes your raw sample size (n), telling you how much total evidence or history you have collected.\n"
            "ELI5: Counting exactly how many students are sitting in a classroom to make sure everyone is present for roll call.\n"
            "Example: Count of ['apple', 'banana', 'cherry'] is 3.\n"
            "Constraint: It counts every single entry blindly, meaning it includes broken data entries, empty placeholders, and duplicate entries without filtering them out.\n"
            "Alternative: Use [bold]COUNT UNIQUE[/] to see distinct items or filter out blank spaces to find the true, valid data count.\n"
            "Format:\n"
            "  [green][✓] Healthy sample size; plenty of data entries available to perform meaningful statistical analysis.[/]\n"
            "  [yellow][!] Low sample size; statistics calculated on this small group might be accidental flukes rather than real trends.[/]\n"
            "  [red][✗] Empty dataset; there are zero entries to analyze, making all further calculations completely impossible.[/]"
        )
        return {
            "return_value": len(values),
            "desc": desc,
        }

    @staticmethod
    def ci_95(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: A calculated range of values that is 95% likely to contain the true, real-world population mean.\n"
            "Purpose: Measures the precision and reliability of your sample average, showing the upper and lower boundaries of your estimating confidence.\n"
            "ELI5: If you guess a jar has 500 jellybeans, you might be wrong. But if you say 'I am 95% confident the real number is somewhere between 480 and 520,' you've created a confidence interval.\n"
            "Example: For a dataset with a mean of 50.0 and a small standard error, the 95% CI might return the tuple range (48.2, 51.8).\n"
            "Constraint: Assumes your data represents a random sample and follows a clean distribution. If the data is highly biased or chaotic, the 95% boundary becomes completely misleading.\n"
            "Alternative: Use a bootstrapping method or report a wider [bold]99% Confidence Interval[/] if your stakes are incredibly high.\n"
            "Format:\n"
            "  [green][✓] Narrow interval gap; your sample size is strong, meaning your calculated average is highly precise.[/]\n"
            "  [yellow][!] Wide interval gap; there is high uncertainty due to heavy data scattering or a small sample size.[/]\n"
            "  [red][✗] Insufficient data (< 2 entries) or empty list; it is mathematically impossible to establish a confidence range.[/]"
        )
        if not values or len(values) < 2:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = float(np.mean(arr))
        se = float(sp_stats.sem(arr))
        ci = sp_stats.t.interval(0.95, len(arr) - 1, loc=m, scale=se)
        return {
            "return_value": (float(ci[0]), float(ci[1])),
            "desc": desc,
        }

    @staticmethod
    def mean_pm_std(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: A formatted string expressing the sample mean followed by the plus/minus symbol and one standard deviation (Mean ± Std).\n"
            "Purpose: Summarizes the operational center and the typical boundary spread of your data points in a single standard notation phrase.\n"
            "ELI5: A factory machine fills cereal boxes. If it says '16.0oz ± 0.2oz', it means the average box gets 16 ounces of cereal, and most boxes fluctuate by 0.2 ounces above or below that center.\n"
            "Example: If mean is 10.0 and standard deviation is 1.5, the output string reads: '10.0000 ± 1.5000'.\n"
            "Constraint: Only paints a perfect picture if your data follows a symmetrical bell curve. If data is heavily skewed or lopsided, this layout will predict impossible or highly inaccurate ranges.\n"
            "Alternative: Use the combination of [bold]MEDIAN[/] and [bold]IQR[/] to summarize center and spread for skewed, uneven datasets.\n"
            "Format:\n"
            "  [green][✓] Balanced data summary; center and spread indicators align flawlessly with standard distributions.[/]\n"
            "  [yellow][!] High fluctuation window; the standard deviation tail is massive compared to the size of the mean.[/]\n"
            "  [red][✗] Empty dataset; cannot format summary figures because center and spread values are non-existent.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = float(np.mean(arr))
        s = float(np.std(arr, ddof=1))
        return {
            "return_value": f"{m:.4f} ± {s:.4f}",
            "desc": desc,
        }

    @staticmethod
    def count_unique(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The total count of completely distinct, unique values present in the dataset, completely ignoring duplicates.\n"
            "Purpose: Measures the variety, diversity, or cardinality score of your dataset items.\n"
            "ELI5: If a room contains 10 people wearing hats, but 5 are wearing red hats and 5 are wearing blue hats, the unique count of hat colors in that room is exactly 2.\n"
            "Example: Count unique of [1, 1, 2, 2, 3, 3, 3] is 3 (those distinct numbers are 1, 2, and 3).\n"
            "Constraint: Extremely sensitive to capitalization, hidden trailing spaces, or tiny typos (e.g., treating 'Apple' and 'apple ' as two completely separate unique things).\n"
            "Alternative: Use raw [bold]COUNT[/] if you want to know the total transactional volume regardless of item variety.\n"
            "Format:\n"
            "  [green][✓] High diversity or expected variation; data points represent a healthy mix of unique values.[/]\n"
            "  [yellow][!] Uniformity alert; almost all entries are identical copies, indicating low variation or high redundancy.[/]\n"
            "  [red][✗] Zero unique entries or empty dataset; no distinct classification data can be established.[/]"
        )
        return {
            "return_value": len(set(values)),
            "desc": desc,
        }

    @staticmethod
    def count_missing(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The total count of empty, null, None, or mathematically invalid (NaN) placeholders inside your data column.\n"
            "Purpose: Acts as a data quality health check, pinpointing exactly how many blank spaces or broken survey responses exist.\n"
            "ELI5: Inspecting an attendance sheet to see exactly how many boxes were left blank because students skipped class or didn't turn in their paperwork.\n"
            "Example: For [5.0, None, 12.5, np.nan], the count of missing items is 2.\n"
            "Constraint: It only tracks technical null/NaN types. If your dataset contains bad entries filled with placeholder strings like 'N/A', 'UNKNOWN', or '0', this function passes over them blindly.\n"
            "Alternative: Use data cleaning functions like Pandas `.isin()` to scan for manual text placeholder strings along with formal null values.\n"
            "Format:\n"
            "  [green][✓] Zero missing values; your data is pristine, perfectly complete, and fully populated.[/]\n"
            "  [yellow][!] Minor data gaps detected; some fields are blank, which could slightly skew your downstream calculations.[/]\n"
            "  [red][✗] High data corruption or empty fields; massive chunks of records are blank, making math formulas highly unstable.[/]"
        )
        missing = sum(
            1 for v in values if v is None or (isinstance(v, float) and np.isnan(v))
        )
        return {
            "return_value": missing,
            "desc": desc,
        }

    @staticmethod
    def percentage_missing(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The proportion of missing, null, or NaN entries relative to the total size of the dataset, expressed as a value from 0% to 100%.\n"
            "Purpose: Delivers a normalized data quality grade, making it easy to see how much of your total dataset is broken or unpopulated.\n"
            "ELI5: If you give a test with 10 questions and a student leaves 2 answers completely blank, their percentage of missing answers is 20%.\n"
            "Example: For a list of 4 items [10.0, None, 30.0, 40.0], 1 out of 4 is missing, which equals (1/4) * 100 = 25.0% missing.\n"
            "Constraint: Does not tell you *why* the data is missing (whether it's an accidental system bug or a deliberate skip pattern in a survey).\n"
            "Alternative: Use [bold]COUNT MISSING[/] if you need the exact raw number of rows to drop or patch rather than a comparative ratio.\n"
            "Format:\n"
            "  [green][✓] Less than 5% missing; highly complete dataset, perfectly safe for standard statistical testing.[/]\n"
            "  [yellow][!] 5% to 20% missing; noticeable data loss; consider applying imputation strategies to fill the blanks responsibly.[/]\n"
            "  [red][✗] Greater than 20% missing data; highly corrupted or severely incomplete dataset; proceeding without extensive patching is dangerous.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        missing = sum(
            1 for v in values if v is None or (isinstance(v, float) and np.isnan(v))
        )
        return {
            "return_value": (missing / len(values)) * 100,
            "desc": desc,
        }

    @staticmethod
    def first_quartile_spread(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total distance between the 25th percentile (Q1) and the absolute minimum value (Q1 - Min).\n"
            "Purpose: Measures the density or spread of the lowest quarter of your dataset to see how far the bottom tail stretches out.\n"
            "ELI5: Imagine a line of students ordered by height. This metric measures the exact height difference between the absolute shortest student and the person standing 25% of the way down the line.\n"
            "Example: If the minimum value is 10 and Q1 is 25, the First Quartile Spread is 25 - 10 = 15.0.\n"
            "Constraint: If your single absolute minimum is a broken data entry or fluke zero, this metric will over-inflate, making the bottom tail look much larger than it actually is.\n"
            "Alternative: Look at the [bold]CENTRAL 50% RANGE[/] or use standard percentiles to avoid the raw minimum value edge.\n"
            "Format:\n"
            "  [green][✓] Normal bottom spread; the lowest quarter of data points are compactly and healthily distributed.[/]\n"
            "  [yellow][!] Wide bottom spread; the lowest 25% of your data exhibits deep inequality or spreads out heavily.[/]\n"
            "  [red][✗] Distorted tail or empty list; an extreme minimum outlier has unnaturally skewed your bottom-end range.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.percentile(arr, 25) - np.min(arr)),
            "desc": desc,
        }

    @staticmethod
    def third_quartile_spread(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total distance between the absolute maximum value and the 75th percentile (Max - Q3).\n"
            "Purpose: Measures the density or spread of the highest quarter of your dataset to see how far the top tail stretches out.\n"
            "ELI5: Imagine checking the test scores of a class. This metric measures the point gap between the student who got the absolute highest score and the student at the 75th percentile mark.\n"
            "Example: If Q3 is 75 and the absolute maximum is 98, the Third Quartile Spread is 98 - 75 = 23.0.\n"
            "Constraint: If a single person gets a freakishly high score (an outlier maximum), this spread inflates dramatically, misrepresenting the top tier.\n"
            "Alternative: Track the [bold]CENTRAL 80% RANGE[/] to inspect high dispersion without relying directly on the vulnerable maximum endpoint.\n"
            "Format:\n"
            "  [green][✓] Normal top spread; your upper-tier data points cluster cleanly and drop off predictably.[/]\n"
            "  [yellow][!] Wide top spread; the highest 25% of your values are stretching out, indicating an elite or extreme high group.[/]\n"
            "  [red][✗] Exploding top tail or empty data; a massive upper outlier has artificially blown up your top-end variance.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.max(arr) - np.percentile(arr, 75)),
            "desc": desc,
        }

    @staticmethod
    def median_difference(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The structural gap between the mathematical center (Mean) and the positional center (Median) of a dataset (Mean - Median).\n"
            "Purpose: Functions as a direct indicator of distribution skewness; revealing how heavily outliers are tugging at the average.\n"
            "ELI5: If you look at houses on a block, the median is the middle house. The mean is the average price. If a billionaire builds a palace on the block, the median house stays the same, but the mean jumps sky-high. The gap between them is the Median Difference.\n"
            "Example: If the mean of a lopsided dataset is 55.0 and the median is 40.0, the Median Difference is 55.0 - 40.0 = 15.0.\n"
            "Constraint: A value of 0 doesn't automatically mean your data is perfectly normal; it could just mean complex left and right anomalies accidentally balanced each other out.\n"
            "Alternative: Run a formal [bold]SKEW[/] function to get a true normalized mathematical assessment of distribution symmetry.\n"
            "Format:\n"
            "  [green][✓] Near zero; the mean and median sit right next to each other, indicating a beautifully balanced, symmetrical distribution.[/]\n"
            "  [yellow][!] Noticeable gap; the mean is pulling away from the median, confirming your data is shifting or lopsided.[/]\n"
            "  [red][✗] Massive divergence or empty array; intense outlier strings are corrupting the average, making it completely untrustworthy.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.mean(arr) - np.median(arr)),
            "desc": desc,
        }

    @staticmethod
    def midrange(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The exact mathematical average of the two most extreme boundary endpoints in your dataset ((Min + Max) / 2).\n"
            "Purpose: Offers a lightning-fast, rudimentary center point calculation using only the absolute floor and ceiling values.\n"
            "ELI5: If the coldest temperature of the day was 40°F and the hottest was 80°F, the midrange temperature is exactly halfway between them at 60°F.\n"
            "Example: Midrange of [10, 15, 20, 22, 90] is (10 + 90) / 2 = 50.0.\n"
            "Constraint: Highly dangerous and fragile. Because it ignores every single number except the absolute minimum and maximum, a single error on either end completely ruins the result.\n"
            "Alternative: Use the traditional [bold]MEDIAN[/] or [bold]MEAN[/] for a safe, comprehensive center measurement that considers the full dataset.\n"
            "Format:\n"
            "  [green][✓] Symmetric boundaries; the midpoint between the absolute minimum and maximum aligns nicely with overall expectations.[/]\n"
            "  [yellow][!] Shifting boundaries; the mid-floor/ceiling average is pulling away from the core mass of the data entries.[/]\n"
            "  [red][✗] Highly distorted boundary values or empty list; extreme outliers on the edges render this center figure useless.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float((np.min(arr) + np.max(arr)) / 2),
            "desc": desc,
        }

    @staticmethod
    def quartile_deviation(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: Half of the Interquartile Range, calculated as (Q3 - Q1) / 2. Also known formalistically as the Semi-Interquartile Range.\n"
            "Purpose: Measures data dispersion by calculating the average distance from the median to the outer edge of the central 50% core.\n"
            "ELI5: Imagine looking at a standard group of students. If you throw out the tallest 25% and shortest 25%, this metric tells you the average height variance left among the normal middle students.\n"
            "Example: If Q3 is 80 and Q1 is 40, the IQR is 40. Dividing that by 2 gives a Quartile Deviation of 20.0.\n"
            "Constraint: Completely blind to data variation occurring in the bottom 25% or top 25% tails. Extreme real-world dangers out on the edges will remain completely hidden.\n"
            "Alternative: Use [bold]STANDARD DEVIATION[/] if you need an all-inclusive dispersion metric that values tail activity.\n"
            "Format:\n"
            "  [green][✓] Low deviation; the core 50% of your data entries are exceptionally close-knit and predictable.[/]\n"
            "  [yellow][!] Moderate deviation; the middle half of your data shows a noticeable internal spread or scatter.[/]\n"
            "  [red][✗] Zero internal variance or empty array; the middle data is entirely flat or cannot be evaluated.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(
                (np.percentile(arr, 75) - np.percentile(arr, 25)) / 2
            ),
            "desc": desc,
        }

    @staticmethod
    def central_50_range(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The mathematical range span of the middle 50% of your data entries, calculated as the 75th percentile minus the 25th percentile (P75 - P25).\n"
            "Purpose: Isolates and tracks the total width of your data's primary engine room, filtering out any strange anomalies on either extreme end.\n"
            "ELI5: Slicing off the bottom 25% lowest scores and the top 25% highest scores, then checking the exact point window that the middle 50% of the crowd occupies.\n"
            "Example: If P75 is 70.0 and P25 is 30.0, the Central 50% Range is 70.0 - 30.0 = 40.0.\n"
            "Constraint: It strictly deletes the outer edges. If you are trying to track system spikes or high-risk edge cases, this metric intentionally drops them.\n"
            "Alternative: Use the comprehensive [bold]RANGE[/] calculation if keeping track of absolute edge boundaries matters to your mission.\n"
            "Format:\n"
            "  [green][✓] Highly stable core range; the center 50% mass of your data maintains a steady, normal footprint.[/]\n"
            "  [yellow][!] Expanding core range; the middle body of data points is growing wider, signaling rising system volatility.[/]\n"
            "  [red][✗] Flat core values or empty dataset; no internal spread exists or calculations are blocked by lack of records.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            "desc": desc,
        }

    @staticmethod
    def central_80_range(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The mathematical range span of the middle 80% of your data entries, calculated as the 90th percentile minus the 10th percentile (P90 - P10).\n"
            "Purpose: Provides a broader look at your data's main body than the 50% range, while still safely shielding your metrics from freak 1% outlier spikes.\n"
            "ELI5: Slicing off the bottom 10% extreme low values and the top 10% extreme high values, leaving you with a comprehensive look at the broad 80% majority of your data.\n"
            "Example: If P90 is 92.0 and P10 is 12.0, the Central 80% Range is 92.0 - 12.0 = 80.0.\n"
            "Constraint: Can still occasionally be affected if your data has massive, dense clumps of values sitting right around the 10th or 90th percentile lines.\n"
            "Alternative: Step down to the more robust [bold]CENTRAL 50% RANGE[/] if you need a tighter focus that handles extreme skew even better.\n"
            "Format:\n"
            "  [green][✓] Stable broad coverage; the vast 80% majority of your dataset fits neatly within expected boundaries.[/]\n"
            "  [yellow][!] Broad range expansion; the gap between your 10th and 90th percentiles is wide, indicating high structural divergence.[/]\n"
            "  [red][✗] Collapsed distribution range or empty list; lack of data points makes an 80% broad range extraction impossible.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.percentile(arr, 90) - np.percentile(arr, 10)),
            "desc": desc,
        }

    @staticmethod
    def most_frequent_value_count(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The exact number of times the single most common item (the mode) appears inside the dataset.\n"
            "Purpose: Measures the absolute strength, volume, or popularity peak of the dominant value.\n"
            "ELI5: If you ask a class their favorite ice cream flavor and 'Chocolate' wins with 15 votes, 15 is the most frequent value count.\n"
            "Example: For [1, 2, 2, 2, 3, 4], the mode is 2, and its most frequent value count is 3.\n"
            "Constraint: If every single item in your list occurs exactly once, the function still returns 1, which might trick you into thinking a dominant trend exists when it doesn't.\n"
            "Alternative: Compare this count directly against the total dataset [bold]COUNT[/] to evaluate if the popularity is actually meaningful or just a tiny minority.\n"
            "Format:\n"
            "  [green][✓] High frequency dominance; a major, clear trend exists in the distribution.[/]\n"
            "  [yellow][!] Low frequency count; the most common item barely beats out the other values, signaling weak popularity.[/]\n"
            "  [red][✗] Empty list or flat data where every item appears only once; no distinct trend can be inferred.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        counts = Counter(values)
        mc = counts.most_common(1)[0]
        return {
            "return_value": mc[1],
            "desc": desc,
        }

    @staticmethod
    def least_frequent_value(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The specific data value or item that registers the lowest occurrence count within the dataset.\n"
            "Purpose: Identifies the rarest, most unique, or least popular entity in your collection.\n"
            "ELI5: Checking your store inventory and finding the single item flavor that nobody ever buys, sitting completely alone on the shelf.\n"
            "Example: For ['apple', 'apple', 'banana'], 'banana' is the least frequent value because it only appears once.\n"
            "Constraint: If there is a tie where 20 different items all appear exactly once, this function blindly picks only the last one it encounters, hiding the other rare items.\n"
            "Alternative: Review a full [bold]VALUE FREQUENCY TABLE[/] to inspect every single low-performing value at the same time.\n"
            "Format:\n"
            "  [green][✓] Clearly isolated rare item; useful for identifying unique niches or extreme exceptions.[/]\n"
            "  [yellow][!] Massive tie found; multiple values share this low frequency floor, reducing the uniqueness of the item.[/]\n"
            "  [red][✗] Empty array; impossible to isolate the rarest item because no values are present.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        counts = Counter(values)
        lf = counts.most_common()[-1]
        return {
            "return_value": lf[0],
            "desc": desc,
        }

    @staticmethod
    def value_frequency_table(values: list) -> dict[str, Any]:
        desc = (
            "Definition: A complete mapped dictionary displaying each distinct item alongside its absolute raw occurrence count.\n"
            "Purpose: Provides a comprehensive blueprint breakdown of exactly how your total data volume is split among categories.\n"
            "ELI5: Dumping a bag of multi-colored candies onto a table and sorting them into separate piles to count exactly how many Reds, Blues, and Greens you got.\n"
            "Example: For ['A', 'B', 'A'], the table returns {'A': 2, 'B': 1}.\n"
            "Constraint: Becomes a massive, unreadable wall of text if your dataset has thousands of unique numeric entries (like precise timestamp values).\n"
            "Alternative: Group numeric data into fixed ranges or bins using a histogram visualization rather than displaying raw individual counts.\n"
            "Format:\n"
            "  [green][✓] Compact, readable summary; distribution of categories is perfectly visible at a glance.[/]\n"
            "  [yellow][!] Table is stretching very wide; a high number of unique categories makes the raw breakdown difficult to digest.[/]\n"
            "  [red][✗] Empty input; cannot compile an inventory map because no data items exist.[/]"
        )
        return {
            "return_value": dict(Counter(values).most_common()),
            "desc": desc,
        }

    @staticmethod
    def relative_frequency_table(values: list) -> dict[str, Any]:
        desc = (
            "Definition: A mapped table showing the proportional occurrence of each distinct item as a decimal ratio of the total dataset.\n"
            "Purpose: Normalizes your frequency counts, allowing you to easily compare categorical breakdowns across different sample sizes.\n"
            "ELI5: Instead of saying '10 people voted yes' out of a massive crowd, you say '0.20 (or 20%) of the crowd voted yes.' It scales the numbers fairly.\n"
            "Example: For [1, 2, 2, 4], the frequency of '2' is 2 out of 4, so its relative frequency is 2/4 = 0.5.\n"
            "Constraint: It strips away raw volume context entirely. A relative frequency of 1.0 could mean a category is 100% dominant out of 1,000,000 entries, or simply that you only sampled 1 single person.\n"
            "Alternative: Use the standard [bold]VALUE FREQUENCY TABLE[/] alongside this one to keep track of the actual underlying raw counts.\n"
            "Format:\n"
            "  [green][✓] Proportions successfully normalized; values cleanly sum up to exactly 1.0 (or 100%).[/]\n"
            "  [yellow][!] High dispersion detected; the decimal distributions are spread across too many tiny categories.[/]\n"
            "  [red][✗] Empty dataset; division by zero is mathematically impossible, preventing proportion tracking.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        n = len(values)
        return {
            "return_value": {k: v / n for k, v in Counter(values).items()},
            "desc": desc,
        }

    @staticmethod
    def cumulative_count(values: list) -> dict[str, Any]:
        desc = (
            "Definition: A progressive running total of value frequencies compiled across an ordered or sorted list of your distinct items.\n"
            "Purpose: Measures the ongoing accumulation of data volume as you climb from the lowest distinct value up to the highest.\n"
            "ELI5: Line up students by age. Count the 10-year-olds (say there are 5). Then add the 11-year-olds (say there are 3, running total = 8). Then add the 12-year-olds (say there are 2, final total = 10).\n"
            "Example: For sorted values [A, A, B, C], the cumulative count dictionary map outputs {'A': 2, 'B': 3, 'C': 4}.\n"
            "Constraint: Heavily reliant on logical sorting. If your categories have no natural order (like sorting 'Blue', 'Green', 'Red'), the running accumulation loses its real-world meaning.\n"
            "Alternative: Use standard non-accumulative [bold]VALUE FREQUENCY TABLE[/] metrics if your categories are purely labels without a ranking.\n"
            "Format:\n"
            "  [green][✓] Orderly volume building; the final entry matches your global dataset count perfectly.[/]\n"
            "  [yellow][!] Sharp accumulation leaps; indicating massive, uneven concentration blocks at specific steps in your data scale.[/]\n"
            "  [red][✗] Dataset is empty; cannot establish an ordered progression map.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        counts = Counter(values)
        sorted_keys = sorted(counts.keys(), key=lambda x: (isinstance(x, str), x))
        cum = {}
        total = 0
        for k in sorted_keys:
            total += counts[k]
            cum[k] = total
        return {
            "return_value": cum,
            "desc": desc,
        }

    @staticmethod
    def cumulative_percentage(values: list) -> dict[str, Any]:
        desc = (
            "Definition: A progressive running total of relative frequencies, tracking the accumulated percentage from 0% to 100% across sorted items.\n"
            "Purpose: Crucial for Pareto analysis, helping you find exactly where the 80% boundary line or major market thresholds fall.\n"
            "ELI5: Adding up test grades from lowest to highest. By the time you finish adding up all the 'C' grades, you see that 70% of the entire class has been accounted for.\n"
            "Example: For sorted categories with counts resulting in 25% steps, the map tracks: {'Tier 1': 25.0, 'Tier 2': 50.0, 'Tier 3': 75.0, 'Tier 4': 100.0}.\n"
            "Constraint: If your dataset changes size constantly or contains un-orderable text categories, these running percentages flip into chaotic nonsense.\n"
            "Alternative: Utilize standard [bold]RELATIVE FREQUENCY TABLE[/] metrics to study items as individual isolated slices instead of a snowballing total.\n"
            "Format:\n"
            "  [green][✓] Clean percentage scaling; the final category finishes at exactly 100.0%.[/]\n"
            "  [yellow][!] Extremely aggressive growth; the first few steps capture nearly all the percentage, highlighting deep concentration inequality.[/]\n"
            "  [red][✗] No records provided; cannot compute percentages because dividing by zero total items is impossible.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        n = len(values)
        counts = Counter(values)
        sorted_keys = sorted(counts.keys(), key=lambda x: (isinstance(x, str), x))
        cum = {}
        total = 0
        for k in sorted_keys:
            total += counts[k]
            cum[k] = (total / n) * 100
        return {
            "return_value": cum,
            "desc": desc,
        }

    @staticmethod
    def percentile_10(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The 10th percentile of the dataset; the cut-off value below which exactly 10% of the sorted data points reside.\n"
            "Purpose: Isolates the bottom fringe layer of your data to help evaluate the earliest floor thresholds or low-end performance.\n"
            "ELI5: Testing the battery life of 100 phones. The 10th Percentile is the exact runtime of the 10th phone to die. 90% of the phones lasted longer than this point.\n"
            "Example: For an ordered array from 1 to 100, the 10th percentile sits squarely at 10.9.\n"
            "Constraint: Highly specialized for floor monitoring; it gives you zero visibility into how high or stable the upper 90% of your data mass behaves.\n"
            "Alternative: Look at the [bold]MEDIAN[/] or [bold]Q1 (25th Percentile)[/] if you want to study the core standard body of values rather than extreme bottom fringes.\n"
            "Format:\n"
            "  [green][✓] Low boundary established; bottom tier floor values are safe and meet expectations.[/]\n"
            "  [yellow][!] Floor is creeping dangerously low, suggesting the bottom 10% of your metrics are tanking out.[/]\n"
            "  [red][✗] Calculation blocked; dataset is empty or doesn't have enough numerical distribution points.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(
                np.percentile(StatisticsEngine._to_array(values), 10)
            ),
            "desc": desc,
        }

    @staticmethod
    def percentile_90(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The 90th percentile of the dataset; the cut-off value below which exactly 90% of the sorted data points reside.\n"
            "Purpose: Isolate the high-performance tier or peak stress threshold, capturing where your elite top 10% bracket begins.\n"
            "ELI5: Monitoring internet speed on a server. The 90th Percentile represents the top peak speeds reached, showing what the system is capable of delivering for the upper crust of traffic.\n"
            "Example: For an ordered array from 1 to 100, the 90th percentile sits squarely at 90.1.\n"
            "Constraint: Can easily be pulled or warped upwards by a handful of freak, astronomical outlier spikes sitting right on the upper border line.\n"
            "Alternative: Track [bold]Q3 (75th Percentile)[/] if you want a safer, more stable evaluation of upper-middle behavior that isn't influenced by top edge flukes.\n"
            "Format:\n"
            "  [green][✓] Upper boundary established; high performance tier is stable and predictable.[/]\n"
            "  [yellow][!] High boundary is spiking violently; indicating extreme, volatile performance swings in your top 10% tier.[/]\n"
            "  [red][✗] Calculation failed; empty dataset provided, preventing percentile extraction.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(
                np.percentile(StatisticsEngine._to_array(values), 90)
            ),
            "desc": desc,
        }

    @staticmethod
    def lower_outlier_boundary(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The traditional statistical fence calculated by subtracting 1.5 times the Interquartile Range from the first quartile (Q1 - 1.5 * IQR).\n"
            "Purpose: Establishes a strict, math-backed security boundary line. Any data point that falls below this threshold is officially flagged as an extreme low outlier.\n"
            "ELI5: Think of a playground fence. Regular data points play inside. If a value falls completely past this lower outlier fence, it's so abnormally small that it's likely a typo, error, or glitch.\n"
            "Example: If Q1 is 50 and IQR is 20, the boundary is 50 - (1.5 * 20) = 50 - 30 = 20.0. Any number below 20 is an outlier.\n"
            "Constraint: If your data naturally spreads out wide in a curve (like long-tail distributions), this standard formula will mistakenly flag perfectly valid data points as glitches.\n"
            "Alternative: Use the [bold]MEDIAN ABSOLUTE DEVIATION (MAD)[/] approach to identify outliers in heavily skewed or non-standard curves.\n"
            "Format:\n"
            "  [green][✓] Threshold clear; data points sitting above this line are statistically normal and clean.[/]\n"
            "  [yellow][!] Boundary is clipping near zero or negative space, indicating high spread in your bottom numbers.[/]\n"
            "  [red][✗] Empty array or degenerate values; boundary cannot be calculated, leaving your data unprotected from low glitches.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        q1v = np.percentile(arr, 25)
        iqrv = np.percentile(arr, 75) - q1v
        return {
            "return_value": float(q1v - 1.5 * iqrv),
            "desc": desc,
        }

    @staticmethod
    def upper_outlier_boundary(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The traditional statistical fence calculated by adding 1.5 times the Interquartile Range to the third quartile (Q3 + 1.5 * IQR).\n"
            "Purpose: Establishes a strict, math-backed security ceiling. Any data point that shoots past this threshold is officially flagged as an extreme high outlier.\n"
            "ELI5: Think of an alarm system ceiling. Normal high scores stay below it. If a data value bursts completely past this upper line, it is such an astronomical freak event that it needs to be isolated.\n"
            "Example: If Q3 is 100 and IQR is 30, the boundary ceiling is 100 + (1.5 * 30) = 100 + 45 = 145.0. Any number higher than 145 is a high outlier.\n"
            "Constraint: If your dataset contains massive legitimate growth trends (like exploding startup revenues), this formula will falsely tag your best successes as anomalies.\n"
            "Alternative: Look at raw [bold]PERCENTILE 90[/] or 99 values to track exceptional growth trends without filtering them out as errors.\n"
            "Format:\n"
            "  [green][✓] Boundary ceiling established; standard data entries sit safely below the warning line.[/]\n"
            "  [yellow][!] Warning line is heavily extended; the core spread is so wide that it requires a massive spike to trigger an outlier flag.[/]\n"
            "  [red][✗] Empty input list; impossible to erect a data security fence because no values exist.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        q3v = np.percentile(arr, 75)
        iqrv = q3v - np.percentile(arr, 25)
        return {
            "return_value": float(q3v + 1.5 * iqrv),
            "desc": desc,
        }

    @staticmethod
    def outlier_values(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: An array filter that extracts every individual numerical value sitting completely outside the standard inner fences (Q1 - 1.5*IQR and Q3 + 1.5*IQR).\n"
            "Purpose: Isolates and names the specific culprit data entries causing distribution skew, making data cleaning or error flagging possible.\n"
            "ELI5: Imagine a security guard writing down the specific names of students who are either freakishly early or incredibly late to school, completely ignoring everyone who arrives on normal schedule.\n"
            "Example: For [10, 20, 22, 24, 26, 30, 100], Q1 is 21, Q3 is 28, IQR is 7. The upper fence is 28 + (1.5 * 7) = 38.5. The isolated outlier value returned is [100.0].\n"
            "Constraint: If your sample contains legitimate, non-linear explosive growth patterns, this function will dump those brilliant data peaks into the outlier trash heap.\n"
            "Alternative: Use Z-score threshold filtering if your data represents a deeply verified normal distribution model.\n"
            "Format:\n"
            "  [green][✓] Clean dataset; no outlier elements were detected past the statistical fences.[/]\n"
            "  [yellow][!] Rogue values extracted; review the output list to ensure they aren't data entry typos.[/]\n"
            "  [red][✗] Empty dataset or severe corruption; unable to establish distribution boundaries for isolation.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        q1v = np.percentile(arr, 25)
        q3v = np.percentile(arr, 75)
        iqrv = q3v - q1v
        low = q1v - 1.5 * iqrv
        high = q3v + 1.5 * iqrv
        outliers = arr[(arr < low) | (arr > high)]
        return {
            "return_value": outliers.tolist() if len(outliers) > 0 else None,
            "desc": desc,
        }

    @staticmethod
    def outlier_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total integer count of numerical values that breach the lower or upper interquartile range boundaries.\n"
            "Purpose: Provides an immediate, clean quality score showing exactly how polluted or volatile your data distribution is.\n"
            "ELI5: Tallying up the total number of times an industrial machine experiences a freak pressure spike or power drop during the workday.\n"
            "Example: For [10, 20, 22, 24, 26, 30, 100], only the number 100 escapes the fence, meaning the total outlier count is exactly 1.\n"
            "Constraint: It only gives you the volume of anomalies; it does not tell you if they are spiking on the ultra-low end or the ultra-high end.\n"
            "Alternative: Combine this with [bold]OUTLIER VALUES[/] to view the actual identities of the numbers being tallied.\n"
            "Format:\n"
            "  [green][✓] Zero outliers found; your distribution is tight, smooth, and statistically pristine.[/]\n"
            "  [yellow][!] Low anomaly count; a tiny handful of values are straying, which could slightly skew sensitive averages.[/]\n"
            "  [red][✗] High anomaly contamination; numerous entries are bursting out of bounds, indicating systemic chaos.[/]"
        )
        if not values:
            return {"return_value": 0, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        q1v = np.percentile(arr, 25)
        q3v = np.percentile(arr, 75)
        iqrv = q3v - q1v
        low = q1v - 1.5 * iqrv
        high = q3v + 1.5 * iqrv
        return {
            "return_value": int(np.sum((arr < low) | (arr > high))),
            "desc": desc,
        }

    @staticmethod
    def coefficient_of_variation(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The ratio of the dataset's standard deviation directly relative to its mean, scaled out as a percentage ((Std / Mean) * 100).\n"
            "Purpose: Measures the relative dispersion of your data, allowing you to fairly compare volatility across completely different baseline scales.\n"
            "ELI5: Comparing the price fluctuation of a \$1 candy bar against a \$50,000 car. A \$1 variation is massive chaos for the candy bar but complete stability for the car. This metric fixes that scale.\n"
            "Example: If Mean = 20.0 and Standard Deviation = 5.0, the calculation is (5 / 20) * 100 = 25.0% variation score.\n"
            "Constraint: Becomes wildly unstable and completely unusable if your dataset mean creeps close to zero, causing the percentage score to shoot to infinity.\n"
            "Alternative: Use raw [bold]STANDARD DEVIATION[/] if your comparison items share the exact same unit baseline scale.\n"
            "Format:\n"
            "  [green][✓] Low coefficient variance; the data exhibits remarkable internal consistency relative to its scale baseline.[/]\n"
            "  [yellow][!] Moderate relative variance; data points are showing noticeable drift relative to the overall average size.[/]\n"
            "  [red][✗] Mean is zero or data is missing; relative percentage scaling is mathematically impossible to process.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = np.mean(arr)
        if m == 0:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float((np.std(arr, ddof=1) / m) * 100),
            "desc": desc,
        }

    @staticmethod
    def mean_absolute_deviation(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The mathematical average of the absolute distances between every individual data point and the dataset mean.\n"
            "Purpose: Quantifies dispersion using standard averages without squaring distances, preventing outliers from dominating the weight.\n"
            "ELI5: Sitting a group of children down and measuring exactly how many inches away each child is sitting from the exact center star drawn on the carpet.\n"
            "Example: For [2, 4, 9], the mean is 5.0. The absolute distances from 5 are [3, 1, 4]. The average of those distances is (3 + 1 + 4) / 3 = 2.66.\n"
            "Constraint: Lacks clean algebraic derivative properties, making it far less common in downstream machine learning loss functions compared to Standard Deviation.\n"
            "Alternative: Choose [bold]STANDARD DEVIATION[/] if you require a traditional metric that plays smoothly with advanced algebraic modeling.\n"
            "Format:\n"
            "  [green][✓] Low absolute deviation; points sit uniformly and comfortably close to the computed average line.[/]\n"
            "  [yellow][!] Expanding absolute deviation; data points are choosing to drift further away from the main center line.[/]\n"
            "  [red][✗] Empty array tracking; cannot compile absolute variance distances because no numerical elements exist.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.mean(np.abs(arr - np.mean(arr)))),
            "desc": desc,
        }

    @staticmethod
    def trimmed_mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The mathematical average calculated after cleanly cutting away a specified percentage (here, 5%) of the lowest and highest sorted entries.\n"
            "Purpose: Offers a highly stable central location estimate that remains completely unaffected by extreme tail spikes or data corruption errors.\n"
            "ELI5: In Olympic gymnastics scoring, judges automatically throw out the single lowest score and single highest score, then average the rest to prevent bias.\n"
            "Example: In a sorted list of 20 numbers, a 5% trim slices away exactly 1 item from the absolute bottom and 1 item from the absolute top before averaging.\n"
            "Constraint: If your tails actually contain critical real-world failure warnings (like stock market crashes), a trimmed mean will actively hide that reality from you.\n"
            "Alternative: Use the traditional [bold]MEAN[/] if keeping track of absolute edge fluctuations is vital to your operation.\n"
            "Format:\n"
            "  [green][✓] Robust center established; extreme edge values have been successfully trimmed away to provide a pristine core average.[/]\n"
            "  [yellow][!] Trimmed mean deviates from the true mean; indicating that significant tail data was discarded during cleanup.[/]\n"
            "  [red][✗] Empty input string array; unable to execute trimming slices because the list lacks required data points.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(
                sp_stats.trim_mean(StatisticsEngine._to_array(values), 0.05)
            ),
            "desc": desc,
        }

    @staticmethod
    def spread_score(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: A custom structural ratio computed by dividing the standard deviation by the absolute total range of the dataset (Std / Range).\n"
            "Purpose: Gauges data density; showing whether your variation is caused by a few isolated edge spikes or a broad, uniform distribution scatter.\n"
            "ELI5: If you scatter toys across a room, this score tells you if they are spread evenly across every square foot or if they are all lumped together with one rogue toy thrown across the house.\n"
            "Example: If Std Dev is 10.0 and total Range is 40.0, your custom Spread Score evaluates to 10 / 40 = 0.25.\n"
            "Constraint: Becomes entirely useless or returns a division error if the range is zero (meaning all numbers in your dataset are identical clones).\n"
            "Alternative: Rely on standard [bold]KURTOSIS[/] or [bold]SKEW[/] metrics for fully normalized, industry-recognized distribution shape analytics.\n"
            "Format:\n"
            "  [green][✓] Normal spread score; internal variation is properly balanced against total boundary limits.[/]\n"
            "  [yellow][!] Low score ratio; indicates that a massive total range boundary is being caused artificially by a few solitary outliers.[/]\n"
            "  [red][✗] Flat line data (Range = 0) or empty array; cannot compute density because variation width does not exist.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        r = float(np.max(arr) - np.min(arr))
        if r == 0:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(np.std(arr, ddof=1) / r),
            "desc": desc,
        }

    @staticmethod
    def range_percentage(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total data range expressed relative to the dataset mean as a direct percentage scale ratio ((Range / Mean) * 100).\n"
            "Purpose: Standardizes total endpoint boundary size, allowing analysts to compare maximum system swings across shifting baselines.\n"
            "ELI5: If a child's height varies by 10 inches over a year, that's huge. If an adult skyscraper's height varies by 10 inches in wind, it's tiny. This normalizes the window scale.\n"
            "Example: If Max - Min gives a total Range of 10.0 and your Mean is 50.0, the calculation equals (10 / 50) * 100 = 20.0% range percentage.\n"
            "Constraint: Breaks down instantly and crashes out if your distribution mean hits 0, causing the percentage expression to explode.\n"
            "Alternative: Utilize standard [bold]COEFFICIENT OF VARIATION[/] if you need a relative metric that relies on standard deviation instead of extreme edges.\n"
            "Format:\n"
            "  [green][✓] Stable boundary ratio; total endpoint swing width is healthy and proportionate to the dataset baseline.[/]\n"
            "  [yellow][!] High range percentage; your system endpoint swings are large relative to the average size, showing high volatility.[/]\n"
            "  [red][✗] Division by a zero mean or empty list; relative endpoint percentage computation is blocked.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = np.mean(arr)
        if m == 0:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": float(((np.max(arr) - np.min(arr)) / m) * 100),
            "desc": desc,
        }

    @staticmethod
    def interval_width(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The mathematical step width or span size allocated to each individual category bucket when applying Sturges' Rule for histograms (Range / Sturges Bin Count).\n"
            "Purpose: Ensures your histogram blocks are perfectly sized so that your charts don't look awkwardly clumped together or over-segmented.\n"
            "ELI5: You have a pile of various sized rocks. This formula calculates exactly how wide your sorting boxes need to be so that every rock fits into an orderly chart category.\n"
            "Example: If your total data range is 50.0 and Sturges' Rule dictates exactly 5 bins, your calculated Interval Width is 50 / 5 = 10.0 per bucket.\n"
            "Constraint: Assumes your data is normally distributed. If your data is heavily skewed or contains huge gaps, this width size will create empty, useless chart segments.\n"
            "Alternative: Adopt the Freedman-Diaconis rule or Scott's rule for width selection if your dataset contains heavy outlier strings.\n"
            "Format:\n"
            "  [green][✓] Optimized interval step size calculated; ready to render perfectly proportioned frequency histograms.[/]\n"
            "  [yellow][!] Narrow step width; small variation windows imply you will need to monitor highly specific numerical data bands.[/]\n"
            "  [red][✗] Zero width or missing elements; data lacks any internal range, preventing interval segmentation features.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        bins = int(np.ceil(np.log2(len(arr))) + 1)
        r = float(np.max(arr) - np.min(arr))
        return {
            "return_value": float(r / bins) if bins > 0 else None,
            "desc": desc,
        }

    @staticmethod
    def bin_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The optimal number of histogram category grouping slots calculated using Sturges' formula, which scales logarithmically based on sample size (Ceil(log2(N)) + 1).\n"
            "Purpose: Eliminates human guesswork when creating charts, calculating the perfect mathematical quantity of columns to present your data cleanly.\n"
            "ELI5: Figuring out exactly how many sorting bins you need to label and set up on a warehouse floor to organize incoming packages by weight.\n"
            "Example: For a dataset containing exactly 32 individual records, log2(32) is 5. Adding 1 gives an optimal Sturges bin count of 6.\n"
            "Constraint: Greatly underestimates the required number of bins if your dataset is massive (e.g., millions of rows), leading to charts that look overly compressed.\n"
            "Alternative: Switch to the Freedman-Diaconis chart rule for massive data collections to allow bin quantities to grow dynamically with variance.\n"
            "Format:\n"
            "  [green][✓] Optimal category count established; chart distribution boxes are scaled perfectly for this sample volume.[/]\n"
            "  [yellow][!] Low bin count; very small sample sizes force compressed groupings, which can hide subtle data patterns.[/]\n"
            "  [red][✗] Empty array tracking; cannot establish organizational chart categories because zero elements are present.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": int(np.ceil(np.log2(len(values))) + 1),
            "desc": desc,
        }

    @staticmethod
    def data_span(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total linear distance covered from the absolute lowest value to the absolute highest value (Max - Min). Directly identical to Range.\n"
            "Purpose: Measures the complete boundary footprint map occupied by your numerical data universe.\n"
            "ELI5: Finding the exact distance from the absolute front bumper to the rear bumper of a truck to ensure it can fit inside a parking garage stall.\n"
            "Example: Data Span for a list containing metrics [12.5, 45.0, 8.0, 92.1] evaluates directly to 92.1 - 8.0 = 84.1.\n"
            "Constraint: Completely unprotected against edge distortion. A single data entry error or typo instantly ruins the metric's accuracy.\n"
            "Alternative: Utilize the [bold]CENTRAL 80% RANGE[/] to track total domain span while shielding your metrics from edge glitches.\n"
            "Format:\n"
            "  [green][✓] Healthy span footprint; upper and lower boundaries sit within normal operating parameters.[/]\n"
            "  [yellow][!] Broad data span; high distance limits signal a massive gap between your best-case and worst-case rows.[/]\n"
            "  [red][✗] Empty element array; data span is non-existent because no coordinates are available to evaluate.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": float(np.max(arr) - np.min(arr)),
            "desc": desc,
        }

    @staticmethod
    def duplicate_count(values: list) -> dict[str, Any]:
        desc = (
            "Definition: The total number of redundant or repeated entries present in the dataset, calculated by subtracting unique entries from the absolute total count (Total - Unique).\n"
            "Purpose: Measures data redundancy or cloning frequency, indicating whether information is highly repetitive or composed of unique standalone entries.\n"
            "ELI5: If you look at a guest list with 10 names, but 'John Doe' is written down 3 times, you have 2 extra redundant entries. Your duplicate count is 2.\n"
            "Example: For [1, 2, 2, 3, 3, 3], total elements = 6, unique elements = 3. Duplicate count is 6 - 3 = 3.\n"
            "Constraint: Treats identical values across different meanings or rows blindly as duplicates. It cannot distinguish between a data entry error and two customers who happen to make the exact same transaction amount.\n"
            "Alternative: Combine with a [bold]VALUE FREQUENCY TABLE[/] to see exactly which specific items are repeating rather than just getting a single total count.\n"
            "Format:\n"
            "  [green][✓] Zero duplicates; every record is distinct, clean, and unique across the board.[/]\n"
            "  [yellow][!] Redundant entries detected; signifies potential data repetition, double-submisions, or recurring categorical profiles.[/]\n"
            "  [red][✗] Extreme duplication; the overwhelming majority of your rows are redundant copies, suggesting a lack of diverse content.[/]"
        )
        n = len(values)
        unique = len(set(values))
        return {
            "return_value": n - unique,
            "desc": desc,
        }

    @staticmethod
    def data_density(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The ratio of total data points relative to the absolute range over which they are spread (Total Count / Range).\n"
            "Purpose: Quantifies how tightly packed or concentrated your data observations are across their operational boundary footprint.\n"
            "ELI5: Imagine 100 people standing in a tiny elevator versus 100 people scattered across an entire football field. The density score tells you how crowded the values are inside their domain boundaries.\n"
            "Example: For a dataset with 20 items where the maximum is 15 and the minimum is 5, the total range is 10. The data density is 20 / 10 = 2.0 items per unit range.\n"
            "Constraint: Highly sensitive to extreme outlier boundaries. A single rogue maximum thrown far out into space explodes your range, making your core dataset look artificially sparse.\n"
            "Alternative: Divide total count by the [bold]CENTRAL 50% RANGE (IQR)[/] to calculate a robust density metric that ignores edge anomalies.\n"
            "Format:\n"
            "  [green][✓] Highly dense distribution; points are tightly clustered together, indicating high consistency or continuous measurement activity.[/]\n"
            "  [yellow][!] Low density footprint; data entries are sparse or widely separated across a broad domain range.[/]\n"
            "  [red][✗] Range is zero or dataset is empty; cannot evaluate packing density because width boundaries are missing or collapsed.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        r = float(np.max(arr) - np.min(arr))
        if r == 0:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": len(values) / r,
            "desc": desc,
        }

    @staticmethod
    def positive_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The absolute total count of numerical values inside the dataset that are strictly greater than zero (Value > 0).\n"
            "Purpose: Isolates growth metrics, upward gains, asset revenues, or forward-moving values from neutral or negative losses.\n"
            "ELI5: Looking through a bank statement and counting exactly how many times you deposited money or got paid, rather than spending it.\n"
            "Example: For [-5, -2, 0, 3, 8.5], the numbers 3 and 8.5 are positive, resulting in an exact count of 2.\n"
            "Constraint: It strictly evaluates sign boundaries, treating a tiny value like 0.0001 identical to a massive value like 1,000,000.\n"
            "Alternative: Calculate a percentage ratio of positive counts relative to the global [bold]COUNT[/] to find the real success rate.\n"
            "Format:\n"
            "  [green][✓] Predominantly positive entries; indicating persistent upward trajectories, financial gains, or constructive states.[/]\n"
            "  [yellow][!] Diminishing positive counts; zero or negative records are beginning to encroach on your dataset pool.[/]\n"
            "  [red][✗] Zero positive items found; the entire dataset is composed exclusively of negative losses, drains, or neutral states.[/]"
        )
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": int(np.sum(arr > 0)),
            "desc": desc,
        }

    @staticmethod
    def negative_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The absolute total count of numerical values inside the dataset that are strictly less than zero (Value < 0).\n"
            "Purpose: Measures the volume of losses, drops, deficits, sub-zero temperatures, or downward system retractions.\n"
            "ELI5: Looking through a ledger and counting exactly how many checks you wrote or times you lost points in a game.\n"
            "Example: For [-5, -2, 0, 3, 8.5], the numbers -5 and -2 are negative, yielding an exact count of 2.\n"
            "Constraint: Counts all negative items equally, meaning it treats a cataclysmic system crash value of -9999 exactly like a safe minor dip of -0.1.\n"
            "Alternative: Review the absolute [bold]MINIMUM[/] value to gauge the maximum damage or deepest point of the negative tail.\n"
            "Format:\n"
            "  [green][✓] Zero negative records; indicating a completely clean run free of deficits, spending transactions, or downward failures.[/]\n"
            "  [yellow][!] Negative values popping up; indicating active resource consumption, financial costs, or retracting metrics.[/]\n"
            "  [red][✗] Purely negative distribution; dataset is completely saturated with deficits or down-tail trends.[/]"
        )
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": int(np.sum(arr < 0)),
            "desc": desc,
        }

    @staticmethod
    def zero_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total number of values inside the dataset that are exactly equal to zero (Value == 0).\n"
            "Purpose: Tracks baseline inactivity, neutral statuses, empty balances, or dead-stop operational resting points.\n"
            "ELI5: Counting how many days a salesperson made absolutely zero sales, or how many times a production machine was turned completely off.\n"
            "Example: For [12.5, 0.0, -3.0, 0.0, 5.0], there are two exact zero instances, giving a count of 2.\n"
            "Constraint: Highly unforgiving with floating-point data; a value that is almost zero due to tiny computational rounding fragments (like 0.000000001) will be completely skipped.\n"
            "Alternative: Apply a tiny precision tolerance boundary (an epsilon check) if you need to catch values that are practically zero.\n"
            "Format:\n"
            "  [green][✓] Zero count is expectedly low or high; system matches intended activity thresholds perfectly.[/]\n"
            "  [yellow][!] Inactivity warning; a growing volume of exact zeros suggests stalls, system idling, or unpopulated data events.[/]\n"
            "  [red][✗] Absolute zero lock; the entire collection is flatlined at zero, signifying a total lack of dynamic movement.[/]"
        )
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": int(np.sum(arr == 0)),
            "desc": desc,
        }

    @staticmethod
    def even_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The count of integer data values that are perfectly divisible by two with zero remainder (Value % 2 == 0).\n"
            "Purpose: Frequently utilized in computer science indexing, structural partitioning, digital pagination, or parsing patterns based on parity splits.\n"
            "ELI5: Counting items that can be divided evenly into couples or pairs without leaving a single odd item left over.\n"
            "Example: For [1, 2, 4, 7, 10], the even numbers are 2, 4, and 10, resulting in a count of 3.\n"
            "Constraint: Python's modulo operator will round down or truncate floating-point numbers awkwardly (e.g., treating 4.2 as an odd pattern step), meaning it is best reserved for strict integer counts.\n"
            "Alternative: Use type casting or filter for integer parameters before executing strict modular parity evaluations.\n"
            "Format:\n"
            "  [green][✓] Even numbers categorized; structural index patterns or round pairs are cleanly mapped.[/]\n"
            "  [yellow][!] Asymmetric parity allocation; the dataset balance is listing heavily toward or away from round pairings.[/]\n"
            "  [red][✗] Zero even values; the input list contains exclusively odd entries, preventing equal dual partitioning.[/]"
        )
        return {
            "return_value": sum(1 for v in values if v % 2 == 0),
            "desc": desc,
        }

    @staticmethod
    def odd_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The count of integer data values that are not perfectly divisible by two, leaving a modular remainder of one (Value % 2 != 0).\n"
            "Purpose: Used for identifying alternating rows, processing step offsets, slot distributions, or verifying hardware data transmission tracks.\n"
            "ELI5: Counting items where, if you try to group them into pairs, there will always be exactly one lonely item left over without a partner.\n"
            "Example: For [1, 2, 4, 7, 10], the odd numbers are 1 and 7, resulting in a count of 2.\n"
            "Constraint: Will misinterpret floating-point decimal entries if they are submitted directly, as fractional remainders trick simple modulo operations.\n"
            "Alternative: Pair with an [bold]EVEN COUNT[/] to cross-check and ensure the sum matches your full valid integer pool total.\n"
            "Format:\n"
            "  [green][✓] Odd numbers categorized; alternating indexing parameters are successfully extracted.[/]\n"
            "  [yellow][!] Shifted parity volume; your collection balances display uneven structural alignment between even and odd slots.[/]\n"
            "  [red][✗] Zero odd numbers present; the dataset is entirely filled with even values, showing complete uniform pair alignment.[/]"
        )
        return {
            "return_value": sum(1 for v in values if v % 2 != 0),
            "desc": desc,
        }

    @staticmethod
    def above_mean_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total number of records that score strictly higher than the overall calculated average of the dataset (Value > Mean).\n"
            "Purpose: Identifies how many observations are outperforming or exceeding the generic baseline level of the group.\n"
            "ELI5: Sizing up a basketball team's average point score, then counting exactly how many players scored more than that average during the game.\n"
            "Example: For [10, 10, 10, 50], the mean is (10+10+10+50)/4 = 20. Only the number 50 is greater than 20, so the count is exactly 1.\n"
            "Constraint: If a single massive outlier pulls the mean way up (like the 50 in the example), almost the entire dataset will end up falling below it, making a high count rare.\n"
            "Alternative: Count values above the [bold]MEDIAN[/] if you want an exact 50/50 split counter that isn't warped by single massive spikes.\n"
            "Format:\n"
            "  [green][✓] Symmetrical distribution; roughly half the dataset sits above the average line, indicating a balanced curve.[/]\n"
            "  [yellow][!] Low count above mean; signifies a heavily skewed distribution where a few top performers are pulling the average up for everyone else.[/]\n"
            "  [red][✗] Missing records or zero count; no values rise above the line, indicating an entirely flat or empty dataset pool.[/]"
        )
        if not values:
            return {"return_value": 0, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": int(np.sum(arr > np.mean(arr))),
            "desc": desc,
        }

    @staticmethod
    def below_mean_count(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The total number of records that score strictly lower than the overall calculated average of the dataset (Value < Mean).\n"
            "Purpose: Measures the volume of data lagging behind or sitting underneath the standard group baseline.\n"
            "ELI5: Checking the average fuel efficiency of a fleet of trucks, then counting exactly how many trucks are burning gas faster than that average baseline.\n"
            "Example: For [10, 10, 10, 50], the mean is 20. The three 10s are all less than 20, so your below-mean count is exactly 3.\n"
            "Constraint: Can easily look over-populated if a few positive outliers drag the mean upward, making completely normal scores look deficient.\n"
            "Alternative: Track values below the [bold]MEDIAN[/] to see a pure geographic mid-split count that ignores tail dragging.\n"
            "Format:\n"
            "  [green][✓] Symmetrical group balance; lower entries match upper entries across a well-distributed center line.[/]\n"
            "  [yellow][!] High count below mean; a massive cluster of values sits beneath the average because a tiny elite tier is spiking the mean high.[/]\n"
            "  [red][✗] Zero records below average; everything sits perfectly at or above baseline, or dataset is empty.[/]"
        )
        if not values:
            return {"return_value": 0, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        return {
            "return_value": int(np.sum(arr < np.mean(arr))),
            "desc": desc,
        }

    @staticmethod
    def closest_to_mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The individual data point from the dataset whose value sits at the absolute minimum distance from the computed arithmetic mean.\n"
            "Purpose: Identifies the most mathematically 'typical' or representative real observation in the collection, serving as the physical anchor for the average.\n"
            "ELI5: Imagine calculating that the average height of a basketball team is exactly 6 feet. This function scans the locker room to find the one player whose actual height is closest to that 6-foot average.\n"
            "Example: For [10, 11, 21], the mean is 14.0. The absolute differences are [4, 3, 7]. The value closest to the mean is 11.0.\n"
            "Constraint: If the dataset is bimodal (like two distinct clusters at 10 and 90), the mean will sit in the empty middle at 50. The point 'closest' to 50 might be 10 or 90, meaning it is not representative of a real center cluster.\n"
            "Alternative: Look at the [bold]MEDIAN[/] if your goal is to find the physical positional center value of a heavily split distribution.\n"
            "Format:\n"
            "  [green][✓] Representative anchor isolated; a real observation sits comfortably close to your mathematical average.[/]\n"
            "  [yellow][!] Distant midpoint anchor; the closest point is still far from the mean, indicating a sparse or split distribution center.[/]\n"
            "  [red][✗] Empty array; cannot locate an observation closest to the average because no values exist.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = np.mean(arr)
        return {
            "return_value": float(arr[np.argmin(np.abs(arr - m))]),
            "desc": desc,
        }

    @staticmethod
    def farthest_from_mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The individual data point from the dataset whose value sits at the absolute maximum distance from the computed arithmetic mean.\n"
            "Purpose: Instantly extracts the most extreme outlier or dominant boundary value, pointing directly to your primary source of variance.\n"
            "ELI5: Scanning a classroom's test scores to find the one student whose grade is furthest away from the class average—whether they scored way higher or way lower than everyone else.\n"
            "Example: For [10, 11, 21], the mean is 14.0. The distances are [4, 3, 7]. The value furthest from the mean is 21.0.\n"
            "Constraint: It evaluates absolute distance blindly. It does not explicitly tell you if this furthest point is an extreme positive spike or an extreme negative drop.\n"
            "Alternative: Compare the [bold]MINIMUM[/] and [bold]MAXIMUM[/] values directly to see which specific side of the boundary tail is stretching furthest.\n"
            "Format:\n"
            "  [green][✓] Outlier boundary identified; helps pin down the exact worst-case or best-case record skewing your system average.[/]\n"
            "  [yellow][!] Tight maximum variance; even the furthest point is close to the average, indicating a highly uniform, low-variance cluster.[/]\n"
            "  [red][✗] Empty data array; impossible to measure variance distances because no elements are available.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = np.mean(arr)
        return {
            "return_value": float(arr[np.argmax(np.abs(arr - m))]),
            "desc": desc,
        }

    @staticmethod
    def lower_half_mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The arithmetic mean computed exclusively from the lower 50% of the dataset values, using the median as the dividing line.\n"
            "Purpose: Measures the average behavior of your lower-performing or bottom-tier observations, isolating floor trends.\n"
            "ELI5: Sorting a company's departmental budgets from cheapest to most expensive, slicing the list right down the middle, and finding the average of the cheaper half.\n"
            "Example: For sorted values [10, 20, 30, 40], the lower half is [10, 20]. The lower half mean is (10 + 20) / 2 = 15.0.\n"
            "Constraint: It cuts the data strictly by position count, meaning heavy value clusters near the median line can obscure deeper bottom-end variations.\n"
            "Alternative: Use [bold]PERCENTILE_10[/] if you want to isolate the absolute bottom floor fringe instead of the entire lower half body.\n"
            "Format:\n"
            "  [green][✓] Lower tier baseline calculated; provides a clean, stable profile of your bottom-half data behavior.[/]\n"
            "  [yellow][!] Falling lower average; indicates that the bottom half of your system is losing ground or dropping in performance.[/]\n"
            "  [red][✗] Array length too short or empty; insufficient data present to divide the collection into halves for evaluation.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = np.sort(StatisticsEngine._to_array(values))
        mid = len(arr) // 2
        return {
            "return_value": float(np.mean(arr[:mid])) if mid > 0 else None,
            "desc": desc,
        }

    @staticmethod
    def upper_half_mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The arithmetic mean computed exclusively from the upper 50% of the dataset values, using the median as the dividing line.\n"
            "Purpose: Measures the average behavior of your higher-performing or top-tier observations, isolating ceiling trends.\n"
            "ELI5: Sorting school test scores from lowest to highest, splitting the class in half, and finding the average score of the top-performing half.\n"
            "Example: For sorted values [10, 20, 30, 40], the upper half is [30, 40]. The upper half mean is (30 + 40) / 2 = 35.0.\n"
            "Constraint: Can be heavily inflated by a single astronomical outlier on the top edge, making the entire upper half look more successful than it actually is.\n"
            "Alternative: Review the [bold]TRIMMED MEAN[/] if you need a high-end summary that filters out extreme edge spikes.\n"
            "Format:\n"
            "  [green][✓] Upper tier baseline calculated; provides a stable operational picture of your top-half system profile.[/]\n"
            "  [yellow][!] Spiking upper average; indicates an elite group is pulling away, or variance is rising at the high end.[/]\n"
            "  [red][✗] Empty array tracking; cannot calculate an upper-tier average because no records are present.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = np.sort(StatisticsEngine._to_array(values))
        mid = len(arr) // 2
        return {
            "return_value": float(np.mean(arr[mid:])),
            "desc": desc,
        }

    @staticmethod
    def data_balance(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The structural ratio of the number of items falling below the mean relative to the number of items sitting above the mean (Below Count / Above Count).\n"
            "Purpose: Acts as a direct diagnostic tool for skewness, showing how data point density is clustered around the average line.\n"
            "ELI5: A balance score of 1.0 means your dataset acts like a perfectly balanced seesaw, with an equal number of people sitting on both sides of the center average pin.\n"
            "Example: If 30 points are below the mean and 10 points are above it, the data balance ratio is 30 / 10 = 3.0 (meaning 3 times as many elements sit below the average).\n"
            "Constraint: It only tracks point counts, not values. A balance of 1.0 can still occur if one side has entries miles away and the other side has entries inches away.\n"
            "Alternative: Check the [bold]MEDIAN DIFFERENCE[/] to see the actual value-based distance shift between structural centers.\n"
            "Format:\n"
            "  [green][✓] Balanced ratio near 1.0; data points are distributed evenly above and below the average line.[/]\n"
            "  [yellow][!] High or low ratio shift; data density is heavily clustered on one side, meaning the mean is being pulled by outliers on the opposite side.[/]\n"
            "  [red][✗] Zero above-mean records or empty list; division by zero is impossible, preventing balance tracking.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        m = np.mean(arr)
        above = int(np.sum(arr > m))
        below = int(np.sum(arr < m))
        if above == 0:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": below / above,
            "desc": desc,
        }

    @staticmethod
    def symmetry_score(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The absolute distance between the mean and median, normalized by dividing it by the standard deviation (abs(Mean - Median) / StdDev).\n"
            "Purpose: Provides a standardized, scale-free symmetry metric. A score of 0.0 indicates a perfectly symmetric distribution curve.\n"
            "ELI5: Measuring how off-center a building's foundation is. If the geographic middle (median) and the weight center (mean) sit in the exact same spot, your symmetry score is 0.0.\n"
            "Example: If Mean = 50, Median = 45, and Std Dev = 10, the score is abs(50 - 45) / 10 = 5 / 10 = 0.5.\n"
            "Constraint: A score of 0 does not guarantee a perfect bell curve; it just means the two center points perfectly align, which can happen in complex bimodal data.\n"
            "Alternative: Run an advanced mathematical [bold]SKEW[/] function for full structural shape classification.\n"
            "Format:\n"
            "  [green][✓] Symmetrical center (score near 0.0); mean and median align perfectly, indicating a beautifully balanced curve.[/]\n"
            "  [yellow][!] Noticeable asymmetry; outliers are pulling the average away from the positional midpoint, warping the distribution shape.[/]\n"
            "  [red][✗] Standard deviation is zero or empty array; distribution is completely flat or missing, making symmetry metrics impossible to run.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        s = float(np.std(arr, ddof=1))
        if s == 0:
            return {"return_value": 0.0, "desc": desc}
        return {
            "return_value": float(abs(np.mean(arr) - np.median(arr)) / s),
            "desc": desc,
        }

    @staticmethod
    def normalized_mean(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The position of the mean scaled strictly within a bounded 0.0 to 1.0 window relative to the dataset boundaries ((Mean - Min) / (Max - Min)).\n"
            "Purpose: Reveals exactly where your average sits relative to the endpoints. A score of 0.5 means the average sits perfectly at the boundary center.\n"
            "ELI5: If the minimum possible score is 0 and the maximum is 100, and the average is 75, your normalized mean is 0.75. It maps the average on a clean percentage track.\n"
            "Example: For [10, 20, 90], Mean = 40, Min = 10, Max = 90. The normalized calculation is (40 - 10) / (90 - 10) = 30 / 80 = 0.375.\n"
            "Constraint: Extreme outlier spikes on the endpoints will compress this score artificially, making a healthy average look heavily skewed toward one side.\n"
            "Alternative: Track the [bold]MIDRANGE[/] metric to view the raw un-normalized boundary midpoint value.\n"
            "Format:\n"
            "  [green][✓] Centered average (near 0.5); the mean sits comfortably in the middle of your operational boundaries.[/]\n"
            "  [yellow][!] Off-center mean; the average sits dangerously close to 0.0 or 1.0, showing that data is heavily compressed against one wall.[/]\n"
            "  [red][✗] Collapsed bounds (Max = Min) or empty list; boundaries have zero width, preventing normalization scaling.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        mn, mx = float(np.min(arr)), float(np.max(arr))
        if mx == mn:
            return {"return_value": 0.0, "desc": desc}
        return {
            "return_value": float((np.mean(arr) - mn) / (mx - mn)),
            "desc": desc,
        }

    @staticmethod
    def normalized_stdv(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The standard deviation divided directly by the dataset's absolute total range (StdDev / (Max - Min)).\n"
            "Purpose: Expresses standard volatility as a fraction of the total boundary width, standardizing variation across different systems.\n"
            "ELI5: Checking if the internal speed changes of a train are small or large relative to the maximum speed gap between a dead stop and full throttle.\n"
            "Example: If Std Dev is 5.0 and your Max - Min Range is 25.0, your normalized variation score is 5 / 25 = 0.20.\n"
            "Constraint: If a single freak outlier creates an artificially massive total range, this score will drop near zero, hiding real internal volatility.\n"
            "Alternative: Use the standard [bold]COEFFICIENT OF VARIATION[/] if you want to normalize variance using the mean instead of extreme endpoints.\n"
            "Format:\n"
            "  [green][✓] Low boundary variation; internal volatility occupies a small, controlled fraction of your total range width.[/]\n"
            "  [yellow][!] Wide normalized variance; internal data scattering is chaotic, filling up a massive portion of your boundary limits.[/]\n"
            "  [red][✗] Range boundary is zero or empty; variation width does not exist, blocking normalization math.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        arr = StatisticsEngine._to_array(values)
        r = float(np.max(arr) - np.min(arr))
        if r == 0:
            return {"return_value": 0.0, "desc": desc}
        return {
            "return_value": float(np.std(arr, ddof=1) / r),
            "desc": desc,
        }

    @staticmethod
    def peak_density(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The frequency count of the single most common value (the mode) divided by the total number of data items in the dataset (Mode Count / Total Count).\n"
            "Purpose: Measures value concentration severity, tracking whether a single observation absolutely dominates the entire dataset population.\n"
            "ELI5: If you poll 10 people and 8 of them choose 'Pizza', your peak density is 8 / 10 = 0.80. A massive concentration peak exists on that single choice.\n"
            "Example: For [1, 2, 2, 2, 3], the mode '2' appears 3 times out of 5 total items. Peak density is 3 / 5 = 0.60.\n"
            "Constraint: In continuous numeric floating-point fields (like 12.34567), values rarely match exactly, rendering peak density close to 0.0 regardless of distribution shape.\n"
            "Alternative: Switch to a [bold]VALUE FREQUENCY TABLE[/] or group continuous values into categorical bins to track real density trends.\n"
            "Format:\n"
            "  [green][✓] Evenly spread population; no single value dominates the dataset excessively.[/]\n"
            "  [yellow][!] Rising peak concentration; a single value is swallowing up a large percentage of your records, creating a massive spike trend.[/]\n"
            "  [red][✗] Empty input array; unable to calculate density peaks because no data elements exist.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        counts = Counter(values)
        mc = counts.most_common(1)[0][1]
        return {
            "return_value": mc / len(values),
            "desc": desc,
        }

    @staticmethod
    def data_uniformity(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The ratio of unique values relative to the absolute total length of the dataset (Unique Count / Total Count). A score of 1.0 means every entry is unique.\n"
            "Purpose: Evaluates dataset diversity, identifying whether your records are highly varied or consist of repetitive entries.\n"
            "ELI5: Checking a deck of cards. If every single card you draw is unique, your data uniformity score is a perfect 1.0. If you keep drawing duplicates, the score drops toward 0.0.\n"
            "Example: For [5, 5, 10, 20], there are 3 unique values out of 4 total items. Data uniformity is 3 / 4 = 0.75.\n"
            "Constraint: Does not tell you which specific items are repeating or how often; it only scales global distinctness.\n"
            "Alternative: Track [bold]DUPLICATE COUNT[/] if you want to view the raw count of redundant entries instead of a percentage ratio.\n"
            "Format:\n"
            "  [green][✓] High uniformity (near 1.0); every record is distinct and unique, indicating high diversity or precise measurements.[/]\n"
            "  [yellow][!] Low uniformity; heavy categorical repetition is compressing the diversity of your collection pool.[/]\n"
            "  [red][✗] Empty array; impossible to gauge uniformity because no observations are present.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": len(set(values)) / len(values),
            "desc": desc,
        }

    @staticmethod
    def value_concentration(values: list[float]) -> dict[str, Any]:
        desc = (
            "Definition: The exact inverse of data uniformity, calculated as 1 minus the uniformity ratio (1 - (Unique Count / Total Count)).\n"
            "Purpose: Measures redundancy concentration. A score of 0.0 means perfect diversity (zero duplicates), while scores near 1.0 indicate high repetition.\n"
            "ELI5: A score of 0.90 means that 90% of your entire dataset is filled with duplicate values, showing that a small set of information is repeating over and over.\n"
            "Example: For [5, 5, 10, 20], Uniformity is 0.75. Value Concentration is 1 - 0.75 = 0.25 (meaning 25% of the data mass is compressed duplication).\n"
            "Constraint: It scales up with duplication volume but remains blind to whether that concentration is locked into a single value or spread across multiple distinct labels.\n"
            "Alternative: Inspect a full [bold]RELATIVE FREQUENCY TABLE[/] to map out the exact share of each individual category peak.\n"
            "Format:\n"
            "  [green][✓] Zero concentration (0.0); data is completely diverse with zero repetitive clutter or cloned records.[/]\n"
            "  [yellow][!] High concentration; information is condensing heavily into repetitive loops, indicating a uniform or redundant environment.[/]\n"
            "  [red][✗] Empty input pool; concentration metrics cannot be evaluated because no data points are present.[/]"
        )
        if not values:
            return {"return_value": None, "desc": desc}
        return {
            "return_value": 1 - (len(set(values)) / len(values)),
            "desc": desc,
        }

    # Dispatch tables
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
        "Count Unique": count_unique.__func__,
        "Count Missing": count_missing.__func__,
        "Percentage Missing": percentage_missing.__func__,
        "First Quartile Spread": first_quartile_spread.__func__,
        "Third Quartile Spread": third_quartile_spread.__func__,
        "Median Difference": median_difference.__func__,
        "Midrange": midrange.__func__,
        "Quartile Deviation": quartile_deviation.__func__,
        "Central 50% Range": central_50_range.__func__,
        "Central 80% Range": central_80_range.__func__,
        "Most Frequent Value Count": most_frequent_value_count.__func__,
        "Least Frequent Value": least_frequent_value.__func__,
        "Value Frequency Table": value_frequency_table.__func__,
        "Relative Frequency Table": relative_frequency_table.__func__,
        "Cumulative Count": cumulative_count.__func__,
        "Cumulative Percentage": cumulative_percentage.__func__,
        "Percentile 10": percentile_10.__func__,
        "Percentile 90": percentile_90.__func__,
        "Lower Outlier Boundary": lower_outlier_boundary.__func__,
        "Upper Outlier Boundary": upper_outlier_boundary.__func__,
        "Outlier Values": outlier_values.__func__,
        "Outlier Count": outlier_count.__func__,
        "Coefficient of Variation": coefficient_of_variation.__func__,
        "Mean Absolute Deviation": mean_absolute_deviation.__func__,
        "Trimmed Mean": trimmed_mean.__func__,
        "Spread Score": spread_score.__func__,
        "Range Percentage": range_percentage.__func__,
        "Interval Width": interval_width.__func__,
        "Bin Count": bin_count.__func__,
        "Data Span": data_span.__func__,
        "Duplicate Count": duplicate_count.__func__,
        "Data Density": data_density.__func__,
        "Positive Count": positive_count.__func__,
        "Negative Count": negative_count.__func__,
        "Zero Count": zero_count.__func__,
        "Even Count": even_count.__func__,
        "Odd Count": odd_count.__func__,
        "Above Mean Count": above_mean_count.__func__,
        "Below Mean Count": below_mean_count.__func__,
        "Closest to Mean": closest_to_mean.__func__,
        "Farthest from Mean": farthest_from_mean.__func__,
        "Lower Half Mean": lower_half_mean.__func__,
        "Upper Half Mean": upper_half_mean.__func__,
        "Data Balance": data_balance.__func__,
        "Symmetry Score": symmetry_score.__func__,
        "Normalized Mean": normalized_mean.__func__,
        "Normalized STDV": normalized_stdv.__func__,
        "Peak Density": peak_density.__func__,
        "Data Uniformity": data_uniformity.__func__,
        "Value Concentration": value_concentration.__func__,
    }

    @classmethod
    def get_stat_descriptions(cls) -> dict[str, str]:
        """Return a mapping of stat name → description string.

        Calls each function with an empty list just to harvest the 'desc' field.
        """
        descriptions: dict[str, str] = {}
        for stat_name, func in cls.METRIC_STATS.items():
            try:
                result = func([])
                descriptions[stat_name] = result.get("desc", "")
            except Exception:
                descriptions[stat_name] = ""
        return descriptions

    @classmethod
    def compute_metric_stats(
        cls, values: list[float], selected_stats: list[str]
    ) -> dict[str, Any]:
        results = {}
        for stat in selected_stats:
            func = cls.METRIC_STATS.get(stat)
            if func:
                result = func(values)
                results[stat] = result["return_value"]
        return results

    @classmethod
    def compute_ordinal_stats(
        cls, values: list, selected_stats: list[str]
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
        cls, values: list, selected_stats: list[str]
    ) -> dict[str, Any]:
        results = {}
        nominal_dispatch = {
            "Mode": lambda v: cls.mode(v)["return_value"],
            "n": lambda v: cls.count(v)["return_value"],
            "Count Unique": lambda v: cls.count_unique(v)["return_value"],
            "Count Missing": lambda v: cls.count_missing(v)["return_value"],
            "Percentage Missing": lambda v: cls.percentage_missing(v)["return_value"],
            "Most Frequent Value Count": lambda v: cls.most_frequent_value_count(v)[
                "return_value"
            ],
            "Least Frequent Value": lambda v: cls.least_frequent_value(v)[
                "return_value"
            ],
            "Value Frequency Table": lambda v: cls.value_frequency_table(v)[
                "return_value"
            ],
            "Relative Frequency Table": lambda v: cls.relative_frequency_table(v)[
                "return_value"
            ],
            "Cumulative Count": lambda v: cls.cumulative_count(v)["return_value"],
            "Cumulative Percentage": lambda v: cls.cumulative_percentage(v)[
                "return_value"
            ],
            "Duplicate Count": lambda v: cls.duplicate_count(v)["return_value"],
        }
        for stat in selected_stats:
            handler = nominal_dispatch.get(stat)
            results[stat] = handler(values) if handler else "N/A"
        return results

    @staticmethod
    def frequency_table(values: list) -> dict[str, int]:
        return dict(Counter(values).most_common())
