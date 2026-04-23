# config.py
import sys
import os

def get_project_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
def get_os_type():
    # automatically recognizes OS
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform.startswith("darwin"):
        return "darwin"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return "unknown"
def get_debug():
    return True
