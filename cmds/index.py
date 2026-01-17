import os
import shutil
import time
import json
import csv
import mimetypes
from rich.progress import Progress, SpinnerColumn, TextColumn
from . import utils

def run_index(path):
    """Indexes the target directory into a .bof directory."""
    target_dir = os.path.abspath(path)
    bof_dir = os.path.join(target_dir, utils.BOF_DIR)
    
    # Check parent
    parent_bof = utils.find_bof_root(os.path.dirname(target_dir))
    if parent_bof:
        utils.console.print(f"[yellow]Warning:[/yellow] A .bof index already exists in parent: [bold]{parent_bof}[/bold]")
        utils.console.print("WORK IN PROGRESS : Aborting indexing to avoid nested .bof directories, should update .bof in parent instead.")
        # TODO 
        return

    # Reset .bof, TODO WIP should only update to avoid reindexing everything
    if os.path.exists(bof_dir):
        shutil.rmtree(bof_dir)
    os.makedirs(os.path.join(bof_dir, utils.CONTENT_DIR))
    
    structure_data = []
    max_mtime = 0.0
    indexing_start = time.time()
    
    # We use a context manager for the UI
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True # Remove bar when done
    ) as progress:
        
        task = progress.add_task(f"[green]Indexing {target_dir}...", total=None)
        
        # Walker
        for root, dirs, files in os.walk(target_dir):
            # 1. Child Logic
            child_bof_path = os.path.join(root, utils.BOF_DIR)
            child_meta = utils.load_index_metadata(root)
            
            # If child index is valid and fresh
            if child_meta and child_meta.get('max_mtime', float('inf')) <= child_meta.get('indexing_date', 0):
                progress.console.print(f"[blue]  -> Merging child index:[/blue] {os.path.relpath(root, target_dir)}")
                
                # Import child structure
                child_struct = utils.load_structure(root)
                for c_path, c_data in child_struct.items():
                    # Reconstruct full relative path from current target_dir
                    rel_from_root = c_path # path relative to child root
                    abs_path = os.path.join(root, rel_from_root)
                    new_rel_path = os.path.relpath(abs_path, target_dir)
                    
                    structure_data.append([new_rel_path, c_data['sha1'], c_data['mtime']])
                    
                    # Copy content JSON if it doesn't exist in new parent
                    src_json = os.path.join(child_bof_path, utils.CONTENT_DIR, f"{c_data['sha1']}.json")
                    dst_json = os.path.join(bof_dir, utils.CONTENT_DIR, f"{c_data['sha1']}.json")
                    if os.path.exists(src_json) and not os.path.exists(dst_json):
                        shutil.copy2(src_json, dst_json)

                    if c_data['mtime'] > max_mtime:
                        max_mtime = c_data['mtime']

                # Remove the child .bof
                shutil.rmtree(child_bof_path)
                
                # Don't walk into this directory anymore (we consumed it)
                dirs.remove(utils.BOF_DIR)
                del dirs[:] # TODO a bit ugly but works 
                continue
                
            if utils.BOF_DIR in dirs:
                dirs.remove(utils.BOF_DIR)

            # 2. File Indexing
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)
                
                # Update spinner text
                progress.update(task, description=f"Indexing: {file}")

                try:
                    stat = os.stat(filepath)
                    mtime = stat.st_mtime
                    if mtime > max_mtime: max_mtime = mtime
                    
                    sha1 = utils.get_sha1(filepath)
                    if not sha1: continue 

                    json_path = os.path.join(bof_dir, utils.CONTENT_DIR, f"{sha1}.json")
                    if not os.path.exists(json_path):
                        content_meta = {
                            "size": stat.st_size,
                            "mimetype": mimetypes.guess_type(filepath)[0]
                        }
                        with open(json_path, 'w') as jf:
                            json.dump(content_meta, jf)

                    structure_data.append([rel_path, sha1, mtime])

                except Exception as e:
                    utils.console.print(f"[red]Error processing {rel_path}: {e}[/red]")

    with open(os.path.join(bof_dir, utils.STRUCTURE_FILE), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filepath', 'sha1', 'mtime'])
        writer.writerows(structure_data)

    with open(os.path.join(bof_dir, utils.INDEX_FILE), 'w') as f:
        json.dump({"indexing_date": indexing_start, "max_mtime": max_mtime}, f)

    utils.console.print(f"[bold green]✓ Indexing complete.[/bold green] Processed {len(structure_data)} files.")