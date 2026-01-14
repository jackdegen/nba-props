import requests
import datetime
import random

import pandas as pd
from bs4 import BeautifulSoup

from __utils import _clean_name, output_msgs
from designs import MoneyLine, Prop, Player

from .conversions import Conversions

class PropScraper:

    def __init__(self, **kwargs):
        """
        Class to scrape individual player props and convert to FPTS
        """
        self.convert = Conversions()
        self.directory_url: str = "https://www.scoresandodds.com/nba/players"

        self.scoresandodds_date_str = datetime.datetime.now().strftime("%m/%d")

        if kwargs.get('tomorrow', False):
            self.scoresandodds_date_str = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d")

        if kwargs.get('yesterday', False):
            self.scoresandodds_date_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%m/%d")

        if self.scoresandodds_date_str != datetime.datetime.now().strftime("%m/%d"):
            print(f'Scraping for {self.scoresandodds_date_str}\n')

        
    def create_webpage_directory(self) -> dict[str, dict[str, str]]:
        """
        Creates a dictionary containing the links to current and historical props
        for every player in the NBA, organized by team
        Links change daily -- No performance gain from saving directory as file since bs4 gets all links <1s
        """
        #         Load HTML into bs4
        soup = BeautifulSoup(requests.get(self.directory_url).text, "html.parser")

        #         Load each team data into dictionary, converting the full team name into initials as used in rest of data
        team_modules = {
            self.convert.team_name(team_html.find("h3").get_text()): team_html.find_all(
                "div", class_="module-body"
            )[0].find("ul")
            for team_html in soup.find_all("div", class_="module")
        }

        # clean_name = lambda name: self.convert.player_name(
        #     " ".join(name.split(" ")[:2]).replace(".", "")
        # )

        #         Parse HTML data for each team to organize links in easily searchable manner
        # {team: {name: url, ...}, ...}
        webpage_directory = {
            team: {
                _clean_name(a_tag.get_text()): self.directory_url.replace(
                    "/nba/players", a_tag["href"]
                )
                for a_tag in module.find_all("a")
            }
            for team, module in team_modules.items()
        }

        return webpage_directory

    @staticmethod
    def _past_week_date_strs(team: str|None = None) -> list[str,...]:
        """
        Return past week of datestrs in website form to determine if non-current dates
        are recent enough to use as a fallback
        """
        range_ = {}.get(team, range(0,1))
        
        return sorted(
            (datetime.datetime.now() - datetime.timedelta(days=N)).strftime("%m/%d")
            for N in range_
            # for N in range(1,6)
        )


    def _parse_spans(self, possible_date_spans):
        current_date_and_after = [possible_date_span.get_text() for possible_date_span in possible_date_spans[:100]] #soup.find_all("span")[18:]]
        msgs = []
        for idx, span_str in enumerate(current_date_and_after):

            if idx > 0:

                if all([
                    '/' in span_str,
                    all(not char in span_str for char in ('.', '$', )),
                    '@' in current_date_and_after[idx-1]
                ]):
                    msgs.append(f'{idx}: {span_str}')

        return msgs

    def _determine_next_date_index(self, possible_date_spans, skip: bool = False):
        current_date_and_after = [possible_date_span.get_text() for possible_date_span in possible_date_spans[:200]] #soup.find_all("span")[18:]]
        original_index = 18
        idx = original_index
        for idx_, span_str in enumerate(current_date_and_after):
            if all([
                idx_ != original_index,
                '/' in span_str,
                all(not char in span_str for char in ('.', '$', )),
                '@' in current_date_and_after[idx-1]
            ]):
                if not skip:
                    idx = idx_
                    break
                else:
                    skip = False

        return idx

    def scrape_player_props(
        self,
        name: str,
        url: str,
        site: str,
        team: str
    ) -> tuple[float, float, str]:

        # Load HTML
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        failed_scrape_return = (0.0, 0.0, '---')
        fallback = False # Tempermental ~ in progress


        # ####################################################################################################
        
        # if name == 'Kelly Olynyk':
        #     props = []
        #     props.append(Prop(name=name, date_str='01/03', stat='points', value=6.5, odds_over=MoneyLine('-122').implied_probability, odds_under=MoneyLine('-111').implied_probability))
        #     props.append(Prop(name=name, date_str='01/03', stat='rebounds', value=3.5, odds_over=MoneyLine('-128').implied_probability, odds_under=MoneyLine('-105').implied_probability))
        #     props.append(Prop(name=name, date_str='01/03', stat='assists', value=2.5, odds_over=MoneyLine('+120').implied_probability, odds_under=MoneyLine('-162').implied_probability))
        #     props.append(Prop(name=name, date_str='01/03', stat='steals', value=0.5, odds_over=MoneyLine('-195').implied_probability, odds_under=MoneyLine('+145').implied_probability))
        #     props.append(Prop(name=name, date_str='01/03', stat='blocks', value=0.5, odds_over=MoneyLine('+145').implied_probability, odds_under=MoneyLine('-195').implied_probability))
        #     props.append(Prop(name=name, date_str='01/03', stat='3 pointers', value=0.5, odds_over=MoneyLine('-145').implied_probability, odds_under=MoneyLine('+110').implied_probability))
        #     props.append(Prop(name=name, date_str='01/03', stat='turnovers', value=1.5, odds_over=MoneyLine('+100').implied_probability, odds_under=MoneyLine('+100').implied_probability))

            # player = Player(name=name, props=props)
            # fpts, e_fpts = player.fpts, player.e_fpts

            # return fpts, e_fpts, 'PRASB3T**'

        # ####################################################################################################
        try:
            if not soup.find_all("span"):
                return failed_scrape_return
        except AttributeError:
            return failed_scrape_return

        #         Make sure current, adjust for weird site format
        zero_fill_date = lambda dp: f"0{dp}" if len(dp) == 1 else dp
        date_str = "/".join([
            zero_fill_date(date_part)
            for date_part in soup.find_all("span")[18].get_text().split(" ")[1].split("/")
        ])

        # Players who dont often have props but get them because of injuries will still be posted (and overweighted) for the next slate
        if all([
            date_str != self.scoresandodds_date_str,
            date_str in self._past_week_date_strs(team=team)
        ]):
            fallback = True
        
        elif all([
            date_str != self.scoresandodds_date_str,
            not date_str in self._past_week_date_strs(team=team) 
        ]):
            # skip_teams = {'MEM'}
            next_date_index = self._determine_next_date_index(soup.find_all('span'))
            date_str = "/".join([
                zero_fill_date(date_part)
                for date_part in soup.find_all("span")[next_date_index].get_text().split(" ")[1].split("/")
            ])
            fallback = True

        if all([
            date_str != self.scoresandodds_date_str,
            not date_str in self._past_week_date_strs(team=team),
        ]):
            return failed_scrape_return
        
        try:
            props_rows = soup.find("table", class_="sticky").find("tbody").find_all("tr")
            if fallback:
                props_rows = soup.find_all("table", class_="sticky")[1].find("tbody").find_all("tr")

        except (AttributeError, IndexError):
            return failed_scrape_return

        prop_targets = ['Points', 'Rebounds', 'Assists', '3 Pointers', 'Steals', 'Blocks', 'Turnovers']

        # Form: Category Line Over Under
        target_rows = [row for row in props_rows if row.find("td").get_text().strip() in prop_targets]

        doubles = 0
        doubles_implied_odds = []
        props = []
        for rowtags in target_rows:
            info = [val.get_text().lower().strip() for val in rowtags.find_all('td')] # (Category, Line, Over, Under)
            
            stat = info[0]
            value = float(info[1])

            implied_odds_over = MoneyLine(info[2]).implied_probability
            implied_odds_under = MoneyLine(info[3]).implied_probability

            if value >= 9.5:
                doubles += 1
                doubles_implied_odds.append(implied_odds_over/sum([implied_odds_over, implied_odds_under]))

            # if name in ['Cam Spencer', 'Vince Williams']:
            #     if stat == 'points':
            #         value -= 1.0
            #     if stat == 'assists':
            #         value -= 1.0
            #     if stat == '3 pointers':
            #         value -= 1.0
            # if name == 'Cam Spencer' and stat == 'steals':
            #     value -= 1.0

            # if name == 'Ajay Mitchell':
            #     if stat == 'points':
            #         value += 1.0
            #     elif stat == 'assists':
            #         value += 1.0
            #     elif stat == '3 pointers':
            #         value += 1.0
            #     elif stat == 'steals':
            #         value += 1.0
                    
            props.append(Prop(
                name=name,
                date_str=date_str,
                stat=stat,
                value=value,
                implied_odds_over=implied_odds_over,
                implied_odds_under=implied_odds_under,     
            ))

        
        player = Player(name=name, props=props)
        fpts, e_fpts = player.fpts, player.e_fpts
        
        bonus = {2: 1.5, 3: 4.5}.get(doubles, 0.0)
        if bonus:
            fpts += bonus
            # e_fpts += 0.5*bonus
            
            e_factor = 1.0
            for implied_odds in doubles_implied_odds:
                e_factor *= implied_odds
            e_fpts += e_factor*bonus
        
        return fpts, e_fpts, player.shorthand

