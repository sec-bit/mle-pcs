# Gemini-PCS (Part IV)

本文介绍一个不同的优化协议，它采用了 FRI 协议的 Query-phase 中选取点的思路，对 $h_0(X)$ 挑战 $X=\beta$ 求值，进而对折叠后的多项式 $h_1(X)$ 挑战 $X=\beta^2$，依次类推，直到 $h_{n-1}(\beta^{2^{n-1}})$ 。这样做的好处是，每一次 $h_i(X)$ 的打开点可以在验证 $h_{i+1}(X)$ 的折叠时复用，从而总共可以节省 $n$ 个打开点。

## 1. 优化思路

## 2. 协议描述

证明目标：一个 $n$ 个变量的 MLE 多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ 在点 $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$ 处的值 $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$ 。

其中 MLE 多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ 表示为如下的系数形式：

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{n-1} c_i\cdot X_0^{i_0}X_1^{i_1}\cdots X_{n-1}^{i_{n-1}}
$$

### 公共输入

1. 向量 $\vec{c}=(c_0, c_1, \ldots, c_{n-1})$ 的承诺 $C_f$

$$
C_f = \mathsf{KZG10.Commit}(\vec{c})
$$

2. 求值点 $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$

3. $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$

### Witness 

- 多项式 $f(X)$ 的系数 $\vec{c}=(c_0, c_1, \ldots, c_{n-1})$

### Round 1.

1. Prover 记 $h_0(X) = f(X)$，然后计算折叠多项式 $h_1(X), h_2(X), \ldots, h_{n-1}(X)$，使得：

$$
h_{i+1}(X^2) = \frac{h_i(X) + h_i(-X)}{2} + u_i\cdot \frac{h_i(X) - h_i(-X)}{2X}
$$

2. Prover 计算承诺 $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$，使得：

$$
C_{h_{i+1}} = \mathsf{KZG10.Commit}(h_{i+1}(X))
$$

3. Prover 发送 $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$

### Round 2.

1. Verifier 发送随机点 $\beta\in\mathbb{F}_p$

2. Prover 计算 $h_0(\beta)$

3. Prover 计算 $h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})$

4. Prover 发送 $\big(h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\big)$

### Round 3.

1. Verifier 发送随机值 $\gamma\in\mathbb{F}_p$，用于聚合多个多项式

2. Prover 计算 $q(X)$ ，满足下面的等式

$$
q(X) = \frac{h_0(X)-h_0(\beta)}{X-\beta}+ \sum_{i=0}^{n-1} \gamma^{i+1}\cdot \frac{h_i(X)-h_i(-\beta^{2^i})}{X+\beta^{2^i}}
$$

3. 定义一个新的 Domain $D$，包含 $3$ 个元素：

$$
D = \{\beta, -\beta, -\beta^2, \ldots, -\beta^{2^{n-1}}\}
$$

4. Prover 计算发送承诺 $C_q=\mathsf{KZG10.Commit}(q(X))$
### Round 4.

1. Verifier 发送随机点 $\zeta\in\mathbb{F}_q$

2. Prover 计算线性化多项式 $L_\zeta(X)$，它在 $X=\zeta$ 处取值为 $0$，即 $L_\zeta(\zeta) = 0$：

$$
L_\zeta(X) = v_D(\zeta)\cdot q(X) - \frac{v_D(\zeta)}{\zeta-\beta}\cdot(h_0(X)-h_0(\beta)) - \sum_{i=0}^{n-1} \gamma^{i+1}\cdot \frac{v_D(\zeta)}{\zeta+\beta^{2^i}}\cdot(h_i(X)-h_i(-\beta^{2^i}))
$$

3. Prover 计算商多项式 $w(X)$

$$
w(X) = \frac{L_\zeta(X)}{(X-\zeta)}
$$

4. Prover 计算并发送 $w(X)$ 的承诺 $C_w$：

$$
C_w = \mathsf{KZG10.Commit}(w(X))
$$

### 证明表示

可以看出，单次证明包括 $n+1$ 个 $\mathbb{G}_1$ 元素，包括 $n+1$ 个 $\mathbb{F}_q$ 元素。

$$
\pi=\Big(C_{f_1}, C_{f_2}, \ldots, C_{f_{n-1}}, C_{q}, C_w, h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\Big)
$$

### 验证过程

1. Verifier 计算 $(h_1(\beta^2), h_2(\beta^{2^2}), \ldots, h_{n-1}(\beta^{2^{n-1}}), h_n(\beta^{2^n}))$

$$
h_{i+1}(\beta^{2^{i+1}}) = \frac{h_i(\beta^{2^i}) + h_i(-\beta^{2^i})}{2} + u_i\cdot \frac{h_i(\beta^{2^i}) - h_i(-\beta^{2^i})}{2\beta^{2^i}}
$$

2. Verifier 检查  $h_{n}(\beta^{2^n})$ 是否等于所要证明的多项式求值 $v=\tilde{f}(\vec{u})$

$$
h_n(\beta^{2^n}) \overset{?}{=} v
$$

3. Verifier 计算 $L_\zeta(X)$ 的承诺 $C_L$:

$$
C_L = v_D(\zeta)\cdot C_q - e_0\cdot(C_{h_0} - h_0(\beta)\cdot[1]_1) - \sum_{i=0}^{n-1} e_{i+1}\cdot(C_{h_i} - h_i(-\beta^{2^i})\cdot[1]_1)
$$

这里 $e_0, e_1, \ldots, e_n$ 定义如下:

$$
\begin{aligned}
e_0 &= \frac{v_D(\zeta)}{\zeta - \beta} \\
e_{i+1} &= \gamma^{i+1}\cdot \frac{v_D(\zeta)}{\zeta+\beta^{2^i}}, \quad i=0,1,\ldots,n-1
\end{aligned}
$$

4. Verifier 检查 $C_w$ 是否为 $C_L$ 在 $X=\zeta$ 处的求值证明：

$$
\mathsf{KZG10.Verify}(C_L, \zeta, 0, C_w) \overset{?}{=} 1
$$

或者直接展开为 Pairing 形式：

$$
e\Big(C_L + \zeta\cdot C_w, [1]_2\Big) \overset{?}{=} e\Big(C_w, [\tau]_2 \Big)
$$

## 3. 优化性能分析


## References

