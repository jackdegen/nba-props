import os
import requests
import datetime

import numpy as np
import pandas as pd

from typing import Callable

from bs4 import BeautifulSoup

# Returns current date as string in desired format for files
def date_path() -> str:
    return '.'.join([
        datetime.datetime.now().strftime("%m%d%y"),
        # (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m%d%y"),
        'csv'
    ])

class Conversions:
    
    def __init__(self):
        """
        Conversions to enable system to work across different sites and formats
        """
        
        self.inits_issues: dict[str,str] = {
            'SAS': 'SA',
            'PHX': 'PHO',
            'GSW': 'GS',
            'NOP': 'NO',
            'NYK': 'NY'
        }
        
        self.inits_teams: dict[str, str] = {
            'NY': 'New York Knicks',
            'LAL': 'Los Angeles Lakers',
            'MIA': 'Miami Heat',
            'UTA': 'Utah Jazz',
            'PHO': 'Phoenix Suns',
            'LAC': 'Los Angeles Clippers',
            # 'LAC': 'LA Clippers',
            'PHI': 'Philadelphia 76ers',
            'DAL': 'Dallas Mavericks',
            'DEN': 'Denver Nuggets',
            'BOS': 'Boston Celtics',
            'ATL': 'Atlanta Hawks',
            'CLE': 'Cleveland Cavaliers',
            'DET': 'Detroit Pistons',
            'TOR': 'Toronto Raptors',
            'CHA': 'Charlotte Hornets',
            'ORL': 'Orlando Magic',
            'MEM': 'Memphis Grizzlies',
            'SA': 'San Antonio Spurs',
            'MIL': 'Milwaukee Bucks',
            'IND': 'Indiana Pacers',
            'CHI': 'Chicago Bulls',
            'OKC': 'Oklahoma City Thunder',
            'GS': 'Golden State Warriors',
            'HOU': 'Houston Rockets',
            'BKN': 'Brooklyn Nets',
            'POR': 'Portland Trail Blazers',
            'NO': 'New Orleans Pelicans',
            'MIN': 'Minnesota Timberwolves',
            'SAC': 'Sacramento Kings',
            'WAS': 'Washington Wizards'
        }

        # Invert
        self.teams_inits: dict[str,str] = { val: key for key, val in self.inits_teams.items() }
        
#         scoresandodds.com: FanDuel name
        self.name_issues: dict[str,str] = {
            'Lu Dort': 'Luguentz Dort',
            'Moe Wagner': 'Moritz Wagner',
            'KJ Martin': 'Kenyon Martin',
            'Devonte Graham': "Devonte' Graham",
            'Shaq Harrison': 'Shaquille Harrison'
        }
    
        
    def team_name(self, team_str: str) -> str:
        return self.teams_inits[team_str]
    
    def team_initials(self, team_init_str: str) -> str:
        return self.inits_teams[team_init_str]
    
    def player_name(self, name: str):
        return self.name_issues.get(name,name)
    
    def initals_issue(self, team_inits: str) -> str:
        return self.inits_issues.get(team_inits,team_inits)
    
    
    

class PropScraper:
    
    def __init__(self):
        """
        Class to scrape individual player props and convert to FPTS
        """
        self.convert = Conversions()
        self.directory_url: str = 'https://www.scoresandodds.com/nba/players'
        
        self.current_date_str = datetime.datetime.now().strftime("%m/%d")
        # self.current_date_str = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d")
        # self.prop_frames = list()
        
    
#     Creates a dictionary containing the links to current and historical props
#     for every player in the NBA, organized by team
    def create_webpage_directory(self) -> dict[str, dict[str, str]]:
        
#         Load HTML into bs4
        soup = BeautifulSoup(
            requests.get(self.directory_url).text,
            'html.parser'
        )

#         Load each team data into dictionary, converting the full team name into initials as used in rest of data
        team_modules = {
            self.convert.team_name(team_html.find('h3').get_text()): team_html.find_all('div', class_='module-body')[0].find('ul')
            for team_html in soup.find_all('div', class_='module')
        }
        
        
        clean_name: Callable[[str],str] = lambda name: self.convert.player_name(' '.join(name.split(' ')[:2]).replace('.', ''))
        
#         Parse HTML data for each team to organize links in easily searchable manner
        teams_players_links: dict[str, dict[str, str]] = {
            
            team: {
                clean_name(a_tag.get_text()): self.directory_url.replace(
                    '/nba/players',
                    a_tag['href']
                )
                for a_tag in module.find_all('a')
            }
            
            for team, module in team_modules.items()
            
        }
        
        return teams_players_links
    
    # Implied Probability = 100 / (Odds + 100)
    @staticmethod
    def pos_ml_prob(ml: str) -> float:
        return 100 / sum([int(ml[1:]),100])
    
    # Implied Probability = (-1*(Odds)) / (-1(Odds) + 100) ->
    @staticmethod
    def neg_ml_prob(ml: str) -> float:
        ml: int = int(ml)
        return (-1*ml) / sum([-1*ml,100])
        
    @classmethod
    def implied_probability(cls, ml: str):
        if ml == '+100':
            return 0.5
        
        return cls.pos_ml_prob(ml) if ml[0]=='+' else cls.neg_ml_prob(ml)
    
    @classmethod
    def expected_value(cls, val: float, ml: str) -> float:
        return cls.implied_probability(ml)*val
        
    def scrape_player_props(
        self, 
        name: str, 
        url: str, 
        site: str
    ) -> tuple[float,float]:
        
#         Load HTML
        soup = BeautifulSoup(
            requests.get(url).text, 
            'html.parser'
        )
        
        # module = soup.find('div', class_="module-body scroll")
        
        try:
            if not len(soup.find_all('span')):
                return (0.0,0.0)
        except AttributeError:
            return (0.0, 0.0)
        
#         Make sure current
        zerofill = lambda dp: f'0{dp}' if len(dp) == 1 else dp
        date_str = '/'.join([
            zerofill(dp) for dp in soup.find_all('span')[18].get_text().split(' ')[1].split('/')
        ])

        
        if date_str != self.current_date_str:
            return (0.0,0.0)

        # props_rows = soup.find('table', class_='sticky').find('tbody').find_all('tr')
        try:
            props_rows = soup.find('table', class_='sticky').find('tbody').find_all('tr')

        except AttributeError:
            print(f'{name} -> Still failing here...')
            # return (0.0, 0.0)
        
        # Steals, blocks are options but noisy, better to use season data for opponents
        
        site_targets: dict[str,tuple[str,...]] = {
            'fanduel': (
                'Points', 
                'Rebounds', 
                'Assists',
                'Steals',
                'Blocks'
            ),
            'draftkings': (
                'Points',
                'Rebounds',
                'Assists',
                '3 Pointers',
                'Steals',
                'Blocks'
            )
        }

        # Form: Category Line Over Under
        target_rows = [row for row in props_rows if row.find('td').get_text() in site_targets[site]]
    
        # TODO: Figure out more efficient way for this, dict(zip()) probably best
        props = {
            # 'name': list(),
            'stat': list(),
            'value': list(),
            # 'over': list(),
            'e_value': list(),
            'fpts': list(),
            'e_fpts': list()
            # 'under': list()
        }
        
        
        site_multipliers: dict[str,dict[str,float]] = {
            'fanduel': {'assists': 1.5, 'rebounds': 1.2, 'blocks': 3.0, 'steals': 3.0, '3 pointers': 0.0},
            'draftkings': {'assists': 1.5, 'rebounds': 1.25, '3 pointers': 0.5, 'blocks': 2.0, 'steals': 2.0, }
        }

        # For DK bonuses
        doubles = 0
        
        multipliers: dict[str,float] = site_multipliers[site]
        for rowtags in target_rows:
            vals = [val.get_text().lower() for val in rowtags.find_all('td')] # (Category, Line, Over, Under)
            
            stat: str = vals[0]
            props['stat'].append(stat)

            # Convert to whole number
            # statval = sum([float(vals[1]), 0.5])
            statval = sum([float(vals[1]), 0.0])
            props['value'].append(statval)

            if statval >= 10.0:
                doubles += 1
            
            overml: str = vals[2]
            
            props['e_value'].append(self.expected_value(statval, overml))
            
            multi: float = multipliers.get(stat, 1.0)
            fpts: float = multi*statval
            
            props['fpts'].append(fpts)
            props['e_fpts'].append(self.expected_value(fpts, overml))
            # props['under'].append(vals[3])
        
        
        df: pd.DataFrame = pd.DataFrame(props).round(2)
        
        fpts = df['fpts'].sum()

        if site == 'draftkings':
            if doubles == 2:
                fpts += 1.5
    
            elif doubles >= 3:
                fpts += 4.5
            
        return (fpts, df['e_fpts'].sum())