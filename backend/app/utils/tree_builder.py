"""Build file tree structure for heatmap visualization."""
from pathlib import Path
from typing import Any

def build_file_tree(paths: list[str], values: dict[str, float]) -> dict[str, Any]:
    """Build nested dict for d3 treemap from flat file paths and debt values."""
    root: dict = {"name": "root", "children": []}
    
    for path in paths:
        parts = Path(path).parts
        node = root
        for part in parts[:-1]:
            child = next((c for c in node.get("children", []) if c["name"] == part and "children" in c), None)
            if not child:
                child = {"name": part, "children": []}
                node.setdefault("children", []).append(child)
            node = child
        # Leaf node
        leaf = {"name": parts[-1], "value": values.get(path, 1), "path": path}
        node.setdefault("children", []).append(leaf)
    
    return root

def flatten_tree(tree: dict, prefix: str = "") -> list[dict]:
    result = []
    for child in tree.get("children", []):
        full_path = f"{prefix}/{child['name']}" if prefix else child["name"]
        if "children" in child:
            result.extend(flatten_tree(child, full_path))
        else:
            result.append({"path": full_path, "value": child.get("value", 1)})
    return result
