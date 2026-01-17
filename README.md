# BOF - Box of Files

**BOF** is a lightweight, content-addressable CLI tool for tracking file redundancy and managing storage topology. It treats your filesystem as a content database, allowing you to identify duplicates, visualize distribution, and detect changes across directory trees.

## ⚡ Quick Start

### Requirements
* Python 3.6+
* `rich` library (for visualization)

```bash 
pip install rich
```

Or use [pixi.sh](https://pixi.prefix.dev/latest/) [recommended]

### Usage
Run the tool from the root of any directory you wish to analyze.

```bash 
python bof.py index 
```

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`index`** | `-p [path]` | Scans files, calculates hashes, and creates/updates the `.bof` index. Merges existing child indexes efficiently. |
| **`status`** | None | Compares the current filesystem state against the `.bof` index (Modified/New files). |
| **`scan`** | `-l [level]` | Analyzes redundancy. `-l` groups files by directory depth for topological visualization. |
| **`clean`** | None | Removes the `.bof` directory. |

---

## 🛠 Design Choices & Architecture

BOF is built on specific architectural decisions to ensure scalability and portability.

### 1. Content-Addressable Storage Logic
BOF tracks files by **content (SHA1)**, not by filename.
* **Benefit:** Renaming a file does not change its identity. Moving a file within the indexed tree is detected as the same content.
* **Deduplication:** Duplicates are identified immediately because they share the same content hash in `content/{sha1}.json`.


### 2. Separation of Content vs. Structure
Data is stored in two parts within `.bof/`:
* **`content/`**: JSON files named by hash (e.g., `da39a3...json`). Stores immutable properties like `size` and `mimetype`. Can be used in the future to group content for `scan` but still in development.
* **`structure.csv`**: Maps `filepath` -> `sha1` + `mtime`.


### 3. Topology Visualization (The Waffle Chart)
The `scan` command uses a scalable "Waffle Chart" visualization.
* **Problem:** Lists of duplicates are hard to parse mentally.
* **Solution:** A color-coded bar representing the entire storage volume.
    * **Hot Colors:** Redundant data (Duplicates).
    * **Cool Colors:** Unique data.
    * **Signatures:** Files are grouped by their specific *combination* of locations (e.g., "Shared between `/src` and `/backup`"), allowing you to see structural redundancy at a glance.

### 4. No intracated .bof
* BOF does not use a hidden `.bof` in every directory. Instead, it uses a single `.bof` at the root of the indexed tree and merges child indexes during `index` runs.
* **Benefit:** In the future, this allows BOF to be used as a portable index for external drives or network shares without cluttering every folder.

---

## 📂 Artifact Structure

When you run `bof index`, the following structure is created:

```text
.bof/
├── content/           # Metadata for unique contents
│   ├── {sha1}.json    # { size: 1024, mimetype: "text/plain" }
│   └── ...
├── structure.csv      # Relational map: Filepath <-> SHA1
└── index.json         # Timestamp of last index & max_mtime seen
```
