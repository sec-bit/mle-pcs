# 扩张域上的求逆计算

对于一个 Base Field $\mathbb{F}_p$ 上的扩张域 $\mathbb{F}_{p^n}$。如果直接采用 Extended Euclidean Algorithm 或者 Fermat Little Theorem 来计算逆元，需要多次在 $\mathbb{F}_{p^n}$ 上进行乘法运算。这个开销较大。一种优化的思路是将 Extension Field 上的求逆运算转换为 Base Field 或者 Subfield 上的求逆运算。转换过程引入少量的额外乘法运算，但整体上计算量会降低。

## 二次扩张

我们先考虑一个简单的情况，假设 Base Field 为 $\mathbb{F}_p$，Extension Field 为 $\mathbb{F}_{p^2}$。

我们指定一个不可约多项式 $f(X)\in\mathbb{F}_p[X]$，然后构造 Extension Field $\mathbb{F}_{p^2}$ 为 $\mathbb{F}_p[X]/(f(X))$。

$$
f(X) = X^2 - c_0
$$

那么 

$$
\mathbb{F}_{p^2} = \mathbb{F}_{p}[X]/(X^2 - c_0)
$$

我们假设 $\alpha$ 为 $X^2-c_0$ 在 $\mathbb{F}_{p^2}$ 上的一个根。那么 $\mathbb{F}_{p^2}$ 可以写成 $\mathbb{F}_{p}[\alpha]$。

根据有限域理论，$\mathbb{F}_{p^2}$ 上的元素可以表示为 $a_0 + a_1 \alpha$，其中 $a_0, a_1 \in \mathbb{F}_{p}$。

$$
\mathbb{F}_{p^2} = \{a_0 + a_1 \alpha \mid a_0, a_1 \in \mathbb{F}_{p}\}
$$

如果我们要求解 $a=a_0 + a_1 \alpha$ 的逆元，记为 $a^{-1}$，我们可以将其转换为 $\mathbb{F}_{p}$ 上的元素。
令 $a^{-1} = b_0 + b_1 \alpha$，那么我们有

$$
(a_0 + a_1 \alpha)(b_0 + b_1 \alpha) = 1
$$

化简上面等式的左边，并且利用 $\alpha^2 = c_0$，我们可以得到下面的等式：

$$
(a_0b_0 + c_0\cdot a_1b_1) + (a_0b_1 + a_1b_0)\alpha = 1
$$

由于等式右边没有 $u$ 项，我们可得 $a_0b_1 + a_1b_0 = 0$，并且 $a_0b_0 + c_0\cdot a_1b_1 = 1$。然后上面这个等式也可以用下面的矩阵形式表示：

$$
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0
\end{bmatrix}
\begin{bmatrix}
b_0 \\
b_1 \\
\end{bmatrix}
= \begin{bmatrix}
1 \\ 0
\end{bmatrix}
$$

将左边的矩阵求逆之后，我们可以得到 $b_0$ 和 $b_1$ 的计算矩阵：

$$
\begin{bmatrix}
b_0 \\
b_1 \\
\end{bmatrix}
=
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0
\end{bmatrix}^{-1}
\begin{bmatrix}
1 \\
0 \\
\end{bmatrix}
=
(a_0^2 - c_0\cdot a_1^2)^{-1}
\begin{bmatrix}
a_0 & - c_0\cdot a_1 \\
-a_1 & a_0
\end{bmatrix}
\begin{bmatrix}
1 \\
0 \\
\end{bmatrix}
$$

上式中的 $(a_0^2 - c_0\cdot a_1^2)^{-1}$ 是 $\mathbb{F}_{p}$ 中的一个元素。因此，求解 $a^{-1}$ 的计算被转换到了 $\mathbb{F}_{p}$ 上的求逆运算，额外带上常数次（这里是五次）$\mathbb{F}_{p}$ 上的乘法运算。

```python
def quadratic_inv(t: K, c0: F):
    if t == K(0):
        raise ValueError("t=0")
    g = K.gen()   # root of f(X)=(X^2 - c0)
    [a0, a1] = t.list()
    a0_sq = a0 * a0
    a1_sq = a1 * a1
    
    scalar = a0_sq - c0 * a1_sq
    scalar_inv = scalar.inverse()

    b0 = scalar_inv * a0
    b1 = scalar_inv * (-a1)
    
    return b0 + b1 * g
```

这个方法不仅限于二项式扩张，对于任意的不可约多项式都适用。比如我们用下面的多项式来产生 $\mathbb{F}_{p^2}$：

$$
g(X) = X^2 + c_1X + c_0
$$

然后我们试探下 $\mathbb{F}_{p^2}$ 中的两个元素的乘积：

$$
\begin{aligned}
(a_0 + a_1 \alpha)(b_0 + b_1 \alpha) &= a_0b_0 + (a_0b_1 + a_1b_0)\alpha + a_1b_1 \alpha^2 \\
&= a_0b_0 + (a_0b_1 + a_1b_0)\alpha + a_1b_1 (c_1\alpha + c_0) \\
&= (a_0b_0 + c_0a_1b_1) + (a_0b_1 + a_1b_0 + c_1a_1b_1)\alpha
\end{aligned}
$$

写成矩阵形式为：

$$
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0+c_1a_1
\end{bmatrix}
\begin{bmatrix}
b_0 \\
b_1 \\
\end{bmatrix}
= \begin{bmatrix}
1 \\ 0
\end{bmatrix}
$$

左边矩阵求逆之后为：

$$
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0+c_1a_1
\end{bmatrix}^{-1}
=
(a_0^2 -a_1^2c_0 + a_0a_1c_1)^{-1}
\begin{bmatrix}
a_0+a_1c_1 & -a_1c_0 \\
-a_1 & a_0
\end{bmatrix}
$$



## 三次扩张

我们仍然假设 Base Field 为 $\mathbb{F}_p$，三次的 Extension Field 为 $\mathbb{F}_{p^3}$。

为了简化起见，我们继续指定一个二项式不可约多项式 $f(X)\in\mathbb{F}_p[X]$，然后构造 Extension Field $\mathbb{F}_{p^3}$ 为 $\mathbb{F}_p[X]/(f(X))$。

$$
f(X) = X^3 - c_0
$$

假设 $\alpha$ 为 $X^3-c_0$ 在 $\mathbb{F}_{p^3}$ 上的一个根。那么 $\mathbb{F}_{p^3}$ 上的元素可以表示为 $a_0 + a_1 \alpha + a_2 \alpha^2$，其中 $a_0, a_1, a_2 \in \mathbb{F}_{p}$。

令 $a^{-1} = b_0 + b_1 \alpha + b_2 \alpha^2$，那么我们有

$$
(a_0 + a_1 \alpha + a_2 \alpha^2)(b_0 + b_1 \alpha + b_2 \alpha^2) = 1
$$

展开之后，并代入 $\alpha^3 = c$，我们可以得到

$$
(a_0b_0 + c_0\cdot a_2b_1 + c_0\cdot a_1b_2) + (a_0b_1 + a_1b_0 + c_0\cdot a_2b_2) \alpha + (a_0b_2 + a_1b_1 + a_2b_0) \alpha^2 = 1
$$

我们把上面的等式写成矩阵形式：

$$
\begin{bmatrix}
a_0 & c_0\cdot a_2 & c_0\cdot a_1 \\
a_1 & a_0 & c_0\cdot a_2 \\
a_2 & a_1 & a_0
\end{bmatrix}
\begin{bmatrix}
b_0 \\
b_1 \\
b_2 \\
\end{bmatrix}
= \begin{bmatrix}
1 \\
0 \\
0 \\
\end{bmatrix}
$$

我们把左边的矩阵求逆：

$$
\begin{bmatrix}
a_0 & c_0\cdot a_2 & c_0\cdot a_1 \\
a_1 & a_0 & c_0\cdot a_2 \\
a_2 & a_1 & a_0
\end{bmatrix}^{-1}
=
(s)^{-1}
\begin{bmatrix}
a_0^2 - c_0\cdot a_1\cdot a_2 
& c_0\cdot a_1^2 - c_0\cdot a_0\cdot a_2 
& c_0^2\cdot a_2^2 - c_0\cdot a_0\cdot a_1 
\\
c_0\cdot a_2^2 - a_0\cdot a_1 
& a_0^2 - c_0\cdot a_1\cdot a_2 
& c_0\cdot a_1^2 - c_0\cdot a_0\cdot a_2 
\\
a_1^2 - a_0\cdot a_2 
& c\cdot a_2^2 - a_0\cdot a_1 
& c\cdot a_1\cdot a_2 - a_0^2
\end{bmatrix}
$$

这里 $s=a_0^3 + c_0\cdot a_1^3 + c_0^2\cdot a_2^3 - 3c_0\cdot a_0\cdot a_1\cdot a_2$ 。

接下来我们可以将 $b_0, b_1, b_2$ 的计算转换为 $\mathbb{F}_{p}$ 上的求逆运算， $s^{-1}$ ，并乘以 Base field 上的元素：

$$
\begin{bmatrix}
b_0 \\
b_1 \\
b_2 \\
\end{bmatrix}
= s^{-1}
\begin{bmatrix}
a_0^2 - c_0\cdot a_1\cdot a_2  \\
c_0\cdot a_2^2 - a_0\cdot a_1  \\
a_1^2 - a_0\cdot a_2 
\end{bmatrix}
$$

```python
def cubic_inv(t: K, w: F):
    [a0, a1, a2] = t.list()
    g = K.gen()
    a0_sq = a0 * a0
    a1_sq = a1 * a1
    a2_w = w * a2
    a0_a1 = a0 * a1

    scalar = a0*a0_sq + w*a1*a1_sq + a2_w * a2_w * a2 - F(3) * a2_w * a0_a1
    scalar_inv = scalar.inverse()
    b0 = scalar_inv * (a0_sq - a1 * a2_w)
    b1 = scalar_inv * (a2_w * a2 - a0_a1)
    b2 = scalar_inv * (a1_sq - a0 * a2)
    return b0 + b1 * g + b2 * g^2
```

我们可以合并一些可以复用的 $\mathbb{F}_{p}$ 上的乘法运算，最终得到 14 次 $\mathbb{F}_{p}$ 上的乘法运算加上一次 $\mathbb{F}_{p}$ 上的求逆运算。

## 四次扩张

对于四次扩张，我们仍然可以采用上面的思路。不过矩阵求逆的复杂度在快速增加。

我们当然可以将四次扩张转换成两步的二次扩张。

$$
\mathbb{F}_{p^4} = \mathbb{F}_{p}(\alpha)(\beta)
$$

那么求逆运算的第一步将四次扩张域上的求逆运算转换成二次扩张域上的求逆运算，最后再利用二次扩张的求逆公式，将其求逆运算转换到 Base Field 上的求逆运算。

如果 $\mathbb{F}_{p^4}$ 是一个直接的四次扩张，但是使用的不可约多项式是一个四次的二项式，那么我们可以有一种更优化的方案（该方案来自 RicsZero 的实现）。

$$
\mathbb{F}_{p^4}\cong\mathbb{F}_{p}[X]/(X^4-c)
$$

为了计算某个元素 $\theta$ 的乘法逆元 $\theta^{-1}$，即

$$
\frac{1}{\theta} = \frac{1}{a_0 + a_1\alpha + a_2\alpha^2 + a_3\alpha^3}
$$

这里 $\alpha$ 是不可约多项式 $X^4-c=0$ 的根，满足 $\alpha^4-c=0$。我们将上面等式的分子分母同时乘上一个辅助元素 $\zeta$

$$
\zeta = a_0 - a_1\alpha + a_2\alpha^2 - a_3\alpha^3
$$

这样

$$
\frac{1}{\theta} = \frac{\zeta}{\zeta\cdot\theta} 
$$

由于 $\theta$ 和 $\zeta$ 中有两个系数正负号相反，因此乘积 $\zeta\cdot\theta$ 中有两个系数（关于 $\alpha$ 和 $\alpha^3$）将被消掉：

$$
\zeta\cdot\theta = (a_0^2 + a_2^2\cdot c - 2a_1a_3\cdot c) + (2a_0a_2 - a_1^2 + a_3^2\cdot c)\cdot \alpha^2
$$

我们令 $\zeta\cdot\theta = b_0 + b_1\alpha^2$，这里 $b_0, b_1\in\mathbb{F}_{p}$，定义如下：

$$
\begin{aligned}
b_0 &= a_0^2 + a_2^2\cdot c - 2a_1a_3\cdot c \\
b_1 &= 2a_0a_2 - a_1^2 + a_3^2\cdot c
\end{aligned}
$$

继续引入一个辅助元素 $\xi=b_0 - b_1\alpha^2$，然后再次在 $\theta^{-1}$ 的分子分母上同时乘上 $\xi$：

$$
\frac{1}{\theta} = \frac{\zeta}{\zeta\cdot\theta} 
= \frac{\zeta\cdot\xi}{\zeta\cdot\xi\cdot\theta}
$$

于是分母 $\zeta\cdot\xi\cdot\theta$ 将是一个 $\mathbb{F}_{p}$ 上的元素，推导见下：

$$
\zeta\cdot\xi\cdot\theta = (b_0 + b_1\alpha^2)(b_0-b_1\alpha^2) = b_0^2 - b_1^2\alpha^4 = b_0^2 - b_1^2\cdot c
$$

注意到这里因为该方案要求不可约多项式必须为一个二项式，即 $X^4-c$，所以上面等式中的 $\alpha^4$ 项可以被完全替换成 $c$，从而确保 $\zeta\cdot\xi\cdot\theta$ 是一个 $\mathbb{F}_{p}$ 上的元素。否则如果不可约多项式形如 $X^4-c'\cdot X+ c$，那么等式右边会引入一个多余的 $\alpha$ 项，这将难以处理。

最后我们可以得到 $\theta^{-1}$ 的计算公式：

$$
\frac{1}{\theta} 
= \frac{\zeta\cdot\xi}{\zeta\cdot\xi\cdot\theta}
= \frac{(a_0 - a_1\alpha + a_2\alpha^2 - a_3\alpha^3)
\cdot (b_0 - b_1\alpha^2)}{b_0^2 - b_1^2\cdot c}
$$

显然上面的等式中的分母是一个 $\mathbb{F}_{p}$ 上的元素。而分子关于 $\alpha$ 的各个系数是若干 $\mathbb{F}_{p}$ 上的元素的乘积。
## 基于 Frobenius Map 的求逆算法

上面几个算法的核心思想是把 Extension Field 上的求逆运算转换成 Base Field 上的求逆运算。

基于 Frobenius Map，我们也可以将 Extension Field 上的求逆运算转换成 Base Field 上的求逆运算。

对于 n 次扩张域 $\mathbb{F}_{p^n}$，其 Frobenius Map 为 $Frob_n: \mathbb{F}_{p^n} \to \mathbb{F}_{p^n}$，定义为 $Frob_n(\alpha) = \alpha^{p}$。

对于任何一个 $\mathbb{F}_{p^n}$ 上的元素 $\alpha$，我们可以用过 Frobeinus Map 得到它的全部共轭元素：

$$
\alpha, \alpha^p, \alpha^{p^2}, \cdots, \alpha^{p^{n-1}}
$$

这些共轭元素的乘积（被称为 $\alpha$ 的 Norm）恰好是一个 $\mathbb{F}_{p}$ 上的元素：

$$
\alpha \cdot \alpha^p \cdot \alpha^{p^2} \cdots \alpha^{p^{n-1}} = c
$$

为何？下面简单证明一下。

假设 $\alpha$ 的特征多项式为 $f(X)$ ，则

$$
f(X) = (X-\alpha)(X-\alpha^p)(X-\alpha^{p^2})\cdots(X-\alpha^{p^{n-1}})
$$

其中 $f(X)$ 的常数项系数恰好为 $c=\alpha \cdot \alpha^p \cdot \alpha^{p^2} \cdots \alpha^{p^{n-1}}$，又因为 $f(X)\in\mathbb{F}_{p}[X]$，所以 $c\in\mathbb{F}_{p}$。除此之外，Norm Map 也是一个常用的从 $\mathbb{F}_{p^n}$ 到 $\mathbb{F}_{p}$ 的同态映射。

那么我们可以利用 Norm Map 的性质来计算任意元素 $\theta\in\mathbb{F}_{p^n}$ 的乘法逆元 $\theta^{-1}$。

$$
\theta^{-1} = \theta^{-r} \cdot \theta^{r-1} 
$$

这里 $r$ 的计算如下：

$$
r = \frac{p^n-1}{p-1} = 1 + p + p^2 + \cdots + p^{n-1}
$$

那么根据定义， $\theta^{r}$ 恰好为 $\theta$ 的 Norm：

$$
\theta^{r} = \theta\cdot\theta^p\cdot\theta^{p^2}\cdots\theta^{p^{n-1}} = c
$$

为了计算 $\theta^{-1}$，我们还需要计算 $\theta^{r-1}$，但它为 $\mathbb{F}_{p^n}$ 中的元素。不过经过分析，我们可以采用下面的公式来「递推地」计算 $\theta^{-1}$：

$$
\begin{aligned}
\theta^{r-1} &= \prod_{i=1}^{n-1} \theta^{p^i} \\
        &= (((1\cdot \theta)^p \cdot \theta)^p \cdot \cdots \cdot \theta)^p
\end{aligned}
$$

写成 Python 代码如下：

```python
def frobenius_map(a: K):
    return a^(K.characteristic())

def frobenius_inv(a: F, degree: int):
    # compute a^{r-1}
    s = F(1)
    for i in range(1, degree):
        s = frobenius_map(s * a)
    t = s * a
    t_inv = t.inverse()

    return s * t_inv
```

可以看出，这个算法是一个通用的算法，这里并没有对 Extension Field 的结构或者不可约多项式有任何假设。

### 二项式扩张域 Frobenius Map 的优化

假如我们这里只考虑二项式扩张域，那么我们可以继续优化 Frobenius Map 的计算。

我们假设扩张域定义如下：

$$
\mathbb{F}_{p^n} = \mathbb{F}_{p}[X]/(X^n - e)
$$

这里 $e$ 为 $\mathbb{F}_{p}$ 上的元素。另外令 $\beta^n-e=0$ ，那么 $\beta$ 为 $\mathbb{F}_{p^n}$ 上的一个元素，并且满足：

$$
\beta^n = c
$$

对于任意一个元素 $\alpha$ ，都可以表示为 $\beta$ 的幂次 Basis 的系数向量：

$$
\alpha = a_0 + a_1\beta + a_2 \beta^2 + \cdots + a_{n-1} \beta^{n-1}
$$

那么 $\alpha$ 的 Frobenius Map 为 $\alpha^p$，可以推导如下：


$$
\begin{aligned}
\alpha^p &= (a_0 + a_1\beta + a_2 \beta^2 + \cdots + a_{n-1} \beta^{n-1})^p \\
    &= a_0^p + a_1^p\beta^p + a_2^p\beta^{2p} + \cdots +  a_{n-1}^p\beta^{p(n-1)} \\
    &= a_0 + a_1\beta^p + a_2\beta^{2p} + \cdots +  a_{n-1}\beta^{p(n-1)} \\
    &= a_0 + a_1\cdot (\beta^{p-1})\cdot \beta  + a_2\cdot (\beta^{p-1})^{2}\cdot \beta^2 + \cdots +  a_{n-1}\cdot (\beta^{p-1})^{(n-1)} \cdot \beta^{n-1}
\end{aligned}
$$

那么 $\alpha^p$ 可以表示为下面向量和 $(1,\beta,\beta^2,\cdots,\beta^{n-1})$ 的点积：

$$
(a_0, a_1\cdot (\beta^{p-1}), a_2\cdot (\beta^{p-1})^{2}, \cdots, a_{n-1}\cdot (\beta^{p-1})^{(n-1)})
$$

令 $z = \beta^{p-1}$，并且如果 $n\mid (p-1)$ ，那么 $z\in\mathbb{F}_{p}$，那么它的计算只涉及 Base Field 上的计算。

$$
z = \beta^{p-1} = c^{\frac{p-1}{n}}
$$

于是，$\alpha^p$ 的系数表示如下：

$$
(a_0, a_1\cdot z, a_2\cdot z^2, \cdots, a_{n-1}\cdot z^{n-1})
$$

