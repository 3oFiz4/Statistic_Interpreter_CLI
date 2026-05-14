

# Statistic_Interpreter_CLI

<img width="962" height="1080" alt="image" src="https://github.com/user-attachments/assets/6ca9b075-477d-48af-9ff5-487f546b67dc" />

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/619c77f3-abcf-4a39-bc8b-780eff234ae9" />


**(on going) A DataViewer and Also statistic interpreter within a terminal, support a lot of statistical metrics (e.g., mean, stdv, mad, max, min, iqr, and a lot more, there's 60+)! Configurable Level of Measurement. And also a graph viewer.**

## How To Use
This program has two files (for now, in the future there might be more):
- `json_to_excel_view.py` (view a .csv or .json file in excel-like manner)
- `stat_interpret.py`  (interpret a .csv or .json file from statistical metric)

To use simply run this:
`python <json_to_excel_view.py | stat_interpret.py> <.csv | .json>`

For example:
`python stat_interpret.py market.json` will run a statistical interpretation of the market.json

### `stat_interpret.py`
<img width="955" height="531" alt="image" src="https://github.com/user-attachments/assets/3c7cb0f1-5d72-4d84-aed6-46127364c681" />

**This will be your first scene of the UI.. It has some features**

Features:
- Configurable Level of Measurement: Metric, Ordinal, Nominal
- <details>
  <summary>Statistical Metric (there's a lot of 'em...) :</summary>
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
</details>
- Graph viewer (on development)
- <details>
  <summary>Custom Theme and Theme Change:</summary>
  <img width="957" height="553" alt="image" src="https://github.com/user-attachments/assets/a6f0a9be-be20-4e35-847e-35e717773e7e" />
</details>
- Reactive against file changes (very useful when used in double pane with  `json_to_excel_view.py`!

### `json_to_excel_view.py` (we might change the name soon)
<img width="956" height="524" alt="image" src="https://github.com/user-attachments/assets/a4009199-0f1c-43b3-a70e-29a260056785" />

Features:
- Cell Editing, different than Excel, since this one requires Confirmation in case for accidentaly edit
- Row Deletion
- Row Appending
- File Save
- Reactive against file changes

## Requirement:
- Textual
- chafa (optional)
- Basic knowledge of statistics

## Instalation
1. `git clone https://github.com/3oFiz4/Statistic_Interpreter_CLI`
2. `pip install textual textual-image pillow numpy scipy textual-plot`
3. Enjoy

## Incoming Feature
more to come soon... please give some star, it will motivate me more to do it! <:3 

> Cool Bloomberg Terminal set-up. Is this for Finance? - @some_guy_while_i_was_developing_this 💀
