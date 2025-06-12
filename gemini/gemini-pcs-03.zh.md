# # Gemini-PCS (Part III)

## 1. 优化思路

## 2. 协议描述

下面的协议证明一个 MLE 多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ 在点 $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$ 处的值 $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$ 。其中 $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ 表示为如下的系数形式：

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{n-1} f_i\cdot X_0^{i_0}X_1^{i_1}\cdots X_{n-1}^{i_{n-1}}
$$

### 公共输入

1. 向量 $\vec{f}=(f_0, f_1, \ldots, f_{n-1})$ 的承诺 $C_f$

$$
C_f = \mathsf{KZG10.Commit}(\vec{f})
$$

2. 求值点 $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$

3. $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$

### Witenss 

1. 多项式 $f(X)$ 的系数 $f_0, f_1, \ldots, f_{n-1}$


### Round 1.

1. Prover 计算 $h_1(X), h_2(X), \ldots, h_{n-1}(X)$，使得：

$$
h_{i+1}(X^2) = \frac{h_i(X) + h_i(-X)}{2} + u_i\cdot \frac{h_i(X) - h_i(-X)}{2X}
$$

其中 $h_0(X) = f(X)$

2. Prover 计算承诺 $(H_1, H_2, \ldots, H_{n-1})$，使得：

$$
H_{i+1} = \mathsf{KZG10.Commit}(h_{i+1}(X))
$$

3. Prover 发送 $(H_1, H_2, \ldots, H_{n-1})$

### Round 2.

1. Verifier 发送随机点 $\beta\in\mathbb{F}_p$

2. Prover 计算 $h_0(\beta), h_1(\beta), \ldots, h_{n-1}(\beta)$

3. Prover 计算 $h_0(-\beta), h_1(-\beta), \ldots, h_{n-1}(-\beta)$

4. Prover 计算 $h_0(\beta^2)$

5. Prover 发送 $\{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}$，以及 $h_0(\beta^2)$

### Round 3.

1. Verifier 发送随机值 $\gamma\in\mathbb{F}_p$，用于聚合多个多项式

2. Prover 计算 $h(X)$ 

$$
h(X) = h_0(X) + \gamma\cdot h_1(X) + \gamma^2\cdot h_2(X) + \cdots + \gamma^{n-1}\cdot h_{n-1}(X)
$$

3. 定义一个新的 Domain $D$，包含 $3$ 个元素：

$$
D = \{\beta, -\beta, \beta^2\}
$$

4. Prover 计算二次多项式 $h^*(X)$ 使得它在 $D$ 上取值等于 $h(X)$ 的取值：

$$
h^*(X) = h(\beta)\cdot \frac{(X+\beta)(X-\beta^2)}{2\beta(\beta-\beta^2)} + h(-\beta)\cdot \frac{(X-\beta)(X-\beta^2)}{2\beta(\beta^2+\beta)} + h(\beta^2)\cdot \frac{X^2-\beta^2}{\beta^4-\beta^2}
$$

5. Prover 计算商多项式 $q(X)$

$$
q(X) = \frac{h(X) - h^*(X)}{(X^2-\beta^2)(X-\beta^2)}
$$

6. Prover 计算 $q(X)$ 的承诺 $C_q$

$$
C_q = \mathsf{KZG10.Commit}(q(X))
$$

5. Prover 发送 $C_q$

### Round 4.

1. Verifier 发送随机点 $\zeta\in\mathbb{F}_p$

2. Prover 计算线性化多项式 $r(X)$，它在 $X=\zeta$ 处取值为 $0$，即 $r(\zeta) = 0$：

$$
r(X) = h(X) - h^*(\zeta) - (\zeta^2-\beta^2)(\zeta-\beta^2)\cdot q(X)
$$

3. Prover 计算商多项式 $w(X)$

$$
w(X) = \frac{r(X)}{(X-\zeta)}
$$

4. Prover 计算 $w(X)$ 的承诺 $C_w$：

$$
C_w = \mathsf{KZG10.Commit}(w(X))
$$

5. Prover 发送 $C_w$

### 证明表示

可以看出，证明包括 $n+1$ 个 $\mathbb{G}_1$ 元素，包括 $2n+1$ 个 $\mathbb{F}_p$ 元素。

$$
\pi=\Big(H_1, H_2, \ldots, H_{n-1}, C_q, C_w, \{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}, h_0(\beta^2) \Big)
$$

### 验证过程

1. Verifier 计算 $(h_1(\beta^2), h_2(\beta^2), \ldots, h_{n-1}(\beta^2))$

$$
h_{i+1}(\beta^2) = \frac{h_i(\beta) + h_i(-\beta)}{2} + u_i\cdot \frac{h_i(\beta) - h_i(-\beta)}{2\beta}
$$

2. Verifier 检查  $h_{n}(\beta^2)$ 是否等于所要证明的多项式求值 $v=\tilde{f}(\vec{u})$

$$
h_n(\beta^2) \overset{?}{=} v
$$

3. Verifier 计算 $h(X)$ 的承诺 $C_h$

$$
C_h = C_f + \gamma\cdot H_1 + \gamma^2\cdot H_2 + \cdots + \gamma^{n-1}\cdot H_{n-1}
$$

4. Verifier 计算 $r_\zeta(X)$ 的承诺 $C_r$:

$$
C_r = C_h - h^*(\zeta)\cdot[1]_1 - (\zeta^2-\beta^2)(\zeta-\beta^2)\cdot C_q
$$

5. Verifier 检查 $C_w$ 是否为 $C_r$ 在 $X=\zeta$ 处的求值证明：

$$
\mathsf{KZG10.Verify}(C_r, \zeta, 0, C_w) \overset{?}{=} 1
$$

或者直接展开为 Pairing 形式：

$$
e\Big(C_r + \zeta\cdot C_w, [1]_2\Big) \overset{?}{=} e\Big(C_w, [\tau]_2 \Big)
$$

## 3. 优化性能分析


## References

