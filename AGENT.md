


# 星系成分分析的方法指南
1. 首先，对星系成分总体判断。基于原图和残差图，分析星系的总体结构， 优先确认以下结构
    1. 是否存在旋臂？
        1. 现象：1. “正负相间”的螺旋图案； 2.明亮的“串珠状”结块：高亮旋臂上，你通常能看到一连串更亮、更紧凑的“高光斑点”。3. 伴生的尘埃带：紧挨着明亮的正残差螺旋带内侧，有一条细长、锐利的深色负残差线。
        2. 对策：通常直接忽略，不影响整体质量评估。
    2. 是否存在内部尘埃带遮挡或者图像上有未被遮掩（Masking）的前景恒星/坏像素？
        1. 现象：存在不规则的暗斑或暗带
        2. 对策：这通常不需要增加发光成分，而是需要完善 Mask 掩膜文件。
    3. 是否存在星系并合遗迹 (Merger Remnants) 的残差特征：
        1. 壳层（Shells）特征：在残差图的边缘区域，你会清晰地看到**微弱的、呈同心弧线状的正残差（壳层）**
        2. 潮汐尾遗特征：在残差图的边缘区域，你会清晰地看到，向外发散的、细长的亮色条带
        3. 混乱的尘埃遮挡 (Chaotic Dust Lanes) 特征：在残差图的核心或盘区，你会看到不规则、像蛛网或裂纹一样的深色负残差网络。这是因为浓密的尘埃遮挡了背后的星光，导致这些区域的实际观测亮度远低于平滑的理论模型。
        4. 对策：使用了1阶傅里叶模式之后，拟合不了的结构可以忽略。
    4. 是否存在偏离中心的独立亮斑或致密源？
        1. 现象：残差图中除了主星系外，散落着一个或几个非常明显的圆形/椭圆形正残差。物理意义：未掩膜的伴星系、大质量星团或前景恒星。可能是正在并合的伴星系（Companion galaxy），也可能是星系盘上极其明亮的巨大 H II 区/恒星形成团块（Clumps）
        2. 对策：如果是星系本身的物理团块或相互作用的伴星系，需要为这些源单独增加 Sersic 或 PSF 成分进行同时拟合（Simultaneous fitting）。
    ps: 要仔细分辨伴星系和潮汐尾的特征，他们的处理方式存在较大差异。伴星系通常表现为一个相对独立的、圆形或椭圆形的亮斑，且其位置可能在主星系的外围；而潮汐尾则是从主星系边缘向外延伸的细长结构，通常呈现出不规则的形态。
2. 其次，细致分析星系所包含的成分类型。采用逐成分递增的方式进行，保证拟合的稳定性；成分添加逻辑
    1. 成分添加次序：先建立双成分基础结构（Disk、Bulge），再添加细节成分（Bulge、Bar、Nucleus等）
    2. 拟合过程是由总体到细节，逐渐细化，先低阶残差，后高阶残差：
        1. 先总体，对比原图 DATA 图和 Model 图，要求优先保障总体轮廓相近：（比如：Bar 的方向大小要一致、总体轮廓的 Disk 亮度区域要接近）
        2. 后细节。只有总体轮廓成分拟合（如双 Sersic）已经符合预期，才开始中心细节的拟合(Bulge/Bar/Nucleus等)
    3. 观察原图、model 图、1D 与 2D 残差图，确定是否存在预期的成分类型（也是成分添加的顺序）？
        1. Disk 成分与Bulge的认定方法
            1. 如果残差中出现大尺度的对称亮区（例如中心过亮而外围过暗，或者呈现环状的明暗交替），通常意味着当前的单成分（如单个 Sersic 轮廓）不足以描述星系。很多星系是“核球+盘”（Bulge + Disk）的双成分结构。
            2. 另外从原图和 model 中的轮廓也是一种很好的辅助判断，是否需要增加成分，来平衡外部大的轮廓和内部的亮度区域。才能是的两者亮度轮廓达到基本相似
        2. Bar 成分认定方法
            1. 如果在单 Sersic 或双成分拟合后，残差图中心区域出现明显的“一字型”或“X型/花生型”亮区，说明星系存在棒（Bar）。在拟合软件中，通常会增加一个低 Sersic 指数（如 $ n =  0.5 $）且椭率（Ellipticity）很高的成分。
        3. Ring 成分认定：振作用会形成核环（Nuclear ring）、内环（Inner ring）或外环（Outer ring）。
            1. 残差图中出现完整的闭合亮环，可以通过增加被截断的 Sersic 成分（Truncated Sersic）或高斯环（Gaussian ring）来进行拟合补偿。
        4. Nucleus 成分的认定方法
            1. 核星团（Nuclear Star Cluster, NSC）： 需要一个 Re 有效半径非常小的高 $ n $ 值（>4） Sersic 成分。伪核球（Pseudobulge）： 内部存在额外的致密结构。
            2. 活动星系核（AGN）： 通常需要用一个点源函数（PSF）来额外拟合。
        5. 高阶残差：偏心成分、壳层（Shells）或潮汐尾 （根据科学目标而定，只有用户特别要求，才需要考虑高阶残差）
            1. 现象：偏心成分：明显的“偶极” (Dipole) 模式，通常是沿着偏心的轴线一侧比另一侧更亮。
            2. 壳层（Shells）特征：在残差图的边缘区域，你会清晰地看到微弱的、呈同心弧线状的正残差（壳层）
            3. 潮汐尾遗特征：在残差图的边缘区域，你会清晰地看到，向外发散的、细长的亮色条带
            4. 对策：引入 1 阶傅里叶模式
    4. 新增成分的初始参数预估方法：
        1. **要求基于上一轮的拟合结果副本的基础上预估与修改，起到逐渐改善效果的目的，不要每次都从头开始**
    5. 调参策略：
        1. 基于上一轮的拟合结果副本的基础上预估与修改，起到逐渐改善效果的目的，不要每次都从头开始
        2. 一些例子
            1. 当遇到 Bulge 的 Re 很小时（比如远小于 1 个像素）；
                - 策略1：根据残差特点，调整 Disk 与 Bulge 的初始，这是必要步骤
                    - 比如：Bulge < 0.2 像素， 但星系边缘还存在明显的正残差，说明 Disk的Re设置过低，同时挤压了 Bulge 的 Re，导致 Bulge 的 Re 过小。需要同步调高两者的 Re 初值
                    - 其他残差特征意味着需要其他调整
                - 当策略1 无效时，根据物理意义分析，才考虑把 Bulge 换成 PSF 进行拟合
        3. 如果新增成分拟合的位置与原来的偏差较大（比如偏离距离大于 Re）；可以考虑添加一个约束，限制偏移量
        4. 当遇到某个通量占比过低，同时残差特征又预算该成分的存在，这预示着 各成分的 mag 初值需要重新分配。
            - 在使用奥卡姆剃刀之前，需要经过充分调参验证。
        5. 对于一般情况，可以直接让 Re、Mag 和 n 都自由拟合; 对于可能包含多个成分的复杂情况（特别是残差非常大的情况），Disk/Bulge可以才考虑固定 n 的, Re 和 Mag 参数拟合充分后，再放开n。都拟合到位了再考增加下一个成分。


## 添加约束
GALFIT 的参数约束文件（通常以 `.cons` 为后缀）是解决成分分配失衡和参数越界最核心的工具。

### 一、如何在 `feedme` 文件中启用约束

在你的主输入文件（`feedme`）开头部分，有一项专门用于指定约束文件：

```text
G) galaxy.cons      # Parameter constraint file (empty string)
```

将你的约束文件名（例如 `galaxy.cons`）填入 `G)` 项即可。如果不需要约束，留空或写 `none`。

---
### 二、`.cons` 文件的基本语法

约束文件的每一行代表一条规则。它的标准语法格式如下：
`[成分编号]   [参数名称]   [约束类型]   [下限]   [上限]`

#### 1. 常见参数名称缩写

在 `.cons` 文件中，参数必须使用特定的英文缩写：

* 位置坐标：`x`, `y` (通常写在一起 `x,y`)
* 总星等：`mag`
* 有效半径：`re` (Sérsic) / `rs` (Exponential disk) / `fwhm` (Gaussian/Moffat)
* Sérsic 指数：`n`
* 轴比：`q` (b/a)
* 位置角：`pa`

```text
# Component/    parameter   constraint    Comment
# operation (see below)   range

  3_2_1_9        x          offset      # Hard constraint: Constrains the
                                        # x parameter for components 3, 2,
                                        # 1, and 9 to have RELATIVE positions
                                        # defined by the initial parameter file.
  
  1_5_3_2       re          ratio       # Hard constraint: similar to above
                                        # except constrain the Re parameters 
                                        # by their ratio, as defined by the
                                        # initial parameter file.

    3           n           0.7 to 5    # Soft constraint: Constrains the 
                                        # sersic index n to within values 
                                        # from 0.7 to 5.

    2           x           -1  0.5     # Soft constraint: Constrains 
                                        # x-position of component
                                        # 2 to within +0.5 and -1 of the
                                        # >>INPUT<< value.

    3-7         mag         -0.5 3      # Soft constraint:  The magnitude 
                                        # of component 7 is constrained to 
                                        # be WITHIN a range -0.5 mag brighter 
                                        # than component 3, 3 magnitudes 
                                        # fainter.

    3/5         re          1  3        # Soft constraint:  Couples components 
                                        # 3 and 5 Re or Rs ratio to be greater 
                                        # than 1, but less than 3. 

# Note on parameter column:
#   The parameter name options are x, y, mag, re (or rs -- it doesn't matter),
#   n, alpha, beta, gamma, pa, q, c, f1a (Fourier amplitude), f1p (Fourier
#   phase angle), f2a, f2p, r5 (coordinate rotation), etc., .  Or 
#   alternatively, one can specify the parameter number instead (for the
#   classical parameters only) corresponding to the same numbers in the 
#   galfit input file.
```

## 约束规范

约束条件（Constraints）是防止算法“暴走”的安全网，但网织得太紧会勒死正常的优化过程。建议流水线采取以下策略：

- 设定符合物理意义的软性边界（Hard Bounds）：
在 .cons 约束文件中，为关键参数划定既安全又不至于太局促的绝对区间：
    - 中心坐标 (x,y)： 约束在初始值的 $\pm 2$ 到 $5$ 个像素内（如果是高度扰动的并合星系可放宽）。绝对不能让星系中心飘到图像边缘。
    - 有效半径 $R_e$： 最小值约束为 0.1 像素（或 PSF 的一半），最大值约束为图像边长的 1/2 或 1/3，防止模型在尝试拟合平坦背景时无限膨胀。
    - Sérsic 指数 $n$： 这是最容易暴走的参数。对于纯星系结构，物理上合理的 $n$ 值通常在 $0.1 \sim 8.0$ 之间。建议将其强制约束在 0.1 8.0（除非星系包含非常尖锐的无法分辨的 AGN 核心，才允许放宽到 15 或 20）。
    - 轴比 $b/a$： 约束在 0.05 1.0 之间，防止弱信噪比的盘成分被压成一条无物理意义的无限细线。

- 利用相对约束（Parameter Tying）稳定复杂模型： 当尝试分解高难度的 Bulge+Disk 甚至添加 Bar 时，参数极易发生简并。此时需要绑定参数：
    - 强绑定：通过在配置文件中将 Bulge 的 x, y 坐标变量与 Disk 强行链接（偏移量设为固定或完全一致），减少两个自由度，能极大提升收敛稳定性。
    - 相对约束：可以约束核球的尺寸始终小于盘（例如在 .cons 中限定 Bulge 的 $R_e$ 不能超过 Disk $R_e$ 的 80%）。

# 星系成分物理意义分析与策略
+ 在拟合得到的结果中，如果目标源的一个成分给出的参数满足n<1 （n~0.5）同时q< 0.5，这个成分可能是个bar或者edge-on disk。如果这个源在这个成分之外存在一个re大于此成分的disk成分， 则可以把这个成分修改成bar 进行拟合（n固定成0.5的sersic model）；如果此成分是该星系唯一成分，则可以不做修改。
+ 如果一个sersic  model拟合出来的结果 , re很小，远远小于1个pixel（如0.2pixel），意味着这个成分拟合的是一个点源，可以换成PSF model去拟合。
+ 同一个源的两个成分bulge+disk拟合完，如果bulge和disk中心之间的距离大于disk成分本身的re，可能两个成分拟合到两个不同的源上了。后续调整可以考虑增加一个成分拟合伴源，同时通过constrain文件限制同一个源不同成分之间中心的距离。
+ 对于盘星系而言，同一个源的两个成分bulge+disk拟合完，如果bulge的re 大于disk的re，意味着在拟合的过程中，bulge和disk的标签反了，可以交换这两个成分的标签。如果是3个成分拟合同一个源，通常情况存在 re_disk>re_bar>re_bulge，可以以此逻辑更新成分的标签。
+ 星系盘 Disk 并不一定要求 n = 1, 也并不要求 disk 的 N 比 Bulge 的 N 小. Disk 的 N 值可以小于 1（如 0.3），这通常对应较平缓的星系盘（Smooth disk）
+ Bugle 的 n 的范围一般在 0.1 < n < 8 之间，并不要要求一定要大于 1，Re在 0.2 pxiel以上都具有物理意义。 但对于 最亮星系系星系（BCGs）或 cD 星系，n 可能会超过 8；对于一些极端的伪核球（Pseudobulge），n 也可以小于 1。
+ Disk 与 Bulge 之间的 n 的关系并不固定，Disk 的 n 不一定比 Bulge 小；他们都存在真实的物理情况。
+ Disk、Bar、Bulge 他们基本同心，偏离太大的情况需要考虑增加一个成分拟合伴源，同时通过constrain文件限制同一个源不同成分之间中心的距离。

## 奥卡姆剃刀原则

如果出现以下直观现象或者 BIC 统计现象，需要使用奥卡姆剃刀原则，剔除不必要的成分。

### 触发条件

> 增加新成分后，残差图肉眼看有一点点改善，但**约化卡方（Reduced $\chi^2$）并没有显著下降**，或者**贝叶斯信息准则（BIC）/ 赤池信息准则（AIC）的数值反而变大了**。

### 具体处理步骤

1. **建立基础模型（Model A）并记录**
   首先用最简单的模型拟合星系。例如，对于一个看起来像旋涡星系的源，先只用一个单 Sérsic 成分（假定它是一个纯盘面），拟合收敛后，记录下它的 $BIC_A$。

2. **建立复杂模型（Model B）并记录**
   在基础模型上增加一个你怀疑存在的物理成分，比如增加一个代表中心核球的额外 Sérsic 模型（双成分拟合）。拟合收敛后，记录下它的 $BIC_B$。

3. **计算 $\Delta BIC$ 并决策**
   计算两个模型的差值：$\Delta BIC = BIC_A - BIC_B$

   | $\Delta BIC$ 范围 | 决策 | 说明 |
   |:-:|:-:|:--|
   | $< 0$ | **拒绝**复杂模型 | 虽然残差变小了，但惩罚项更大，说明发生过拟合，保留简单模型 |
   | $0 \sim 10$ | 仅供参考，**不作为接受依据** | 证据不足以支撑增加新成分的必要性 |
   | $> 10$ | **值得考虑接受**复杂模型 | 证据充分，可结合残差改善情况决定是否接受新成分 |

   > **默认判据：** $\Delta BIC > 10$ 是接受更复杂模型的必要门槛。$0 \sim 10$ 之间的证据仅作参考，不作为接受新成分的充分条件。如果拟合策略有更具体的倾向性，也可以进一步调高此阈值。

## Galfit 添加成分类型的规范 （必须严格遵守）

- 要增加成分BULGE： Component type选用 sersic.
- 要增加edge-on的星系盘：Component type选用 edgedisk。
- 当添加的 Bulge的 Re远远小于 1 pixel, 需要更换类型， 采用Component type为psf
- 要增加棒 Bar：Component type选用  n~0.5 的 Sersic 模型.
- 要增加指数衰减的星系盘disk: 选择 n=1 的 Sersic 模型。
- 如果星系已经有一个 Disk 成分了，针对星系外围（Outskirt）未拟合上的情况，可以添加第二个 Disk 成分或 Sérsic 成分，以捕捉更延展的结构，
- 星系是 Face-on、Edge-on需要需要先区分, 有助于提升 Disk的选择和初值设置的准确性；一个Disk的（b/a）小于 0.5，可以认定为Edge-on；
**要求基于上一轮的拟合结果副本的基础上预估与修改，起到逐渐改善效果的目的，不要每次都从头开始**

## 成分初始参数的设置参考

在深入各个模型之前，以下参数的获取方式通常是通用的，
- x 和 y（中心位置）：直接读取图像上该成分的亮度峰值像素坐标。如果多个成分同心（如核球+盘），它们的初始 x、y 应该设为相同。
- mag（积分星等）：如果是多成分拟合，初值设定方法。需要考虑 mag 的值，需要基于原来的 sersic 星等下调整；避免初始值差异过大导致拟合失败
  - a. 建议将成分间的通量差异分为“Comparable（相当）”
  - b. “Faint（较暗，约 1/3）”
  - c. “Much Fainter（暗很多，差 1-1.5 个星等）”三个等级
- b/a（轴比）：视觉估算。正圆为 1，越扁越接近 0。
- PA（位置角）：长轴相对于 y 轴（通常是正北）逆时针旋转的角度。初始值通过原图中预估, 特别是 Bar,该初值非常重要。
- 将单成分拆分为双成分拟合时： 例如准备用核球+盘 (Bulge+Disk) 的替代原来单 Sérsic 是：
    - 通量分配： 将测得的总通量按 $3:7$ 或 $4:6$ 的比例拆分，分别转换为星等赋值给核球和盘。
    - 尺寸分配： 核球的初始 $R_e$ 通常设为测光总半径的 $1/5$ 到 $1/3$；盘的初值 $R_e$ 要求大于单Sérsic的 Re （具体值需要考虑 1D Surface profile 残差曲线中部与后部的表现，要求Disk能够承接这个区域的光通量）。
    - 形态分配： 核球初始给定 n=4，盘初始n=1。
- 如果再残差图和原图上能够看到 Bar的特征，则可以考虑添加 Bar 成分，Bar 的初始参数设置为： n 固定为 0.5，轴比 b/a 初值设定在 0.2 - 0.4 之间，位置角 PA 根据图像中 Bar 的长轴方向测量后初始化，尺寸参数 R_e 则设定在核球和盘之间。Disk 与 Re的初值也进行对应调整，使得总体合理。


## 成分参数定义
1. sersic — 常用于 BULGE / Bar / Disk

0) sersic                 #  Component type
1) <x>  <y>  1 1          #  Position x, y
3) <mag>       1          #  Integrated magnitude
4) <R_e>       1          #  R_e (effective radius) [pix]
5) <n>         1          #  Sersic index n (de Vaucouleurs n=4)
6) 0.0000      0          #  -----
7) 0.0000      0          #  -----
8) 0.0000      0          #  -----
9) <b/a>       1          #  Axis ratio (b/a)
10) <PA>       1          #  Position angle (PA) [deg]
Z) 0                      #  Skip this model? (yes=1, no=0)

---
1. edgedisk — 常用于沿着视线方向几乎垂直观察的薄盘（$Z$ 轴方向的亮度分布）。

0) edgedisk               #  Component type
1) <x>  <y>  1 1          #  Position x, y
3) <mu0>       1          #  Mu(0) [mag/arcsec^2]
4) <h_s>       1          #  h_s (disk scale-height) [pix]
5) <R_s>       1          #  R_s (disk scale-length) [pix]
10) <PA>       1          #  Position angle (PA) [deg: Up=0, Left=90]
Z) 0                      #  Skip this model?

关键参数：h_s（标高）、R_s（标长）。
- mu0（中心表面亮度）：同上，盘中心的表面亮度。
- h_s（标高 Scale-height）：代表盘的厚度。初始化方法：在图中观察侧向盘在垂直方向的可见厚度，取其 1/3 或 1/4 作为初始值。
- R_s（标长 Scale-length）：代表盘的水平延伸。在长轴方向测量可见长度，除以 3 或 4 作为初始值。

---
1. psf — (常用于 活动星系核 AGN / 恒星 / 极其致密的核)

0) psf                    #  Component type
1) <x>  <y>  1 1          #  Position x, y
3) <mag>       1          #  Integrated magnitude
Z) 0                      #  Skip this model?

关键参数：仅 x, y 位置和积分星等，形状参数全部固定。
- x, y（中心位置）：必须极其精确。通常直接锁定图像中最亮的一个像素位置。
- mag（星等）：如果中心有明显的致密亮核（如 AGN），估算这个点源的星等。可以尝试用较小孔径测光的结果作为初始值。


# 成分的高阶参数，需要拟合高阶成分特征时使用。
The parameters C0, B1, B2, F1, F2, etc. listed below are hidden from the user unless he/she explicitly requests them.  These can be tagged on to the end of any previous components except, of course, the PSF and the sky -- If a Fourier or Bending amplitude is set to 0 initially GALFIT will reset it  to a value of 0.01. To prevent GALFIT from doing so, one can set it to any other value.

- Bending modes
B1)  0.07      1       # Bending mode 1 (shear)
B2)  0.01      1       # Bending mode 2 (banana shape)
B3)  0.03      1       # Bending mode 3 (S-shape)

- Azimuthal fourier modes
F1)  0.07  30.1  1  1  # Az. Fourier mode 1, amplitude and phase angle

- Traditional Diskyness/Boxyness parameter c
C0) 0.1         0      # traditional diskyness(-)/boxyness(+)


## Galfit 执行规范
- 执行 Galfit 优化，必须使用 galmcp 中的run_galfit工具， 不能直接使用用bash工具执行 galfit 命令行。因为 run_galfit 工具会自动处理一些后续的分析步骤（如残差图生成、参数解析等），直接调用 galfit 可能会导致后续流程无法



# Working Note 的格式内容要求
例如：
- Round 1.a : Disk + Bar
  - 成分分析要点：
    - component_analysis分析摘要：xxx
    - 预估存在的物理成分类型，包含 Disk + Bugle + Bar
    - 本轮需要添加的 Bar 成分; 其主要的 R_e预期小于Disk的R_e，Mag 预期和Disk 相当或者稍暗。
  - 参数设置摘要：xxx
  - galfit拟合结果摘要：
    - 拟合后成分类型与关键参数（位置、星等、尺寸、形状参数等）xxxx, 距离预期目标的偏差
    - 拟合统计指标（如 reduced chi-square, BIC/AIC 等
- Round 1.b : Disk + Bar
  - 参数设置摘要：上一轮 Mag 拟合后偏低， 考虑调整 mag 初值再次拟合。
  - galfit拟合结果摘要：
    - 拟合后成分类型与关键参数（位置、星等、尺寸、形状参数等）xxxx, 距离预期目标的偏差
    - 拟合统计指标（如 reduced chi-square, BIC/AIC 等
- Round 2.a : Disk + Bugle + Bar
  - 成分分析要点：
    - component_analysis分析摘要：xxx
    - 预估存在的物理成分类型，包含 Disk + Bugle + Bar
    - 本轮需要添加的 Bugle 成分; 其主要的 n预期2， xxx
  - 参数设置摘要：xxx
  - galfit拟合结果摘要：
    - 拟合后成分类型与关键参数（位置、星等、尺寸、形状参数等）xxxx, 距离预期目标的偏差
    - 拟合统计指标（如 reduced chi-square, BIC/AIC 等
