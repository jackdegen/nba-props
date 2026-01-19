import os

# Error Handling for issues with data filing
class IncorrectInstallError(Exception):
    """If data directory does not exist"""
    def __init__(self):
        ERR_MSG = sum([
            "The specified data directory does not exist.",
            "If no path was specified and error was raised with the default, the project was not installed correctly.",
            "Please follow these steps:",
            "- Delete current project/directory (`nba-props`).",
            "- Re-try with the installation instructions in the README.md."
        ], '')
        super.__init__(ERR_MSG)