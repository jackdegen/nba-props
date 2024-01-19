import pandas as pd

def pandas_settings() -> None:
    for option in ('display.max_rows', 'display.max_columns', 'display.width'):
        pd.set_option(option, 250)
        
    pd.set_option('display.memory_usage', False)
    return None

if __name__ == "customsettings":
    pandas_settings()