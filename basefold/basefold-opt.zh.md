# Basefold 优化

Yu Guo <yu.guo@secbit.io>

最后更新时间：2025-06-10

## 协议回顾

对于任意一个 $n$ 个变量（Indeterminate）的 Multilinear Polynomial $\tilde{f}(X_0, X_1,\ldots, X_{n-1})\in F^{\leq 1}[X_0, X_1,\ldots, X_{n-1}]$，如果要证明其在一个任意点 $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$ 的运算值是正确的，Basefold 协议 [ZCF23] 提供了一个简洁优雅的方案。其核心思路是用 Sumcheck 协议来证明 $\tilde{f}(u_0, u_1, \ldots, u_{n-1})$ ，然后在 Sumcheck 协议的最后一步，Verifier 需要验证 $\tilde{f}(r_0, r_1, \ldots, r_{n-1})$ 的运算值， Basefold 并没有借助于另一个 MLE PCS 来完成这最后一步的证明，而是借助一个 FRI 协议来辅助完成。本来 FRI 协议的证明目的是证明一个 Codeword 的 Proximity，即与正确的码字的距离不超过一个安全参数 $\delta$，然而在 FRI 协议的最后一步，Prover 会发送一个折叠后的 Codeword 对应的 Message，如果折叠充分，那么最后的 Message 是一个常数（多项式），如果 Prover 诚实，那么这个值恰好等于 $\tilde{f}(r_0, r_1, \ldots, r_{n-1})$ 的值，恰好与 Sumcheck 形成互补的情况。

下面我们过一下协议细节，首先 $\tilde{f}(\vec{X})$ 可以重写成下面的等式：

$$
\tilde{f}(\vec{X}) = \sum_{\vec{b}\in\{0,1\}^n} \tilde{f}(\vec{b}) \cdot eq(\vec{X}, \vec{b})
$$

可以看出等式右边是一个求和式，这满足 Sumcheck 协议的要求。Sumcheck 协议可以证明下面的内积等式：

$$
v = \sum_{\vec{b}\in\{0,1\}^n} \tilde{f}(\vec{b}) \cdot \tilde{g}(\vec{b})
$$

### 基于 Sumcheck 协议的内积证明

我们回顾一下如何利用 Sumcheck 协议证明内积，我们假设两个长度为 $2^n$ 的向量 $\vec{f}$ 与 $\vec{g}$ 分别对应两个 n 个变量的 Multilinear Polynomial，$\tilde{f}$ 与 $\tilde{g}$，那么接下来我们解释 Prover 和 Verifier 如何证明下面的目标：

$$
s = \sum_{\vec{b}\in\{0,1\}^n} \tilde{f}(b_0, b_1, \ldots, b_{n-1}) \cdot \tilde{g}(b_0, b_1, \ldots, b_{n-1})
$$

第一轮：Prover 构造一个 Degree 为 2 的一元多项式 $h^{(0)}(X)$，发送它在 $X=0,1,2$ 这三个点上的求值，即 $(h^{(0)}(0), h^{(0)}(1), h^{(0)}(2))$。

$$
h^{(0)}(X) = \sum_{\vec{b}\in\{0,1\}^{n-1}} \tilde{f}(X, b_1, b_2, \ldots, b_{n-1}) \cdot \tilde{g}(X, b_1, b_2, \ldots, b_{n-1})
$$

Verifier 检查 $h^{(0)}(0)+h^{(0)}(1)\overset{?}{=}v$，如果成立，则回应一个随机挑战数 $r_0\in\mathbb{F}_q$，然后证明目标就被转换成了一个新的证明目标：

$$
h^{(0)}(r_0) = \sum_{\vec{b}\in\{0,1\}^{n-1}} \tilde{f}(r_0, b_1, b_2, \ldots, b_{n-1}) \cdot \tilde{g}(r_0, b_1, b_2, \ldots, b_{n-1})
$$

观察到 $\tilde{f}(r_0, X_1, \ldots, X_{n-1})$ 和 $\tilde{g}(r_0, X_1, \ldots, X_{n-1})$ 仍然是 Multilinear Polynomial，我们将其分别记为 $\tilde{f}^{(1)}(X_1, \ldots, X_{n-1})$ 与 $\tilde{g}^{(1)}(X_1, \ldots, X_{n-1})$，

$$
\begin{aligned}
\tilde{f}^{(1)}(X_1, \ldots, X_{n-1}) &= \tilde{f}(r_0, X_1, \ldots, X_{n-1}) \\
\tilde{g}^{(1)}(X_1, \ldots, X_{n-1}) &= \tilde{g}(r_0, X_1, \ldots, X_{n-1})
\end{aligned}
$$

于是新的证明目标可以写为：

$$
h^{(0)}(r_0) = v^{(1)} \overset{?}{=} \sum_{\vec{b}\in\{0,1\}^{n-1}} \tilde{f}^{(1)}(b_1, \ldots, b_{n-1}) \cdot \tilde{g}^{(1)}(b_1, \ldots, b_{n-1})
$$

这样 Sumcheck 可以看成一个递归调用的协议，每次调用就会讲求和的长度减半。
接着 Prover 和 Verifier 重复上述过程，直到 Sumcheck 的证明长度变成 1 为止。

第 $n$ 轮，Prover 构造 $h^{(n-1)}(X)$，发送 $(h^{(n-1)}(0), h^{(n-1)}(1), h^{(n-1)}(2))$ 三个点，

$$
h^{(n-1)}(X) = \tilde{f}^{(n-1)}(X) \cdot \tilde{g}^{(n-1)}(X)
$$

Verifier 检查 $h^{(n-1)}(0)+h^{(n-1)}(1)\overset{?}{=}v^{(n-1)}$，如果成立，则回应一个随机挑战数 $r_{n-1}\in\mathbb{F}_q$，然后证明目标就被转换成了一个新的证明目标：

$$
h^{(n-1)}(r_{n-1}) \overset{?}{=} \tilde{f}^{(n-1)}(r_{n-1}) \cdot \tilde{g}^{(n-1)}(r_{n-1})
$$

然后 Prover 无需再发送任何消息，Verifier 直接计算 $h^{(n-1)}(r_{n-1})$ 的值，然后调用 $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ 与 $\tilde{g}(X_0, X_1, \ldots, X_{n-1})$ 的 Oracle，得到 $\tilde{f}^{(n-1)}(r_{n-1})$ 与 $\tilde{g}^{(n-1)}(r_{n-1})$ 的值，然后验证等式是否成立：

$$
\begin{aligned}
f^{(n-1)}(r_{n-1}) &= \tilde{f}(r_0, r_1, \ldots, r_{n-1}) \\
g^{(n-1)}(r_{n-1}) &= \tilde{g}(r_0, r_1, \ldots, r_{n-1}) \\
\end{aligned}
$$

通常来说，在 Sumcheck 最后一步，Verifier 所依赖的 $\tilde{f}$ 与 $\tilde{g}$ 的 Oracle 采用 Polynomial Commitment 来实现。即在 Sumcheck 开始之前，Prover 先发送它们的 Commitment，然后在 Sumcheck 的最后一步，由 Prover 来发送 $\tilde{f}(r_0, r_1, \ldots, r_{n-1})$ 与 $\tilde{g}(r_0, r_1, \ldots, r_{n-1})$ 的值，并附上相应的 Multilinear Polynomial Evaluation 的证明。

### 基于 FRI 协议的 Proximity 证明

> TODO

### 基于 Multilinear Basis 的 Basefold 证明过程

我们采用实现的视角过一遍 Prover 的证明过程。为了方便读者理解，我们假设 $\tilde{f}$ 是一个三变量的 Multilinear Polynomial，协议总共有 $n=3$ 轮，那么 Prover 先做一轮的 Sumcheck，然后复用 Sumcheck 的随机数，再做一轮 FRI 协议，这等于完成了一轮的 Basefold 协议；然后依次做下去，直到 Sumcheck 的证明长度变成 1 为止。

$$
\begin{aligned}
 v &= \sum_{(b_0,b_1,b_2)\in\{0,1\}^3} \tilde{f}(b_0, b_1, b_2) \cdot eq((u_0, u_1, u_2), (b_0, b_1, b_2)) \\
 &= \sum_{i=0}^{7} a_i\cdot w_i
\end{aligned}
$$

这里 $v= \tilde{f}(u_0, u_1, u_2)$，向量 $\vec{a}=(a_0, a_1, \cdots, a_{7})$ 是 $\tilde{f}(\vec{X})$ 在 Boolean Hypercube 上的运算值，而 $\vec{w}=(w_0, w_1, \cdots, w_{7})$ 是 $eq(\vec{u}, \vec{X})$ 在 Boolean Hypercube 上取值：

$$
\begin{aligned}
w_0 &= (1-u_0)(1-u_1)(1-u_2) \\
w_1 &= u_0(1-u_1)(1-u_2) \\
w_2 &= (1-u_0)u_1(1-u_2) \\
w_3 &= u_0u_1(1-u_2) \\
w_4 &= (1-u_0)(1-u_1)u_2 \\
w_5 &= u_0(1-u_1)u_2 \\
w_6 &= (1-u_0)u_1u_2 \\
w_7 &= u_0u_1u_2 \\
\end{aligned}
$$

Prover 需要证明这个内积计算的正确性。即

$$
v = a_0w_0 + a_1w_1 + a_2w_2 + a_3w_3 + a_4w_4 + a_5w_5 + a_6w_6 + a_7w_7
$$

Prover 维护长度为 $2^n$ 的两个数组，分别保存 $\vec{a}$ 和 $\vec{w}$，分别对应 $\tilde{f}$ 和 $eq$ 的 Evaluations 表示。

$$
\begin{aligned}
a_i &= \tilde{f}(i_0, i_1, i_2) \\
w_i &= eq((u_0, u_1, u_2), (i_0, i_1, i_2))
\end{aligned}
$$

第一轮的 Sumcheck 协议，Prover 计算 $h^{(0)}(X)$。这是一个 Degree 为 2 的一元多项式，我们只要得到它在至少三个不同点上的求值，就可以唯一表示这个多项式，为了优化计算，我们特意选择 $X=0,1,2$ 这三个点。

$$
h^{(0)}(X) = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{g}(X, b_1, b_2)
$$

而 $h^{(0)}(0)$ 恰好等于内积求和项中的位于偶数位置的项的和，而 $h^{(0)}(1)$ 恰好等于内积求和项中的位于奇数位置的项的和，表示如下：

$$
\begin{aligned}
h^{(0)}(0) &= a_0w_0 + a_2w_2 + a_4w_4 + a_6w_6  \\
h^{(0)}(1) &= a_1w_1 + a_3w_3 + a_5w_5 + a_7w_7 \\
\end{aligned}
$$

因此 Prover 只需两遍 $2^{n-1}$ 次乘法与 $2^{n-1}$ 次加法（总计 $2^n$ 次乘法与 $2^{n}$ 次加法）就能计算出 $h^{(0)}(0)$ 和 $h^{(0)}(1)$。但如何计算 $h^{(0)}(2)$ 呢？我们先证明下面的等式，这个等式我们反复要用到：

$$
\tilde{f}(X_0+1, X_1, X_2) = \tilde{f}(X_0, X_1, X_2) + 
\tilde{f}(1, X_1, X_2) - \tilde{f}(0, X_1, X_2)
$$

推而广之，我们可以得到下面的式子

$$
\tilde{f}(\vec{Y}, X_k+1, \vec{Z}) = \tilde{f}(\vec{Y}, X_k, \vec{Z}) + 
\tilde{f}(\vec{Y}, 1, \vec{Z}) - \tilde{f}(\vec{Y}, 0, \vec{Z})
$$

那么根据 Multilinear Polynomial 的性质，我们可以计算出 $h^{(0)}(2)$ 的值：

$$
\begin{aligned}
h^{(0)}(2) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(2, b_1, b_2) \cdot \tilde{w}(2, b_1, b_2)  \\
&=  \sum_{b_1,b_2\in\{0,1\}^{2}} \Big( 2\cdot\tilde{f}(1, b_1, b_2) - \tilde{f}(0, b_1, b_2) \Big)\cdot \Big( 2\cdot\tilde{w}(1, b_1, b_2)  - \tilde{w}(0, b_1, b_2) \Big)
\end{aligned}
$$

这需要 Prover 计算 $2^{n-1}$ 次乘法 与 $5\cdot 2^{n-1}$ 次加法。然后 Prover 发送 $h^{(0)}(0), h^{(0)}(1), h^{(0)}(2)$ 给 Verifier，Verifier 检查下面的等式是否成立：

$$
h^{(0)}(0)+h^{(0)}(1) \overset{?}{=} v
$$
如果成立，则回复一个随机数 $r_0\in\mathbb{F}_q$，然后证明目标就 Reduce 成了一个新的证明目标：

$$
\begin{aligned}
h^{(0)}(r_0) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(r_0, b_1, b_2) \cdot \tilde{w}(r_0, b_1, b_2) \\
& = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}^{(1)}(b_1,b_2) \cdot \tilde{w}^{(1)}(b_1,b_2)
\end{aligned}
$$

这里 $f^{(1)}(X_1, X_2)$ 和 $w^{(1)}(X_1, X_2)$ 在二维 Boolean Hypercube 上的 Evaluations 实际上直接可以通过 $\tilde{f}$ 和 $\tilde{w}$ 的 Evaluations 计算得到：

$$
\begin{aligned}
a^{(1)}_0 &= \tilde{f}^{(1)}(0, 0) = (1-r_0)\cdot\tilde{f}(0, 0, 0) + r_0\cdot\tilde{f}(1, 0, 0) \\
a^{(1)}_1 &= \tilde{f}^{(1)}(0, 1) = (1-r_0)\cdot\tilde{f}(0, 0, 1) + r_0\cdot\tilde{f}(1, 0, 1) \\
a^{(1)}_2 &= \tilde{f}^{(1)}(1, 0) = (1-r_0)\cdot\tilde{f}(0, 1, 0) + r_0\cdot\tilde{f}(1, 1, 0) \\
a^{(1)}_3 &= \tilde{f}^{(1)}(1, 1) = (1-r_0)\cdot\tilde{f}(0, 1, 1) + r_0\cdot\tilde{f}(1, 1, 1) \\
\end{aligned}
$$

所以这需要 Prover 计算 $2^{n-1}$ 次乘法与 $2^n$ 次加法从而得到 $f^{(1)}(X_1, X_2)$ 的 Evaluations 表示，记在 $(a^{(1)}_0, a^{(1)}_1, a^{(1)}_2, a^{(1)}_3)$ 中

$$
\begin{aligned}
a^{(1)}_0 &= (1-r_0)\cdot a_0 + r_0\cdot a_1 \\
a^{(1)}_1 &= (1-r_0)\cdot a_2 + r_0\cdot a_3 \\
a^{(1)}_2 &= (1-r_0)\cdot a_4 + r_0\cdot a_5 \\
a^{(1)}_3 &= (1-r_0)\cdot a_6 + r_0\cdot a_7 \\
\end{aligned}
$$

除此之外，Prover 还需要以同样的方式（$2^{n-1}$ 次乘法与 $2^n$ 次加法）计算 $\tilde{w}^{(1)}(X_1,X_2)$ 的 Evaluations 表示：

$$
\begin{aligned}
w^{(1)}_0 &= \tilde{w}^{(1)}(0, 0) = (1-r_0)\cdot\tilde{w}(0, 0, 0) + r_0\cdot\tilde{w}(1, 0, 0) \\
w^{(1)}_1 &= \tilde{w}^{(1)}(0, 1) = (1-r_0)\cdot\tilde{w}(0, 0, 1) + r_0\cdot\tilde{w}(1, 0, 1) \\
w^{(1)}_2 &= \tilde{w}^{(1)}(1, 0) = (1-r_0)\cdot\tilde{w}(0, 1, 0) + r_0\cdot\tilde{w}(1, 1, 0) \\
w^{(1)}_3 &= \tilde{w}^{(1)}(1, 1) = (1-r_0)\cdot\tilde{w}(0, 1, 1) + r_0\cdot\tilde{w}(1, 1, 1) \\
\end{aligned}
$$


这两部分对 Multilinear Polynomial 的折叠计算加起来总共需要 $2^n$ 次乘法与 $2\cdot 2^n$ 次加法。计算结果保存在两个长度为 $2^{n-1}$ 的数组 $\vec{a}^{(1)}$ 和 $\vec{w}^{(1)}$ 中。

接下来 Prover 和 Verifier 要完成 FRI 协议的第一轮（Commit-phase），即计算折叠后的一元多项式的 RS Code。下面是 $\tilde{f}(X_0, X_1, X_2)$ 所对应的一元多项式，$\hat{f}(X)$。请务必注意，它的系数式对应于 $\tilde{f}(X)$ 的 Evaluations表示，这不同于 Basefold 论文 [ZCF23] 中的形式：

$$
\hat{f}(X) = a_0 + a_1X + a_2X^2 + a_3X^3 + a_4X^4 + a_5X^5 + a_6X^6 + a_7X^7
$$

Prover 在 Sumcheck 第一轮中已经计算得到了折叠后的 $\tilde{f}^{(1)}(X_1, X_2)$ 的 Evaluations 表示，即 $\vec{a}^{(1)}$。它也对应到一个一元多项式 $\hat{f}^{(1)}(X)$，其系数式表示为：

$$
\begin{aligned}
\hat{f}^{(1)}(X) &= a^{(1)}_0 + a^{(1)}_1X + a^{(1)}_2X^2 + a^{(1)}_3X^3
\end{aligned}
$$

接下来，Prover 需要计算 $\tilde{f}^{(1)}(X)$ 的 RS Code，如果直接计算，这需要 Prover 计算 $(n2^{n-1})$ 次乘法。幸运地是，由于 RS Code 是一种「线性编码」，因此 Prover 可以直接在 $\hat{f}(X)$ 的 RS Code 上直接用 $(1-r_0, r_0)$ 进行折叠运算，即可得到 $\hat{f}^{(1)}(X)$ 的 RS Code。

先回顾下熟悉的 $\hat{f}(X)$ 的多项式分解：

$$
\begin{aligned}
\hat{f}(X) &= f_e(X^2) + X\cdot f_o(X^2) \\
\hat{f}(-X) &= f_e(X^2) - X\cdot f_o(X^2)
\end{aligned}
$$

其中 $f_e(X)$ 是偶数项组成的多项式，$f_o(X)$ 是奇数项组成的多项式：

$$
\begin{aligned}
f_e(X) &= a_0 + a_2X + a_4X^2 + a_6X^3 \\
f_o(X) &= a_1 + a_3X + a_5X^2 + a_7X^3
\end{aligned}
$$

又因为

$$
\begin{aligned}
\hat{f}^{(1)}(X^2) &= (1-r_0)\cdot f_e(X^2) + r_0\cdot f_o(X^2) \\
& = (1-r_0)\cdot\frac{\hat{f}(X)+\hat{f}(-X)}{2} + r_0\cdot\frac{\hat{f}(X)-\hat{f}(-X)}{2}
\end{aligned}
$$

所以，Prover 只需要对 $\hat{f}(X)$ 的 RS Code 进行同样的折叠运算，就可以得到 $\hat{f}^{(1)}(X)$ 的 RS Code：

$$
\mathsf{encode}(\hat{f}^{(1)})_i = (1-r_0)\cdot\mathsf{encode}(\hat{f})_i + r_0\cdot\mathsf{encode}(\hat{f})_{(i+N/2)}, \quad i\in[0, N)
$$

这里 $N$ 为长度为 $2^n$ 的消息经过编码后的长度，其中 $\rho=2^n/N$ 为码率。

这时候 Prover 发送 $\mathsf{encode}(\hat{f}^{(1)})$ 的 Merkle Root 作为承诺，然后 Prover 和 Verifier 进行 Sumcheck 的第二轮，重复上面的过程，直到 Sumcheck 协议的求和项长度为 1 ，这时伴随执行的 FRI 协议也将多项式折叠到了一个常数多项式 $\hat{f}^{(3)}(X)$。如果 Prover 诚实，那么 $\hat{f}^{(3)}(X)$ 的常数项恰好就是 $\tilde{f}(r_0, r_1, r_2)$：

$$
\hat{f}^{(3)}(X) = \tilde{f}(r_0, r_1, r_2)
$$

这个值正好可以被 Verifier 利用用来验证：

$$
v^{(3)} \overset{?}{=} \hat{f}^{(3)}(0)\cdot \tilde{eq}((u_0, u_1, u_2), (r_0, r_1, r_2))
$$

这时候，Verifier 需要计算 $\tilde{eq}((u_0, u_1, u_2), (r_0, r_1, r_2))$ 来完成最后的验证步，这需要 $2n$ 次乘法：

$$
\begin{aligned}
\tilde{eq}((u_0, u_1, u_2), (r_0, r_1, r_2)) &= \prod_{i=0}^{2} \Big( (1-r_i)\cdot(1-u_i) + r_i\cdot u_i \Big) \\
&= \prod_{i=0}^{2} \Big( 1 + 2r_i\cdot u_i - r_i -u_i \Big)
\end{aligned}
$$

对于 FRI 的 Query-phase 部分，这里我们略去。

### Sumcheck 性能分析

在 Sumcheck 协议部分，Prover 总共的计算量为 

- 计算 $\vec{w}$：$2^n$ 次乘法
- 计算 $h^{i}(0)$：$2^n$ 次乘法，$2\cdot 2^n$ 次加法
- 计算 $h^{i}(1)$：$2^n$ 次乘法，$2\cdot 2^n$ 次加法
- 计算 $h^{i}(2)$： 需要 $2^{n}$ 次乘法 与 $5\cdot 2^{n}$ 次加法
- 折叠计算 $\vec{a}$： 需要 $2^n$ 次乘法 与 $2\cdot 2^n$ 次加法
- 折叠计算 $\vec{w}$： 需要 $2^n$ 次乘法 与 $2\cdot 2^n$ 次加法

Verifier 计算量：

- 验证 $h^{(i)}(0)+h^{(i)}(1)\overset{?}{=}h^{(i-1)}(r_{i-1})$： $n$ 次加法
- 插值计算 $h^{(i)}(r_i)$：$4n$ 次除法、$3n$ 次乘法与 $9n$ 次加法
- 计算 $\tilde{eq}(r_0, r_1, \cdots, r_{n-1})$： $n$ 次乘法，$4n$ 次加法
- 最终验证：$1$ 次乘法

## Sumcheck 优化 

在上面的协议中，Prover 需要发送 Degree 为 2 的 $h^{(0)}(X), h^{(1)}(X), h^{(2)}(X)$ 三个多项式。最朴素的实现是 Prover 发送这些多项式在 $X=0,1,2$ 处的三个运算值，Verifier 检查前两个值，然后利用第三个值来计算 Lagrange Interpolation，计算得到 $h^{(0)}(r_0)$。

我们可以对上面的协议稍做变化，即可让 Prover 只发送 Degree 为 1 的线性多项式，那么 Prover 仅需要发两个点的运算值即可，而且 Verifier 也只需要做线性插值即可计算出下一个求和值。

Habock 在 [Hab24] 中给出了一个 Basefold 协议的优化版本，可以把 $h(X)$ 变成 Degree 为 1 的线性多项式。这个优化技术最早出现在 [Gru24] 中。下面我们简述下这个优化技术。


根据 $\tilde{eq}(\vec{X}, \vec{Y})$ 的定义，它可以被分解为：

$$
\tilde{eq}(\vec{X}_0\parallel\vec{X}_1, \vec{Y}_0\parallel\vec{Y}_1) = eq(\vec{X}_0, \vec{Y}_0) \cdot eq(\vec{X}_1, \vec{Y}_1)
$$

我们先观察下 $h^{(0)}(X)$ 的定义：

$$
h^{(0)}(X) = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{eq}((u_0, u_1, u_2), (X, b_1, b_2))
$$

它的等式右边可以改写为：

$$
\begin{aligned}
h^{(0)}(X) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{eq}((u_0, u_1, u_2), (X, b_1, b_2)) \\
&= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot eq(u_0, X) \cdot eq((u_1, u_2), (b_1, b_2)) \\
&= eq(u_0, X) \cdot \sum_{(b_1,b_2)\in\{0,1\}^2`}  \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big) \\
\end{aligned}
$$

我们引入记号 $g^{(0)}(X)$ 来表示等式右边的除 $eq(u_0, X)$ 之外的线性多项式，那么 $h^{(0)}(X)$ 可以表示为两个线性多项式的乘积：

$$
h^{(0)}(X) = eq(u_0, X) \cdot g^{(0)}(X)
$$

我们按照下面的方式修改协议，让 Prover 不直接发送 $h_0(X)$，而是发送线性多项式 $g_0(X)$，即 $g^{(0)}(0), g^{(0)}(1)$，

$$
g^{(0)}(X) = \sum_{(b_1,b_2)\in\{0,1\}^2} \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big)
$$

而 Verifier 收到 $g^{(0)}(0), g^{(0)}(1)$ 多项式之后，可以自行计算 $h^{(0)}(0), h^{(0)}(1)$ 的值，因为 

$$
\begin{aligned}
h^{(0)}(0) &= (1-u_0)\cdot g^{(0)}(0) \\
h^{(0)}(1) &= u_0 \cdot g^{(0)}(1) \\
\end{aligned}
$$

然后 Verifier 可以验证 $h^{(0)}(0)+h^{(0)}(1)\overset{?}{=}v$，如果验证通过，那么 Verifier 可以计算 $h^{(0)}(r_0)$，

$$
h^{(0)}(r_0) = \Big((1-u_0)(1-r_0)+u_0r_0\Big) \cdot g^{(0)}(r_0)
$$

这里 $g^{(0)}(r_0)$ 也可以通过 $g^{(0)}(0), g^{(0)}(1)$ 计算得到：

$$
g^{(0)}(r_0) = g^{(0)}(0) + \Big(g^{(0)}(1)-g^{(0)}(0)\Big)\cdot r_0
$$

最后计算得到 $h_0(r_0)$ 。总结下，这样Verifier 需要一个乘法来验证 $v$，三个乘法来计算 $h^{(0)}(r_0)$。

### 性能分析

Prover 总共的计算量为 

- 计算 $g^{i}(0)$：$2^n$ 次乘法，$2\cdot 2^n$ 次加法
- 计算 $g^{i}(1)$：$2^n$ 次乘法
- 折叠计算 $\vec{a}$： 需要 $2^n$ 次乘法 与 $2\cdot 2^n$ 次加法
- 折叠计算 $\vec{w}$： 需要 $2^n$ 次乘法 与 $2\cdot 2^n$ 次加法

Verifier 计算量：

- 计算 $h^{(i)}(0)$：$n$ 次乘法，$n$ 次加法
- 计算 $h^{(i)}(1)$：$n$ 次乘法，$n$ 次加法
- 验证 $h^{(i)}(0)+h^{(i)}(1)$： $n$ 次加法
- 计算 $h^{(i)}(r_i)$：$3n$ 次乘法、$6n$ 次加法
- 计算 $\tilde{eq}(r_0, r_1, \cdots, r_{n-1})$： $n$ 次乘法，$4n$ 次加法
- 最终验证：$1$ 次乘法


## 进一步优化 Verifier

我们再观察下 $g^{(0)}(X)$ 的定义：

$$
g^{(0)}(X) = \sum_{(b_1,b_2)\in\{0,1\}^2} \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big)
$$

这个求和式恰好等于 $\tilde{f}(X, u_1, u_2)$，于是我们可以换一个视角回顾下上面的优化协议：

Prover 在第一步发送 $g^{(0)}(0), g^{(0)}(1)$，实际上是发送：

$$
\begin{aligned}
g^{(0)}(0) &= \tilde{f}(0, u_1, u_2) \\
g^{(0)}(1) &= \tilde{f}(1, u_1, u_2) \\
\end{aligned}
$$

Verifier 检查验证 $h^{(0)}(X)$ 的正确性，等价于验证 $g^{(0)}(X)$ 的正确性：

$$
h^{(0)}(u_0) = eq(u_0, u_0) \cdot g^{(0)}(u_0) = g^{(0)}(u_0) = g^{(0)}(0) + \Big(g^{(0)}(1)-g^{(0)}(0)\Big)\cdot u_0 \overset{?}{=} v
$$

然后 Verifier 计算 $g^{(0)}(r_0)$ 作为下一轮 Sumcheck 的求和值。

$$
g^{(0)}(r_0) = g^{(0)}(0) + \Big(g^{(0)}(1)-g^{(0)}(0)\Big)\cdot r_0
$$

因此，我们好像可以不再需要引入 $h^{(i)}(X)$，而直接使用 $g^{(i)}(X)$ 即可。这样每一轮 Sumcheck 协议，Prover 需要发送 $g^{(i)}(0), g^{(i)}(1)$，Verifier 只需要计算两次乘法，一次用来计算 $g^{(i)}(u_i)$，一次用来计算 $g^{(i)}(r_i)$。而且在 Sumcheck 的最后一步，Verifier 只需要验证：

$$
g^{(n-1)}(r_{n-1}) \overset{?}{=} \tilde{f}(r_0, r_1, \cdots, r_{n-1})
$$

不难发现，在第  $i$ 轮，如果 Prover 诚实，$g^{(i)}(X)$ 恰好应该等于 $\tilde{f}^{(i)}(r_0, r_1, \cdots, r_{i-1}, X, u_{i+1}, \cdots, u_{n-1})$。我们重新写一下 改头换面后的 Sumcheck 协议：

第一轮：Prover 发送 $\tilde{f}(0, u_1, u_2), \tilde{f}(1, u_1, u_2)$，Verifier 验证：

$$
(1-u_0)\cdot \tilde{f}(0, u_1, u_2) + u_0\cdot \tilde{f}(1, u_1, u_2) \overset{?}{=} \tilde{f}(u_0, u_1, u_2) = v
$$

Verifier 回应 $r_0\in F$，并计算 $g^{(0)}(r_0) = \tilde{f}(r_0, u_1, u_2)$ 作为新的求和值 $v^{(1)}$：

$$
\tilde{f}(r_0, u_1, u_2) = (1-r_0)\cdot \tilde{f}(0, u_1, u_2) + r_0\cdot \tilde{f}(1, u_1, u_2)
$$

第二轮：Prover 发送 $\tilde{f}(r_0, 0, u_2), \tilde{f}(r_0, 1, u_2)$，Verifier 验证：

$$
(1-u_1)\cdot \tilde{f}(r_0, 0, u_2) + u_1\cdot \tilde{f}(r_0, 1, u_2) \overset{?}{=} \tilde{f}(r_0, u_1, u_2) = v^{(1)}
$$

Verifier 回应 $r_1\in F$，并计算 $g^{(1)}(r_1) = \tilde{f}(r_0, r_1, u_2)$ 作为新的求和值：

$$
\tilde{f}(r_0, r_1, u_2) = (1-r_1)\cdot \tilde{f}(r_0, 0, u_2) + r_1\cdot \tilde{f}(r_0, 1, u_2)
$$

第三轮：Prover 发送 $\tilde{f}(r_0, r_1, 0), \tilde{f}(r_0, r_1, 1)$，Verifier 验证：

$$
(1-u_2)\cdot \tilde{f}(r_0, r_1, 0) + u_2\cdot \tilde{f}(r_0, r_1, 1) \overset{?}{=} \tilde{f}(r_0, r_1, u_2) = v^{(2)}
$$

Verifier 回应 $r_2\in F$，并计算 $g^{(2)}(r_2) = \tilde{f}(r_0, r_1, r_2)$ 作为新的求和值：

$$
\tilde{f}(r_0, r_1, r_2) = (1-r_2)\cdot \tilde{f}(r_0, r_1, 0) + r_2\cdot \tilde{f}(r_0, r_1, 1)
$$

验证步：Verifier 通过 $\tilde{f}(X_0, X_1, X_2)$ Oracle，验证下面的等式：

$$
g^{(2)}(r_2) \overset{?}{=} \tilde{f}(r_0, r_1, r_2)
$$

这样每轮 Verifier 只需要进行两次乘法运算即可，第一个乘法是验证求和值 $v^{(i)}$ 的正确性，第二个乘法是计算 $g^{(i)}(r_i)$，总共 $2n$ 个乘法。


## Prover 的计算优化

Prover 在三轮中，需要依次发送：$g^{(0)}(0)$ 和 $g^{(0)}(1)$，$g^{(1)}(0)$ 和 $g^{(1)}(1)$，$g^{(2)}(0)$ 和 $g^{(2)}(1)$。

$$
\begin{aligned}
g^{(0)}(0) &= \tilde{f}(0, u_1, u_2) \\
g^{(0)}(1) &= \tilde{f}(1, u_1, u_2) \\
g^{(1)}(0) &= \tilde{f}(r_0, 0, u_2) \\
g^{(1)}(1) &= \tilde{f}(r_0, 1, u_2) \\
g^{(2)}(0) &= \tilde{f}(r_0, r_1, 0) \\
g^{(2)}(1) &= \tilde{f}(r_0, r_1, 1) \\
\end{aligned}
$$

这一节我们看下 Prover 如何能高效地计算 $g^{(i)}(0), g^{(i)}(1)$。

前文我们提到 Prover 维护了一个数组 $\vec{a}$，长度为 $2^n$，

$$
\begin{aligned}
a_0 &= \tilde{f}(0, 0, 0) \\
a_1 &= \tilde{f}(1, 0, 0) \\
a_2 &= \tilde{f}(0, 1, 0) \\
a_3 &= \tilde{f}(1, 1, 0) \\
a_4 &= \tilde{f}(0, 0, 1) \\
a_5 &= \tilde{f}(1, 0, 1) \\
a_6 &= \tilde{f}(0, 1, 1) \\
a_7 &= \tilde{f}(1, 1, 1) \\
\end{aligned}
$$

在每次 Sumcheck 轮中进行折叠，例如在经过第一轮的折叠（ $r_0$ 作为折叠因子）后，Prover 得到：

$$
\begin{aligned}
a^{(1)}_0 &= \tilde{f}^{(1)}(0, 0) = (1-r_0)\cdot\tilde{f}(0, 0, 0) + r_0\cdot\tilde{f}(1, 0, 0) \\
a^{(1)}_1 &= \tilde{f}^{(1)}(0, 1) = (1-r_0)\cdot\tilde{f}(0, 0, 1) + r_0\cdot\tilde{f}(1, 0, 1) \\
a^{(1)}_2 &= \tilde{f}^{(1)}(1, 0) = (1-r_0)\cdot\tilde{f}(0, 1, 0) + r_0\cdot\tilde{f}(1, 1, 0) \\
a^{(1)}_3 &= \tilde{f}^{(1)}(1, 1) = (1-r_0)\cdot\tilde{f}(0, 1, 1) + r_0\cdot\tilde{f}(1, 1, 1) \\
\end{aligned}
$$

为了高效计算 $g^{(i)}(0), g^{(i)}(1)$，我们让 Prover 在 Sumcheck 协议开始前，进行一番预计算，得到一个长度为 $2^n-1$ 的向量 $\vec{d}$。

这个向量是将 $\vec{a}$ 向量（$u_2, u_1, u_0$ 作为折叠因子）折叠后计算得到的结果。我们先将 $\vec{a}$ 向量采用 $u_2$ 折叠，得到 $d_0, d_1, d_2, d_3$：

$$
\begin{aligned}
d_0 &= (1-u_2)\cdot a_0 + u_2\cdot a_4 = \tilde{f}(0, 0, u_2)\\
d_1 &= (1-u_2)\cdot a_1 + u_2\cdot a_5 = \tilde{f}(1, 0, u_2)\\
d_2 &= (1-u_2)\cdot a_2 + u_2\cdot a_6 = \tilde{f}(0, 1, u_2)\\
d_3 &= (1-u_2)\cdot a_3 + u_2\cdot a_7 = \tilde{f}(1, 1, u_2)\\
\end{aligned}
$$

然后 Prover 对 $d_0, d_1, d_2, d_3$ 再次进行折叠运算，使用折叠因子 $u_1$，得到 $d_4, d_5$：

$$
\begin{aligned}
d_4 &= (1-u_1)\cdot d_0 + u_1\cdot d_2 = \tilde{f}(0, u_1, u_2)\\
d_5 &= (1-u_1)\cdot d_1 + u_1\cdot d_3 = \tilde{f}(1, u_1, u_2)\\
\end{aligned}
$$

最后 Prover 对 $d_4, d_5$ 进行折叠运算，使用折叠因子 $u_0$，得到 $d_6$：

$$
d_6 = (1-u_0)\cdot d_4 + u_0\cdot d_5 = \tilde{f}(u_0, u_1, u_2)
$$

观察下，向量 $(d_0, d_1, d_2, d_3, d_4, d_5, d_6)$ 的末尾值 $d_6$ 恰好是 $\tilde{f}(u_0, u_1, u_2)$，而倒数第二个和第三个元素，恰好是 $g^{(0)}(0), g^{(0)}(1)$：

$$
g^{(0)}(0) = d_4 \\
g^{(0)}(1) = d_5 \\
$$

如果 Prover 去除 $d_6$，将剩下的向量 $(d_0, d_1, d_2, d_3, d_4, d_5)$ 跟随 $\vec{a}$ 一同折叠（采用 $r_0$ 作为折叠因子），那么我们可以得到：

$$
\begin{aligned}
d'_0 &= (1-r_0)\cdot d_0 + r_0\cdot d_1 = \tilde{f}(r_0, 0, u_2) \\
d'_1 &= (1-r_0)\cdot d_2 + r_0\cdot d_3 = \tilde{f}(r_0, 1, u_2) \\
d'_2 &= (1-r_0)\cdot d_4 + r_0\cdot d_5 = \tilde{f}(r_0, u_1, u_2) \\
\end{aligned}
$$

我们惊奇地发现，$d'_2$ 恰好是 $g^{(0)}(r_0)$ 的值，而 $d'_0, d'_1$ 恰好是 $g^{(1)}(0), g^{(1)}(1)$ 的值。

接下来在第二轮 Sumcheck 中，Prover 将 $(d'_0, d'_1)$ 跟随 $\vec{a}'$ 一起采用 $r_1$ 进行折叠，可以得到 $d''_0$ 的值：

$$
d''_0 = (1-r_1)\cdot d'_0 + r_1\cdot d'_1 = \tilde{f}(r_0, r_1, u_2)
$$

这恰好是 $g^{(1)}(r_1)$ 的值。

那么在第三轮 Sumcheck 中，Prover 需要发送 $g^{(2)}(0), g^{(2)}(1)$ 的值，可是 $\vec{d}$ 向量已经折叠消失，不过这时候，Prover 手里有折叠后的 $\vec{a}$ 向量：

$$
\begin{aligned}
a^{(2)}_0 &= \tilde{f}^{(2)}(0) = \tilde{f}(r_0, r_1, 0) \\
a^{(2)}_1 &= \tilde{f}^{(2)}(1) = \tilde{f}(r_0, r_1, 1) \\
\end{aligned}
$$

这两个值恰好等于 $g^{(2)}(0), g^{(2)}(1)$ 的值。

### 性能分析

至此，我们总结下，只需要让 Prover 在 Sumcheck 开始前，预计算出向量 $\vec{d}$，它保存了 $\tilde{f}(X_0, X_1, X_2)$ 依次带入 $X_2=u_2, X_1=u_1, X_0=u_0$ 进行 Partial Evaluation 的所有中间结果。而这个向量跟随 $\vec{a}$ 向量采用相同的随机挑战数一同进行折叠，那么就可以高效计算出 $g^{(i)}(0), g^{(i)}(1), g^{(i)}(r_i)$ 的值。其中预计算需要 $2^n-1$ 次乘法，折叠总共需要 $2^n-2$ 次乘法。

Prover 计算量：

- 预计算 $\vec{d}$：$2^n$ 次乘法与 $2\cdot 2^n$ 次加法
- 折叠 $\vec{a}$：$2^n$ 次乘法与 $2\cdot 2^n$ 次加法
- 折叠 $\vec{d}$：$2^n$ 次乘法与 $2\cdot 2^n$ 次加法

Verifier 计算量：

- 验证 $g^{(i)}(0), g^{(i)}(1)$：$n$ 次乘法与 $2n$ 次加法
- 计算 $g^{(i)}(r_i)$：$n$ 次乘法与 $2n$ 次加法

## 再进一步优化 Verifier 

在上面的协议中，Prover 需要发送 $g^{(i)}(0), g^{(i)}(1)$ ，然后 Verifier 验证 

$$
g^{(i)}(0) +  (g^{(i)}(1) - g^{(i)}(0))\cdot u_i \overset{?}{=} g^{(i-1)}(r_{i-1}) = g^{(i)}(u_i)
$$

那么其实，Prover 在每轮 Sumcheck 中只需发送一个值 $g^{(i)}(0)$，然后 Verifier 根据「验证等式」反向计算得到 $g^{(i)}(1)$ ：

$$
g^{(i)}(1) = \frac{g^{(i-1)}(r_{i-1}) - g^{(i)}(0)}{u_i} + g^{(i)}(0)
$$

这样一来 Verifier 用一次除法计算来换取通讯量的减少（一半）。但注意有限域除法（求逆）的计算开销要显著大于乘法，计算量至少是 $o(\log{q})$ 的复杂度。但是无论如何，我们通过这种方式，可以进一步减少通讯量，即 Proof size。

其实，我们不难发现这个开销相对不小的除法是可以优化掉的，这个思路来源于 Deepfold []。我们让 Prover 在每轮 Sumcheck 中只发送 $g^{(i)}(u_i+1)$ 而不是 $g_i(0)$ 或 $g_i(1)$：

$$
g^{(i)}(u_i+1) = g^{(i)}(u_i) + g^{(i)}(1) - g^{(i)}(0)
$$

再次提醒，$g^{(i)}(u_i)$ 是 $\vec{d}$ 向量每次折叠之后的尾部元素，因此它的计算开销已经包含在 $\vec{d}$ 的折叠计算中。因此 Prover 的代价仅仅为在每轮额外计算两次加法。

然后，又因为此时Verifier 手里已经有了 $g^{(i)}(u_{i})=g^{(i-1)}(r_{i-1})$，这样 Verifier 可以不用除法就可得到 $g^{(i)}(r_i)$：

$$
g^{(i)}(r_i) = g^{(i)}(u_i) + \Big(g^{(i)}(u_i+1)-g^{(i)}(u_i)\Big)\cdot (r_i - u_i)
$$

计算开销仅为三次加法与一次乘法。

### 性能分析

Prover 计算量：

- 预计算 $\vec{d}$：$2^n$ 次乘法与 $2\cdot 2^n$ 次加法
- 折叠 $\vec{a}$：$2^n$ 次乘法与 $2\cdot 2^n$ 次加法
- 折叠 $\vec{d}$：$2^n$ 次乘法与 $2\cdot 2^n$ 次加法
- 计算 $g^{(i)}(u_i+1)$： $2n$ 次加法

Verifier 计算量：

- 计算 $g^{(i)}(r_i)$：$n$ 次乘法与 $3n$ 次加法

## 从另一个角度来理解 Sumcheck 优化

上面我们经过多步的优化，达到了一个比较理想的状态。我们看看能否更容易地去理解这个简洁的协议。

我们可以把上面的优化协议看成是一个 Recursive Split-and-fold 风格的求和证明。因为本身 $\tilde{f}(u_0, u_1, u_2)$ 就是一个数量为 8 项的求和式：

$$
\begin{aligned}
\tilde{f}(u_0, u_1, u_2) &= a_0(1-u_0)(1-u_1)(1-u_2) + a_1u_0(1-u_1)(1-u_2) \\
&+ a_2(1-u_0)u_1(1-u_2) + a_3u_0u_1(1-u_2) \\
&+ a_4(1-u_0)u_1u_2 + a_5u_0(1-u_1)u_2 \\
&+ a_6u_0u_1(1-u_2) + a_7u_0u_1u_2  \\
& = (1-u_0)\cdot \Big(a_0(1-u_1)(1-u_2) + a_2u_1(1-u_2) + a_4(1-u_1)u_2 + a_6u_1u_2 \Big) \\
&+ u_0\cdot \Big(a_1(1-u_1)(1-u_2) + a_3u_1(1-u_2) + a_5(1-u_1)u_2 + a_7u_1u_2 \Big) \\
\end{aligned}
$$

第一轮，Prover 分别发送左半边的括号中 4 项的和，右半边括号中 4 项的和，分别记为 $g_0(0)$ 和 $g_0(1)$，并发送给 Verifier：

$$
\begin{aligned}
g_0(0) &= a_0(1-u_1)(1-u_2) + a_2u_1(1-u_2) + a_4(1-u_1)u_2 + a_6u_1u_2 \\
g_0(1) &= a_1(1-u_1)(1-u_2) + a_3u_1(1-u_2) + a_5(1-u_1)u_2 + a_7u_1u_2 \\
\end{aligned}
$$

或者

$$
\begin{aligned}
g_0(0) &= \tilde{f}(0, u_1, u_2) \\
g_0(1) &= \tilde{f}(1, u_1, u_2) \\
\end{aligned}
$$


然后 Verifier 首先验证 $(g_0(0), g_0(1))$ 与 $(1-u_0, u_0)$ 进行内积的结果是否等于待证明的和 $v$，

$$
(1-u_0)\cdot g_0(0) + u_0\cdot g_0(1) \overset{?}{=} \tilde{f}(u_0, u_1, u_2)
$$

这样一来，Prover 和 Verifier 就将长度为 8 的求和证明 Reduce 到了两个长度为 4 的求和证明。又因为这两个新的求和式实际上具有相同的结构，即它们都是多项式的奇偶项系数分别和同一向量 $(1-u_1,u_1)\otimes(1-u_2,u_2)$ 进行内积的结果，

$$
\begin{aligned}
g^{(0)}(0) &= \langle(a_0, a_2, a_4, a_6), (1-u_1, u_1)\otimes(1-u_2, u_2)\rangle \\
g^{(0)}(1) &= \langle(a_1, a_3, a_5, a_7), (1-u_1, u_1)\otimes(1-u_2, u_2)\rangle \\
\end{aligned}
$$

所以 Verifier 可以给出一个随机数 $r_0$，利用它把这两个新的求和证明合并（Batching）在一起。巧合的是，合并之后的长度为 4 的求和值恰好是 $g^{(0)}(r_0)$ ，并且它等于 $\tilde{f}(r_0, u_1, u_2)$。当然这其实不是巧合，因为我们故意采用 $(1-r_0, r_0)$ 这种 Multilinear Basis 对 $g^{(0)}(0), g^{(0)}(1)$ 进行折叠，目的正是使之与 $g^{(0)}(r_0)$ 保持相等：

$$
(1-r_0)\cdot g_0(0) + r_0\cdot g_0(1) = \tilde{f}(r_0, u_1, u_2)
$$

这样，Prover 和 Verifier 接下来证明合并后的长度为 4 个向量的求和值等于 $\tilde{f}(r_0, u_1, u_2)$，即

$$
(1-r_0)\cdot g^{(0)}(0) + r_0\cdot g^{(0)}(1) \overset{?}{=} a'_0w'_0 + a'_1w'_1 + a'_2w'_2 + a'_3w'_3
$$

依次类推，这个协议和 Sumcheck 协议的思路是一致的，都是将一个求和等式，通过拆分成多段不同部分的求和，然后再用随机数将这些不同的求和段合并在一起证明。直到最后一轮，求和证明 Reduce 到了多项式的求值证明，Prover 和 Verifier 再借助其他工具来补上最后的证明部分。

而最原始的 Sumcheck in Basefold 协议，则没有利用求和式内部结构，而是采用了一个更通用的内积求和的证明。因此本文介绍的简洁协议正式充分利用了求和项的内部结构。

## References 

- [GLH+24] Yanpei Guo, Xuanming Liu, Kexi Huang, Wenjie Qu, Tianyang Tao, and Jiaheng Zhang. "DeepFold: Efficient Multilinear Polynomial Commitment from Reed-Solomon Code and Its Application to Zero-knowledge Proofs." _Cryptology ePrint Archive_ (2024).
- [ACFY24] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "WHIR: Reed–Solomon Proximity Testing with Super-Fast Verification." _Cryptology ePrint Archive_ (2024).
- [ZCF23] Hadas Zeilberger, Binyi Chen, and Ben Fisch. "BaseFold: efficient field-agnostic polynomial commitment schemes from foldable codes." Annual International Cryptology Conference. Cham: Springer Nature Switzerland, 2024.
- [Hab24] Ulrich Haböck. "Basefold in the List Decoding Regime." _Cryptology ePrint Archive_(2024).
- [Gru24] Angus Gruen. "Some Improvements for the PIOP for ZeroCheck". (2024). https://eprint.iacr.org/2024/108.