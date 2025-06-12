# Ligerito-PCS 笔记

Yu Guo <yu.guo@secbit.io>

最后更新时间：2025-06-05

Ligerito [NA25] 是在 Ligero [AHIV17] 基础上，模仿 FRI 协议进行递归证明的 MLE 多项式承诺方案。在理解过 Ligerito 协议之后，我发现它的递归协议调用的思路与 FRI 协议类似，在协议中加入 Paritial Sumcheck 协议的思路应该是源于 Basefold。在递归调用过程中的 Sumcheck 协议可以和上一次迭代中的 Paritial Sumcheck 协议可以进行合并，这一思路与 Whir 协议中对 Shift Queries 的处理几乎一摸一样。在论文第 13 页中的 Discussion 一节中，作者这么写道：

> Remco Bloemen and Giacomo Fenzi have commented that this protocol is structurally similar to the WHIR protocol of [ACFY24], though we note that Ligerito uses general linear codes, the logarithmic randomness of [DP24], and as far as we can tell, results in concretely different (and smaller) numbers in the unique decoding regime. A natural open question is whether there is a simple generalization of both protocols that can recast them in a common framework.

本文带着大家概览下 Ligerito 协议的核心思想，并对比下和 Whir 协议的在表述上有哪些不同点。最后，笔者感觉两者没有实质上的差别，尽管两个协议设计的路径不同，但最终的协议在核心流程上几乎一样。Whir 此外增加了 Out-of-domain Query 的步骤，并且有在迭代过程中倾向使用更大的 Domain 去计算中间多项式的 RS Code，目的是提高码率，降低 Query 次数。

> 思路:
> 1. 回顾 Ligero 协议
> 2. Sumcheck 的关键作用
> 3. 递归调用


## 1. Ligero 

我们通过一个简单的例子来过一遍 Ligero 协议的流程，方便读者快速理解这个协议。这里假设一个仅有四个变量的 MLE 多项式，其定义如下：

$$
f(x_0, x_1, x_2, x_3) = \sum_{i=0}^{2^4-1} a_i \cdot eq(\mathsf{bits}(i), (x_0, x_1, x_2, x_3))
$$

其中向量 $\vec{a}=(a_0, a_1, \cdots, a_{15})$ 为 $f$ 多项式在 4 维 Boolean Hypercube ($\{0, 1\}^4$) 上的运算求值。

### 计算承诺

我们可以把这个向量 $\vec{a}$ 重新排布成一个 $4\times 4$ 的矩阵，记为 $A$：

$$
A=
\begin{bmatrix}
a_0 & a_1 & a_2 & a_3 \\
a_4 & a_5 & a_6 & a_7 \\
a_8 & a_9 & a_{10} & a_{11} \\
a_{12} & a_{13} & a_{14} & a_{15}
\end{bmatrix}
$$

我们用一个线性编码，$C[\mathbb{F}, 4, 8]$，与之相关联的生成矩阵 $G\in\mathbb{F}^{4\times 8}$ ，它对矩阵的每一个行向量进行编码（这个编码方案的码率为 $1/2$）：

$$
\mathsf{enc}(a_0, a_1, a_2, a_3) = 
\begin{bmatrix}
a_0 & a_1 & a_2 & a_3
\end{bmatrix}
G
$$

我们可以选择 RS Code 当然也可以选择任何定义在有限域 $\mathbb{F}_q$ 上的线性编码。
在上面的编码例子中，$\mathsf{enc}(a_0, a_1, a_2, a_3)$ 的计算结果为长度为 8 的行向量，我们暂且记为 $(e_0, e_1, e_2, e_3, e_4, e_5, e_6, e_7)$。依此，我们用 $G$ 对 A 的所有行进行编码，即可计算得到编码后的矩阵 $B$，其大小为 $4\times 8$：

$$
B= AG =
\begin{bmatrix}
e_0 & e_1 & e_2 & e_3 & e_4 & e_5 & e_6 & e_7 \\
e_8 & e_9 & e_{10} & e_{11} & e_{12} & e_{13} & e_{14} & e_{15} \\
e_{16} & e_{17} & e_{18} & e_{19} & e_{20} & e_{21} & e_{22} & e_{23} \\
e_{24} & e_{25} & e_{26} & e_{27} & e_{28} & e_{29} & e_{30} & e_{31}
\end{bmatrix}
$$

与任何的基于 Hash 的 PCS 协议一样，我们用 Merkle Tree 对 $B$ 进行承诺计算。不过这里我需要强调，我们采用一种列优先（Column-wise）的方式来对 $B$ 进行承诺。即首先把矩阵的每一列作为一颗 Merkle Tree 的叶子结点，然后计算它的根。这样我们可以得到关于 $B$ 矩阵的 $8$ 个 Merkle Tree 的根：

$$
\begin{aligned}
\mathsf{t}_0 &= \mathsf{MerkleRoot}(e_0, e_8, e_{16}, e_{24}) \\
\mathsf{t}_1 &= \mathsf{MerkleRoot}(e_1, e_9, e_{17}, e_{25}) \\
\vdots \\
\mathsf{t}_7 &= \mathsf{MerkleRoot}(e_7, e_{15}, e_{23}, e_{31}) \\
\end{aligned}
$$

然后我们再把这 8 个根作为一颗新的 Merkle Tree 的叶子节点，计算它们的根，

$$
\mathsf{t} = \mathsf{MerkleRoot}(\mathsf{t}_0, \mathsf{t}_1, \cdots, \mathsf{t}_7)
$$

最后，我们得到的 $\mathsf{t}$ 就是 $B$ 的承诺。当然，我们上面的承诺计算方式，也可以看成是把矩阵 $B$ 按列进行展开成一个一维的长度为 $32$ 的列向量，然后把它们依次看成是 Merkle Tree 的叶子结点，然后计算它的根，也可以得到相同的值 $\mathsf{t}$。

### 证明随机点求值的正确性

Prover 可以按照上面的方式提前 Commit 一个 MLE 多项式，并且发送其承诺 $\mathsf{t}$ 给 Verifier。然后 Verifier 就可以随机挑选一个点（$r_0, r_1, r_2, r_3$），并发送给 Prover，Prover 返回值 $v$，并附带一个证明 $\pi_{eval}$，证明求值过程的正确性：

$$
\pi_{eval}: v=f(r_0, r_1, r_2, r_3)
$$

我们快速过一下 Ligero 的思路。

**第一步**：Prover 计算 $B$ 与它的承诺 $\mathsf{t}$，并发送给 Verifier。

**第二步**：Verifier 随机选取一个随机点 $(r_0, r_1, r_2, r_3)\in\mathbb{F}_q^{4}$，并发送给 Prover。

**第三步**：Prover 利用 $r_3, r_2$ 对矩阵 $A$ 的所有「行」进行「纵向折叠」，并发送计算得到折叠后的行向量 $\vec{a}'$：

$$
\vec{a}' = 
\begin{bmatrix}
(1-r_2)(1-r_3) & r_2(1-r_3) & r_3(1-r_2) & r_2r_3 \\
\end{bmatrix}
\begin{bmatrix}
a_0 & a_1 & a_2 & a_3 \\
a_4 & a_5 & a_6 & a_7 \\
a_8 & a_9 & a_{10} & a_{11} \\
a_{12} & a_{13} & a_{14} & a_{15}
\end{bmatrix}
$$

这里需要注意的是，因为矩阵总共有 $4$ 行，而 Prover 仅需要两个随机数就可以折叠 4 行，这是因为我们可以利用 $k$ 个随机数来构造 $2^k$ 个线性不相关的值：

$$
\bar{r} = (1-r_2, r_2) \otimes (1-r_3, r_3)
$$

我们借助 Ligerito 论文的符号 $\bar{r}$ 表示用 $\log{n}$ 多个随机因子来构造 $n$ 个线性不相关的值的向量，这个思路源于论文 [DP24]。这里 $\otimes$ 表示 Kronecker 积。如果我们展开， $\bar{r}$ 的表达式可以写成：

$$
\bar{r} = 
\begin{bmatrix}
(1-r_2)(1-r_3) & 
(1-r_2)r_3 &
r_2(1-r_3) &
r_2r_3
\end{bmatrix}
$$

上面写的数学符号如果并不容易理解，我们下面采用更形象的方式来解释这个 $\vec{a}'$ 的计算过程。

我们先引入一个新的符号 $\mathsf{fold}(r, \vec{c})$，它表示将列向量 $\vec{c}$ 用一个随机数 $r$ 进行折叠，即：

$$
\mathsf{fold}(r, (c_0,c_1,c_2,\ldots, c_7)^T) = 
\begin{bmatrix}
(1-r)\cdot c_0 + r\cdot c_4 \\
(1-r)\cdot c_1 + r\cdot c_5 \\
(1-r)\cdot c_2 + r\cdot c_6 \\
(1-r)\cdot c_3 + r\cdot c_7
\end{bmatrix}
=\begin{bmatrix}
c_0' \\
c_1' \\
c_2' \\
c_3'
\end{bmatrix}
=\vec{c}'
$$

这个 fold 函数可以理解成把向量对半拆分成两部分，然后将前一半乘上 $(1-r)$ 因子，后一半乘上 $r$ 因子，然后将两个向量对位相加，得到一个长度为之前一半的列向量。

如果我们继续对上面折叠后的向量，记为 $\vec{c}'=(c_0', c_1', c_2', c_3')^T$ 继续采用一个新随机数 $r'$进行折叠：我们可以得到：

$$
\mathsf{fold}(r', \vec{c}') = 
\begin{bmatrix}
(1-r')\cdot c_0' + r'\cdot c_2' \\
(1-r')\cdot c_1' + r'\cdot c_3' \\
\end{bmatrix}
= 
\begin{bmatrix}
(1-r')(1-r)\cdot c_0 + (1-r')r\cdot c_4 + r'(1-r)\cdot c_2 + r'r\cdot c_6 \\
(1-r')(1-r)\cdot c_1 + (1-r')r\cdot c_5 + r'(1-r)\cdot c_3 + r'r\cdot c_7 \\
\end{bmatrix}
= \vec{c}''
$$

我们如果允许$\mathsf{fold}$ 可以复合，那么我们用下面的表示复合的折叠：

$$
\mathsf{fold}(r', r, \vec{a}) = \mathsf{fold}(r', \mathsf{fold}(r, \vec{a}))
= \vec{a}''
$$

继续我们的例子，这时我们可以借助 $\mathsf{fold}$ 函数将 $\vec{a}'$ 的计算过程写成：

$$
\vec{a}' = 
\begin{bmatrix}
\mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\mathsf{fold}(r_2, r_3, (a_1, a_5, a_9, a_{13})) \\
\mathsf{fold}(r_2, r_3, (a_2, a_6, a_{10}, a_{14})) \\
\mathsf{fold}(r_2, r_3, (a_3, a_7, a_{11}, a_{15}))
\end{bmatrix}
$$

**第四步**：Verifier 抽样 $Q\subset\{0, 1, 2, \ldots, 7\}$，并发送给 Prover。

$$
Q = \{q_0, q_1, \ldots, q_{l-1}\}
$$

Verifier 随机抽样的目的是检查 Prover 是否诚实地按照 $\mathsf{fold}(r2,r_3,\cdot)$ 函数来计算 $\vec{a}'$。由于线性编码具有 **Proximity Gap** 的神奇性质，折叠后的线性编码要么仍然是一个正确的编码，要么极大概率距离一个正确的编码很远。所谓编码距离是衡量两个码字之间不同元素的数量的度量，也被称为 Hamming Distance。这样 Verifier 可以只抽样少量的码字中的位置，来检查折叠过程是否正确即可。当然 Verifier 抽样越多越安全，但是抽样越多，证明通讯量（Proof Size）就越大。我们一般可以通过概率公式来保证安全性的前提下，采用最少的抽样次数。这里我们把抽样次数记为 $l$。

**第五步**：Prover 回应 Verifier 的随机抽样，发送 $Q=\{q_i\}$ 中每一个查询点 $q_i$ 所对应的 $B$ 的列向量，记为 $\vec{b}_{q_i}$，以及它们所对应的 Merkle Tree 的根，即 $\mathsf{t}_{q_i}$；还有 $\mathsf{t}_{q_i}$ 在 $\mathsf{t}$ 上的 Merkle Path $\pi_{q_i}$。

例如 $q_0=2$，那么，Prover 要发送 $(e_2, e_{10}, e_{18}, e_{26})$，以及它们的 Merkle Root $\mathsf{t}_{2}$；还有 $\mathsf{t}_{2}$ 在 $\mathsf{t}$ 上的 Merkle Path。

**验证步**：Verifier 需要验证下面的等式是否成立：

1. 所有的 $\mathsf{t}_{q_i}$ 都与 $\mathsf{t}$ 一致，即
$$
\mathsf{t}_{q_i} \overset{?}{=} \mathsf{MerkleRoot}(\vec{b}_{q_i}), \quad \forall q_i\in Q
$$

2. $t_{q_i}$ 是否属于 $\mathsf{t}$ 的叶子，即

$$
\mathsf{MerkleTree.verify}(\mathsf{t}, \mathsf{t}_{q_i}, \pi_{q_i}) \overset{?}{=} 1, \quad \forall q_i\in Q
$$

3. 计算 $\vec{b}_{q_i}$ 的折叠是否与编码 $\vec{a}'G$ 的对应点一致，即

$$
\mathsf{fold}(r_2, r_3,\vec{b}_{q_i}) \overset{?}{=} \vec{a}'^TG_{q_i}, \quad \forall q_i\in Q
$$

这里 $G_{q_i}$ 表示生成矩阵 $G$ 的第 $q_i$ 列。

4. 验证 $\vec{a}'$ 向量

$$
\vec{a}'^T\cdot\big((1-r_0,r_0)\otimes(1-r_1,r_1)\big)\overset{?}{=}v
$$

至此，如果上面四个检查步骤都通过，Verifier 则接受证明：

$$
\pi_{eval}:f(r_0, r_1, r_2, r_3) = v
$$

## 2. Sumcheck 的关键作用

上一节的协议有一个明显的问题，那就是 Verifier 必须在 Prover 承诺 $f$ 多项式之后才能给出，而且这个求值点必须是一个足够随机的点，不能是一个事先公开的点。这样造成上面协议其实并不满足多项式承诺的一般性应用场景。我们希望协议可以支持 MLE 多项式在任意的，甚至不随机的点上求值。

这就我们需要引入 Sumcheck 协议。具体地说，我们在 Ligero 协议的基础之上，只需要引入一个**部分运行**的 Sumcheck 子协议，就能完成一个 MLE 多项式的在任意点求值证明。这个思路实际上是来源于 Basefold [ZCF23]。这里我们假设读者已经熟悉 Sumcheck 协议，或者请读者参考我们之前写的文章。(TODO)

我们仍然采用之前的仅有四个未知数的 MLE 多项式 $f$，但是想让 Prover 证明 $f$ 在任意点 $\vec{u}=(u_0, u_1, u_2, u_3)$ 上的求值。根据 MLE 多项式的定义，它可以唯一地表示为 $(a_0, a_1, a_2, \ldots, a_{15})$ 在 Boolean Hypercube 上的插值多项式：

$$
f(u_0, u_1, u_2, u_3) = \sum_{\vec{b}\in\{0,1\}^4} f(b_0,b_1,b_2,b_3) \cdot eq\big((b_0, b_1, b_2, b_3), (u_0, u_1, u_2, u_3)\big)
$$

我们再次强调： $\vec{u}=(u_0, u_1, u_2, u_3)$ 是一个事先公开的任意给定的点。上面等式中的 $eq(\vec{b}, \vec{u})$ 是 Lagrange 多项式，定义为：

$$
eq(\vec{b}, \vec{u}) = \prod_{i=0}^{n-1} \big((1-b_i)(1-u_i) + b_i\cdot u_i\big)
$$

其中 $n$ 表示 BooleanHypercube 的维度，这里 $n=4$。如果我们固定 $\vec{b}\in\{0,1\}^4$，那么我们引入一个记号 $w_i$，表示 $eq(\mathsf{bits}(i), \vec{u})$，即

$$
w_i = eq(\mathsf{bits}(i), (u_0, u_1, u_2, u_3))
$$

到此为止，我们可以看到下面的等式成立：

$$
f(u_0, u_1, u_2, u_3) = \sum_{i=0}^{2^4-1} a_i \cdot w_i
$$

上面我们说过 $\vec{a}=(a_0, a_1, a_2, \ldots, a_{15})$ 是 $f$ 在 4 维 Boolean Hypercube 上的取值：

$$
\vec{a} = \begin{bmatrix}
f(0,0,0,0) \\
f(1,0,0,0) \\
f(0,1,0,0) \\
f(1,1,0,0) \\
\vdots \\
f(1,1,1,1)
\end{bmatrix}
$$

即

$$
a_i=f(\mathsf{bits})
$$

鉴于 $f(u_0, u_1, u_2, u_3)$ 可以表示为一个求和式，即$\vec{a}$ 和 $\vec{w}$ 的内积，于是我们可以考虑采用 Sumcheck 协议来证明这个内积运算。

$$
f(u_0, u_1, u_2, u_3) = \sum_{\vec{b}\in\{0,1\}^4} f(b_0, b_1, b_2, b_3) \cdot \tilde{w}(b_0, b_1, b_2, b_3)
$$

其中 $\tilde{w}$ 为 $\vec{w}$ 所对应的 MLE 多项式。Sumcheck 协议的一轮可以将上面的内积等式 Reduce 到一个长度减半的内积等式。例如，当 Prover 和 Verifier 仅进行一轮的 Sumcheck 协议后，我们得到一个长度为 8 的求和等式：

$$
f(u_0, u_1, u_2, {\color{red}r_3}) = \sum_{\vec{b}\in\{0,1\}^3} f(b_0, b_1, b_2, {\color{red}r_3}) \cdot \tilde{w}(b_0, b_1, b_2, {\color{red}r_3})
$$

这里 $r_3$ 是 Verifier 在第一轮 Sumcheck 交互中随机产生的挑战值。如果再来一轮，这个求和等式的长度会进一步减半：

$$
f(u_0, u_1, {\color{red}r_2}, r_3) = \sum_{\vec{b}\in\{0,1\}^2} f(b_0, b_1, {\color{red}r_2}, r_3) \cdot \tilde{w}(b_0, b_1, {\color{red}r_2}, r_3)
$$

这时候，求和等式右边的 $f(X_0, X_1, r_2, r_3)$ 可以看成是关于 $X_0,X_1$ 的 MLE 多项式，其在 Boolean Hypercube 上的取值是一个长度为 4 个向量，并且其中每个元素可以看成是矩阵 $A$ 根据 $r_2, r_3$ （按 Multilinear Basis 展开向量）的随机线性组合：
 
$$
\begin{bmatrix}
f(0,0,r_2,r_3) \\
f(0,1,r_2,r_3) \\
f(1,0,r_2,r_3) \\
f(1,1,r_2,r_3)
\end{bmatrix}
= 
\begin{bmatrix}
\mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\mathsf{fold}(r_2, r_3, (a_1, a_5, a_9, a_{13})) \\
\mathsf{fold}(r_2, r_3, (a_2, a_6, a_{10}, a_{14})) \\
\mathsf{fold}(r_2, r_3, (a_3, a_7, a_{11}, a_{15}))
\end{bmatrix}
$$

我们可以用向量的第一个元素 $f(0,0,r_2,r_3)$ 为例来具体推导上面这个等式来为什么成立：

$$
\begin{aligned}
f(0,0,r_2,r_3) &= \sum_{i=0}^{3} a_i \cdot eq(\mathsf{bits}(i), (0,0,r_2,r_3)) \\
&= f(0,0,0,0) \cdot eq(\mathsf{bits}(0), (0,0,r_2,r_3)) + f(0,0,1,0) \cdot eq(\mathsf{bits}(4), (0,0,r_2,r_3)) \\
& + f(0,0,0,1) \cdot eq(\mathsf{bits}(8), (0,0,r_2,r_3)) + f(0,0,1,1) \cdot eq(\mathsf{bits}(12), (0,0,r_2,r_3)) \\
&= a_0 \cdot eq(\mathsf{bits}(0), (r_2,r_3)) + a_4 \cdot eq(\mathsf{bits}(1), (r_2,r_3)) \\
& + a_8 \cdot eq(\mathsf{bits}(2), (r_2,r_3)) + a_{12} \cdot eq(\mathsf{bits}(3), (r_2,r_3)) \\
& = a_0 \cdot eq(0,r_2)eq(0,r_3) + a_4 \cdot eq(1,r_2)eq(0,r_3) + a_8 \cdot eq(0,r_2)eq(1,r_3) + a_{12} \cdot eq(1,r_2)eq(1,r_3) \\
& = eq(0,r_2)\cdot \Big(a_0 \cdot eq(0,r_3) + a_8 \cdot eq(1,r_3)\Big) + eq(1,r_2)\cdot \Big(a_4 \cdot eq(0,r_3) + a_{12} \cdot eq(1,r_3)\Big) \\
&=eq(0,r_2)\cdot \Big(\mathsf{fold}(r_3,(a_0,a_8))\Big) + eq(1,r_2)\cdot \Big(\mathsf{fold}(r_3,(a_4,a_{12}))\Big) \\
&= \mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\end{aligned}
$$

全部四个值排在一起，恰好就是上一节协议中 $A$ 经过折叠产生的向量 $\vec{a}'$。不过与上一节协议不同的是，这里的 $r_2, r_3$ 并不是直接由 Verifier 直接随机产生，而是在一个 Sumcheck 协议运行过程中由 Verifier 产生，而本节 Sumcheck 协议的目的是证明一个任意点求值 $f(u_0, u_1, u_2, u_3)$ 的正确性。

换句话说，Sumcheck 协议的用处是可以证明 MLE 多项式在任意一个公开点的求值，并且将其转换为 $f$ 在随机点的取值，转换后的证明目标就可以采用上一节的协议来完成证明。这个随机数相当于是被复用了两次。不过值得注意的是，我们并不会运行完全部的 Sumcheck 轮次，而是在这里停止，然后剩下未证明的求和等式，直接全部交由 Verifier 来验证。

此时，Prover 只需要将 $\vec{a}'$ 直接发送给 Verifier，然后 Verifier 有两个检查任务，第一个任务检查 $\vec{a}'\cdot (1-u_0,u_0)\otimes(1-u_1,u_1)$ 是否等于 $\tilde{f}(u_0, u_1, r_2, r_3)$；第二个任务随机抽查 $\vec{a}'$ 是否是 $A$ 矩阵经由 $r_2, r_3$ 折叠而来。

我们下面给出协议的流程，读者可以对照上面的解释理解下协议的全貌。

### 协议流程

**公共输入**：$\mathsf{t}$，$\vec{u}=(u_0, u_1, u_2, u_3)$

**Witness**：$\vec{a}=(a_0, a_1, a_2, \ldots, a_{15})$

#### 承诺：

Prover 计算编码矩阵 $B=AG$：

$$
B = \begin{bmatrix}
\mathsf{enc}(a_0, a_1, a_2, a_3) \\
\mathsf{enc}(a_4, a_5, a_6, a_7) \\
\mathsf{enc}(a_8, a_9, a_{10}, a_{11}) \\
\mathsf{enc}(a_{12}, a_{13}, a_{14}, a_{15})
\end{bmatrix}
=
\begin{bmatrix}
e_0 & e_1 & e_2 & e_3 & e_4 & e_5 & e_6 & e_7 \\
e_8 & e_9 & e_{10} & e_{11} & e_{12} & e_{13} & e_{14} & e_{15} \\
e_{16} & e_{17} & e_{18} & e_{19} & e_{20} & e_{21} & e_{22} & e_{23} \\
e_{24} & e_{25} & e_{26} & e_{27} & e_{28} & e_{29} & e_{30} & e_{31}
\end{bmatrix}
$$

然后对 $B$ 矩阵的每一列计算 Merkle Tree 的根，
$$
\begin{aligned}
\mathsf{t}_0 &= \mathsf{MerkleRoot}(e_0, e_8, e_{16}, e_{24}) \\
\mathsf{t}_1 &= \mathsf{MerkleRoot}(e_1, e_9, e_{17}, e_{25}) \\
\vdots \\
\mathsf{t}_7 &= \mathsf{MerkleRoot}(e_7, e_{15}, e_{23}, e_{31}) \\
\end{aligned}
$$

最后对这些根计算 Merkle Tree，得到一个根 $\mathsf{t}$。

$$
\mathsf{t} = \mathsf{MerkleRoot}(\mathsf{t}_0, \mathsf{t}_1, \cdots, \mathsf{t}_7)
$$

#### Evaluation 证明

**第一步**：Prover 与 Verifier 进行第一轮的 Sumcheck 协议：Prover 发送 $h^{(0)}(X)$

$$
h^{(0)}(X) = f(u_0, u_1, u_2, X) = \sum_{\vec{b}\in\{0,1\}^3} \tilde{a}(b_0, b_1, b_2, X) \cdot \tilde{w}(b_0, b_1, b_2, X)
$$

**第二步**: Verifier 发送随机数 $r_3\in\mathbb{F}$，检查下面的等式：

$$
f(u_0, u_1, u_2, u_3)\overset{?}{=}h^{(0)}(0)+h^{(0)}(1)
$$

**第三步**：Prover 发送 $h^{(1)}(X)$

$$
h^{(1)}(X) =f(u_0, u_1, X, r_3) = \sum_{\vec{b}\in\{0,1\}^2} \tilde{a}(b_0, b_1, X, r_3) \cdot \tilde{w}(b_0, b_1, X, r_3)
$$

**第四步**：Verifier 发送随机数 $r_2\in\mathbb{F}_q$，检查下面的等式：

$$
h^{(0)}(r_3) = f(u_0, u_1, u_2, r_3) \overset{?}{=}h^{(1)}(0)+h^{(1)}(1)
$$

**第五步**：Prover 停止 Sumcheck 协议，发送折叠后的 $\vec{a}'$ 向量，

$$
\vec{a}' = \begin{bmatrix}
\mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\mathsf{fold}(r_2, r_3, (a_1, a_5, a_9, a_{13})) \\
\mathsf{fold}(r_2, r_3, (a_2, a_6, a_{10}, a_{14})) \\
\mathsf{fold}(r_2, r_3, (a_3, a_7, a_{11}, a_{15}))
\end{bmatrix}
$$

**第六步**：Verifier 抽样 $Q\subset\{0, 1, 2, \ldots, 7\}$，并发送给 Prover，记 $|Q|=l$

$$
Q = \{q_0, q_1, \ldots, q_{l-1}\}
$$

第七步：Prover 发送 $Q=\{q_i\}$ 中每一个查询点 $q_i$ 所对应的编码矩阵 $B$ 的列向量，记为 $\vec{b}_{q_i}$，以及它们所对应的 Merkle Tree 的根，即 $\mathsf{t}_{q_i}$；还有 $\mathsf{t}_{q_i}$ 在 $\mathsf{t}$ 上的 Merkle Path $\pi_{q_i}$。

验证步：Verifier 验证下面的等式是否成立：

1. 所有的 $\mathsf{t}_{q_i}$ 都与 $\mathsf{t}$ 一致，即
$$
\mathsf{t}_{q_i} = \mathsf{MerkleRoot}(\vec{b}_{q_i}), \quad \forall q_i\in Q
$$

2. $t_{q_i}$ 是否属于 $\mathsf{t}$ 的叶子，即

$$
\mathsf{MerkleTree.verify}(\mathsf{t}, \mathsf{t}_{q_i}, \pi_{q_i}) = 1, \quad \forall q_i\in Q
$$

3. 计算 $\vec{b}_{q_i}$ 的折叠是否与编码 $\vec{a}'^T G$ 的对应点一致，即

$$
\mathsf{fold}(r_2, r_3,\vec{b}_{q_i}) \overset{?}{=} \vec{a}'^T G_{q_i}, \quad \forall q_i\in Q
$$

其中 $G_{q_i}$ 是生成矩阵的第 $q_i$ 列。

4. 检查向量的内积 

$$
\vec{a}'\cdot\tilde{w}(u_0, u_1, r_2, r_3)\overset{?}{=}h^{(1)}(r_2) = \tilde{f}(u_0, u_1, r_2, r_3)
$$

## 3. 递归调用

我们引入一个新的多项式 $f'(X_0, X_1)$ 表示 $f(X_0, X_1, X_2, X_3)$ 在带入 $X_2=r_2, X_3=r_3$ 进行部分运算后得到的长度为 $2^2$ 的多项式：

$$
f'(X_0, X_1) = f(X_0, X_1, r_2, r_3)
$$

在上一节协议的**第五步**开始，Prover 和 Verifier 实际上可以看成是在证明 

$$
f'(u_0, u_1) = h^{(1)}(r_2)
$$

而且不难验证， $f'(X_0, X_1)$ 在 2维 Boolean Hypercube 上的求值恰好为 $\vec{a}'=(a'_0, a'_1, a'_2, a'_3)$，即：

$$
\begin{aligned}
f'(X_0, X_1) &= f(X_0, X_1, r_2, r_3) \\
&= a'_0\cdot\tilde{w}(X_0, X_1, r_2, r_3) + a'_1\cdot\tilde{w}(X_0, X_1, r_2, r_3) + a'_2\cdot\tilde{w}(X_0, X_1, r_2, r_3) + a'_3\cdot\tilde{w}(X_0, X_1, r_2, r_3)
\end{aligned}
$$


只是这个证明过程被压缩成： Prover 简单粗暴地把多项式表示（即 $\vec{a}'$ 作为 $f'$ 的 Evaluation Form）直接发送给 Verifier，由 Verifier 自己进行内积计算来完成检验。

请注意！这里我们可以换个思路，上一节描述的前半段协议实际上是把验证目标（验证步的第四步）

$$
f(u_0, u_1, u_2, u_3) \overset{?}{=} v
$$

的转换为下面的证明目标：

$$
f'(u_0, u_1) = f(u_0, u_1, r_2, r_3) \overset{?}{=} h^{(1)}(r_2)
$$

即证明 MLE 多项式 $f'(X_0, X_1)$ 在 $(u_0, u_1)$ 处的求值的正确性。虽然新的目标还是 MLE 求值证明，但是多项式长度已经从 16 减少到 4。

因此，我们可以让 Prover 和 Verifier 递归地调用上一节的协议，把这个 MLE 的求值证明 $f'(u_0, u_1)=v'$ 继续 Reduce 到一个更小的证明目标，直到新的多项式长度短到可以让 Verifier 轻松验证为止。

观察验证步的**第三项**，是 Verifier 检查 $l$ 个内积计算的验证。
$$
\mathsf{fold}(r_2, r_3,\vec{b}_{q}) \overset{?}{=} \vec{a}'G_{q}, \quad \forall q\in Q
$$

注意到等式左边可以由 Verifier 计算，等式右边是一个长度为 $N/N'$ 长度的向量的内积。我们这里引入符号 $N$ 表示多项式 $f$ 的长度，$N=2^n$，其中 $n$ 为未知数的个数；再引入符号 $N'$ 表示我们把 $f$ 的 Evaluations over boolean hypercube 组织成 $N'\times N_1$ 的矩阵，不难验证，一次协议调用后，Prover 最后发送的折叠向量 $\vec{a}'$ 的长度为 $N_1=N/N'$。

等式右边的矩阵乘法可以拆分为 $l$ 个向量内积计算，所以这个计算过程其实可以仍然采用 Sumcheck 协议交由 Prover 来完成，从而进一步降低 Verifier 的计算量。
并且这个 Sumcheck 协议可以和下一个递归调用的协议中的 Sumcheck 协议合并，从而降低 Verifier 的计算量。这个 Sumcheck 合并的思路最早出现在 Whir [ACFY24] 中，（我推测）Ligerito [NA25] 作者很有可能也是独立得到这个思路的。


### 协议的递归流程

我们假设初始的 MLE 多项式为 $f^{(0)}(X_0, X_1, \cdots, X_{n-1})$，其长度为 $N=2^n$。

第一次协议调用将多项式的求值形式折叠为 $N'\times N_1$ 的矩阵，记为 $A_0$，其中 $N_1=2^{n_1}$，$N'=2^{n_0}$，满足 $n_0 + n_1 = n$，即 $N_1\cdot N'=N$。

$$
A_0 = \begin{bmatrix}
a_0 & a_1 & \cdots & a_{N_1-1} \\
a_{N_1} & a_{N_1+1} & \cdots & a_{2N_1-1} \\
\vdots & \vdots & \ddots & \vdots \\
a_{(N_1-1)N'} & a_{(N_1-1)N'+1} & \cdots & a_{N-1}
\end{bmatrix}
$$

承诺计算为 

$$
B_0 = A_0G_1 = \begin{bmatrix}
b_0 & b_1 & \cdots & b_{N_1-1} \\
b_{N_1} & b_{N_1+1} & \cdots & b_{2N_1-1} \\
\vdots & \vdots & \ddots & \vdots \\
b_{N'-1} & b_{N'-1+1} & \cdots & b_{N-1}
\end{bmatrix}
$$

$$
\mathsf{t}^{(0)} = \mathsf{MerkleRoot}(\mathsf{t}_0, \mathsf{t}_1, \cdots, \mathsf{t}_{N_1-1})
$$

**公共输入**：

1. $\vec{u}=(u_0, u_1, \cdots, u_{n_1-1}, u_{n_1}, u_{n_1+1}, \cdots, u_{n-1})$
2. $\mathsf{t}^{(0)}$

**协议循环**：$i=0, 1, \cdots, l-1$，其中变量 $i$ 表示递归的层数。
 
**循环第一步**：如果 $i=0$，那么 Prover 直接跳到循环的第二步；

如果 $i\neq 0$，Prover 承诺 $f^{(i)}$，即将其排成 $N'\times N_i$ 的矩阵，记为 $A^{(i)}$，计算其编码矩阵 $B^{(i)}$，与其 Merkle Tree 的根 $\mathsf{t}^{(i)}$。Prover 发送  $\mathsf{t}^{(i)}$。

**循环第二步**：Prover 与 Verifier 进行 $k=\log_2(N')$ 轮的 Sumcheck 协议，协议过程中，Verifier 依次发送随机数 $r^{(i)}_{k-1}, r^{(i)}_{k-2}, \cdots, r^{(i)}_{0}$，并且最后 Prover 发送多项式 $h^{(i)}(X)$，满足
$$
h^{(i)}(X) = \tilde{f}^{(i)}(u_0, u_1, u_{n_1-1}, X, r^{(i)}_{1},\ldots, r^{(i)}_{k-1}) = \sum_{\vec{b}\in\{0,1\}^{n_1}} \tilde{a}^{(i)}(\vec{b}, X) \cdot \tilde{w}^{(i)}(\vec{b}, X)
$$

而 $h^{(i)}(r^{(i)}_{0})$ 就是 $\tilde{f}^{(i+1)}$ 在 $(u_0, u_1, \cdots, u_{n_i-1})$ 处的求值，记为 $v^{(i+1)}$：

$$
v^{(i+1)}= h^{(i)}(r^{(i)}_{0}) = \tilde{f}^{(i+1)}(u_0, u_1, \cdots, u_{n_i-1})
$$

不难推导，$v^{(i+1)}$ 是折叠后的向量 $\vec{a}^{(i+1)}$ 与 $\vec{w}^*$ 的内积：

$$
v^* = \vec{a}^{(i+1)}\cdot\vec{w}^*
$$

这里 
$$
\vec{a}^{(i+1)} = \mathsf{fold}((r^{(i)}_{0}, r^{(i)}_{1}, \cdots, r^{(i)}_{k-1}), \vec{a}^{(i)})
$$

$$
\vec{w}^*= \mathsf{fold}((r^{(i)}_{0}, r^{(i)}_{1}, \cdots, r^{(i)}_{k-1}), \vec{w}^{(i)})
$$

请注意，这里我们先不着急占用符号 $w^{(i+1)}$，因为这个向量 $\vec{w}^*$ 只是一个中间结果，后面要和其它的向量进行合并。

**循环第三步**：Verifier 抽样 $Q\subset\{0, 1, 2, 3\}$，并发送给 Prover，其数量记为 $|Q|$，由协议安全参数所事先设定：

$$
Q = \{q_0, q_1, \ldots, q_{|Q|-1}\}
$$

**循环第四步**：Prover 发送 $Q$ 中每一个查询点 $q\in Q$ 所对应的编码矩阵 $B$ 的列向量，记为 $\vec{b}_{q}$，以及它们所对应的 Merkle Tree 的根，即 $\mathsf{t}^{(i)}_{q}$；还有 $\mathsf{t}^{(i)}_{q}$ 在 $\mathsf{t}^{(i)}$ 上的 Merkle Path $\pi^{(i)}_{q}$。

**循环第五步**：Verifier 验证下面的等式是否成立：

1. 所有的 $\mathsf{t}^{(i)}_{q}$ 都与 $\mathsf{t}^{(i)}$ 一致，即
$$
\mathsf{t}^{(i)}_{q} = \mathsf{MerkleRoot}(\vec{b}_{q}), \quad \forall q\in Q
$$

2. $\mathsf{t}^{(i)}_{q}$ 是否属于 $\mathsf{t}^{(i)}$ 的叶子，即

$$
\mathsf{MerkleTree.verify}(\mathsf{t}^{(i)}, \mathsf{t}^{(i)}_{q}, \pi^{(i)}_{q}) = 1, \quad \forall q\in Q
$$

**循环第六步**：对于每一个 $q\in Q$，Prover 计算 $\vec{a}^{(i+1)}$ 与 向量 $G^{(i)}_q$ 的内积， $y^{(i)}_q$ ，并发送给 Verifier。

$$
y^{(i)}_q = \vec{a}^{(i+1)}\cdot G^{(i)}_q
$$

这里 $G^{(i)}_q$ 为 $C[\mathbb{F}_q,N_i, \mathcal{R}N_i]$ 线性编码的生成矩阵 $G^{(i)}$ 的第 $q$ 列

**循环第七步**：Verifier 发送随机数 $\beta^{(i)}$，用来合并 $y^{(i)}_q$ 和上面第二步中产生的 $v^*$ 内积求和。新的求和值为：

$$
{v}^{(i+1)} =v^* + \beta^{(i)}\cdot y^{(i)}_0 + {\beta^{(i)}}^2\cdot y^{(i)}_1 + \cdots + {\beta^{(i)}}^{|Q|}\cdot y^{(i)}_{|Q|-1}
$$

如果 Prover 诚实，那么它应该是下面两个向量的内积：

$$
\vec{w}^{(i+1)} = \vec{w}^* + \beta^{(i)}\cdot G^{(i)}_{q_0} + {\beta^{(i)}}^2\cdot G^{(i)}_{q_1} + \cdots + {\beta^{(i)}}^{|Q|}\cdot G^{(i)}_{q_{|Q|-1}}
$$

其中 $G_{q_i}$ 是生成矩阵的第 $q_i$ 列。

**循环终止步**：如果 $n_i \leq n'$，那么 Prover 和 Verifier 结束循环；否则跳回 **循环第一步**，令 $i\leftarrow i+1$。

**循环外第一步**：Prover 直接发送 $\vec{a}^{(l)}$ 给 Verifier

**循环外第二步**：Verifier 计算 $\vec{w}^{(l)}$，并检查下面的等式：

$$
v^{(l)} \overset{?}{=} \vec{a}^{(l)}\cdot\vec{w}^{(l)}
$$

**协议完成**。

值得注意的是 $\vec{a}^{(l)}$ 与 $\vec{w}^{(l)}$ 是两个长度为 $N_l$ 的向量。

## 4. 降低 Verifier 的计算量

上面这个协议的第七步中，计算 $\vec{w}^{(i+1)}$ 的复杂度与 $\vec{w}^*$ 的长度有关，如果 Verifier 直接按照上面第七步的公式计算，那么计算复杂度将为 $O(|Q|\cdot N)$ 这显然不满足 Succinctness 的要求。

论文 [NA25] 讨论了如果线性编码是一类特殊的编码，其生成矩阵的每一列都具有 Tensor Structure，那么 Verifier 用指数级的时间复杂度计算出 $\vec{w}^{(l)}$。

主要想法是，如果有两个向量 $\vec{r}$ 和 $\vec{w}$ 都具有 Tensor Structure：

$$
\begin{aligned}
\vec{r} &= r_0 \otimes r_1 \otimes \cdots \otimes r_{k-1} \\
\vec{w} &= w_0 \otimes w_1 \otimes \cdots \otimes w_{k-1} \\
\end{aligned}
$$

那么 $\vec{r}$ 和 $\vec{w}$ 的内积可以表示为：

$$
\vec{r}\cdot\vec{w} = \prod_{i=0}^{k-1} r_i \cdot w_i
$$

## References 

- [NA25] Andrija Novakovic and Guillermo Angeris. Ligerito: A Small and Concretely Fast Polynomial Commitment Scheme. 2025. https://angeris.github.io/papers/ligerito.pdf.
- [ACFY24] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi and Eylon Yogev. WHIR: Reed–Solomon Proximity Testing with Super-Fast Verification. 2024. https://eprint.iacr.org/2024/1586.pdf
- [DP23] Benjamin Diamond and Jim Posen. Proximity Testing with Logarithmic Randomness. 2023. https://eprint.iacr.org/2023/630.pdf
- [AHIV17] Scott Ames, Carmit Hazay, Yuval Ishai, and Muthuramakrishnan Venkitasubramaniam. Ligero: lightweight sublinear arguments without a trusted setup”. 2022. https://eprint.iacr.org/2022/1608.pdf
