import os
import sys
from pathlib import Path

parent_directory = Path(__file__).parent.parent.absolute()


def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        basedir = os.path.join(os.path.dirname(sys.executable), relative_path)
    else:
        basedir = os.path.join(parent_directory, relative_path)
    return basedir
