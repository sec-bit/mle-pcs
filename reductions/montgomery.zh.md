# Montgomery Reduction

在有限域运算中，我们需要频繁使用mod N运算。对于涉及连乘的指数运算，Montgomery Reduction能提供更好的性能优化。

Montgomery Reduction的核心思想是将运算数转换到一个特殊的Montgomery Form，其所有的除法运算都可以被显著简化。

让我们通过一个具体例子来理解：

设模数 N = 97，我们需要计算 $(a \cdot b) \bmod N$。传统方法需要对$a \cdot b$的结果进行求余运算，这涉及到开销较大的除法运算。

### Montgomery Form转换
1. 选择R = 100（通常选择为2的幂，这里为便于演示选用100，我们仅需在10进制下取尾数和抹除尾部的00即可）
2. 对于输入 a = 15, b = 32：
   - $T_a = aR \bmod N = 45$
   - $T_b = bR \bmod N = 96$

### Montgomery乘法过程
1. 计算Montgomery Form的乘积：
   $T_r = T_a \cdot T_b = 45 \cdot 96 = 4320$

2. 结果转换：
   - 由于经过了两次Montgomery Form转换，结果包含 $R^2$ 项，需要消除一个 $R$
   - 我们需要在不改变 $mod N$ 结果的情况下调整 $T_r$ ，使其能被 $R$ 整除
   - 我们可以给T加上若干次 $N$ ，这样$mod N$的结果仍然不会被影响，于是我们有了 $T + xN$
   - 我们又需要合适的x，使得 $T + xN$ 能被 $R$ 整除
   - 通过同余等式 $T + xN \equiv 0 \pmod{R}$，即 $x = T \cdot (-\frac{1}{N}) \bmod R$
   - 我们把 $-\frac{1}{N}$ 记为 $N'$，$N' = -\frac{1}{N} \bmod R = 67$（提前计算）
   - 上面求得的 $x$ 即为Montgomery Reduction中的 $m$, $t = T + mN$

3. 具体计算：
   第一次Montgomery Reduction ($aR \cdot bR/R$)：

   $m = T_r \cdot N' \bmod R = 4320 \cdot 67 \bmod 100 = 289440 \bmod 100 = 40$
   （注：mod 100在10进制下就是取2位尾数）

   $t = (T_r + m \cdot N) / R = (4320 + 40 \cdot 97) / 100 = 8200 / 100 = 82 = abR$ 
   （注：除以100在10进制下就是抹掉尾部的00）

   第二次Montgomery Reduction ($abR/R$)：

   $m' = t \cdot N' \bmod R = 82 \cdot 67 \bmod 100 = 94$

   $t' = (t + m' \cdot N) / R = (82 + 94 \cdot 97) / 100 = 92 = ab$

### 优势分析
虽然单次运算时Montgomery Reduction似乎并未节省太多计算资源（转换到Montgomery Form时仍需mod N运算），但在需要连续模乘运算的场景下（如模幂运算），其优势就非常明显：

1. 模幂运算示例：计算 $a^5 \bmod N$
   - 传统方法需要在每次乘法后进行mod N运算
   - 使用Montgomery Form后：
     - 初始转换：$T_a = aR \bmod N$
     - 中间运算无需除法：$T_a \cdot T_a / R = (aR \cdot aR) / R = a^2R$
     - 只需在最后转换回原始形式

2. 主要优势：
   - 避免中间步骤的mod N运算
   - 消除大部分除法运算
   - 适合硬件实现（R选择2的幂时，除法和取模都可以用移位和位与运算完成）
   - 特别适合需要连续模乘运算的场景

### 工程实现
在实际工程中，我们通常通过将元素a乘以$R^2$来将其编码到Montgomery Form。这种方式的优点是：

1. Montgomery Reduction和乘法可以合并为统一的mul函数：
   - $\text{mul}(a, b) = ab/R$

2. 这样encode和decode都可以用同一个mul函数：
   - $\text{encode}(a) = \text{mul}(a, R^2) = aR^2/R = aR$
   - $\text{decode}(T_a) = \text{mul}(T_a, 1) = aR/R = a$

这种统一的实现方式使代码更简洁，同时当R选择为2的幂时，所有的除法和取模运算都可以通过移位和位与运算高效完成。

对于模幂运算，我们可以看到Mont乘的优势：
1. 传统算法：
   $a^5 = ((((a \cdot a) \bmod N) \cdot a) \bmod N) \cdot a) \bmod N) \cdot a) \bmod N$
   每一步都需要进行昂贵的除法运算来求余

2. Montgomery算法：
   - $T_a = aR \bmod N$
   - $T_a \cdot T_a / R = a^2R$
   - $(a^2R \cdot aR) / R = a^3R$
   - $(a^3R \cdot aR) / R = a^4R$
   - $(a^4R \cdot aR) / R = a^5R$
   - $\text{decode}(a^5R) = a^5$

所有中间步骤都只需要简单的移位操作，大大提升了性能。