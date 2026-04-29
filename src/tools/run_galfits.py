
import os
import re
import shlex
import subprocess
from datetime import datetime
from glob import glob
from typing import Any, Annotated
import shutil
import importlib.util


def _write_fitting_log(
    config_file: str,
    workplace_dir: str,
    cmd: list[str],
    summary_stats: dict[str, Any],
    summary_files: list[str],
    imagefit_pngs: list[str],
    sedmodel_pngs: list[str],
    constrain_files: list[str],
    params_files: list[str],
    read_summary: str | None = None,
    prior_file: str | None = None,
) -> str:
    """Append a round record to fitting_log.md in the galaxy directory.

    Returns the path to the log file.
    """
    # Galaxy root: derive from workplace_dir (output/timestamp_basename)
    # This works regardless of where the config file is located (e.g. /tmp/)
    workplace_parent = os.path.dirname(os.path.abspath(workplace_dir))
    if os.path.basename(workplace_parent) == "output":
        galaxy_dir = os.path.dirname(workplace_parent)
    else:
        # Fallback: try config file location
        galaxy_dir = os.path.dirname(os.path.abspath(config_file))
    log_path = os.path.join(galaxy_dir, "fitting_log.md")

    # Count existing rounds to determine round number
    round_num = 1
    if os.path.exists(log_path):
        with open(log_path) as f:
            round_num = f.read().count("### Round") + 1

    # Build command string
    cmd_parts = []
    for p in cmd:
        if " " in p and not p.startswith("-"):
            cmd_parts.append(f'"{p}"')
        else:
            cmd_parts.append(p)
    cmd_str = " ".join(cmd_parts)

    # Relative paths for readability
    def rel(p: str) -> str:
        try:
            return os.path.relpath(p, config_dir)
        except ValueError:
            return p

    # Extract key spatial parameters
    params = summary_stats.get("parameters", {})
    spatial_lines = []
    # Group parameters by component (disk_xcen, bulge_Re, ring_r0, etc.)
    components = set()
    for k in params:
        m = re.match(r"(\w+)_(?:xcen|ycen|Re|n|ang|axrat|r0|sig)", k)
        if m:
            components.add(m.group(1))
    for comp in sorted(components):
        xcen = params.get(f"{comp}_xcen")
        ycen = params.get(f"{comp}_ycen")
        ang = params.get(f"{comp}_ang")
        axrat = params.get(f"{comp}_axrat")
        if xcen is None:
            continue

        # Sersic components have Re and n; GauRing has r0 and sig
        re_val = params.get(f"{comp}_Re")
        n_val = params.get(f"{comp}_n")
        r0_val = params.get(f"{comp}_r0")
        sig_val = params.get(f"{comp}_sig")

        if re_val is not None:
            spatial_lines.append(
                f"    - {comp}: x={xcen:.4f}, y={ycen:.4f}, Re={re_val:.4f}, "
                f"n={n_val:.4f}, PA={ang:.2f}, q={axrat:.4f}"
            )
        elif r0_val is not None:
            spatial_lines.append(
                f"    - {comp}: x={xcen:.4f}, y={ycen:.4f}, r0={r0_val:.4f}, "
                f"sig={sig_val:.4f}, PA={ang:.2f}, q={axrat:.4f}"
            )

    # Per-band chi-squared
    per_band = summary_stats.get("per_band_chisq", {})
    chisq_lines = []
    for band, val in sorted(per_band.items()):
        chisq_lines.append(f"    - {band}: {val}")

    # Build output file list
    output_names = []
    for f in summary_files + imagefit_pngs + sedmodel_pngs + constrain_files + params_files:
        output_names.append(f"- {rel(f)}")

    # Get timestamp from workplace dir name
    ts_match = re.search(r"(\d{8}_\d{6})", workplace_dir)
    timestamp_str = ts_match.group(1) if ts_match else datetime.now().strftime("%Y%m%d_%H%M%S")

    record = f"""### Round {round_num}
**Timestamp:** {timestamp_str}

**1. Config file**
- {rel(config_file)}

**2. Command**
```bash
{cmd_str}
```

**3. Output files**
{chr(10).join(output_names) if output_names else "- (none)"}

**4. Fitting statistics**
- Global reduced chisq: {summary_stats.get("reduced_chisq", "N/A")}
- BIC: {summary_stats.get("bic", "N/A")}
{chr(10).join(chisq_lines) if chisq_lines else "- (per-band chisq not available)"}

**5. Fitted spatial parameters**
{chr(10).join(spatial_lines) if spatial_lines else "- (none)"}

**6. VLM Analysis** *(filled after running analyze tool)*

- Overall Judgement: *(pending)*

- Fitting problems:
  - *(pending)*

- Next-Step Decision: *(pending)*

- Reasons: *(pending)*


"""

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(record)

    return log_path


def _build_galfits_command(config_file: str, workplace: str, saveimgs: bool) -> list[str]:
    """Build a robust command to run GalfitS.

    We avoid relying on shell aliases (common for GalfitS installs) by preferring:
    1) GALFITS_BIN (can be an executable, a .py file, or a full command string)
    2) python -m galfits.galfitS (if module is importable)
    3) fallback to `galfits` executable on PATH
    """

    galfits_bin = os.getenv("GALFITS_BIN")
    if galfits_bin:
        # Allow specifying a full command string, e.g. "python /path/to/galfitS.py"
        parts = shlex.split(galfits_bin)
        if len(parts) == 1 and parts[0].endswith(".py"):
            python_exec = os.getenv("GALFITS_PYTHON", os.getenv("PYTHON", "python3"))
            cmd = [python_exec, parts[0]]
        else:
            cmd = parts

        cmd += ["--config", config_file, "--workplace", workplace]
        if saveimgs:
            cmd.append("--saveimgs")
        return cmd

    # If GalfitS is installed as a Python package, this is the most reliable.
    # Guard against import-time failures (e.g. missing jax) during probing.
    try:
        module_ok = importlib.util.find_spec("galfits.galfitS") is not None
    except Exception:
        module_ok = False

    if module_ok:
        cmd = [os.getenv("GALFITS_PYTHON", os.getenv("PYTHON", "python3")), "-m", "galfits.galfitS"]
        cmd += ["--config", config_file, "--workplace", workplace]
        if saveimgs:
            cmd.append("--saveimgs")
        return cmd

    cmd = ["galfits", "--config", config_file, "--workplace", workplace]
    if saveimgs:
        cmd.append("--saveimgs")
    return cmd


def _parse_gssummary(summary_path: str) -> dict[str, Any]:
    """Parse a .gssummary file and extract key statistics.

    Returns a dict with reduced_chisq, bic, per_band_chisq, and parameter values.
    """
    if not summary_path or not os.path.exists(summary_path):
        return {}

    with open(summary_path) as f:
        content = f.read()

    result: dict[str, Any] = {
        "reduced_chisq": None,
        "bic": None,
        "per_band_chisq": {},
        "parameters": {},
    }

    # Global reduced chi-squared
    m = re.search(r"reduced\s+chi.*?[:\s]+([\d.]+)", content, re.IGNORECASE)
    if m:
        result["reduced_chisq"] = float(m.group(1))

    # BIC
    m = re.search(r"BIC\s*[:\s]+([\d.eE+-]+)", content, re.IGNORECASE)
    if m:
        result["bic"] = float(m.group(1))

    # Per-band chi-squared (look for patterns like "band_xxx chisq: 1.23" or in tables)
    for m in re.finditer(r"(band\s*\w+|f\d+w)\s*.*?(?:reduced\s+)?chi.*?[:\s]+([\d.]+)", content, re.IGNORECASE):
        band_name = m.group(1).strip()
        result["per_band_chisq"][band_name] = float(m.group(2))

    # Free parameters (tab-separated name-value lines)
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) == 2:
            name, value = parts
            try:
                result["parameters"][name] = float(value)
            except ValueError:
                pass

    return result


async def run_galfits(
    config_file: Annotated[str, "the path to the GalfitS (.lyric) configuration file"],
    timeout_sec: Annotated[int, "timeout in seconds"] = 3600,
    extra_args: Annotated[list[str] | None, "extra GalfitS CLI args (e.g. ['--fit_method','optimizer','--num_steps','200'])"] = None,
    read_summary: Annotated[str | None, "path to previous .gssummary to carry forward best-fit parameters"] = None,
    prior_file: Annotated[str | None, "path to .prior file for mass/size constraints"] = None,
) -> dict[str, Any]:
    """Execute GalfitS (multi-band) with the given config file.

    Runs GalfitS as a subprocess and returns discovered artifacts (summary + PNGs) and logs.
    """

    if not config_file or not os.path.exists(config_file):
        return {"status": "failure", "error": f"Config file not found: {config_file}"}

    # Validate optional inputs
    if read_summary and not os.path.exists(read_summary):
        return {"status": "failure", "error": f"Summary file not found: {read_summary}"}
    if prior_file and not os.path.exists(prior_file):
        return {"status": "failure", "error": f"Prior file not found: {prior_file}"}

    # Find galaxy root: if config is inside output/, walk up past it
    config_dir = os.path.dirname(os.path.abspath(config_file))
    parts = config_dir.split(os.sep)
    if "output" in parts:
        config_dir = os.sep.join(parts[:parts.index("output")])
    config_basename = os.path.splitext(os.path.basename(config_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(os.path.join(config_dir, "output"), exist_ok=True)
    workplace_dir = os.path.join(config_dir, "output", f"{timestamp}_{config_basename}")
    os.makedirs(workplace_dir, exist_ok=True)
    shutil.copy(config_file, workplace_dir)

    cmd = _build_galfits_command(config_file=config_file, workplace=workplace_dir, saveimgs=True)

    # Add --readsummary to carry forward previous round parameters
    if read_summary:
        cmd.extend(["--readsummary", os.path.abspath(read_summary)])

    # Add --prior for mass/size constraints
    if prior_file:
        cmd.extend(["--prior", os.path.abspath(prior_file)])

    if extra_args:
        cmd.extend([str(x) for x in extra_args])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_sec,
            cwd=config_dir,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "failure",
            "error": f"GalfitS execution timed out after {timeout_sec} seconds",
        }
    except FileNotFoundError:
        return {
            "status": "failure",
            "error": "GalfitS executable not found. Set GALFITS_BIN (or install GalfitS as a Python package).",
            "command": cmd,
        }

    log = (proc.stdout or "") + (proc.stderr or "")

    # Save log to workplace (both success and failure)
    log_path = os.path.join(workplace_dir, "run.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log)

    if proc.returncode != 0:
        return {
            "status": "failure",
            "error": f"GalfitS failed with return code {proc.returncode}",
            "workplace": workplace_dir,
            "command": cmd,
            "log": log,
            "log_path": log_path,
        }

    # Discover common outputs
    summary_files = sorted(glob(os.path.join(workplace_dir, "*.gssummary")))

    # GalfitS output filenames vary between versions; support common patterns.
    imagefit_pngs = sorted(
        set(
            glob(os.path.join(workplace_dir, "*.imagefit.png"))
            + glob(os.path.join(workplace_dir, "*image_fit.png"))
            + glob(os.path.join(workplace_dir, "*imagefit*.png"))
        )
    )
    sedmodel_pngs = sorted(
        set(
            glob(os.path.join(workplace_dir, "*.sedmodel.png"))
            + glob(os.path.join(workplace_dir, "*SED_model.png"))
            + glob(os.path.join(workplace_dir, "*sed*model*.png"))
        )
    )

    result_fits = sorted(set(glob(os.path.join(workplace_dir, "*_result.fits"))))

    # Additional output files from GalfitS
    constrain_files = sorted(glob(os.path.join(workplace_dir, "*.constrain")))
    params_files = sorted(glob(os.path.join(workplace_dir, "*.params")))

    # Parse gssummary for structured statistics
    summary_stats = _parse_gssummary(summary_files[0]) if summary_files else {}

    # Write fitting log
    fitting_log_path = ""
    try:
        fitting_log_path = _write_fitting_log(
            config_file=config_file,
            workplace_dir=workplace_dir,
            cmd=cmd,
            summary_stats=summary_stats,
            summary_files=summary_files,
            imagefit_pngs=imagefit_pngs,
            sedmodel_pngs=sedmodel_pngs,
            constrain_files=constrain_files,
            params_files=params_files,
            read_summary=read_summary,
            prior_file=prior_file,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Warning: Failed to write fitting log: {e}")

    return {
        "status": "success",
        "message": f"GalfitS completed successfully for {config_file}. Output files:\n"
        f"- summary_files : .gssummary files contain fitting parameters, χ² statistics, and model components for all bands\n"
        f"- imagefit_pngs : PNG visualizations showing observed data, model fits, and residuals for all image bands\n"
        f"- sedmodel_pngs : PNG plots of Spectral Energy Distribution (SED) models showing multi-band flux fitting across wavelengths\n"
        f"- result_fits : FITS files containing the best-fit model results\n"
        f"- constrain_files : Constraint files used during fitting\n"
        f"- params_files : Parameter files with initial and fitted values",
        "workplace": workplace_dir,
        "summary_files": summary_files,
        "imagefit_pngs": imagefit_pngs,
        "sedmodel_pngs": sedmodel_pngs,
        "result_fits": result_fits,
        "constrain_files": constrain_files,
        "params_files": params_files,
        "log_path": log_path,
        "fitting_log": fitting_log_path,
        "reduced_chisq": summary_stats.get("reduced_chisq"),
        "bic": summary_stats.get("bic"),
        "per_band_chisq": summary_stats.get("per_band_chisq", {}),
        "parameters": summary_stats.get("parameters", {}),
    }
