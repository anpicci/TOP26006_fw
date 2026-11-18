# EFTFit project-governance delta

Applies to TOP-26-006 project work in `EFTFit`, the package/workspace/inference repository in the current CMSSW area, selected through [`../repositories.md`](../repositories.md). Root governance and applicable EFTFit-native/upstream policy both apply. This module creates no write or production permission.

Statistical-model and inference semantics, the package/workspace contract, and repository-native EFTFit technical documentation remain with the applicable repository/domain semantic authority, outside TOP26006_fw repository-governance ownership. Current task ownership is resolved by the external TOP-26-006 control plane, not serialized here.

The default project posture is `read_only` until an exact mutating round authorizes EFTFit paths and effects. Use the generic root branch lifecycle unless live EFTFit-native policy adds constraints; do not encode historical HEADs, current branch names, or trees as permanent truth. `CombinedLimit` is an external upstream dependency, not a TOP26006_fw-owned implementation repository. Its own upstream policy and separately authorized scope govern any action there.
