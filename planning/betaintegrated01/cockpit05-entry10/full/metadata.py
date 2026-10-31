"""Pure allocation ledger; exclude only explicitly budgeted full-case raw/export objects."""
from pathlib import Path

def allocated_metadata(root):
    root=Path(root);total=0
    if not root.exists():return 0
    for path in root.rglob('*'):
        if not path.is_file()or path.is_symlink():continue
        parts=path.relative_to(root).parts
        if len(parts)>=3 and parts[0]=='actual-combined01'and parts[1]in('raw','AP-state'):continue
        if parts==('actual-combined01','control','native-private.tar'):continue
        total+=path.stat().st_blocks*512
    return total
