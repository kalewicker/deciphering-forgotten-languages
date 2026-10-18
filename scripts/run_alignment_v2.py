from pathlib import Path
import argparse
from fl_decipher.experiment_v2 import run
parser=argparse.ArgumentParser()
parser.add_argument('--run-id',required=True)
args=parser.parse_args()
print(run(Path(__file__).resolve().parents[1],args.run_id)/'report.md')
