from pathlib import Path
import csv
import json

class FileLoader:
    """Loads and parses .json and .csv files into a list of dictionaries."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: list[dict[str, Any]] = []
        self.keys: list[str] = []
        self._load()

    def _load(self) -> None:
        ext = Path(self.filepath).suffix.lower()
        if ext == ".json":
            self._load_json()
        elif ext == ".csv":
            self._load_csv()
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _load_json(self) -> None:
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            self.data = [row for row in raw if isinstance(row, dict)]
        elif isinstance(raw, dict):
            if all(isinstance(v, list) for v in raw.values()):
                length = max(len(v) for v in raw.values()) if raw else 0
                self.data = []
                for i in range(length):
                    row = {}
                    for k, v in raw.items():
                        row[k] = v[i] if i < len(v) else None
                    self.data.append(row)
            else:
                self.data = [raw]
        if self.data:
            all_keys, seen = [], set()
            for row in self.data:
                for k in row.keys():
                    if k not in seen:
                        all_keys.append(k)
                        seen.add(k)
            self.keys = all_keys

    def _load_csv(self) -> None:
        with open(self.filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.data = list(reader)
        if self.data:
            self.keys = list(self.data[0].keys())

    def get_column(self, key: str) -> list[Any]:
        return [row.get(key) for row in self.data if row.get(key) is not None]

    def get_numeric_column(self, key: str) -> list[float]:
        values = []
        for row in self.data:
            val = row.get(key)
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        return values

    def row_count(self) -> int:
        return len(self.data)
