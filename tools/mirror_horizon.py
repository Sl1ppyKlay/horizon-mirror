"""Archive upstream history and verified nightly assets; never execute upstream code."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

UPSTREAM = 'https://github.com/horizon-rust/horizon.git'
REPO = os.environ.get('GITHUB_REPOSITORY', 'Sl1ppyKlay/horizon-mirror')

def run(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()

def gh_json(*args):
    return json.loads(run('gh', *args))

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / 'source.git'
        run('git', 'init', '--bare', str(source))
        run('git', 'fetch', '--no-tags', UPSTREAM, '+refs/heads/main:refs/heads/horizon-upstream', '+refs/tags/nightly-source/*:refs/tags/nightly-source/*', cwd=source)
        upstream_sha = run('git', 'rev-parse', 'horizon-upstream', cwd=source)
        # Store the exact full history in a bundle, including original CI files.
        bundle = root / 'horizon-history.bundle'
        run('git', 'bundle', 'create', str(bundle), '--all', cwd=source)
        run('git', 'bundle', 'verify', str(bundle), cwd=source)
        # The browsable branch excludes executable CI. Never run upstream workflows.
        run('git', 'read-tree', 'horizon-upstream', cwd=source)
        workflows = run('git', 'ls-files', '.github/workflows', cwd=source).splitlines()
        if workflows:
            run('git', 'update-index', '--force-remove', '--', *workflows, cwd=source)
        tree = run('git', 'write-tree', cwd=source)
        remote = f'https://github.com/{REPO}.git'
        previous = run('git', 'ls-remote', remote, 'refs/heads/horizon-upstream').split()
        parents = []
        if previous:
            run('git', 'fetch', remote, 'refs/heads/horizon-upstream:refs/heads/previous', cwd=source)
            parents = ['-p', previous[0]]
        os.environ.update(GIT_AUTHOR_NAME='Horizon archive', GIT_AUTHOR_EMAIL='archive@users.noreply.github.com', GIT_COMMITTER_NAME='Horizon archive', GIT_COMMITTER_EMAIL='archive@users.noreply.github.com')
        if not previous or run('git', 'rev-parse', 'previous^{tree}', cwd=source) != tree:
            commit = run('git', 'commit-tree', tree, *parents, '-m', f'Archive upstream {upstream_sha} (original CI in history bundle)', cwd=source)
            run('git', 'push', remote, f'{commit}:refs/heads/horizon-upstream', cwd=source)
        release = gh_json('api', 'repos/horizon-rust/horizon/releases/tags/nightly')
        assets = root / 'assets'
        assets.mkdir()
        run('gh', 'release', 'download', 'nightly', '--repo', 'horizon-rust/horizon', '--dir', str(assets))
        bundle.replace(assets / 'horizon-history.bundle')
        sums = {}
        for line in (assets / 'SHA256SUMS').read_text().splitlines():
            sha, name = line.split(maxsplit=1)
            name = name.lstrip('*')
            if Path(name).name != name or len(sha) != 64:
                raise ValueError('Invalid checksum entry')
            sums[name] = sha.lower()
        for name, sha in sums.items():
            if digest(assets / name) != sha:
                raise ValueError(f'Checksum mismatch: {name}')
        for name in ('horizon-windows-x64.zip', 'horizon-macos-arm64.zip', 'horizon-source.tar.gz'):
            if name not in sums:
                raise ValueError(f'Missing required checksum: {name}')
        # A digest of the full checksum list distinguishes successive builds on the same day.
        tag = 'horizon-build-' + digest(assets / 'SHA256SUMS')[:24]
        releases = gh_json('api', '--paginate', f'repos/{REPO}/releases?per_page=100')
        existing = next((r for r in releases if r['tag_name'] == tag), None)
        if existing and not existing['draft']:
            expected = {p.name: p.stat().st_size for p in assets.iterdir() if p.name != 'horizon-history.bundle'}
            actual = {a['name']: a['size'] for a in existing['assets']}
            if any(actual.get(n) != size for n, size in expected.items()):
                raise ValueError('Published archive is incomplete; refusing to advertise it')
        else:
            if not existing:
                notes = root / 'notes.md'
                notes.write_text('Archived from https://github.com/horizon-rust/horizon/releases/tag/nightly\n\n' + release['body'], encoding='utf-8')
                run('gh', 'release', 'create', tag, '--repo', REPO, '--target', 'horizon-upstream', '--draft', '--title', tag, '--notes-file', str(notes))
            run('gh', 'release', 'upload', tag, '--repo', REPO, '--clobber', *map(str, assets.iterdir()))
            # Verify the stored bytes, not only the local downloads, before publication.
            verify = root / 'verify'
            verify.mkdir()
            run('gh', 'release', 'download', tag, '--repo', REPO, '--dir', str(verify))
            for path in assets.iterdir():
                if digest(path) != digest(verify / path.name):
                    raise ValueError(f'Uploaded checksum mismatch: {path.name}')
            run('gh', 'release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest')
        manifest = {'game': {'label': tag}}
        for platform, name in [('windows', 'horizon-windows-x64.zip'), ('macos-arm64', 'horizon-macos-arm64.zip')]:
            manifest['game'][platform] = {'url': f'https://github.com/{REPO}/releases/download/{tag}/{name}', 'sha256': sums[name]}
        checkout = root / 'updates'
        run('git', 'clone', '--depth=1', '--branch=main', f'https://github.com/{REPO}.git', str(checkout))
        run('git', 'config', 'user.name', 'Horizon archive', cwd=checkout)
        run('git', 'config', 'user.email', 'horizon-archive@users.noreply.github.com', cwd=checkout)
        target = checkout / 'manifest.json'
        content = json.dumps(manifest, indent=2) + '\n'
        if not target.exists() or target.read_text() != content:
            target.write_text(content, encoding='utf-8')
            run('git', 'add', 'manifest.json', cwd=checkout)
            run('git', 'commit', '-m', f'Archive {tag}', cwd=checkout)
            run('git', 'push', 'origin', 'main', cwd=checkout)
        print(f'Archive ready: https://github.com/{REPO}/releases/tag/{tag}')

if __name__ == '__main__':
    main()

