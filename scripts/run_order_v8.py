import argparse
from pathlib import Path
from fl_decipher.experiment_v8 import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='000008_kamri_order_admission')
    args = parser.parse_args()
    print(run(Path(__file__).resolve().parents[1], args.run_id))
