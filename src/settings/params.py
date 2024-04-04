draftkings: bool = True
singlegame: bool = False

SITE: str = {
    True: 'draftkings',
    False: 'fanduel'
}[draftkings]


MODE: str = {
    True: 'single-game',
    False: 'main-slate'
}[singlegame]

scraper_settings_msgs = [
    'Current parameters for scraping props:',
    f'     - Site: {SITE.replace("fanduel", "FanDuel").replace("draftkings", "DraftKings")}',
    f'     - Mode: {" ".join([part.capitalize() for part in MODE.split("-")])}',
]

print(*scraper_settings_msgs, sep='\n')