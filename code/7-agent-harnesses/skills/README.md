# Lab Skills Directory

Skills installed here are picked up by the lazy loader in `harness_lab.py`
(Exercise 2). Each skill is a folder containing a `SKILL.md` with `name` and
`description` frontmatter.

- **`code_review/` and `technical_writing/`** ship pre-installed (copies of the
  repo-root examples) so Exercise 2 has real skills to index and measure.
- **Exercise 3** asks you to author `dataset_profiler/SKILL.md` here yourself.
  A completed example lives in `.examples/dataset_profiler/` — try your own
  before peeking.
- **Exercise 4** installs the NVIDIA-verified `accelerated-computing-cudf`
  skill here via `scripts/install_nvidia_skill.sh`.
- **Exercise 5** has the agent write a new skill into this directory on its
  own.

Directories starting with `.` are ignored by the loader.
