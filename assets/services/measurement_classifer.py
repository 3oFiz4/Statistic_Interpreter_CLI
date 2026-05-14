class MeasurementClassifier:
    """Classifies columns into Metric, Ordinal, or Nominal."""

    ORDINAL_INDICATORS = [
        "rank", "rating", "grade", "level", "priority", "order",
        "stage", "tier", "class", "score", "scale", "degree",
        "satisfaction", "quality", "education", "income_level",
    ]

    ORDINAL_VALUE_PATTERNS = [
        ["low", "medium", "high"],
        ["small", "medium", "large"],
        ["poor", "fair", "good", "excellent"],
        ["never", "rarely", "sometimes", "often", "always"],
        ["strongly disagree", "disagree", "neutral", "agree", "strongly agree"],
        ["beginner", "intermediate", "advanced", "expert"],
    ]

    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self.classifications: dict[str, str] = {}
        self._classify_all()

    def _classify_all(self) -> None:
        for key in self.loader.keys:
            self.classifications[key] = self._classify_key(key)

    def _classify_key(self, key: str) -> str:
        values = self.loader.get_column(key)
        if not values:
            return "nominal"

        numeric_count = 0
        for v in values:
            try:
                float(v)
                numeric_count += 1
            except (ValueError, TypeError):
                pass

        numeric_ratio = numeric_count / len(values) if values else 0

        if numeric_ratio > 0.8:
            numeric_values = self.loader.get_numeric_column(key)
            unique_values = set(numeric_values)
            all_integers = all(v == int(v) for v in numeric_values)

            if all_integers and len(unique_values) <= 10 and len(unique_values) < len(values) * 0.3:
                key_lower = key.lower().replace("_", " ").replace("-", " ")
                for indicator in self.ORDINAL_INDICATORS:
                    if indicator in key_lower:
                        return "ordinal"
                if len(unique_values) <= 5:
                    return "ordinal"
            return "metric"

        string_values = [str(v).lower().strip() for v in values]
        unique_strings = set(string_values)

        key_lower = key.lower().replace("_", " ").replace("-", " ")
        for indicator in self.ORDINAL_INDICATORS:
            if indicator in key_lower:
                return "ordinal"

        for pattern in self.ORDINAL_VALUE_PATTERNS:
            pattern_set = set(pattern)
            if unique_strings.issubset(pattern_set) or len(unique_strings & pattern_set) >= 2:
                return "ordinal"

        return "nominal"

    def get_metric_keys(self) -> list[str]:
        return [k for k, v in self.classifications.items() if v == "metric"]

    def get_ordinal_keys(self) -> list[str]:
        return [k for k, v in self.classifications.items() if v == "ordinal"]

    def get_nominal_keys(self) -> list[str]:
        return [k for k, v in self.classifications.items() if v == "nominal"]

    def reclassify(self, key: str, new_classification: str) -> None:
        if new_classification in ("metric", "ordinal", "nominal"):
            self.classifications[key] = new_classification
