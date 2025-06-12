# Greyhound 承诺



Greyhound 是一个基于lattice的polynomial commitment scheme（PCS）。对于degree为$N$ 的多项式，evaluation 证明的尺寸是$poly\log(N)$，证明的验证时间是$O(\sqrt{N})$。本文的主要目的是帮助读者理解Greyhound多项式承诺的方法，evaluation证明的做法，以及如何用Greyhound证明一个 $\mathbb{F}_q$ 上的多项式的求值。

### 1. 符号和相关背景

在介绍 Greyhound 的设计思路前，先引入一些符号。

设$d$是一个2的幂次，$\mathcal{R} = \mathbb{Z}[X]/(X^d + 1)$ 是 $2d$ 次分圆域的整环，用奇素数$q$定义环 $\mathcal{R}_q = \mathbb{Z}_q[X]/(X^d + 1)$，定义 $\delta = \lfloor \log q \rfloor$. 为了避免符号混淆，后文统一使用“向量”表示 $\mathcal{R}$ 或 $\mathcal{R}_q$ 上的多项式列向量。

对整数$n \geq 1$，定义一个用于二进制合成十进制的工具矩阵 $\mathbf{G}_n = \mathbf{I} \otimes [1 ~2~ 4~ \cdots~ 2^\delta] \in \mathcal{R}_q^{n \times n\delta}$ ，对应地，二进制分解用符号 $\mathbf{G}_n^{-1} ： \mathcal{R}_q^n \to  \mathcal{R}_q^{\delta n}$ 表示。

例对于一个向量 $\mathbf{t} \in \mathcal{R}_q^n$，符号$\mathbf{G}_n^{-1}(\mathbf{t})$表示，将 $\mathbf{t}$ 的系数全部分解成二进制数，再通过系数填充成的向量。
$\mathbf{G}_n$ 与 $\mathbf{G}_n^{-1}$是可逆的过程，有 $\mathbf{G}_n \mathbf{G}_n^{-1}(\mathbf{t}) = \mathbf{t}$.

> 例如，$\mathcal{R}_{10} = \mathbb{Z}_{10} [X]/(X^3+1)$，$\mathbf{t} = (t_1, t_2) = (6+2X+5X^2, 4+X+9X^2) \in \mathcal{R}_{10}^2$ ，定义$\delta = \lceil \log 10 \rceil = 4$。
> 那么 $\mathbf{G}_3^{-1}(\mathbf{t})$ 是先把$(6,5,1),(4,9,2)$ 全部写成二进制数$(0110,0010,0101,0100,1001,0010)$，然后填充成 $\mathcal{R}_q$ 上的向量 $\hat{\mathbf{t}} = (0+X+X^2, 0+0X+0X^2, 1+0X+0X^2, 1+0X+1X^2, 0+X+0X^2, 0+X+0X^2, 0+X+0X^2, 0+X+0X^2)\in \mathcal{R}^{2 \delta}$，即$\mathbf{G}_3^{-1}(\mathbf{t}) = \hat{\mathbf{t}}$. 
 对应地，矩阵 $$\mathbf{G}_3 = \begin{bmatrix} 1 & 2  & 2^3 & 2^4 & 0 &&&&&&\cdots&0\\ 0 & & \cdots &0 & 1 & 2  & 2^3 & 2^4 &0 && \cdots & 0\\ 0 & &\cdots & & & &  &0 & 1 & 2  & 2^3 & 2^4 \end{bmatrix}$$
 表示上述过程的逆运算，即 $\mathbf{G}_3 \hat{\mathbf{t}} = \mathbf{t} = (6+2X+5X^2, 4+X+9X^2) \in \mathcal{R}_{10}^2$.

#### Ajtai 承诺
此外，介绍SIS问题与Ajtai承诺的定义。

SIS问题定义为，给定一个公开矩阵 $\mathbf{A} \in \mathcal{R}_q^{n \times m}$，求解一个非零短向量 $\mathbf{z} \in \mathcal{R}_q^m$ 满足 $\mathbf{A}\mathbf{z}=\mathbf{0}, |\mathbf{z}|\leq B$.

对于一个二进制消息，通过系数填充将其填充成 $\mathcal{R}$ 上的向量 $\mathbf{m} \in \mathcal{R}^n$，Ajtai承诺过程如下：
- KeyGen  输入安全参数$\lambda$ ，生成承诺密钥 $\mathbf{A} \in \mathcal{R}_q^{n\times m}$
- Com 输入承诺密钥 $\mathbf{A} \in \mathcal{R}_q^{n\times m}$与二进制的消息$\mathbf{m} \in \mathcal{R}^m$， 计算承诺 $\mathbf{t} = \mathbf{Am}$.

关于Ajtai承诺，有3个点可以进一步讨论：1. 承诺的安全性，2. 承诺消息的范数和 3. 承诺值的压缩性质。

1. 承诺的binding性质基于 SIS 问题，如果一个恶意的攻击者想把承诺值 $\mathbf{t}$ 换成另一个消息的承诺 $\mathbf{t} = \mathbf{Am}'$，等价于找到SIS问题的解 $\mathbf{m-m'}$，满足 $\mathbf{0} = \mathbf{Am-m}', |\mathbf{m-m}'|_\infty \leq 2$.

2. 注意到，我们求出SIS问题的解能够满足$|\mathbf{m-m}'|_\infty \leq 2$，是因为我们要求了承诺的消息都是二进制的。这里要求消息为二进制数实际上是在约束 $\mathbf{m}$ 的范数（norm）比较小。在其他情况下也可以是 $\mathbf{m}$ 的范数小于某一个bound $B$，那么承诺的binding性质就会归约到bound为 $B$ 的解：$|\mathbf{m-m}'|_\infty \leq 2B$.

3. 承诺值的压缩性质体现在，承诺值 $\mathbf{t} \in \mathcal{R}_q^n$ 是 $\mathcal{R}_q$上的$n$维向量，与承诺的消息长度（$\mathcal{R}_q$ 上的 $m$ 维向量）无关，且在SIS问题的安全性定义下，承诺值的长度 $n<m$.


### 2. Greyhound的承诺方案

Greyhound承诺可以理解为一个两层Ajtai承诺。

假设要承诺一组（例如 $r$ 个）任意的向量 $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$。注意每个 $\mathbf{f}_i$ 都是一个$\mathcal{R}_q$上的$m$维向量，向量的每个分量为一个 $\mathcal{R}_q$ 上的元素。

承诺密钥为内层的公开矩阵 $\mathbf{A}\in \mathcal{R}_q^{n\times m\delta}$ 与外层的公开矩阵 $\mathbf{B} \in \mathcal{R}_q^{n \times r n \delta}$.

- 内层承诺：在上一节提到Ajtai承诺的消息应当为二进制字符串。因此，要使用Ajtai承诺对 $\mathbf{f}_1, \dots, \mathbf{f}_r$ 承诺，首先需要利用进制转化的工具矩阵 $\mathbf{G}^{-1}$ 将这组向量转化成二进制的向量$\mathbf{s}_i \in \mathcal{R}_q^{m \delta}$，即 $\mathbf{s}_i = \mathbf{G}_m^{-1}(\mathbf{f}_i)$。现在，可以对消息$\mathbf{s}_i$做Ajtai承诺： $$\mathbf{t}_i := \mathbf{As}_i = \mathbf{AG}^{-1}_m(\mathbf{f}_i)$$
这样，可以得到 $r$ 个消息$\mathbf{f}_1, ...,\mathbf{f}_r$ 的承诺值 $\mathbf{t}_1, ..., \mathbf{t}_r \in \mathcal{R}_q^n$.

- 外层承诺：内层承诺完成后，我们得到了 $r$ 个向量$\mathbf{t}_1, ..., \mathbf{t}_r \in \mathcal{R}_q^n$ ，目前的承诺值与消息的长度（$r$ 组 长度为$m$ 的向量），即$\mathcal{O}(mr)$ 是亚线性的关系。为了获得更压缩的承诺值，即$\mathcal{O}(1)$，我们希望对内层承诺值 $\mathbf{t}_1, ..., \mathbf{t}_r$ 再做一次Ajtai承诺。可以通过把 $\mathbf{t}_1, ..., \mathbf{t}_r$ 看成承诺消息，重复上面的过程来完成。首先使用 $\mathbf{G}^{-1}$ 将 $\mathbf{t}_1, ..., \mathbf{t}_r$ 转化成二进制系数的向量 $\hat{\mathbf{t}}_i = \mathbf{G}^{-1}(\mathbf{t}_i)$ ，然后计算外层承诺值： $$\mathbf{u} := \mathbf{B}\begin{bmatrix} \hat{\mathbf{t}}_1 \\ \vdots \\ \hat{\mathbf{t}}_r \end{bmatrix} \in \mathcal{R}_q^n$$
最后，对一组向量 $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$ 的承诺就是向量 $\mathbf{u} \in \mathcal{R}_q^n$.


### 3. Greyhound承诺的多项式求值

在上一节我们只讨论了如何承诺一组向量 $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$，但我们的目标是构造一个PCS，所以需要讨论这组向量与一个要做evaluation的多项式 $f(\mathsf{X}) = \sum_{i=0}^{N-1} f_i \mathsf{X}^i \in \mathcal{R}_q^{<N}[\mathsf{X}]$ 之间的关系。

需要注意的是， $\mathsf{X}$ 是多项式 $f$ 的变量，与$\mathcal{R} = = \mathbb{Z}[X]/(X^d + 1)$ 中的 $X$ 没有关系。

假设 $N=m \cdot r$，我们希望证明多项式 $f$ 在点 $x \in \mathcal{R}_q$ 的求值为$y$, 即 $f(x) = \sum_{i=0}^{N-1} f_i x^i =  y$.

类似mercury，我们可以把上述求值过程用矩阵和向量的乘法表示：
$$f(x) = [1~x~x^2~\cdots~x^{m-1}] \begin{bmatrix} f_0 & f_m & \cdots & f_{(r-1)m} \\ f_{1} & f_{m+1} &\cdots & f_{(r-1)m+1} \\ f_{2} & f_{m+2} &\cdots & f_{(r-1)m+2} \\ &&\cdots& \\ f_{m-1} & f_{2m-1} &\cdots & f_{rm-1} \end{bmatrix} \begin{bmatrix} 1 \\ x^m \\ (x^m)^2\\ \vdots \\ (x^m)^r \end{bmatrix}.$$


因此，如果定义向量 $\mathbf{f}_i = [ f_{(i-1)m}, f_{(i-1)m+1}, ... , f_{im-1}] \in \mathcal{R}_q^m$，为多项式 $f$ 的系数组成的一组向量，那么，对$\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$的承诺就是对多项式 $f$ 的承诺。

现在，我们定义向量 $\mathbf{a}^\top = [1~x~x^2~\cdots~x^{m-1}]$ 与 $\mathbf{b}^\top = \begin{bmatrix} 1 ~ x^m ~\dots ~ (x^m)^r \end{bmatrix}$ ，那么多项式 $f$ 的求值可以表示为 $$f(x) = \mathbf{a}^\top [\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{b}.$$

### 4. 多项式求值的证明

多项式求值的证明包括2点：1. 多项式的承诺是正确计算的；2. 多项式求值的运算是正确的。

1. 首先一个证明者需要对多项式 $f$ 按照1.1节的方式做承诺，那么证明承诺计算的正确性，即证明：
$$\begin{align*} \mathbf{s}_i &= \mathbf{G}^{-1}_m(\mathbf{f}_i), \\ \mathbf{t}_i &= \mathbf{G}_n\hat{\mathbf{t}}_i = \mathbf{As}_i,  \\ \mathbf{u} &= \mathbf{B}\begin{bmatrix} \hat{\mathbf{t}}_1 \\ \vdots \\ \hat{\mathbf{t}}_r \end{bmatrix}. \end{align*} $$

由于$\mathbf{G}$的转化是可逆的，第一个等式也可以写成 $\mathbf{f}_i = \mathbf{G}_m \mathbf{s}_i$.

2. 证明多项式求值的正确性，即证明：$$f(x) = \mathbf{a}^\top [\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{b}.$$

Greyhound 证明以上4个等式的思路是，由证明者计算与多项式 $\mathbf{f}_i$ 直接相关的部分，由验证者计算其余部分。我们先展示证明过程，再来讨论这个证明思路。

假设协议的公开参数为承诺密钥$\mathbf{A,B}$，承诺$u$与多项式$f$. 整个协议由2轮交互组成：

1. 证明者首先计算$f(x)$的前半部分，发送 $\mathbf{w}$ 给验证者：
$$ \mathbf{w}^\top := \mathbf{a}^\top[\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r]. $$

2. 验证者选择一个随机挑战向量 $\mathbf{c} = (c_1, ..., c_r) \in \mathcal{R}_q^r$ 发送给证明者。

3. 证明者发送中间承诺 $(\hat{\mathbf{t}}_1, ...,\hat{\mathbf{t}}_r)$， 使用 $\mathbf{c}$ 对$\mathbf{s}_i$ 做线性组合： $\mathbf{z} := [\mathbf{s}_1 ~ \cdots~ \mathbf{s}_r] \mathbf{c} =  \mathbf{s}_1c_1 + ... +\mathbf{s}_r c_r\in \mathcal{R}_q^m$.

最后，验证者使用证明者发送的所有信息$\mathbf{w}, \hat{\mathbf{t}}_i, \mathbf{z}$，验证以下的等式是否成立：

$$
\begin{align}
\mathbf{w}^\top \mathbf{b} &= y, \\
\mathbf{w}^\top \mathbf{c} &= \mathbf{a}^\top \mathbf{G}_m \mathbf{z},\\
\mathbf{Az} & = c_1\mathbf{G}_n \hat{\mathbf{t}}_1 + \cdots + c_r \mathbf{G}_n \hat{\mathbf{t}}_r,\\
\mathbf{u} &= \mathbf{B}\begin{bmatrix} \hat{\mathbf{t}}_1 \\ \vdots \\ \hat{\mathbf{t}}_r \end{bmatrix}.
\end{align}
$$

第一个等式实际上是在验证多项式 $f(x)$ 求值运算的后半部分，因为如果 $\mathbf{w}$ 是正确的（这由第二个等式保证），那么 $$f(x) = \mathbf{a}^\top[\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{b}  = \mathbf{w}^\top \mathbf{b} = y.$$

第二个等式在挑战向量 $\mathbf{c}$ 的参与下验证了$f(x)$求值运算前半部分的正确性 

$$
\begin{align*} \mathbf{w}^\top \mathbf{c} &= \mathbf{a}^\top [\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{c} \\ & = \mathbf{a}^\top \mathbf{G}_m [\mathbf{s}_1~ \cdots ~\mathbf{s}_r] \mathbf{c} \\
& = \mathbf{a}^\top \mathbf{G}_m \mathbf{z}
\end{align*}.
$$

第三个等式验证了PCS内层承诺的正确性 

$$
\begin{align*} \mathbf{Az} & = \mathbf{A s}_1 c_1 + ... +  \mathbf{A s}_r c_r\\ &= c_1\mathbf{G}_n \hat{\mathbf{t}}_1 + \cdots + c_r \mathbf{G}_n \hat{\mathbf{t}}_r. \\
\end{align*}
$$

第四个等式验证了PCS的外层承诺。

这个证明可以进一步使用 Labrador 的递归证明来优化证明尺寸，通过把 (1) 中的等式改写成 Labrador 证明的标准形式，具体细节请参考Greyhound文档。

### 5. 使用 $\mathcal{R}_q$ 证明 $\mathbb{F}_q$ 上的多项式求值

在之前的介绍中，我们忽略了一个重要的问题：就是所有的运算与证明都是在 $\mathcal{R}_q$ 上执行的，而大部分实际应用都是用$\mathbb{F}_q$ 上的多项式。本节讨论如何将 $\mathbb{F}_q$ 上的多项式等价表示为 $\mathcal{R}_q$ 上的多项式，进而使用前几节的证明方法。

从 $\mathbb{F}_q$ 到 $\mathcal{R}_q$ 的转化需要把 $\mathbb{F}_q$ 上的向量通过系数填充填充到 $\mathcal{R}_q$ 上，然后利用 $\mathcal{R}_q$ 上的运算表示 $\mathbb{F}_q$ 上的运算。

定义一种自同构映射 $\sigma: \mathcal{R}_q \to \mathcal{R}_q$，该映射把 $\mathcal{R}_q$ 上的元素映射到负幂次，$\sigma{X} = X^{-1}$.  例如，$a = a_0 + \sum_{i=1}^{d-1} a_i X^i \in \mathcal{R}_q$，那么 $\sigma(a) = a_0 +\sum_{i=1}^{d-1} a_i X^{-i} \in \mathcal{R}_q$. 
在 $\mathcal{R}_q$ 上，$a\sigma{a}$的常数项为：$a_0 a_0 + \sum_{i=1}^{d-1} a_i a_i = \sum_{i=0}^{d-1} a_i a_ic$，即 $a$ 中的项 与 $\sigma(a)$ 中的项乘积不包含$X$的所有项求和。

先明确以下符号：$\mathbb{F}_q$ 上的多项式记为 $F(U) = \sum_{i=0}^{N'-1} F_i U^i = V \in \mathbb{F}_q$， $\mathcal{R}_q$ 上的多项式记为 $f(x) = \sum_{i=0}^{N-1} f_i x^i =  y \in \mathcal{R}_q$，我们用$f$表示$F$通过系数填充到$\mathcal{R}_q$上的多项式。 为了区分，我们用 $N-1$ 表示 $f$ 的多项式次数，$N'-1$ 表示  $F$ 的次数。经过系数填充后，$N$ 与 $N'$是不相等的。

- 当 $N' \leq d$ 时， 不失一般性地，我们讨论 $N'=d$，当 $N' < d$时，我们可以通过对 $F$ 填充 $0$ 让 $N'=d$ 成立。此时只需要一个$\mathcal{R}_q$上的元素就可以存储 $F$ 的所有系数，因此 $N = 1$。

我们定义$F$系数填充后的求值式为 $f(x) = f_0 \sigma(x)$ .
这里的 $f_0 = \sum_{i=0}^{d-1} F_i X^i \in \mathcal{R}_q$ 是$F$ 的所有系数$(F_0, ..., F_{N'-1})$ 通过系数填充得到的，$\sigma(x)$ 是 $F$ 的求值点 $U$ 的所有幂次 $(1, U, ..., U^{N'-1})$，先通过系数填充到$x = \sum_{i=0}^{d-1} U^i X^i\in \mathcal{R}_q$ ，再做 $\sigma$ 映射得到的， $\sigma(x) = 1+ \sum_{i=1}^{d-1} U^i X^i \in \mathcal{R}_q$。 
需要再次提醒的是，此处的 $X$ 是$\mathcal{R}_q$ 中的符号，没有实际意义。

那么，利用上面讨论的 $\sigma$ 映射，$f(x) = f_1 \sigma(x)$ 的常数项为 $$\sum_{i=0}^{N'-1} F_i U^{i} = V.$$这意味着，一个Greyhound的验证者可以通过检查 $f(x)$ 的常数项是否为 $V$ 来检查$F(U) = V$是否成立。

- 当 $N' > d$ 时，我们讨论 $N' = Nd$. 此时，$F$ 的系数 $(F_0, ..., F_{N'-1})$ 会填充到 $N$ 个 $\mathcal{R}_q$ 上的元素 $f_0, f_1 ..., f_{N-1} \in \mathcal{R}_q$，但是多项式$f(x)$的运算方法与 $N'=d$ 时是类似的。

我们只需要把 $F$ 的系数依次填充到 $(f_0, f_1 ..., f_{N-1})$， 再把 $(1, U, ..., U^{N'-1})$ 依次填充到 $x_1, x_2, ..., x_N \in \mathcal{R}_q$， 然后定义$$f(x) = \sum_{i=0}^{N} f_i x_i.$$

那么，$f(x)$ 中 $f_i$ 与 $x_i$ 的乘法运算会分段地将$\sum_{j=0}^{d} F_{id+j}{U^{id+j}}$ 保存在 $f_i x_i$ 的常数项中，这与先前的讨论类似。
由于 $\mathcal{R}_q$ 上的加法运算是对应系数相加，那么外层从 $i=0$ 到 $N$ 的加法运算 $\sum_{i=0}^{N-1} f_i x_i$ ，会把各个常数项中的 $\sum_{j=0}^{d} F_{id+j}{U^{id+j}}$进一步合并起来，即 $f(x)$的常数项为 $$\sum_{i=0}^{N-1} \sum_{j=0}^{d} F_{id+j}{U^{id+j}} = \sum_{i=0} ^{N'-1} F_i U^i = V.$$

现在，我们已经可以使用greyhound对任意的 $\mathbb{F}_q$ 上的多项式做承诺，以及证明它们的evaluations了，感谢阅读致此。


---
参考文献
[1] Ngoc Khanh Nguyen, Gregor Seiler: Greyhound: Fast Polynomial Commitments from Lattices. CRYPTO (10) 2024: 243-275.











