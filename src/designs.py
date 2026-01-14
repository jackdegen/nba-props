import os
import random
import time
import datetime

import pandas as pd

from dataclasses import dataclass, field

import settings.custom

SCORING = {
    "points": 1.0,
    "rebounds": 1.25,
    "assists": 1.5,
    "3 pointers": 0.5,
    "blocks": 2.0,
    "steals": 2.0,
    "turnovers": -0.5,
}

SHORTHAND_ORDER = list(SCORING.keys())

NAME_ISSUES = {
    'Alex Sarr': 'Alexandre Sarr',
    'Ron Holland': 'Ronald Holland',
    'David Jones-Garcia': 'David Jones',
    "Moe Wagner": "Moritz Wagner",
    'Kenneth Simpson': 'KJ Simpson',
    'Herb Jones': 'Herbert Jones',
}

PROPS_CURRENT_DATE_STR = datetime.datetime.now().strftime("%m/%d")
# PROPS_CURRENT_DATE_STR = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d")

@dataclass(frozen=True)
class MoneyLine:
    moneyline_str: str|None = None
    moneyline: int = 100
    implied_probability: float = 0.5

    def __post_init__(self): 
        if self.moneyline_str:
            object.__setattr__(self, 'moneyline', self._parse_moneyline_str(str(self.moneyline_str)))
            object.__setattr__(self, 'implied_probability', self._calculate_implied_probability())

    def _parse_moneyline_str(self, moneyline_str: str|None = None) -> int:
        """Converts string into integer using first character to determine sign"""
        return {True: 1, False: -1}[moneyline_str[0] == '+'] * int(moneyline_str[1:])

    def _calculate_implied_probability(self) -> float:
        """Returns implied probability of a moneyline using standard American odds formulas"""
        return {
            True: self._negative_moneyline_probability,
            False: self._positive_moneyline_probability
        }[self.moneyline < 0]()

    def _negative_moneyline_probability(self) -> float:
        """Implied Probability for a negative money line (always > 0.5)"""
        return (-1*self.moneyline) / (-1*self.moneyline + 100)

    def _positive_moneyline_probability(self) -> float:
        """Implied Probability for a negative money line (always <= 0.5)"""
        return 100 / (self.moneyline+100)


@dataclass(slots=True, frozen=True)
class Prop:
    name: str
    date_str: str
    stat: str
    value: float
    implied_odds_over: float
    implied_odds_under: float
    vig: float = 0.0
    true_odds_over: float = 0.0
    true_odds_under: float = 0.0
    fpts: float = 0.0
    e_fpts: float = 0.0
    shorthand: str = ''
    past: bool = False

    @staticmethod
    def _calculate_vig(implied_odds_over: float, implied_odds_under: float) -> float:
        return sum([implied_odds_over, implied_odds_under]) - 1.0 
        
    def __post_init__(self):
        
        object.__setattr__(self, 'name', NAME_ISSUES.get(self.name, self.name))
        object.__setattr__(self, 'fpts', SCORING[self.stat.lower()]*self.value)

        object.__setattr__(self, 'vig', sum([self.implied_odds_over, self.implied_odds_under]) - 1.0)

        total_implied_probability = sum([self.implied_odds_over, self.implied_odds_under])
        object.__setattr__(self, 'true_odds_over', self.implied_odds_over / total_implied_probability)
        object.__setattr__(self, 'true_odds_under', self.implied_odds_under / total_implied_probability)
        
        # object.__setattr__(self, 'e_fpts', self.implied_odds_over*self.fpts)
        # object.__setattr__(self, 'e_fpts', (1.0 - self.implied_odds_under)*self.fpts)
        object.__setattr__(self, 'e_fpts', self.true_odds_over*self.fpts)
        
        object.__setattr__(self, 'shorthand', self.stat[0].upper())
        object.__setattr__(self, 'past', self.date_str != PROPS_CURRENT_DATE_STR)

    
    def to_dict(self):
        return {
            'name': self.name,
            'date': self.date_str,
            'stat': self.stat,
            'value': self.value,
            'odds_over': self.implied_odds_over,
            'odds_under': self.implied_odds_under,
            'fpts': self.fpts,
            'e_fpts': self.e_fpts
        }



IMPUTE_PROPS = {
    'steals': 0.5, # S/B props vary, but most starters will have offered
    'blocks': 0.5, # Want to include for all since valuable FPTS but dont want to overshoot, hence 0.5
    # '3 pointers': 0.5, # Most shooters will have props offered
    'turnovers': 1.5, # NBA average
}


# PLAYER_PROP_TRACKER = PlayerPropTracker()

@dataclass(slots=True, frozen=True)
class Player:
    name: str
    props: list[Prop,...]|None = None
    fpts: float = 0.0
    e_fpts: float = 0.0
    props_log: list[str,...]|None = None
    shorthand: str = ''

    @staticmethod
    def _impute_missing_props(props_log: list[str,...]) -> tuple[float,float,str]:

        fpts, e_fpts = 0.0, 0.0
        shorthand = ''
        
        if props_log:
            
            shorthand_vals = []
            missing_props = set(IMPUTE_PROPS.keys()).intersection(set(SCORING.keys()).difference(set(props_log)))
    
            for missing in missing_props:
                shorthand_vals.append(missing[0].upper())
                fpts += SCORING[missing]*IMPUTE_PROPS[missing]
                e_fpts += 0.5*SCORING[missing]*IMPUTE_PROPS[missing]

            shorthand = f'({"".join(sorted(shorthand_vals, key=lambda sh: 'PRASB3T'.index(sh)))})' if missing_props else ''
            
        return fpts, e_fpts, shorthand
            
    def __post_init__(self):
        
        if not self.props:
            object.__setattr__(self, 'props_log', [])
            object.__setattr__(self, 'fpts', 0.0)
            object.__setattr__(self, 'e_fpts', 0.0)
            object.__setattr__(self, 'shorthand', '---')
            
        else:

            # PLAYER_PROP_TRACKER.update(*[prop.to_dict() for prop in self.props])
            object.__setattr__(self, 'props_log', sorted([prop.stat for prop in self.props], key=lambda stat_: SHORTHAND_ORDER.index(stat_)))

            imputed_fpts, imputed_efpts, imputed_shorthand = self._impute_missing_props(self.props_log)
            past_props_marker = '*' if self.props[0].past else ''
            object.__setattr__(self, 'fpts', sum(prop.fpts for prop in self.props) + imputed_fpts)
            object.__setattr__(self, 'e_fpts', sum(prop.e_fpts for prop in self.props) + imputed_efpts)
            object.__setattr__(self, 'shorthand', ''.join(sorted([prop.shorthand for prop in self.props], key=lambda sh: 'PRASB3T'.index(sh))) + imputed_shorthand + past_props_marker)





# import pandas as pd

# # from dataclasses import dataclass

# # from designs import NAME_ISSUES
from propscraper import PropScraper
from prophandler.proptracker import PropTracker

from __utils import (
    _clean_name,
    _load_injuries,
    _output_msgs,
    _timeit,
)

# DATA_DIR = os.getcwd().replace('src', 'data')

# @dataclass
# class _PropHandler_:
#     site: str = 'draftkings'
#     mode: str = 'classic'
#     input_file: str|None = None
#     output_file: str|None = None
#     constant: bool = False
#     verbose: bool = False
#     drop: list[str,...] = field(default_factory=list)
#     edits: dict[str,float] = field(default_factory=dict)
#     override_edits: dict[str,float] = field(default_factory=dict)
#     ownership: dict[str,float] = field(default_factory=dict)
#     scraper: PropScraper|None = None
#     scraper_kwargs: dict[str,bool]|None = None
#     tracker: PropTracker|None = None

#     def __post_init__(self):

#         if not self.input_file:
#             self.input_file = os.path.join(
#                 DATA_DIR,
#                 f'current-{self.site}{"-sg" if self.mode == "showdown" else ""}.csv'
#             )

#         if len(pd.read_csv(self.input_file).TeamAbbrev.drop_duplicates()) == 2:
#             self.mode = 'showdown'
        
#         if not self.output_file:
#             self.output_file = os.path.join(
#                 DATA_DIR,
#                 f'{self.site}-props{"-sg" if self.mode == "showdown" else ""}.csv'
#             )

            
#         self.drop += _load_injuries()

#         # if not self.edits:
#         #     self.edits = {}
#         # if not self.override_edits:
#         #     self.override_edits = {}
#         # if not self.ownership:
#         #     self.ownership = {}
            
#         if not self.scraper:
#             if not self.scraper_kwargs:
#                 self.scraper_kwargs = {}
#             self.scraper = PropScraper(**self.scraper_kwargs)

#         self.directory = self.scraper.create_webpage_directory()
        
#         if not self.tracker:
#             self.tracker = PropTracker()

#     @staticmethod
#     def _parse_gametime_str(gametime_str: str) -> str:
#         return tuple(
#             int(part)
#             for part in gametime_str.replace(' ET', '').replace('AM', '').replace('PM', '').split(' ')[-1].split(':')
#         )

#     def _run_prop_scrape(self, name: str, team: str) -> tuple[float,float,str]:
#         try:
#             return self.scraper.scrape_player_props(
#                 name,
#                 self.directory[team][name],
#                 self.site,
#                 team,
#             )

#         except KeyError:
#             return (0.0, 0.0, '---')

#     def _clean_and_scrape_data(self):

#         columns: dict[str, str] = {
#             "Name": "name",
#             "Roster Position": "pos",
#             "TeamAbbrev": "team",
#             "Salary": "salary",
#             'Game Info': 'game',
#         }

#         inits_issues = {
#             "SAS": "SA",
#             "PHX": "PHO",
#             "GSW": "GS",
#             "NOP": "NO",
#             "NYK": "NY",
#             'CHO': 'CHA',
#             'BRK': 'BKN'
#         }

        

#         df = (pd
#             .read_csv(self.input_file, usecols=columns)
#             .rename(columns, axis=1)
#             .assign(
#                 name=lambda df_: df_.name.apply(_clean_name),
#                 team=lambda df_: df_.team.map(lambda team_: inits_issues.get(team_, team_)),
#                 pos=lambda df_: df_.pos.str.replace("/[GF]/UTIL", "", regex=True).str.replace("C/UTIL", "C", regex=False).str.replace("/[GF]", "", regex=True),
#                 opp=lambda df_: df_[['game', 'team']].apply(lambda row: [inits_issues.get(team_, team_) for team_ in row.game.split(' ')[0].split('@') if team_ != row.team].pop(), axis=1),
#                 gametime=lambda df_: df_.game.apply(self._parse_gametime_str)
#             )
#             .pipe(lambda df_: df_.loc[(df_.pos != "CPT") & (df_.name.isin(self.drop) == False), ['name', 'pos', 'salary', 'team', 'opp', 'gametime']])
#              )


#         df['input'] = tuple(zip(df.name, df.team))
#         df["output"] = df.input.apply(lambda x: self._run_prop_scrape(*x))

#         df["fpts"] = df.output.map(lambda x: x[0])
#         df["e_fpts"] = df.output.map(lambda x: x[1])
#         df["props"] = df.output.map(lambda x: x[2])

#         df = (df
#               .drop(["input", "output"], axis=1)
#               .set_index("name")
#               .round(2)
#         )

#         if self.mode == 'showdown':
#             df = (
#                 df.assign(
#                     cpt_pts=lambda df_: df_.fpts*1.5,
#                     cpt_sal=lambda df_: df_.salary*1.5,
#                 )
#                 .assign(cpt_sal=lambda df_: df_.cpt_sal.astype("int"))
#                 .round(2)
#             )

#         return df

#     def _post_scrape_processing(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:

#         names_in_edits = set(self.edits.keys())
#         names_in_props = set(df.loc[df['fpts'] > 0.0].index)

#         if not self.constant:
#             print(f'Prop projection only: {str([name for name in names_in_props if name not in names_in_edits])}')
        
#         for name, edit in self.edits.items():
#             # Check if has prop projection
#             fpts = df.fpts.get(name, 0.0) #loc[name, 'fpts'] if name in df.index else -1

#             if not fpts:
#                 # If no prop projection
#                 df.loc[name, 'fpts'] = edit
#                 df.loc[name, 'e_fpts'] = 0.5*edit
#                 df.loc[name, 'props'] = '---'
                
#         for name, override_edit in self.override_edits.items():
#             if self.verbose:
#                 print(f'Overriding prop projection for {name}: {df.loc[name, "fpts"]} -> {override_edit} ')
#             df.loc[name, 'fpts'] = override_edit
#             df.loc[name, 'e_fpts'] = 0.5*override_edit


#         for col in ("fpts", "e_fpts"):
#             df[f"{col}/$"] = 1_000 * (df[col] / df.salary)

        

#         open_props = self.tracker.data().props_open.round(2).to_dict() if self.tracker else df.fpts.round(2).to_dict()
#         open_e_props = self.tracker.data().e_props_open.round(2).to_dict() if self.tracker else df.e_fpts.round(2).to_dict()

#         df['open'] = df.index.map(lambda name: open_props.get(name, 0.0))
#         df['e_open'] = df.index.map(lambda name: open_e_props.get(name, 0.0))

#         df = df.loc[df.fpts > 0.0]

#         df.loc[(df.open == 0.0) & (df.fpts > 0.0), 'open'] = df.loc[(df.open == 0.0) & (df.fpts > 0.0), 'fpts']
#         df.loc[(df.e_open == 0.0) & (df.e_fpts > 0.0), 'e_open'] = df.loc[(df.open == 0.0) & (df.e_fpts > 0.0), 'e_fpts']

#         df['movement'] = (df.fpts-df.open).round(2)
#         df['e_movement'] = (df.e_fpts-df.e_open).round(2)


#         if self.verbose:
#             for name, row in df.loc[df.movement != 0.0, ['fpts', 'open', 'movement']].iterrows():
#                 print(f'Prop movement for {name}: {row["open"]} -> {row["fpts"]} = {row["movement"]} move')

#         historical_path = os.path.join(DATA_DIR, 'historical', f'{datetime.date.today().isoformat()}.csv')
#         output_movement = kwargs.get('output_movement', False)
        
#         if any([
#             all([not self.constant, os.path.exists(historical_path), not df.loc[df.movement > 0.0].empty]),
#             all([self.constant, output_movement])
#         ]):

#             n_display = 5 if self.constant else 10
            
#             print('Biggest movers (fpts):')
#             display(df.assign(swing=lambda df_: abs(df_.movement)).sort_values('swing', ascending=False).drop('swing', axis=1).head(n_display))

#             print('Biggest movers (e_fpts):')
#             display(df.assign(swing=lambda df_: abs(df_.e_movement)).sort_values('swing', ascending=False).drop('swing', axis=1).head(n_display))
#         else:
#             if not self.constant:
#                 _output_msgs(['No prop movement since last scrape.'])


#         if not os.path.exists(historical_path):
#             df.to_csv(historical_path.replace('.csv', '-backup.csv'))
            
#         df.to_csv(historical_path)
#         df.to_csv(self.output_file)

#         self.tracker.update(df[['fpts', 'e_fpts']])

#         # Exporting to main (private) codebase containing models/model weights, season data, ownership, optimizer, etc
#         # The file private.py contains info which should not be public, thus is kept in .gitignore
#         if os.path.exists(os.path.join(os.getcwd().split("/src")[0], "src", "private.py")):
#             import private

#             for path in private.EXPORT_TEMPLATES:
#                 df.to_csv(path.format(site="draftkings"))

#         return

#     def player_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Counts players for each team to see if evernly spread out
#         """
#         df = (df
#               .groupby("team")["team"]
#               .agg(["count"])
#               .set_axis(["num-players"], axis=1)
#               .sort_values("num-players", ascending=False)
#              )


#         team_column = "TeamAbbrev" if self.site == "draftkings" else "Team"
#         total_teams = len(pd.read_csv(self.input_file, usecols=[team_column])[team_column].drop_duplicates())

#         _output_msgs([
#             f"{df.shape[0]} teams total",
#             f"Missing: {int(100*(1 - (len(df) / total_teams)))}% of teams"
#         ])

#         return df


#     def load_slate(self, **kwargs) -> pd.DataFrame:
#         # verbose = kwargs.get("verbose", 1)
#         # exclude = kwargs.get("exclude", list())
#         # inactive = kwargs.get("inactive", list())

#         ret: pd.DataFrame = (pd
#                              .read_csv(self.output_file)
#                              .pipe(lambda df_: df_.loc[df_["name"].isin(self.drop) == False])
#                              .set_index("name")
#                              .assign(own=lambda df_: df_.index.map(lambda name: self.ownership.get(name, 0.1)))
#                              .sort_values(kwargs.get('sort', 'e_fpts/$'), ascending=False)
#                             )

#         _output_msgs([f"{len(ret)} total players".upper(), self.player_distribution(ret)])

#         return ret
        
#     @_timeit
#     def load(self, **kwargs) -> pd.DataFrame:

#         update = kwargs.get("update", kwargs.get("run", True))

#         if update:
#             _output_msgs("Beginning WebScrape of NBA Player Props.")
#             self._post_scrape_processing( self._clean_and_scrape_data() )
        
#         return self.load_slate(**kwargs)


#     @_timeit
#     def constant_scrape(self, **kwargs):
#         # path = self.datafilepath(
#         #     f'{self.site}-props{"-sg" if self.mode == "showdown" else ""}'
#         # )
        
#         total_runs = 0
#         while True:
#             output_movement = False
#             if total_runs == 0:
#                 _output_msgs(['Initialized constant PropScraper'])
#             elif not total_runs % 10:
#                 output_movement = True
#                 _output_msgs([f'Performing scrape #{total_runs}'])
#             self._post_scrape_processing( self._clean_and_scrape_data(), output_movement=output_movement )
#             # self.ScrapeProps(output_movement=output_movement, **kwargs)

#             total_runs += 1
#             # time.sleep(10)
#             time.sleep(random.randint(30,60))