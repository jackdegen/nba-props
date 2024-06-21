[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fjackdegen%2Fnba-props%2F&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=Views&edge_flat=false)](https://hits.seeyoufarm.com)
[![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# nba-props

### Scrape up to date NBA props and convert into fanstasy points.

- Different settings in `src/main.ipynb` for DraftKings or FanDuel (`SITE`), Classic or Single Game contests (`MODE`).
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
    
### Installation

- To install this is just like installing any other GitHub repository.
- I have noticed I've received lots of clones, and I assume it is individuals in the DFS / Sports Betting space, so I figured I'd add some directions for people not used to dealing with Python super heavily.
- On Linux or MacOS: Installation is done from the Command Line so open Terminal or equivalent.
    - (windows users, I'm working on it)
- *(optional)* If want to install in location that is not home directory:

```
$ cd path/to/target/directory
```

- Clone this repository:

```
$ git clone https://github.com/jackdegen/nba-props
```

- *(optional)* If you want to create a virtual environment, `.venv`; if you prefer a different name, repalce `.venv` with it:
    - *Note: if you do not do this step and you do not use Python, you will have to manually install `pandas`, `requests`, `BeautifulSoup`, and all other necessary packages on your system with `pip`. This may require dealing with different system dependencies*
    - I **strongly suggest** following these steps, even if you are not entirely sure what they are doing.
    - They are just installing the external libraries required to run the code ***only*** in this directory, not on your entire machine.

```
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
```

- If you have **JupyterLab/JupyterNotebook**, I suggest running the code in that as it is easier on the eyes and more interactive if you are familiar with Jupyter.
- *If not, check back here in a few days as I configure the code to work in the Python shell of the command line.*

```
$ jupyter-lab
```
- This should have opened up a **Jupyter Notebook** in your browser.
- Go to the navigation menu, and open `src/main.py`.
- Toggle settings in first cell for `SITE` and `MODE`.
- Run the cells either one by one or with fast-forward button, just be wary of last cell.
- Need to be careful with the cell containing the following: `handler.constant_scrape()`:
    - Running an infinite loop to update data and add any new players.
    - However, it will need to be manually stopped in order to make notebook interactive again.
    - Doing so will trigger a `KeyboardInterrupt` error, that is not an actual error it is a result of shutting down the loop.
    - All data will have been saved and updated behind the scenes, will not be any output since it runs quietly in background. 
- A new file will have been created in `data/` containing the info for the NBA slate that day for whichever site you specified.
- You can read this in with `pd.read_csv()` or simply access it using `handler` to get the data and assign it to a new variable if you would like to further interact with the dataset in a notebook.
- The `PropHandler` class already has some built in functionality for basic data analysis, so feel free to consult the source code in `src/prophandler/prophandler.py`.

</br>

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

</br>
</br>
