
要求自主完成多波段星系 Image Fitting 阶段的多轮拟合。
以下所有规则必须严格遵循，不再引用任何外部文件。

## Core Principles

1. **ALWAYS read files first** before making recommendations - never assume config contents
2. **Identify the current phase** (1/2/3) before providing diagnostics
3. **Follow the required response format** strictly
4. **Prioritize Image Analysis** when multiple issues exist
5. **Reference specific case numbers** from the diagnostic framework

---

## Image Fitting Strategy (Phase 1)

### Principle
- Start from the simplest model (single Sersic), add components incrementally.
- Image residuals are the PRIMARY decision driver.
- Apply Occam's Razor: use BIC to validate every component addition.
- Accept features that cannot be meaningfully fitted (spiral arms, small clumps).

### Initial Setup
Start with a **single Sersic component** (disk). Typical initial parameters:

| Parameter | Initial | Bounds |
|-----------|---------|--------|
| Center (x,y) | ~0 (relative) | ±0.3 |
| Re | 0.23-0.33 | 0.01 to 0.75-1.00 |
| n | 2.5 | 0.2 to 8 |
| PA | from image/catalog | -180 to +180 |
| q | from image/catalog | 0 to 1 |

### Residual → Decision Mapping

| Residual Pattern | Action | Parameter Rules |
|------------------|--------|-----------------|
| Large-scale symmetric excess (center + radial alternation) | Add **bulge** | bulge: n=4, Re=50-75% of disk; disk n→1 |
| Linear/X-shaped bright center | Add **bar** | bar: n=0.5 (fixed, vary=0), q≈0.3; PA from prev fit; disk PA→0, q↑ |
| Compact central positive residual (PSF-like) | Add **PSF/AGN** | Use PSF model when Re<1 pixel |
| Off-center compact bright spot | Add **companion** Sersic | Position from residual; wide ranges |
| Outer closed bright ring | Add **ring** | Gaussian ring or truncated Sersic |
| Asymmetric/tidal/merger features | Add **Fourier mode** | 1st order Fourier; ignore what can't be fitted |
| Large-scale systematic offset or gradient | **STOP fitting, report issue** | Likely: bad initial guess / sky background / PSF mismatch |
| Spiral arms ("positive-negative alternating spiral pattern") | **ACCEPT**, do not add components | Impact on mass is negligible |
| Small clumps | **ACCEPT**, do not add components | |
| Unmasked foreground/background source | **Update mask**; if impossible, STOP and report | |

### Physical Meaning Check (after every round)

| Issue | Condition | Action |
|-------|-----------|--------|
| Bar vs edge-on disk | n<1 AND q<0.5 | If another larger disk exists → set as bar (n=0.5); if only component → keep |
| Point source in Sersic | Re << 1 pixel | Replace with PSF model |
| Bulge+Disk center offset | Distance between centers > disk Re | Add companion + constrain centers |
| Bulge/Disk label swap | Bulge Re > Disk Re | Swap component labels |
| 3-component label order | Not re_disk > re_bar > re_bulge | Reorder by Re size |

### Occam's Razor (after every component addition)

**BIC Decision Standard:**

| ΔBIC = BIC_simple - BIC_complex | Decision |
|----------------------------------|----------|
| < 0 | Reject complex model (overfitting) |
| 2-6 | Keep simple model (weak evidence) |
| > 6 | Accept complex model |

**Deletion Priority (when simplifying):**
1. Remove "patch" components covering background/PSF issues
2. Replace Re<1px "fake Sersic" with PSF model
3. Merge highly degenerate redundant components
4. Remove components contributing <1% of total flux

### Component Parameter Inheritance

When adding a new component:
1. Copy ALL spatial parameters from the existing primary component as initial values
2. Only modify the parameters specific to the new component type (see table above)
3. Use `--readsummary <prev.gssummary>` to carry forward all fitted parameters

### Auto-Iteration & Stopping Criteria

**Auto-Iteration Rule:**
After each round, evaluate the average fitting score:
- **Average score < 60 (Tier 3 Fair or below)**: Automatically proceed to next round WITHOUT asking user. Identify residual pattern, modify config, and run next iteration.
- **Average score ≥ 60 (Tier 2 Good or above)**: STOP and report results to user. Let user decide whether to continue optimizing or proceed to next phase.

**"Good Enough" Stopping Criteria (to report to user):**
- Residuals appear noise-like ("TV static") with no systematic structure
- Remaining features are explicitly accepted (spiral arms, clumps, tidal tails after Fourier)
- BIC has improved (ΔBIC > 2) and parameters are physical
- No parameters hitting boundaries
- OR: max 5 rounds reached (report current best result)

### Config File Isolation

**NEVER modify the original .lyric file.** For the initial fit and each later iteration:
1. Create a timestamped output directory using `YYYYMMDD_HHMMSS_<basename>` for the initial fit or `YYYYMMDD_HHMMSS_<basename>_iterN` for later iterations
2. Write the config file into that directory: `{galaxy_dir}/output/{timestamp}_{basename}/{basename}.lyric` for the initial fit, or `{galaxy_dir}/output/{timestamp}_{basename}_iterN/{basename}_iterN.lyric` for later iterations
3. Pass the config path to `run_galfits`, which will detect the existing workplace and use it directly
4. Use `--readsummary` to inherit parameters from the previous fit when continuing iterations

**Directory structure example:**
```
obj40/
├── obj40_s1.lyric                              # Original config (NEVER modify)
├── fitting_log.md                              # Auto-generated fitting log
├── output/                                     # Pre-created output directories
│   ├── 20260423_142428_obj40_s1/               # Initial fit output
│   │   ├── obj40_s1.lyric                      # Config (written before run)
│   │   ├── obj40_s1.gssummary                  # Initial fit results
│   │   └── ...
│   ├── 20260423_143334_obj40_s1_iter2/         # Later iteration output
│   │   ├── obj40_s1_iter2.lyric                # Config (written before run)
│   │   ├── obj40_s1_iter2.gssummary            # Iteration results
│   │   └── ...
│   └── 20260423_144053_obj40_s1_iter3/         # Later iteration output
│       ├── obj40_s1_iter3.lyric                # Config (written before run)
│       ├── obj40_s1_iter3.gssummary            # Iteration results
│       └── ...
```

---

# Diagnosis Logic & Rule Base (Structured Thinking)

Analyze the fitting results across THREE dimensions. If multiple issues exist, prioritize "Image Analysis" FIRST.

## 1. Image Analysis

### 1.1 Data Image Diagnostics
**CRITICAL: Per-Band Analysis Required**
For multi-band fitting, you MUST analyze EACH band SEPARATELY:
- Do we see contamination sources in the image that are neither fitted nor mask? If yes, we need to request to add a mask and consider if this is the main reason of the bad fitting.
- Do we see spiral-like pattern in the galaxy? If yes, we need to include a disk component and may add a bulge, a bar, or both.
- Do we see a bar-like pattern in the center of the galaxy? If yes, we need to add a bar component in the fitting.
- Do we see PSF like pattern in the center of the source? If yes, we may try to include a PSF model in the center.

**Global evaluation**
- Compare the common and special features of the individual bands
- If the data quality of some individual bands are particularly bad, ignore them in the residual evaluation

### 1.2 Residual Map Diagnostics
**CRITICAL: Per-Band Analysis Required**
For multi-band fitting, you MUST analyze EACH band SEPARATELY:
- Examine residual images for each band individually
- Provide independent analysis process and conclusions for each band
- Identify which specific band(s) exhibit issues
- If issues are band-specific, clearly indicate which bands need adjustments

For each band, examine the residual image (Original - Model) for systematic patterns:

**Bad Fitting Indications & Prescribed Actions:**
*   **Case A:** Blue/Red color split in residuals (band misalignment).
    *   *Action:* Allow position shifts between bands; adjust center initial values and fitting ranges.
    *   *Band-specific:* Identify which bands are misaligned
*   **Case B:** Off-center bright source in residuals.
    *   *Action:* Add a new Sersic component at that position.
    *   *Band-specific:* Note if the off-center source appears in specific bands only
*   **Case C:** Axisymmetric (e.g. doughnut-like) residual or long strip of positive residual through center.
    *   *Action:* Add a 'bar' component to the model (Sersic profile with n=0.5).
    *   *Band-specific:* Check if a bar-like feature is visible in the galaxy center across all bands
*   **Case D:** Circular positive residual in center.
    *   *Action:* Add a 'bulge' or 'AGN' point-source component.
    *   *Band-specific:* Determine which bands show the central excess
*   **Case E:** Model structure deviates significantly from Input image.
    *   *Action:* Re-adjust initial parameters (axis ratio, position angle, center coordinates).
    *   *Band-specific:* Identify which bands show structural deviation

**Good Fitting Indications:**
*   Residuals appear flat/noise-like (no systematic patterns).
*   Irregular residuals in high-SNR bands that do NOT match Case A-E are acceptable.

*Important Note:* IGNORE spiral arm or ring features. These are complex structures beyond current scope. Do NOT recommend adding ring components.

### 1.3 Fitting Quality Scoring Standard
**CRITICAL:** You MUST assign a score (0-100) for EACH band individually, then calculate the overall average score.

#### Five Scoring Tiers:

| Tier | Score Range | Quality Level | Residual Features Description |
|------|-------------|---------------|-------------------------------|
| **Tier 1** | 80-100 | Excellent | 残差图像呈现纯噪声特征，无明显系统性结构。中心区域无明显正/负残差，边缘无扩散状残留。模型与原始图像视觉上几乎完全一致。 |
| **Tier 2** | 60-79 | Good | 残差总体呈噪声状，但存在轻微局部结构。中心或边缘有微弱系统性残差（强度<背景噪声的2倍）。整体拟合良好，仅需微调。 |
| **Tier 3** | 40-59 | Fair | 存在明显但不严重的系统性残差结构。可识别轻微的Case A-E特征，但强度中等。拟合基本可用，建议针对性优化。 |
| **Tier 4** | 20-39 | Poor | 存在强烈的系统性残差结构。Case A-E特征清晰可见，强度显著（>背景噪声3倍）。模型明显偏离数据，需重新拟合。 |
| **Tier 5** | 0-19 | Failed | 模型完全无法描述数据。残差呈现原始图像的主要结构特征，或出现严重的拟合失败迹象（如负通量、参数边界溢出）。必须重新拟合。 |

#### Scoring Guidelines:
1. **Per-Band Scoring:** 每个波段独立打分，考虑该波段的SNR和残差特征
2. **Holistic Consideration:** 综合考虑残差形态、统计量（χ²）和参数合理性；注意，在没有用很多模型成分的情况下，χ²小于1是可以接受的。
3. **SNR Adjustment:** 高SNR波段要求更严格，低SNR波段可适当放宽
4. **Output Format:** 输出每个波段得分 + 总体平均分 + 对应档位

## 2. Summary Statistics Analysis
Check the optimization output for numerical issues:

*   **Check A:** Any parameter hit upper/lower limits?
    *   *Action:* Expand the limit bounds (ensure radius < image size).
*   **Check B:** `reduced chisq` in one band >> median of others?
    *   *Action:* Flag as problematic; cross-reference with Image/SED issues.
*   **Check C:** SED parameters hit limits?
    *   *Action:* Adjust SED parameter limits.

*Conclusion:* If no issues in A/B/C, mark Summary as **Good**.

## 3. Lyric File Reference

GALFITS uses `.lyric` config files. Key parameter format:

```text
[initial_value, min, max, step, vary]
```

- `vary=1`: free parameter | `vary=0`: fixed parameter

### Phase Modifications

| Phase | Ia15 (Use SED) | Pa3-Pa8 (Spatial) | Pa9-Pa16 (SED) |
|-------|---------------|-------------------|----------------|
| 1 | 0 | vary=1 | vary=0 |
| 2 | 1 | vary=0 | vary=1 |
| 3 | 1 | vary=1 | vary=1 |

### Component Type Quick Reference

| Prefix | Component | Parameters | Edit Example |
|--------|-----------|------------|--------------|
| **R** | Region | R1-R3 | `R1) MyGalaxy` |
| **I** | Image | Ia1-Ia15 | `Ia15) 0` # No SED (Phase 1) |
| **S** | Spectrum | Sa1-Sa4 | `Sa1) spectrum.txt` |
| **A** | Atlas | Aa1-Aa7 | `Aa2) ['a','b']` |
| **P** | Profile | Pa1-Pa32 | `Pa2) sersic` |
| **N** | Nuclei/AGN | Na1-Na27 | `Na12) ['Hb','Ha']` |
| **G** | Galaxy | Ga1-Ga7 | `Ga2) ['a','b']` |

---

## GalfitS Manual SKILL

**IMPORTANT: Use `/skill galfits-manual` to access the complete documentation before modifying configs.**

Key sections:
- **SKILL.md** - Main navigation and quick reference
- **data-config.md** - Region (R), Images (I), Spectra (S), Atlas (A)
- **model-components/** - Galaxy (G), Profile (P), Nuclei/AGN (N), Foreground Star (F)
- **examples/** - Configuration examples for different scenarios
- **running-galfits.md** - Command-line arguments and MCP interface
- **constraints/** - MSR, MMR, SFH, AGN constraints

### SKILL Sections for Common Edits

| Edit Task | SKILL Reference | Key Parameters |
|-----------|-----------------|----------------|
| **Add Sersic bulge** | model-components/profile-sersic.md | Pa1-Pa32, set Pa2=sersic |
| **Add Sersic bar** | model-components/profile-sersic.md | Pa1-Pa32, set Pa2=sersic |
| **Add AGN** | model-components/nuclei-agn.md | Na1-Na27 |
| **Fix band misalignment** | running-galfits.md → Troubleshooting | Ia13=1, Ia14 ranges |
| **Enable SED fitting** | SKILL.md → Phase-Specific | Ia15=1, Pa9-Pa16 vary=1 |
| **Apply MSR constraint** | constraints/mass-size-relation.md | --priorpath file |

### Action: Edit Configuration Files

When editing .lyric files, you MUST:

1. **Read current config first** - Never assume contents
2. **Reference SKILL** (`/skill galfits-manual`) for correct parameter format
3. **NEVER modify the original .lyric file** - write the new config into a timestamped output directory using `YYYYMMDD_HHMMSS_<basename>` for the initial fit or `YYYYMMDD_HHMMSS_<basename>_iterN` for later iterations
4. **Use Write tool** to create new config files (not Edit on originals)

**Example: Adding a bar component**
```text
# Before: Use SKILL to understand format
/skill galfits-manual → model-components/profile-sersic.md

# Action: Write new config with bar component
Pc1) bar      # Component name
Pc2) sersic   # Profile type (Sersic mode for bars)
Pc3) [0,-5,5,0.1,1]  # x-center
Pc4) [0,-5,5,0.1,1]  # y-center
Pc5) [2.69,0.67,10.75,0.1,1]  # Re of the bar
Pc6) [0.5,1,6,0.1,0] # **important** Fix the Sersic index to 0.5 for the bar
...

# Update Galaxy to include new component
Ga2) ['a','b','c']  # Add 'c' for the new bar component
```

---

## Available MCP Tools

### Important GalfitS CLI Parameters

| Parameter | Purpose | When to Use |
|-----------|---------|-------------|
| `--fit_method ES` | Evolution Strategy optimizer | All image-fitting rounds (REQUIRED) |
| `--readsummary <.gssummary>` | Carry forward best-fit params from previous fit | Every iteration after the initial fit |
| `--prior <.prior>` | Apply mass/size constraints | When prior file is available in galaxy directory |
| `--saveimgs` | Save diagnostic images | Always |

### mcp__galmcp__run_galfits
Execute GalfitS multi-band fitting.

**Parameters:**
- `config_file`: Path to .lyric config file
- `timeout_sec`: Optional (default: 3600)
- `read_summary`: Path to previous .gssummary to carry forward parameters
- `prior_file`: Path to .prior file for mass/size constraints
- `extra_args`: Additional CLI args (e.g. `["--fit_method", "ES"]`)

**Important:** Only use `--fit_method=ES` to run GalfitS. Always use this MCP tool; if not possible, provide the reason and ask if proceed with bash.

### mcp__galmcp__galfits_analyze_by_vlm
Analyze results using multimodal AI.

**Parameters (all required unless noted):**
- `image_file` (required): Combined stamp (original|model|residual) PNG
- `summary_file` (required): Optimization summary file
- `config_file` (required): Path to the .lyric config file
- `user_prompt` (required): Structured observations
- `sed_file` (optional): SED plot PNG
- `llm_type` (optional, default "openai"): LLM provider type

**user_prompt template:**
```text
## CURRENT PHASE
Phase 1

## USER OBSERVATIONS
### Image Residuals
- [Describe patterns]

### Summary Statistics
- [Parameters hitting limits?]
- [Reduced chi-square issues?]

### SED Analysis
- [Data vs Model quality]

## USER QUESTION
- [Specific question]
```

**Important:** Always use this MCP tool for analysis; if not possible, provide the reason and ask if proceed with manual analysis.

---

## Workflow

### 阶段一. 确认文件与原图分析
* **确认目录结构：** 确认每个波段的 FITS、mask、sigma、PSF、.lyric 文件是否存在。确认 .prior 文件是否存在（若存在，后续每轮传入 --prior）。
* **原图分析：** 使用 `view_original_image` 分析原图，逐波段确认形态特征。
* **确认配置：** 读取 .lyric 文件内容，确认处于 Phase 1 状态（Ia15=0, 空间参数 vary=1, SED 参数 vary=0）。

### 阶段二. 多轮迭代拟合（最多 5 轮）

每轮执行以下流程：

**步骤 1. 执行拟合**
* 首次拟合：先在 `output/{timestamp}_{basename}/` 中写入配置文件，再使用 `run_galfits` 执行拟合，并通过 `extra_args` 传入 `--fit_method ES`。
* 后续迭代：先在 `output/{timestamp}_{basename}_iterN/` 中写入新的配置文件，再使用 `run_galfits`；传入 `read_summary` 参数指向上一轮的 `.gssummary` 文件，以及 `prior_file` 参数指向 `.prior` 文件（若存在），并通过 `extra_args` 传入 `--fit_method ES`。
* 等待拟合完成，获取 image_fit.png、.gssummary、.params。

**步骤 2. 残差分析**
* 使用 `galfits_analyze_by_vlm` 分析残差图像和拟合摘要。
* 按照 Residual → Decision Mapping 表（见上方），判断残差属于哪种模式。
* 逐波段评估残差特征，按 Case A-E 分类。

**步骤 3. 物理意义检查**
* 检查拟合参数是否符合物理意义：
  - 是否存在 bar vs edge-on disk 歧义？（n<1 且 q<0.5）
  - 是否有点源误用 Sersic？（Re < 1 pixel）
  - bulge 和 disk 中心是否偏离过大？
  - bulge/disk 标签是否反转？（bulge Re > disk Re）
  - 多成分 Re 顺序是否合理？（应满足 re_disk > re_bar > re_bulge）
* 如有不物理情况，按 Physical Meaning Check 表处理。

**步骤 4. 奥卡姆剃刀检查**
* 计算与上轮的 ΔBIC，判断新增成分是否合理。
* 检查参数简并、碰边界等过拟合迹象。
* 如 ΔBIC < 0，拒绝复杂模型，回退到上轮配置。

**步骤 5. 评分与决策**
* 按评分标准（五档评分标准，见上方 1.3 节）对每个波段独立打分。
* 根据评分结果决策：
  - **平均分 ≥ 60 (Tier 2 Good or above)**: STOP，进入阶段三报告结果。
  - **平均分 < 60 (Tier 3 Fair or below)**: 自动进入下一轮迭代，无需询问用户。
  - 达到 5 轮上限：报告当前最佳结果。
* 如需添加/修改成分，遵循 Component Parameter Inheritance 规则，使用 `/skill galfits-manual` 获取正确的参数格式，写入新的 `output/{timestamp}_{basename}_iterN/{basename}_iterN.lyric` 文件。
* 如遇到系统性偏差或无法更新 mask，进入阶段三并说明问题。

**每轮输出简要评估记录：**
- Overall: Good/Bad/Stop
- Residual: [一句话描述]
- ΔBIC vs 上轮: [数值]
- Reduced chisq vs 上轮：[数值]
- Decision: [动作]
- Parameter Changes: [具体修改]

### 阶段三. 结果报告
* 锁定最佳结果（参数符合物理意义且残差评分最优的轮次）。给出各成分的形态学物理意义（如：成分 a 代表经典的指数盘结构，成分 b 代表致密的经典核球）。
* 写入 `analysis_report_xxx.md` 到星系目录。
* 报告内容：
  - **每轮评估记录汇总**（Overall、Residual、ΔBIC、Decision、Changes）
  - **最终参数表**（空间参数，逐成分）
  - **各波段评分**
  - **物理意义解读**
  - **附件索引**（.lyric 路径、image_fit.png 路径、.gssummary 路径）

## 待拟合星系

{argument}
