import os
import datetime
import pandas as pd

from dataclasses import dataclass

import settings.custom

@dataclass
class PropTracker:
    date_str: str = datetime.date.today().isoformat()
    init_time: str|None = None
    latest_time: str|None = None
    # offset: int = -15 

    # For deegs computer being fast
    @staticmethod
    def current_time(offset: int = -15):
        return (datetime.datetime.now() + datetime.timedelta(minutes=offset)).strftime("%H:%M")

    @staticmethod
    def _just_moved(props_: list[float,...]):
        if len(props_) < 2:
            return 1
        try:
            return 1 if any(props_[-n] != props_[-1*(n+1)] for n in range(1,3)) else 0
        except IndexError:
            return 1
    
    def __post_init__(self):

        self.source = f'/home/deegs/devel/repos/nba-props-git/nba-props/src/prophandler/proptrackers/{self.date_str}.parquet'
        if os.path.exists(self.source):
            df = pd.read_parquet(self.source).set_index('name')
            self.tracker = {name: list(props) for name, props in df.props.items()}
            self.e_tracker = {name: list(e_props) for name, e_props in df.e_props.items()}
            self.scrape_times = {name: list(scrape_times) for name, scrape_times in df.scrape_times.items()}
            
            self.init_time = df.init_time.iloc[0]
            self.latest_time = self.current_time()

        else:
            print('Initializing tracker...')
            self.tracker = {}
            self.e_tracker = {}
            self.scrape_times = {}

            self.init_time = self.current_time()
            self.latest_time = self.current_time()

    def update(self, fpts_df: pd.DataFrame) -> None:

        for name, row in fpts_df.iterrows():
            self.tracker[name] = self.tracker.get(name, []) + [row.fpts]
            self.e_tracker[name] = self.e_tracker.get(name, []) + [row.e_fpts]
            self.scrape_times[name] = self.scrape_times.get(name, []) + [self.latest_time]

        # Ensure trackers line up
        self.tracker = dict(sorted(self.tracker.items(), key=lambda item: item[0]))
        self.e_tracker = dict(sorted(self.e_tracker.items(), key=lambda item: item[0]))
        self.scrape_times = dict(sorted(self.scrape_times.items(), key=lambda item: item[0]))
        
        # Constructed dataframe this way so list of props all in a single column, whereas if did DataFrame(data={...}) it would automatically expand the list
        (pd
            .DataFrame()
            .assign(
                name=self.tracker.keys(),
                props=pd.Series([list(val) for val in self.tracker.values()]),
                e_props=pd.Series([list(val) for val in self.e_tracker.values()]),
                scrape_times=pd.Series([list(val) for val in self.scrape_times.values()]),
                init_time=self.init_time,
                latest_time=self.latest_time,
                props_open=lambda df_: df_.props.map(lambda props_: props_[0]),
                e_props_open=lambda df_: df_.e_props.map(lambda e_props_: e_props_[0]),
                props_now=lambda df_: df_.props.map(lambda props_: props_[-1]),
                e_props_now=lambda df_: df_.e_props.map(lambda e_props_: e_props_[-1]),
                movements=lambda df_: df_.props.map(lambda props: sum(1 for i, prop in enumerate(props) if all([i > 0, prop != props[i-1]]))),
                e_movements=lambda df_: df_.e_props.map(lambda e_props: sum(1 for i, e_prop in enumerate(e_props) if all([i > 0, e_prop != e_props[i-1]]))),
                just_moved=lambda df_: df_.props.apply(self._just_moved)
            )
            .sort_values('e_props_now', ascending=False)
            .reset_index(drop=True)
            .to_parquet(self.source)
        )

    def data(self) -> pd.DataFrame:
        return pd.read_parquet(self.source).set_index('name')


    def visualize(self, name: str, value: str = 'e_props') -> pd.DataFrame:
        df = self.data().loc[name]
    
        n_props = len(list(df.props))
        
        df_viz = pd.DataFrame(data = {
            'name': [name]*n_props,
            'props': list(df.props),
            'e_props': list(df.e_props),
            'scrape_times': list(df.scrape_times)
        })
    
        step = (max(df_viz[value]) - min(df_viz[value])) / 10
    
        return df_viz.groupby('name')[value].plot.line(
            title=f'{value} movement for {name} since {df.init_time}',
            figsize=(12,6),
            xticks=[i for i, time in enumerate(df_viz.scrape_times) if not i % 10],
            yticks=[min(df_viz[value]) + n*step for n in range(-1, n_props+10) if (min(df_viz[value]) + n*step) <= max(df_viz[value])+step]
        )
        
        
    def __bool__(self) -> bool:
        return len(self.tracker) > 0