"""Run tests available without the local research archive; exclusions are explicit."""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))

# These modules load the historical, generated v1 lexicon at import time.
ARCHIVE_MODULES = {'test_editorial_v7', 'test_coverage_v9', 'test_content_v10', 'test_conflict_v11'}
ARCHIVE_CASES = {
    'test_alignment_v2.AlignmentV2Tests.test_frozen_data_and_lexicon_have_no_fresh_training_evidence',
    'test_passage_v3.PassageTests.test_frozen_inputs_and_no_new_training_evidence',
    'test_precision_v4.PrecisionTests.test_generator_truth_and_function_eligibility',
    'test_register_v5.RegisterTests.test_baseline_eligibility_and_offsets_unchanged',
}


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main():
    suite = unittest.TestSuite()
    excluded = []
    loader = unittest.TestLoader()
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        if path.stem in ARCHIVE_MODULES:
            # Count exclusions without importing a module requiring absent evidence.
            tree = ast.parse(path.read_text())
            for cls in tree.body:
                if isinstance(cls, ast.ClassDef):
                    excluded += [f'{path.stem}.{cls.name}.{node.name}' for node in cls.body
                                 if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
            continue
        for case in flatten(loader.loadTestsFromName(path.stem)):
            if case.id() in ARCHIVE_CASES:
                excluded.append(case.id())
            else:
                suite.addTest(case)
    print(f'Public suite: {suite.countTestCases()} tests; {len(excluded)} archive-dependent tests excluded.', flush=True)
    for name in excluded:
        print(f'  archive required: {name}', flush=True)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
