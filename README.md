# nba-props


### Scrape up to date NBA props and convert into fanstasy points.

- Toggle settings in `params.py` for DraftKings or FanDuel, Classic or Single Game contests
- Input provided contest files from DFS sites in `data/` as `current-{site}.csv`; if Single Game, add `-sg` before `.csv` in file name.
    - Only manual step required from user besides toggling desired settings.
- Alerts to let you know what players have had props added since last run-through.
    - Initial run through will spit out large list of names
- Calculates `fpts` according to site rules, hence requirement to toggle setting.
    - Uses provided salaries to determine best allocation of salary for players as FPTS / $1,000, `fpts/$`.
- Factors in implied probabilities of player props for separate value of "Expected Fantasy Points", `e_fpts`.
    - Similarly uses this value with salary to determine best allocation, `e_fpts/$`
- Uses industy standard `value` of 5 x (`salary`/$1,000) as another metric, heavily correlates with previous two values
- Organizes players by site provided positions and teams.
- Calculates distribution of players by team in order to be cognizant of over representation of some teams.
    - Later games and teams with injuries tend to have props updated later in day
    
