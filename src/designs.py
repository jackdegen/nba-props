from dataclasses import dataclass

SCORING = {
    "points": 1.0,
    "assists": 1.5,
    "rebounds": 1.25,
    "3 pointers": 0.5,
    "blocks": 2.0,
    "steals": 2.0,
}

NAME_ISSUES = {
    'Alex Sarr': 'Alexandre Sarr',
    'Ron Holland': 'Ronald Holland'
}

@dataclass(slots=True, frozen=True)
class Prop:
    name: str
    date: str
    stat: str
    value: str
    odds_over: float
    odds_under: float
    fpts: float = 0.0
    e_fpts: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'name', NAME_ISSUES.get(self.name, self.name))
        object.__setattr__(self, 'fpts', SCORING[self.stat.lower()]*self.value)
        object.__setattr__(self, 'e_fpts', self.odds_over*self.fpts)

    def to_dict(self):
        return {
            'name': self.name,
            'date': self.date,
            'stat': self.stat,
            'value': self.value,
            'odds_over': self.odds_over,
            'odds_under': self.odds_under,
            'fpts': self.fpts,
            'e_fpts': self.e_fpts
        }

@dataclass(slots=True, frozen=True)
class Player:
    name: str
    props: list[Prop,...]
    fpts: float = 0.0
    e_fpts: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'fpts', sum(prop.fpts for prop in self.props))
        object.__setattr__(self, 'e_fpts', sum(prop.e_fpts for prop in self.props))