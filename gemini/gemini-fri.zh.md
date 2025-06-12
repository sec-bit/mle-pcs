# Gemini ：对接 FRI

- Jade Xie  <jade@secbit.io>

Gemini 协议 [BCH+22] 为我们提供了一种将 multilinear polynomial PCS 转换为一元多项式承诺方案的思路。简单回顾下，即为了证明一个 MLE 多项式在某个点的打开值为 $v$ ，可以转换为一个内积证明，该内积证明是对一个一元多项式不断进行类似 sumcheck 或者 FRI 协议中的 split-and-fold 得到的，这样又把内积证明转换为了要证明一些一元多项式在某些随机点处的值是正确的。在 Gemini 原论文中采用 KZG10 的一元多项式 PCS 实现了该证明。其实，一元多项式 PCS 也可以采用 FRI PCS 的方案。FRI PCS 有一个好处是对于不同次数的多项式在多个点的打开，可以用随机数合并成一个多项式，只需要再调用一次 FRI 的 low degree test 就能一次完成这些证明。

下面借鉴HyperPlonk 论文 [BBBZ23] 附录 B 中的描述，给出 Gemini 对接 FRI PCS 的详细协议。

## 协议描述

证明目标：对于一个有 $n$ 个变量的 MLE 多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ ，其表示为系数形式：

$$
\tilde{f}(X_0, X_1, \ldots, X_{n - 1}) = \sum_{i = 0}^{2^n - 1}c_i \cdot X_0^{i_0} X_1^{i_1} \cdots X_{n - 1}^{i_{n-1}}
$$
其中 $(i_0, i_1,\ldots,i_{n - 1})$ 是 $i$ 的二进制表示，$i_0$  是二进制表示的最低位，满足 $i = \sum_{j=0}^{n-1}i_j 2^{j}$ 。

证明的目标是证明 $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ 在点 $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$ 处的值为 $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 。

### 公共输入

1.  FRI 协议参数：Reed Solomon 编码选取的区域 $D_n \subset D_{n-1} \subset \cdots \subset D_0 = D$ ，码率 $\rho$ ，查询阶段的次数 $l$ 。
2. 多项式 $f(X)$ 的承诺 $C_f$

$$
C_f = \mathsf{cm}([f(x)|_{x \in D}]) = \mathsf{MT.commit}([f(x)|_{x \in D}]) 
$$
其中 $f(X)$ 是一个次数为 $2^n - 1$ 的多项式，其和 $\tilde{f}$ 有相同的系数 $\vec{c}$ ，

$$
f(X) = \sum_{i = 0}^{2^n - 1} c_i \cdot X^i
$$
3. 求值点  $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$
4. $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 


### Witness

- 多元多项式 $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ 的系数 $\vec{c} = (c_0,c_1, \ldots, c_{2^n - 1})$ 


### Round 1

1. Prover 记 $h_0(X) = f(X)$ ，计算折叠多项式 $h_1(X), h_2(X), \ldots, h_{n-1}(X)$ ，使得对于 $i = 1, \ldots, n-1$ 有

$$
h_{i}(X^{2}) = \frac{h_{i - 1}(X) + h_{i - 1}(-X)}{2} + u_{i - 1} \cdot \frac{h_{i - 1}(X) - h_{i - 1}(-X)}{2X}
$$
2. Prover 计算承诺 $(C_{h_{1}},C_{h_{2}}, \ldots, C_{h_{n-1}})$ ，其中对于 $i = 1, \ldots, n-1$ 有

$$
C_{h_{i}} = \mathsf{cm}([h_{i}(x)|_{x \in D}]) = \mathsf{MT.commit}([h_{i}(x)|_{x \in D})
$$

### Round 2

1. Verifier 发送随机数 $\beta \stackrel{\$}{\leftarrow} \mathbb{F}^* \setminus D$
2. Prover 计算 $\{h_i(\beta), h_{i}(- \beta), h_i(\beta^2)\}_{i = 0}^{n-1}$ ，并发送给 Verifier。

### Round 3

1. Verifier 发送随机数 $r \stackrel{\$}{\leftarrow} \mathbb{F}$
2. 先对每一个多项式 $h_{i}(X)(i = 1, \ldots, n)$ 进行 degree correction ，使得次数都对齐到 $2^{n}- 1$ 。每个多项式的次数为 $\deg(h_i)=2^{n-i}-1$ 。对于 $i = 1, \ldots, n - 1$ ，分别计算 $h'_i(X)$ ，

方法一：

$$
h'_i(X)=h_i(X)+r\cdot X^{2^{n} - 2^{n-i}} \cdot h_i(X)
$$

方法二：若采用 STIR 论文 [ACFY24] 中的 degree correction 方法，则

$$
h'_i(X)=\sum_{j = 0}^{2^{n}- 2^{n - i}} r^{j} \cdot X^{j} \cdot h_i(X)=h_i(X)+r\cdot X \cdot h_i(X)+r^{2} \cdot X^2 \cdot h_i(X) + \ldots + r^{2^n - 2^{n-i}} \cdot X^{2^n - 2^{n-i}} \cdot h_i(X)
$$
> 注：方法二会比方法一有更高的安全性。([ACFY24, 2.3])

3. 将 $h_0(X)$ 与 $h_1'(X), \ldots, h_{n-1}'(X)$ 用随机数 $r$ 的幂次 batch 成一个多项式，

方法一：计算

$$
\begin{align*}
h^*(X) & = h_0(X) + r^{1 + (0)} \cdot h_1'(X) + r^{2 + (0 + 1)} \cdot h_2'(X) + r^{3 + (0 + 1 + 1)} \cdot h_3'(X)+ \ldots + r^{n - 1 + (0 + 1 \cdot (n - 2))} \cdot h_{n-1}'(X) \\
& = h_0(X) + r \cdot h_1'(X) + r^{3} \cdot h_2'(X) + r^{5} \cdot h_3'(X)+ \ldots + r^{2n-3} \cdot h_{n-1}'(X) 
\end{align*} \tag{1}
$$

方法二：若采用 STIR 论文中的 degree correction 方法，则此时 batch 的多项式计算为

$$
\begin{align*}
h^*(X) & = h_0(X) + r^{1 + (0)} \cdot h_1'(X) + r^{2 + (0 + e_1)} \cdot h_2'(X) + r^{3 + (0 + e_1 + e_2)} \cdot h_3'(X)\\
& \quad + \ldots + r^{n - 1 + (0 + e_1 + e_2 + \ldots + e_{n-2})} \cdot h_{n-1}'(X) \\
& = h_0(X) + r \cdot h_1'(X) + r^{2 + 2^n - 2^{n -1}} \cdot h_2'(X) + r^{2 + \sum_{i=1}^{2}(2^n-2^i)} \cdot h_3'(X) \\
& \quad + \ldots + r^{n - 1+\sum_{i=1}^{n-2}(2^n-2^i)} \cdot h_{n-1}'(X) 
\end{align*} \tag{2}
$$
4. 计算商多项式 $q'(X)$ ，能验证 $h^*(X)$ 同时在点 $(\beta,-\beta,\beta^2)$ 打开是否正确，

$$
q'(X) = \frac{h^*(X)-h^*(\beta)}{X-\beta} + \frac{h^*(X)-h^*(-\beta)}{X+\beta} + \frac{h^*(X)-h^*(\beta^2)}{X-\beta^2}
$$
上述商多项式的构造参考论文 [H22] Multi-point queries 小节。

### Round 4

这一轮将商多项式 $q'(X)$ 对齐到 $2$ 的幂次，以对接 FRI 协议。

1. Verifier 发送随机数 $\lambda \stackrel{\$}{\leftarrow} \mathbb{F}$
2. Prover 计算 

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$
在 $D$ 上的值。

### Round 5

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

### Round 6

这一轮是接着 Prover 与 Verifier 进行 FRI 协议的 low degree test 交互的查询阶段，Verifier 重复查询 $l$ 次，每一次 Verifier 都会从 $D_0$ 中选取一个随机数，让 Prover 发送在第 $i$ 轮折叠的值及对应的 Merkle Path，用来让 Verifier 验证每一轮折叠的正确性。

重复 $l$ 次：
- Verifier 从 $D_0$ 中随机选取一个数 $s^{(0)} \stackrel{\$}{\leftarrow} D_0$ 
- Prover 打开 $\{h_i(s^{(0)})\}_{i = 0}^{n-1}$ 与 $\{h_i(-s^{(0)})\}_{i = 0}^{n-1}$ 的承诺，即这些点的值与对应的 Merkle Path，并发送给 Verifier
  
  $$
  \{(h_i(s^{(0)}), \pi_{h_i}(s^{(0)}))\}_{i = 0}^{n-1} \leftarrow \{\mathsf{MT.open}([h_i(x)|_{x \in D_0}], s^{(0)})\}_{i = 0}^{n-1}
  $$

$$
  \{(h_i(-s^{(0)}), \pi_{h_i}(-s^{(0)}))\}_{i = 0}^{n-1} \leftarrow \{\mathsf{MT.open}([h_i(x)|_{x \in D_0}], -s^{(0)})\}_{i = 0}^{n-1}
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

### Proof

Prover 发送的证明为

$$
\pi = (C_{h_{1}},C_{h_{2}}, \ldots, C_{h_{n-1}}, \{h_i(\beta), h_{i}(- \beta), h_i(\beta^2)\}_{i = 0}^{n-1}, \pi_{q})
$$
用符号 $\{\cdot\}^l$ 表示在 FRI low degree test 的查询阶段重复查询 $l$ 次产生的证明，由于每次查询是随机选取的，因此花括号中的证明也是随机的。那么 FRI 进行 low degree test 的证明为

$$
\begin{aligned}
  \pi_{q} = &  ( \mathsf{cm}(q^{(1)}(X)), \ldots, \mathsf{cm}(q^{(n - 1)}(X)),q^{(n)}(x_0),  \\
  & \, \{h_0(s^{(0)}), \pi_{h_0}(s^{(0)}), h_0(- s^{(0)}), \pi_{h_0}(-s^{(0)}), \cdots ,\\
  & \quad h_{n-1}(s^{(0)}), \pi_{h_{n-1}}(s^{(0)}), h_{n-1}(- s^{(0)}), \pi_{h_{n-1}}(-s^{(0)}), \\
  & \quad q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)}),q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)}), \ldots, \\
  & \quad q^{(n - 1)}(s^{(n - 1)}), \pi_{q^{(n - 1)}}(s^{(n - 1)}),q^{(n - 1)}(-s^{(n - 1)}), \pi_{q^{(i)}}(-s^{(n - 1)})\}^l)
\end{aligned}
$$

### Verification


1. Verifier 验证折叠过程是否正确，对于 $i = 1, \ldots, n - 1$ ，根据 Prover 发送过来的值计算并验证

$$
h_{i}(\beta^{2}) \stackrel{?}{=} \frac{h_{i - 1}(\beta) + h_{i - 1}(-\beta)}{2} + u_{i - 1} \cdot \frac{h_{i - 1}(\beta) - h_{i - 1}(-\beta)}{2\beta}
$$
2. Verifier 验证最后是否折叠为常数 $v$ ，验证

$$
\frac{h_{n - 1}(\beta) + h_{n - 1}(-\beta)}{2} + u_{n - 1} \cdot \frac{h_{n - 1}(\beta) - h_{n - 1}(-\beta)}{2\beta} \stackrel{?}{=} v
$$

3. 验证 $q(X)$ 的 low degree test 证明，

$$
\mathsf{FRI.LDT.verify}(\pi_{q}, 2^n) \stackrel{?}{=} 1
$$

具体验证过程为，重复 $l$ 次：
- 验证 $\{h_i(s^{(0)})\}_{i = 0}^{n-1}$ 与 $\{h_i(-s^{(0)})\}_{i = 0}^{n-1}$ 的正确性 ，对于 $i = 0, \ldots, n - 1$ ，验证

$$
\mathsf{MT.verify}(\mathsf{cm}(h_i(X)), h_i(s^{(0)}), \pi_{h_i}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(h_i(X)), h_i(-s^{(0)}), \pi_{h_i}(-s^{(0)})) \stackrel{?}{=} 1
$$
- Verifier 根据 $\{h_i(s^{(0)})\}_{i = 0}^{n-1}$ 与 $\{h_i(-s^{(0)})\}_{i = 0}^{n-1}$ 这些值计算出 $h^*(s^{(0)})$ 与 $h^*(-s^{(0)})$ 的值，根据 $\{h_i(\beta)\}_{i = 0}^{n-1}, \{h_i(-\beta)\}_{i = 0}^{n-1}, \{h_i(\beta^2)\}_{i = 0}^{n-1}$ 计算出 $h^*(\beta), h^*(-\beta), h^*(\beta^2)$ ，对于 $x \in \{s^{(0)}, -s^{(0)}, \beta, -\beta, \beta^2\}$ ，Verifier 计算出 $h^*(x)$ 的方法如下：

方法一：对于 $i = 1, \ldots, n - 1$ ，计算出

$$
h'_i(x)=h_i(x)+r\cdot (x)^{2^{n} - 2^{n-i}} \cdot h_i(x)
$$

接着计算

$$
\begin{align*}
h^*(x) & = h_0(x) + r \cdot h_1'(x) + r^{3} \cdot h_2'(x) + r^{5} \cdot h_3'(x)+ \ldots + r^{2n-3} \cdot h_{n-1}'(x) 
\end{align*} 
$$

方法二：若采用 STIR 论文 [ACFY24] 中的 degree correction 方法，对于 $i = 1, \ldots, n - 1$ ，计算出

$$
h'_i(x)=\sum_{j = 0}^{2^{n}- 2^{n - i}} r^{j} \cdot (x)^{j} \cdot h_i(x) = \begin{cases}
 h_i(x) \cdot \frac{1 - (r \cdot x)^{2^n - 2^{n-i} + 1}}{1 - r \cdot x} & \text{if } r \cdot x \neq 0\\
h_i(x) \cdot (2^n - 2^{n-i} + 1) & \text{if } r \cdot x = 0
\end{cases}
$$
接着计算得到

$$
\begin{align*}
h^*(x) & = h_0(x) + r \cdot h_1'(x) + r^{2 + 2^n - 2^{n -1}} \cdot h_2'(x) + r^{2 + \sum_{i=1}^{2}(2^n-2^i)} \cdot h_3'(x) \\
& \quad + \ldots + r^{n - 1+\sum_{i=1}^{n-2}(2^n-2^i)} \cdot h_{n-1}'(x) 
\end{align*} 
$$


- Verifier 计算
  $$
  q'(s^{(0)}) = \frac{h^*(s^{(0)})-h^*(\beta)}{s^{(0)}-\beta} + \frac{h^*(s^{(0)})-h^*(-\beta)}{s^{(0)}+\beta} + \frac{h^*(s^{(0)})-h^*(\beta^2)}{s^{(0)}-\beta^2}
  $$

$$
  q'(-s^{(0)}) = \frac{h^*(-s^{(0)})-h^*(\beta)}{-s^{(0)}-\beta} + \frac{h^*(-s^{(0)})-h^*(-\beta)}{-s^{(0)}+\beta} + \frac{h^*(-s^{(0)})-h^*(\beta^2)}{-s^{(0)}-\beta^2}
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
  
## Reference

- [BCH+22] Bootle, Jonathan, Alessandro Chiesa, Yuncong Hu, *_et al. "Gemini: Elastic SNARKs for Diverse Environments."_ Cryptology ePrint Archive* (2022). [https://eprint.iacr.org/2022/420](https://eprint.iacr.org/2022/420) 
- [BBBZ23] Chen, Binyi, Benedikt Bünz, Dan Boneh, and Zhenfei Zhang. "Hyperplonk: Plonk with linear-time prover and high-degree custom gates." In _Annual International Conference on the Theory and Applications of Cryptographic Techniques_, pp. 499-530. Cham: Springer Nature Switzerland, 2023.
- [H22] Haböck, Ulrich. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [ACFY24] Arnon, Gal, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "STIR: Reed-Solomon proximity testing with fewer queries." In _Annual International Cryptology Conference_, pp. 380-413. Cham: Springer Nature Switzerland, 2024.