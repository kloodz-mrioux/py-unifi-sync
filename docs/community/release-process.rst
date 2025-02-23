.. _release-process:

Release Process and Rules
=========================

This outlines a streamlined release process inspired by Gitflow, accommodating **major**, **minor**, and **hotfix** versions for efficient software delivery.

Branching Model
---------------

* **Main Branch**: Reflects production-ready code. Only updated via merges from ``release`` or ``hotfix`` branches.
* **Develop Branch**: Integration branch for ongoing development. Contains the latest features and fixes.
* **Feature Branches**: Short-lived, branched from ``develop`` for specific tasks (e.g., ``feature/new-login``).
* **Release Branches**: Branched from ``develop`` for final prep (e.g., ``release/1.2.0``).
* **Hotfix Branches**: Branched from ``main`` for urgent fixes (e.g., ``hotfix/1.0.1``).

Versioning
----------
* Use Semantic Versioning (``MAJOR.MINOR.PATCH``):
    * **Major (X.0.0)**: Significant changes, breaking compatibility.
    * **Minor (0.X.0)**: New features, backward-compatible.
    *  **Hotfix (0.0.X)**: Critical bug fixes, no new features.

Release Process
---------------

* **Major/Minor Releases**:
    * *Start*: Create a ``release/x.y.0`` branch from ``develop``.
    * *Prep*: Finalize code, update docs, run tests, and bump version.
    * *Finish*: Merge into ``main`` and ``develop``. Tag ``main`` with ``x.y.0`` (e.g., ``v1.2.0``). Deploy to production. Delete the release branch.

* **Hotfix Releases**:
    * *Start*: Create a ``hotfix/x.y.z`` branch from ``main``.
    * *Fix*: Address the bug, test thoroughly, increment PATCH version.
    * *Finish*: Merge into ``main`` and ``develop``. Tag ``main`` with ``x.y.z`` (e.g., ``v1.0.1``). Deploy immediately. Delete the hotfix branch.

Rules
-----

* **Commits**: Write clear, concise messages. Reference issue numbers where applicable.
* **Pull Requests (PRs)**:
    * Feature branches merge into ``develop`` via PRs with at least one review.
    * Release and hotfix branches require testing and approval before merging.
* **Testing**: Automated tests must pass on all branches. Manual QA is mandatory for releases.
* **Tagging**: Only tag ``main`` with version numbers after merging.
* **Hotfixes**: Limit scope to critical fixes. Avoid feature creep.
* **Conflicts**: Resolve merge conflicts in the source branch before merging.
* **Rollback**: If a release fails, revert ``main`` to the last stable tag and investigate.

Workflow Example
----------------

* **Minor Release (1.1.0)**:
    * Branch ``release/1.1.0`` from ``develop``.
    * Finalize features, test, merge to ``main`` and ``develop``, tag ``v1.1.0``.

* **Hotfix (1.1.1)**:
    * Branch ``hotfix/1.1.1`` from ``main``.
    * Fix bug, test, merge to ``main`` and ``develop``, tag ``v1.1.1``.

Tools
-----

* Use Git for version control.
* Automate builds and tests with CI/CD pipelines.
* Track tasks and versions in a project management tool.

This process ensures stability in ``main``, agility in ``develop``, and rapid response via hotfixes, aligning with Gitflow’s structured approach.
