# Zeromorph 系列协议复杂度分析

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

## Evaluation 证明协议（朴素版）复杂度分析

协议描述文档：[Evaluation 证明协议（朴素版）](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md#protocol-description)

下面我们先给出一个简单朴素的协议实现，方便理解。

### 公共输入

- MLE 多项式 $\tilde{f}$ 的承诺 $\mathsf{cm}([[\tilde{f}]]_n)$
- 求值点 $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- 求值结果 $v = \tilde{f}(\mathbf{u})$

### Witness

- MLE 多项式  $\tilde{f}$ 在 $n$ 维 HyperCube 上的点值向量 $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

### Round 1

Prover 发送余数多项式的承诺

- 计算 $n$ 个余数 MLE 多项式， $\{\tilde{q}_k\}_{k=0}^{n-1}$ 
- 构造余数 MLE 多项式所映射到的 Univariate 多项式 $\hat{q}_k=[[\tilde{q}_k]]_k, \quad 0 \leq k < n$
- 计算并发送它们的承诺：$\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1})$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{k=0}^{n-1} (X_k-u_k) \cdot \tilde{q}_k(X_0,X_1,\ldots, X_{k-1})
$$

Prover 计算，$\pi_k=\mathsf{cm}(X^{D_{max}-2^k+1}\cdot \hat{q}_k), \quad 0\leq k<n$ ，作为 $\deg(\hat{q}_k)<2^k$ 的 Degree Bound 证明 ，一并发送给 Verifier

> Prover:
>
> - 直接用 [Zeromorph](https://eprint.iacr.org/2023/917) 论文 Appendix A.2 的算法能计算出 $\tilde{q}_k$ 在 Hypercube 上的值，即可以得到 $Q_k$ 的系数，根据论文的结论，整个算法复杂度为 $(2^{n+1} - 3) ~ \mathbb{F}_{\mathsf{add}}$ 以及 $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。这里不计入加法的复杂度，因此计算出 $\hat{q}_k=[[\tilde{q}_k]]_k, \quad 0 \leq k < n$ 的复杂度为 $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 计算 $\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1})$ ，这里涉及 MSM 算法，对于每一个 $\mathsf{cm}(\hat{q}_{k})$ ，多项式 $q_{k}$ 的系数有 $2^k$ 个，复杂度为 $\mathsf{msm}(2^k,\mathbb{G}_1)$ ，因此这一步的总复杂度为
> $$
>   \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
> $$
> - 计算 $\pi_k=\mathsf{cm}(X^{D_{max}-2^k+1}\cdot \hat{q}_k), \quad 0\leq k<n$ ，
>   - 计算 $X^{D_{max}-2^k+1}\cdot \hat{q}_k$ ，这里涉及多项式的乘法，$\deg(\hat{q}_k) = 2^k - 1$ ，复杂度记为 $\mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1)$ ，因此总复杂度为
>       $$
>           \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1)
>       $$
>   - 计算 $\pi_k=\mathsf{cm}(X^{D_{max}-2^k+1}\cdot \hat{q}_k), \quad 0\leq k<n$ ，复杂度为
>       $$
>           \sum_{k=0}^{n-1} \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) = n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)
>       $$
>   因此这一步的总复杂度为
>  $$
>   \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)
>  $$
>
> 因此这一轮的总复杂度为
> 
> $$
>   (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)
> $$


> 💡 这里计算多项式的乘法，$X^{D_{max}-2^k+1}\cdot \hat{q}_k$ 应该可以优化，直接挪动 $\hat{q}_k$ 的系数就可以了。

### Round 2

1. Verifier 发送随机数 $\zeta\in \mathbb{F}_p^*$

2. Prover 计算辅助多项式 $r(X)$ 与商多项式 $h(X)$，并发送 $\mathsf{cm}(h)$ 
- 计算 $r(X)$ ，

$$
r(X) = [[\tilde{f}]]_{n} - v\cdot \Phi_{n}(\zeta) - \sum_{k=0}^{n-1} \Big(\zeta^{2^k}\cdot \Phi_{n-k-1}(\zeta^{2^{k+1}}) - u_k\cdot \Phi_{n-k}(\zeta^{2^{k}})\Big)\cdot \hat{q}_k(X)
$$

- 计算 $h(X)$ 及其承诺 $\mathsf{cm}(h)$， 作为 $r(X)$ 在 $X=\zeta$ 点取值为零的证明

$$
h(X) = \frac{r(X)}{X-\zeta}
$$

- [ ] 修改计算 $\Phi_n(\zeta)$ 的复杂度

> Prover:
>
> - 先根据随机数 $\zeta$ 计算出 $\zeta$ 的幂次，即 $\zeta^2, \ldots, \zeta^{2^{n}}$ ，涉及 $n$ 次有限域的乘法，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 计算 $r(X)$ ，
>   - 计算 $\Phi_n(\zeta)$,
>        $$
>         \Phi_n(\zeta) = \sum_{i=0}^{n-1} \zeta^{2^i}
>        $$
> 
>    这里可以直接用前面计算出的 $\zeta$ 的幂次直接进行累加，涉及到的是有限域的加法，因此不做记录。
>   - 计算 $v \cdot \Phi_n(\zeta)$ ，涉及一次有限域乘法，复杂度为 $\mathbb{F}_{\mathsf{mul}}$ 。
>   - 计算 $\Phi_{n-k-1}(\zeta^{2^{k+1}})$ ，由于
>       $$
>       \Phi_{n-k-1}(X^{2^{k+1}}) = 1 + X^{2^{k + 1}} + X^{2 \cdot 2^{k + 1}} + \ldots + X^{(2^{n - k - 1} - 1) \cdot 2^{k + 1}}
>       $$
>     因此
>       $$
>       \Phi_{n-k-1}(\zeta^{2^{k+1}}) = 1 + \zeta^{2^{k + 1}} + \zeta^{2 \cdot 2^{k + 1}} + \ldots + \zeta^{(2^{n - k - 1} - 1) \cdot 2^{k + 1}}
>       $$ 
>     这里依然可以通过有限域的加法直接计算得到，同理对于计算 $\Phi_{n-k}(\zeta^{2^{k}})$ 也是一样的，通过有限域的加法得到。
>   - 计算 $\zeta^{2^k}\cdot \Phi_{n-k-1}(\zeta^{2^{k+1}}) - u_k\cdot \Phi_{n-k}(\zeta^{2^{k}})$ 这里就涉及两次有限域的乘法，复杂度为 $2 ~ \mathbb{F}_{\mathsf{mul}}$ ， $k$ 次累加就为 $2n ~ \mathbb{F}_{\mathsf{mul}}$ 。
>   - 计算 $\Big(\zeta^{2^k}\cdot \Phi_{n-k-1}(\zeta^{2^{k+1}}) - u_k\cdot \Phi_{n-k}(\zeta^{2^{k}})\Big)\cdot \hat{q}_k(X)$ ，涉及多项式的乘法，复杂度为 $\mathsf{polymul}(0, 2^k - 1)$ 。$k$ 经过累加之后，总复杂度为 
>       $$
>           \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>       $$
>   因此计算 $r(X)$ 的总复杂度为
>
>   $$
>       \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{mul}} +  \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) = (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>   $$
>
> - 计算 $\mathsf{cm}(h)$ ，先计算 $h(X)$ ，其可以用线性除法的方式得到，复杂度与 $r(X)$ 的次数相关，由于 $\deg(r) = 2^{n - 1} - 1$ ，因此这里多项式除法的复杂度为 $(2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}}$ ，接着计算承诺，其复杂度为 $\mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)$ 。 这里总复杂度为
>   $$
>       (2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
>   $$
>
> 这一轮的总复杂度为：
> $$
>   (3n + 2^{n - 1}) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
> $$


### Verification 

Verifier 验证下面的等式

- 构造 $\mathsf{cm}(r)$ 的承诺：

$$
\mathsf{cm}(r) = \mathsf{cm}([[\tilde{f}]]_{n}) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)
$$

- 验证 $r(\zeta) = 0$

$$
e(\mathsf{cm}(r), \ [1]_2) = e(\mathsf{cm}(h), [\tau]_2 - \zeta\cdot [1]_2)
$$

- 验证 $(\pi_0, \pi_1, \ldots, \pi_{n-1})$ 是否正确，即验证所有的余数多项式的 Degree Bound： $\deg(\hat{q}_i)<2^i$ ，对于 $0\leq i<n$

$$
e(\mathsf{cm}(\hat{q}_i), [\tau^{D_{max}-2^i+1}]_2) = e(\pi_i, [1]_2), \quad 0\leq i<n
$$


> Verifier:
>
> - 构造 $\mathsf{cm}(r)$ 的承诺
>   - 先根据随机数 $\zeta$ 计算出 $\zeta$ 的幂次，即 $\zeta^2, \ldots, \zeta^{2^{n}}$ ，涉及 $n$ 次有限域的乘法，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
>   - $\mathsf{cm}(v\cdot \Phi_{n}(\zeta))$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>   - 计算 $\sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$ ，复杂度为
>     $$
>        n( 2 ~ \mathbb{F}_{\mathsf{mul}}  + \mathsf{EccMul}^{\mathbb{G}_1}) + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} = 2n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>     $$
>   - 计算 $\mathsf{cm}([[\tilde{f}]]_{n}) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$ ，就是三个椭圆曲线上的点相加，复杂度为 $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$ 。
>   
>   构造 $r$ 的承诺的总复杂度为
>   $$
>     (3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>   $$
> - 验证 $r(\zeta) = 0$
>   - 计算 $[\tau]_2 - \zeta\cdot [1]_2$ ，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2}$
>   - 计算 $e(\mathsf{cm}(r), \ [1]_2)$ 与 $e(\mathsf{cm}(h), [\tau]_2 - \zeta\cdot [1]_2)$ ，涉及两个椭圆曲线上的配对操作，记为 $2~P$ 。
>   
>   这一步的总复杂度为
>   $$
>     \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
>   $$
> - 验证 $(\pi_0, \pi_1, \ldots, \pi_{n-1})$ 是否正确，
>     $$
>         e(\mathsf{cm}(\hat{q}_i), [\tau^{D_{max}-2^i+1}]_2) = e(\pi_i, [1]_2), \quad 0\leq i<n
>     $$
>     这里每一次涉及的复杂度为 $2 ~ P$ ，因此总复杂度为 $2n ~ P$ 。
>
> 这一轮的总复杂度为
>
> $$
> (3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} +  (2n + 2)~P
> $$

### 汇总

> **Prover 计算复杂度：**
> 
> $$
> \begin{aligned}
>     & (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) \\
>     & + (3n + 2^{n - 1}) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
>     = & ( 3 \cdot 2^{n - 1} + 3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
>     & + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
> \end{aligned}
> $$
> 
> **Verifier 计算复杂度：**
> 
> $$
> (3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} +  (2n + 2)~P
> $$
> 
> **证明大小：**
> 
> Prover 发送的证明有 
> 
> $$
> (\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1}), \pi_0, \ldots, \pi_{n - 1}, \mathsf{cm}(h))
> $$
> 
> 总计为 $(2n + 1) \mathbb{G}_1$ .


代入多项式相乘的复杂度  $\mathsf{polymul}(a, b) = (a + 1) (b + 1) ~ \mathbb{F}_{\mathsf{mul}} = (ab + a + b + 1) ~ \mathbb{F}_{\mathsf{mul}}$ ，得到

Prover 复杂度：

$$
\begin{align}
& ( 3 \cdot 2^{n - 1} + 3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
& + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
=  & ( \frac{3}{2}  N + 3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + ((D_{max} + 2)(N - 1) - \frac{1}{3}(N^2 - 1))~ \mathbb{F}_{\mathsf{mul}} + (N - 1) ~ \mathbb{F}_{\mathsf{mul}}\\
& + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
= & ((D_{max} + \frac{9}{2}) N - \frac{1}{3} N^2 + 3n - D_{max} - \frac{14}{3}) ~ \mathbb{F}_{\mathsf{mul}} \\
& + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
\end{align}
$$

Verifier 复杂度：

$$
(3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} +  (2n + 2)~P
$$

Proof size:

$$
(2n + 1) \mathbb{G}_1
$$

## Evaluation 证明协议（优化版-Degree Bound 聚合）

协议描述文档：[Evaluation 证明协议（优化版）](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md#optimized-protocol)

### 公共输入

- MLE 多项式 $\tilde{f}$ 映射到 Univariate 多项式 $f(X)=[[\tilde{f}]]_n$ 的承诺 $\mathsf{cm}([[\tilde{f}]]_n)$
- 求值点 $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- 求值结果 $v = \tilde{f}(\mathbf{u})$

### Witness

- MLE 多项式  $\tilde{f}$ 的求值向量 $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

### Round 1

第一轮：Prover 发送余数多项式的承诺

- 计算 $n$ 个余数 MLE 多项式， $\{q_i\}_{i=0}^{n-1}$ 
- 构造余数 MLE 多项式所映射到的 Univariate 多项式 $\hat{q}_i=[[q_i]]_i, \quad 0 \leq i < n$
- 计算并发送它们的承诺：$\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1})$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{i=0}^{n-1} (X_k-u_k) \cdot q_i(X_0,X_1,\ldots, X_{k-1})
$$

> Prover:
> 
> - 直接用 [Zeromorph](https://eprint.iacr.org/2023/917) 论文 Appendix A.2 的算法能计算出 $q_i$ 在 Hypercube 上的值，即可以得到 $Q_i$ 的系数，根据论文的结论，整个算法复杂度为 $(2^{n+1} - 3) ~ \mathbb{F}_{\mathsf{add}}$ 以及 $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。这里不计入加法的复杂度，因此计算出 $Q_i=[[q_i]]_i, \quad 0 \leq i < n$ 的复杂度为 $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 计算 $\mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1})$ ，这里涉及 MSM 算法，对于每一个 $\mathsf{cm}(q_{k})$ ，多项式 $q_{k}$ 的系数有 $2^k$ 个，复杂度为 $\mathsf{msm}(2^k,\mathbb{G}_1)$ ，因此这一步的总复杂度为
> 
> $$
>   \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
> $$
>
> 因此这一轮的总复杂度为
> 
> $$
>   (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
> $$
>

- [ ] 计算 $Q_i$ 的算法及代码细节 

### Round 2

1. Verifier 发送随机数 $\beta\in \mathbb{F}_p^*$ 用来聚合多个 Degree Bound 证明

2. Prover 构造 $\bar{q}(X)$ 作为聚合商多项式 $\{\hat{q}_i(X)\}$ 的多项式，并发送其承诺 $\mathsf{cm}(\bar{q})$ 

$$
\bar{q}(X) = \sum_{i=0}^{n-1} \beta^i \cdot X^{2^n-2^i}\hat{q}_i(X)
$$
> Prover： 
> 
> - 可以先由随机数 $\beta$ 计算得到 $\beta^2, \ldots, \beta^{n - 1}$ ，复杂度为 $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$
> - 计算 $\beta^i \cdot X^{2^n-2^i}\hat{q}_i(X)$ ，为多项式的乘法，复杂度为 $\mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{polymul}(0, 2^n - 1)$ ，因此求和相加的复杂度为
>     $$
>     \begin{aligned}
>         & \sum_{i = 0}^{n - 1} \big( \mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{polymul}(0, 2^n - 1) \big) \\
>         = & n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1)
>     \end{aligned}
>     $$
> - 计算 $\mathsf{cm}(\bar{q})$ ，复杂度为 $\mathsf{msm}(2^n , \mathbb{G}_1)$
> 
> 这一轮的总复杂度为
> 
> $$
> (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{msm}(2^n , \mathbb{G}_1)
> $$

### Round 3

1. Verifier 发送随机数 $\zeta\in \mathbb{F}_p^*$ ，用来挑战多项式在 $X=\zeta$ 处的取值

2. Prover 计算 $h_0(X)$ 与 $h_1(X)$

- 计算 $r(X)$ ，

$$
r(X) = \hat{f}(X) - v\cdot \Phi_{n}(\zeta) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot\hat{q}_i(X)
$$
- 计算 $s(X)$ ，

$$
s(X) = \bar{q}(X) - \sum_{k=0}^{n-1} \beta^k \cdot \zeta^{2^n-2^k}\cdot \hat{q}_k(X)
$$

- 计算商多项式 $h_0(X)$ 与 $h_1(X)$ 

$$
h_0(X) = \frac{r(X)}{X-\zeta}, \qquad h_1(X) = \frac{s(X)}{X-\zeta}
$$

> Prover：
> 
> - 先根据随机数 $\zeta$ 计算出 $\zeta$ 的幂次，即 $\zeta^2, \ldots, \zeta^{2^{n}}$ ，涉及 $n$ 次有限域的乘法，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 计算 $r(X)$ 复杂度与上面朴素协议的分析一致，复杂度为
> 
>     $$
>     (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>     $$
> 
> - 计算 $s(X)$
>   - $\beta^k \cdot \zeta^{2^n-2^k}$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
>   - $\beta^k \cdot \zeta^{2^n-2^k}\cdot \hat{q}_k(X)$ ，复杂度为 $\mathsf{polymul}(0, 2^k - 1)$
>   
>   因此 计算 $s(X) = \bar{q}(X) - \sum_{k=0}^{n-1} \beta^k \cdot \zeta^{2^n-2^k}\cdot \hat{q}_k(X)$ 复杂度为
> 
>   $$
>     n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>   $$
> 
> - 计算商多项式 $h_0(X)$ 与 $h_1(X)$ ，这里可以用线性除法进行计算，由于 $\deg(r) = 2^n - 1$ ，$\deg(s(X)) = 2^n - 1$ ，因此这里的复杂度为
> 
>     $$
>         (2^{n + 1} - 2) ~ \mathbb{F}_{\mathsf{mul}}
>     $$
> 
> 因此这一轮的总复杂度为
> 
> $$
> \begin{aligned}
>     & n ~ \mathbb{F}_{\mathsf{mul}} + (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} \\
>     & + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) +  n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) +  (2^{n + 1} - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
>      = & (4n + 2^{n + 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
> \end{aligned}
> $$

### Round 4

1. Verifier 发送随机数 $\alpha\in \mathbb{F}_p^*$ ，用来聚合 $h_0(X)$ 与 $h_1(X)$

2. Prover 计算 $h(X)$ 并发送其承诺 $\mathsf{cm}(h)$ 

$$
h(X)=(h_0(X) + \alpha\cdot h_1(X))\cdot X^{D_{max}-2^n+2}
$$ 

> Prover:
> 
> - 计算 $h_0(X) + \alpha\cdot h_1(X)$ ，复杂度为 $\mathsf{polymul}(0, 2^n - 2)$ 。
> - $(h_0(X) + \alpha\cdot h_1(X))\cdot X^{D_{max}-2^n+1}$ 复杂度为 $\mathsf{polymul}(2^n - 2, D_{max}-2^n+1)$ 。
> - 计算 $\mathsf{cm}(h)$ 复杂度为 $\mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})$
> 
> 这一轮的总复杂度为
> 
> $$
> \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})
> $$

### Verification 

Verifier

- 构造 $\mathsf{cm}(r)$ 的承诺：

$$
\mathsf{cm}(r) = \mathsf{cm}(f) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)
$$

- 构造 $\mathsf{cm}(s)$ 的承诺：

$$
\mathsf{cm}(s) = \mathsf{cm}(\bar{q}) - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)
$$
- 验证 $r(\zeta) = 0$ 与 $s(\zeta) = 0$

$$
e(\mathsf{cm}(r) + \alpha\cdot \mathsf{cm}(s), \ [\tau^{D-2^n+2}]_2) = e(\mathsf{cm}(h),\ [\tau]_2 - \zeta\cdot [1]_2)
$$


> 证明大小：
> 
> 在 Verifier 进行验证前，其收到的证明为
> 
> $$
> \pi = (\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1}), \mathsf{cm}(\bar{q}), \mathsf{cm}(h))
> $$
> 
> 因此证明的大小为 $(n + 2) ~ \mathbb{G}_1$ 。


> Verifier:
> 
> - 构造 $\mathsf{cm}(r)$ 的承诺
>   - 计算 $\zeta^2, \zeta^4, \ldots, \zeta^{2^n}$ ，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
>   - 计算 $\mathsf{cm}(v\cdot \Phi_{n}(\zeta))$ 复杂度： $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>   - 计算 $\sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$
>     - $\Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$ 复杂度为：$2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>     
>     得到的 $n$ 个 $\mathbb{G}_1$ 上的点还要相加，因此这步计算的总复杂为 $2n ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~\mathsf{EccAdd}^{\mathbb{G}_1}$
> 
>   - 将上边得到的三个 $\mathbb{G}_1$ 上的点相加，复杂度为 $2~\mathsf{EccAdd}^{\mathbb{G}_1}$ 。
>   
>   因此计算出 $\mathsf{cm}(r)$ 的复杂度为 
> 
>   $$
>     \begin{aligned}
>         & n ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} + 2n ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~\mathsf{EccAdd}^{\mathbb{G}_1} + 2~\mathsf{EccAdd}^{\mathbb{G}_1} \\
>         = & (3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>     \end{aligned}
>   $$
> 
> - 计算 $\mathsf{cm}(s)$ 的承诺
>   - 先计算出 $\beta^2, \ldots, \beta^{n - 1}$ ，复杂度为 $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$
>   - 计算 $\beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)$ 复杂度为： $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$， 因此求和计算的复杂度不仅有每一项的计算，同时计算完椭圆曲线上的点之后，还要将这 $n$ 个点相加，因此计算 $\sum_{i=0}^{n-1} \beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)$ 的总复杂度为
>   
>     $$
>     n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>     $$
> 
>   - 计算 $\mathsf{cm}(\bar{q}) - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)$ 的复杂度为两个椭圆曲线 $\mathbb{G}_1$ 上的点相加，为 $\mathsf{EccAdd}^{\mathbb{G}_1}$ 。
>   
>   因此计算出 $\mathsf{cm}(s)$ 的复杂度为
> 
>   $$
>   (2n - 2) ~ \mathbb{F}_{\mathsf{mul}}  + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>   $$
> 
> - 验证 $r(\zeta) = 0$ 与 $s(\zeta) = 0$
>   - 计算 $\mathsf{cm}(r) + \alpha\cdot \mathsf{cm}(s)$ 和 $[\tau]_2 - \zeta\cdot [1]_2$ 的复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2}$
>   - 计算 $e(\mathsf{cm}(r) + \alpha\cdot \mathsf{cm}(s), \ [\tau^{D-2^n+2}]_2)$ 与 $e(\mathsf{cm}(h),\ [\tau]_2 - \zeta\cdot [1]_2)$ ，涉及两个椭圆曲线上的配对操作，记为 $2~P$ 。
>   
>   因此这一步的总复杂度为
> 
>   $$
>   \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
>   $$
> 
> 因此在 Verification 阶段的总复杂度为
> 
> $$
> \begin{aligned}
>   & (3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + (2n - 2) ~ \mathbb{F}_{\mathsf{mul}}  + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & +   \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P \\
>   = & (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
> \end{aligned}
> $$

### 汇总

> **Prover 计算复杂度：**
> 
> $$
> \begin{aligned}
>   & (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) \\
>   & + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{msm}(2^n , \mathbb{G}_1) \\
>   & + (4n + 2^{n + 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
>   & + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})\\
>   = & (3 \cdot 2^n + 5n - 5) ~ \mathbb{F}_{\mathsf{mul}} +  n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) \\
>   & + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1)\\
>   & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})
> \end{aligned}
> $$
> 
> **Verifier 计算复杂度：**
> 
> $$
> (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
> $$
> 
> **证明大小：**
> 
> $$
> (n + 2) ~ \mathbb{G}_1
> $$

代入多项式相乘的复杂度  $\mathsf{polymul}(a, b) = (a + 1) (b + 1) ~ \mathbb{F}_{\mathsf{mul}} = (ab + a + b + 1) ~ \mathbb{F}_{\mathsf{mul}}$ ，得到

Prover 复杂度：

$$
\begin{align}
& (3 \cdot 2^n + 5n - 5) ~ \mathbb{F}_{\mathsf{mul}} +  n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) \\
& + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1)\\
& + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1}) \\
=  & (3 N + 5n - 5) ~ \mathbb{F}_{\mathsf{mul}} +  nN ~ \mathbb{F}_{\mathsf{mul}} + (\frac{2}{3}N^2 - \frac{2}{3}) ~ \mathbb{F}_{\mathsf{mul}} \\
& + (2N - 2) ~ \mathbb{F}_{\mathsf{mul}} + (N - 1) ~ \mathbb{F}_{\mathsf{mul}} + ((D_{max} + 3)N - N^2 - D_{max} - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
& + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})  \\
=  & (-\frac{1}{3}N^2 +nN +(D_{max} +9)N + 5n - \frac{32}{3} - D_{max}) ~ \mathbb{F}_{\mathsf{mul}}  \\
& + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})  \\
\end{align}
$$
> 
> **Verifier 计算复杂度：**
> 
> $$
> (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
> $$
> 
> **证明大小：**
> 
> $$
> (n + 2) ~ \mathbb{G}_1
> $$
## zeromorph-pcs (degree bound optimized)

协议描述文档：[Zeromorph-PCS (Part II)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-02.md)

### 公共输入

- MLE 多项式 $\tilde{f}$ 映射到 Univariate 多项式 $f(X)=[[\tilde{f}]]_n$ 的承诺 $\mathsf{cm}(f)$
- 求值点 $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- 求值结果 $v = \tilde{f}(\mathbf{u})$

### Witness

- MLE 多项式  $\tilde{f}$ 的求值向量 $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

### Round 1

- Prover 计算 $n$ 个余数 MLE 多项式， $\{\tilde{q}_i\}_{i=0}^{n-1}$ 
- Prover 构造余数 MLE 多项式所映射到的 Univariate 多项式 $q_i=[[\tilde{q}_i]]_i, \quad 0 \leq i < n$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{i=0}^{n-1} (X_i-u_i) \cdot \tilde{q}_i(X_0,X_1,\ldots, X_{i-1})
$$

- Prover 计算并发送它们的承诺：$\mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1})$

**Prover Cost：** 

这一轮和上一个 batched degree bound 协议一样，这一轮的复杂度为

$$
(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
$$

### Round 2

1. Verifier 发送随机数 $\beta\in \mathbb{F}_q^*$ 
2. Prover 构造 $g(X)$ 作为聚合多项式 $\{q_i(X)\}$ 的多项式，满足

$$
g(X^{-1}) = \sum_{i=0}^{n-1} \beta^i \cdot X^{-2^i+1}\cdot q_i(X)
$$

3. Prover 计算并发送 $g(X)$ 的承诺 $\mathsf{cm}(g)$ 


**Prover Cost：** 
 
- 可以先由随机数 $\beta$ 计算得到 $\beta^2, \ldots, \beta^{n - 1}$ ，复杂度为 $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$
- 计算 $g(X)$ 的方式可以按下面这种方式计算

$$
g(X) = \sum_{i = 0}^{n - 1} \beta^i \cdot X^{2^i-1}{q}_i(X^{-1})
$$

$X^{2^i-1}{q}_i(X^{-1})$ 其实是 $q_i(X)$ 的系数进行翻转，然后再乘以 $\beta^i$ ，这里的复杂度为 $\mathsf{polymul}(0, 2^i - 1)$ ，因此求和相加的复杂度为

$$
\sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^i - 1)
$$

- 计算 $\mathsf{cm}(g)$ ，由于 $\deg(g) = 2^{n - 1} - 1$ ，因此复杂度为 $\mathsf{msm}(2^{n - 1} , \mathbb{G}_1)$ 。

这一轮的总复杂度为

$$
(n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^i - 1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1)
$$

### Round 3

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

**Prover Cost：**

- 先根据随机数 $\zeta$ 计算出 $\zeta$ 的幂次，即 $\zeta^2, \ldots, \zeta^{2^{n}}$ ，涉及 $n$ 次有限域的乘法，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $\zeta^{-1}$ ，复杂度为 $\mathbb{F}_{\mathsf{inv}}$ 。
- 计算 $g(\zeta^{-1})$ ，用 Horner 求值方法，由于 $\deg(g) = 2^{n - 1} - 1$ ，因此复杂度为 $2^{n - 1} ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $q_g(X)$ ，可以使用线性除法，复杂度为 $(2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $r_{\zeta}(X)$ ，计算方法与上面的优化协议一致，因此复杂度也是一样的，为

$$
 (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
$$
- 计算 $s_{\zeta}(X)$ ，计算 $\beta^i \cdot \zeta^{2^i - 1} \cdot q_i(X)$ 的复杂度为 $\mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^i - 1)$ ，因此整体计算 $s_{\zeta}(X)$ 的复杂度为

$$
n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1}\mathsf{polymul}(0, 2^i - 1)
$$

- 计算 $w_r(X)$ 和 $w_s(X)$ ，都可以用多项式的线性除法算法，由于 $\deg(r_{\zeta}) = 2^n - 1$ , $\deg(s_{\zeta}) = 2^{n - 1} - 1$ ，因此这一步的复杂度为 $(3 \cdot 2^{n - 1} - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。

- 计算 $\mathsf{cm}(q_g)$ ，复杂度为 $\mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)$ 。

这一轮的总复杂度为

$$
\begin{aligned}
    & n ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + 2^{n - 1} ~ \mathbb{F}_{\mathsf{mul}} + (2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
    & + n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1}\mathsf{polymul}(0, 2^i - 1) + (3 \cdot 2^{n - 1} - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
    = & (5 \cdot 2^{n - 1} + 4n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
\end{aligned}
$$

### Round 4

1. Verifier 发送随机数 $\alpha\in \mathbb{F}_p^*$ ，用来聚合 $w_r(X)$ 与 $w_s(X)$

2. Prover 计算 $w(X)$ 并发送其承诺 $\mathsf{cm}(w)$ 

$$
w(X) = w_r(X) + \alpha\cdot w_s(X)
$$

**Prover Cost：**

- 计算 $w_r(X) + \alpha \cdot w_s(X)$ ，复杂度为 $\mathsf{polymul}(0, 2^{n - 1} - 2)$ 。
- 计算 $\mathsf{cm}(w)$ ，由于 $\deg(w(X)) = 2^n - 2$ ，因此复杂度为 $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$ 。

这一轮的总复杂度为

$$
\mathsf{polymul}(0, 2^{n - 1} - 2) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
$$

### Proof

总共 $n+3$ 个 $\mathbb{G}_1$ ，$1$ 个 $\mathbb{F}_q$：

$$
\pi= \Big( \mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1}), \mathsf{cm}(g), \mathsf{cm}(q_g), \mathsf{cm}(w), g(\zeta^{-1})\Big)
$$

**Proof size:**

$$
\begin{aligned}
    (n + 3) \cdot \mathbb{G}_1 + \mathbb{F}_q
\end{aligned}
$$


### Verification

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


**Verifier Cost:**

- 构造 $\mathsf{cm}(r_{\zeta})$ ，复杂度与上面的优化协议一致，为

$$
(3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
$$

- 构造 $\mathsf{cm}(s_{\zeta})$ 
  - 计算 $\zeta^{-1}$ , 复杂度为 $\mathbb{F}_{\mathsf{inv}}$ 。
  - 计算 $g(\zeta^{-1}) \cdot [1]_1$ ，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$ 。
  - 计算 $(\zeta^{-1})^{2^2 - 1}, \ldots, (\zeta^{-1})^{2^{n -1} - 1}$ ，复杂度为 $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。
  - 计算 $\beta^i \cdot (\zeta^{-1})^{2^i - 1} \cdot \mathsf{cm}(\hat{q}_i)$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$ ，因此 $n$ 个 $\mathbb{G}_1$ 上的点再求和的复杂度为
  
  $$
    n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
  $$
  - 上面计算得到了两个椭圆曲线 $\mathbb{G}_1$ 上的点，这时再相加，复杂度为 $\mathsf{EccAdd}^{\mathbb{G}_1}$ 。
  
  因此构造 $\mathsf{cm}(s_{\zeta})$ 这一步的复杂度为

$$
\begin{aligned}
    & \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1} + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
    = & (2n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1}
\end{aligned}
$$

> - 验证 $r_{\zeta}(\zeta) = 0$ 与 $s_{\zeta}(\zeta) = 0$
>   - 计算 $\mathsf{cm}(r_{\zeta}) + \alpha \cdot \mathsf{cm}(s_{\zeta}) + \zeta \cdot \mathsf{cm}(w)$ ，复杂度为 $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1}$ 。
>  - 计算 $e(\mathsf{cm}(r_{\zeta}) + \alpha \cdot \mathsf{cm}(s_{\zeta}) + \zeta \cdot \mathsf{cm}(w), [1]_2)$ 与 $e(\mathsf{cm}(w), [\tau]_2)$ ，复杂度为 $2~P$ 。
>   
>   因此这一步的总复杂度为 $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1} + 2~P$ 。
> 
> - 验证 $g(\zeta^{-1})$ 的正确性
>   - 计算 $\mathsf{cm}(g) - g(\zeta^{-1}) \cdot [1]_1 + \zeta^{-1} \cdot \mathsf{cm}(q_g)$ ，复杂度为 $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$ 。
>   - 计算 $e(\mathsf{cm}(g) - g(\zeta^{-1}) \cdot [1]_1 + \zeta^{-1} \cdot \mathsf{cm}(q_g), [1]_2)$ 与 $e(\mathsf{cm}(q_g), [\tau]_2)$ ，复杂度为 $2~P$ 。
>  
>   因此这一步的总复杂度为 $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P$ 。

可以将 3 和 4 中的 pairing 进行合并，即验证

$$
e(\mathsf{cm}(r_{\zeta}) + \alpha \cdot \mathsf{cm}(s_{\zeta}) + \zeta \cdot \mathsf{cm}(w) + \mathsf{cm}(g) - g(\zeta^{-1}) \cdot [1]_1 + \zeta^{-1} \cdot \mathsf{cm}(q_g), [1]_2) \overset{?}{=} e(\mathsf{cm}(w) + \mathsf{cm}(q_g), [\tau]_2)
$$

复杂度为 $4 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 6 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P$

因此在 Verification 阶段的总复杂度为

$$
\begin{aligned}
    & (3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + (2n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + 4 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 6 ~\mathsf{EccAdd}^{\mathbb{G}_1} + 2~P  \\
    = & (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (2n + 6) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 7) ~ \mathsf{EccAdd}^{\mathbb{G}_1}  + 2~P
\end{aligned}
$$

### 汇总

**Prover 计算复杂度：**

$$
\begin{aligned}
    & (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) \\
    & + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^i - 1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1)\\
    & + (5 \cdot 2^{n - 1} + 4n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
    & + \mathsf{polymul}(0, 2^{n - 1} - 2) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (\frac{7}{2} \cdot 2^n + 5n - 6) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} \\
    & + 3 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^{n - 1} - 2) \\
    & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

即

$$
\begin{aligned}
    & (\frac{7}{2} \cdot 2^n + 5n - 6) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} \\
    & + 3 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^{n - 1} - 2) \\
    & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

**Verifier 计算复杂度：**

$$
\begin{aligned}
    (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (2n + 6) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 7) ~ \mathsf{EccAdd}^{\mathbb{G}_1}  + 2~P
\end{aligned}
$$

**证明大小：**

$$
\begin{aligned}
    (n + 3) \cdot \mathbb{G}_1 + \mathbb{F}_q
\end{aligned}
$$