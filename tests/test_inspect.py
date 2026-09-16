import pandas as pd

from longgate.inspect import profile_dataframe
from longgate.types import DataClass


def test_common_subject_id_is_identifier():
    df = pd.DataFrame({"participant_id": [101, 102], "score": [3, 4]})
    profiles = {p.name: p for p in profile_dataframe(df)}
    assert profiles["participant_id"].data_class == DataClass.IDENTIFIER
