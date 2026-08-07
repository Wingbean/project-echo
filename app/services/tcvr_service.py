# app/services/tcvr_service.py - Thai CVD Risk calculator (ported from labncd)
import numpy as np
import pandas as pd

from app.services.hosxp_service import execute_sql_on_hosxp

# Ported verbatim from labncd services/data_service.py::fetch_tcvr_df — do not
# tweak constants/formula without clinical sign-off (RAMA Thai CVD Risk score).
KEEP_COLUMNS = [
    "HN", "Name", "Sex", "Age", "DM", "HT", "Smoke",
    "bps_ops", "TC_ops", "waist_ops", "height_ops",
    "lastDate", "RegDate", "ThaiCVD_Risk_pct", "RiskCat",
]


def fetch_tcvr_df(startdate: str) -> pd.DataFrame:
    """Run sql/tcvr.sql for one screening day and compute Thai CVD Risk %.

    - Has TC (cholesterol) -> blood formula.
    - No TC -> waist/height ratio formula.
    """
    df = execute_sql_on_hosxp("tcvr.sql", params={"startdate": startdate})
    if df is None or df.empty:
        return pd.DataFrame()

    for col in ["Age", "bps_ops", "TC_ops", "waist_ops", "height_ops", "Sex"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["SEX01"] = np.where(df.get("Sex", 0) == 1, 1, 0)
    df["DM01"] = np.where(df.get("DM", "N") == "Y", 1, 0)
    df["SMK01"] = np.where(df.get("Smoke", 0) == 2, 1, 0)

    AGE = df["Age"].fillna(0)
    SBP = df["bps_ops"].fillna(0)
    CHOL = df["TC_ops"].where(pd.to_numeric(df["TC_ops"], errors="coerce") > 0)
    W = df["waist_ops"].fillna(0)
    H = df["height_ops"].replace(0, np.nan).fillna(np.nan)
    SX = df["SEX01"]
    DM01 = df["DM01"]
    SMK = df["SMK01"]

    has_tc = CHOL.notna()
    sur_root = 0.964588

    full_blood = (0.08183 * AGE) + (0.39499 * SX) + (0.02084 * SBP) + (0.69974 * DM01) + (0.00212 * CHOL.fillna(0)) + (0.41916 * SMK)
    p_blood = (1 - (sur_root ** (np.exp(full_blood - 7.04423)))) * 100.0

    ratio = (W / H)
    ratio = ratio.fillna(0)
    full_anth = (0.079 * AGE) + (0.128 * SX) + (0.019350987 * SBP) + (0.58454 * DM01) + (3.512566 * ratio) + (0.459 * SMK)
    p_anth = (1 - (sur_root ** (np.exp(full_anth - 7.712325)))) * 100.0

    df["ThaiCVD_Risk_pct"] = np.where(has_tc, p_blood, p_anth)
    df["ThaiCVD_Risk_pct"] = df["ThaiCVD_Risk_pct"].clip(lower=0, upper=100).round(1)

    bins = [-float("inf"), 10, 20, 30, 40, float("inf")]
    labels = ["Low", "Medium", "High", "VeryHigh", "Extreme"]
    df["RiskCat"] = pd.cut(df["ThaiCVD_Risk_pct"], bins=bins, labels=labels, right=False)

    existing = [c for c in KEEP_COLUMNS if c in df.columns]
    return df[existing].copy()
