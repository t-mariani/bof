import os
import shutil
from . import utils

def run_clean():
    """Removes the .bof directory in the current working directory."""
    cwd = os.getcwd()
    bof_path = os.path.join(cwd, utils.BOF_DIR)
    
    if os.path.exists(bof_path):
        try:
            shutil.rmtree(bof_path)
            utils.console.print("Removed .bof directory.")
        except Exception as e:
            utils.console.print(f"Error removing .bof: {e}")
    else:
        utils.console.print("No .bof directory found in current folder.")