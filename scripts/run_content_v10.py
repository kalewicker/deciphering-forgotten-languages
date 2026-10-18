import argparse
from pathlib import Path
from fl_decipher.experiment_v10 import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='000010_kamri_content_capacity')
    args = parser.parse_args()
    print(run(Path(__file__).resolve().parents[1], args.run_id))
