draftkings: bool = True
singlegame: bool = False

site: str = {
    True: 'draftkings',
    False: 'fanduel'
}[draftkings]


mode: str = {
    True: 'single-game',
    False: 'main-slate'
}[singlegame]