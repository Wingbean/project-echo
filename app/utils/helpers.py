# app/utils/helpers.py - General Helper Functions


def _json_safe(val):
    """Convert a single pandas/py value to a JSON-safe scalar.

    Mirrors the per-cell conversion the per-HN endpoints used to inline:
    Timedelta -> "HH:MM:SS", datetime/Timestamp -> isoformat, NaT/None -> "".
    """
    if hasattr(val, "components"):  # pandas Timedelta -> "0 days 22:00:10.x"
        ts = str(val).split()[-1]
        return ts.split(".")[0]
    if hasattr(val, "isoformat"):  # datetime / Timestamp / date
        dt_str = val.isoformat()
        return "" if dt_str == "NaT" else dt_str
    if val is None:
        return ""
    return val if isinstance(val, (int, float, str, bool)) else str(val)


def records_from_df(df):
    """Turn a DataFrame into (columns, JSON-safe records).

    Single source of truth for the per-HN endpoints so the serialization
    logic lives in one place. Fills NaN/NaT with "" then normalises every
    cell via `_json_safe`.

    Args:
        df: pandas DataFrame.

    Returns:
        (columns: list[str], records: list[dict]) ready for jsonify.
    """
    df = df.fillna("")
    columns = df.columns.tolist()
    records = df.to_dict(orient="records")
    for record in records:
        for key, val in record.items():
            record[key] = _json_safe(val)
    return columns, records
