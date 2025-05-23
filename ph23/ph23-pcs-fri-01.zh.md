# 缺失的协议 PH23-PCS（四）

- Jade Xie  <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

本文给出 PH23 协议接一元多项式承诺 FRI-PCS 的方案。

## 对接 FRI

先回顾下 PH23 协议，对于一个 $n$ 元 MLE 多项式 $\tilde{f}(X_0,X_1, \ldots, X_{n - 1})$ ，其写成在 hypercube $\{0,1\}^n$ 上的点值形式：

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$
其中 $N = 2^n$ 。当要证明该 MLE 多项式在一个点 $\vec{u} = (u_0, u_1, \ldots, u_{n-1})$ 的值为 $v$ 时，即

$$
\tilde{f}(u_0, u_1, \ldots, u_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (u_0, u_1, \ldots, u_{n-1})) = v
$$
令 $c_i = \overset{\sim}{eq}(\mathsf{bits}(i), (u_0, u_1, \ldots, u_{n-1}))$ ，那么上面的求值证明就转换为证明一个内积

$$
\sum_{i = 0}^{N - 1} a_i \cdot c_i = \langle \vec{a}, \vec{c} \rangle =  v
$$

$\vec{c}$ 是 Prover 提供的，为了防止 Prover 作弊，需要证明 $\vec{c}$ 是正确构造的。PH23 协议的证明也就分为两部分：

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

为了证明 2 内积的正确性，采用 Grand Sum 方法来证明，构造出多项式 $z(X)$ ，用下面的多项式进行约束，这些多项式同样需要在 $H$ 上的取值为 $0$ ，

$$
\begin{aligned}
h_0(X) = &L_0(X)\cdot\big(z(X) - a_0\cdot c_0\big) \\
h_1(X) = &(X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) = &L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{aligned}
$$

用 Verifier 给出的随机数 $\alpha$ 可以将上述 $n + 4$ 个多项式聚合成一个多项式 $h(X)$ ，

$$
\begin{aligned}
h(X) &= p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)\\  & + \alpha^{n+1} \cdot h_0(X) + \alpha^{n+2} \cdot h_1(X) + \alpha^{n+3} \cdot h_2(X) 
\end{aligned}
$$

那么现在只需要说明 $h(X)$ 在 $H$ 上的取值都为 $0$ ，也就能完成 $\tilde{f}(u_0, u_1, \ldots, u_{n-1}) = v$ 的证明。取 $v_H(X)$ 为 $H$ 上的 Vanishing 多项式，那么存在一个商多项式 $t(X)$ ，满足

$$
h(X) = t(X) \cdot v_H(X)
$$

为了验证商多项式的存在性，Verifier 选取随机点 $\zeta$ ，似乎 Prover 发送 $t(\zeta), h(\zeta)$ 给 Verifier 就可以了，但其实，Prover 承诺的是 $a(X)$ ，$c(X)$ ，$z(X)$ ，$t(X)$ ，因此 Prover 发送的值

$$
\big(a(\zeta), c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), z(\zeta), z(\zeta\cdot\omega^{-1}), t(\zeta)\big)
$$
Verifier 拿着 Prover 发送的 $a(\zeta), c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), z(\zeta), z(\zeta\cdot\omega^{-1})$ 可以自己计算出 $h(\zeta)$ ，$H$ 是公开的，因此 Verifier 可以自行计算出 $v_H(\zeta)$ ，然后验证

$$
h(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
$$

要让 Verifier 相信 Prover 发送过来的这些值没有问题，那么就要用一元多项式的 PCS 来实现。前面的文章已经介绍了用 KZG10 来实现，本文用 FRI-PCS 来进行证明。

通过上面多项式的构造过程，可以得知 $a(X), c(X), z(X), t(X)$ 的次数都为 $N - 1$ 。$a(X)$ 需要在 $\zeta$ 点打开，FRI-PCS 用到了 DEEP 技巧，记 Reed-Solomon 编码空间 $\mathsf{RS}_{k}[\mathbb{F},D]$ 表示
$$
\mathsf{RS}_{k}[\mathbb{F},D] = \{p(x)_{x \in D} : p(X) \in \mathbb{F}[X], \deg p(X) \le k - 1 \}
$$
那么这里要求 Verifier 选取的随机数来自 $\zeta \stackrel{\$}{\leftarrow} \mathbb{F} \setminus D$ 。为了证明 $a(\zeta)$ 的正确性，需要证明商多项式

$$
q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
$$
的次数小于 $N - 1$。

对于 $c(X)$ ，其要打开的点有 $n + 1$ 个，为 $H_{\zeta}' = \{\zeta, \zeta\cdot\omega, \zeta\cdot\omega^2, \ldots, \zeta\cdot\omega^{2^{n-1}} \}$ ，用 [H22] 论文在 Multi-point queries 小节介绍的方法同时打开多个点，令商多项式

$$
q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
$$

这样转换为需要证明 $q_c(X)$ 的次数小于 $N - 1$ 。

对于 $z(X)$ ，类似地，证明商多项式

$$
q_z(X) = \frac{z(X) - z(\zeta)}{X - \zeta} + \frac{z(X) - z(\zeta \cdot \omega^{-1})}{X - \zeta \cdot \omega^{-1}}
$$
次数小于 $N - 1$ 。

对于 $t(X)$ ，证明商多项式

$$
q_t(X) = \frac{t(X) - t(\zeta)}{X - \zeta}
$$
次数小于 $N - 1$ 。

这时，向 Verifier 要一个随机数 $r \stackrel{\$}{\leftarrow} \mathbb{F}$ ，可以将上面要证明的四个商多项式 batch 在一起，令

$$
q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_z(X) + r^3 \cdot q_t(X)
$$

这样只需要调用一次 FRI 的 low degree test 就可以了，证明 $\deg(q'(X)) < N - 1$ 。最后为了对接 FRI low degree test 协议，需要将 $q'(X)$ 的次数对齐到 $2$ 的幂次，即向 Verifier 要一个随机数 $\lambda$ ，证明

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$

的次数小于 $N$ 。

> 📝 **Remark:**
>上面 batch 不同多项式时也可以从 $\mathbb{F}$ 中选取三个不同的随机数 $r_1, r_2,r_3$ ，令
> 
> $$
> q'(X) = q_a(X) + r_1 \cdot q_c(X) + r_2 \cdot q_z(X) + r_3 \cdot q_t(X)
> $$
> 
> 这种方式会比上面用一个随机数的幂次进行 batch 有更高一点的安全性。([BCIKS20])

还有一点需要说明，由于我们用 DEEP 方法来构造商多项式，因此这里要求选取的随机数 $\zeta$ 构成打开点的集合与 Reed-Solomon 编码的群不能相交，即

$$
\{\zeta, \zeta\cdot\omega, \zeta\cdot\omega^2, \ldots, \zeta\cdot\omega^{2^{n-1}}, \zeta \cdot \omega^{-1}\} \cap D = \emptyset
$$


## PH23 + FRI 协议

证明目标：对于一个有 $n$ 个变量的 MLE 多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ ，其表示为点值形式：

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$

证明的目标是证明 $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ 在点 $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$ 处的值为 $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 。

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

3. 构造累加多项式 $z(X)$，满足

$$
\begin{split}
z(1) &= a_0\cdot c_0 \\
z(\omega_{i}) - z(\omega_{i-1}) &=  a(\omega_{i})\cdot c(\omega_{i}), \quad i=1,\ldots, N-1 \\ 
z(\omega^{N-1}) &= v \\
\end{split}
$$

4. 构造约束多项式 $h_0(X), h_1(X), h_2(X)$，满足

$$
\begin{split}
h_0(X) &= L_0(X)\cdot\big(z(X) - c_0\cdot a(X) \big) \\
h_1(X) &= (X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) & = L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{split}
$$

5. 把 $p(X)$ 和 $h_0(X), h_1(X), h_2(X)$ 聚合为一个多项式 $h(X)$，满足

$$
\begin{split}
h(X) &= p(X) + \alpha^{n+1} \cdot h_0(X) + \alpha^{n+2} \cdot h_1(X) + \alpha^{n+3} \cdot h_2(X)
\end{split}
$$

6. 计算 Quotient 多项式 $t(X)$，满足

$$
h(X) =t(X)\cdot v_H(X)
$$

7. 计算 $t(X)$ 和 $z(X)$ 的承诺 $C_t, C_z$ ，并发送给 Verifier

$$
\begin{split}
C_t &= \mathsf{cm}([t(x)|_{x \in D}]) = \mathsf{MT.commit}([t(x)|_{x \in D}]) \\
C_z &= \mathsf{cm}([z(x)|_{x \in D}]) = \mathsf{MT.commit}([z(x)|_{x \in D}])
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

4. 计算并发送 $z(\zeta)$ 和 $z(\omega^{-1}\cdot\zeta)$
5. 计算并发送 $t(\zeta)$
6. 计算并发送 $a(\zeta)$

#### Round 4

Verifier: 发送随机数 $r \stackrel{\$}{\leftarrow} \mathbb{F}_p$

Prover:

1. 计算商多项式 $q_a(X)$ 

$$
q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
$$
2. 计算商多项式 $q_c(X)$

$$
q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
$$
3. 计算商多项式 $q_z(X)$

$$
q_z(X) = \frac{z(X) - z(\zeta)}{X - \zeta} + \frac{z(X) - z(\zeta \cdot \omega^{-1})}{X - \zeta \cdot \omega^{-1}}
$$
4. 计算商多项式 $q_t(X)$

$$
q_t(X) = \frac{t(X) - t(\zeta)}{X - \zeta}
$$
5. 将上面的四个商多项式用随机数 $r$ 的幂次 batch 成一个多项式

$$
q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_z(X) + r^3 \cdot q_t(X)
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
  - 对于任意的 $y \in D_i$ ，在 $D_{i - 1}$ 中找到 $x$ 满足 $x^2 = y$，Prover 计算

  $$
    q^{(i)}(y) = \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(x) - q^{(i - 1)}(-x)}{2x}
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
- Prover 打开 $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),z(s^{(0)}),z(-s^{(0)}),t(s^{(0)}),t(-s^{(0)})$ 的承诺，即这些点的值与对应的 Merkle Path，并发送给 Verifier
  
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
  (z(s^{(0)}), \pi_{z}(s^{(0)})) \leftarrow \mathsf{MT.open}([z(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (z(-s^{(0)}), \pi_{z}(-s^{(0)})) \leftarrow \mathsf{MT.open}([z(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (t(s^{(0)}), \pi_{t}(s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (t(-s^{(0)}), \pi_{t}(-s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], -s^{(0)})
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
\pi = (C_c,C_t, C_z, c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), z(\zeta), z(\omega^{-1} \cdot \zeta), t(\zeta), a(\zeta), \pi_{q})
$$
用符号 $\{\cdot\}^l$ 表示在 FRI low degree test 的查询阶段重复查询 $l$ 次产生的证明，由于每次查询是随机选取的，因此花括号中的证明也是随机的。那么 FRI 进行 low degree test 的证明为

$$
\begin{aligned}
  \pi_{q} = &  ( \mathsf{cm}(q^{(1)}(X)), \ldots, \mathsf{cm}(q^{(n - 1)}(X)),q^{(n)}(x_0),  \\
  & \, \{a(s^{(0)}), \pi_{a}(s^{(0)}), a(- s^{(0)}), \pi_{a}(-s^{(0)}),\\
  & \quad c(s^{(0)}), \pi_{c}(s^{(0)}), c(- s^{(0)}), \pi_{c}(-s^{(0)}), \\
  & \quad z(s^{(0)}), \pi_{z}(s^{(0)}), z(- s^{(0)}), \pi_{z}(-s^{(0)}), \\
  & \quad t(s^{(0)}), \pi_{t}(s^{(0)}), t(- s^{(0)}), \pi_{t}(-s^{(0)}), \\
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

4. Verifier 计算 $v_H(\zeta), L_0(\zeta), L_{N-1}(\zeta)$ 


$$
v_H(\zeta) = \zeta^N - 1
$$

$$
L_0(\zeta) = \frac{1}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-1}
$$

$$
L_{N-1}(\zeta) = \frac{\omega^{N-1}}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-\omega^{N-1}}
$$
5. Verifier 计算 $h_0(\zeta), h_1(\zeta), h_2(\zeta)$

$$
\begin{split}
h_0(\zeta) &= L_0(\zeta)\cdot\big(z(\zeta) - c_0\cdot a(\zeta) \big) \\
h_1(\zeta) &= (\zeta-1)\cdot\big(z(\zeta)-z(\omega^{-1}\cdot \zeta)-a(\zeta)\cdot c(\zeta)) \\
h_2(\zeta) & = L_{N-1}(\zeta)\cdot\big( z(\zeta) - v \big) \\
\end{split}
$$

6. Verifier 计算 $h(\zeta)$

$$
\begin{split}
h(\zeta) &= p(\zeta) + \alpha^{n+1} \cdot h_0(\zeta) + \alpha^{n+2} \cdot h_1(\zeta) + \alpha^{n+3} \cdot h_2(\zeta)
\end{split}
$$

7. Verifier 验证商多项式的正确性

$$
h(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
$$

8. Verifier 验证 $q(X)$ 的 low degree test 证明，

$$
\mathsf{FRI.LDT.verify}(\pi_{q}, 2^n) \stackrel{?}{=} 1
$$

具体验证过程为，重复 $l$ 次：
- 验证  $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),z(s^{(0)}),z(-s^{(0)}),t(s^{(0)}),t(-s^{(0)})$ 的正确性 ，验证

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
\mathsf{MT.verify}(\mathsf{cm}(z(X)), z(s^{(0)}), \pi_{z}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(z(X)), z(-s^{(0)}), \pi_{z}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(s^{(0)}), \pi_{t}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(-s^{(0)}), \pi_{t}(-s^{(0)})) \stackrel{?}{=} 1
$$

- Verifier 根据 $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),z(s^{(0)}),z(-s^{(0)}),t(s^{(0)}),t(-s^{(0)})$  这些值计算出 $q^{(0)}(s^{(0)})$ 与 $q^{(0)}(-s^{(0)})$ ，对于 $x \in \{s^{(0)}, -s^{(0)} \}$ ，计算

$$
\begin{align}
q'(x) & = \frac{a(x) - a(\zeta)}{x - \zeta} + r \cdot \left( \frac{c(x) - c(\zeta)}{x - \zeta} + \frac{c(x) - c(\zeta \cdot \omega)}{x - \zeta \cdot \omega} + \ldots + \frac{c(x) - c(\zeta \cdot \omega^{2^{n-1}})}{x - \zeta \cdot \omega^{2^{n-1}}}\right) \\ \\
& \qquad + r^2 \cdot \left(\frac{z(x) - z(\zeta)}{x - \zeta} + \frac{z(x) - z(\zeta \cdot \omega^{-1})}{x - \zeta \cdot \omega^{-1}}\right) + r^3 \cdot \frac{t(x) - t(\zeta)}{x - \zeta}
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

## 总结

本文用 ph23 协议对接 FRI 协议来实现 MLE 多项式的 PCS，该协议的内积证明是通过 Grand Sum 实现的，其也能通过 Univariate Sumcheck ，在下一篇文章中将具体介绍这种协议，并与该协议进行对比。

## References

- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/1284
- [H22] Haböck, Ulrich. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.
