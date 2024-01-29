import pandas as pd
import matplotlib.pyplot as plt

def pandas_settings() -> None:
    for option in ('display.max_rows', 'display.max_columns', 'display.width'):
        pd.set_option(option, 250)

    pd.set_option('display.precision', 3)
    pd.set_option('styler.format.precision', 2)
    pd.set_option('display.memory_usage', False)
    return

def matplotlib_settings() -> None:
    plt.style.use('fivethirtyeight')

    return

if __name__ == "customsettings":
    pandas_settings()
    matplotlib_settings()