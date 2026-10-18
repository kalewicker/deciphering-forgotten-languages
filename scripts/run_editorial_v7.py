import argparse
from pathlib import Path
from fl_decipher.experiment_v7 import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='000007_kamri_editorial_robustness')
    args = parser.parse_args()
    print(run(Path(__file__).resolve().parents[1], args.run_id))
