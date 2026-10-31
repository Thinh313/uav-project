"""Compatibility entrypoint. Executes the retained-metrics Python oracle.
No JavaScript verifier imports. FAIL metrics are saved before a nonzero exit.
"""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('oracle-result.py')), run_name='__main__')
