import os
import glob
import json

import pandas as pd

def read_json_file(file: str) -> dict[str,float]:
    proj = dict()
    with open(file, 'r') as f:
        proj = json.load(f)

    if not proj:
        raise ValueError('No backup projections, issue with site.')

    return proj

def load_json_projections(files: list[str,...]) -> dict[str,float]:

    proj = read_json_file(files[0])

    for f in files[1:]:
        proj = {
            **proj,
            **read_json_file(f)
        }

    return proj

def load_csv_projections(files: list[str,...]) -> dict[str,float]:
    
    return {
        name: fpts
        for name, fpts in (pd
                           .concat([pd.read_csv(file) for file in files])
                           [['name', 'fpts']]
                           .drop_duplicates('name')
                           .set_index('name')
                           ['fpts']
                           .items()
                          )
    }
    

def load_backup_projections(**kwargs) -> dict[str,float]:

    files = kwargs.get('file', kwargs.get('files', '/home/deegs/devel/repos/nba-props-git/nba-props/data/backup_projections.json'))

    if isinstance(files, str):
        files = files.split(',')

    return {
        'json': load_json_projections,
        'csv': load_csv_projections,
    }[files[0].split('.')[-1]](files)

def create_historical_props():
    return (pd
            .concat([pd.read_csv(f) for f in glob.glob('/home/deegs/devel/repos/nba-props-git/nba-props/data/historical/*.csv')])
            .groupby('name')
            ['fpts']
            .agg('mean')
            .to_dict()
           )