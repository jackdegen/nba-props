import os
import random
import time
import datetime
import pandas as pd
from dataclasses import dataclass, field

import settings.custom
from _utils import _clean_name
from _errors import IncorrectInstallError

SCORING = {
    'draftkings': {
        "points": 1.0,
        "rebounds": 1.25,
        "assists": 1.5,
        "3 pointers": 0.5,
        "blocks": 2.0,
        "steals": 2.0,
        "turnovers": -0.5
    },

    'fanduel': {
        "points": 1.0,
        "rebounds": 1.2,
        "assists": 1.5,
        "3 pointers": 0.0,
        "blocks": 3.0,
        "steals": 3.0,
        "turnovers": -1.0
    }
}

# Common order for prop listings: PRA3BST
SHORTHAND_ORDER = list(SCORING['draftkings'].keys())

# Current date -> YYYY-MM-DD -> common date format for filing and similar basic usage
CONTEST_DATE_STR = datetime.date.today().isoformat()

# Current date -> MM/DD -> site's date format used to determine if up-to-date props
SITE_CURRENT_DATE_STR = datetime.datetime.now().strftime("%m/%d")
# Toggle commented out for switching to props: yesterday, tomorrow, etc. -> ensure input data aliged
# SITE_CURRENT_DATE_STR = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d")

# Data directory where all non-python files are stored
# Made global for easy configuration to other destinations
# Default is defined only relative to this project and works right away
default_data_dir = os.getcwd().replace('src', 'data')
def _load_data_dir(data_dir: str|None = default_data_dir) -> str:
    if not data_dir:
        data_dir = default_data_dir
    if not os.path.exists(data_dir):
        raise IncorrectInstallError
    return data_dir

DATA_DIR = _load_data_dir()

@dataclass(frozen=True, slots=True)
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
        
        object.__setattr__(self, 'name', _clean_name(self.name))
        object.__setattr__(self, 'fpts', SCORING['draftkings'][self.stat.lower()]*self.value)

        object.__setattr__(self, 'vig', sum([self.implied_odds_over, self.implied_odds_under]) - 1.0)

        total_implied_probability = sum([self.implied_odds_over, self.implied_odds_under])
        object.__setattr__(self, 'true_odds_over', self.implied_odds_over / total_implied_probability)
        object.__setattr__(self, 'true_odds_under', self.implied_odds_under / total_implied_probability)

        # With no vig: true_odds_over + true_odds_under = 1.0
        object.__setattr__(self, 'e_fpts', self.true_odds_over*self.fpts)
        
        object.__setattr__(self, 'shorthand', self.stat[0].upper())
        object.__setattr__(self, 'past', self.date_str != SITE_CURRENT_DATE_STR)

    
    def to_dict(self):
        return {
            'name': self.name,
            'date': self.date_str,
            'stat': self.stat,
            'value': self.value,
            'implied_odds_over': self.implied_odds_over,
            'implied_odds_under': self.implied_odds_under,
            'vig': self.vig,
            'true_odds_over': self.true_odds_over,
            'true_odds_under': self.true_odds_under,
            'fpts': self.fpts,
            'e_fpts': self.e_fpts
        }

    @property
    def df(self) -> pd.DataFrame:
        """Used for filing of individual props before converting to FPTS"""
        return pd.DataFrame(data={column: [value] for column, value in self.to_dict().items()})


# Impute props that are not listed for players
# Up to discretion, based on type of players not to have these props listed
# Imputed props appear in "()" in shorthand: Ex: PRA3T(BS)
IMPUTE_PROPS = {
    'steals': 0.5, # S/B props vary, but most starters will have offered
    'blocks': 0.5, # Want to include for all since valuable FPTS but dont want to overshoot, hence 0.5
    # '3 pointers': 0.5, # Most shooters will have props offered
    'turnovers': 1.5, # NBA average
}

@dataclass(slots=True, frozen=True)
class Player:
    name: str
    props: list[Prop,...] = field(default_factory=list)
    site: str = 'draftkings'
    scoring: dict[str,float] = field(default_factory=dict)
    fpts: float = 0.0
    e_fpts: float = 0.0
    props_log: list[str,...] = field(default_factory=list)
    shorthand: str = ''

    @staticmethod
    def _impute_missing_props(props_log: list[str,...], scoring: dict[str,float]) -> tuple[float,float,str]:

        fpts, e_fpts = 0.0, 0.0
        shorthand = ''
        
        if props_log:
            
            shorthand_vals = []
            missing_props = set(IMPUTE_PROPS.keys()).intersection(set(scoring.keys()).difference(set(props_log)))
    
            for missing in missing_props:
                shorthand_vals.append(missing[0].upper())
                fpts += scoring[missing]*IMPUTE_PROPS[missing]
                e_fpts += 0.5*scoring[missing]*IMPUTE_PROPS[missing]

            shorthand = f'({"".join(sorted(shorthand_vals, key=lambda sh: 'PRASB3T'.index(sh)))})' if missing_props else ''
            
        return fpts, e_fpts, shorthand

    @staticmethod
    def _save_props(props: list[Prop,...]) -> None:
        """
        - Saves current INDIVIDUAL props in standardized format.
        - Easy to transfer from .parquet to .csv, .parquet was 
          used because of better performance when building the
          minimal viable feature.
        - Robust, complete and easy-to-use feature in development
          currently since so many requests made for this tool
          completely separate from fantasy.
        - Current version usage (commented out) + additonal info at EOF.
        """
        master_props_file = os.path.join(DATA_DIR, 'playerprops', f'{CONTEST_DATE_STR}.parquet')

        if not os.path.exists(master_props_file):
            pd.concat(p.df for p in props).to_parquet(master_props_file)
            return
        
        (pd
         .concat([
             pd.read_parquet(master_props_file),
             pd.concat(p.df for p in props)
         ])
        ).to_parquet(master_props_file)

        return
        
    def __post_init__(self):
        
        if not self.props:
            object.__setattr__(self, 'props_log', [])
            object.__setattr__(self, 'fpts', 0.0)
            object.__setattr__(self, 'e_fpts', 0.0)
            object.__setattr__(self, 'shorthand', '---')
            
        else:
            object.__setattr__(self, 'scoring', SCORING[self.site])
            
            object.__setattr__(self, 'props_log', sorted([prop.stat for prop in self.props], key=lambda stat_: SHORTHAND_ORDER.index(stat_)))

            imputed_fpts, imputed_efpts, imputed_shorthand = self._impute_missing_props(self.props_log, self.scoring)
            past_props_marker = '*' if self.props[0].past else ''
            object.__setattr__(self, 'fpts', sum(prop.fpts for prop in self.props) + imputed_fpts)
            object.__setattr__(self, 'e_fpts', sum(prop.e_fpts for prop in self.props) + imputed_efpts)
            object.__setattr__(self, 'shorthand', ''.join(sorted([prop.shorthand for prop in self.props], key=lambda sh: 'PRASB3T'.index(sh))) + imputed_shorthand + past_props_marker)

            # In progress, loads individual props but need to work on better data transfer
            # Need to build multi-tiered tracker as well to track various line movements
            # self._save_props(self.props)
