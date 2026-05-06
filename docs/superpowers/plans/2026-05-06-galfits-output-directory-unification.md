# GalfitS Output Directory Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify GalfitS workflow output directory handling so workflow-created timestamped directories are the only supported format and `run_galfits.py` reuses them without creating duplicate output trees.

**Architecture:** Keep directory ownership in the workflow prompt, which creates `YYYYMMDD_HHMMSS_<basename>` or `YYYYMMDD_HHMMSS_<basename>_iterN` directories before writing `.lyric` files. Update `run_galfits.py` to validate and reuse only those directories when configs are already under `output/`, fail fast for invalid legacy names, and preserve standalone auto-create behavior for configs outside `output/`.

**Tech Stack:** Python 3.10+, pytest, markdown prompt specifications, standard library (`pathlib`, `re`, `shutil`, `datetime`).

---

## File Structure

- Modify: `src/tools/run_galfits.py`
  - Add a small helper for strict workflow directory validation.
  - Update workplace selection logic in `run_galfits()`.
- Modify: `src/prompts/workflow_galfits.md`
  - Remove contradictory instructions about writing iter configs in the galaxy main directory.
  - Make all workflow examples and rules use only timestamp-based output directories.
- Create: `tests/test_run_galfits.py`
  - Add focused tests for directory reuse, invalid legacy directory rejection, and standalone auto-create behavior.
- Create: `docs/superpowers/plans/2026-05-06-galfits-output-directory-unification.md`
  - This implementation plan.

### Task 1: Add failing tests for directory selection behavior

**Files:**
- Modify: `tests/test_run_galfits.py`
- Test: `tests/test_run_galfits.py`

- [ ] **Step 1: Write the failing test for valid workflow directory reuse**

```python
import asyncio
from pathlib import Path
from unittest.mock import patch

from tools.run_galfits import run_galfits


def test_run_galfits_reuses_valid_timestamp_workflow_directory(tmp_path):
    galaxy_dir = tmp_path / "obj6414"
    workplace_dir = galaxy_dir / "output" / "20260429_170957_obj6414_s1_iter2"
    workplace_dir.mkdir(parents=True)
    config_file = workplace_dir / "obj6414_s1_iter2.lyric"
    config_file.write_text("R1) obj6414\n")

    def fake_run(cmd, capture_output, text, check, timeout, cwd):
        assert cwd == str(galaxy_dir)
        assert "--workplace" in cmd
        workplace = Path(cmd[cmd.index("--workplace") + 1])
        assert workplace == workplace_dir
        (workplace / "result.gssummary").write_text("BIC 123\n")
        return type("Proc", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    with patch("tools.run_galfits.subprocess.run", side_effect=fake_run):
        result = asyncio.run(run_galfits(str(config_file)))

    assert result["status"] == "success"
    assert Path(result["workplace"]) == workplace_dir
    assert (workplace_dir / "run.log").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_run_galfits.py::test_run_galfits_reuses_valid_timestamp_workflow_directory -v`
Expected: FAIL because current code may not create enough output for a clean success path yet, or because the helper/validation logic does not exist.

- [ ] **Step 3: Write the failing test for rejecting invalid legacy workflow directories**

```python
def test_run_galfits_rejects_legacy_round_directory_under_output(tmp_path):
    galaxy_dir = tmp_path / "obj6414"
    legacy_dir = galaxy_dir / "output" / "20260429_round2_obj6414_s1_iter2"
    legacy_dir.mkdir(parents=True)
    config_file = legacy_dir / "obj6414_s1_iter2.lyric"
    config_file.write_text("R1) obj6414\n")

    result = asyncio.run(run_galfits(str(config_file)))

    assert result["status"] == "failure"
    assert "20260429_round2_obj6414_s1_iter2" in result["error"]
    assert "YYYYMMDD_HHMMSS_<basename>" in result["error"]
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_run_galfits.py::test_run_galfits_rejects_legacy_round_directory_under_output -v`
Expected: FAIL because current code silently creates a new timestamped directory instead of rejecting the legacy one.

- [ ] **Step 5: Write the failing test for standalone config auto-create behavior**

```python
def test_run_galfits_creates_timestamped_output_for_standalone_config(tmp_path):
    galaxy_dir = tmp_path / "obj6414"
    galaxy_dir.mkdir()
    config_file = galaxy_dir / "obj6414_s1.lyric"
    config_file.write_text("R1) obj6414\n")

    def fake_run(cmd, capture_output, text, check, timeout, cwd):
        assert cwd == str(galaxy_dir)
        workplace = Path(cmd[cmd.index("--workplace") + 1])
        assert workplace.parent == galaxy_dir / "output"
        assert workplace.name.startswith("20")
        assert (workplace / "obj6414_s1.lyric").exists()
        (workplace / "result.gssummary").write_text("BIC 123\n")
        return type("Proc", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    with patch("tools.run_galfits.subprocess.run", side_effect=fake_run):
        result = asyncio.run(run_galfits(str(config_file)))

    assert result["status"] == "success"
    assert Path(result["workplace"]).parent == galaxy_dir / "output"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_run_galfits.py::test_run_galfits_creates_timestamped_output_for_standalone_config -v`
Expected: FAIL if the mocked expectations do not yet match the current structure exactly; the test establishes the intended contract before implementation changes.

- [ ] **Step 7: Commit**

```bash
git add tests/test_run_galfits.py
git commit -m "test: add galfits output directory cases"
```

### Task 2: Implement strict directory validation in `run_galfits.py`

**Files:**
- Modify: `src/tools/run_galfits.py`
- Test: `tests/test_run_galfits.py`

- [ ] **Step 1: Write the minimal helper for timestamp workflow directory validation**

```python
WORKFLOW_OUTPUT_DIR_RE = re.compile(r"^\d{8}_\d{6}_.+")


def _is_valid_workflow_output_dir(dirname: str) -> bool:
    return bool(WORKFLOW_OUTPUT_DIR_RE.match(dirname))
```

Place it near the top of `src/tools/run_galfits.py` after imports.

- [ ] **Step 2: Replace workplace detection logic with strict three-case behavior**

```python
    config_dir = os.path.dirname(os.path.abspath(config_file))
    config_basename = os.path.splitext(os.path.basename(config_file))[0]
    parts = config_dir.split(os.sep)

    if "output" in parts:
        idx = parts.index("output")
        galaxy_dir = os.sep.join(parts[:idx])
        subdir = os.path.basename(config_dir)
        if _is_valid_workflow_output_dir(subdir):
            workplace_dir = config_dir
            os.makedirs(workplace_dir, exist_ok=True)
            work_cwd = galaxy_dir
        else:
            return {
                "status": "failure",
                "error": (
                    f"Invalid workflow output directory name: {subdir}. "
                    "Expected YYYYMMDD_HHMMSS_<basename> or "
                    "YYYYMMDD_HHMMSS_<basename>_iterN. "
                    "Legacy roundN naming is not supported."
                ),
            }
    else:
        galaxy_dir = config_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workplace_dir = os.path.join(galaxy_dir, "output", f"{timestamp}_{config_basename}")
        os.makedirs(workplace_dir, exist_ok=True)
        shutil.copy(config_file, workplace_dir)
        work_cwd = galaxy_dir
```

This removes the old `reuse_workplace` flag and the silent fallback path for invalid `output/*` directory names.

- [ ] **Step 3: Run focused tests to verify the implementation passes**

Run: `pytest tests/test_run_galfits.py::test_run_galfits_reuses_valid_timestamp_workflow_directory tests/test_run_galfits.py::test_run_galfits_rejects_legacy_round_directory_under_output tests/test_run_galfits.py::test_run_galfits_creates_timestamped_output_for_standalone_config -v`
Expected: PASS for all three tests.

- [ ] **Step 4: Run the full `test_run_galfit.py` file to catch regressions**

Run: `pytest tests/test_run_galfit.py tests/test_run_galfits.py -v`
Expected: PASS, or skips only for tests that depend on unavailable external real data/executables.

- [ ] **Step 5: Commit**

```bash
git add src/tools/run_galfits.py tests/test_run_galfits.py
git commit -m "fix: enforce galfits output directory contract"
```

### Task 3: Align workflow prompt text with the strict directory contract

**Files:**
- Modify: `src/prompts/workflow_galfits.md`
- Test: `src/prompts/workflow_galfits.md`

- [ ] **Step 1: Write the failing text expectations as a checklist before editing**

```text
Expected prompt rules after edit:
- Config File Isolation examples use only YYYYMMDD_HHMMSS_<basename> and YYYYMMDD_HHMMSS_<basename>_iterN
- No remaining instruction says to write iter configs in the galaxy main directory
- No remaining operational instruction references round1/round2 naming
```

This is a prompt-content contract rather than executable pytest coverage.

- [ ] **Step 2: Edit the contradictory prompt lines**

Replace the contradictory instruction near `src/prompts/workflow_galfits.md:269` with text equivalent to:

```md
3. **NEVER modify the original .lyric file** - write the new config into a pre-created timestamped output directory using `YYYYMMDD_HHMMSS_<basename>` for round 1 or `YYYYMMDD_HHMMSS_<basename>_iterN` for later rounds
```

Also update the later operational instruction near `src/prompts/workflow_galfits.md:391` to text equivalent to:

```md
* 如需添加/修改成分，遵循 Component Parameter Inheritance 规则，使用 `/skill galfits-manual` 获取正确的参数格式，写入新的 `output/{timestamp}_{basename}_iter{n}/{basename}_iter{n}.lyric` 文件。
```

- [ ] **Step 3: Verify the prompt text no longer contains contradictory legacy wording**

Run: `python - <<'PY'
from pathlib import Path
text = Path('src/prompts/workflow_galfits.md').read_text()
assert 'write new config in the galaxy\'s main directory' not in text
assert 'YYYYMMDD_HHMMSS_<basename>' in text
assert 'YYYYMMDD_HHMMSS_<basename>_iterN' in text
print('prompt contract ok')
PY`
Expected: `prompt contract ok`

- [ ] **Step 4: Commit**

```bash
git add src/prompts/workflow_galfits.md
git commit -m "docs: align galfits workflow directory rules"
```

### Task 4: Run final verification across code and prompt behavior

**Files:**
- Modify: none
- Test: `tests/test_run_galfits.py`, `src/prompts/workflow_galfits.md`

- [ ] **Step 1: Run the targeted test file cleanly**

Run: `pytest tests/test_run_galfits.py -v`
Expected: PASS for the new directory contract tests.

- [ ] **Step 2: Re-run the prompt contract check**

Run: `python - <<'PY'
from pathlib import Path
import re
text = Path('src/prompts/workflow_galfits.md').read_text()
assert 'round1_obj' not in text
assert 'round2_obj' not in text
assert re.search(r'YYYYMMDD_HHMMSS_<basename>', text)
assert re.search(r'YYYYMMDD_HHMMSS_<basename>_iterN', text)
print('prompt naming verified')
PY`
Expected: `prompt naming verified`

- [ ] **Step 3: Inspect the working tree to confirm only intended files changed**

Run: `git status --short`
Expected: only `src/tools/run_galfits.py`, `src/prompts/workflow_galfits.md`, `tests/test_run_galfits.py`, and plan/spec docs should appear for this task.

- [ ] **Step 4: Commit**

```bash
git add src/tools/run_galfits.py src/prompts/workflow_galfits.md tests/test_run_galfits.py
git commit -m "fix: unify galfits workflow output directories"
```
