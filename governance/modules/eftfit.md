# EFTFit project-governance delta

Applies to TOP-26-006 project work in `EFTFit`, the package/workspace/inference repository in the current CMSSW area, selected through [`../repositories.md`](../repositories.md). Root governance and applicable EFTFit-native/upstream policy both apply. This module creates no write or production permission.

lane_09 and the EFTFit native owner own the statistical model, inference, package/workspace contract, and repository-native EFTFit documentation. Those scientific and technical documents stay with their semantic owner; central project governance does not transfer their content to lane_15.

The default project posture is `read_only` until an explicit lane_09/EFTFit mutating round authorizes exact paths and effects. Use the generic root branch lifecycle unless live EFTFit-native policy adds constraints; do not encode historical HEADs, current branch names, or trees as permanent truth. `CombinedLimit` is an external upstream dependency, not a TOP26006_fw-owned implementation repository. Its own upstream policy and separately authorized scope govern any action there.
