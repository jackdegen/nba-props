import time
import datetime
import functools
import unidecode

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from typing import Any, Callable

def timeit(func: Callable[[Any], Any], *args, **kwargs) -> Callable[[Any], Any]:
    """
    Will be used as decorator to output time it taks for func to complete.
    Input: func -> Function want to wrap timer info about.
    Output: Timing information about duration it took func, also returning func
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'{func.__qualname__} started at: {datetime.datetime.strftime(datetime.datetime.now(), '%I:%M:%S')}')
        start = time.perf_counter()

        # Call func and set to variable
        res = func(*args, **kwargs)
        
        stop = time.perf_counter()
        
        elapsed: float = (stop - start)/60.0
        
        elapsed_str: str = str(elapsed)
        minutes: int = int( elapsed_str.split('.')[0] )
        
        decimals: float = float( f'0.{elapsed_str.split(".")[1]}' )
        seconds: int = int(decimals * 60.0)
        
        performance_time: str = f'{minutes}m {seconds}s.'
        
        print(f'Performance time for {func.__qualname__}: {performance_time}\n')

        return res
    
    return wrapper

def output_msgs(msgs: str|list[str,...], char=None, warning=False) -> None:
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


def load_injuries() -> list[str,...]:
    fanduel_file = f'/home/deegs/devel/repos/nba-boxscores-git/nba-boxscores/data/2025-2026/contest-files/fanduel/main-slate/{datetime.date.today().isoformat()}.csv'
    # fanduel_file = f'/home/deegs/devel/repos/nba-boxscores-git/nba-boxscores/data/2025-2026/contest-files/fanduel/main-slate/{(datetime.date.today()+datetime.timedelta(days=1)).isoformat()}.csv'

    df = (pd
          .read_csv(fanduel_file)
          [['Nickname', 'Salary', 'FPPG', 'Injury Indicator']]
          .set_axis(['name', 'salary', 'fpts', 'status'], axis=1)
          .assign(name=lambda df_: df_.name.map(_clean_name))
          # .pipe(lambda df_: df_.loc[(df_.salary > 3_500)])
          .pipe(lambda df_: df_.loc[(df_.salary > 4_000) | (df_.fpts > 15.0)])
          .set_index('name')
         )
    
    injuries = {status: sorted(df.loc[df.status == status].index, key=lambda name_: df.loc[name_, 'salary'], reverse=True) for status in {'GTD', 'D', 'O'}}

    # inj_report_players = await example_todays_games_only_out()
    
    # inj['O'].append(inj_report_players)

    return sorted(injuries['O'] + injuries['D'])

# ######################################################################################################################################################

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
    }.get(name, unidecode.unidecode(" ".join(name.split(" ")[:2]).replace(".", "")))


def _load_injuries() -> list[str,...]:
    fanduel_file = f'/home/deegs/devel/repos/nba-boxscores-git/nba-boxscores/data/2025-2026/contest-files/fanduel/main-slate/{datetime.date.today().isoformat()}.csv'
    # fanduel_file = f'/home/deegs/devel/repos/nba-boxscores-git/nba-boxscores/data/2025-2026/contest-files/fanduel/main-slate/{(datetime.date.today()+datetime.timedelta(days=1)).isoformat()}.csv'

    df = (pd
          .read_csv(fanduel_file)
          [['Nickname', 'Salary', 'FPPG', 'Injury Indicator']]
          .set_axis(['name', 'salary', 'fpts', 'status'], axis=1)
          .assign(name=lambda df_: df_.name.map(_clean_name))
          # .pipe(lambda df_: df_.loc[(df_.salary > 3_500)])
          .pipe(lambda df_: df_.loc[(df_.salary > 4_000) | (df_.fpts > 15.0)])
          .set_index('name')
         )
    
    injuries = {status: sorted(df.loc[df.status == status].index, key=lambda name_: df.loc[name_, 'salary'], reverse=True) for status in {'GTD', 'D', 'O'}}

    # inj_report_players = await example_todays_games_only_out()
    
    # inj['O'].append(inj_report_players)

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

        # Call func and set to variable
        res = func(*args, **kwargs)
        
        stop = time.perf_counter()
        
        elapsed = (stop - start)/60.0
        
        elapsed_str = str(elapsed)
        minutes = int( elapsed_str.split('.')[0] )
        
        decimals = float( f'0.{elapsed_str.split(".")[1]}' )
        seconds = int(decimals * 60.0)
        
        performance_time = f'{minutes}m {seconds}s.'
        
        _output_msgs(f'Performance time for {func.__qualname__}: {performance_time}')

        return res
    
    return wrapper