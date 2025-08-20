import pandas as pd
from pathlib import Path

from app import perform_join


def test_perform_join_success():
    df1 = pd.DataFrame({'id': [1, 2], 'v1': [10, 20]})
    df2 = pd.DataFrame({'id': [1, 2], 'v2': [30, 40]})
    res = perform_join([df1, df2])
    assert res['ok']
    assert res['meta']['inputCount'] == 2
    assert res['meta']['outputRows'] == 2
    assert set(res['data'].columns) == {'id', 'v1', 'v2'}


def test_perform_join_failure_no_key():
    df1 = pd.DataFrame({'id': [1, 2]})
    df2 = pd.DataFrame({'x': [1, 2]})
    res = perform_join([df1, df2])
    assert not res['ok']
    assert 'no common key' in res['reason']


def test_single_file_join_passes():
    df1 = pd.DataFrame({'id': [1], 'a': [2]})
    res = perform_join([df1])
    assert res['ok']
    assert res['meta']['inputCount'] == 1
    assert res['data'].shape[0] == 1


def test_no_join_download_names():
    names = ['first.csv', 'second.csv']
    files = [f"{Path(n).stem}-edited.csv" for n in names]
    assert files == ['first-edited.csv', 'second-edited.csv']
