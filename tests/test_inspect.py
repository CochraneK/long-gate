import pandas as pd

from longgate.inspect import profile_dataframe
from longgate.types import DataClass


def test_common_subject_id_is_identifier():
    df = pd.DataFrame({"participant_id": [101, 102], "score": [3, 4]})
    profiles = {p.name: p for p in profile_dataframe(df)}
    assert profiles["participant_id"].data_class == DataClass.IDENTIFIER


def test_common_record_number_names_are_identifiers():
    df = pd.DataFrame(
        {
            "mrn": [900001, 900002],
            "account_number": [700001, 700002],
            "uuid": [111111, 222222],
            "measurement": [1.25, 2.75],
        }
    )
    profiles = {p.name: p for p in profile_dataframe(df)}
    assert profiles["mrn"].data_class == DataClass.IDENTIFIER
    assert profiles["account_number"].data_class == DataClass.IDENTIFIER
    assert profiles["uuid"].data_class == DataClass.IDENTIFIER
    assert profiles["measurement"].data_class == DataClass.GENERAL
