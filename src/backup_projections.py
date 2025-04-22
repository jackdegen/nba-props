import json


def load_backup_projections() -> dict[str,float]:

    source = '/home/deegs/devel/repos/nba-props-git/nba-props/src/backup_projections.json'

    proj = dict() # Can't shake my C++ training about SCOPE!!!
    with open(source, 'r') as f:
        proj = json.load(f)

    if not proj:
        raise ValueError('No backup projections, issue with site.')
    
    return proj


EDITS = load_backup_projections()