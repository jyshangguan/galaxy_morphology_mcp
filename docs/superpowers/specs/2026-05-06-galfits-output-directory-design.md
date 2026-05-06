# GalfitS workflow output directory unification design

## Background

The current `workflow_galfits` flow and `run_galfits.py` both participate in output directory management, but they use different naming rules.

Observed behavior in `2026/GALFITS_examples/zhongyi9/6414/output/` showed two parallel directory families for a single run:

- workflow-created directories like `20260429_round1_obj6414_s1` and `20260429_round2_obj6414_s1_iter2`
- tool-created directories like `20260429_170251_obj6414_s1` and `20260429_170957_obj6414_s1_iter2`

This causes empty placeholder directories, partially populated directories containing only `.lyric`, and a second set of directories containing the real fitting results.

## Goal

Unify the output directory contract so that:

1. `workflow_galfits` creates the round directory first.
2. The config file for that round is written into that directory.
3. `run_galfits.py` reuses that exact directory.
4. Only one naming format is accepted.
5. Old `round1` / `round2` naming is no longer supported.

## Non-goals

- Do not migrate or rewrite historical output directories.
- Do not add compatibility logic for legacy `YYYYMMDD_roundN_*` directories.
- Do not change fitting result file naming produced by GalfitS itself.

## Required naming format

The only valid workflow output directory format is:

- Round 1: `YYYYMMDD_HHMMSS_<basename>`
- Round 2+: `YYYYMMDD_HHMMSS_<basename>_iterN`

Examples:

- `20260429_170251_obj6414_s1`
- `20260429_170957_obj6414_s1_iter2`

Where:

- `YYYYMMDD_HHMMSS` is a timestamp with second precision
- `<basename>` is the config filename stem without `.lyric`
- `iterN` is present only for iteration rounds after round 1

## Behavioral design

### 1. workflow_galfits prompt behavior

The workflow prompt must explicitly instruct the agent to:

1. create a new output directory using the strict timestamp-based format
2. write the round config file into that directory
3. pass that config path to `run_galfits`

The prompt must not mention legacy `round1` / `round2` directory naming anywhere.

### 2. run_galfits.py reuse behavior

`run_galfits.py` should apply the following rules:

#### Case A: config file is inside `output/<valid_timestamp_dir>/`
- Reuse the config directory as `workplace_dir`
- Do not create a second output directory
- Do not copy the config elsewhere

#### Case B: config file is inside `output/<invalid_dir>/`
- Return failure immediately
- Explain that the directory name does not match the required timestamp-based format
- Do not create a fallback output directory

#### Case C: config file is outside `output/`
- Keep the existing standalone behavior
- Create a new timestamped output directory automatically
- Copy the config there and run as before

This keeps the tool independently usable while enforcing strict workflow hygiene when the workflow has already chosen an output location.

## Validation rules

A valid reusable workflow directory must satisfy both:

1. the config file lives directly under an `output/<subdir>/` path
2. `<subdir>` matches the strict regex pattern for timestamp-based names

Recommended matching rule:

- `^\d{8}_\d{6}_.+`

This is sufficient because:

- it enforces the timestamp prefix
- it allows both first-round and `_iterN` basenames
- it rejects legacy `YYYYMMDD_roundN_*` names

## Error handling

If the config is under `output/` but the directory name is invalid, the tool should fail with a message that clearly states:

- the offending directory name
- the accepted naming pattern
- that legacy `roundN` naming is unsupported

This is intentional fail-fast behavior so that workflow mistakes surface immediately instead of silently producing duplicated output trees.

## Files to change

### `src/prompts/workflow_galfits.md`
Update the documentation and operational instructions so that all examples and rules use only:

- `YYYYMMDD_HHMMSS_<basename>`
- `YYYYMMDD_HHMMSS_<basename>_iterN`

Remove any remaining references to:

- `round1`
- `round2`
- `YYYYMMDD_roundN_*`

### `src/tools/run_galfits.py`
Update workplace detection logic so that:

- configs inside valid timestamp-based workflow directories are reused
- configs inside invalid `output/*` directories fail immediately
- configs outside `output/` still get an auto-created timestamped directory

## Expected outcome

After this change:

- each fitting round has exactly one output directory
- the round config and all GalfitS outputs live in the same directory
- workflow-created placeholder directories are no longer left behind
- duplicated directory trees from a single logical run no longer appear

## Testing strategy

### Prompt-level verification

Check that `workflow_galfits.md` examples and instructions consistently use the new timestamp format and no longer mention legacy round-based naming.

### Tool-level verification

Verify these behaviors:

1. valid workflow directory is reused
2. invalid `output/*` directory is rejected
3. config outside `output/` still creates a fresh timestamped directory

### Regression focus

The key regression to prevent is:

- config written under one output subdirectory, but results emitted into a second automatically created subdirectory

## Trade-off decision

This design intentionally prefers strictness over backward compatibility.

Reason:

- the user explicitly requested no legacy compatibility
- strict failure is easier to debug than silent fallback
- directory structure is part of the workflow contract and should be deterministic
