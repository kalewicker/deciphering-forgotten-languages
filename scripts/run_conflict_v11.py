import argparse
from pathlib import Path
from fl_decipher.experiment_v11 import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='000011_kamri_anchor_conflicts')
    args = parser.parse_args()
    print(run(Path(__file__).resolve().parents[1], args.run_id))
