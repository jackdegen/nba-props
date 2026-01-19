import time
import datetime
import functools
import unidecode
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any, Callable


def _clean_name(name: str) -> str:
    return {
        'Alex Sarr': 'Alexandre Sarr',
        'Carlton Carrington': 'Bub Carrington',
        "Day'ron Sharpe": "Day'Ron Sharpe",
        'Egor Diomin': 'Egor Demin',
        'GG Jackson': 'Gregory Jackson',
        'Kenneth Simpson': 'KJ Simpson',
        "Lu Dort": "Luguentz Dort",
        "Moe Wagner": "Moritz Wagner",
        "Robert Dillingham": "Rob Dillingham",
        'Ron Holland': 'Ronald Holland',
        'Tristan Da Silva': 'Tristan Da Silva',
        'Tristan da Silva': 'Tristan Da Silva',
        # 'Hansen Yang': 'Yang Hansen',
        'Yang Hansen': 'Hansen Yang'
    }.get(
        unidecode.unidecode(name),
        unidecode.unidecode(" ".join(name.split(" ")[:2]).replace(".", ""))
    ).strip()

def _clean_team(team: str) -> str:
    """Clean player name to standard format."""
    return {'GSW': 'GS', 'SAS': 'SA', 'NOP': 'NO', 'PHX': 'PHO', 'NYK': 'NY'}.get(team, team).strip()

def _load_injuries(
    fanduel_contest_data_path: str = f'/home/deegs/devel/repos/nba-boxscores-git/nba-boxscores/data/2025-2026/contest-files/fanduel/main-slate/{datetime.date.today().isoformat()}.csv',
    report: bool = False # Verbose flag
) -> list[str,...]:
    """
    Load injured players from FanDuel contest file
    Returns both Out players and Doubtful players
    """
    abbreviations = {'GTD': 'Game-time Decision', 'P': 'Probable', 'Q': 'Questionable', 'D': 'Doubtful', 'O': 'Out'}
    
    df = (pd
          .read_csv(fanduel_contest_data_path)
          [['Nickname', 'Played', 'Salary', 'Team', 'FPPG', 'Injury Indicator']]
          .set_axis(['name', 'n_games', 'salary', 'team', 'fpts', 'status'], axis=1)
          .assign(
              name=lambda df_: df_.name.map(_clean_name),
              fpts_1k=lambda df_: 1_000 * (df_.fpts / df_.salary),
              status=lambda df_: df_.status.map(lambda status_: status_.strip() if isinstance(status_, str) else status_)
          )
          # .pipe(lambda df_: df_.loc[(df_.salary > 3_500)])
          .pipe(lambda df_: df_.loc[((df_.salary > 4_000) | (df_.fpts >= 20.0)) & ((df_.n_games >= 10) & (df_.fpts_1k <= 6.0))])
          .set_index('name')
         )
    
    injuries = {status: sorted(df.loc[df.status == status].index, key=lambda name_: df.loc[name_, 'salary'], reverse=True) for status in abbreviations}

    if report:
        report_msgs = []
        report_players = {status: {team: sorted(df.loc[(df.status == status) & (df.team == team)].index, key=lambda name_: df.loc[name_, 'salary'], reverse=True) for team in df.team.drop_duplicates()} for status in abbreviations}
        for status, team_players in report_players.items():
            if any(team_players.values()):
                report_msgs.append(f'{abbreviations[status]}:')
                for team, players in team_players.items():
                    if players:
                        report_msgs.extend(sum([
                            [f' * {team}:'],
                            [f'    - {_clean_name(p)}' for p in players]
                        ], []))

        _output_msgs(report_msgs, char='*')
    
    return sorted(injuries['O'] + injuries['D'])

def _output_msgs(msgs: str|list[str,...], char=None, warning=False) -> None:
    """
    Prettier output
    """
    if isinstance(msgs, str):
        msgs = [msgs]

    if not char:
        char = '-'

    if warning:
        msgs = [f'\n\nWARNING: {msg_}\n\n' for msg_ in msgs]

    padding = char*min(150, max([len(msg_) for msg_ in msgs]))
    output = [padding] + msgs + [padding]

    print(*output, sep='\n')
    
    return

def _timeit(func: Callable[[Any], Any], *args, **kwargs) -> Callable[[Any], Any]:
    """
    Will be used as decorator to output time it taks for func to complete.
    Input: func -> Function want to wrap timer info about.
    Output: Timing information about duration it took func, also returning func
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _output_msgs(f'{func.__qualname__} started at: {datetime.datetime.strftime(datetime.datetime.now(), '%I:%M:%S')}')
        start = time.perf_counter()

        res = func(*args, **kwargs)
        stop = time.perf_counter()
        
        elapsed = (stop - start)/60.0
        elapsed_str = str(elapsed)
        minutes = int( elapsed_str.split('.')[0] )
        decimals = float( f'0.{elapsed_str.split(".")[1]}' )
        seconds = int(decimals * 60.0)
        
        _output_msgs(f'Performance time for {func.__qualname__}: {minutes}m {seconds}s')

        return res
    
    return wrapper