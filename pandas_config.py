#  This config file offers basic configurations for visual dataframe generation

import pandas as pd

MAX_COLUMS = None             # Recommended to set to None
MAX_ROWS = None
MAX_WIDTH = None              # Recommended to set to None to prevent dataframe from splitting up into multiple lines
MAX_COLWIDTH = 75             # Set to None to disable column truncation
COLHEADER_JUSTIFY = "left"
ALIGN_ASIAN_CHARS = True      # Noticably affects processing power (2x slower), aligns asian characters properly with columns


def configurate_pd():
    pd.set_option("display.max_columns", MAX_COLUMS)
    pd.set_option("display.max_rows", MAX_ROWS)
    pd.set_option("display.width", MAX_WIDTH)
    pd.set_option("display.max_colwidth", MAX_COLWIDTH)
    pd.set_option("display.colheader_justify", COLHEADER_JUSTIFY)
    pd.set_option("display.unicode.east_asian_width", ALIGN_ASIAN_CHARS)
