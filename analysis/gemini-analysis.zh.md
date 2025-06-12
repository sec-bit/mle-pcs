# Gemini-PCS 算法复杂度分析

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

## 优化版本 1

- 协议描述文档：[Gemini-PCS (Part III)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-3.md)
- 对应 python 代码：[bcho_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/bcho_pcs.py)

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

### Round 1

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

> Prover: 
> 
> - 对于 $i = 1, \ldots, n-1$ 计算多项式 $h_{i}$ ，其计算公式为
> 
> $$
> h_{i}(X) = h_e^{(i-1)}(X) + u_{i-1} \cdot h_o^{(i-1)}(X)
> $$
> 
> > 💡 这里 prover 不需要计算和发送 $h_n(X)$ 的原因是最后一个为常数多项式，其应该就等于求值的结果 $v$ ，Verifier 可以通过对 $h_{n - 1}(X)$ 进行 oracle 来进行验证。
> 
>   那么计算 $h_{i}(X)$ 就按上式进行计算，$h_{i - 1}(X)$ 的系数是已知的，$h_e^{(i-1)}(X)$ 和 $h_o^{(i-1)}(X)$ 的系数就分别是 $h_{i - 1}(X)$ 系数的偶数项和奇数项，因此主要的复杂度在计算 $u_{i-1} \cdot h_o^{(i-1)}(X)$ ，这里涉及有限域元素的乘积，$h_{i - 1}(X)$ 的系数有 $2^{n - (i - 1)}$ 个，那么 $h_o^{(i-1)}(X)$ 的系数取 $h_{i - 1}(X)$ 的奇数项系数，因此系数有 $2^{n - (i - 1) - 1} = 2^{n - i}$ 个，因此分别计算 $u_{i - 1}$ 与这些系数相乘的复杂度为 $2^{n - i} ~ \mathbb{F}_{\mathsf{mul}}$ 。
>
>   因此计算 $h_1(X), \ldots, h_{n - 1}(X)$ 的复杂度为 
>
>   $$
>       \sum_{i = 1}^{n - 1} 2^{n - i} ~ \mathbb{F}_{\mathsf{mul}} = (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}}
>   $$
>
> - 计算 $H_1 = [h_{1}(\tau)]_1,\ldots,H_{n - 1} = [h_{n-1}(\tau)]_1$ 的复杂度为
>
>   $$
>   \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{n - i}, \mathbb{G}_1) = \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1)
>   $$
>
> 因此这一轮的计算复杂度总共为
>
> $$
> (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1)
> $$

### Round 2

1. Verifier 发送随机点 $\beta\in\mathbb{F}_p$

2. Prover 计算 $h_0(\beta), h_1(\beta), \ldots, h_{n-1}(\beta)$

3. Prover 计算 $h_0(-\beta), h_1(-\beta), \ldots, h_{n-1}(-\beta)$

4. Prover 计算 $h_0(\beta^2)$

5. Prover 发送 $\{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}$，以及 $h_0(\beta^2)$

Prover:

- 计算 $\beta^2$ 复杂度为 $\mathbb{F}_{\mathsf{mul}}$ ，计算 $- \beta$ 只涉及有限域上的加减操作，因此不做计入。
- 使用 Horner 的方法求一个点在多项式处的值，多项式的系数有多少个就会涉及多少个有限域上的乘法操作，因此计算 $\{h_i(\beta), h_i(-\beta)\}_{i = 0}^{n - 1}$ 复杂度为

$$
2 \sum_{i = 0}^{n - 1} 2^{n - i}  ~ \mathbb{F}_{\mathsf{mul}} = (2^{n + 1} - 4) ~ \mathbb{F}_{\mathsf{mul}}
$$

- 计算 $h_0(\beta^2)$ 的复杂度为 $2^{n} ~ \mathbb{F}_{\mathsf{mul}}$

因此这一轮的总复杂度为

$$
\mathbb{F}_{\mathsf{mul}} + (2^{n + 1} - 4) ~ \mathbb{F}_{\mathsf{mul}} + 2^{n} ~ \mathbb{F}_{\mathsf{mul}} = (3 \cdot 2^{n} - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$


> 🎈 代码中 Prover 也计算了 $\{h_i(\beta^2)\}_{i = 1}^{n - 1}$ 的值，其实可以不用计算，可以节省 Prover 的计算量，这样的话 Verifier 需要在验证阶段自己计算这些值，增加了 Verifier 一些计算量。
> 
> ```python
> # Compute evaluations of h_i(X) at beta, -beta, beta^2
> evals_pos = []
> evals_neg = []    
> evals_sq = []
> for i in range(k):
>     poly = h_poly_vec[i]
>     poly_at_beta = UniPolynomial.evaluate_at_point(poly, beta)
>     poly_at_neg_beta = UniPolynomial.evaluate_at_point(poly, -beta)
>     poly_at_beta_sq = UniPolynomial.evaluate_at_point(poly, beta * beta)
>     evals_pos.append(poly_at_beta)
>     evals_neg.append(poly_at_neg_beta)
>     evals_sq.append(poly_at_beta_sq)
> ```

### Round 3


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

Prover:

- 先计算出 $\gamma^2, \ldots, \gamma^{n - 1}$ ，复杂度为 $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $h(X)$ ，复杂度主要来自 $\gamma^i \cdot h_i(X)$ ，这里涉及有限域上的乘法，需要将 $\gamma^i$ 去分别乘以多项式 $h_i(X)$ 的各个系数，因此系数有多少个就涉及多少次有限域上的乘法草组欧，最后再将这些多项式相加，这里就只涉及有限域的加法操作了，因此计算出 $h(X)$ 的复杂度为

$$
\sum_{i = 1}^{n - 1} 2^{n - i} ~ \mathbb{F}_{\mathsf{mul}} = (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}}
$$

- 计算 $h^*(X)$ ，

    $$
    h^*(X) = h(\beta) \cdot \frac{(X + \beta)(X - \beta^2)}{2 \beta (\beta - \beta^2)} + h(-\beta) \cdot \frac{(X - \beta)(X - \beta^2)}{2 \beta (\beta^2 + \beta)} + h(\beta^2) \cdot \frac{X^2 - \beta^2}{\beta^4 - \beta^2}
    $$

    如果按上式的计算方式计算

    - 计算 $\beta^4$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
    - 计算分母 $2 \beta (\beta - \beta^2), 2 \beta (\beta^2 + \beta), \beta^4 - \beta^2$ ，复杂度为 $2 ~ \mathbb{F}_{\mathsf{mul}}$
    - 计算分母 $2 \beta (\beta - \beta^2), 2 \beta (\beta^2 + \beta), \beta^4 - \beta^2$ 的逆元，复杂度为 $3 ~ \mathbb{F}_{\mathsf{inv}}$ 
    - 用上一步计算的逆元，再分别乘以 $h(\beta), h(-\beta), h(\beta^2)$ ，复杂度为 $3 ~ \mathbb{F}_{\mathsf{mul}}$
    - 分子的三个多项式都可以直接展开构造，分别为

    $$
    \begin{aligned}
        & X^2 + (\beta - \beta^2) X - \beta^3  \\
        & X^2 - (\beta + \beta^2) X + \beta^3 \\
        & X^2 - \beta^2
    \end{aligned}
    $$

    这里要计算 $\beta^3$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$ 。

    - 用这三个多项式再分别乘以前面的系数，复杂度为

    $$
    2 ~ \mathbb{F}_{\mathsf{mul}} + 2 ~\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{mul}} = 5 ~ \mathbb{F}_{\mathsf{mul}}
    $$

    因此计算 $h^*(X)$ 的总复杂度为

    $$
    (1 + 2 + 3 + 1 + 5) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}}= 12 ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}}
    $$

    > 🎈 代码里直接用的是将这三个点 $(\beta, h(\beta)), (-\beta, h(-\beta)), (\beta^2, h(\beta^2))$ 直接进行插值，用的是 Barycenreic 插值方法。
    > 
    > - [ ] 分析该插值的复杂度，会涉及多项式的乘法和除法


- 计算商多项式 $q(X)$ ，分母为三个一次多项式相乘，分子为 $h(X) - h^*(X)$ ，然后和分母的多项式相除，因此复杂度为

$$
\mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3)
$$

- 计算 $C_q$ ，多项式 $q((X)$ 的次数为 $\deg(q) = 2^n - 1 - 3 = 2^n - 4$ ，因此计算 $C_q$ 的复杂度为

$$
\mathsf{msm}(2^n - 3, \mathbb{G}_1)
$$

因此这一轮的总复杂度为

$$
\begin{aligned}
    & (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + 12 ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}}\\
    &  + \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) \\
    = & (2^{n} + n + 8) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    &  + \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) \\
\end{aligned}
$$

### Round 4

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

Prover：

- 计算 $\zeta^2$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
- 计算 $r(X)$ 
  - 计算 $h^*(\zeta)$ ，由于 $\deg(h^*) = 2$ ，因此计算该多项式在一个点的取值的复杂度为 $3 ~ \mathbb{F}_{\mathsf{mul}}$
  - 计算 $(\zeta^2 - \beta^2)(\zeta - \beta^2)$ ，涉及一次有限域的乘法，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
  - 计算 $(\zeta^2 - \beta^2)(\zeta - \beta^2) \cdot q(X)$ ，$\deg(q) =2^n - 4$ ，因此这里的复杂度为 $\mathsf{polymul}(0, 2^n - 4)$
  
  因此计算 $r(X)$ 的总复杂度为

  $$
    4 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4)
  $$

- 计算商多项式 $w(X)$ ，可以用线性除法，被除的多项式的次数为多少，就涉及多少的有限域上的乘法操作，由于 $\deg(r) = 2^n - 1$ ，因此这一步的复杂度为 $(2^n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $C_w$ ，复杂度为 $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$ 。

这一轮的总复杂度为

$$
\begin{aligned}
    & \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4) + (2^n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (2^n + 4) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) 
\end{aligned}
$$

### Prover 总复杂度

将上面的所有复杂度进行汇总，为

$$
\begin{aligned}
    & (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) \\
    & + (3 \cdot 2^{n} - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (2^{n} + n + 8) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    &  + \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) \\
    & + (2^n + 4) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (6 \cdot 2^{n} + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polymul}(0, 2^n - 4) +  \mathsf{polydiv}(2^n - 1, 3) \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
\end{aligned}
$$

用 polynomial long division 方法，有

$$
\mathsf{polydiv}(N, k) = (N - k + 1) ~ \mathbb{F}_{\mathsf{inv}} + (kN - k^2 + k) ~ \mathbb{F}_{\mathsf{mul}} 
$$

可以得到

$$
\begin{align}
\mathsf{polydiv}(2^n - 1, 3)  & = (N - 1 - 3 + 1) ~ \mathbb{F}_{\mathsf{inv}} + (3(N - 1) - 3^2 + 3) ~ \mathbb{F}_{\mathsf{mul}}  \\
 & = (N - 3) ~ \mathbb{F}_{\mathsf{inv}} + (3N - 9) ~ \mathbb{F}_{\mathsf{mul}} 
\end{align}
$$

> [!important] 
> - [ ] 这里除法应该有更好的实现方法。


因此复杂度为

$$
\begin{align}
& (6 \cdot 2^{n} + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polymul}(0, 2^n - 4) +  \mathsf{polydiv}(2^n - 1, 3) \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
= & (6 N + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  4 ~ \mathbb{F}_{\mathsf{mul}} + 6 ~ \mathbb{F}_{\mathsf{mul}} + (N - 3) ~ \mathbb{F}_{\mathsf{mul}}+  (N - 3) ~ \mathbb{F}_{\mathsf{inv}} + (3N - 9) ~ \mathbb{F}_{\mathsf{mul}}  \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
=  & (10 N + n + 5) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{inv}} \\
& + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(N - 3, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1) 
\end{align}
$$




### 证明表示

可以看出，证明包括 $n+1$ 个 $\mathbb{G}_1$ 元素，包括 $2n+1$ 个 $\mathbb{F}_p$ 元素。

$$
\pi=\Big(H_1, H_2, \ldots, H_{n-1}, C_q, C_w, \{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}, h_0(\beta^2) \Big)
$$


证明大小：

$$
(n + 1)~\mathbb{G}_1 + (2n + 1) ~ \mathbb{F}_p
$$

### Verification


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


Verifier:

1. 计算 $h_1(\beta^2), \ldots, h_{n - 1}(\beta^2)$

- 计算 $\beta^2$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
- 对于每一个 $h_{i + 1}(\beta^2)$ ，计算 $2, 2\beta$ 的逆元，再分别与分子相乘，复杂度为 $2 ~ \mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$ ，后面一项计算好后和 $u_i$ 相乘，因此计算一项的复杂度为 $2 ~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathbb{F}_{\mathsf{mul}}$ ，总共有 $n - 1$ 项

- [ ] 是不是计算少写一项？

因此这一步的总复杂度为

$$
\mathbb{F}_{\mathsf{mul}} + (2n - 2) ~ \mathbb{F}_{\mathsf{inv}} + (3n - 3) ~ \mathbb{F}_{\mathsf{mul}} = (3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (2n - 2) ~ \mathbb{F}_{\mathsf{inv}}
$$

2. 计算 $C_h$

- 先计算 $\gamma^2, \ldots, \gamma^{n - 1}$ ，复杂度为 $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$
- 计算 $\gamma \cdot H_1, \ldots, \gamma^{n - 1} \cdot H_{n - 1}$ ，复杂度为 $(n - 1) ~ \mathsf{EccMul}^{\mathbb{G}_1}$
- 将 $n$ 个椭圆曲线上的点相加得到 $C_h$ ，复杂度为 $(n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}$

这一步计算总复杂度为

$$
(n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
$$

3. 计算 $C_r$

- 计算 $h^*(\zeta)$ ，通过 bary-centric 插值方式，verifier 自己计算得到
    
    这里分析的思路与 ph23 协议中的分析一致，这里 $h^*(X)$ 是由 3 个点值对插值得到的，

    $$
        h^*(X) = \frac{h(\beta) \cdot \frac{\hat{\omega_0}}{X- \beta} + h(-\beta) \cdot \frac{\hat{\omega_1}}{X+ \beta} + h(\beta^2) \cdot \frac{\hat{\omega_2}}{X- \beta^2}}{\frac{\hat{\omega_0}}{X- \beta} + \frac{\hat{\omega_1}}{X+ \beta} + \frac{\hat{\omega_2}}{X- \beta^2}}
    $$

    其中

    $$
    \begin{aligned}
        & \hat{\omega_0} = (\beta + \beta)(\beta - \beta^2) \\
        & \hat{\omega_1} = (-\beta - \beta)(-\beta - \beta^2) \\
        & \hat{\omega_2} = (\beta^2 - \beta)(\beta^2 - (-\beta))
    \end{aligned}
    $$

    这里由于 $\beta$ 是随机产生的，因此没有办法预计算，复杂度为 $3 ~ \mathbb{F}_{\mathsf{mul}}$ 。

    将 $\zeta$ 代入 $h^*(X)$ 的表达式来计算 $h^*(\zeta)$ ，即

    $$
        h^*(\zeta) = \frac{h(\beta) \cdot \frac{\hat{\omega_0}}{\zeta- \beta} + h(-\beta) \cdot \frac{\hat{\omega_1}}{\zeta+ \beta} + h(\beta^2) \cdot \frac{\hat{\omega_2}}{\zeta- \beta^2}}{\frac{\hat{\omega_0}}{\zeta- \beta} + \frac{\hat{\omega_1}}{\zeta+ \beta} + \frac{\hat{\omega_2}}{\zeta- \beta^2}}
    $$

    这里不详细列出方法，复杂度分析与 ph23 中的分析一致，对于一个长度为 $n$ 的点值对，这一步计算的复杂度为 $(2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}}$ ，因此这里计算的复杂度为 $7 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}$ 。

    因此计算 $h^*(\zeta)$ 的总复杂为

    $$
        10 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}
    $$

- 计算 $[h^*(\zeta)]_1$ ，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$

- 计算 $(\zeta^2 - \beta^2)(\zeta - \beta^2) \cdot C_q$ ，计算 $\zeta^2$ 复杂度为 $\mathbb{F}_{\mathsf{mul}}$ ，计算 $(\zeta^2 - \beta^2)(\zeta - \beta^2)$ 复杂度为 $\mathbb{F}_{\mathsf{mul}}$ ，计算 $(\zeta^2 - \beta^2)(\zeta - \beta^2) \cdot C_q$ 复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$ ，总复杂度为 

$$
2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}
$$

- 计算 $C_r$ ，三个椭圆曲线 $\mathbb{G}_1$ 上的点进行相加减，复杂度为 $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$

这一步的总复杂度为

$$
\begin{aligned}
    & 10 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}\\
    &  + \mathsf{EccMul}^{\mathbb{G}_1} \\
    & + 2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    = & 12 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}  + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}
\end{aligned}
$$

4. 通过 Pairing 的形式进行验证

$$
e(C_r + \zeta \cdot C_w, [1]_2) \overset{?}{=} e(C_w, [\tau]_2)
$$

- 计算 $C_r + \zeta \cdot C_w$ 复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
- 再计算两个 pairing ，复杂度为 $2 ~ P$

这一步的总复杂度为

$$
\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
$$

### Verifier 复杂度

汇总 Verifier 所有的计算复杂度，为

$$
\begin{aligned}
    & (3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (2n - 2) ~ \mathbb{F}_{\mathsf{inv}} \\
    & + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + 12 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}  + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P \\
    = & (4n + 8) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
\end{aligned}
$$

### 总结

**Prover's cost:**

$$
\begin{aligned}
    & (6 \cdot 2^{n} + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polymul}(0, 2^n - 4) +  \mathsf{polydiv}(2^n - 1, 3) \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
\end{aligned}
$$

化简有

$$
(10 N + n + 5) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{inv}} 
+ \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(N - 3, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1) 
$$



**Verifier's cost:**

$$
\begin{aligned}
    & (4n + 8) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
\end{aligned}
$$


**Proof size:**

$$
(2n + 1)  \mathbb{F}_p + (n + 1) \cdot \mathbb{G}_1
$$

## 优化版本 2

- 协议描述文档：[Gemini-PCS-4](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-4.md)

优化技巧：

本文介绍一个不同的优化协议，它采用了 FRI 协议的 Query-phase 中选取点的思路，对 $h_0(X)$ 挑战 $X=\beta$ 求值，进而对折叠后的多项式 $h_1(X)$ 挑战 $X=\beta^2$，依次类推，直到 $h_{n-1}(\beta^{2^{n-1}})$ 。这样做的好处是，每一次 $h_i(X)$ 的打开点可以在验证 $h_{i+1}(X)$ 的折叠时复用，从而总共可以节省 $n$ 个打开点。

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

### Round 1

1. Prover 记 $h_0(X) = f(X)$，然后计算折叠多项式 $h_1(X), h_2(X), \ldots, h_{n-1}(X)$，使得：

$$
h_{i+1}(X^2) = \frac{h_i(X) + h_i(-X)}{2} + u_i\cdot \frac{h_i(X) - h_i(-X)}{2X}
$$

2. Prover 计算承诺 $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$，使得：

$$
C_{h_{i+1}} = \mathsf{KZG10.Commit}(h_{i+1}(X))
$$

3. Prover 发送 $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$

这一轮的计算方式和优化版本 1 一样，因此计算复杂度相同，为

$$
(2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1)
$$

### Round 2

1. Verifier 发送随机点 $\beta\in\mathbb{F}_p$

2. Prover 计算 $h_0(\beta)$

3. Prover 计算 $h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})$

4. Prover 发送 $\big(h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\big)$

Prover:

- 计算 $\beta^2, \ldots, \beta^{2^{n - 1}}$ ，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $h_0(\beta), h_0(- \beta), \ldots, h_{n - 1}(-\beta^{2^{n - 1}})$ ，复杂度为 

$$
2^{n}  ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} 2^{n - i}  ~ \mathbb{F}_{\mathsf{mul}} = (3 \cdot 2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}
$$

因此这一轮的总复杂度为

$$
(n - 1)  ~ \mathbb{F}_{\mathsf{mul}} + (3 \cdot 2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}  = (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

### Round 3

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

Prover:

- 先计算出 $\gamma^2, \ldots, \gamma^{n}$ ，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $\gamma^{i + 1} \cdot (h_i(X) - h_i(- \beta^{2^i}))$ ，复杂度为 $\mathsf{polymul}(0, 2^{n - i})$ ，得到多项式再与 $(X - (\beta^{2^i}))$ 相除，这里可以用线性除法，复杂度为 $2^{n - i} ~ \mathbb{F}_{\mathsf{mul}}$ ，加上 $q(X)$ 中的第一项，整个计算出 $q(X)$ 的复杂度为

$$
2^{n} ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} (\mathsf{polymul}(0, 2^{n - i}) + 2^{n - i} ~ \mathbb{F}_{\mathsf{mul}}) = (3 \cdot 2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1})
$$

- 最后计算 $C_q$ ，复杂度为 $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$ .

因此这一轮的总复杂度为

$$
\begin{aligned}
    & (n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (3 \cdot 2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1})  + \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
    & = (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

### Round 4


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

**复杂度分析：**

1. 计算 $L_{\zeta}(X)$

- 计算 $\gamma^2, \ldots, \gamma^{n}$ ，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $v_D(\zeta)$ ，
  
    $$
    v_D(\zeta) = (\zeta - \beta)(\zeta - (-\beta)) \cdots (\zeta - (-\beta^{2^{n - 1}}))
    $$

    $D$ 中总共有 $n + 1$ 个元素，因此这里是 $n + 1$ 个元素相乘，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $L_{\zeta}(X)$ 的复杂度为

$$
\begin{aligned}
    & \mathsf{polymul}(0, 2^n - 2) + \mathbb{F}_{\mathsf{inv}} +  \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n) \\
    & + \sum_{i = 0}^{n - 1} (\mathbb{F}_{\mathsf{inv}} +  2 ~ \mathbb{F}_{\mathsf{mul}}  + \mathsf{polymul}(0, 2^{n  - i})) \\
    & = (2n + 1) ~ \mathbb{F}_{\mathsf{mul}}  + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(0, 2^n)
\end{aligned} 
$$     

2. 计算 $w(X)$ ，这里依然可以用线性除法方式，分子的次数是多少，那么复杂度就涉及多少次的乘法操作，由于 $\deg(w) = 2^n$ ，因此这一步的复杂度为 $2^n ~ \mathbb{F}_{\mathsf{mul}}$。

3. 计算 $C_w$ ，复杂度为 $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$ 。

因此这一轮的复杂度为

$$
\begin{aligned}
    & (2n + 1) ~ \mathbb{F}_{\mathsf{mul}}  + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, 2^n) + 2^n ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (2^n + 2n + 1) ~ \mathbb{F}_{\mathsf{mul}}  + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, 2^n) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$


### 证明表示

可以看出，单次证明包括 $n+1$ 个 $\mathbb{G}_1$ 元素，包括 $n+1$ 个 $\mathbb{F}_q$ 元素。

$$
\pi=\Big(C_{f_1}, C_{f_2}, \ldots, C_{f_{n-1}}, C_{q}, C_w, h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\Big)
$$


证明大小为

$$
(n + 1) \cdot \mathbb{G}_1 + (n + 1) \cdot \mathbb{F}_p
$$

### Verification


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


Verifier:

1. 计算 $h_1(\beta^2), \ldots, h_{n}(\beta^{\beta^{2^n}})$

- 计算 $\beta^2, \beta^{2^2}, \ldots, \beta^{2^n}$ ，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$
- 对于每一个 $h_{i + 1}(\beta^{2^{i+1}})$ ，计算 $2, 2\beta^{2^i}$ 的逆元，再分别与分子相乘，复杂度为 $2 ~ \mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$ ，后面一项计算好后和 $u_i$ 相乘，因此计算一项的复杂度为 $2 ~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathbb{F}_{\mathsf{mul}}$ ，总共有 $n$ 项

因此这一步的总复杂度为

$$
n ~ \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{inv}} + 3n ~ \mathbb{F}_{\mathsf{mul}} = 4n ~ \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{inv}}
$$

2. 计算 $C_L$

- 先计算 $v_D(\zeta)$ ，
  
    $$
    v_D(\zeta) = (\zeta - \beta)(\zeta - (-\beta)) \cdots (\zeta - (-\beta^{2^{n - 1}}))
    $$

    $D$ 中总共有 $n + 1$ 个元素，因此这里是 $n + 1$ 个元素相乘，复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
    
- 计算 $e_0$ ，分母求逆后和分子相乘，复杂度为 $\mathbb{F}_{\mathsf{inv}} + \mathbb{F}_{\mathsf{mul}}$ 。
- 计算出 $\gamma^2, \ldots, \gamma^n$ ，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $e_{i + 1}$ ，分母求逆后和分子相乘，再和 $\gamma^{i + 1}$ 相乘，复杂度为 $\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$ ，$i = 0, 1, \ldots, n - 1$ ，总共有 $n$ 项，因此这里总复杂度为 $n ~ \mathbb{F}_{\mathsf{inv}} + 2n ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 

$$
\sum_{i = 0}^{n - 1} e_{i + 1} \cdot (C_{h_i} - h_i(- \beta^{2^{i}}) \cdot [1]_1)
$$

计算 $e_{i + 1} \cdot (C_{h_i} - h_i(- \beta^{2^{i}}) \cdot [1]_1)$ 复杂度为 $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$ ，总复杂度为 $2n ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}$ ，即 $2n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}$ 。

- 计算 $e_0 \cdot (C_{h_0} - h_0(\beta) \cdot [1]_1)$ ，复杂度为 $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$ 。
- 计算 $C_L$ ，先计算出 $v_D(\zeta) \cdot C_q$ ，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$ ，接着三个椭圆曲线上的点相加，因此这里的总复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1} + 2~ \mathsf{EccAdd}^{\mathbb{G}_1}$ 。

因此这一步的总复杂度为

$$
\begin{aligned}
    & n ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathbb{F}_{\mathsf{inv}} + 2n ~ \mathbb{F}_{\mathsf{mul}} \\
    & + 2n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_1} + 2~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    = & 4n ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (2n + 3) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} 
\end{aligned}
$$

3. 最后一步进行检查，用 Pairing 形式

$$
e(C_L + \zeta \cdot C_w, [1]_2) \overset{?}{=} e(C_w, [\tau]_2)
$$

- 计算 $C_L + \zeta \cdot C_w$ 复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
- 再计算两个 pairing ，复杂度为 $2 ~ P$

这一步的总复杂度为

$$
\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
$$

### Verifier 复杂度

汇总 Verifier 所有的计算复杂度，为
  
$$
\begin{aligned}
    & 4n ~ \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{inv}} \\
    & + 4n ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (2n + 3) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P \\
    & = 8n ~ \mathbb{F}_{\mathsf{mul}} + (3n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (2n + 4) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 3) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
\end{aligned}
$$

### 总结

**Prover's cost:**

$$
\begin{aligned}
    & (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) \\
    & + (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    & + (2^n + 2n + 1) ~ \mathbb{F}_{\mathsf{mul}}  + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, 2^n) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (8 \cdot 2^{n} + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, 2^n) + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
\end{aligned}
$$

即

$$
\begin{aligned}
    & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, N) + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)\\
\end{aligned}
$$

代入 $\mathsf{polymul}(0, N) = (N + 1)  ~ \mathbb{F}_{\mathsf{mul}}$ 有

$$
\begin{aligned}
    & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, N) + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)\\
	= & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} (2^{i + 1} + 1) ~ \mathbb{F}_{\mathsf{mul}} + (2^n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1) \\
	= & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} (2^{i + 1} + 1) ~ \mathbb{F}_{\mathsf{mul}} + (2^n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1) \\
	= & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (4N + 2n - 4) ~ \mathbb{F}_{\mathsf{mul}} + (N - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1) \\
	= & (14 N + 6n - 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)   \\
\end{aligned}
$$


**Verifier's cost:**

$$
8n ~ \mathbb{F}_{\mathsf{mul}} + (3n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (2n + 4) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 3) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
$$

**Proof size:**

$$
(n + 1) \cdot \mathbb{F}_p + (n + 1) \cdot \mathbb{G}_1
$$