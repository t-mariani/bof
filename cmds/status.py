import os
from . import utils

def run_status():
    """Checks the status of the current folder against the .bof index"""
    cwd = os.getcwd()
    bof_root = utils.find_bof_root(cwd)

    if not bof_root:
        print("No .bof directory found in current or parent folders.")
        return

    is_parent = bof_root != cwd
    if is_parent:
        print(f"Using .bof found in parent: {bof_root}")
    else:
        print("Using .bof in current directory.")

    # Load data
    index_meta = utils.load_index_metadata(bof_root)
    structure = utils.load_structure(bof_root)
    
    if not index_meta:
        print("Index corrupted.")
        return

    indexing_date = index_meta['indexing_date']
    
    modified_count = 0
    added_count = 0

    # Iterate over files on disk
    for root, dirs, files in os.walk(cwd):
        if utils.BOF_DIR in dirs:
            dirs.remove(utils.BOF_DIR)

        for file in files:
            abs_path = os.path.join(root, file)
            # path relative to the BOF root (to match CSV keys)
            rel_to_bof = os.path.relpath(abs_path, bof_root)

            # Check logic
            if rel_to_bof in structure:
                # File exists in index, check modification time
                current_mtime = os.path.getmtime(abs_path)
                # Use a small epsilon for float comparison or strict > 
                if current_mtime > indexing_date:
                    modified_count += 1
            else:
                # File not in index
                added_count += 1

    utils.console.rule("[bold]BOF Status[/bold]") # Prints a horizontal line
    
    if modified_count > 0:
        utils.console.print(f"[yellow]• Files modified since last index:[/yellow] [bold]{modified_count}[/bold]")
    
    if added_count > 0:
        utils.console.print(f"[green]• Files added since last index:[/green]    [bold]{added_count}[/bold]")

    if modified_count == 0 and added_count == 0:
        utils.console.print(":sparkles: [bold green]bof index up to date[/bold green]")