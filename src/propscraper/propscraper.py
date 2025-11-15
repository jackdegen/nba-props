import requests
import datetime

import pandas as pd
from bs4 import BeautifulSoup

from designs import Prop, Player

class Conversions:

    def __init__(self):
        """
        Conversions to enable system to work across different sites and formats
        """

        self.inits_issues: dict[str, str] = {
            "SAS": "SA",
            "PHX": "PHO",
            "GSW": "GS",
            "NOP": "NO",
            "NYK": "NY",
        }

        self.inits_teams: dict[str, str] = {
            "NY": "New York Knicks",
            "LAL": "Los Angeles Lakers",
            "MIA": "Miami Heat",
            "UTA": "Utah Jazz",
            "PHO": "Phoenix Suns",
            "LAC": "Los Angeles Clippers",
            # 'LAC': 'LA Clippers',
            "PHI": "Philadelphia 76ers",
            "DAL": "Dallas Mavericks",
            "DEN": "Denver Nuggets",
            "BOS": "Boston Celtics",
            "ATL": "Atlanta Hawks",
            "CLE": "Cleveland Cavaliers",
            "DET": "Detroit Pistons",
            "TOR": "Toronto Raptors",
            "CHA": "Charlotte Hornets",
            "ORL": "Orlando Magic",
            "MEM": "Memphis Grizzlies",
            "SA": "San Antonio Spurs",
            "MIL": "Milwaukee Bucks",
            "IND": "Indiana Pacers",
            "CHI": "Chicago Bulls",
            "OKC": "Oklahoma City Thunder",
            "GS": "Golden State Warriors",
            "HOU": "Houston Rockets",
            "BKN": "Brooklyn Nets",
            "POR": "Portland Trail Blazers",
            "NO": "New Orleans Pelicans",
            "MIN": "Minnesota Timberwolves",
            "SAC": "Sacramento Kings",
            "WAS": "Washington Wizards",
        }

        # Invert
        self.teams_inits: dict[str, str] = {
            val: key for key, val in self.inits_teams.items()
        }

        #         scoresandodds.com: DraftKings name
        self.name_issues: dict[str, str] = {
            "Lu Dort": "Luguentz Dort",
            "Moe Wagner": "Moritz Wagner",
            "KJ Martin": "Kenyon Martin",
            "Devonte Graham": "Devonte' Graham",
            "Shaq Harrison": "Shaquille Harrison",
            "Robert Dillingham": "Rob Dillingham",
            'Kenneth Simpson': 'KJ Simpson',
            'Alex Sarr': 'Alexandre Sarr'
            # 'KJ Simpson': 'Kenneth Simpson',
        }

    def team_name(self, team_str: str) -> str:
        return self.teams_inits[team_str]

    def team_initials(self, team_init_str: str) -> str:
        return self.inits_teams[team_init_str]

    def player_name(self, name: str):
        return self.name_issues.get(name, name)

    def initals_issue(self, team_inits: str) -> str:
        return self.inits_issues.get(team_inits, team_inits)


class PropScraper:

    def __init__(self, **kwargs):
        """
        Class to scrape individual player props and convert to FPTS
        """
        self.convert = Conversions()
        self.directory_url: str = "https://www.scoresandodds.com/nba/players"

        self.current_date_str = datetime.datetime.now().strftime("%m/%d")

        if kwargs.get('tomorrow', False):
            self.current_date_str = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d")

        if kwargs.get('yesterday', False):
            self.current_date_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%m/%d")

        if self.current_date_str != datetime.datetime.now().strftime("%m/%d"):
            print(f'Scraping for {self.current_date_str}\n')
        # self.prop_frames = list()

    #     Creates a dictionary containing the links to current and historical props
    #     for every player in the NBA, organized by team
    def create_webpage_directory(self) -> dict[str, dict[str, str]]:

        #         Load HTML into bs4
        soup = BeautifulSoup(requests.get(self.directory_url).text, "html.parser")

        #         Load each team data into dictionary, converting the full team name into initials as used in rest of data
        team_modules = {
            self.convert.team_name(team_html.find("h3").get_text()): team_html.find_all(
                "div", class_="module-body"
            )[0].find("ul")
            for team_html in soup.find_all("div", class_="module")
        }

        clean_name = lambda name: self.convert.player_name(
            " ".join(name.split(" ")[:2]).replace(".", "")
        )

        #         Parse HTML data for each team to organize links in easily searchable manner
        teams_players_links: dict[str, dict[str, str]] = {
            team: {
                clean_name(a_tag.get_text()): self.directory_url.replace(
                    "/nba/players", a_tag["href"]
                )
                for a_tag in module.find_all("a")
            }
            for team, module in team_modules.items()
        }

        return teams_players_links

    # Implied Probability = 100 / (Odds + 100)
    @staticmethod
    def pos_ml_prob(ml: str) -> float:
        return 100 / sum([int(ml[1:]), 100])

    # Implied Probability = (-1*(Odds)) / (-1(Odds) + 100) ->
    @staticmethod
    def neg_ml_prob(ml: str) -> float:
        ml: int = int(ml)
        return (-1 * ml) / sum([-1 * ml, 100])

    @classmethod
    def implied_probability(cls, ml: str):
        if ml == "+100":
            return 0.5

        return cls.pos_ml_prob(ml) if ml[0] == "+" else cls.neg_ml_prob(ml)

    @classmethod
    def expected_value(cls, val: float, ml: str) -> float:
        return cls.implied_probability(ml) * val

    @staticmethod
    def _parse_moneyline(ml_str: str|None) -> str:
        if not ml_str:
            return '+100'

        return str(ml_str)

    def scrape_player_props(
        self,
        name: str,
        url: str,
        site: str
    ) -> tuple[float, float]:

        # Load HTML
        soup = BeautifulSoup(requests.get(url).text, "html.parser")

        try:
            if not soup.find_all("span"):
                return (0.0, 0.0)
        except AttributeError:
            return (0.0, 0.0)

        #         Make sure current, adjust for weird site format
        zero_fill_date = lambda dp: f"0{dp}" if len(dp) == 1 else dp
        date_str = "/".join([
            zero_fill_date(date_part)
            for date_part in soup.find_all("span")[18].get_text().split(" ")[1].split("/")
        ])

        if date_str != self.current_date_str:
            return (0.0, 0.0)

        try:
            props_rows = soup.find("table", class_="sticky").find("tbody").find_all("tr")

        except AttributeError:
            print(f"{name} -> Failing to find table...")
            return (0.0, 0.0)

        prop_targets = ['Points', 'Rebounds', 'Assists', '3 Pointers', 'Steals', 'Blocks']

        # Form: Category Line Over Under
        target_rows = [row for row in props_rows if row.find("td").get_text() in prop_targets]

        doubles = 0
        props = []
        for rowtags in target_rows:
            info = [val.get_text().lower().strip() for val in rowtags.find_all('td')] # (Category, Line, Over, Under)
            
            stat = info[0]
            value = float(info[1])

            if value >= 10.0:
                doubles += 1

            odds_over = self.implied_probability(self._parse_moneyline(info[2]))
            odds_under = self.implied_probability(self._parse_moneyline(info[3]))
            
            props.append(Prop(
                name=name,
                date=date_str,
                stat=stat,
                value=value,
                odds_over=odds_over,
                odds_under=odds_under,
            ))
        
        player = Player(name=name, props=props)
        fpts, e_fpts = player.fpts, player.e_fpts
        
        bonus = {2: 1.5, 3: 4.5}.get(doubles, 0.0)
        if bonus:
            fpts += bonus
            e_fpts += 0.5*bonus
        
        return (fpts, e_fpts)

