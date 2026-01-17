import os
import math
from collections import defaultdict
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from . import utils

# Palette
COLORS_DUPE = ["bright_red", "bright_yellow", "bright_magenta", "orange3", "deep_pink2"]
COLORS_UNIQUE = ["green", "blue", "cyan", "chartreuse3", "sky_blue2", "plum3"]

def get_group(rel_path, level):
    parts = rel_path.split(os.sep)
    if len(parts) - 1 < level:
        group = os.path.dirname(rel_path)
        return group if group else "."
    return os.path.join(*parts[:level])

def run_scan(level):
    """Scans the current working directory and reports redundancy statistics."""
    cwd = os.getcwd()
    bof_root = utils.find_bof_root(cwd)

    if not bof_root:
        utils.console.print("[red]No .bof found.[/red]")
        return

    structure = utils.load_structure(bof_root)
    
    # 1. Map SHA1 -> Paths
    sha1_map = defaultdict(list)
    for rel_path, data in structure.items():
        abs_path = os.path.join(bof_root, rel_path)
        try:
            if os.path.commonpath([cwd, abs_path]) == cwd:
                sha1_map[data['sha1']].append(rel_path)
        except ValueError:
            continue

    # 2. Build Signatures
    redundancy_stats = defaultdict(int)
    signatures = defaultdict(int)
    total_contents = 0
    total_files = 0
    
    for sha1, paths in sha1_map.items():
        total_contents += 1
        count = len(paths)
        total_files += count
        
        is_redundant = count > 1

        if is_redundant:
            redundancy_stats[count] += 1
        
        groups = set()
        for path in paths:
            full_path = os.path.join(bof_root, path)
            rel_to_cwd = os.path.relpath(full_path, cwd)
            groups.add(get_group(rel_to_cwd, level))
        
        sig = (frozenset(groups), is_redundant)
        signatures[sig] += 1

    if total_contents == 0:
        utils.console.print("[yellow]Index is empty.[/yellow]")
        return

    # 3. Sorting (Duplicates first)
    sorted_sigs = sorted(
        signatures.items(), 
        key=lambda item: (item[0][1], item[1]), 
        reverse=True
    )
    
    # We want the bar to be ~100 characters wide max 
    TARGET_WIDTH = 80 
    
    # If total contents < TARGET_WIDTH, we can use 1 block per file.
    # Otherwise, we scale down.
    if total_contents <= TARGET_WIDTH:
        scale_ratio = 1.0
        display_mode = "exact"
    else:
        scale_ratio = TARGET_WIDTH / total_contents
        display_mode = "scaled"

    bar_text = Text()
    
    # Legend Table
    legend_table = Table(box=None, padding=(0, 2), show_header=True, header_style="bold white")
    legend_table.add_column("Color", width=6, justify="center")
    legend_table.add_column("State", width=10)
    legend_table.add_column("Location Groups")
    legend_table.add_column("Count", justify="right")
    legend_table.add_column("%", justify="right")

    dupe_idx = 0
    uniq_idx = 0
    
    # Track used width to handle rounding errors
    current_width = 0

    for (groups_set, is_redundant), count in sorted_sigs:
        # Determine Color
        if is_redundant:
            color = COLORS_DUPE[dupe_idx % len(COLORS_DUPE)]
            dupe_idx += 1
            lbl = "Duplicate"
            char = "█"
        else:
            color = COLORS_UNIQUE[uniq_idx % len(COLORS_UNIQUE)]
            uniq_idx += 1
            lbl = "Unique"
            char = "▓"

        # Calculate visual blocks
        if display_mode == "exact":
            blocks = count
        else:
            # Calculate proportional width
            blocks = math.ceil(count * scale_ratio)
            # Ensure very small segments get at least 1 block if they exist
            if blocks < 1: blocks = 1
        
        # Add to Bar
        bar_text.append(char * blocks, style=color)
        current_width += blocks
        
        # Legend Data
        percentage = (count / total_contents) * 100
        group_list = sorted(list(groups_set))
        if len(group_list) == 1:
            loc = group_list[0]
        else:
            loc = f"Shared: {', '.join(group_list)}"

        legend_table.add_row(
            Text("████", style=color),
            f"[dim]{lbl}[/dim]",
            loc,
            str(count),
            f"{percentage:.1f}%"
        )

    # First report : Redundancy Stats
    table = Table(title="Global Redundancy Report")
    table.add_column("Copies", justify="right", style="cyan", no_wrap=True)
    table.add_column("File Count", justify="right", style="magenta")

    sorted_stats = sorted(redundancy_stats.items())
    if not sorted_stats:
        utils.console.print("[green]No duplicates found.[/green]")
    else:
        for copies, count in sorted_stats:
            table.add_row(str(copies), str(count))
        utils.console.print(table)

    # Second Report : Storage Overview
    utils.console.print(f"\n[bold]Storage Overview (Level {level})[/bold]")
    utils.console.print(f"Total Files: {total_files} | Unique Contents: {total_contents}")
    if display_mode == "scaled":
        utils.console.print(f"[dim italic]Visualization scaled (approx 1 block = {math.ceil(1/scale_ratio)} files)[/dim italic]")
    
    utils.console.print(Panel(bar_text, title="Distribution Map", border_style="dim", expand=False))
    utils.console.print(legend_table)