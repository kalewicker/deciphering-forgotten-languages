import argparse
from pathlib import Path
from fl_decipher.experiment_v4 import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='000004_kamri_precision_mass')
    args = parser.parse_args()
    print(run(Path(__file__).resolve().parents[1], args.run_id))
