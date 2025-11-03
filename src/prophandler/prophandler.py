import os
import random
import time
import datetime

import pandas as pd

from propscraper import PropScraper


"""
TODO:
    - Still way to much repetition for accomodating different sites
    - Can easily create some functions/classes for conversions, issues, export, etc.
    - utils file instead of including them in top of PropHandler
"""


class PropHandler:

    @staticmethod
    def output_box(msg: str, *args, **kwargs) -> None:
        """
        Pretty printer
        """
        char = kwargs.get("char", "=")
        tb = "".join(["   ", char * len(msg)])

        print(*[tb, f"   {msg}", tb], sep="\n")
        return

    @staticmethod
    def output_msgs(msgs: list[str, ...]) -> None:
        """
        Prettier pretty printer
        """

        padding = "=" * max([len(msg_) for msg_ in msgs])
        output = [padding] + msgs + [padding]

        print(*output, sep="\n")

        return

    @staticmethod
    def output_times(func, **kwargs):
        """
        Wrapper function to print performance time in Xm Ys format
        """
        start = time.perf_counter()
        func(**kwargs)
        stop = time.perf_counter()

        elapsed: float = (stop - start) / 60.0
        elapsed_str: str = str(elapsed)
        minutes: int = int(elapsed_str.split(".")[0])

        decimals: float = float(f'0.{elapsed_str.split(".")[1]}')
        seconds: int = int(decimals * 60.0)

        performance_time: str = f"{minutes}m {seconds}s."

        print(f"{func.__name__} performance time: {performance_time}\n")

        return

    @staticmethod
    def datafilepath(fname: str, **kwargs) -> str:
        """
        Returns full file path for data instead of using relative path.
        TODO: Auto adjusments for showdown
        """
        if ".csv" not in fname:
            fname += ".csv"

        return os.path.join(os.getcwd().split("src")[0], "data", fname)

    @staticmethod
    def clean_name(name: str) -> str:
        """
        Properly formats name so aligns with all data
        """
        return " ".join(name.split(" ")[:2]).replace(".", "")

    def __init__(self, site: str, mode: str, **kwargs):
        """
        Provides the logistical handling for scraping props with various possible conditions
        Goal of this was to have as a little code in the actual notebook, just interactive stuff.
        Old Name: UI --> confusing since usually means other things, but very very very basic user interface
        """
        self.site = site
        self.mode = mode

        self.Props = PropScraper(**kwargs)

        # URL directory, indexed first by team, then by name
        # Directory in typical sense, not computer sense
        self.directory = self.Props.create_webpage_directory()

        # Last update
        self.last = pd.read_csv(
            self.datafilepath(f'{site}-props{"-sg" if mode == "showdown" else ""}')
        ).set_index("name")

        self.edits = kwargs.get('edits', dict())

        self.DATA_DIR = os.getcwd().replace('src', 'data')

    def save_directory(self) -> None:
        """
        Saves URLs to every single player to a local .csv file for two reasons:
            1. Don't have to scrape URLs every time one runs the code.
            2. In case the directory page goes down (which it sometimes does),
                one can still navigate the site seamlessly.
        """
        # Initialize empty dictionary to be loaded with data from directory, which is a dictionary
        df_data = {column: list() for column in ["team", "name", "url"]}

        # Assumes non empty directory (handler in different function)
        for team, player_links in self.directory.items():
            for name, url in player_links.items():
                df_data["team"].append(team)
                df_data["name"].append(name)
                df_data["url"].append(name)

        df = pd.DataFrame(df_data)

        df.to_csv(self.datafilepath("url-directory"), index=False)

        return

    def load_directory(self) -> dict[str, dict[str, str]]:
        """
        Load last saved directory in case of website issues
        """

        df = pd.read_csv(self.datafilepath("url-directory"))

        team_dfs = {
            team: (df
                   .loc[df["team"] == team]
                   .set_index("name")
                   .drop(["team"], axis=1)
                   .T
                   .to_dict()
                  )
            for team in df["team"].drop_duplicates()
        }

        directory = {team: dict() for team in team_dfs}

        # TODO: Improve this process somehow
        for team, names in team_dfs.items():
            for name in names:
                directory[team][name] = team_dfs[team][name]["url"]

        return directory

    def scrape_props(
        self, name: str, team: str, site: str, **kwargs
    ) -> tuple[float, float]:
        """
        Scrape props for individual player with site-specific scoring, return zeroes if issues with site / naming / etc.
        """
        # if name in self.edits:
        #     return (self.edits[name], 0.5*self.edits[name])
        
        try:
            return self.Props.scrape_player_props(
                name,
                self.directory[team][name],
                site,
                **kwargs
            )

        except KeyError:
            return (0.0, 0.0)

    def check_site(self) -> str:
        """
        Returns message about site directory status
        """
        return (
            "No Issues."
            if len(self.directory)
            else "ScoresAndOdds.com is down / page containing links is down."
        )

    def update_directory(self) -> None:
        """
        In case there are issues, adjust directory to read last saved links and hope they work (URLs change)
        """
        if len(self.directory):
            self.save_directory()
        else:
            self.directory = self.load_directory()

        return

    def scrape_draftkings(self, **kwargs) -> None:
        """
        Scrape props for all players in ../data/current-draftkings.csv and save for those players where props exist.
        """
        verbose = kwargs.get('verbose', 1)
        fname = "current-draftkings"
        inactive = kwargs.get('inactive', list())
        if self.mode == "showdown":
            fname += "-sg"

        columns: dict[str, str] = {
            "Name": "name",
            "Roster Position": "pos",
            "TeamAbbrev": "team",
            "Salary": "salary",
        }

        inits_issues = {
            "SAS": "SA",
            "PHX": "PHO",
            "GSW": "GS",
            "NOP": "NO",
            "NYK": "NY",
        }

        MIN_SAL: int = 3_000 if kwargs.get("drop_minimums", True) else 0

        keep_minimums: tuple[str, ...] = ('Ron Holland',)
        drop_minimums: tuple[str, ...] = tuple(
            [
                name
                for name in (
                    pd.read_csv(
                        self.datafilepath(fname), usecols=["Name", "Salary"]
                    ).pipe(lambda df_: df_.loc[df_["Salary"] == MIN_SAL]["Name"])
                )
                if name not in keep_minimums
            ]
        )

        df: pd.DataFrame = (
            pd.read_csv(self.datafilepath(fname), usecols=columns)
            .rename(columns, axis=1)
            .pipe(
                lambda df_: df_.loc[(df_["pos"] != "CPT")]
            )  # For single game contests
            .assign(
                name=lambda df_: df_.name.str.replace(".", "", regex=False),
                pos=lambda df_: df_.pos.str.replace("/[GF]/UTIL", "", regex=True)
                .str.replace("C/UTIL", "C", regex=False)
                .str.replace("/[GF]", "", regex=True),
            )
            # .pipe(lambda df_: df_.loc[(df_["name"].isin(drop_minimums) == False)])
            # .pipe(lambda df_: df_.loc[(df_['salary'] > 3_000)])
        )

        name_issues: dict[str, str] = {"Moe Wagner": "Moritz Wagner"}

        df["name"] = df["name"].map(lambda x: name_issues.get(x, self.clean_name(x)))
        df["team"] = df["team"].map(lambda x: inits_issues.get(x, x))

        df["input"] = tuple(zip(df["name"], df["team"]))
        # df['input'] = df.loc[:,['name','team']].apply(tuple, axis=1) # Does the same thing
        df["output"] = df["input"].apply(lambda x: self.scrape_props(*x, "draftkings"))

        df["fpts"] = df["output"].map(lambda x: x[0])
        df["e_fpts"] = df["output"].map(lambda x: x[1])


        for col in ("fpts", "e_fpts"):
            df[f"{col}/$"] = 1000 * (df[col] / df["salary"])

        df["5x"] = 5 * (df["salary"] / 1000)
        df["value"] = df["fpts"] - df["5x"]

        df = (df
              # .loc[df["fpts"] > 0.0]
              .loc[df['name'].isin(inactive) == False]
              .drop(["input", "output", "5x"], axis=1)
              # .assign(fpts_1k=lambda df_: 1000 * df_.fpts / df_.salary)
              # .rename({"fpts_1k": "fpts-1k"}, axis=1)
              .sort_values("value", ascending=False)
              .set_index("name")
              .round(2)
        )

        single_game = (
            self.mode == "showdown" or len(df["team"].drop_duplicates()) == 2
        )

        if single_game:
            df = (
                df.assign(
                    cpt_pts=lambda df_: df_.fpts * 1.5,
                    cpt_sal=lambda df_: df_.salary * 1.5,
                    # cpt_fpts_1k=lambda df_: 1000 * df_.cpt_pts / df_.cpt_sal,
                )
                .assign(cpt_sal=lambda df_: df_.cpt_sal.astype("int"))
                .round(2)
            )

        
        names_in_edits = set(self.edits.keys())
        names_in_props = set(df.loc[df['fpts'] > 0.0].index)

        print(f'Prop projection only: {", ".join([name for name in names_in_props if name not in names_in_edits])}')

        df['no-props'] = 0
        
        for name, edit in self.edits.items():
            # Check if has prop projection
            fpts = df.loc[name, 'fpts'] if name in df.index else -1

            if fpts == -1:
                # If not in contest pool
                pass
            
            elif fpts > 0.0:
                # If prop projection
                if verbose:
                    symbol = {True: '+', False: '-'}[fpts > edit] * 5
                    print(f'Player props added for: {name}, projection went from {edit} -> {fpts} ({symbol}).')
            else:
                # If no prop projection
                df.loc[name, 'fpts'] = edit
                df.loc[name, 'no-props'] = 1
                

        df = df.loc[df['fpts'] > 0.0]

        for col in ("fpts", "e_fpts"):
            df[f"{col}/$"] = 1000 * (df[col] / df["salary"])

        path = self.datafilepath(f'draftkings-props{"-sg" if single_game else ""}')
                
        self.last = pd.read_csv(path)
        df.to_csv(path)

        df.to_csv(os.path.join(self.DATA_DIR, 'historical', f'{datetime.date.today().isoformat()}.csv'))

        # Exporting to main (private) codebase containing models/model weights, season data, ownership, optimizer, etc
        # The file private.py contains info which should not be public, thus is kept in .gitignore
        if os.path.exists(
            os.path.join(os.getcwd().split("/src")[0], "src", "private.py")
        ):
            import private

            for path in private.EXPORT_TEMPLATES:
                df.to_csv(path.format(site="draftkings"))

            # df.to_csv(private.EXPORT_TEMPLATE.format(site="draftkings"))

        return

    def scrape_fanduel(self, **kwargs) -> None:
        """
        Scrape props for all players in ../data/current-fanduel.csv and save for those players where props exist.
        """

        fname = "current-fanduel"
        if self.mode == "showdown":
            fname += "-sg"

        columns: dict[str, str] = {
            "Nickname": "name",
            "Position": "pos",
            "Team": "team",
            "Salary": "salary",
            "Injury Indicator": "injury",
        }

        MIN_SAL: int = 3_500 if kwargs.get("drop_minimums", False) else 0

        keep_minimums: tuple[str, ...] = tuple()
        drop_minimums: tuple[str, ...] = tuple(
            [
                name
                for name in (
                    pd.read_csv(
                        self.datafilepath(fname, usecols=["Nickname", "Salary"])
                    ).pipe(lambda df_: df_.loc[df_["Salary"] == MIN_SAL]["Nickname"])
                )
                if name not in keep_minimums
            ]
        )

        df: pd.DataFrame = (
            pd.read_csv(self.datafilepath(fname), usecols=columns)
            .rename(columns, axis=1)
            .pipe(lambda df_: df_.loc[df_["injury"] != "O"])
            .drop("injury", axis=1)
            .assign(name=lambda df_: df_.name.str.replace(".", "", regex=False))
            # .pipe(lambda df_: df_.loc[(df_['name'].isin(drop_minimums) == False)])
        )

        # scoresandodds : FanDuel
        name_issues = {
            "Moe Wagner": "Moritz Wagner",
        }

        df["name"] = df["name"].map(lambda x: name_issues.get(x, self.clean_name(x)))
        df["input"] = df.loc[:, ["name", "team"]].apply(tuple, axis=1)
        df["output"] = df["input"].apply(lambda x: self.scrape_props(*x, "fanduel"))

        df["fpts"] = df["output"].map(lambda x: x[0])
        df["e_fpts"] = df["output"].map(lambda x: x[1])

        for col in ("fpts", "e_fpts"):
            df[f"{col}/$"] = 1000 * (df[col] / df["salary"])

        df["5x"] = 5 * (df["salary"] / 1000)
        df["value"] = df["fpts"] - df["5x"]

        df = (
            df.loc[df["fpts"] > 0.0]
            .drop(["input", "output", "5x"], axis=1)
            .assign(fpts_1k=lambda df_: 1000 * df_.fpts / df_.salary)
            .rename({"fpts_1k": "fpts-1k"}, axis=1)
            .sort_values("value", ascending=False)
            .set_index("name")
            .round(2)
        )

        single_game = (
            self.mode == "showdown" or len(df["team"].drop_duplicates()) == 2
        )

        path = self.datafilepath(f'fanduel-props{"-sg" if single_game else ""}')

        self.last = pd.read_csv(path)
        df.to_csv(path)

        # Exporting to main (private) codebase containing models/model weights, season data, ownership, optimizer, etc
        # The file private.py contains info which should not be public, thus is kept in .gitignore
        if os.path.exists(
            os.path.join(os.getcwd().split("/src")[0], "src", "private.py")
        ):
            import private
            # Not saving to new repo as of now
            df.to_csv(private.EXPORT_TEMPLATES[0].format(site="fanduel"))

        return

    def ScrapeProps(self, **kwargs) -> None:
        """
        Handler so can just run this function instead of flipping between two above functions.
        Can technically do in one line:
            - This is more aesthetically pleasing.
            - Single line conditionals without an assignment look funky.
        """
        if self.site == "draftkings":
            self.scrape_draftkings(**kwargs)
        else:
            self.scrape_fanduel(**kwargs)

        return

    def player_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Counts players for each team to see if evernly spread out
        """
        df = (df
              .groupby("team")["team"]
              .agg(["count"])
              .set_axis(["num-players"], axis=1)
              .sort_values("num-players", ascending=False)
             )

        fname = f"current-{self.site}"
        if self.mode == "showdown":
            fname += "-sg"

        team_column = "TeamAbbrev" if self.site == "draftkings" else "Team"

        total_teams: int = len(
            pd.read_csv(self.datafilepath(fname), usecols=[team_column])[
                team_column
            ].drop_duplicates()
        )

        print(f"{df.shape[0]} teams total...")
        print(f"Missing: {int(100*(1 - (len(df) / total_teams)))}% of teams...\n")

        return df

    def load_slate(self, **kwargs) -> pd.DataFrame:
        verbose = kwargs.get("verbose", 1)
        exclude = kwargs.get("exclude", list())
        inactive = kwargs.get("inactive", list())

        fname = f'{self.site}-props{"-sg" if self.mode == "showdown" else ""}'

        ret: pd.DataFrame = (pd
                             .read_csv(self.datafilepath(fname))
                             .pipe(lambda df_: df_.loc[df_["name"].isin(inactive) == False])
                             .pipe(lambda df_: df_.loc[df_["team"].isin(exclude) == False])
                             .sort_values(by=kwargs.get("sort", "fpts"), ascending=False)
                             .set_index("name")
                            )

        if verbose:
            msg = f"{len(ret)} total players".upper()
            self.output_box(msg)
            print(self.player_distribution(ret))

        return ret

    def load(self, **kwargs) -> pd.DataFrame:

        update = kwargs.get("update", kwargs.get("run", True))

        if update:
            self.output_box("Beginning WebScrape of NBA Player Props.", char="-")
            self.output_times(
                self.ScrapeProps, drop_minimums=kwargs.get("drop_minimums", False)
            )
        
        df = self.load_slate(**kwargs)

        # inactive = kwargs.get("inactive", list())

        return (df
                # .loc[df.index.isin(inactive) == False]
                .sort_values(kwargs.get("sort", "value"), ascending=False)
               )

    def create_pos_dfs(self):
        if hasattr(self, "pos_dfs"):
            return self.pos_dfs

        df = (
            self.load_slate(verbose=0).drop("fpts-1k", axis=1).copy(deep=True)
        )  # Still need to figure out!!

        self.pos_dfs = dict()
        for pos in ("PG", "SG", "SF", "PF", "C", "G", "F"):
            df[pos] = df["pos"].map(lambda pos_: int(pos in pos_))
            self.pos_dfs[pos] = (
                df.loc[df[pos] == 1]
                .drop(pos, axis=1)
                .sort_values("value", ascending=False)
            )  # .copy(deep=True)
            df = df.drop(pos, axis=1)

        return self.pos_dfs

    def load_pos(self, pos: str) -> pd.DataFrame:
        return self.create_pos_dfs()[pos]

    def create_team_dfs(self):
        if hasattr(self, "team_dfs"):
            return self.team_dfs

        df = (
            self.load_slate(verbose=0).drop("fpts-1k", axis=1).copy(deep=True)
        )  # Still need to figure out!!

        self.team_dfs = dict(
            sorted(
                {
                    team: (
                        df.loc[df["team"] == team].sort_values("value", ascending=False)
                    )
                    for team in df["team"].drop_duplicates()
                }.items(),
                key=lambda item: item[0],
            )
        )

        return self.team_dfs

    def load_team(self, team: str) -> pd.DataFrame:
        try:
            return self.create_team_dfs()[team]
        except KeyError:
            print(f"{team} not playing in current contest.\n")
            return pd.DataFrame()

    def constant_scrape(self, **kwargs):
        path = self.datafilepath(
            f'{self.site}-props{"-sg" if self.mode == "showdown" else ""}'
        )

        
        
        while True:

            last = set(pd.read_csv(path)["name"])

            self.ScrapeProps(**kwargs)

            cur = set(pd.read_csv(path)["name"])

            updated = list(cur.difference(last))
            if len(updated):
                msgs = [f'Added the following player{"s" if len(updated) > 1 else ""}:']
                for name in updated:
                    msgs.append(f"- {name}")
                self.output_msgs(msgs)

            # Disguise requests a little bit
            rand_int_sleep_time = random.randint(2, 7)
            time.sleep(rand_int_sleep_time)
