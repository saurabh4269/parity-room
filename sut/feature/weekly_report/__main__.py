import sys

from .digest import render
from .events import load_events
from .settings import load_settings

if __name__ == "__main__":
    print(render(load_events(sys.argv[1]), load_settings()))
