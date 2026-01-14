# import datetime
# import requests
import unidecode

# import pandas as pd
# from bs4 import BeautifulSoup

# from __utils import output_msgs
from designs import Prop, Player

from dataclasses import dataclass

@dataclass
class Conversions:

    def __post_init__(self):

        self.initials_teams_map = {
            'ATL': 'Atlanta Hawks',
            'BKN': 'Brooklyn Nets',
            'BOS': 'Boston Celtics',
            'CHA': 'Charlotte Hornets',
            'CHI': 'Chicago Bulls',
            'CLE': 'Cleveland Cavaliers',
            'DAL': 'Dallas Mavericks',
            'DEN': 'Denver Nuggets',
            'DET': 'Detroit Pistons',
            'GS': 'Golden State Warriors',
            'HOU': 'Houston Rockets',
            'IND': 'Indiana Pacers',
            'LAC': 'Los Angeles Clippers',
            'LAL': 'Los Angeles Lakers',
            'MEM': 'Memphis Grizzlies',
            'MIA': 'Miami Heat',
            'MIL': 'Milwaukee Bucks',
            'MIN': 'Minnesota Timberwolves',
            'NO': 'New Orleans Pelicans',
            'NY': 'New York Knicks',
            'OKC': 'Oklahoma City Thunder',
            'ORL': 'Orlando Magic',
            'PHI': 'Philadelphia 76ers',
            'PHO': 'Phoenix Suns',
            'POR': 'Portland Trail Blazers',
            'SA': 'San Antonio Spurs',
            'SAC': 'Sacramento Kings',
            'TOR': 'Toronto Raptors',
            'UTA': 'Utah Jazz',
            'WAS': 'Washington Wizards'
        }

        # Invert
        self.teams_initials_map = {val: key for key, val in self.initials_teams_map.items()}

        # Other name (scoresandodds.com, basketball-reference.com, etc): DraftKings name
        self.standardize_names = {
            'Alex Sarr': 'Alexandre Sarr',
            'Carlton Carrington': 'Bub Carrington',
            'David Jones-Garcia': 'David Jones',
            'Kenneth Simpson': 'KJ Simpson',
            'Lu Dort': 'Luguentz Dort',
            'Moe Wagner': 'Moritz Wagner',
            'Robert Dillingham': 'Rob Dillingham'
        }

        self.team_initials_issues = {
            'CHO': 'CHA',
            'BRK': 'BKN',
            "GSW": "GS",
            "NOP": "NO",
            "NYK": "NY",
            "PHX": "PHO",
            "SAS": "SA",
        }

    def team_name(self, team_str: str) -> str:
        """All teams accounted for, so want KeyError if anything changes/breaks"""
        return self.teams_initials_map[team_str]

    def team_initials(self, initials_str: str) -> str:
        return self.initials_teams_map[initials_str]

    def player_name(self, name: str):
        return self.standardize_names.get(name, name)

    def initals_issue(self, initials_str: str) -> str:
        return self.inits_issues.get(initials_str, initials_str)