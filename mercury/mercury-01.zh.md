# Mercury 笔记：实现常数证明尺寸

- Jade Xie  <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

Mercury [EG25] 是一个基于 KZG10 的多元线性多项式承诺方案，即 Prover 向 Verifier 证明一个 $n$ 元线性多项式 $\tilde{f}(X_0,X_1,\ldots,X_{n-1})$ 在某一个公开点 $\vec{u} = (u_0,u_1,\ldots,u_{n-1})$ 处的取值为 $v$ 。设 $N = 2^n$ ，那么 $\tilde{f}$ 的大小就为 $N$ 。对比同样基于 KZG10 的 ph23 [PH23]、zeromorph [BCHO23]、gemini [KT23]方案，mercury 能在不牺牲 Prover 线性 $O(N)$ 的有限域运算的情况下，达到常数的证明尺寸，而非对数级别的 $O(\log N)$。同期的研究工作 SamaritanPCS [GPS25] 也达到了这样的性能。这两个协议在思想上有类似的地方，它们都在基于 pairing 的多元线性多项式承诺方案的研究中取得了显著的突破。本系列文章将详细介绍 mercury 是如何做到这一点的。

mercury 能做到常数证明尺寸的核心在于其洞见了一元多项式分解与多元线性多项式求值之间的关系，能将一个一元多项式在一个随机点处的求值转换为一个多元线性多项式在一个点处的求值，该求值可以转换为常数证明尺寸的内积证明，而一元多项式的分解证明也只需要常数的证明尺寸。

mercury 协议的整体思路与 Hyrax [WTSTW16] 协议有一些类似，先将 $\tilde{f}$ 在 boolean hypercube $\mathbf{B} = \{0,1\}^n$ 上的 $N$ 个值排成一个 $\sqrt{N} \times \sqrt{N}$ 的矩阵，先将这个矩阵一次按列「拍扁」。设 $b = \sqrt{N}, t = \log b$ ，「拍扁」的动作相当于先代入 $\vec{u}$ 中前半部分值求和，即先计算 $\tilde{h}(X_t, \ldots, X_{n - 1}):=\tilde{f}(u_0, \ldots, u_{t - 1}, X_t, \ldots, X_{n - 1})$ ，接着再计算 $\tilde{h}(u_t, \ldots, u_{n - 1}) = \tilde{f}(u_0, \ldots, u_{t - 1}, u_t, \ldots, u_{n - 1})$ ，证明其等于 $v$ 。这样分成两部分求和有一个好处，可以将计算的规模从原来的 $N$ 长变为 $\sqrt{N}$ 长，Prover 有一些计算复杂度原来是 $N \log N$ ，现在计算的规模变小后，计算复杂度最多达到 $\sqrt{N} \log \sqrt{N} = O(N)$ ，这也是 mercury 能保持 Prover 线性 $O(N)$ 复杂度的一个重要原因。

## 多元线性多项式的表示

对于一个多元线性多项式 $\tilde{f}(X_0, X_1,\ldots, X_{n-1})$ ，用其在 boolean hypercube $\mathbf{B}_n = \{0,1\}^n$ 的取值进行表示，

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) = \sum_{i=0}^{2^n - 1} f_i \cdot \tilde{eq}(\mathsf{bits}(i),(X_0, X_1, \ldots, X_{n-1}))
$$
其中 $\mathsf{bits}(i) = (i_0, i_1, \ldots, i_{n-1})$ 是 $i$ 的二进制表示，$i_0$ 表示最低位，满足 $i = \sum_{j = 0}^{n - 1}i_j \cdot 2^j$ 。$\tilde{eq}(\mathsf{bits}(i),(X_0, X_1, \ldots, X_{n-1}))$ 可以看作是在 $\mathbf{B} = \{0,1\}^n$ 上的 Lagrange 插值函数，其具体表达式为

$$
\tilde{eq}(\mathsf{bits}(i),(X_0, X_1, \ldots, X_{n-1})) = \prod_{j = 0}^{n-1} ((1- i_j)(1- X_j) + i_j \cdot X_j)
$$

当 $(X_0, X_1, \ldots, X_{n-1}) \in \mathbf{B}_n$ 时，若 $\mathsf{bits}(i) = (X_0, X_1, \ldots, X_{n-1})$ ，那么这两个向量的各个分量都是相等的，因此 $(1- i_j)(1- X_j) + i_j \cdot X_j = 1$ ，最后 $\tilde{eq}$ 函数的计算结果也为 $1$ 。当 $\mathsf{bits}(i) \neq (X_0, X_1, \ldots, X_{n-1})$ 时，$\tilde{eq}$ 函数的计算结果为 $0$ 。

由于 $\tilde{eq}$ 函数实际上是 $n$ 项连乘，乘积具有结合律，因此是可以对 $\tilde{eq}$ 函数进行分解。设 $n = 2 \cdot t, b = 2^t = \sqrt{N}$ 。将向量 $\mathsf{bits}(i)$ 分成等长的两部分，$\mathsf{bits}(i) = ((i_0,\ldots,i_{t-1}), (i_t,\ldots,i_{n-1}))$ ，同样将  $(X_0, X_1, \ldots, X_{n-1})$ 也分成两部分，$(X_0, X_1, \ldots, X_{n-1}) = ((X_0, \ldots, X_{t-1}), (X_t, \ldots, X_{n-1})) := (\vec{X}_1, \vec{X}_2)$ ，那么

$$
\begin{align}
\tilde{eq}(\mathsf{bits}(i),(X_0, X_1, \ldots, X_{n-1})) & = \prod_{j = 0}^{n-1} ((1- i_j)(1- X_j) + i_j \cdot X_j) \\
 & = \left(\prod_{j = 0}^{t-1} ((1- i_j)(1- X_j) + i_j \cdot X_j) \right)  \cdot \left(\prod_{j = t}^{n-1} ((1- i_j)(1- X_j) + i_j \cdot X_j) \right)  \\
 & = \tilde{eq}((i_0,\ldots,i_{t-1}),\vec{X}_1) \cdot \tilde{eq}((i_t,\ldots,i_{n-1}),\vec{X}_2)
\end{align}
$$

正因为 $\tilde{eq}$ 函数具有这样的拆分性质，因此我们可以更加方便的将 $\tilde{f}$ 的求值也进行拆分。

## 拆分

现在要证明 $\tilde{f}$ 在点 $\vec{u} = (u_0, u_1, \ldots, u_{n-1})$ 处的值为 $v$ ，即证明

$$
\tilde{f}(u_0,u_1,\ldots, u_{n-1}) = \sum_{i=0}^{2^n - 1} f_i \cdot \tilde{eq}(\mathsf{bits}(i),(u_0, u_1, \ldots, u_{n-1})) = v \tag{1}
$$

这里涉及到 $N$ 个项的求和，将其分为两个部分进行计算证明。

将变量 $\vec{u} = (\vec{u}_1, \vec{u}_2)$ 拆分成两个等长的向量，$\vec{u}_1 = (u_0,\ldots,u_{t-1}), \vec{u_2} = (u_t,\ldots,u_{n - 1})$ 。另外将 $\tilde{f}$ 在 $\mathbf{B}_n$ 上的取值 $(f_0,f_1, \ldots, f_{2^n - 1})$ 划分成 $b$ 组，用两个下脚标进行表示 

$$
(f_0,f_1, \ldots, f_{2^n - 1}) = (f_{0,0}, f_{0,1}, \ldots, f_{0,b-1}, \ldots, f_{b-1,0}, \ldots, f_{b-1,b-1})
$$

用矩阵排列下表示为

$$
M_f = \begin{bmatrix}
 f_{0,0} &  f_{0,1}   & \cdots  & f_{0,b-1} \\
 f_{1,0} &  f_{1,1}   & \cdots  & f_{1,b-1} \\
 \vdots &  \vdots   & \  & \vdots  \\
f_{b-1,0} &  f_{b-1,1}   & \cdots  & f_{b-1,b-1}
\end{bmatrix}
$$

那么根据前面介绍的 $\tilde{eq}$ 函数可以进行分解，可以得到

$$
\begin{align}
\tilde{f}(\vec{u}_1, \vec{u}_2)  & = \sum_{i=0}^{2^n - 1} f_i \cdot \tilde{eq}(\mathsf{bits}(i),(\vec{u}_1, \vec{u}_2)) \\
 & = \sum_{i=0}^{2^t - 1} \sum_{j=0}^{2^t - 1} f_{i,j} \cdot \tilde{eq}((\mathsf{bits}(j),\mathsf{bits}(i)),(\vec{u}_1, \vec{u}_2))\\
 & = \sum_{i=0}^{2^t - 1} \sum_{j=0}^{2^t - 1} f_{i,j} \cdot \tilde{eq}(\mathsf{bits}(j),\vec{u}_1) \cdot \tilde{eq}(\mathsf{bits}(i),\vec{u}_2)  \\
 & = \sum_{i=0}^{2^t - 1} \left(\tilde{eq}(\mathsf{bits}(i),\vec{u}_2)  \cdot\left(\sum_{j=0}^{2^t - 1} f_{i,j} \cdot \tilde{eq}(\mathsf{bits}(j),\vec{u}_1) \right) \right)
\end{align}
$$

上面的形式用矩阵表示更为直观，

$$
\begin{align}
& \tilde{f}(\vec{u}_1, \vec{u}_2)  \\
& =\begin{bmatrix}
\tilde{eq}(\mathsf{bits}(0), \vec{u}_2)  & \tilde{eq}(\mathsf{bits}(1), \vec{u}_2)  & \cdots  & \tilde{eq}(\mathsf{bits}(b-1), \vec{u}_2) 
\end{bmatrix}
\begin{bmatrix}
 f_{0,0} &  f_{0,1}   & \cdots  & f_{0,b-1} \\
 f_{1,0} &  f_{1,1}   & \cdots  & f_{1,b-1} \\
 \vdots &  \vdots   & \  & \vdots  \\
f_{b-1,0} &  f_{b-1,1}   & \cdots  & f_{b-1,b-1}
\end{bmatrix} 
\begin{bmatrix}
\tilde{eq}(\mathsf{bits}(0), \vec{u}_1)   \\
 \tilde{eq}(\mathsf{bits}(1), \vec{u}_1)   \\
\cdots   \\
\tilde{eq}(\mathsf{bits}(b-1), \vec{u}_1) 
\end{bmatrix} \\
& \stackrel{\triangle}{=}  \vec{v}_2^{\intercal} \cdot (M_f \cdot \vec{v}_1)
\end{align}
$$

以 $n = 2$ 为例，分解过程如下图所示：

![](./img/mercury-decomposing.svg)

要证明 $\tilde{f}(\vec{u}_1, \vec{u}_2)  = v$ ，可以分成两部分：

1. 证明 $M_f \cdot \vec{v}_1 = \vec{b}$ ，对应于先计算一个多元线性多项式 $\tilde{h}(\vec{X}_2) := \tilde{f}(\vec{u}_1, \vec{X}_2)$ 
2. 证明 $\vec{v}_2^{\intercal} \cdot \vec{b} = v$ ，对应于计算 $\tilde{h}(\vec{u}_2) = \tilde{f}(\vec{u}_1, \vec{u_2})$ ，证明其结果为 $v$ 。

至此我们已经将 $(1)$ 中 $N$ 项的求和转换成了两个计算步骤，先代入 $\vec{u}_1$ 进行部分求和，再代入 $\vec{u_2}$ 得到最终的求和结果 $v$ 。下面先引入多元线性多项式到一元多项式的转换，再借助于一元多项式的承诺方案 KZG10 来进行证明。

## 从多元线性多项式到一元多项式

对于多元线性多项式

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) = \sum_{i=0}^{2^n - 1} f_i \cdot \tilde{eq}(\mathsf{bits}(i),(X_0, X_1, \ldots, X_{n-1}))
$$
将其在 boolean hypercube $\mathbf{B}_n$ 上的取值 $f_i$ 直接作为一元多项式的系数，得到其对应的一元多项式为

$$
f(X) = \sum_{i = 0}^{2^n - 1} f_i \cdot X^i
$$

对于任意的一个多元线性多项式，都按照这种方式对应到一元多项式，即将多元线性多项式在 boolean hypercube 上的取值直接作为一元多项式的系数。

依然以 $n = 2$ 为例，多元线性多项式到一元多项式的转换，可以理解为只是变换了不同的基，多元线性多项式的基为 Lagrange 基，$(\tilde{eq}(\mathsf{bits}(0), \vec{X}), \tilde{eq}(\mathsf{bits}(1), \vec{X}), \tilde{eq}(\mathsf{bits}(2), \vec{X}), \tilde{eq}(\mathsf{bits}(3), \vec{X}))$ ，而一元多项式的基为 $(1, X, X^2, X^3)$ 。

![](./img/mercury-multi-to-univariate.svg)

对于前面提到的 $\tilde{h}(\vec{X}_2) = \tilde{f}(\vec{u}_1, \vec{X}_2)$ ，其用矩阵表示为

$$
\begin{align}
& \tilde{h}(\vec{X}_2) = \tilde{f}(\vec{u}_1, \vec{X}_2)  \\
& =\begin{bmatrix}
\tilde{eq}(\mathsf{bits}(0), \vec{X}_2)  & \tilde{eq}(\mathsf{bits}(1), \vec{X}_2)  & \cdots  & \tilde{eq}(\mathsf{bits}(b-1), \vec{X}_2) 
\end{bmatrix}
\begin{bmatrix}
 f_{0,0} &  f_{0,1}   & \cdots  & f_{0,b-1} \\
 f_{1,0} &  f_{1,1}   & \cdots  & f_{1,b-1} \\
 \vdots &  \vdots   & \  & \vdots  \\
f_{b-1,0} &  f_{b-1,1}   & \cdots  & f_{b-1,b-1}
\end{bmatrix} 
\begin{bmatrix}
\tilde{eq}(\mathsf{bits}(0), \vec{u}_1)   \\
 \tilde{eq}(\mathsf{bits}(1), \vec{u}_1)   \\
\cdots   \\
\tilde{eq}(\mathsf{bits}(b-1), \vec{u}_1) 
\end{bmatrix} \\
& = \begin{bmatrix}
\tilde{eq}(\mathsf{bits}(0), \vec{X}_2)  & \tilde{eq}(\mathsf{bits}(1), \vec{X}_2)  & \cdots  & \tilde{eq}(\mathsf{bits}(b-1), \vec{X}_2) 
\end{bmatrix}
\begin{bmatrix}
 f_{0,0} \cdot \tilde{eq}(\mathsf{bits}(0), \vec{u}_1) + f_{0,1} \cdot \tilde{eq}(\mathsf{bits}(1), \vec{u}_1) + \ldots +  f_{0,b-1} \cdot \tilde{eq}(\mathsf{bits}(b-1), \vec{u}_1)\\
 f_{1,0} \cdot \tilde{eq}(\mathsf{bits}(0), \vec{u}_1) + f_{1,1} \cdot \tilde{eq}(\mathsf{bits}(1), \vec{u}_1) + \ldots +  f_{1,b-1} \cdot \tilde{eq}(\mathsf{bits}(b-1), \vec{u}_1) \\
 \vdots   \\
f_{b-1,0} \cdot \tilde{eq}(\mathsf{bits}(0), \vec{u}_1) + f_{b-1,1} \cdot \tilde{eq}(\mathsf{bits}(1), \vec{u}_1) + \ldots +  f_{b-1,b-1} \cdot \tilde{eq}(\mathsf{bits}(b-1), \vec{u}_1)
\end{bmatrix}  
\end{align}
$$

可以发现右边列向量的每一项其实就是 $\tilde{h}(\vec{X}_2)$ 在 boolean hypercube $\mathbf{B}_t = \{0,1\}^t$ 上的取值，对应到一元多项式 $h(X)$ ，右边列向量的第 $i$ 行就是 $h(X)$ 中 $X^i$ 项前面的系数。

$$
h(X) = \sum_{i = 0}^{b - 1} \left(\left( \sum_{j = 0}^{b - 1} f_{i,j} \cdot \tilde{eq}(\mathsf{bits}(j), \vec{u}_1)\right) \cdot X^i \right)
$$
可以发现 $h(X)$ 中每一项的系数 $\sum_{j = 0}^{b - 1} f_{i,j} \cdot \tilde{eq}(\mathsf{bits}(j), \vec{u}_1)$ 也是一个数乘以 $\tilde{eq}$ 的形式，其实我们还可以将 $f_{i,j}$ 作为一元多项式的系数，将 $M_f$ 矩阵的每一列作为一个一元多项式对应的系数，表示为

$$
\begin{align}
 & f_0(X) = f_{0,0} + f_{1,0}  X + \ldots + f_{b-1, 0} X^{b-1} \\
 & f_1(X) = f_{0,1} + f_{1,1}  X + \ldots + f_{b-1, 1} X^{b-1} \\
 & \qquad \qquad \qquad \qquad \ldots \\
 & f_{b-1}(X) = f_{0,b-1} + f_{1,b-1}  X + \ldots + f_{b-1, b-1} X^{b-1}
\end{align}
$$

将 $M_f$ 的每一列作为一元多项式的系数的好处是，$M_f$ 矩阵的第 $i$ 行的元素对应的正好是 $X^i$ 的系数，例如矩阵 $M_f$ 的第 $1$ 行，其元素为 $(f_{1,0}, f_{1,1}, \ldots, f_{1,b-1})$ ，其分别是 $f_0(X), f_1(X), \ldots, f_{b-1}(X)$ 中 $X^1$ 前面的系数。

$f_i(X)$ 其实也可以看作是对 $f(X)$ 的一个分解，

$$
\begin{align}
f(X)  & = \sum_{i = 0}^{2^n - 1} f_i \cdot X^i = \sum_{i = 0}^{b - 1} \sum_{j = 0}^{b - 1} f_{i,j} \cdot X^{i \cdot b + j} \\
 & = \sum_{i = 0}^{b - 1} \sum_{j = 0}^{b - 1} f_{i,j} \cdot (X^{b})^i \cdot X^{j}  \\
& = \sum_{j = 0}^{b - 1} \sum_{i = 0}^{b - 1} f_{i,j} \cdot (X^{b})^i \cdot X^{j} \\
& = \sum_{j = 0}^{b - 1} f_j(X^b) \cdot X^j \\
& = \sum_{i = 0}^{b - 1} f_i(X^b) \cdot X^i
\end{align}
$$
即将 $f(X)$ 分解成 $b$ 个多项式求和，

$$
f(X) = f_0(X^b) + X \cdot f_1(X^b) + \ldots + X^{b-1} \cdot f_{b-1}(X^b) \tag{2}
$$

其实这里对一元多项式的分解与上一小节讲到的对多元多项式求值 $\tilde{f}(\vec{u}_1,\vec{u}_2)$ 的分解是一致的，多元线性多项式利用了 $\tilde{eq}$ 函数的可拆分性，一元多项式中对 $X^i$ 也可以进行拆分分解。以 $n = 2$ 为例，对两者进行对比，如下图所示。

![](./img/mercury-decomposing-univariate.svg)

此时 $h(X)$ 就可以表示为

$$
\begin{align}
h(X)  & = \sum_{i = 0}^{b - 1} \left(\left( \sum_{j = 0}^{b - 1} f_{i,j} \cdot \tilde{eq}(\mathsf{bits}(j), \vec{u}_1)\right) \cdot X^i \right) \\
 & = \sum_{j = 0}^{b - 1} \left(\left( \sum_{i = 0}^{b - 1} f_{i,j} \cdot X^i \right) \cdot \tilde{eq}(\mathsf{bits}(j), \vec{u}_1) \right) \\
 & = \sum_{j = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(j), \vec{u}_1) \cdot f_j(X) \\
& = \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(X)
\end{align}
$$

以 $n = 2$ 为例，下图表示了 $h(X)$ 的分解过程。

![](./img/mercury-h.svg)


那么 $h(X)= \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(X)$ 对应的多元线性多项式就是 $\tilde{h}(\vec{X}) = \tilde{f}(\vec{u}_1, \vec{X})$ 。这就相当于一次性替换了 $\tilde{f}$ 中的前 $t$ 个变量。那么我们承诺与 $\tilde{f}(\vec{u}_1, \vec{X})$ 对应的一元多项式 $\mathsf{cm}(h(X))$ ，再证明 $\tilde{h}(\vec{u}_2) = v$ 就完成了证明。也就是对应前一小节所说的证明分为两个部分：

1. 证明 $M_f \cdot \vec{v}_1 = \vec{b}$ ，对应于先计算一个多元线性多项式 $\tilde{h}(\vec{X}_2) := \tilde{f}(\vec{u}_1, \vec{X}_2)$ 
2. 证明 $\vec{v}_2^{\intercal} \cdot \vec{b} = v$ ，对应于计算 $\tilde{h}(\vec{u}_2) = \tilde{f}(\vec{u}_1, \vec{u_2})$ ，证明其结果为 $v$ 。

第 2 部分其实是证明两个向量的内积，可以转换为内积的证明。

这样就完成证明了吗？那么怎么实现常数大小的 proof size 呢？这里面其实有一个关键的地方需要证明，那就是 Verifier 要去相信 $h(X)$ 的构造是正确的，也就是

$$
h(X)= \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(X) \tag{3}
$$

Prover 需要向 Verifier 证明其确实是按照这种方式构造的，而不是任意发送的一个多项式。要证明 $(3)$ 式构造正确，那么 Verifier 可以随机发起一个挑战值 $r$ ，Prover 要证明

$$
h(r^b)= \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(r^b) \tag{4}
$$

$f_i(r^b)$ 是和 $f$ 的值相关的，根据 $f(X)$ 的分解式 $(2)$ 

$$
f(X) = f_0(X^b) + X \cdot f_1(X^b) + \ldots + X^{b-1} \cdot f_{b-1}(X^b) ,
$$

令 $\omega^b = 1$ ，可知

$$
\begin{align}
 & f(r) = f_0(r^b) + r \cdot f_1(r^b) + \ldots + r^{b-1} \cdot f_{b-1}(r^b) \\
 & f(\omega r) = f_0(r^b) + \omega r \cdot f_1(r^b) + \ldots + (\omega r)^{b-1} \cdot f_{b-1}(r^b)  \\
 & \ldots \\
 & f(\omega^{b-1} r) = f_0(r^b) + \omega^{b-1} r \cdot f_1(r^b) + \ldots + (\omega^{b-1} r)^{b-1} \cdot f_{b-1}(r^b)
\end{align}
$$

上面相当于是一个有 $b$ 个未知数 $f_i(r^b)$ ，以及有 $b$ 个方程的线性方程组，求解该线性方程组，就可以用 $\{f(r), f(\omega r), \ldots, f(\omega^{b - 1} r) \}$ 这些值计算得到 $f_i(r^b)$ 的值。Prover 可以发送 $h(r^b)$ 以及 $\{f(r), f(\omega r), \ldots, f(\omega^{b - 1} r) \}$ 这些值及对应的打开证明，让 Verifier 自己计算出 $f_i(r^b)$ 的值，进而验证 $(4)$ 式是否成立。这种方案的问题是发送的证明大小肯定是 $O(b)$ 级别的，而不是常数。

有没有什么方法既可以实现常数大小的证明，又能证明 $(4)$ 式的正确性呢？mercury 巧妙的将证明 $(4)$ 式中一个在一元多项式的取值 $h(r^b)$ 转换为了证明在一个多元线性多项式处的取值。

## 实现常数证明尺寸

Prover 的目标是用常数证明尺寸来证明

$$
h(r^b)= \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(r^b) \tag{4}
$$
不妨设 $\alpha = r^b$ 。

令 $g(X)  = f(X) \mod{X^b - \alpha}$ ，记商多项式为 $q(X)$ ，那么有

$$
f(X) = q(X) \cdot (X^b - \alpha) + g(X) \tag{5}
$$
在上式中代入 $X^b = \alpha$ 的条件，可以得到

$$
g(X) = f(X) = \sum_{i = 0}^{b - 1} f_i(X^b) \cdot X^i = \sum_{i = 0}^{b - 1} f_i(\alpha) \cdot X^i
$$

可以看到 $g(X)$ 的系数为 $f_i(\alpha)$ ，与 $g(X)$ 对应的多元线性多项式就应该为

$$
\tilde{g}(X_0, \ldots , X_{b-1}) = \sum_{i = 0}^{b - 1} f_i(\alpha) \cdot \tilde{eq}(\mathsf{bits}(i), (X_0, \ldots , X_{b-1}))
$$

那么 $(4)$ 式也就转换为

$$
h(\alpha)= \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(\alpha) = \tilde{g}(\vec{u}_1) 
$$
此时要证明 $(4)$ 式正确，就转换成了证明

$$
h(\alpha) = \tilde{g}(\vec{u}_1) \tag{6}
$$

以 $n = 2$ 为例，转换证明的过程如下图所示。

![](./img/mercury-h-alpha.svg)

这样就将在一个一元多项式 $h(\alpha)$ 处的值转换为了在一个多元线性多项式在某一个点处的值 $\tilde{g}(\vec{u}_1)$ 。这时我们就需要再证明与 $\tilde{g}$ 对应的 $g(X)$ 的构造是正确的，也就是 $(5)$ 式成立，Prover 可以承诺 $q(X)$ 和 $g(X)$ ，Verifier 再选取一个随机点 $\zeta$ ，来验证 $(5)$ 式成立，这只需要常数的证明大小，这就是 mercury 协议能实现常数证明大小的核心。

另外，为了防止 Prover 作弊，我们还需要限制 $\deg(g) < b$ 。

至此，就将上一小节提到的两个证明：

1. 证明 $M_f \cdot \vec{v}_1 = \vec{b}$ ，对应于先计算一个多元线性多项式 $\tilde{h}(\vec{X}_2) := \tilde{f}(\vec{u}_1, \vec{X}_2)$ 
2. 证明 $\vec{v}_2^{\intercal} \cdot \vec{b} = v$ ，对应于计算 $\tilde{h}(\vec{u}_2) = \tilde{f}(\vec{u}_1, \vec{u_2})$ ，证明其结果为 $v$ 。

转换为下面四个证明：

1. $f(X) = q(X) \cdot (X^b - \alpha) + g(X)$ 
2. $\deg(g) < b$
3. $\tilde{g}(\vec{u}_1) = h(\alpha)$
4. $\tilde{h}(\vec{u}_2) = v$

第一项的证明，Prover 可以先发送 $q(X)$ 和 $g(X)$ 的承诺，Verifier 发送一个随机点 $\zeta$ ，让 Prover 在该随机点打开，发送 $q(\zeta), g(\zeta)$ ，Prover 只要证明商多项式

$$
\frac{f(X) - q(\zeta) \cdot (\zeta^b - \alpha) + g(\zeta)}{X - \zeta}
$$
存在，就证明了第 $1$ 项中的式子是成立的，这一项的证明只需要常数的证明大小。

对于第二项，是 degree bound 的证明，也可以由常数的证明大小实现。

对于第三项和第四项，都是证明有 $b$ 个变量的多元线性多项式在某个点的打开值，这可以转换为内积证明，例如对于多元线性多项式 $\tilde{g}$ ，

$$
\begin{align}
\tilde{g}(\vec{u}_1)  & = \sum_{i = 0}^{b - 1} \tilde{eq}(\mathsf{bits}(i), \vec{u}_1) \cdot f_i(\alpha)  \\
\end{align}
$$

上面其实计算的是向量 $\vec{a}_1 = (\tilde{eq}(\mathsf{bits}(0),\vec{u}_1),\ldots, \tilde{eq}(\mathsf{bits}(b-1), \vec{u}_1)$ 和 $\vec{b}_1 = (f_0(\alpha),\ldots, f_{b-1}(\alpha))$ 的内积。对于 $\tilde{h}(\vec{u}_2)$ 也是类似的，这样第三项和第四项就能转换为两个内积证明，而这两个内积证明又能用随机数聚合成一个证明，也能达到常数的证明大小。

因此，mercury 的这四部分证明都是常数的证明大小，同时由于证明第三项和第四项的多元线性多项式的长度为 $b$ ，就算有些计算 Prover 需要 $O(b \log b)$ 的复杂度，这也是不超过 $O(N)$ 的复杂度，依然能够保持 Prover 线性的计算复杂度。

本文介绍了 mercury 能在保持 Prover 线性复杂度下实现常数证明尺寸的原因，在下一篇文章中将详细介绍 mercury 是如何证明这四项的。

## References
- [EG25] Eagen, Liam, and Ariel Gabizon. "MERCURY: A multilinear Polynomial Commitment Scheme with constant proof size and no prover FFTs." Cryptology ePrint Archive (2025). https://eprint.iacr.org/2025/385
- [GPS25] Ganesh, Chaya, Sikhar Patranabis, and Nitin Singh. "Samaritan: Linear-time Prover SNARK from New Multilinear Polynomial Commitments." _Cryptology ePrint Archive_ (2025). https://eprint.iacr.org/2025/419
- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/1284
- [BCHO23] Bootle, Jonathan, Alessandro Chiesa, Yuncong Hu, and Michele Orru. "Gemini: Elastic SNARKs for diverse environments." In _Annual International Conference on the Theory and Applications of Cryptographic Techniques_, pp. 427-457. Cham: Springer International Publishing, 2022. [https://eprint.iacr.org/2022/420](https://eprint.iacr.org/2022/420)
- [KT23] Kohrita, Tohru, and Patrick Towa. "Zeromorph: Zero-knowledge multilinear-evaluation proofs from homomorphic univariate commitments." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/917 
- [WTSTW16] Riad S. Wahby, Ioanna Tzialla, abhi shelat, Justin Thaler, and Michael Walfish. "Doubly-efficient zkSNARKs without trusted setup."  In 2018 IEEE Symposium on Security and Privacy (SP), pp. 926-943. IEEE, 2018.  https://eprint.iacr.org/2016/263 