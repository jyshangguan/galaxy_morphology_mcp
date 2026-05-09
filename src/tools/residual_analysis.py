
import os
import uuid
from typing import Annotated, Any
import dotenv
from . import prompt
from .analyze_image import (
    create_vlm_client,
    encode_image_to_base64,
    read_summary_file,
    call_vlm_api,
)

dotenv.load_dotenv()


def component_analysis(
    image_file: Annotated[str, "Path to the combined residual image file [png file] containing three stamps: original, model, residual"],
    summary_file: Annotated[str, "Path to the optimization summary file containing detailed fitting information"],
    mode: Annotated[str, "Fitting mode: 'single-band' for GALFIT or 'multi-band' for GalfitS"],
    custom_instructions: Annotated[str, "Context for this round of analysis: must include (1) scientific objective of this fitting task  (2) file path of `working_note.md`"] = "",
) -> dict[str, Any]:
    """
    Analyze galaxy fitting results to determine component composition and parameter adjustments.

    This function examines the fitting result stamps (Original | Model | Residual) alongside
    the fitting summary, identifies missing or misconfigured physical components (bulge, disk,
    bar, AGN, etc.), and provides actionable suggestions for component addition/removal and
    parameter refinement.
    Args:
        image_file (str): Path to the combined image file containing three stamps displayed horizontally:
                        - Original galaxy image
                        - Model image (fitted model)
                        - Residual image (Original - Model)
                        For multi-band fitting, each band has its own set of stamps.
        summary_file (str): Path to the optimization summary file containing:
                          - Fitted parameter values and their uncertainties
                          - Chi-squared statistics and goodness-of-fit metrics
                          - Component descriptions
        mode (str): 'single-band' for GALFIT or 'multi-band' for GalfitS.
        custom_instructions (str): Required context for multi-round iterative fitting. Must contain:
            1. **Scientific objective** — the scientific goal of this fitting task (e.g., bulge-disk decomposition, bar identification, AGN detection, galaxy morphology classification).
            2. **Round history summary** — file path of `working_note.md`                 
            Additional specific requirements or constraints can also be appended.

    Returns:
        dict[str, Any]: A dictionary containing:
            - status (str): "success" if analysis completed successfully, "failure" otherwise
            - analysis (str, optional): The diagnostic analysis report (only on success)
            - analysis_file (str, optional): Path to the saved analysis markdown file (only on success)
    """
    # Validate input files
    if not os.path.exists(image_file):
        return {"status": "failure", "error": f"Image file not found: {image_file}"}
    if not os.path.exists(summary_file):
        return {"status": "failure", "error": f"Summary file not found: {summary_file}"}

    # Read summary (needed for both modes)
    summary_content = read_summary_file(summary_file)
    if not summary_content:
        return {"status": "failure", "error": f"Failed to read summary file: {summary_file}"}

    # Build prompt and system message from the residual analysis templates

    system_message = prompt.RESIDUAL_ANALYSIS_SYSTEM_MESSAGE

    # Append component specification based on mode
    if mode == "multi-band":
        component_spec = prompt.get_component_specification_galfits()
    else:
        component_spec = prompt.get_component_specification_galfit()

    if component_spec:
        system_message = system_message + "\n\n" + component_spec


    # ── Dispatch to the chosen analysis backend ──────────────────────
    analysis_mode = os.environ.get("ANALYSIS_MODE", "vlm").lower()
    session_id = ""

    if analysis_mode == "cc":
        if not os.environ.get("CLAUDECODE_API_KEY"):
            return {"status": "failure", "error": "ANALYSIS_MODE=cc requires CLAUDECODE_API_KEY to be set in environment"}
        from .cc_analysis import run_component_analysis_cc
        session_id = str(uuid.uuid4())

        prompts_list: list[str] = [
            f"{os.path.abspath(image_file)},查看原图图像和模型图像，分析中心星系的结构特征；重点描述二维残差图与一维轮廓图的差异特征。要求分析出真实存在的物理成分（盘、核球、侧视盘、棒、AGN核）。要求：所有现象描述必然基于图片内容， 不能主观臆测",
            f"集合拟合summmary文件：{os.path.abspath(summary_file)}，严格按照残差图分析与决策诊断树的逻辑，对成分进行分析，是否需要增加或删除成分？要求\n1。 仅关注中心区域星系图像与残差特征。2。仅关注拟合盘、核球、侧视盘、棒、AGN核这五种物理成分，仅可对这五种成分的残差添加模型成分拟合，其他残差特征可以选择保留不拟合\n 3。补充信息：{custom_instructions}",
            "只提供一个最重要的结论（不允许一次增加或删除多个成分）。调整成分的同时，如果需要同步修改其他成分的参数也需同步提供。输出格式要去：\n## 本次调整决策如下：\n1。本次调整物理目标:xxx \n2。具体内容:xxx",
        ]
        analysis, error = run_component_analysis_cc(
            system_prompt=system_message,
            analysis_prompts=prompts_list,
            session_id=session_id,
        )
        if error:
            return {"status": "failure", "error": error}

    elif analysis_mode == "acp":
        from .acp_analysis import run_component_analysis_acp

        step1 = f'''
你是一个集成了“计算机视觉特征提取”与“天体物理形态学专家推理”的自动化诊断 Agent。你的任务是基于 GALFIT 的拟合结果，通过严密的四步思维链（Chain-of-Thought），诊断当前模型的缺陷，并输出下一步的调整决策,

在这个过程中只能使用read_file 和 write_file 工具，不能使用其他工具。 write_file 可以用于编写 /tmp/todo_xxx.md来记录代办进展。

【输入信息】
1. 参数汇总：
{{os.path.abspath(summary_file)}}
2. 图像对比：
{os.path.abspath(image_file)} （包含原图、模型图、2D残差图及1D表面亮度轮廓图）
3. 补充信息：
{custom_instructions}

【执行步骤】
请你依次执行以下 4 个阶段的分析。在阶段 1 和阶段 2 中，你必须保持绝对的客观，严禁进行任何物理成分的猜测与推断。

**阶段一：参数与运行状态健康度审查（仅客观排查）**
1. 边界碰撞排查：排查并列出所有带有星号 (*) 的参数，描述 Sérsic 指数 n 是否触及优化算法设定的上下限极值边界。
2. 误差异常排查：对比括号内的参数不确定度（Error）与参数本身的量级差异，指出并描述任何发生不确定度异常放大的参数项。
3. 物理尺度反常排查：排查并描述所有成分的有效半径 (Re) 存在的极大或极小异常情况，以及轴比 (q) 的极端取值状态。

**阶段二：多模态视觉特征提取（仅客观描述）**
1. 2D 原图与模型对比：观察原图的主体区域轮廓与等亮度线分布，对比模型图及其叠加的模型轮廓线，详细描述模型与原图在宏观大小、扁率和倾斜角度上的贴合程度及视觉边界差异。
2. 2D 残差图-核心区：描述中心区域残差的空间分布形态，重点说明正负残差交替的排列几何方式、四极矩特征的形状表现，以及特定方向上视觉残留的分布走向。
3. 2D 残差图-外围区：描述主星系外围空间的背景平整度状态，明确指出任何非对称高亮区域的位置特征，以及微弱结构残影的几何形态细节。
4. 1D 轮廓图：描述 x、y坐标意义；数据曲线、模型曲线的结构特征；成分组成与成分曲线的结构特征、流量比例。
5。1D 残差图：描述 x、y坐标意义；残差曲线（Data-Model）的结构特征；特别是 R = 0 附近的残差表现，以及残差曲线在不同半径范围内的震荡特征。

**阶段三：物理映射与诊断树推理（专家思维链CoT）**
结合阶段一和二的客观发现，以及【残差图分析与决策诊断树】，进行严密推导：
1. 异常归因：分析残差和参数异常的根本原因，明确说明问题是源于数据污染、优化算法陷入局部极小值，还是缺失或冗余了特定的核心物理成分。
2. 物理成分映射：仅限在“核球(Bulge)、盘(Disk)、侧视盘(Edge-on Disk)、棒(Bar)、致密核(AGN/PSF)”这五种物理成分范围中进行成分映射与增减考量。
3. 冲突校验：交叉对比二维/一维视觉残差表现与参数边界状态，推演是否存在两者指向相左的逻辑冲突，并给出化解该物理冲突的推导逻辑。

**阶段四：最小化原子动作输出**
- 只提供一个最重要的结论（不允许一次增加或删除多个成分）。
    - 处理优先级如下：优先确认上一轮的目标是否达成，达成后再进行下一轮的调整。如果上一轮的目标没有完全达成，优先继续调整该目标，
    - 成分添加遵守由外到内，尺寸由大到小原则。
- 初始值参数要基于现有成分和目标成分进行有效推理和高质量预估。需要确定 x,y,n,man,Re,ba,pa等关键参数的调整方向和幅度。
- 输出格式要求：
    ···
    ## 本次调整决策如下：
    # 1.本次调整物理目标:xxx 
    # 2.具体调整内容:xxx"（包含新一轮拟合的所需的成分的参数初值）    
    ···

'''
        prompts_list: list[str] = [step1]
        analysis, session_id, error = run_component_analysis_acp(
            system_prompt=system_message,
            analysis_prompts=prompts_list,
        )
        if error:
            return {"status": "failure", "error": error}

    else:
        analysis_prompt = prompt.get_residual_analysis_prompt(summary_content)
        if custom_instructions:
            analysis_prompt += f"\n\n--- Additional requirements ---\n{custom_instructions}"        
        # --- VLM mode (original single-shot path) ---
        client, error = create_vlm_client()
        if error:
            return {"status": "failure", "error": error}

        base64_image = encode_image_to_base64(image_file)
        if not base64_image:
            return {"status": "failure", "error": f"Failed to encode image: {image_file}"}

        vlm_prompt = f'残差图文件路径：{image_file}' + analysis_prompt
        additional_content = [{"type": "text", "text": vlm_prompt}]

        analysis, error = call_vlm_api(
            client=client,  # type: ignore[arg-type]
            base64_image=base64_image,
            additional_content=additional_content,
            system_message=system_message,
        )
        if error:
            return {"status": "failure", "error": error}

    # analysis is guaranteed to be str when error is None
    assert analysis is not None, "Analysis should not be None when error is None"

    # Save analysis
    base_name = os.path.splitext(os.path.basename(image_file))[0]
    if session_id:
        output_file = os.path.join(os.path.dirname(image_file), f"{base_name}_component_analysis_{session_id}.md")
    else:
        output_file = os.path.join(os.path.dirname(image_file), f"{base_name}_component_analysis.md")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(analysis)
        print(f"Component analysis saved to: {output_file}")
    except Exception as e:
        print(f"Warning: Failed to save analysis to file: {e}")
        output_file = None

    return {
        "status": "success",
        "analysis": analysis,
        "analysis_file": output_file,
    }
