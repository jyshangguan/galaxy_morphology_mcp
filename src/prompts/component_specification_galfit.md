
# 成分添加规范

## Galfit 添加成分类型的规范 （必须严格遵守）

- 要增加成分BULGE： Component type选用 sersic.
- 要增加沿着视线方向几乎垂直观察的薄盘：Component type选用 edgedisk。
- 要增加活动星系核 AGN / 恒星 / 极其致密的核：Component type选用psf 
- 要增加棒 Bar：Component type选用  n~0.5 的 Sersic 模型.
- 要增加指数衰减的星系盘disk: Component type选用expdisk（等效于 n=1 的 Sersic 模型）。
- 对于Bar而言， PA 需要从图中观察的位置角，提供一个相对可靠的初值；否则galfit很难收敛；


## 各成分的具体参数设置

在深入各个模型之前，以下参数的获取方式通常是通用的，
- x 和 y（中心位置）：直接读取图像上该成分的亮度峰值像素坐标。如果多个成分同心（如核球+盘），它们的初始 x、y 应该设为相同。
- mag（积分星等）：如果是多成分拟合，可以将总星等按经验比例分配（例如核球比盘暗 1-2 个星等）。
- b/a（轴比）：视觉估算。正圆为 1，越扁越接近 0。
- PA（位置角）：长轴相对于 y 轴（通常是正北）逆时针旋转的角度。初始值通过原图中预估
- 多组件拟合的光度与尺寸拆分策略： 如果你准备拟合核球+盘 (Bulge+Disk) 的双 Sérsic 模型，绝对不能把 SExtractor 测出的总星等和总半径原封不动地同时赋予两个组件。经验法则：
    - 通量分配： 将测得的总通量按 $3:7$ 或 $4:6$ 的比例拆分，分别转换为星等赋值给核球和盘。
    - 尺寸分配： 核球的初始 $R_e$ 通常设为测光总半径的 $1/5$ 到 $1/3$；盘的 $R_e$ 则设为测光总半径的 $1 \sim 1.5$ 倍。
    - 形态分配： 核球初始给定 $n=4.0$（接近德沃库勒尔定律），盘初始给定 $n=1.0$（指数盘）。
---

在使用 GALFIT 进行三成分拟合时，核球（Bulge）与星系棒（Bar）通常使用 sersic 模型，而星系盘（Disk）建议使用专用的 expdisk 模型。以下是严格的参数初始化与约束规则：

### 1. Bulge（核球）— sersic 模型

- **Sérsic 指数 (n)**：
  - 经典核球 (Classical)：初始化 n = 4 (de Vaucouleurs 轮廓)。
  - 伪核球 (Pseudobulge)：初始化 n = 1。
  - 未知类型：初始化 n = 2 或 2.5，设为允许自由拟合 (vary=1)。
- **有效半径 (R_e)**：通常为尺寸最小的成分。

### 2. Bar（星系棒）— sersic 模型（需硬约束）

星系棒极易与核球或盘发生流量简并，必须施加严格的硬约束：

- **Sérsic 指数 (n) [硬约束]**：强制固定为 n = 0.5（即 vary=0）。
  - 异常处理：若允许自由演化且 n > 1，会导致结构分解失效。
- **轴比 (b/a 或 q) [硬约束]**：初始化在 0.2 - 0.4 之间。约束上限设定为 < 0.5。
  - 异常处理：若演化结果 b/a > 0.6，会导致 Bar 的流量被错误地并入 Bulge。
- **位置角 (PA) [高敏感]**：必须根据图像手动测量长轴后初始化。
  - 若初始 PA 偏离真实值 > 45°，算法易拟合到背景噪声上。
- **有效半径 (R_e)**：尺寸居中。

### 3. Disk（星系盘）— expdisk 模型

- **模型特性**：expdisk 是纯指数盘模型，没有 Sérsic 指数 n 参数。
- **尺寸参数 (R_s)**：请注意，expdisk 的第 4 项参数是标度长 (Scale length, $R_s$)，而非有效半径 ($R_e$)。
  - 换算关系：对于指数盘，有效半径与标度长的关系为 $R_e \approx 1.678 \times R_s$。
- **轴比与 PA**：通常反映星系整体在天空平面的倾角和投影方向。


1. sersic — 常用于 BULGE / Bar

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
1. expdisk  — 常用于 DISK 专为指数衰减的星系盘设计（等效于 n=1 的 Sersic 模型）。

0) expdisk                #  Component type
1) <x>  <y>  1 1          #  Position x, y
3) <mag>       1          #  Integrated magnitude
4) <R_s>       1          #  R_s (disk scale-length) [pix]
5) 0.0000      0          #  -----
6) 0.0000      0          #  -----
7) 0.0000      0          #  -----
8) 0.0000      0          #  -----
9) <b/a>       0          #  Axis ratio (b/a)
10) <PA>       0          #  Position angle (PA) [deg: Up=0, Left=90]
Z) 0                      #  Skip this model?

关键参数：R_s（盘标长）
- R_s（盘标长 Scale-length）：表面亮度下降 $e$ 倍（约 2.718 倍）的距离。它与有效半径 $R_e$ 的数学关系为：$R_e \approx 1.678 R_s$。初始化方法：如果你知道盘的半光半径（通过测光或肉眼估计盘的范围），除以 1.678 即可作为 R_s 的初始值。肉眼看的话，大概是盘的整体可见半径的 1/3 到 1/4 左右。

---
1. edgedisk — 常用于沿着视线方向几乎垂直观察的薄盘（$Z$ 轴方向的亮度分布）。

0) edgedisk               #  Component type
1) <x>  <y>  1 1          #  Position x, y
3) <mu0>       1          #  Mu(0) [mag/arcsec^2]
4) <h_s>       1          #  h_s (disk scale-height) [pix]
5) <R_s>       1          #  R_s (disk scale-length) [pix]
10) <PA>       1          #  Position angle (PA) [deg: Up=0, Left=90]
Z) 0                      #  Skip this model?

关键参数：h_s（标高）、R_s（标长）。注意 b/a 固定为 1。
- mu0（中心表面亮度）：同上，盘中心的表面亮度。
- h_s（标高 Scale-height）：代表盘的厚度。初始化方法：在 DS9 中测量侧向盘在垂直方向的可见厚度，取其 1/3 或 1/4 作为初始值。通常是一个很小的值（例如 2~10 像素，取决于图像分辨率）。
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
