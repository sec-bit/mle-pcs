# Zeromorph-PCS (Part II)

## 1. 优化思路

## 2. 协议描述

### Evaluation 证明协议

#### 公共输入

- MLE 多项式 $\tilde{f}$ 映射到 Univariate 多项式 $f(X)=[[\tilde{f}]]_n$ 的承诺 $\mathsf{cm}(f)$
- 求值点 $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- 求值结果 $v = \tilde{f}(\mathbf{u})$

#### Witness

- MLE 多项式  $\tilde{f}$ 的求值向量 $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

#### Round 1

- Prover 计算 $n$ 个余数 MLE 多项式， $\{\tilde{q}_i\}_{i=0}^{n-1}$ 
- Prover 构造余数 MLE 多项式所映射到的 Univariate 多项式 $q_i=[[\tilde{q}_i]]_i, \quad 0 \leq i < n$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{i=0}^{n-1} (X_i-u_i) \cdot \tilde{q}_i(X_0,X_1,\ldots, X_{i-1})
$$

- Prover 计算并发送它们的承诺：$\mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1})$

#### Round 2

1. Verifier 发送随机数 $\beta\in \mathbb{F}_q^*$ 
2. Prover 构造 $g(X)$ 作为聚合多项式 $\{q_i(X)\}$ 的多项式，满足

$$
g(X^{-1}) = \sum_{i=0}^{n-1} \beta^i \cdot X^{-2^i+1}\cdot q_i(X)
$$

3. Prover 计算并发送 $g(X)$ 的承诺 $\mathsf{cm}(g)$ 

#### Round 3

1. Verifier 发送随机数 $\zeta\in \mathbb{F}_p^*$ ，用来挑战多项式在 $X=\zeta$ 处的取值

2. Prover 计算 $g(\zeta^{-1})$，并计算商多项式 $q_g(X)$ 

$$
q_g(X) = \frac{g(X) - g(\zeta^{-1})}{X-\zeta^{-1}}
$$

3. Prover 构造线性化多项式 $r_\zeta(X)$ ，$s_\zeta(X)$ 

- 计算 $r_\zeta(X)$ ，

$$
r_\zeta(X) = f(X) - v\cdot \Phi_{n}(\zeta) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot q_i(X)
$$
- 计算 $s_\zeta(X)$ ，它在 $X=\zeta$ 处取值为零

$$
s_\zeta(X) = g(\zeta^{-1}) - \sum_i\beta^i\zeta^{2^i-1}\cdot q_i(X)
$$

- 计算商多项式 $w_r(X)$ 与 $w_s(X)$ 

$$
w_r(X) = \frac{r_\zeta(X)}{X-\zeta}, \qquad w_s(X) = \frac{s_\zeta(X)}{X-\zeta}
$$

4. 计算并发送承诺 $\mathsf{cm}(q_g)$ 


#### Round 4

1. Verifier 发送随机数 $\alpha\in \mathbb{F}_p^*$ ，用来聚合 $w_r(X)$ 与 $w_s(X)$

2. Prover 计算 $w(X)$ 并发送其承诺 $\mathsf{cm}(w)$ 

$$
w(X) = w_r(X) + \alpha\cdot w_s(X)
$$

#### Proof 

总共 $n+3$ 个 $\mathbb{G}_1$ ，$1$ 个 $\mathbb{F}_q$：

$$
\pi= \Big( \mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1}), \mathsf{cm}(g), \mathsf{cm}(q_g), \mathsf{cm}(w), g(\zeta^{-1})\Big)
$$

#### Verification 

Verifier

1. 构造 $\mathsf{cm}(r_\zeta)$ 的承诺：

$$
\mathsf{cm}(r_\zeta) = \mathsf{cm}(f) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(q_i)
$$

2. 构造 $\mathsf{cm}(s_\zeta)$ 的承诺：

$$
\mathsf{cm}(s_\zeta) = g(\zeta^{-1})\cdot[1]_1 - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{-2^i+1}\cdot \mathsf{cm}(q_i)
$$
3. 验证 $r_\zeta(\zeta) = 0$ 与 $s_\zeta(\zeta) = 0$

$$
e(\mathsf{cm}(r_\zeta) + \alpha\cdot \mathsf{cm}(s_\zeta), \ [1]_2) = e(\mathsf{cm}(w),\ [\tau]_2 - \zeta\cdot [1]_2)
$$

转换下，可以得到下面的 Pairing 等式：

$$
e(\mathsf{cm}(r_\zeta) + \alpha\cdot \mathsf{cm}(s_\zeta) + \zeta\cdot\mathsf{cm}(w), \ [1]_2) = e(\mathsf{cm}(w),\ [\tau]_2)
$$

4. 验证 $g(\zeta^{-1})$ 的正确性

$$
e(\mathsf{cm}(g) - g(\zeta^{-1})\cdot [1]_1 + \zeta^{-1}\cdot\mathsf{cm}(q_g),\  [1]_2) = e(\mathsf{cm}(q_g), \ [\tau]_2)
$$


## 3. 性能分析