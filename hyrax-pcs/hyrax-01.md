# Notes on Hyrax-PCS

This article briefly introduces the principles of Hyrax-PCS, whose security assumption is Discrete Log. Its main idea is to prove an Inner Product and adopts the recursive folding approach to gradually fold two vectors of length $n$ into two vectors of length $n/2$, reducing the inner product calculation to the inner product calculation of vectors with only half the length. The recursive folding idea mainly comes from [BCC+16] and [BBB+18], with the main problem being that the Verifier's computational complexity is $O(n)$. To make Hyrax meet the requirements of zkSNARK, Hyrax rearranges the vector into a $\sqrt{n}\times\sqrt{n}$ matrix, then reduces the inner product calculation to the inner product calculation of vectors with length $\sqrt{n}$. This results in the Verifier's computational complexity being optimized to $O(\sqrt{n})$. At the same time, after optimization by [BCC+16], Hyrax's Proof size (communication complexity) is also optimized to $O(\log{n})$.

## 1. Evaluation Proof of MLE Polynomials

Whether the MLE polynomial is in Coefficients form or Evaluation form, we can prove the evaluation of the polynomial at certain points through the "Inner Product Argument".

$$
f(X_0, X_1, ..., X_{n-1}) = \sum_{i=0}^{2^n-1} a_i \cdot \tilde{eq}(\mathsf{bits}(i), X_0, X_1, ..., X_{n-1})
$$

$$
f(X_0, X_1, ..., X_{n-1}) = \sum_{i=0}^{2^n-1} c_i \cdot X_0^{i_0} \cdot X_1^{i_1} \cdot ... \cdot X_{n-1}^{i_{n-1}},  \quad \text{where } \mathsf{bits}(i) = (i_0, i_1, ..., i_{n-1})
$$

If we have an inner product proof protocol, we can easily construct an evaluation proof for MLE polynomials.

### Public Input

1. Commitment of $\vec{a}$: $C_a=\mathsf{cm}(a_0, a_1, ..., a_{2^n-1})$
2. $\vec{u}=(u_0, u_1, ..., u_{n-1})$ 
3. $v=\tilde{f}(u_0, u_1, ..., u_{n-1})$

### Witness

1. $\vec{a}$

### Inner Product Protocol

Prover computes vector $\vec{e}$, length $2^n$,

$$
\begin{aligned}
e_0 &= \tilde{eq}(\mathsf{bits}(0), u_0, u_1, ..., u_{n-1}) \\
e_1 &= \tilde{eq}(\mathsf{bits}(1), u_0, u_1, ..., u_{n-1}) \\
\cdots \\
e_{2^n-1} &= \tilde{eq}(\mathsf{bits}(2^n-1), u_0, u_1, ..., u_{n-1}) \\
\end{aligned}
$$

Prover and Verifier use an Inner Product Argument protocol to prove that the inner product of $\vec{a}$ and $\vec{e}$ equals $v$. Below, we introduce a simple inner product proof that proves the inner product of two hidden vectors equals a public value.

## 2. Mini-IPA

Let's start with the simplest case. Suppose Prover has two vectors $\vec{a}$ and $\vec{b}$, satisfying $\langle \vec{a}, \vec{b} \rangle = c$ (note: $c$ is a *public value* here).

### Proof Goal

Prover has knowledge $(\vec{a},\vec{b})$ (two vectors of equal length, denoted as $m$, so there are $2m$ witnesses in total), and $\langle \vec{a}, \vec{b} \rangle = c$

### Public Parameters

To compute the Pedersen Commitment of vectors, we need to select a set of random group elements $g_1, g_2, g_3, \ldots, g_m, h \in \mathbb{G}$.

### Public Input

1. Inner product result $c$
2. Commitment of vector $\vec{a}$: $C_a=\mathsf{cm}(\vec{a};\rho_a)$,
3. Commitment of vector $\vec{b}$: $C_b=\mathsf{cm}(\vec{b};\rho_b)$

### Witnesses

1. $(\vec{a}, \rho_a)$ 
2. $(\vec{b}, \rho_b)$

### Basic Protocol Idea

Prover introduces two "blinder vectors", $\vec{r}$ and $\vec{s}$. These two vectors are flattened into one vector through a challenge number $\mu$ (from Verifier):

$$
\vec{a}' = \vec{r}+ \mu\cdot \vec{a}  \qquad \vec{b}' = \vec{s}+ \mu\cdot \vec{b}
$$

Then calculate the inner product (or dot product) of $\vec{a}'\cdot \vec{b}'$. 

$$
\langle \vec{a}', \vec{b}' \rangle = (\vec{r}+ \mu\cdot \vec{a})(\vec{s}+ \mu\cdot \vec{b}) =\mu^2(\langle \vec{a}, \vec{b} \rangle) + \mu(\langle \vec{a}, \vec{s} \rangle + \langle \vec{b}, \vec{r} \rangle) + \langle \vec{r}, \vec{s} \rangle
$$

Observing $\vec{a}'$ and $\vec{b}'$, we find that both vectors have $\mu$ terms. After flattening the vectors and performing the inner product operation, we get a **quadratic polynomial** in $\mu$, where the "coefficient" of the $\mu^2$ term is exactly the inner product of vectors $\vec{a}$ and $\vec{b}$ (should equal $c$), and the constant term $\vec{r}\cdot\vec{s}$ is exactly the inner product of the two "blinder vectors". However, the coefficient of $\mu$ looks somewhat *messy*. We can ignore the messy coefficient of $\mu$ for now and focus on the coefficient of the $\mu^2$ term. According to the Schwartz-Zippel theorem, as long as Prover can successfully respond to Verifier's challenge, the coefficients of all terms in the polynomial must be (with high probability) correct.

We let Prover not only commit to the "blinder vectors" in the first step of the protocol but also commit to the coefficients of the polynomial (in $\mu$) after expanding the inner product. Then in the third step, Prover only needs to send the two flattened vectors $\vec{a}'$ and $\vec{b}'$, which is just right. Verifier first verifies if $a'$ can open $A'$, then verifies if $b'$ can open $B'$, and finally Verifier verifies if $\vec{a}'\cdot\vec{b}'$ can open the commitment $C'$. Let's see how the protocol is specifically defined:

### Protocol

#### Round 1

Prover sends commitments $C_r$ and $C_s$ of two "blinder vectors" $\vec{r}$ and $\vec{s}$; also sends polynomial coefficient commitments $C_0$ and $C_1$:

$$
\begin{aligned}
C_r&=\mathsf{cm}(\vec{r};\rho_{r}) \\
C_s&=\mathsf{cm}(\vec{s} ;\rho_{s}) \\
C_0&=\mathsf{cm}(\langle \vec{r}, \vec{s} \rangle; \rho_0) \\
C_1&=\mathsf{cm}(\langle \vec{a}, \vec{s} \rangle + \langle \vec{b}, \vec{r} \rangle; \rho_1) \\
\end{aligned}
$$

#### Round 2

1. Verifier replies with a challenge number $\mu$

2. Prover sends two flattened vectors $\vec{a}'$, $\vec{b}'$, three random numbers mixed with $\mu$: $\rho'_a$, $\rho'_b$, $\rho'_{ab}$ 

$$
\begin{aligned}
\vec{a}'&=\vec{r} + \mu \cdot \vec{a}\\
\vec{b}'&=\vec{s} + \mu \cdot \vec{b}\\
\end{aligned}
$$

$$
\begin{aligned}
\rho'_a&=\rho_{r} + \mu \cdot \rho_a \\
\rho'_b&=\rho_{s} + \mu \cdot \rho_b \\
\rho'_{ab}&=\rho_0 + \mu \cdot \rho_1 \\
\end{aligned}
$$

#### Verification

Verifier homomorphically verifies in group $\mathbb{G}$: $\vec{a}'$ and $\vec{b}'$, and their inner product

$$
\begin{aligned}
\mathsf{cm}(\vec{a}'; \rho'_a)&\overset{?}{=} C_r + \mu\cdot C_a \\
\mathsf{cm}(\vec{b}'; \rho'_b)&\overset{?}{=} C_s + \mu \cdot C_b \\
\end{aligned}
$$

$$
\mathsf{cm}(\langle \vec{a}', \vec{b}' \rangle; \rho'_{ab})\overset{?}{=} \mu^2\cdot\mathsf{cm}(c;0) + \mu\cdot C_1 + C_0
$$

The biggest problem with this protocol is that Verifier's computational complexity is $O(n)$, because Verifier needs to compute $\langle \vec{a}', \vec{b}' \rangle$. Also, $\vec{b}$ is hidden information, but for the MLE Evaluation proof protocol, $\vec{e}$ (computed from $\vec{u}$) is a public value, so we need to adjust the protocol.

## 3. Square-root inner product argument

The Hyrax paper proposes a simple and direct approach to reduce Verifier's computational complexity to $O(\sqrt{n})$. A Sublinear Verifier is a basic requirement of zkSNARK. We still only consider the Coefficients form of $\tilde{f}$, i.e., $\vec{c}$ is the coefficient of $\tilde{f}$.

We assume $n=4$, so $\vec{a}$ has a length of 16, and we can arrange this vector into a matrix:

$$
\begin{bmatrix}
c_0 & c_1 & c_2 & c_3 \\
c_4 & c_5 & c_6 & c_7 \\
c_8 & c_9 & c_{10} & c_{11} \\
c_{12} & c_{13} & c_{14} & c_{15}
\end{bmatrix}
$$

The MLE polynomial represented by $\vec{a}$ can be expressed in the following form:

$$
\tilde{f}(X_0, X_1, X_2, X_3) = 
\begin{bmatrix}
1 & X_2 & X_3 & X_2X_3 \\
\end{bmatrix}
\begin{bmatrix}
c_0 & c_1 & c_2 & c_3 \\
c_4 & c_5 & c_6 & c_7 \\
c_8 & c_9 & c_{10} & c_{11} \\
c_{12} & c_{13} & c_{14} & c_{15}
\end{bmatrix}
\begin{bmatrix}
1 \\
X_0 \\
X_1 \\
X_0X_1 \\
\end{bmatrix}
$$

The result of this matrix calculation is as follows:

$$
\tilde{f}(X_0, X_1, X_2, X_3) = c_0 + c_1X_0 + c_2X_1 + c_3X_0X_1 + c_4X2 + \cdots + c_{14}X_1X_2X_3 + c_{15}X_0X_1X_2X_3
$$

We first split $\vec{u}$ into two short vectors:

$$
\vec{u} = (u_0, u_1, u_2, u_3) = (u_0, u_1) \parallel (u_2, u_3)
$$

Then $\tilde{f}(u_0, u_1, u_2, u_3)$ can be represented as:

$$
\tilde{f}(u_0, u_1, u_2, u_3) = \begin{bmatrix}
1 & u_2 & u_3 & u_2u_3 \\
\end{bmatrix}
\begin{bmatrix}
c_0 & c_1 & c_2 & c_3 \\
c_4 & c_5 & c_6 & c_7 \\
c_8 & c_9 & c_{10} & c_{11} \\
c_{12} & c_{13} & c_{14} & c_{15}
\end{bmatrix}
\begin{bmatrix}
1 \\
u_0 \\
u_1 \\
u_0u_1 \\
\end{bmatrix}
$$

Then, we calculate the commitments of the matrix composed of $\vec{c}$ by rows, obtaining $C_0, C_1, C_2, C_3$,

$$
\begin{aligned}
C_0 &= \mathsf{cm}(c_0, c_1, c_2, c_3; \rho_0) \\
C_1 &= \mathsf{cm}(c_4, c_5, c_6, c_7; \rho_1) \\
C_2 &= \mathsf{cm}(c_8, c_9, c_{10}, c_{11}; \rho_2) \\
C_3 &= \mathsf{cm}(c_{12}, c_{13}, c_{14}, c_{15}; \rho_3)
\end{aligned}
$$

Then we can use $(1, u_2, u_3, u_2u_3)$ and $(C_0, C_1, C_2, C_3)$ to perform an inner product operation, obtaining $C^*$:

$$
C^* = C_0 + u_2C_1 + u_3C_2 + u_2u_3C_3
$$

Then $C^*$ can be seen as the inner product of the column vector of matrix $M_c$ and $(1, u_2, u_3, u_2u_3)$, denoted as $\vec{d}=(d_0, d_1, d_2, d_3)$,

$$
\begin{split}
d_0 &= c_0 + c_4\cdot u_0 + c_8\cdot u_2 + c_{12}\cdot u_2u_0 \\
d_1 &= c_1 + c_5\cdot u_0 + c_9\cdot u_2 + c_{13}\cdot u_2u_0 \\
d_2 &= c_2 + c_6\cdot u_0 + c_{10}\cdot u_2 + c_{14}\cdot u_2u_0 \\
d_3 &= c_3 + c_7\cdot u_0 + c_{11}\cdot u_2 + c_{15}\cdot u_2u_0 \\
\end{split}
$$

It's easy to verify:

$$
C^* = \mathsf{cm}(d_0, d_1, d_2, d_3; \rho^*)
$$

Here $\rho^*=\rho_0 + \rho_1u_2 + \rho_2u_3 + \rho_3u_2u_3$.

Using this approach, we construct a simple MLE polynomial commitment scheme.

### Public Input

1. Commitment of $\vec{a}$: $C_a=\mathsf{cm}(a_0, a_1, ..., a_{2^n-1})$
2. $\vec{u}=(u_0, u_1, ..., u_{n-1})$ 
3. $v=\tilde{f}(u_0, u_1, ..., u_{n-1})$

### Witness

1. $\vec{a}$

### Commitment

1. Prover rearranges $\vec{a}$ into a matrix $M_a\in\mathbb{F}_p^{l\times h}$:

$$
M_a =
\begin{bmatrix}
a_0 & a_1 & a_2 & \cdots & a_{l-1} \\
a_l & a_{l+1} & a_{l+2} & \cdots & a_{2l-1} \\
a_{2l} & a_{2l+1} & a_{2l+2} & \cdots & a_{3l-1} \\
a_{(h-1)l} & a_{(h-1)l+1} & a_{(h-1)l+2} & \cdots & a_{hl-1} \\
\end{bmatrix}
$$

2. Prover calculates commitments $C_0, C_1, ..., C_{h-1}$ by row

$$
\begin{aligned}
C_0 &= \mathsf{cm}(a_0, a_1, ..., a_{l-1}; \rho_0) \\
C_1 &= \mathsf{cm}(a_l, a_{l+1}, ..., a_{2l-1}; \rho_1) \\
C_2 &= \mathsf{cm}(a_{2l}, a_{2l+1}, ..., a_{3l-1}; \rho_2) \\
\cdots\ &=\quad \cdots \\
C_{h-1} &= \mathsf{cm}(a_{(h-1)l}, a_{(h-1)l+1}, ..., a_{hl-1}; \rho_{h-1}) \\
\end{aligned}
$$

### Evaluation Proof Protocol

1. Prover and Verifier split $\vec{u}$ into two short vectors, represented by $\vec{u}_L$ and $\vec{u}_R$ respectively:

$$
\begin{aligned}
\vec{u}_L &= (u_0, u_1, ..., u_{\log(l)-1}) \\
\vec{u}_R &= (u_{\log(l)}, u_{\log(l)+1}, ..., u_{n-1}) \\
\end{aligned}
$$

Obviously

$$
\vec{u} = \vec{u}_L \parallel \vec{u}_R
$$

#### Round 1

1. Prover calculates $\vec{e}=(e_0, e_1, ..., e_{h-1})$, length $h$:

$$
\begin{split}
e_0 &= \tilde{eq}(\mathsf{bits}(0), \vec{u}_R) \\
e_1 &= \tilde{eq}(\mathsf{bits}(1), \vec{u}_R) \\
\cdots\ &=\quad \cdots \\
e_{h-1} &= \tilde{eq}(\mathsf{bits}(h-1), \vec{u}_R) \\
\end{split}
$$

2. Prover calculates the matrix multiplication of $\vec{e}$ and $M_a$, obtaining a new vector $\vec{b}$, length $l$

$$
\begin{split}
b_0 &= \langle \vec{e}, (a_0, a_l, ..., a_{(h-1)l}) \rangle \\
b_1 &= \langle \vec{e}, (a_1, a_{l+1}, ..., a_{(h-1)l+1}) \rangle \\
\cdots\ &=\quad \cdots \\
b_{l-1} &= \langle \vec{e}, (a_{l-1}, a_{l+l-1}, ..., a_{(h-1)l+l-1}) \rangle \\
\end{split}
$$

2. Prover calculates the commitment $C^*$ of $\vec{b}$

$$
C^* = \mathsf{cm}(\vec{b}; \rho^*)
$$

#### Round 2. 

Prover and Verifier conduct an Inner Product Argument protocol to complete the inner product proof of $\vec{b}$ and $\vec{d}$.

$$
\begin{split}
d_0 &= \tilde{eq}(\mathsf{bits}(0), \vec{u}_L) \\
d_1 &= \tilde{eq}(\mathsf{bits}(1), \vec{u}_L) \\
\cdots\ &=\quad \cdots \\
d_{h-1} &= \tilde{eq}(\mathsf{bits}(h-1), \vec{u}_L) \\
\end{split}
$$

1. Prover first samples a random number vector $\vec{r}$, used to protect the information of $\vec{b}$, then calculates its commitment:

$$
C_{r} = \mathsf{cm}(\vec{r}; \rho_{r})
$$

2. Prover calculates the inner product of $\vec{r}$ and $\vec{b}$, obtaining $v$

$$
s = \vec{r}\cdot\vec{d}
$$


$$
C_0 = \mathsf{cm}(s; \rho_s)
$$

$$
C_1 = \mathsf{cm}(0; \rho_t)
$$

#### Round 3.

1. Verifier sends a random number $\mu$

2. Prover calculates and sends the following values:

$$
\vec{z_b} = \vec{r} + \mu\cdot\vec{b}
$$

$$
z_\rho = \rho_r + \mu\cdot\rho^*
$$

$$
z_t = \rho_s + \mu^{-1}\cdot\rho_t
$$

#### Verification

Verifier verifies:

$$
C_r + \mu\cdot{}C^*\overset{?}{=} \mathsf{cm}(\vec{z_b}; z_\rho)
$$

$$
C_0 + \mu^{-1}\cdot{}C_1 + \mu\cdot\mathsf{cm}(v; 0)\overset{?}{=} \mathsf{cm}(\langle\vec{z}_b, \vec{d}\rangle; z_t)
$$

## 4. Bulletproofs Optimization

In the Round-2 of the "inner product proof" protocol (Mini-IPA) mentioned above, since Prover needs to send a vector of length $l$ ($\vec{z}_b$), the overall communication of the protocol is $O(l)$. If the vector is quite long, the final proof size will be relatively large. J. Bootle et al. proposed a very interesting idea in the [BCC+16] paper, using a recursive method to gradually fold the proof, achieving **compression of the proof size**.

Suppose we have a vector $\vec{a} = (a_1, a_2, a_3, a_4)$ of length 4, we can split it in half into two vectors $\vec{a}_1 = (a_1, a_2)$ and $\vec{a}_2 = (a_3, a_4)$, then stack them vertically to form a matrix:

$$
\begin{bmatrix}
a_1 & a_2\\
a_3 & a_4 \\
\end{bmatrix}
$$

Then we perform a "flattening" operation on this $2\times 2$ matrix (with the help of a random number vector):

$$
(x, x^{-1})
\left[
\begin{array}{ll}
a_1 &a_2\\
a_3 &a_4
\end{array}
\right]
= (a_1x + a_3x^{-1},\quad a_2x + a_4x^{-1})
= \vec{a}'
$$

As shown in the above formula, we left multiply the matrix by a random number vector $(x, x^{-1})$, then obtain a vector $\vec{a}'$ of length 2. We can view this action as a special vertical flattening. This trick is slightly different from the vertical flattening in the previous text, not using the naive flattening vector $(x^0, x^1)$. We call this action "folding".

We can notice that the length of the folded vector $\vec{a}'$ is only half of $\vec{a}$. Doing this recursively, by Verifier continuously sending challenge numbers and Prover repeatedly recursively folding, the vector can eventually be folded into a vector of prime length. However, if we are allowed to append some redundant values to the vector to align the vector length to $2^k$, then after $k$ folds, we can fold the vector into a number with a length of only 1. This is equivalent to performing **horizontal flattening** on a matrix.

This preliminary idea faces **the first problem**, which is that after the vector is cut in half, the commitment $A$ of the original vector $\vec{a}$ seems unusable. So how can Verifier obtain the commitment of the folded vector after Prover performs a folding action? From another perspective, Pedersen commitment, in a sense, is also a kind of inner product, that is, the inner product of the "vector to be committed" and the "base vector":

$$
\mathsf{cm}_{\vec{G}}(\vec{a}) = a_1G_1 + a_2G_2 + \cdots + a_mG_m
$$

The next trick is crucial. We split the base vector $\vec{G}$ in the same way, then fold it similarly, but use a **different** "challenge vector":
$$
(x^{-1}, x)
\left[
\begin{array}{ll}
G_1 &G_2\\
G_3 &G_4
\end{array}
\right]
= (G_1x^{-1} + G_3x, \quad G_2x^{-1} + G_4x) = \vec{G}'
$$

Please note that the two challenge vectors $(x, x^{-1})$ and $(x^{-1}, x)$ above look *symmetric*. The purpose of doing this is to create a special constant term. When calculating the inner product of the new vectors $\vec{a}'$ and $\vec{G}'$ together, its constant term is exactly the inner product of the original vector $\vec{a}$ and $\vec{G}$. But for the non-constant terms (coefficients of $x^2$ and $x^{-2}$ terms), they are some values that look *rather messy*.

Let's expand the calculation. First, we split $\vec{a}$ into two sub-vectors $\vec{a}=(\vec{a}_1, \vec{a}_2)$, $\vec{G}=(\vec{G}_1, \vec{G}_2)$, then perform folding respectively to get $\vec{a}'=\vec{a}_1x + \vec{a}_2x^{-1}$, $\vec{G}'=\vec{G}_1x^{-1} + \vec{G}_2x$,

$$
\vec{a}'\cdot\vec{G}'= 
(1,1)\left(\left[
\begin{array}{cc}
\vec{a}_1\cdot\vec{G}_1 &  \vec{a}_1\cdot\vec{G}_2 \\
\vec{a}_2\cdot\vec{G}_1 &  \vec{a}_2\cdot\vec{G}_2
\end{array}
\right]
\circ
\left[
\begin{array}{cc}
1 & x^2 \\
x^{-2} &  1
\end{array}
\right]\right)
\left(
\begin{array}{c}
1\\
1
\end{array}
\right)
$$

The right side of the above formula is a polynomial in $x$, so we can clearly see the coefficients of $x^2$ and $x^{-2}$.

Next, let's solve the problem raised above: How to let Verifier calculate the commitment of the folded vector $\vec{a}'$:
$$
A'=A + (\vec{a}_1\cdot\vec{G}_2)~x^2 + (\vec{a}_2\cdot\vec{G}_1)~x^{-2}
$$
We let Verifier calculate $A'=\vec{a}'\cdot \vec{G}'$. Obviously, Verifier can calculate $\vec{G}'$ on their own, then Verifier can calculate $A'$ based on $\vec{a}'$ sent by Prover.

The commitment $A'$ is a polynomial in $x$, where the constant term is the commitment $A$ of the original vector, and the coefficients of the $x^2$ and $x^{-2}$ terms can be calculated and sent by Prover. What about the coefficients of the $x^1$ and $x^{-1}$ terms? They happen to be *zero*. Because we cleverly used two symmetric challenge vectors to perform folding operations on $\vec{a}$ and $\vec{G}$ respectively, the coefficients of the $x$ and $x^{-1}$ terms are exactly canceled out, while making the constant term equal to the inner product of the original vectors.

The new commitment $A'$ is easy to calculate $A'=A + Lx^2 + Rx^{-2}$, where $L=(\vec{a}_1\cdot \vec{G}_2)$, $R=(\vec{a}_2\cdot \vec{G}_1)$. The commitments $L$ and $R$ appear to be the result of cross inner products of the two sub-vectors. In this way, the problem is solved. When Prover needs to send a vector $\vec{v}$ of length $m$, Prover can choose to send the vector $\vec{v}'$ that is **folded and flattened**, which has a length of only $m/2$. Then Verifier can also verify the correctness of the original vector by verifying the opening of the folded and flattened vector.

Recursive folding also has its cost. In addition to Verifier having to calculate $\vec{G}'$ extra, Prover also has to calculate $L$ and $R$ extra, and they also need to add one round of interaction. We can see the complete process of recursive folding through the following recursive folding inner product proof protocol.

#### Public Parameters

$\vec{G}, \vec{H}\in\mathbb{G}^n$; $U, T\in\mathbb{G}$

#### Public Input

$P = \vec{a}\vec{G} + \vec{b}\vec{H} + cU + \rho T$

**Witnesses**: $\vec{a}, \vec{b}\in\mathbb{Z}^n_p$; $c\in\Z_p$

**Step 1 (Commitment Step)**: Prover sends commitments of two mask vectors $P_0$ and $C_1$, $C_2$:

1. $P_0=\vec{a}_0\vec{G} + \vec{b}_0\vec{H} + \rho_{0}T$
2. $C_1=\vec{a}_0\cdot\vec{b}_0\cdot{}U + \rho_{1}T$
3. $C_2 = (\vec{a}\cdot\vec{b}_0 + \vec{a}_0\cdot\vec{b})\cdot U + \rho_{2}T$

**Step 2 (Challenge)**: Verifier replies with a challenge number $z$

**Step 3**: Prover calculates the flattened vectors $\vec{a}'$, $\vec{b}'$, $\rho'$ with $z$, and sends $\rho_c$

1. $\vec{a}' = \vec{a} + z\vec{a}_0$
2. $\vec{b}' = \vec{b} + z\vec{b}_0$
3. $\rho' = \rho + z\rho_0$
4. $\rho_c = z^2\rho_1 + z\rho_2$

#### Verification

Verifier can calculate $P'$

1. $P' = P + zP_0 + zC_2 + z^2C_1 - \rho_cT$

Thus, Prover and Verifier can continue to run the rIPA protocol to prove $\vec{a}'\cdot\vec{b}'\overset{?}{=}c'$, where the commitments of these three values are merged into $P' = \vec{a}'\vec{G} + \vec{b}'\vec{H} + (\vec{a}'\cdot\vec{b}')U + \rho'T$.

## 5. Complete Protocol

Below is the complete protocol combining recursive folding and Square-root IPA, which supports the Zero-Knowledge property. If the ZK property is not needed, simply remove the $H$ part related to $\rho$.

### Public Parameters

- $G_0, G_1, G_2, \ldots, G_{2^n-1}, H, U \in \mathbb{G}$.


### Calculating Commitment

1. Prover rearranges $\vec{a}$ into a matrix $M_a\in\mathbb{F}_p^{l\times h}$:

$$
M_a =
\begin{bmatrix}
a_0 & a_1 & a_2 & \cdots & a_{l-1} \\
a_l & a_{l+1} & a_{l+2} & \cdots & a_{2l-1} \\
a_{2l} & a_{2l+1} & a_{2l+2} & \cdots & a_{3l-1} \\
a_{(h-1)l} & a_{(h-1)l+1} & a_{(h-1)l+2} & \cdots & a_{hl-1} \\
\end{bmatrix}
$$

2. Prover calculates commitments $C_0, C_1, ..., C_{h-1}$ by row

$$
\begin{aligned}
C_0 &= \mathsf{cm}(a_0, a_1, ..., a_{l-1}; \rho_0) \\
C_1 &= \mathsf{cm}(a_l, a_{l+1}, ..., a_{2l-1}; \rho_1) \\
C_2 &= \mathsf{cm}(a_{2l}, a_{2l+1}, ..., a_{3l-1}; \rho_2) \\
\cdots\ &=\quad \cdots \\
C_{h-1} &= \mathsf{cm}(a_{(h-1)l}, a_{(h-1)l+1}, ..., a_{hl-1}; \rho_{h-1}) \\
\end{aligned}
$$

Here, $\mathsf{cm}(\vec{a};\rho)$ is defined as:

$$
\mathsf{cm}(\vec{a};\rho) = \sum_{i=0}^{l-1} a_iG_i + \rho H
$$

### Evaluation Proof Protocol


### Public Input

1. Commitment of $\vec{a}$: $(C_0, C_1, ..., C_{h-1})$
2. $\vec{u}=(u_0, u_1, ..., u_{n-1})=\vec{u}_L \parallel \vec{u}_R$, where $|\vec{u}_L|=\log(h)$, $|\vec{u}_R|=\log(l)$
3. $v=\tilde{f}(u_0, u_1, ..., u_{n-1})$

### Witness

1. $\vec{a}$
2. $(\rho_0, \rho_1, ..., \rho_{h-1})$

### Proof Protocol

#### Round 1

1. Prover calculates $\vec{e}$:

$$
\begin{split}
e_0 &= \tilde{eq}(\mathsf{bits}(0), \vec{u}_R) \\
e_1 &= \tilde{eq}(\mathsf{bits}(1), \vec{u}_R) \\
\cdots\ &=\quad \cdots \\
e_{h-1} &= \tilde{eq}(\mathsf{bits}(h-1), \vec{u}_R) \\
\end{split}
$$

2. Prover calculates the matrix multiplication of $\vec{e}$ and $M_a$, obtaining $\vec{b}$, length $l$

$$
\begin{split}
b_0 &= \langle \vec{e}, (a_0, a_l, ..., a_{(h-1)l}) \rangle \\
b_1 &= \langle \vec{e}, (a_1, a_{l+1}, ..., a_{(h-1)l+1}) \rangle \\
\cdots\ &=\quad \cdots \\
b_{l-1} &= \langle \vec{e}, (a_{l-1}, a_{l+l-1}, ..., a_{(h-1)l+l-1}) \rangle \\
\end{split}
$$

3. Prover calculates the commitment $C^*$ of $\vec{b}$

$$
C^* = \mathsf{cm}(\vec{b}; \rho^*)
$$

#### Round 2. 

Prover and Verifier conduct an IPA protocol to complete the inner product proof of $\vec{b}$ and $\vec{d}$, $\vec{d}$ is calculated as follows:

$$
\begin{split}
d_0 &= \tilde{eq}(\mathsf{bits}(0), \vec{u}_L) \\
d_1 &= \tilde{eq}(\mathsf{bits}(1), \vec{u}_L) \\
\cdots\ &=\quad \cdots \\
d_{h-1} &= \tilde{eq}(\mathsf{bits}(h-1), \vec{u}_L) \\
\end{split}
$$

1. Verifier sends a random number $\gamma$

2. Prover and Verifier calculate $U'\in\mathbb{G}$

$$
U' = \gamma\cdot U
$$

#### Round 3 (Repeated $i=0, 1, ..., n-1$). 

First introduce the following symbols, for example, $\vec{b}_L$ represents the first half of $\vec{b}$, $\vec{b}_R$ represents the second half of $\vec{b}$.

$$
\begin{aligned} 
\vec{b}^{(i)}_L &= (b^{(i)}_0, b^{(i)}_1, ..., b^{(i)}_{2^{n-1}-1}) \\
\vec{b}^{(i)}_R &= (b^{(i)}_{2^{n-1}}, b^{(i)}_{2^{n-1}+1}, ..., b^{(i)}_{2^n-1}) \\
\vec{d}^{(i)}_L &= (d^{(i)}_0, d^{(i)}_1, ..., d^{(i)}_{2^{n-1}-1}) \\
\vec{d}^{(i)}_R &= (d^{(i)}_{2^{n-1}}, d^{(i)}_{2^{n-1}+1}, ..., d^{(i)}_{2^n-1}) \\
\vec{G}^{(i)}_L &= (G^{(i)}_0, G^{(i)}_1, ..., G^{(i)}_{2^{n-1}-1}) \\
\vec{G}^{(i)}_R &= (G^{(i)}_{2^{n-1}}, G^{(i)}_{2^{n-1}+1}, ..., G^{(i)}_{2^n-1}) \\
\end{aligned}
$$

Note the initial values here, $\vec{b}^{(0)} = \vec{b}$, $\vec{d}^{(0)} = \vec{d}$, $\vec{G}^{(0)}_L=\vec{G}_L$, $\vec{G}^{(0)}_R=\vec{G}_R$.

1. Prover sends $L^{(i)}$ and $R^{(i)}$:

$$
\begin{aligned}
L^{(i)} &= \mathsf{cm}_{\vec{G}^{(i)}_L}(\vec{b}^{(i)}; \rho^{(i)}_L) + \langle\vec{b}^{(i)}_R, \vec{d}^{(i)}_L\rangle\cdot{}U' \\
R^{(i)} &= \mathsf{cm}_{\vec{G}^{(i)}_R}(\vec{b}^{(i)}; \rho^{(i)}_R) + \langle\vec{b}^{(i)}_L, \vec{d}^{(i)}_R\rangle\cdot{}U' \\
\end{aligned}
$$


2. Verifier sends a random number $\mu^{(i)}$, 

3. Prover calculates and sends the following values:

$$
\begin{aligned}
\vec{b}^{(i+1)} &= \vec{b}^{i}_L + \mu^{(i)}\cdot\vec{b}^{i}_R \\
\vec{d}^{(i+1)} &= \vec{d}^{i}_L + {\mu^{(i)}}^{-1}\cdot\vec{d}^{i}_R \\
\end{aligned}
$$

4. Prover and Verifier calculate $\vec{G}^{(i+1)}$

$$
\begin{aligned}
\vec{G}^{(i+1)} &= \vec{G}^{(i)}_L + {\mu^{(i)}}^{-1}\cdot\vec{G}^{(i)}_R \\
\end{aligned}
$$ 

5. Prover and Verifier recursively perform Round 3 until $i=n-1$

6. Prover calculates

$$
\hat{\rho} = \rho^* + \sum_{i=0}^{n-1}\mu^{(i)}\cdot\rho^{(i)}_L + {\mu^{(i)}}^{-1}\cdot\rho^{(i)}_R
$$

#### Round 4.

1. Prover calculates and sends $R$, where $r, \rho_r\in\mathbb{F}_p$ are random numbers sampled by Prover

$$
R = r\cdot(G^{(n-1)} + b^{(n-1)}\cdot{U'}) + \rho_r\cdot{}H
$$

#### Round  5.

1. Verifier sends a random number $\zeta\in\mathbb{F}_p$

2. Prover calculates $z$ and $z_r$

$$
z = r + \zeta\cdot b^{(n-1)}
$$

$$
z_r = \rho_r + \zeta\cdot\hat{\rho}
$$

#### Verification

1. Verifier calculates $C^*$ and $P$

$$
C^* = d_0C_0 + d_1C_1 + ... + d_{h-1}C_{h-1}
$$

$$
P = C^* + \sum_{i=0}^{n-1}\mu^{(i)}L^{(i)} + {\mu^{(i)}}^{-1}R^{(i)}
$$

2. Verifier verifies if the following equation holds

$$
R + \zeta\cdot P \overset{?}{=} z\cdot (G^{(n-1)} + b^{(n-1)}\cdot{U'}) + z_r\cdot{}H
$$


## References

1. [WTSTW16] Riad S. Wahby, Ioanna Tzialla, abhi shelat, Justin Thaler, and Michael Walfish. "Doubly-efficient zkSNARKs without trusted setup."  In 2018 IEEE Symposium on Security and Privacy (SP), pp. 926-943. IEEE, 2018.  https://eprint.iacr.org/2016/263 
2. [BBB+18] Bünz, Benedikt, Jonathan Bootle, Dan Boneh, Andrew Poelstra, Pieter Wuille, and Greg Maxwell. "Bulletproofs: Short proofs for confidential transactions and more." In 2018 IEEE symposium on security and privacy (SP), pp. 315-334. IEEE, 2018. https://eprint.iacr.org/2017/1066 
3. [BCC+16] Jonathan Bootle, Andrea Cerulli, Pyrros Chaidos, Jens Groth, and Christophe Petit. "Efficient Zero-Knowledge Arguments for Arithmetic Circuits in the Discrete Log Setting."  In Advances in Cryptology–EUROCRYPT 2016: 35th Annual International Conference on the Theory and Applications of Cryptographic Techniques, Vienna, Austria, May 8-12, 2016, Proceedings, Part II 35, pp. 327-357. Springer Berlin Heidelberg, 2016.  https://eprint.iacr.org/2016/263
