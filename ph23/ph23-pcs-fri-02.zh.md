# 缺失的协议 PH23-PCS（五）

- Jade Xie  <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

在上篇文章 *缺失的协议 PH23-PCS（四）* 中的 *对接 FRI* 这一小节回顾了 PH23 协议的证明分为两部分：

1. 证明 $\vec{c}$ 是 Well-Formedness。
2. 证明内积 $\langle \vec{a}, \vec{c} \rangle = v$ 。

为了证明 1 的正确性，需要证明下面 $n + 1$ 个多项式在一个乘法子群 $H = \{\omega^0, \omega^1, \ldots, \omega^{N - 1}\}$ 上的值都为 $0$ 。

$$
\begin{aligned}
p_0(X) = &s_0(X)\cdot \big(c(X) - (1-u_0)(1-u_1)\cdots(1-u_{n-1})\big)      \\
p_1(X) = &s_0(X)\cdot \big(c(X)u_{n-1} - c(\omega^{2^{n-1}}\cdot X)(1-u_{n-1})\big) \\
p_2(X) = &s_1(X)\cdot \big(c(X)u_{n-2} - c(\omega^{2^{n-2}}\cdot X)(1-u_{n-2})\big)  \\
\cdots & \quad\cdots \\
p_{n}(X) = &s_{n-1}(X)\cdot \big(c(X)u_0 - c(\omega\cdot X)(1-u_0)\big) \\
\end{aligned}
$$

在文章 *缺失的协议 PH23-PCS（四）* 介绍的协议中为了证明 2 的正确性，采用的是 Grand Sum 方法来证明。这里我们使用 Univariate Sumcheck 协议来证明内积。对 $a(X) \cdot c(X)$ 进行分解

$$
a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N), \quad \deg(g)<N-1
$$
如果证明了上面的等式成立以及 $\deg (g) < N - 1$ ，也就证明了内积正确 $\langle \vec{a}, \vec{c} \rangle = v$ 。

下面看看 Verifier 如何验证上面的多项式成立以及 $\deg (g) < N - 1$ 。

1. 证明 $\vec{c}$ 是 Well-Formedness。
	
	先用 Verifier 给出的随机数 $\alpha$ 将 $n + 1$ 个多项式 $p_i(X)$ 聚合成一个多项式 $p(X)$ ，
	
	$$
	p(X) = p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)\
	$$
	
	现在需要说明 $p(X)$ 在 $H$ 上的取值都为 $0$ ，那么取 $v_H(X)$ 为 $H$ 上的 Vanishing 多项式，那么存在一个商多项式 $t(X)$ ，满足
	
	$$
	p(X) = t(X) \cdot v_H(X)
	$$
	为了验证商多项式的存在性，Verifier 选取随机点 $\zeta$ ，Prover 发送
	
	$$
	\big(c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), t(\zeta)\big)
	$$
	Verifier 可以计算出 $p(\zeta)$ ，自行计算出 $v_H(\zeta)$ ，来验证
	
	$$
	p(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
	$$

2. 证明内积 $\langle \vec{a}, \vec{c} \rangle = v$ 。
	
	为了证明
	
	$$
	a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N), \quad \deg(g)<N-1
	$$
	
	可以采用同一个随机数 $\zeta$ ，Prover 再发送
	
	$$
	\big(a(\zeta), q_{ac}(\zeta), g(\zeta)\big)
	$$
	
	Verifier 验证
	
	$$
	a(\zeta)\cdot c(\zeta) \overset{?}{=} q_{ac}(\zeta)\cdot v_H(\zeta) + \zeta\cdot g(\zeta) + (v/N)
	$$
	
	同时需要证明 $\deg(g)<N-1$ ，这可以用 FRI 的 low degree test 来证明。

为了说明上面 Prover 发送的值正确，需要借助 FRI-PCS 来进行证明。为了结合 FRI 协议，这里先分析这些多项式的次数，由于 $a(X)$ 与 $c(X)$ 分别是通过 $\vec{a}$ 与 $\vec{c}$ 得到的，因此

$$
\deg(a(X)) = N - 1, \quad \deg(c(X)) = N - 1
$$

而

$$
s_i(X) = \frac{v_H(X)}{v_{H_i}(X)} = \frac{X^N-1}{X^{2^i}-1}
$$

可知 $\deg(s_i) = N - 2^i$ ，因此 

$$
\deg(p(X)) = \deg(p_0(X)) = \deg(s_0(X)) + \deg(c(X)) = N - 1+ N - 1 = 2N - 2
$$

$$
\deg(t(X)) = \deg(p(X)) - \deg(v_H(X)) = 2N - 2 - N = N - 2
$$

根据 $a(X) \cdot c(X)$ 的分解，可以得出

$$
\deg(q_{ac}(X)) = \deg(a(X) \cdot c(X)) - \deg(v_H(X)) = 2N - 2 - N = N - 2 
$$

$$
\deg(g(X)) = N - 1 - 1 = N - 2
$$

为了只调用一次 FRI 的 low degree test ，先进行 degree correction，向 Verifier 要一个随机数 $r \stackrel{\$}{\leftarrow} \mathbb{F}$ ，

$$
t'(X) = t(X) + r \cdot X \cdot t(X)
$$

$$
q'_{ac}(X) = q_{ac}(X) + r \cdot X \cdot q_{ac}(X)
$$

$$
g'(X) = g(X) + r \cdot X \cdot g(X)
$$

现在多项式 $a(X), c(X), t'(X), q'_{ac}(X), g'(X)$ 的次数都为 $N - 1$ 。Prover 发送的值有

$$
\big(c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), t(\zeta),a(\zeta), q_{ac}(\zeta), g(\zeta)\big)
$$

为了证明上面发送的值是正确的，一个函数可能在多个点同时打开，依然采用与本文**对接 FRI** 小节介绍的构造商多项式的相同方法。

- 对于 $a(X)$ ， 证明商多项式
	
	$$
	q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
	$$
	
	的次数小于 $N - 1$ 。

- 对于 $c(X)$ ，证明商多项式
	
	$$
	q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
	$$
	的次数小于 $N - 1$ 。

- 对于 $t(X)$ ，用 $t'(X)$ 的商多项式来证明，证明

	$$
	q_{t'}(X) = \frac{t'(X) - t'(\zeta)}{X - \zeta}
	$$
	的次数小于 $N - 1$ 。


- 对于 $q_{ac}(X)$ ，用 $q_{ac}'(X)$ 的商多项式来证明，证明
	
	$$
	q_{q_{ac}'}(X) = \frac{q_{ac}'(X) - q_{ac}'(\zeta)}{X - \zeta}
	$$
	的次数小于 $N - 1$ 。

- 对于 $g(X)$ ，用 $g'(X)$ 的商多项式来证明，证明
	
	$$
	q_{g'}(X) = \frac{g'(X) - g'(\zeta)}{X - \zeta}
	$$
	
	的次数小于 $N - 1$ 。这里也就自然证明了 $\deg(g(X)) < N - 1$ 。


接着用随机数 $r$ 的幂次将上面 $5$ 个 low degree test batch 成一个 low degree test 证明。令

$$
q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_{t'}(X) + r^4 \cdot q_{q_{ac}'}(X) + r^6 \cdot q_{g'}(X)
$$
注意，由于 $t'(X), q_{ac}'(X) , g'(X)$ 多项式进行 degree correction 时已经用了随机数 $r$ ，为了能用一个随机数的幂次达到多个随机数的效果，因此上面 batch 的幂次不是按自然数递增的，不是 $(1, r, r^2, r^3, r^4)$  而是 $(1, r, r^2, r^4, r^6)$ 。

下面只需要用 FRI 的 low degree test 来证明 $\deg(q'(X)) < N - 1$ 就大功告成了。最后为了对接 FRI low degree test 协议，需要将 $q'(X)$ 的次数对齐到 $2$ 的幂次，即向 Verifier 要一个随机数 $\lambda$ ，证明

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$

的次数小于 $N$ 。

## PH23 + FRI 协议

### Commit 阶段

对于 FRI 协议，对多项式的承诺就是计算其 Reed-Solomon 编码，并对编码进行承诺。在 PCS 的 Commit 阶段需要对原 MLE 多项式进行承诺，即

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$

$\vec{a}$ 就唯一确定了一个 $n$ 元 MLE 多项式，要对 MLE 多项式 $\tilde{f}$ 承诺其实就是对 $\vec{a}$ 进行承诺，若用 FRI 协议，那么就先要将 $\vec{a}$ 转换成多项式 $a(X)$ ，再对其在 $D$ 上的 Reed-Solomon 编码进行承诺。

1. Prover 构造一元多项式 $a(X)$ ，使其在 $H$ 上的求值为 $\vec{a} = (a_{0,}a_{1},\ldots, a_{N-1})$ 。

	$$
	a(X) = a_0 \cdot L_0(X) + a_1 \cdot L_1(X) + \ldots + a_{N-1} \cdot L_{N-1}(X)
	$$
	
2. Prover 计算多项式 $a(X)$ 的承诺 $C_a$ ，并将 $C_a$ 发送给 Verifier 

	$$
	C_a = \mathsf{cm}([a(x)|_{x \in D}]) = \mathsf{MT.commit}([a(x)|_{x \in D}]) 
	$$

### 公共输入

1.  FRI 协议参数：Reed Solomon 编码选取的区域 $D_n \subset D_{n-1} \subset \cdots \subset D_0 = D$ ，码率 $\rho$ ，查询阶段的次数 $l$ 。
2. 承诺 $C_a$

	$$
	C_a = \mathsf{cm}([a(x)|_{x \in D}]) = \mathsf{MT.commit}([a(x)|_{x \in D}]) 
	$$
	
3. 求值点  $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$
4. $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 

### Witness

- 多元多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ 的在 Boolean Hypercube 上的取值 $\vec{a} = (a_0,a_1, \ldots, a_{N-1})$ 

### Evaluation 证明协议

#### Round 1

Prover:

1. 计算向量 $\vec{c}$，其中每个元素 $c_i=\overset{\sim}{eq}(\mathsf{bits}(i), \vec{u})$

2. 构造多项式 $c(X)$，其在 $H$ 上的运算结果恰好是 $\vec{c}$ 。

	$$
	c(X) = \sum_{i=0}^{N-1} c_i \cdot L_i(X)
	$$
3. 计算 $c(X)$ 的承诺 $C_c$，并发送 $C_c$
	
	$$
	C_c = \mathsf{cm}([c(x)|_{x \in D}]) = \mathsf{MT.commit}([c(x)|_{x \in D}]) 
	$$

4. 分解 $a(X) \cdot c(X)$ ，计算得到 $q_{ac}(X)$ 与 $g(X)$ ，满足

	$$
	a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N)
	$$
	
5. 计算 $q_{ac}(X)$ 的承诺 $C_{q_{ac}}$ ，并发送 $C_{q_{ac}}$ 

	$$
	C_{q_{ac}} = \mathsf{cm}([q_{ac}(x)|_{x \in D}]) = \mathsf{MT.commit}([q_{ac}(x)|_{x \in D}]) 
	$$
	
6. 计算 $g(X)$ 的承诺 $C_g$ ，并发送 $C_{g}$ 

	$$
	C_{g} = \mathsf{cm}([g(x)|_{x \in D}]) = \mathsf{MT.commit}([g(x)|_{x \in D}]) 
	$$

#### Round 2

Verifier: 发送挑战数 $\alpha \stackrel{\$}{\leftarrow} \mathbb{F}_p$ 

Prover: 

1. 构造关于 $\vec{c}$ 的约束多项式 $p_0(X),\ldots, p_{n}(X)$
	
	$$
	\begin{split}
	p_0(X) &= s_0(X) \cdot \Big( c(X) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
	p_k(X) &= s_{k-1}(X) \cdot \Big( u_{n-k}\cdot c(X) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot X)\Big) , \quad k=1\ldots n
	\end{split}
	$$
	
2. 把 $\{p_i(X)\}$ 聚合为一个多项式 $p(X)$ 
	
	$$
	p(X) = p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)
	$$
	
3. 计算 Quotient 多项式 $t(X)$，满足
	
	$$
	p(X) =t(X)\cdot v_H(X)
	$$
	
4. 计算 $t(X)$ 的承诺 $C_t$ ，并发送给 Verifier

	$$
	\begin{split}
	C_t &= \mathsf{cm}([t(x)|_{x \in D}]) = \mathsf{MT.commit}([t(x)|_{x \in D}])
	\end{split}
	$$

#### Round 3

Verifier: 发送随机求值点 $\zeta \stackrel{\$}{\leftarrow} \mathbb{F}_p^* \setminus D$  

Prover: 

1. 计算 $s_i(X)$ 在 $\zeta$ 处的取值：
	
	$$
	s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)
	$$
	
	这里 Prover 可以高效计算 $s_i(\zeta)$ ，由 $s_i(X)$ 的公式得
	
	$$
	\begin{aligned}
	  s_i(\zeta) & = \frac{\zeta^N - 1}{\zeta^{2^i} - 1} \\
	  & = \frac{(\zeta^N - 1)(\zeta^{2^i} +1)}{(\zeta^{2^i} - 1)(\zeta^{2^i} +1)} \\
	  & = \frac{\zeta^N - 1}{\zeta^{2^{i + 1}} - 1} \cdot (\zeta^{2^i} +1) \\
	  & = s_{i + 1}(\zeta) \cdot (\zeta^{2^i} +1)
	\end{aligned} 
	$$
	
	因此 $s_i(\zeta)$ 的值可以通过 $s_{i + 1}(\zeta)$ 计算得到，而
	
	$$
	s_{n-1}(\zeta) = \frac{\zeta^N - 1}{\zeta^{2^{n-1}} - 1} = \zeta^{2^{n-1}} + 1
	$$
	
	因此可以得到一个 $O(n)$ 的算法来计算 $s_i(\zeta)$ ，并且这里不含除法运算。计算过程是：$s_{n-1}(\zeta) \rightarrow s_{n-2}(\zeta) \rightarrow \cdots \rightarrow s_0(\zeta)$ 。
	
2. 定义求值 Domain $H_\zeta'$，包含 $n+1$ 个元素：
	
	$$
	H_\zeta'=\zeta H = \{\zeta, \omega\zeta, \omega^2\zeta,\omega^4\zeta, \ldots, \omega^{2^{n-1}}\zeta\}
	$$
	
3. 计算并发送 $c(X)$ 在 $H_\zeta'$ 上的取值 
	
	$$
	c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})
	$$
4. 计算并发送 $t(\zeta)$
5. 计算并发送 $a(\zeta)$
6. 计算并发送 $q_{ac}(\zeta)$ 
7. 计算并发送 $g(\zeta)$ 

#### Round 4

Verifier: 发送随机数 $r \stackrel{\$}{\leftarrow} \mathbb{F}_p$

Prover:

1. 进行 degree correction ，计算多项式 $t'(X), q'_{ac}(X), g'(X)$ 
	
	$$
	t'(X) = t(X) + r \cdot X \cdot t(X)
	$$
	
	$$
	q'_{ac}(X) = q_{ac}(X) + r \cdot X \cdot q_{ac}(X)
	$$
	
	$$
	g'(X) = g(X) + r \cdot X \cdot g(X)
	$$

2. 计算商多项式 $q_a(X)$ 
	
	$$
	q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
	$$
	
3. 计算商多项式 $q_c(X)$
	
	$$
	q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
	$$
	
4. 计算商多项式 $q_{t'}(X)$

	$$
	q_{t'}(X) = \frac{t'(X) - t'(\zeta)}{X - \zeta}
	$$
	
5. 计算商多项式 $q_{q_{ac}'}(X)$

	$$
	q_{q_{ac}'}(X) = \frac{q_{ac}'(X) - q_{ac}'(\zeta)}{X - \zeta}
	$$

6. 计算商多项式 $q_{g'}(X)$
	
	$$
	q_{g'}(X) = \frac{g'(X) - g'(\zeta)}{X - \zeta}
	$$
7. 将上面的 $5$ 个商多项式用随机数 $r$ 的幂次 batch 成一个多项式
	
	$$
	q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_{t'}(X) + r^4 \cdot q_{q_{ac}'}(X) + r^6 \cdot q_{g'}(X)
	$$
#### Round 5

这一轮将商多项式 $q'(X)$ 对齐到 $2$ 的幂次，以对接 FRI 协议。

1. Verifier 发送随机数 $\lambda \stackrel{\$}{\leftarrow} \mathbb{F}$
2. Prover 计算 

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$
在 $D$ 上的值。

#### Round 6

Prover 和 Verifier 进行 FRI 的 low degree test 证明交互，证明 $q(X)$ 的次数小于 $2^n$ 。

$$
\pi_{q} = \mathsf{FRI.LDT}(q(X), 2^n)
$$

这里包含 $n$ 轮的交互，直到最后将原来的多项式折叠为常数多项式。下面用 $i$ 表示第 $i$ 轮，具体交互过程如下：

- 记 $q^{(0)}(x)|_{x \in D} := q(x)|_{x \in D}$
- 对于 $i = 1,\ldots, n$ ，
  - Verifier 发送随机数 $\alpha^{(i)}$
  - 对于任意的 $y \in D_i$ ，在 $D_{i - 1}$ 中找到 $x$ 满足 $y^2 = x$，Prover 计算

  $$
    q^{(i)}(y) = \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2x}
  $$

  
  - 如果 $i < n$ ，Prover 发送 $[q^{(i)}(x)|_{x \in D_{i}}]$ 的 Merkle Tree 承诺，
  
  $$
  \mathsf{cm}(q^{(i)}(X)) = \mathsf{cm}([q^{(i)}(x)|_{x \in D_{i}}]) = \mathsf{MT.commit}([q^{(i)}(x)|_{x \in D_{i}}])
  $$

  - 如果 $i = n$ ，任选 $x_0 \in D_{n}$ ，Prover 发送 $q^{(i)}(x_0)$ 的值。

> 📝 **Notes**
>
> 如果折叠次数 $r < n$ ，那么最后不会折叠到常数多项式，因此 Prover 在第 $r$ 轮时会发送一个 Merkle Tree 承诺，而不是发送一个值。

#### Round 7

这一轮是接着 Prover 与 Verifier 进行 FRI 协议的 low degree test 交互的查询阶段，Verifier 重复查询 $l$ 次，每一次 Verifier 都会从 $D_0$ 中选取一个随机数，让 Prover 发送在第 $i$ 轮折叠的值及对应的 Merkle Path，用来让 Verifier 验证每一轮折叠的正确性。

重复 $l$ 次：
- Verifier 从 $D_0$ 中随机选取一个数 $s^{(0)} \stackrel{\$}{\leftarrow} D_0$ 
- Prover 打开 $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),t(s^{(0)}),t(-s^{(0)}),q_{ac}(s^{(0)}),q_{ac}(-s^{(0)}),g(s^{(0)}),g(-s^{(0)})$ 的承诺，即这些点的值与对应的 Merkle Path，并发送给 Verifier
  
$$
  (a(s^{(0)}), \pi_{a}(s^{(0)})) \leftarrow \mathsf{MT.open}([a(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (a(-s^{(0)}), \pi_{a}(-s^{(0)})) \leftarrow \mathsf{MT.open}([a(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (c(s^{(0)}), \pi_{c}(s^{(0)})) \leftarrow \mathsf{MT.open}([c(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (c(-s^{(0)}), \pi_{c}(-s^{(0)})) \leftarrow \mathsf{MT.open}([c(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (t(s^{(0)}), \pi_{t}(s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (t(-s^{(0)}), \pi_{t}(-s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (q_{ac}(s^{(0)}), \pi_{q_{ac}}(s^{(0)})) \leftarrow \mathsf{MT.open}([q_{ac}(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (q_{ac}(-s^{(0)}), \pi_{q_{ac}}(-s^{(0)})) \leftarrow \mathsf{MT.open}([q_{ac}(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (g(s^{(0)}), \pi_{g}(s^{(0)})) \leftarrow \mathsf{MT.open}([g(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (g(-s^{(0)}), \pi_{g}(-s^{(0)})) \leftarrow \mathsf{MT.open}([g(x)|_{x \in D_0}], -s^{(0)})
$$

- Prover 计算 $s^{(1)} = (s^{(0)})^2$ 
- 对于 $i = 1, \ldots, n - 1$
  - Prover 发送 $q^{(i)}(s^{(i)}), q^{(i)}(-s^{(i)})$ 的值，并附上 Merkle Path。
  
  $$
  \{(q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], s^{(i)})
  $$
$$
  \{(q^{(i)}(-s^{(i)}), \pi_{q}^{(i)}(-s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], -s^{(i)})
  $$
  - Prover 计算 $s^{(i + 1)} = (s^{(i)})^2$

> 如果折叠次数 $r < n$ ，那么最后一步就要发送 $q^{(r)}(s^{(r)})$ 的值，并附上 Merkle Path。

#### Proof

Prover 发送的证明为

$$
\pi = (C_c,C_{q_{ac}}, C_g, C_t, c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), t(\zeta), a(\zeta), q_{ac}(\zeta), g(\zeta), \pi_{q})
$$
用符号 $\{\cdot\}^l$ 表示在 FRI low degree test 的查询阶段重复查询 $l$ 次产生的证明，由于每次查询是随机选取的，因此花括号中的证明也是随机的。那么 FRI 进行 low degree test 的证明为

$$
\begin{aligned}
  \pi_{q} = &  ( \mathsf{cm}(q^{(1)}(X)), \ldots, \mathsf{cm}(q^{(n - 1)}(X)),q^{(n)}(x_0),  \\
  & \, \{a(s^{(0)}), \pi_{a}(s^{(0)}), a(- s^{(0)}), \pi_{a}(-s^{(0)}),\\
  & \quad c(s^{(0)}), \pi_{c}(s^{(0)}), c(- s^{(0)}), \pi_{c}(-s^{(0)}), \\
  & \quad t(s^{(0)}), \pi_{t}(s^{(0)}), t(- s^{(0)}), \pi_{t}(-s^{(0)}), \\
  & \quad q_{ac}(s^{(0)}), \pi_{q_{ac}}(s^{(0)}), q_{ac}(- s^{(0)}), \pi_{q_{ac}}(-s^{(0)}), \\
  & \quad g(s^{(0)}), \pi_{g}(s^{(0)}), g(- s^{(0)}), \pi_{g}(-s^{(0)}), \\
  & \quad q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)}),q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)}), \ldots, \\
  & \quad q^{(n - 1)}(s^{(n - 1)}), \pi_{q^{(n - 1)}}(s^{(n - 1)}),q^{(n - 1)}(-s^{(n - 1)}), \pi_{q^{(i)}}(-s^{(n - 1)})\}^l)
\end{aligned}
$$

#### Verification

1. Verifier 计算 $s_0(\zeta), \ldots, s_{n-1}(\zeta)$ ，其计算方法可以采用前文提到的递推方式进行计算。
2. Verifier 计算 $p_0(\zeta), \ldots, p_n(\zeta)$
	
	$$
	\begin{split}
	p_0(\zeta) &= s_0(\zeta) \cdot \Big( c(\zeta) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
	p_k(\zeta) &= s_{k-1}(\zeta) \cdot \Big( u_{n-k}\cdot c(\zeta) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot \zeta)\Big) , \quad k=1\ldots n
	\end{split}
	$$
3. Verifier 计算 $p(\zeta)$
	
	$$
	p(\zeta) = p_0(\zeta) + \alpha\cdot p_1(\zeta) + \alpha^2\cdot p_2(\zeta) + \cdots + \alpha^{n}\cdot p_{n}(\zeta)
	$$
	
4. Verifier 计算 $v_H(\zeta)$ 

	
	$$
	v_H(\zeta) = \zeta^N - 1
	$$
	
5. Verifier 验证商多项式的正确性

	$$
	p(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
	$$
6. Verifier 验证内积的正确性

	$$
	a(\zeta)\cdot c(\zeta) \overset{?}{=} q_{ac}(\zeta)\cdot v_H(\zeta) + \zeta\cdot g(\zeta) + (v/N)
	$$
	
7. Verifier 验证 $q(X)$ 的 low degree test 证明，

$$
\mathsf{FRI.LDT.verify}(\pi_{q}, 2^n) \stackrel{?}{=} 1
$$

具体验证过程为，重复 $l$ 次：
- 验证 $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),t(s^{(0)}),t(-s^{(0)}),q_{ac}(s^{(0)}),q_{ac}(-s^{(0)}),g(s^{(0)}),g(-s^{(0)})$  的正确性 ，验证

$$
\mathsf{MT.verify}(\mathsf{cm}(a(X)), a(s^{(0)}), \pi_{a}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(a(X)), a(-s^{(0)}), \pi_{a}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(c(X)), c(s^{(0)}), \pi_{c}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(c(X)), c(-s^{(0)}), \pi_{c}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(s^{(0)}), \pi_{t}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(-s^{(0)}), \pi_{t}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(q_{ac}(X)), q_{ac}(s^{(0)}), \pi_{q_{ac}}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(q_{ac}(X)), q_{ac}(-s^{(0)}), \pi_{q_{ac}}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(g(X)), g(s^{(0)}), \pi_{g}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(g(X)), g(-s^{(0)}), \pi_{g}(-s^{(0)})) \stackrel{?}{=} 1
$$
- Verifier 计算出 $t'(s^{(0)}), t'(-s^{(0)}), q'_{ac}(s^{(0)}), q'_{ac}(-s^{(0)}), g'(s^{(0)}), g'(-s^{(0)})$ 以及 $t'(\zeta), q'_{ac}(\zeta),  g'(\zeta)$ 

$$
t'(s^{(0)}) = t(s^{(0)}) + r \cdot s^{(0)} \cdot t(s^{(0)}), \qquad t'(-s^{(0)}) = t(-s^{(0)}) + r \cdot (-s^{(0)}) \cdot t(-s^{(0)}) 
$$

$$
q_{ac}'(s^{(0)}) = q_{ac}(s^{(0)}) + r \cdot s^{(0)} \cdot q_{ac}(s^{(0)}), \qquad q_{ac}'(-s^{(0)}) = q_{ac}(-s^{(0)}) + r \cdot (-s^{(0)}) \cdot q_{ac}(-s^{(0)}) 
$$

$$
g'(s^{(0)}) = g(s^{(0)}) + r \cdot s^{(0)} \cdot g(s^{(0)}), \qquad g'(-s^{(0)}) = g(-s^{(0)}) + r \cdot (-s^{(0)}) \cdot g(-s^{(0)}) 
$$

$$
t'(\zeta) = t(\zeta) + r \cdot \zeta \cdot t(\zeta)
$$

$$
q_{ac}'(\zeta) = q_{ac}(\zeta) + r \cdot \zeta \cdot q_{ac}(\zeta)
$$

$$
g'(\zeta) = g(\zeta) + r \cdot \zeta \cdot g(\zeta)
$$

- Verifier 根据 $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),t(s^{(0)}),t(-s^{(0)}),q_{ac}(s^{(0)}),q_{ac}(-s^{(0)}),g(s^{(0)}),g(-s^{(0)})$  这些值计算出 $q'(s^{(0)})$ 与 $q'(-s^{(0)})$ ，计算

$$
\begin{align}
q'(s^{(0)}) & = \frac{a(s^{(0)}) - a(\zeta)}{s^{(0)} - \zeta} + r \cdot \left( \frac{c(s^{(0)}) - c(\zeta)}{s^{(0)} - \zeta} + \frac{c(s^{(0)}) - c(\zeta \cdot \omega)}{s^{(0)} - \zeta \cdot \omega} + \ldots + \frac{c(s^{(0)}) - c(\zeta \cdot \omega^{2^{n-1}})}{s^{(0)} - \zeta \cdot \omega^{2^{n-1}}}\right) \\ \\
& \qquad + r^2 \cdot \frac{t'(s^{(0)}) - t'(\zeta)}{s^{(0)} - \zeta} + r^4 \cdot \frac{q_{ac}'(s^{(0)}) - q_{ac}'(\zeta)}{s^{(0)} - \zeta} + r^6 \cdot \frac{g'(s^{(0)}) - g'(\zeta)}{s^{(0)} - \zeta}
\end{align}
$$

$$
\begin{align}
q'(-s^{(0)}) & = \frac{a(-s^{(0)}) - a(\zeta)}{-s^{(0)} - \zeta} + r \cdot \left( \frac{c(-s^{(0)}) - c(\zeta)}{-s^{(0)} - \zeta} + \frac{c(-s^{(0)}) - c(\zeta \cdot \omega)}{-s^{(0)} - \zeta \cdot \omega} + \ldots + \frac{c(-s^{(0)}) - c(\zeta \cdot \omega^{2^{n-1}})}{-s^{(0)} - \zeta \cdot \omega^{2^{n-1}}}\right) \\ \\
& \qquad + r^2 \cdot \frac{t'(-s^{(0)}) - t'(\zeta)}{-s^{(0)} - \zeta} + r^4 \cdot \frac{q_{ac}'(-s^{(0)}) - q_{ac}'(\zeta)}{-s^{(0)} - \zeta} + r^6 \cdot \frac{g'(-s^{(0)}) - g'(\zeta)}{-s^{(0)} - \zeta}
\end{align}
$$

- Verifier 计算

$$
q^{(0)}(s^{(0)}) = (1 + \lambda \cdot s^{(0)}) q'(s^{(0)})
$$

$$
q^{(0)}(-s^{(0)}) = (1 - \lambda \cdot s^{(0)}) q'(-s^{(0)})
$$

- 验证 $q^{(1)}(s^{(1)}), q^{(1)}(-s^{(1)})$ 的正确性

$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)})) \stackrel{?}{=} 1
$$


$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)})) \stackrel{?}{=} 1
$$

- 验证第 $1$ 轮的折叠是否正确

$$
q^{(1)}(s^{(1)}) \stackrel{?}{=} \frac{q^{(0)}(s^{(0)}) + q^{(0)}(- s^{(0)})}{2} + \alpha^{(1)} \cdot \frac{q^{(0)}(s^{(0)}) - q^{(0)}(- s^{(0)})}{2 \cdot s^{(0)}}
$$
- 对于 $i = 2, \ldots, n - 1$
  - 验证 $q^{(i)}(s^{(i)}), q^{(i)}(-s^{(i)})$ 的正确性

  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)})) \stackrel{?}{=} 1
  $$

  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(-s^{(i)}), \pi_{q^{(i)}}(-s^{(i)})) \stackrel{?}{=} 1
  $$
  - 验证第 $i$ 轮的折叠是否正确
  $$
  q^{(i)}(s^{(i)}) \stackrel{?}{=} \frac{q^{(i-1)}(s^{(i - 1)}) + q^{(i - 1)}(- s^{(i - 1)})}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(s^{(i - 1)}) - q^{(i - 1)}(- s^{(i - 1)})}{2 \cdot s^{(i - 1)}}
  $$
- 验证最后是否折叠到常数多项式
  $$
  q^{(n)}(x_0) \stackrel{?}{=} \frac{q^{(n-1)}(s^{(n - 1)}) + q^{(n - 1)}(- s^{(n - 1)})}{2} + \alpha^{(n)} \cdot \frac{q^{(n - 1)}(s^{(n - 1)}) - q^{(n - 1)}(- s^{(n - 1)})}{2 \cdot s^{(n - 1)}}
  $$

## 两种对接 FRI 协议的比较

对比 *缺失的协议 PH23-PCS（四）* 和本文的协议，两种协议的不同点是由证明内积的方式不同导致的，用协议 1 表示文章 *缺失的协议 PH23-PCS（四）* 中的协议，证明内积使用的是 Grand Sum 方法，需要计算类和的多项式 $z(X)$ ，并用三个多项式在 $H$ 上都需要为 $0$ 来约束 $z(X)$ 构造的正确性，即

$$
\begin{aligned}
h_0(X) = &L_0(X)\cdot\big(z(X) - a_0\cdot c_0\big) \\
h_1(X) = &(X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) = &L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{aligned}
$$

用协议 2 表示本文的协议，协议 2 证明内积使用的是 Univariate Sumcheck 方法，需要对 $a(X) \cdot c(X)$ 进行分解，得到 $q_{ac}(X)$ 与 $g(X)$ ，

$$
a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N), \quad \deg(g)<N-1
$$
下面根据这两个协议的不同之处对比下它们之间的计算复杂度。

Prover 计算量：
- 协议 1 需要额外计算的有
	- 计算 $z(X), h_0(X), h_1(X), h_2(X)$
	- 计算承诺 $C_z$
	- 计算 $z(\zeta), z(\omega^{-1} \cdot \zeta)$
	- 计算 $q_z(X)$

- 协议 2 需要额外计算的有
	- 分解 $a(X) \cdot c(X)$ 得到 $q_{ac}(X)$ 与 $g(X)$
	- 计算承诺 $C_{q_{ac}}, C_{g}$
	- 计算 $q_{ac}(\zeta), g(\zeta)$
	- 进行 degree correction，计算 $t'(X), q'_{ac}(X), g'(X)$
	- 计算 $q_{q'_{ac}}(X), q_{g'}(X)$

通过对比可以发现，复杂度涉及多项式的计算方法，但整体上两个协议在 Prover 计算量上差别不是特别大。


Proof 大小：
- 协议 2 需要额外发送的证明有：
	- 多一个多项式的承诺，$C_g$
	- FRI 的 query 阶段，重复 $l$ 次，多发送两个点的值与其 Merkle Path 作为证明
	
通过对比可以发现协议 2 的 proof size 更大，需要额外发送一些哈希值和有限域上的值，且该数量是和重复次数 $l$ 相关的。

Verifier 计算量：
- 协议 1 需要额外计算的有
	- 计算 $L_0(\zeta), L_{N-1}(\zeta)$
	- 计算 $h_0(\zeta), h_1(\zeta), h_2(\zeta)$
	协议 1 额外计算的复杂度为 $2 ~ \mathbb{F}_{\mathsf{inv}} + 9 ~\mathbb{F}_{\mathsf{mul}}$ 。
- 协议 2 需要额外计算的有
	- 验证 $a(\zeta)\cdot c(\zeta) \overset{?}{=} q_{ac}(\zeta)\cdot v_H(\zeta) + \zeta\cdot g(\zeta) + (v/N)$
	- 重复 $l$ 次：多 2 个打开点的验证，如验证 $g(s^{(0)}), g(-s^{(0)})$ 发送的是否正确，这里涉及一些哈希计算
	- 重复 $l$ 次：多计算 degree correction 后的多项式在对应点的值，对于 $x \in \{s^{(0)}, -s^{(0)}, \zeta\}$ ，根据 $t(x)，g(x), q_{ac}(x)$ 来计算对应的 $t'(x), g'(x), q_{ac}'(x)$ ，这里计算一个值的复杂度是 $2 ~ \mathbb{F}_{\mathsf{mul}}$ ，因此这里总的复杂度是 $18l ~ \mathbb{F}_{\mathsf{mul}}$ 。
	
通过对比可以发现协议 1 的 Verifier 计算量要优于协议 2。

综合来看，由于协议 2 中对接 FRI 协议时，需要处理的多项式有 $5$ 个，分别是 $a(X),c(X),t(X),q_{ac}(X),g(X)$ ，这相比协议 1 多了 1 个多项式，同时这 5 个多项式中的次数不统一，需要将 $t(X),q_{ac}(X),g(X)$ 这几个多项式进行 degree correction 提升到 $N - 1$ 次。由于协议开始承诺的是原多项式 $a(X),c(X),t(X),q_{ac}(X),g(X)$ ，相比协议 1 多承诺的 1 个多项式以及进行 degree correction 的操作，就会导致在后续在进行 FRI low degree test 时增加复杂度。

在 query 阶段，协议 2 就需要多发送一个多项式对应查询点的证明，而这需要重复 $l$ 次，这就导致了 proof size 的增加，另一方面，在 verifier 验证阶段，verifier 不仅要多对发过来的查询点的证明进行验证，同时需要自己计算 degree correction 之后的函数在查询点的值，这也是和 $l$ 相关的，导致了 verifier 计算复杂度的增加。

通过上述分析能发现，对接 FRI 协议的复杂度是和需要处理的多项式的个数以及打开点的个数相关的。协议 2 中要处理的多项式更多，因此整体证明大小和 Verifier 计算复杂度也会比协议 1 高。

## References

- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/1284
- [H22] Haböck, Ulrich. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.
