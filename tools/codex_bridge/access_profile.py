"""Installation/access facts only; no CPC parser, model policy or CLI admission."""
import hashlib
import importlib.util
import stat
from pathlib import Path

from repository_task import governance
from project_reader import local_git as git


class AccessInbox:
    access = True

    def __init__(self, profile_path, workspace):
        from project_reader import directory_identity
        import yaml
        self.root = Path(workspace).absolute()
        self.namespace = directory_identity(self.root)
        if Path(git(self.root, 'rev-parse', '--show-toplevel').decode().strip()) != self.root:
            raise ValueError('COORDINATION_GIT_ROOT_MISMATCH')
        self.master = git(self.root, 'rev-parse', 'refs/heads/master^{commit}').decode().strip()
        self.dependencies = {p: git(self.root, 'rev-parse', self.master + ':' + p).decode().strip()
                             for p in ('governance/repositories.md', 'config/local_profile.schema.yml')}
        self.profile_path = str(Path(profile_path).absolute())
        if not stat.S_ISREG(Path(self.profile_path).lstat().st_mode):
            raise ValueError('UNSAFE_PROFILE_ALIAS')
        self.profile_namespace = directory_identity(Path(self.profile_path).parent)
        self.profile_digest = hashlib.sha256(Path(self.profile_path).read_bytes()).hexdigest()
        # The shared maintained resolver is packaged with this producer, while
        # registry/schema policy is always read from current master.
        source = Path(__file__).with_name('resolve_local_profile.py')
        if not source.exists():
            source = Path(__file__).resolve().parents[1] / 'resolve_local_profile.py'
        spec = importlib.util.spec_from_file_location('access_profile_resolver', source)
        resolver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(resolver)
        schema = yaml.safe_load(git(self.root, 'show', self.master + ':config/local_profile.schema.yml'))
        self.profile = resolver.resolve(resolver.read_yaml(self.profile_path), schema,
                                        execution_ready=True, access_only=True)
        if (Path(self.profile['workspace_root']) != self.root or
                Path(self.profile['repositories']['TOP26006_fw']['path']) != self.root):
            raise ValueError('LOCAL_PROFILE_COORDINATION_IDENTITY_MISMATCH')
        self.check()

    def check(self):
        from project_reader import directory_identity
        if (directory_identity(self.root) != self.namespace or
                directory_identity(Path(self.profile_path).parent) != self.profile_namespace):
            raise ValueError('ACCESS_ROOT_CHANGED')
        if (not stat.S_ISREG(Path(self.profile_path).lstat().st_mode) or
                hashlib.sha256(Path(self.profile_path).read_bytes()).hexdigest() != self.profile_digest):
            raise ValueError('LOCAL_PROFILE_CHANGED')
        return governance(self.root, self.dependencies, reader=git)
