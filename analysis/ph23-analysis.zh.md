# PH23 协议性能分析

协议来源：[PH23+KZG10 协议（优化版）](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-02.zh.md#2-ph23kzg10-%E5%8D%8F%E8%AE%AE%E4%BC%98%E5%8C%96%E7%89%88)

## PH23+KZG10 协议（优化版）

对于 KZG10 协议，因为其 Commitment 具有加法同态性。

### Precomputation 

1. 预计算 $s_0(X),\ldots, s_{n-1}(X)$ 以及 $v_H(X)$	

$$
v_H(X) = X^N -1 
$$

$$
s_i(X) = \frac{v_H(X)}{v_{H_i}(X)} = \frac{X^N-1}{X^{2^i}-1}
$$

2. 预计算 $D=(1, \omega, \omega^2, \ldots, \omega^{2^{n-1}})$ 上的 Bary-Centric Weights $\{\hat{w}_i\}$。这个可以加速

$$
\hat{w}_j = \prod_{l\neq j} \frac{1}{\omega^{2^j} - \omega^{2^l}}
$$

3. 预计算 Lagrange Basis 的 KZG10 SRS $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$ 

### Common inputs

1. $C_a=[\hat{f}(\tau)]_1$:  the (uni-variate) commitment of $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ 
2. $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$: 求值点
3. $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$: MLE 多项式 $\tilde{f}$ 在 $\vec{X}=\vec{u}$ 处的运算值

### Commit 计算过程

1. Prover 构造一元多项式 $a(X)$，使其 Evaluation form 等于 $\vec{a}=(a_0, a_1, \ldots, a_{N-1})$，其中 $a_i = \tilde{f}(\mathsf{bits}(i))$, 为 $\tilde{f}$ 在 Boolean Hypercube $\{0,1\}^n$ 上的取值。

$$
a(X) = a_0\cdot L_0(X) + a_1\cdot L_1(X) + a_2\cdot L_2(X) + \cdots + a_{N-1}\cdot L_{N-1}(X)
$$

> Prover: 这一步 Prover 不需要求出系数式，直接用 evaluation form 进行计算，不涉及计算复杂度。

2. Prover 计算 $\hat{f}(X)$ 的承诺 $C_a$，并发送 $C_a$

$$
C_{a} = a_0\cdot A_0 + a_1\cdot A_1 + a_2\cdot A_2 + \cdots + a_{N-1}\cdot A_{N-1} = [\hat{f}(\tau)]_1
$$

其中 $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$ ，在预计算过程中已经得到。

> Prover: 算法复杂度为 $\mathsf{msm}(N, \mathbb{G}_1)$ ，表示 $N$ 长的向量的承诺。

> #### Commit 阶段复杂度
>
> 在 commit 阶段 prover 的复杂度总计为：
>
> $$
> \mathsf{msm}(N, \mathbb{G}_1)
> $$

### Evaluation 证明协议

回忆下证明的多项式运算的约束：

$$
\tilde{f}(u_0, u_1, u_2, \ldots, u_{n-1}) = v
$$

这里 $\vec{u}=(u_0, u_1, u_2, \ldots, u_{n-1})$ 是一个公开的挑战点。

###### Prover Memory

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([z_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\}$

#### Round 1.

Prover:

##### Round 1-1

1. 计算向量 $\vec{c}$，其中每个元素 $c_i=\overset{\sim}{eq}(\mathsf{bits}(i), \vec{u})$

###### Prover Cost 1-1

> Prover: 
> 
> 向量 $\vec{c}$ 的计算算法为
> 
> ```python
> @classmethod
> def eqs_over_hypercube(cls, rs):
>     k = len(rs)
>     n = 1 << k
>     evals = [Field(1)] * n
>     half = 1
>     for i in range(k):
>         for j in range(half):
>             evals[j+half] = evals[j] * rs[i]
>             evals[j] = evals[j] - evals[j+half]
>         half *= 2
>     return evals
> ```
> 例如 $k = 2$ ，计算结果应该为
> 
> $$
> \begin{aligned}
>   00 & \quad (1 - u_0) & (1- u_1)  \\
>   10 & \quad u_0 & (1- u_1) \\
>   01 & \quad (1 - u_0) & u_1 \\
>   11 & \quad u_0 & u_1
> \end{aligned}
> $$
> 
> 这个算法就是先按 $u_0$ 所在的二进制位进行计算，接着如果增加一位 $u_1$ ，再更新所有的元素。
> 
> - `for j in range(1)` 循环内部计算出 `evals[1]` 和 `evals[0]`:
>   - `evals[1]` = $u_0$ ，对应 $u_0$ 所在的位 `1`
>   - `evals[0]` = $1 - u_0$ ，对应 $u_0$ 所在的二进制位 `0`
> - `for j in range(2)` ，更新 $u_1$ 所在的位。
>   - `j = 0`，更新 `evals[0]` 和 `evals[2]`
>   - `j = 1`，更新 `evals[1]` 和 `evals[3]`
> 
> 每次循环 `for j in range(half)` 内部有 1 次有限域上的乘法，即 `evals[j+half] = evals[j] * rs[i]` ，而 `half` 的变化为 $1, 2, 2^2, \ldots, 2^{k-1}$ ，因此总共的有限域乘法个数为：
> 
> $$
>   1 + 2 + 2^2 + \ldots + 2^{k - 1} = \frac{1(1 - 2^k)}{1 - 2} = 2^k - 1 = N - 1
> $$
> 
> 因此这里的计算复杂度为 $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。

###### Prover Memory 1-1

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\}$

##### Round 1-2

构造多项式 $c(X)$，其在 $H$ 上的运算结果恰好是 $\vec{c}$ 。

$$
c(X) = \sum_{i=0}^{N-1} c_i \cdot L_i(X)
$$


######  Prover Cost 1-2

Prover: 这一步不需要计算 $c(X)$ ，直接拿到 $\vec{c}$ 进行后续的计算。


##### Round 1-3

计算 $c(X)$ 的承诺 $C_c= [c(\tau)]_1$，并发送 $C_c$

$$
C_c = \mathsf{KZG10.Commit}(\vec{c})  =  [c(\tau)]_1 
$$


###### Prover Cost 1-3

$C_c$ 的承诺计算方法为

$$
C_c = c_0 \cdot A_0 + c_1 \cdot A_1 + \ldots + c_{N - 1} \cdot A_{N - 1}
$$

这里算法复杂度为  $\mathsf{msm}(N, \mathbb{G}_1)$

##### Prover Cost Round 1

> 
> Prover 复杂度为：
>
> $$
> (N - 1) ~ \mathbb{F}_{\mathsf{mul}}  + \mathsf{msm}(N, \mathbb{G}_1)
> $$

##### Prover Memory Round 1

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\}$

#### Round 2.

Verifier: 发送挑战数 $\alpha\leftarrow_{\$}\mathbb{F}_p$ 

Prover: 

##### Round 2-1

构造关于 $\vec{c}$ 的约束多项式 $p_0(X),\ldots, p_{n}(X)$

$$
\begin{split}
p_0(X) &= s_0(X) \cdot \Big( c(X) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
p_k(X) &= s_{k-1}(X) \cdot \Big( u_{n-k}\cdot c(X) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot X)\Big) , \quad k=1\ldots n
\end{split}
$$


###### Prover Cost 2-1

> 📝 **笔记**：先介绍一般如何快速的做有限域上的多项式乘法和除法，不妨设
> $$
> H' = \{g^0, g^1, \ldots, g^{2N - 1}\} = \langle g \rangle
> $$
>
> 取 
>   
> $$
>H = \langle g^2  \rangle = \langle \omega  \rangle = \{\omega^0, \omega^1, \ldots, \omega^{N - 1} \}
> $$
>
> 则
>   
> $$
>gH = \{g\omega^0, g\omega^1, \ldots, g\omega^{N - 1} \} =\{ g^1, g^3, \ldots, g^{2N - 1} \}
> $$
>
> 若要计算 
>    
> $$
>a(X) = a_1 + a_2 X + \ldots + a_{N - 1}X^{N - 1}
> $$
>
> 与
>   
> $$
>b(X) = b_1 + b_2 X + \ldots + b_{N - 1}X^{N - 1}
> $$
> 
> 的乘积多项式 $c(X) = a(X)\cdot b(X)$ 。若我们拥有的是 $a(X)$ 与 $b(X)$ 在 $H$ 上的 evaluation form，即
>   $$
> [a(x)|_{x \in H}], \quad [b(x)|_{x \in H}]
>$$
> 
> 我们想要计算的是商多项式
> 
> $$
>q(X) = \frac{a(X) \cdot b(X)}{z_H(X)}
> $$
>
> 由于 $\deg(q) < N$ ，因此存储 $q(X)$ 依然可以用 evaluation form ，由于 $z_H(X)$ 在 $H$ 上都为 $0$ ，因此我们可以分别求出
>   
> $$
>[(a(x) \cdot b(x))|_{x \in gH}], \quad [z_H(x)|_{x \in gH}]
> $$
>
> 再对位相除计算出 $[q(x)|_{x \in gH}]$ 。
> - 计算得到 $[a(x))|_{x \in gH}]$ : 先对 $[a(x)|_{x \in H}]$ 做一次 IFFT 得到 $a(X)$ 的系数，再做一次 FFT 计算得到其在 $gH$ 上的值。这里实际实现时可以同步进行计算，不过复杂度应该没有变化，为 $N \log N ~ \mathbb{F}_{\mathsf{mul}}$ ，也记为 $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$ 。
>- 计算得到 $[b(x))|_{x \in gH}]$ : 先对 $[b(x)|_{x \in H}]$ 做一次 IFFT 得到 $b(X)$ 的系数，再做一次 FFT 计算得到其在 $gH$ 上的值。这一步复杂度为 $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$ ，即 $N \log N ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 先计算 $[(a(x) \cdot b(x))|_{x \in gH}]$ : $N$ 个元素相乘，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 计算 $[z_H(x)|_{x \in gH}]$ : 由于 $z_H(X) = X^N - 1$ ，因此
> $$
>   z_H(x) = z_H(g\omega^i) = (g\omega^i)^N - 1 = g^N \cdot (\omega^N)^i - 1 = g^N - 1
> $$
> $z_H(X)$ 在 $gH$ 上的值始终是一个常数，那么其逆 $(g^N - 1)^{-1}$ 也可以提前计算好。这一步不涉及 Prover 的复杂度。
> - 计算 $[q(x)|_{x \in gH}]$ ：用 $[(a(x) \cdot b(x))|_{x \in gH}]$ 的值分别乘以 $(g^N - 1)^{-1}$ 就能得到 $[q(x)|_{x \in gH}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。
> 
> 因此整体计算除法的复杂度为
> 
> $$
> 2~ \mathsf{FFT}(N) + 2~\mathsf{IFFT}(N) + 2N ~ \mathbb{F}_{\mathsf{mul}}
> $$


现在分析算法复杂度。Prover 要计算出 $[p_i(x)|_{x \in gH}]$ ，便于后续计算商多项式的 evaluation form。

1. prover 计算 $[s_0(x)|_{x \in gH}], [s_1(x)|_{x \in gH}], \ldots, [s_{n - 1}(x)|_{x \in gH}]$ 。可以以一个 $O(n)$ 的算法得到任意一个点 $s_0(x), \ldots, s_{n - 1}(x)$ 的值，具体计算方法如 Round 3 所示，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。由于 $|gH| = N$ ，因此求出所有在 $gH$ 上的值的复杂度为 $(n - 1)N ~ \mathbb{F}_{\mathsf{mul}}$ 。
2. 计算得到 $[c(x)|_{x \in gH}]$ ，对 $[c(x)|_{x \in H}]$ 先用 IFFT 得到其系数，再用 FFT 求其在 $gH$ 上的值，复杂度为 $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$ 。
3. 计算 $[(c(x) - (1 - u_0)(1 - u_1) \ldots (1 - u_{n - 1}))|_{x \in gH}]$ ： $(1 - u_0)(1 - u_1) \ldots (1 - u_{n - 1})$ 其实就是 $c_0$ ，这里直接相减进行计算就行。
4. 计算 $[p_0(x)|_{x \in gH}]$ ，涉及 $N$ 个数相乘，复杂度为 $N ~  \mathbb{F}_{\mathsf{mul}}$ 。
5. 对于 $k = 1, \ldots, n$ ，计算 $[( u_{n-k}\cdot c(x) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot x))|_{x \in gH}]$ ：对每一个 $k$ 与 $x \in gH$ ，每次涉及 $2$ 次有限域的乘法，因此计算所有 $k$ 对应的值的复杂度为 $2nN ~  \mathbb{F}_{\mathsf{mul}}$ 。
6. 对于 $k = 1, \ldots, n$ ，计算 $[p_k(x)|_{x \in gH}]$ ，对每一个 $k$ ，涉及 $N$ 个数相乘，因此总复杂度为 $nN ~  \mathbb{F}_{\mathsf{mul}}$

总结下这一步的总复杂度为

$$
\begin{aligned}
  & (n - 1)N ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N) + \mathsf{IFFT}(N) + N ~  \mathbb{F}_{\mathsf{mul}} + 3nN ~  \mathbb{F}_{\mathsf{mul}} \\
  = & \mathsf{FFT}(N) + \mathsf{IFFT}(N) + 4nN ~ \mathbb{F}_{\mathsf{mul}}
\end{aligned}
$$

###### Prover Memory 2-1

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $c(X)$ 的系数
- $[c(x)|_{x \in gH}]$
- $\{[p_k(x)|_{x \in gH}]\}_{k = 0}^n$


##### Round 2-2

把 $\{p_i(X)\}$ 聚合为一个多项式 $p(X)$ 

$$
p(X) = p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)
$$


###### Prover Cost 2-2

这一步其实算的并不是多项式的系数，而是中间计算出 $[p(x)|_{x \in gH}]$ 。

1. prover 由 $\alpha$ 计算得到 $\alpha^2, \alpha^3, \ldots, \alpha^n$ ，总共有 $n - 1$ 次有限域上的乘法，因此复杂度是 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
2. 对每一个 $x \in gH$ ，直接计算

$$
p(x) = p_0(x) + \alpha\cdot p_1(x) + \alpha^2\cdot p_2(x) + \cdots + \alpha^{n}\cdot p_{n}(x)
$$

涉及有限域乘法为 $n$ 个，总共有 $|gH| = N$ 个 $x$ ，因此复杂度为 $nN ~ \mathbb{F}_{\mathsf{mul}}$ 。

总结下这一步的复杂度为

$$
(nN + n - 1) ~ \mathbb{F}_{\mathsf{mul}}
$$

###### Prover Memory 2-2

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$


##### Round 2-3

构造累加多项式 $z(X)$，满足

$$
\begin{split}
z(1) &= a_0\cdot c_0 \\
z(\omega_{i}) - z(\omega_{i-1}) &=  a(\omega_{i})\cdot c(\omega_{i}), \quad i=1,\ldots, N-1 \\ 
z(\omega^{N-1}) &= v \\
\end{split}
$$


###### Prover Cost 2-3

前面已经得到了 $[a(x)|_{x \in H}]$ 以及 $[c(x)|_{x \in H}]$ ，得到 $[z(x)|_{x \in H}]$ 就比较好计算了。

$$
\begin{aligned}
  & z(1) = a_0 \cdot c_0 \\
  & z(\omega_1) = z(1) + a(\omega_1) \cdot c(\omega_1) \\
  & \cdots \\
  & z(\omega_{N - 1}) = z(\omega_{N - 2}) + a(\omega_{N - 1}) \cdot c(\omega_{N - 1}) \\
  & z(\omega^{N - 1}) = v
\end{aligned}
$$

涉及的复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$

###### Prover Memory 2-3

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([z_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$

##### Round 2-4

构造约束多项式 $h_0(X), h_1(X), h_2(X)$，满足

$$
\begin{split}
h_0(X) &= L_0(X)\cdot\big(z(X) - c_0\cdot a(X) \big) \\
h_1(X) &= (X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) & = L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{split}
$$


###### Prover Cost 2-4

要计算出 $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$ 。
- 先计算出 $[z(x)|_{x \in gH}]$ ，复杂度为 $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$ 。
- 计算出 $[a(x)|_{x \in gH}]$ ，复杂度为 $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$ 。
- 计算出 $[h_0(x)|_{x \in gH}]$ ，复杂度为 $2N ~ \mathbb{F}_{\mathsf{mul}}$
- 计算出 $[(a(x) \cdot c(x))|_{x \in gH}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算出 $[h_1(x)|_{x \in gH}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$
- 计算出 $[h_2(x)|_{x \in gH}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$
这一步的总复杂度为

$$
2~ \mathsf{FFT}(N) + 2~ \mathsf{IFFT}(N) + 5N ~ \mathbb{F}_{\mathsf{mul}}
$$

###### Prover Memory 2-4

这一轮增加 $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$ 。

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([z_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $z(X)$ 的系数 (Round 2-4)
- $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$

##### Round 2-5

把 $p(X)$ 和 $h_0(X), h_1(X), h_2(X)$ 聚合为一个多项式 $h(X)$，满足

$$
\begin{split}
h(X) &= p(X) + \alpha^{n+1} \cdot h_0(X) + \alpha^{n+2} \cdot h_1(X) + \alpha^{n+3} \cdot h_2(X)
\end{split}
$$

###### Prover Cost 2-5

这一轮计算 $[h(x)_{x \in gH}]$ 。
- 在这一轮中的前面第 2 步已经计算出 $\alpha^2, \ldots, \alpha^n$ ，现在要计算 $\alpha^{n + 1}, \alpha^{n + 2} , \alpha^{n + 3}$ ，这里涉及 $3$ 次有限域上的乘法，因此复杂度为 $3 ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $[h(x)|_{gH}]$ ，复杂度为 $3N ~ \mathbb{F}_{\mathsf{mul}}$
这一轮的总复杂度为
$$
(3N + 3) ~ \mathbb{F}_{\mathsf{mul}}
$$
###### Prover Memory 2-5

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([v_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$
- $[h(x)|_{x \in gH}]$

##### Round 2-6

计算 Quotient 多项式 $t(X)$，满足

$$
h(X) =t(X)\cdot v_H(X)
$$
###### Prover Cost 2-6

计算出 $[t(x)|_{x \in gH}]$ ，对于 $\forall x \in gH$

$$
t(x) = h(x) \cdot (v_H(x))^{-1} =  h(x) \cdot (g^N - 1)^{-1}
$$
复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。

###### Prover Memory 2-6

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([v_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $[t(x)|_{x \in gH}]$

##### Round 2-7

计算 $C_t=[t(\tau)]_1$， $C_z=[z(\tau)]_1$，并发送 $C_t$ 和 $C_z$

$$
\begin{split}
C_t &= \mathsf{KZG10.Commit}(t(X)) = [t(\tau)]_1 \\
C_z &= \mathsf{KZG10.Commit}(z(X)) = [z(\tau)]_1
\end{split}
$$
######  Prover Cost 2-7

计算 $C_t$ 

- 通过 $[t(x)|_{x \in gH}]$ 计算出 $[t(x)|_{x \in H}]$ ，复杂度为 $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$ ，
- 计算

$$
C_t = t_0 A_0 + \ldots + t_{N - 1}A_{N - 1}
$$
复杂度为 $\mathsf{msm}(N, \mathbb{G}_1)$

计算 $C_z$:  $\mathsf{msm}(N, \mathbb{G}_1)$

因此这一步的总复杂度为 
$$
\mathsf{FFT}(N) + \mathsf{IFFT}(N) + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)
$$

> 💡 **Option**
>
> 如果在不考虑内存的情况下，内存中可以提前存好另一组 KZG10 的 SRS，$B_0 =[L'_0(\tau)]_1, B_1= [L'_1(\tau)]_1, B_2=[L'_2(\tau)]_1, \ldots, B_{N-1} = [L'_{2^{n} - 1}(\tau)]_1$ ，其中 $L_0', \ldots, L_{N - 1}'$ 是在 $gH$ 上的 Lagrange 插值多项式。
>
> - 计算 $C_t$ ，
>   $$
>   C_t = t_0 B_0 + \ldots + t_{N - 1}B_{N - 1}
>   $$
>   其中 $[t_0, \ldots, t_{N-1}]$ 就是 $[t(x)|_{x \in gH}]$ 。那么这一步的复杂度为 $\mathsf{msm}(N, \mathbb{G}_1)$ 。
>
> - 计算 $C_z$: $\mathsf{msm}(N, \mathbb{G}_1)$
>
> 总复杂度为
> $$
> 2 ~ \mathsf{msm}(N, \mathbb{G}_1)
> $$
> 这种方案会少一次 FFT 和一次 IFFT，节省 $N \log N ~ \mathbb{F}_{\mathsf{mul}}$ 的计算。

#### Prover Cost Round 2

汇总上面所有步骤的 Prover 计算复杂度

$$
\begin{aligned}
& \mathsf{FFT}(N) + \mathsf{IFFT}(N) + 4nN ~ \mathbb{F}_{\mathsf{mul}} + (nN + n - 1) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathsf{FFT}(N) + 2~ \mathsf{IFFT}(N) + 5N ~ \mathbb{F}_{\mathsf{mul}} \\
& + (3N + 3) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N) + \mathsf{IFFT}(N) + 2 ~ \mathsf{msm}(N, \mathbb{G}_1) \\
= & 4 ~ \mathsf{FFT}(N) + 4 ~ \mathsf{IFFT}(N) + (5nN + 10N + n + 2) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)
\end{aligned}
$$

#### Round 3.

Verifier: 发送随机求值点 $\zeta\leftarrow_{\$}\mathbb{F}_p$ 

Prover: 

##### Round 3-1

1. 计算 $s_i(X)$ 在 $\zeta$ 处的取值：

$$
s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)
$$

###### Prover Cost  3-1

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

> - 可以先由随机数 $\zeta$ 计算出 $\zeta^2, \zeta^4, \ldots, \zeta^{2^{n - 1}}$ 次，这里由 $\zeta^2 = \zeta \times \zeta$ 需要一次有限域乘法，接着 $\zeta^4 = \zeta^2 \times \zeta^2$ ，需要一次有限域乘法，以此类推得到所有这些值，每次需要一次有限域乘法，总共会涉及 $n - 1$ 次有限域乘法，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - 计算得到 $s_{n-1}(\zeta) = \zeta^{2^{n-1}} + 1$ ，这里只涉及有限域的加法，不计入复杂度中。
> - 计算 $s_{i}(\zeta) (i = 0, \ldots, n - 2)$ ，$s_{i}(\zeta) = s_{i + 1}(\zeta) \cdot (\zeta^{2^i} +1)$ 这里需要一次有限域乘法，因此需要的有限域乘法操作为 $\mathbb{F}_{\mathsf{mul}}$ ，取遍 $i = 0, \ldots, n - 2$ ，总复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
> 
> 因此总共的复杂度为
> 
> $$
>   (n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathbb{F}_{\mathsf{mul}} = 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}}
> $$

##### Round 3-2
定义求值 Domain $D'$，包含 $n+1$ 个元素：

$$
D'=D\zeta = \{\zeta, \omega\zeta, \omega^2\zeta,\omega^4\zeta, \ldots, \omega^{2^{n-1}}\zeta\}
$$

##### Round 3-3
计算并发送 $c(X)$ 在 $D'$ 上的取值 

$$
c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})
$$
###### Prover Cost 3-3
- 这里 $(1, \omega, \omega^2, \ldots, \omega^{2^{n - 1}})$ 可以提前计算好，因此计算点 $(\zeta, \zeta \cdot \omega, \zeta \cdot \omega^2, \ldots, \zeta \cdot \omega^{2^{n - 1}})$ 会涉及 $n$ 个有限域乘法，复杂度为 $n ~\mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $[c(x)|_{x \in D'}]$ ，在 Round 2-1 中求得了 $c(X)$ 的系数，这里用 FFT 方法可以在一个大小为 $N$ 的子群 $D' \subset D^{(2)}$ 求出 $[c(x)|_{x \in D^{(2)}}]$ ，其中  $|D'| = n, |D^{(2)}| = N$ 。自然就能得到 $[c(x)|_{x \in D'}]$ ，复杂度为 $\mathsf{FFT}(N)$ 。

> 💡 这里由于多算了很多值，本来只需要在 $D'$ 上的值，现在算了在 $D^{(2)}$ 上的值，还有优化的空间。
> - [ ] 求在 D' 上的 sub tree 复杂度为 $n\log^2n$ 
> - [ ] 是否有优化算法

这一步的复杂度为

$$
n ~\mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N)
$$
##### Round 3-4

计算并发送 $z(\omega^{-1}\cdot\zeta)$

###### Prover Cost 3-4

在 Round 2-4 已经计算出 $z(X)$ 的系数式，这里可以直接拿着系数式求 $z(X)$ 在一点的值。

> Prover:
>
> 计算 $\omega^{-1}\cdot\zeta$ 复杂度为 $\mathbb{F}_{\mathsf{mul}}$ ，计算 $z(\omega^{-1}\cdot\zeta)$ 复杂度为 $N ~\mathbb{F}_{\mathsf{mul}}$ ，总复杂度为：
>
> $$
>   (N + 1) ~ \mathbb{F}_{\mathsf{mul}}
> $$

######  Prover Memory  3-4

- KZG10 SRS : $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([v_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $L_0(X)$ 与 $L_{N - 1}(X)$ 的系数
- $\omega^{-1}$ (Precompution)
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $[z(x)|_{x \in gH}]$
- $[t(x)|_{x \in gH}]$
- $c(X)$ 的系数
- $z(X)$ 的系数
- $c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})$
- $s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)$
- $z(\omega^{-1}\cdot\zeta)$
- $\alpha, \alpha^2, \ldots, \alpha^{n + 3}$ (Round 2-5)

##### Round 3-5

计算 Linearized Polynomial $l_\zeta(X)$

$$
\begin{split}
l_\zeta(X) =& \Big(s_0(\zeta) \cdot (c(\zeta) - c_0) \\
& + \alpha\cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))\\
  & + \alpha^2\cdot s_1(\zeta) \cdot (u_{n-2}\cdot c(\zeta) - (1-u_{n-2})\cdot c(\omega^{2^{n-2}}\cdot\zeta)) \\
  & + \cdots \\
  & + \alpha^{n-1}\cdot s_{n-2}(\zeta)\cdot (u_{1}\cdot c(\zeta) - (1-u_{1})\cdot c(\omega^2\cdot\zeta))\\
  & + \alpha^n\cdot s_{n-1}(\zeta)\cdot (u_{0}\cdot c(\zeta) - (1-u_{0})\cdot c(\omega\cdot\zeta)) \\
  & + \alpha^{n+1}\cdot (L_0(\zeta)\cdot\big(z(X) - c_0\cdot a(X))\\
  & + \alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(X)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(X) ) \\
  & + \alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(X) - v) \\
  & - v_H(\zeta)\cdot t(X)\ \Big)
\end{split}
$$

显然，$l_\zeta(\zeta)= 0$，因此这个运算值不需要发给 Verifier，并且 $[l_\zeta(\tau)]_1$ 可以由 Verifier 自行构造。

###### Prover Cost 3-5

计算得到 $[l_{\zeta}(x)|_{x \in H}]$ 。

- $L_0(\zeta)$ 与 $L_{N - 1}(\zeta)$ ：$L_0(X)$ 与 $L_{N - 1}(X)$ 的系数可以提前在预计算在得到，那么计算 $L_0(\zeta)$ 与 $L_{N - 1}(\zeta)$ 的复杂度为 $2N ~\mathbb{F}_{\mathsf{mul}}$ 。
- $s_0(\zeta) \cdot (c(\zeta) - c_0)$ ，涉及一次有限域乘法，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
- $\alpha \cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))$ ，复杂度为 $4 ~ \mathbb{F}_{\mathsf{mul}}$ ，从第 $2$ 到 $n + 1$ 项都是如此，因此复杂度为 $4n ~ \mathbb{F}_{\mathsf{mul}}$
- 对于 $x \in H$ ，计算 $[\alpha^{n+1}\cdot L_0(\zeta)\cdot\big(z(x) - c_0\cdot a(x))\big)]$ ，每一项涉及 $3$ 次有限域上的乘法，因此总复杂度为 $3N ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 对于 $x \in H$ ，计算 $[\alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(x)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(x)]$ ，计算 $\omega^{-1}\cdot\zeta$ 涉及一次有限域上的乘法，对每一个 $x$ 涉及 $3$ 次有限域乘法，因此总复杂度为 $(3N + 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 对于 $x \in H$ ，计算 $[\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(x) - v)]$ ，每次涉及 $2$ 次有限域的乘法，复杂度为 $2N ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $v_H(\zeta)$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 对于 $x \in H$ ，计算 $[v_H(\zeta)\cdot t(x)]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。

这一步的总复杂度为

$$
(12 N + 4n + 2) ~ \mathbb{F}_{\mathsf{mul}}
$$
##### Round 3-6

构造多项式 $c^*(X)$，它是下面向量在 $D\zeta$ 上的插值多项式

$$
\vec{c^*}= \Big(c(\omega\cdot\zeta), c(\omega^2\cdot\zeta), c(\omega^4\cdot\zeta), \ldots, c(\omega^{2^{n-1}}\cdot\zeta), c(\zeta)\Big)
$$

Prover 可以利用事先预计算的 $D$ 上的 Bary-Centric Weights $\{\hat{w}_i\}$ 来快速计算 $c^*(X)$，

$$
c^*(X) = \frac{c^*_0 \cdot \frac{\hat{w}_0}{X-\omega\zeta} + c^*_1 \cdot \frac{\hat{w}_1}{X-\omega^{2}\zeta} + \cdots + c^*_n \cdot \frac{\hat{w}_n}{X-\omega^{2^n}\zeta}}{
   \frac{\hat{w}_0}{X-\omega\zeta} + \frac{\hat{w}_1}{X-\omega^2\zeta} + \cdots + \frac{\hat{w}_n}{X-\omega^{2^n}\zeta}
  }
$$

这里 $\hat{w}_j$ 为预计算的值：

$$
\hat{w}_j = \prod_{l\neq j} \frac{1}{\omega^{2^j} - \omega^{2^l}}
$$

###### Prover Cost 3-6

> 📝 Notes
> - $c(X)$ 的系数在前面已经计算得到了
> - [ ] 这里 $c(X)$ 计算得到系数式，再求 $\vec{c^*}$
> - [ ] 这里得到的是 $c^*(X)$ 的系数式
> - [ ] product fast inter
> - [ ] 算 $c^*(X)$ 复杂度为 $(n + 1) \log^2(n + 1)$

> 📝 之前的分析过程：
>
   Prover:
> 
> - $\vec{c^*}$ 与 $\omega^{2^i}\zeta$ 的值在本轮的第 $3$ 步已经计算得到。
> - 计算 $\frac{\hat{w}_i}{X-\omega^{2^i}\zeta}$ ，分子是一个常数，分母是一个一次多项式，复杂度记为 $\mathsf{polydiv}(0, 1)$ ，得到的结果其实是一个分式。
> - 计算 $c_i^* \cdot \frac{\hat{w}_i}{X-\omega^{2^i}\zeta}$ ，这里将复杂度记为 $\mathsf{polymul}(0, -1)$ 。
> - 最后计算 $c^*(X)$ ，分子和分母分别通分后，分子分母均为一个次数为 $n$ 的多项式，因此它们相除的复杂度记为 $\mathsf{polydiv}(n, n)$ ，最后得到的结果 $c^*(X)$ 次数也为 $n$ 。
> 
> 多项式相加的复杂度只涉及有限域的加法，不做计入，因此这一步 $c^*(X)$ 的复杂度为 
>  
> $$
>  n ~ \mathsf{polymul}(0, -1) + n ~\mathsf{polydiv}(0, 1) + \mathsf{polydiv}(n, n) 
> $$


复杂度为

$$
(n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}}
$$


##### Round 3-7

因为 $l_\zeta(\zeta)= 0$，所以存在 Quotient 多项式 $q_\zeta(X)$ 满足

$$
q_\zeta(X) = \frac{1}{X-\zeta}\cdot l_\zeta(X)
$$

###### Prover Cost 3-7

> 这一步的计算采用的是下面的算法，代码为
> 
> ```python
> def division_by_linear_divisor(self, d):
>     """
>     Divide a polynomial by a linear divisor (X - d) using Ruffini's rule.
> 
>     Args:
>         coeffs (list): Coefficients of the polynomial, from lowest to highest degree.
>         d (Scalar): The constant term of the linear divisor.
> 
>     Returns:
>         tuple: (quotient coefficients, remainder)
>     """
>     assert len(self.coeffs) > 0, "Polynomial degree must be at least 1"
> 
>     n = len(self.coeffs)
>     quotient = [0] * (n - 1)
>     
>     # Start with the highest degree coefficient
>     current = self.coeffs[-1]
>     
>     # Iterate through coefficients from second-highest to lowest degree
>     for i in range(n - 2, -1, -1):
>         # Store the current value in the quotient
>         quotient[i] = current
>         
>         # Compute the next value
>         current = current * d + self.coeffs[i]
>     
>     # The final current value is the remainder
>     remainder = current
> 
>     return UniPolynomial(quotient), remainder
> ```
> 
> 对于一个 $n$ 次的多项式 
> 
> $$
> f(X) = f_0 + f_1 X + f_2 X^2 + \cdots + f_{n-1} X^{n-1} + f_n X^n
> $$
> 
> 除上一个一次多项式 $X - d$ ，想得到其商多项式和余项，即满足 $f(X) = q(X)(X - d) + r(X)$ ，那么可以这样来分解
> 
> $$
> \begin{aligned}
>   & f_0 + f_1 X + f_2 X^2 + \cdots + f_{n-1} X^{n-1} + f_n X^n  \\
>   = & (X -  d)(f_n \cdot X^{n - 1}) + d \cdot f_n \cdot X^{n - 1} + f_{n - 1} X^{n - 1} + \cdots + f_1 X + f_0 \\
>   = & (X -  d)(f_n \cdot X^{n - 1}) + (X - d)((df_n + f_{n - 1}) \cdot X^{n - 2}) \\
>   & + d \cdot (df_n + f_{n - 1}) + f_{n - 2} X^{n - 2} + \cdots + f_1 X + f_0 \\
> \end{aligned}
> $$
> 
> 通过上式子发现，
> 
> $$
> \begin{aligned}
>   & q_{n - 1} = f_n \\
>   & q_i = d \cdot q_{i + 1} + f_{i + 1} , \quad i = n - 2, \ldots, 0 \\
> \end{aligned}
> $$
> 
> 因此最后的余项为
> 
> $$
> r(X) = d \cdot q_0 + f_0
> $$
> 
> 这里 $i$ 从 $n - 2, \ldots, 0$ ，每次会涉及一次有限域乘法，最后算 $r(X)$ 也涉及一次乘法，因此复杂度为 $n ~ \mathbb{F}_{\mathsf{mul}}$ 。
> 
> 回到分析计算 $q_\zeta(X)$ 的复杂度，需要分析 $l_\zeta(X)$ 的次数。
> 
> $$
> \begin{split}
> l_\zeta(X) =& \Big(s_0(\zeta) \cdot (c(\zeta) - c_0) \\
> & + \alpha\cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))\\
>   & + \alpha^2\cdot s_1(\zeta) \cdot (u_{n-2}\cdot c(\zeta) - (1-u_{n-2})\cdot c(\omega^{2^{n-2}}\cdot\zeta)) \\
>   & + \cdots \\
>   & + \alpha^{n-1}\cdot s_{n-2}(\zeta)\cdot (u_{1}\cdot c(\zeta) - (1-u_{1})\cdot c(\omega^2\cdot\zeta))\\
>   & + \alpha^n\cdot s_{n-1}(\zeta)\cdot (u_{0}\cdot c(\zeta) - (1-u_{0})\cdot c(\omega\cdot\zeta)) \\
>   & + \alpha^{n+1}\cdot (L_0(\zeta)\cdot\big(z(X) - c_0\cdot a(X))\\
>   & + \alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(X)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(X) \big) \\
>   & + \alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(X) - v) \\
>   & - v_H(\zeta)\cdot t(X)\ \Big)
> \end{split}
> $$
> 
> 前面几项都为常数，
> - $\alpha^{n+1}\cdot (L_0(\zeta)\cdot\big(z(X) - c_0\cdot a(X))$ 的次数为 $N - 1 + N - 1 = 2N - 2$ 。
> - $\alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(X)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(X) \big)$ 的次数为 $N - 1$ 。
> - $\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(X) - v)$ 的次数为 $N - 1 + N - 1 = 2N - 2$ 。$v_H(\zeta)\cdot t(X)$ 的次数为 $2N - 1$ 。
> 
> 因此 $l_\zeta(X)$ 的次数为 $2N - 1$ 。因此计算 $q_\zeta(X)$ 的复杂度为 $(2N - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。


📝 **高效求逆算法**

一般地，对于 $N$ 个任意点 $a_0, \ldots, a_{N - 1}$ ，想要求出它们的逆 $a_0^{-1}, \ldots, a_{N-1}^{-1}$ ，如果直接求逆的话，计算消耗比较大，想将求逆操作转换为有限域上的乘法操作。具体的算法是

1. 先计算出 $N$ 个乘积
   
$$
\begin{aligned}
& b_0 = a_0 \\
& b_1 = b_0 \cdot a_1 = a_0 \cdot a_1 \\
& b_2 = b_1 \cdot a_2 = a_0 \cdot a_1 \cdot a_2 \\
& \ldots \\
& b_{N - 2} = b_{N - 3} \cdot a_{N - 2} = a_0 \cdot a_1 \cdots a_{N - 2} \\
& b_{N - 1} = b_{N - 2} \cdot a_{N - 1} = a_0 \cdot a_1 \cdots a_{N - 2} \cdot a_{N - 1}\\
\end{aligned}
$$

计算 $b_1, \ldots, b_{N - 1}$ ，每次都涉及一次有限域的乘法，复杂度为 $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。

2. 计算出 $b_{N-1}^{-1}$ ，复杂度为 $\mathbb{F}_{\mathsf{inv}}$ 。
3. 计算

$$
\begin{aligned}
  & b_{N-2}^{-1} = (a_0 \cdot a_1 \cdots a_{N - 2} )^{-1} = a_{N - 1} \cdot b_{N-1}^{-1} \\
  & b_{N-3}^{-1} = (a_0 \cdot a_1 \cdots a_{N - 3} )^{-1} = a_{N - 2} \cdot b_{N-2}^{-1} \\
  & \ldots \\
  & b_{1}^{-1} = (a_0 \cdot a_1 )^{-1} = a_{2} \cdot b_{2}^{-1} \\
\end{aligned}
$$

这一步复杂度为 $(N - 2) ~ \mathbb{F}_{\mathsf{mul}}$

4. 现在再从头相乘计算出 $a_0^{-1}, \ldots, a_{N-1}^{-1}$ 。

$$
\begin{aligned}
  & a_0^{-1} = \frac{1}{a_0 \cdot a_1} \cdot a_1 = b_1^{-1} \cdot a_1 \\
  & a_1^{-1} = \frac{1}{a_0 \cdot a_1} \cdot a_0 = b_1^{-1} \cdot b_0\\
  & a_2^{-1} = \frac{1}{a_0 \cdot a_1 \cdot a_2} \cdot (a_0 \cdot a_1) = b_2^{-1} \cdot b_1\\
  & \ldots \\
  & a_{N - 2}^{-1} = \frac{1}{a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 3} \cdot a_{N - 2}} \cdot (a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 3} ) = b_{N - 2}^{-1} \cdot b_{N - 3} \\
  & a_{N - 1}^{-1} = \frac{1}{a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 2} \cdot a_{N - 1}} \cdot (a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 2} ) = b_{N - 1}^{-1} \cdot b_{N - 2} 
\end{aligned}
$$

复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。

因此计算出逆 $a_0^{-1}, \ldots, a_{N-1}^{-1}$ 的总复杂度为 $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$ 。

**分析 Prover Cost**

在 Round 3-5 已经计算得到 $[l_{\zeta}(x)|_{x \in H}]$ ，下面计算 $[q_{\zeta}(x)|_{x \in H}]$ 。

- 先计算 $N$ 个逆，$[(x - \zeta)^{-1}|_{x \in H}]$ ，用上面介绍的高效求逆算法，复杂度为 $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $[q_{\zeta}(x)|_{x \in H}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$

因此这一步总复杂度为

$$
\mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

##### Round 3-8
第 8 步. 构造 $D\zeta$ 上的消失多项式 $z_{D_{\zeta}}(X)$

$$
z_{D_{\zeta}}(X) = (X-\zeta\omega)\cdots (X-\zeta\omega^{2^{n-1}})(X-\zeta)
$$

###### Prover Cost 3-8

在 Round 3-6 中已经计算出消失多项 $z_{D_{\zeta}}(X)$ 的系数形式。

##### Round 3-9
第 9 步，构造 Quotient 多项式  $q_c(X)$ :

$$
q_c(X) = \frac{(c(X) - c^*(X))}{(X-\zeta)(X-\omega\zeta)(X-\omega^2\zeta)\cdots(X-\omega^{2^{n-1}}\zeta)}
$$

###### Prover Cost 3-9

这里由于分母的多项式的次数比较高，因此用点值式来进行计算会比较高效。

已有：$c^*(X)$ 和 $z_{D_{\zeta}}(X)$ 的系数形式，在 Round 3-6 已经计算得到。

- 计算 $[c^*(x)|_{x \in H}]$ ，一次 FFT ，求 $c^*(X)$ 在 $H$ 上的取值，复杂度记为 $\mathsf{FFT}(N)$ 。
- 计算 $[z_{D_{\zeta}}(x)|_{x \in H}]$ ，一次 FFT ，求 $z_{D_{\zeta}}(X)$ 在 $H$ 上的取值，复杂度为 $\mathsf{FFT}(N)$ 。
- 计算逆 $[(z_{D_{\zeta}}(x))^{-1}|_{x \in H}]$ ，通过前面已经介绍的高效求逆算法，复杂度为 $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $[q_c(x)|_{x \in H}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。

因此这一步的总复杂度为

$$
2 ~ \mathsf{FFT}(N) + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

##### Round 3-10

第 10 步，构造 Quotient 多项式 $q_{\omega\zeta}(X)$

$$
q_{\omega\zeta}(X) = \frac{z(X) - z(\omega^{-1}\cdot\zeta)}{X - \omega^{-1}\cdot\zeta}
$$

###### Prover Cost 3-10

方法一：用系数式进行相除。

在前面 Round 2-4 已经计算得到了 $z(X)$ 的系数形式，那么 $z(X) - z(\omega^{-1}\cdot\zeta)$ 多项式的系数也很好得到，只需要改变常数项的值就行，分母的多项式为一次多项式，系数式也直接可以得到，那么这里分母除的是一个一元多项式，用线性多项式的除法，复杂度为 $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。

方法二：用点值式进行计算。

计算得到 $[q_{\omega\zeta}(x)|_{x \in H}]$ ，
- 先计算 $[(x - \omega^{-1} \cdot \zeta)^{-1}|_{x \in H}]$ ，用高效求逆算法进行计算，复杂度为 $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算 $[q_{\omega\zeta}(x)|_{x \in H}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。

这种方法的总复杂度为

$$
\mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

可以看到，由于分母只是一次多项式，用方法一会更高效一些。

##### Round 3-11

第 11 步，发送 $\big(Q_c = [q_c(\tau)]_1, Q_\zeta=[q_\zeta(\tau)]_1, Q_{\omega\zeta}=[q_{\omega\zeta}(\tau)]_1,  \big)$

###### Prover Cost 3-11

1. 在 Round 3-9 得到的 $[q_c(x)|_{x \in H}]$ ，那么

$$
Q_c = q_c(\omega^0) \cdot A_0 + \ldots q_c(\omega^{N - 1}) \cdot A_{N - 1}
$$
复杂度为 $\mathsf{msm}(N, \mathbb{G}_1)$ 。

2. 在 Round 3-7 得到 $[q_{\zeta}(x)|_{x \in H}]$ ，那么

$$
Q_\zeta = q_\zeta(\omega^0) \cdot A_0 + \ldots q_\zeta(\omega^{N - 1}) \cdot A_{N - 1}
$$
复杂度为 $\mathsf{msm}(N, \mathbb{G}_1)$ 。

3. 在 Round 3-10
- 若用方法一，则得到的是 $q_{\omega\zeta}(X)$ 的系数式 $q_{\omega\zeta}^{(0)}, q_{\omega\zeta}^{(1)}, \ldots, q_{\omega\zeta}^{(N - 2)}$ ，那么

$$
Q_{\omega\zeta} = q_{\omega\zeta}^{(0)} \cdot G + q_{\omega\zeta}^{(1)} \cdot (\tau \cdot G) + \cdots + q_{\omega\zeta}^{(N - 2)} \cdot (\tau^{N - 2} \cdot G)
$$
其中 $G$ 是椭圆曲线 $\mathbb{G}_1$ 上的生成元，$(G, \tau G, \ldots, \tau^{N - 2}G)$ 是 KZG10 的 SRS。那么这种方法的复杂度为 $\mathsf{msm}(N - 1, \mathbb{G}_1)$ 。

- 若用方法二，得到的是 $[q_{\omega\zeta}(x)|_{x \in H}]$ ，那么

$$
Q_\zeta = q_{\omega\zeta}(\omega^0) \cdot A_0 + \ldots q_{\omega \zeta}(\omega^{N - 1}) \cdot A_{N - 1}
$$
复杂度为 $\mathsf{msm}(N, \mathbb{G}_1)$ 。

总结上面的复杂度：

1. 在 Round 3-10 用方法一，系数形式，复杂度为

$$
2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
$$
2.  在 Round 3-10 用方法二，点值形式，复杂度为

$$
3 ~ \mathsf{msm}(N, \mathbb{G}_1)
$$
##### Prover Cost Round 3

将这一轮的计算复杂度相加为

1. 在 Round 3-10 用方法一，系数形式，复杂度为

$$
\begin{aligned}
& 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N)  +  (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + (12 N + 4n + 2) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{FFT}(N) + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{red} (N - 1) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (21N + 7n - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}}  } \\
& + {\color{red} (N - 1) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (22N + 7n - 4) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} }
\end{aligned}
$$
这种方法要求内存中要存储 SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ ，便于用系数形式进行多项式的承诺。

2.  在 Round 3-10 用方法二，点值形式，复杂度为

$$
\begin{aligned}
& 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N)  +  (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + (12 N + 4n + 2) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{FFT}(N) + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{red} \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 3 ~ \mathsf{msm}(N, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (21N + 7n - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } \\
& + {\color{red} \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 3 ~ \mathsf{msm}(N, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (25N + 7n - 6) ~ \mathbb{F}_{\mathsf{mul}} + 3~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathsf{msm}(N, \mathbb{G}_1) + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } \\
\end{aligned}
$$


#### Round 4.

##### Round 4-1

 Verifier 发送第二个随机挑战点 $\xi\leftarrow_{\$}\mathbb{F}_p$ 

##### Round 4-2

Prover 构造第三个 Quotient 多项式 $q_\xi(X)$

$$
q_\xi(X) = \frac{c(X) - c^*(\xi) - z_{D_\zeta}(\xi)\cdot q_c(X)}{X-\xi}
$$

###### Prover Cost 4-2

- $c^*(X)$ 的次数为 $N - 1$ ，因此计算 $c^*(\xi)$ 的复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。
- $z_{D_\zeta}(X)$ 的次数为 $n + 1$ ，因此计算 $z_{D_\zeta}(\xi)$ 的复杂度为 $(n + 2) ~ \mathbb{F}_{\mathsf{mul}}$
- 在 Round 3-9 已经得到 $[q_c(x)|_{x \in H}]$ ，先计算 $[(z_{D_\zeta}(\xi)\cdot q_c(x))|_{x \in H}]$ ，复杂度为 $N ~ \mathbb{F}_{\mathsf{mul}}$ 。
- 计算得到 $z_{D_\zeta}(\xi)\cdot q_c(X)$ 的系数式，用一次 IFFT，复杂度为 $\mathsf{IFFT}(N)$ 。
- 计算 $\frac{c(X) - c^*(\xi) - z_{D_\zeta}(\xi)\cdot q_c(X)}{X-\xi}$ 可以用到线性除法，分母多项式的次数为 $N - 1$ ，因此这里的复杂度为 $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 

因此这一步的总复杂度为

$$
\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} 
$$
##### Round 4-3

Prover 计算并发送 $Q_\xi$

$$
Q_\xi = \mathsf{KZG10.Commit}(q_\xi(X)) = [q_\xi(\tau)]_1
$$
###### Prover Cost 4-3

前面一步计算得到的是 $q_\xi(X)$ 的系数式，因此这一步承诺的复杂度主要看多项式的次数， $\deg(q_\xi) = N - 2$ ，复杂度为 $\mathsf{msm}(N - 1, \mathbb{G}_1)$ 。


这种方法要求内存中要存储 SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ 。

##### Prover Cost Round 4

汇总这一轮的复杂度

$$
\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N - 1, \mathbb{G}_1)
$$

#### Prover Cost

汇总所有轮的 Prover Cost

1. 在 Round 3-10 用方法一，系数形式，复杂度为

$$
\begin{align}
 & {\color{blue} (N - 1) ~ \mathbb{F}_{\mathsf{mul}}  + \mathsf{msm}(N, \mathbb{G}_1)}  \\
& + {\color{red} 4 ~ \mathsf{FFT}(N) + 4 ~ \mathsf{IFFT}(N) + (5nN + 10N + n + 2) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)}  \\
 & + 3 ~ \mathsf{FFT}(N) + (22N + 7n - 4) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } \\
 & + {\color{purple}\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
=  & (17nN + 36N + 9n - 2) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + 2~ \mathbb{F}_{\mathsf{inv}} + 5 ~ \mathsf{msm}(N, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

这种方法要求内存中要存储 SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ ，便于用系数形式进行多项式的承诺。


2.  在 Round 3-10 用方法二，点值形式，复杂度为

$$
\begin{align}
 & {\color{blue} (N - 1) ~ \mathbb{F}_{\mathsf{mul}}  + \mathsf{msm}(N, \mathbb{G}_1)}  \\
& + {\color{red} 4 ~ \mathsf{FFT}(N) + 4 ~ \mathsf{IFFT}(N) + (5nN + 10N + n + 2) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)}  \\
 & + 3 ~ \mathsf{FFT}(N) + (25N + 7n - 6) ~ \mathbb{F}_{\mathsf{mul}} + 3~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathsf{msm}(N, \mathbb{G}_1) + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } \\
& + {\color{purple}\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & (17nN + 39N + 9n - 4) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + 3~ \mathbb{F}_{\mathsf{inv}} + 6 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$


### 证明表示

$7\cdot\mathbb{G}_1$, $(n+1)\cdot\mathbb{F}_{p}$ 

$$
\begin{aligned}
\pi_{eval} &= \big(z(\omega^{-1}\cdot\zeta), c(\zeta)，c(\omega\cdot\zeta), c(\omega^2\cdot\zeta), c(\omega^4\cdot\zeta), \ldots, c(\omega^{2^{n-1}}\cdot\zeta), \\
& \qquad C_{c}, C_{t}, C_{z}, Q_c, Q_\zeta, Q_\xi, Q_{\omega\zeta}\big)
\end{aligned}
$$


### 验证过程

#### Step 1
1. Verifier 计算 $c^*(\xi)$ 使用预计算的 Barycentric Weights $\{\hat{w}_i\}$

$$
c^*(\xi)=\frac{\sum_i c_i^*\frac{\hat{w}_i}{\xi-x_i}}{\sum_i \frac{\hat{w}_i}{\xi-x_i}}
$$

再计算对应的承诺 $C^*(\xi)=[c^*(\xi)]_1$ 。

###### Verifier Cost 1

- [x] 待计算复杂度，主要涉及重心插值算法。 ✅ 2025-04-24

> Verifier:
> 
> - 先分析每一项计算的复杂度，计算 $\frac{\hat{w}_i}{\xi-x_i}$ ，分子 $\hat{w}_i$ 可以由预计算得到，分母 $\xi-x_i$ 计算得到后要计算其逆元，再和 $\hat{w}_i$ 相乘，因此这里的复杂度为 $\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}}$ 。
> - 计算 $c_i^*\frac{\hat{w}_i}{\xi-x_i}$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$ 。
> - 最后将分子分母得到有限域上的值相除，其实就是分母的值求逆，再和分子相乘，复杂度为 $\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}}$ 。
> - 计算得到 $c^*(\xi)$ 后计算其承诺 $C^*(\xi)$ ，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$
> 
> 因此这一步的总复杂度为 
>
> $$
> \begin{aligned}
>   & (n + 1) ~ (\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}}) + (n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1} \\
>  = & \color{orange}{(2n + 3) ~ \mathbb{F}_{\mathsf{mul}} + (n + 2) ~ \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1}}
> \end{aligned}
> $$

#### Step 2
Verifier 计算 $v_H(\zeta), L_0(\zeta), L_{N-1}(\zeta)$ 


$$
v_H(\zeta) = \zeta^N - 1
$$

$$
L_0(\zeta) = \frac{1}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-1}
$$

$$
L_{N-1}(\zeta) = \frac{\omega^{N-1}}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-\omega^{N-1}}
$$
###### Verifier Cost 2

> Verifier:
> - $v_H(\zeta)$ : $\zeta^N$ 可以用 $\log N$ 次有限域乘法计算得到，复杂度为 $\log N ~ \mathbb{F}_{\mathsf{mul}}$
> - $L_0(\zeta)$ : $1/N$ 可以在预计算中给出。计算 $\zeta-1$ 的逆元，涉及一次有限域中元素的求逆操作，复杂度记为 $\mathbb{F}_{\mathsf{inv}}$ ，$\zeta-1$ 的逆元与 $v_{H}(\zeta)$ 相乘，涉及一次有限域中的乘法操作，为 $\mathbb{F}_{\mathsf{mul}}$ ，其结果再与 $1/N$ 相乘，复杂度为 $\mathbb{F}_{\mathsf{mul}}$ ，因此这一步的总复杂度为 $\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - $L_{N-1}(\zeta)$ : $\omega^{N-1}/N$ 可以在预计算中给出。计算 $\zeta-\omega^{N-1}$ 的逆元，涉及一次有限域中元素的求逆操作，复杂度记为 $\mathbb{F}_{\mathsf{inv}}$ ，$\zeta-\omega^{N-1}$ 的逆元与 $v_{H}(\zeta)$ 相乘，涉及一次有限域中的乘法操作，为 $\mathbb{F}_{\mathsf{mul}}$ ，其结果再与 $\omega^{N-1}/N$ 相乘，复杂度为 $\mathbb{F}_{\mathsf{mul}}$ ，因此这一步的总复杂度为 $\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$ 。
>
> 因此这一步的总复杂度为 $2 ~ \mathbb{F}_{\mathsf{inv}} + (\log N + 4) ~ \mathbb{F}_{\mathsf{mul}}$

#### Step 3
Verifier 计算 $s_0(\zeta), \ldots, s_{n-1}(\zeta)$ ，其计算方法可以采用前文提到的递推方式进行计算。

###### Verifier Cost 3
- $\zeta^2, \zeta^4, \ldots, \zeta^{2^{n - 1}}$ 在 Step 2 中求 $\zeta^N$ 中可以得到。
- 剩下求值与在 Round 3-1 的分析一致，这一步的复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。

#### Step 4
Verifier 计算 $z_{D_\zeta}(\xi)$ ，
   
$$
z_{D_{\zeta}}(\xi) = (\xi-\zeta\omega)\cdots (\xi-\zeta\omega^{2^{n-1}})(\xi-\zeta)
$$


###### Verifier Cost 4

> Verifier:
> 
> $\xi-\zeta\omega^i$ 的计算在本轮的第 $1$ 步已经计算得到，因此这里的复杂度主要为 $n$ 个有限域上的数相乘，复杂度为 $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$ 。

#### Step 5

Verifier 计算线性化多项式的承诺 $C_l$ 


$$
\begin{split}
C_l & = 
\Big( \Big((c(\zeta) - c_0)s_0(\zeta) \\
& + \alpha \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))\cdot s_0(\zeta)\\
  & + \alpha^2\cdot (u_{n-2}\cdot c(\zeta) - (1-u_{n-2})\cdot c(\omega^{2^{n-2}}\cdot\zeta))\cdot s_1(\zeta)  \\
  & + \cdots \\
  & + \alpha^{n-1}\cdot (u_{1}\cdot c(\zeta) - (1-u_{1})\cdot c(\omega^2\cdot\zeta))\cdot s_{n-2}(\zeta)\\
  & + \alpha^n\cdot (u_{0}\cdot c(\zeta) - (1-u_{0})\cdot c(\omega\cdot\zeta))\cdot s_{n-1}(\zeta) \Big) \cdot [1]_1 \\
  & + \alpha^{n+1}\cdot L_0(\zeta)\cdot(C_z - c_0\cdot C_a)\\
  & + \alpha^{n+2}\cdot (\zeta-1)\cdot\big(C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a} ) \\
  & + \alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(C_z - v \cdot [1]_1) \\
  & - v_H(\zeta)\cdot C_t \Big)
\end{split}
$$

###### Verifier Cost 5

> Verifier: 
>
> - 先计算 $\alpha^2, \ldots, \alpha^{n+3}$ ，这里涉及 $n + 2$ 次有限域乘法，复杂度为 $(n + 2) ~ \mathbb{F}_{\mathsf{mul}}$ 。
> - $s_0(\zeta) \cdot (c(\zeta) - c_0)$ ，涉及一次有限域乘法，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
> - $\alpha \cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))$ ，复杂度为 $4 ~ \mathbb{F}_{\mathsf{mul}}$ ，从第 $2$ 到 $n + 1$ 项都是如此，因此复杂度为 $4n ~ \mathbb{F}_{\mathsf{mul}}$
> - 将上面计算的结果相加得到一个有限域的值，再与 $[1]_1$ 相乘，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$
> - $\alpha^{n+1}\cdot L_0(\zeta)\cdot(C_z - c_0\cdot C_a)$  
>   - $c_0\cdot C_a$ 复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $C_z - c_0\cdot C_a$ 涉及椭圆曲线的减法，但是椭圆曲线的减法是由椭圆曲线上的加法转换的，$P_1 - P_2 = P_1 + (-P_2)$ ，而设 $P_2 = (x_2, y_2)$ ，那么 $-P_2 = (x_2, -y_2)$ ，这里 $x_2, y_2$ 都是有限域上的值，因此相比椭圆曲线上的加法，多了一次有限域上取负数的操作，可由有限域上的加法完成，这里复杂度不做计入。因此这步的复杂度记为 $\mathsf{EccAdd}^{\mathbb{G}_1}$
> 
>     > 📝 关于椭圆曲线上的加法或减法 python 实现可参考 [py_ecc](https://github.com/ethereum/py_ecc/blob/main/py_ecc/bn128/bn128_curve.py) 。
>
>   - $\alpha^{n+1}\cdot L_0(\zeta)$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
>   - $\alpha^{n+1}\cdot L_0(\zeta)\cdot(C_z - c_0\cdot C_a)$ ，将上面计算的结果进行相乘，复杂度为 $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - 因此计算这一步的总复杂度为 $\mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $\alpha^{n+2}\cdot (\zeta-1)\cdot\big(C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a} \big)$
>   - $c(\zeta)\cdot C_{a}$ : $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $z(\omega^{-1}\cdot \zeta)\cdot [1]_1$ : $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a}$ : $2 ~\mathsf{EccAdd}^{\mathbb{G}_1}$
>   - $\alpha^{n+2}\cdot (\zeta-1)$: $\mathbb{F}_{\mathsf{mul}}$
>   - $\alpha^{n+2}\cdot (\zeta-1)\cdot\big(C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a} \big)$: $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - 总计： $\mathbb{F}_{\mathsf{mul}} + 3~\mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1}$
> - $\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(C_z - v \cdot [1]_1)$ 
>   - $v \cdot [1]_1$: $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $C_z - v \cdot [1]_1$: $\mathsf{EccAdd}^{\mathbb{G}_1}$
>   - $\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(C_z - v \cdot [1]_1)$: $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>   - 总计： $\mathbb{F}_{\mathsf{mul}} + 2~\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $v_H(\zeta)\cdot C_t$: $\mathsf{EccMul}^{\mathbb{G}_1}$
> - 将上面所有结果相加，涉及椭圆曲线上 $4$ 次加法，复杂度为 $4 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
> 
> 因此，在这一步计算 $l_{\zeta}(X)$ 的复杂度总计为
> 
> $$
> \begin{aligned}
>   & (n + 2 + 1 + 4n) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} \\
>   & + \mathbb{F}_{\mathsf{mul}} + 2~\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + \mathbb{F}_{\mathsf{mul}} + 3~\mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + \mathbb{F}_{\mathsf{mul}} + 2~\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + \mathsf{EccMul}^{\mathbb{G}_1} + 4 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   = & (5n + 6) ~ \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1}
> \end{aligned}
> $$

#### Step 6

Verifier 产生随机数 $\eta$ 来合并下面的 Pairing 验证：

$$
\begin{split}
e(C_l + \zeta\cdot Q_\zeta, [1]_2)\overset{?}{=}e(Q_\zeta, [\tau]_2)\\
e(C_c - C^*(\xi) - z_{D_\zeta}(\xi)\cdot Q_c + \xi\cdot Q_\xi, [1]_2) \overset{?}{=} e(Q_\xi, [\tau]_2)\\
e(C_z + \zeta\cdot Q_{\omega\zeta} - z(\omega^{-1}\cdot\zeta)\cdot[1]_1, [1]_2) \overset{?}{=} e(Q_{\omega\zeta}, [\tau]_2)\\
\end{split}
$$

合并后的验证只需要两个 Pairing 运算。


$$
\begin{split}

P &= \Big(C_l + \zeta\cdot Q_\zeta\Big) \\

& + \eta\cdot \Big(C_c - C^*(\xi) - z_{D_\zeta}(\xi)\cdot Q_c + \xi\cdot Q_\xi\Big) \\

& + \eta^2\cdot\Big(C_z + \zeta\cdot Q_{\omega\zeta} - z(\omega^{-1}\cdot\zeta)\cdot[1]_1\Big)

\end{split}
$$

$$
e\Big(P, [1]_2\Big) \overset{?}{=} e\Big(Q_\zeta + \eta\cdot Q_\xi + \eta^2\cdot Q_{\omega\zeta}, [\tau]_2\Big)
$$

###### Verifier Cost 6

> Verifier:
> 
> - 可以先计算出 $\eta^2$ ，复杂度为 $\mathbb{F}_{\mathsf{mul}}$
> - $\Big(C_l + \zeta\cdot Q_\zeta\Big)$: $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $\eta\cdot \Big(C_c - C^*(\xi) - z_{D_\zeta}(\xi)\cdot Q_c + \xi\cdot Q_\xi\Big)$ :
> 
>   $$
>   2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 3 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_1} = 3 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 3 ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>   $$
> - $\eta^2\cdot\Big(C_z + \zeta\cdot Q_{\omega\zeta} - z(\omega^{-1}\cdot\zeta)\cdot[1]_1\Big)$:  $3 ~\mathsf{EccMul}^{\mathbb{G}_1} + 2~\mathsf{EccAdd}^{\mathbb{G}_1}$
> - 计算 $P$ ，需要将上面的结果进行相加，复杂度为 $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $e\Big(P, [1]_2\Big)$ ，涉及一次椭圆曲线 pairing 操作，记为 $P$
> - $Q_\zeta + \eta\cdot Q_\xi + \eta^2\cdot Q_{\omega\zeta}$: $2 ~\mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $e\Big(Q_\zeta + \eta\cdot Q_\xi + \eta^2\cdot Q_{\omega\zeta}, [\tau]_2\Big)$ ，涉及一次椭圆曲线 pairing 操作，复杂度为 $P$
> 
> 将上面的所有结果相加，得到这一步的总复杂度为
> 
> $$
> \begin{aligned}
>   & \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + 3 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 3 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + 3 ~\mathsf{EccMul}^{\mathbb{G}_1} + 2~\mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + P + 2 ~\mathsf{EccMul}^{\mathbb{G}_1} + P \\
>   = & \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
> \end{aligned}
> $$

#### Verifier Cost

$$
\begin{aligned}
  & {\color{orange} (2n + 3) ~ \mathbb{F}_{\mathsf{mul}} + (n + 2) ~ \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1}}  \\
  & + 2 ~ \mathbb{F}_{\mathsf{inv}} + (\log N + 4) ~ \mathbb{F}_{\mathsf{mul}} \\
  & + 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
  & + (n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
  & + (5n + 6) ~ \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
  & + \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P \\
  = &  (9n + 8) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathbb{F}_{\mathsf{inv}} + 18 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 16 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P \\
  & + {\color{orange} (2n + 3) ~ \mathbb{F}_{\mathsf{mul}} + (n + 2) ~ \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1}} \\
  = & (11n + 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 4) ~ \mathbb{F}_{\mathsf{inv}} + 19 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 16 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
\end{aligned}
$$

## 协议复杂度汇总

### Commit Phase

**Prover's cost:**

$$
N\log N ~\mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N, \mathbb{G}_1)
$$

### Evaluation Protocol

**Prover's cost:**

1. 在 Round 3-10 用方法一，系数形式，复杂度为

$$
\begin{align}
 (17nN + 36N + 9n - 2) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + 2~ \mathbb{F}_{\mathsf{inv}} + 5 ~ \mathsf{msm}(N, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

这种方法要求内存中要存储 SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ ，便于用系数形式进行多项式的承诺。

2.  在 Round 3-10 用方法二，点值形式，复杂度为

$$
\begin{align}
  (17nN + 39N + 9n - 4) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + 3~ \mathbb{F}_{\mathsf{inv}} + 6 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

**Verifier's cost:**

$$
(11n + 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 4) ~ \mathbb{F}_{\mathsf{inv}} + 19 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 16 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
$$

**Proof size:**

$$
(n + 1) \cdot \mathbb{F}_p + 7 ~ \mathbb{G}_1
$$
