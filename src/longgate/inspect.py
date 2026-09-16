from __future__ import annotations

import re
import pandas as pd
from .types import ColumnProfile, DataClass

IDENTIFIER_PATTERNS = [
    r"(^|_)(name|full_name|first_name|last_name)(_|$)",
    r"phone|mobile|telephone|tel",
    r"email|e_mail",
    r"(^|_)(id|subject_id|participant_id|patient_id|student_id|employee_id|record_id)(_|$)|passport|nhs|ssn|national_id|identity|id_card|身份证|手机号|电话|邮箱|姓名|护照|学号|工号|病历号",
    r"address|postcode|postal|zip|住址|地址|邮编",
]

QUASI_PATTERNS = [
    r"(^|_)(age|dob|birth|birthday|sex|gender|ethnicity|nationality|occupation|job|school|university|city|region|country)(_|$)",
    r"年龄|生日|出生|性别|民族|国籍|职业|学校|大学|城市|地区|国家",
]

SENSITIVE_PATTERNS = [
    r"diagnos|disease|symptom|medicat|health|clinical|hospital|condition|therapy|trauma|psychi|mental",
    r"phq|gad|cape|pcl|score|scale|questionnaire|rt|reaction_time",
    r"诊断|疾病|症状|药物|健康|临床|医院|治疗|创伤|心理|精神|量表|评分|反应时",
]


def _matches(name: str, patterns: list[str]) -> bool:
    n = name.lower().strip()
    return any(re.search(p, n, re.IGNORECASE) for p in patterns)


def _looks_like_free_text(series: pd.Series) -> bool:
    if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
        return False
    s = series.dropna().astype(str)
    if s.empty:
        return False
    avg_len = float(s.str.len().mean())
    p90_len = float(s.str.len().quantile(0.9))
    return avg_len > 60 or p90_len > 160


def profile_dataframe(df: pd.DataFrame) -> list[ColumnProfile]:
    profiles: list[ColumnProfile] = []
    for col in df.columns:
        s = df[col]
        unique = int(s.nunique(dropna=True))
        ratio = unique / max(int(s.notna().sum()), 1)
        if _matches(str(col), IDENTIFIER_PATTERNS):
            cls = DataClass.IDENTIFIER
            strategy = "regenerate"
            notes = "Direct identifier; never released as source value."
        elif _looks_like_free_text(s):
            cls = DataClass.FREE_TEXT
            strategy = "block_v0_1"
            notes = "Free text requires a dedicated local semantic synthesis path; blocked in v0.1."
        elif _matches(str(col), QUASI_PATTERNS):
            cls = DataClass.QUASI_IDENTIFIER
            strategy = "joint_synthesis"
            notes = "Potential linkage field; synthesize jointly rather than map deterministically."
        elif _matches(str(col), SENSITIVE_PATTERNS):
            cls = DataClass.SENSITIVE
            strategy = "joint_synthesis"
            notes = "Sensitive attribute; source values remain local."
        else:
            cls = DataClass.GENERAL
            strategy = "joint_synthesis"
            notes = "General field; source values still remain local under Long Gate's strict mode."
        profiles.append(ColumnProfile(name=str(col), dtype=str(s.dtype), data_class=cls, strategy=strategy, non_null=int(s.notna().sum()), unique=unique, unique_ratio=round(ratio, 6), notes=notes))
    return profiles
