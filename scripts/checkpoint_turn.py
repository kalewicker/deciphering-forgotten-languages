"""Commit public work, checkpoint local evidence, then push only main.

Run after the turn's appropriate tests and evidence checks. Never merges or
pushes the evidence branch. No checkout or worktree deletion is performed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'local-evidence-2026-10-18'
PUBLIC_ROOTS = {'.gitignore', 'AGENTS.md', 'README.md', 'PLAN_REVIEW.md', 'PUBLICATION.md',
                'pyproject.toml', 'uv.lock', 'src', 'scripts', 'tests', 'experiments', 'reports', 'benchmarks'}
SECRET = re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{32,}|AKIA[0-9A-Z]{16}')


def git(*args, env=None, data=None):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT, env=env, input=data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', required=True)
    args = parser.parse_args()
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert git('remote', 'get-url', 'origin').decode().strip() in {
        'https://github.com/kalewicker/deciphering-forgotten-languages.git',
        'git@github.com:kalewicker/deciphering-forgotten-languages.git'}
    previous = git('rev-parse', ARCHIVE).decode().strip()
    env = os.environ.copy()
    env['GIT_INDEX_FILE'] = str(ROOT / '.git/local-evidence.index')
    # Reuse its stat cache rather than rehashing the multi-gigabyte archive.
    if not Path(env['GIT_INDEX_FILE']).exists():
        git('read-tree', previous, env=env)
    assert git('write-tree', env=env).strip() == git('rev-parse', previous + '^{tree}').strip(), 'Archive index differs: inspect before retrying'
    git('add', '-A')
    staged = [p.decode() for p in git('diff', '--cached', '--name-only', '-z').split(b'\0') if p]
    for name in staged:
        assert Path(name).parts[0] in PUBLIC_ROOTS, name
        assert not name.startswith(('data/', 'runs/', 'benchmarks/inputs/')), name
        if (ROOT / name).exists():
            assert not (ROOT / name).is_symlink(), name
            raw = git('show', ':' + name)
            assert len(raw) < 10 * 1024 * 1024 and not SECRET.search(raw), name
    if staged:
        git('commit', '-m', args.message)
    public = git('rev-parse', 'HEAD').decode().strip()
    git('add', '-A', env=env)
    git('add', '--force', '--', 'data', 'runs', 'benchmarks',
        ':(exclude,glob)**/.DS_Store', ':(exclude,glob)**/__pycache__/**', ':(exclude,glob)**/*.pyc', env=env)
    tree = git('write-tree', env=env).decode().strip()
    archive = previous
    if tree != git('rev-parse', previous + '^{tree}').decode().strip():
        archive = git('commit-tree', tree, '-p', previous, '-p', public,
                      data=(args.message + '\nLocal evidence checkpoint; do not push this branch.\n').encode()).decode().strip()
        git('update-ref', 'refs/heads/' + ARCHIVE, archive, previous)
    # Refresh inherited stat-only entries before comparing index and worktree.
    git('update-index', '--refresh', env=env)
    git('diff-files', '--quiet', env=env)
    assert not git('status', '--porcelain').strip()
    subprocess.run(['gh', 'auth', 'status'], cwd=ROOT, check=True)
    git('push', '--set-upstream', 'origin', 'main')
    remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
    assert remote == public == git('rev-parse', 'origin/main').decode().strip()
    assert not git('status', '--porcelain').strip()
    print(json.dumps({'public_commit': public, 'local_evidence_commit': archive,
                      'remote_main_matches': True, 'worktree_clean': True}, indent=2), flush=True)


if __name__ == '__main__':
    main()
