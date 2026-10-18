import argparse
from pathlib import Path
from fl_decipher.experiment_v3 import run
parser = argparse.ArgumentParser(description='Run the frozen passage alignment factorial offline')
parser.add_argument('--run-id', required=True)
args = parser.parse_args()
print(run(Path(__file__).resolve().parents[1], args.run_id) / 'report.md')
