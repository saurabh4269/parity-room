# Team conventions (maintained by maya, PM)

1. Reports use UTC calendar days (config/settings.json: report_timezone = "UTC").
2. The package supports Python 3.9 and newer (pyproject.toml requires-python). Do not rely on newer-only APIs.
3. Paths in code must match the on-disk file name exactly, including letter case.
4. A branch is READY only when the verifier has confirmed every check green on BOTH environments (Mac and Linux).
5. Only a human (sam) approves a merge. After approval the implementer merges the branch into main and says so in the room.
6. When a test and a convention disagree, the convention wins. Say which expectation you changed and why.
