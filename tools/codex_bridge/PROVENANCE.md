# Source adoption

The owner-authorized initial source is the untracked local R6 package
`/users/apiccine/work/correction-lib/glados_codex_bridge_r6`, not an installed
upstream release or a governance authority. This round adopts only bridge.py,
repository_task.py, test_bridge.py, test_repository_task.py, test_inbox.py,
package.json and package-lock.json from that package. Their local modifications
are reviewable in this maintained source and its implementation commit.

server.mjs was copied from the read-only deployed R6 server at
`/users/apiccine/.local/opt/glados-codex-bridge-r6/server.mjs`. Static byte
comparison established that its only difference from packaged server.mjs was
`timeout: 30000` becoming `timeout: 120000`. The 120-second value is retained.

| Source identity | SHA-256 |
| --- | --- |
| packaged server.mjs | 4842773c77b79f7d43eb3863cc62ba568266f3392752d5a2a6f7053acd8d0a79 |
| deployed server.mjs | f6ea4f087711ea3682fd649b34f3017730ad693ff87ff7934eb5176dacca1d81 |
| packaged bridge.py | d562d3a38b64b69cd2f14ad5d200acc51fec3fe83a12ef2e0f9c52dbf594638f |
| packaged repository_task.py | f59dce02865b55466849397ee27a6a8a70d3359d1d94f528480adead0872604f |

The new governed adapter, evidence/artifact adapter, tests, local entry point and
documentation are maintained here. R6's installer, tunnel credentials/identity,
fixed intake prompt, release binding, preparation evidence and generated test
results are not adopted as runtime authority. Existing state and installations
remain in place. Node dependencies are pinned by the adopted lockfile and are
not vendored or installed by this round. The wrapper remains site-owned protected
infrastructure and is selected through the maintained local-profile contract.
