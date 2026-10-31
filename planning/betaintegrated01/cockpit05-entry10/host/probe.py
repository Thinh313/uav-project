"""Read-only current free-space probe. Never primes, writes, launches or allocates."""
from pathlib import Path
from importlib import import_module
import argparse,json,shutil
R=Path(__file__).resolve().parents[4]
policy=import_module('planning.betaintegrated01.cockpit05-entry10.host.policy')

def inspect(path=R):
    result=policy.task_budget(shutil.disk_usage(path).free)
    result.update(probePath=str(Path(path).resolve()),guardPrimed=False,actualRuntimeAdmission=False)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--path',default=str(R));args=parser.parse_args();print(json.dumps(inspect(args.path),indent=2))
