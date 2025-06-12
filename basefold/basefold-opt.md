# Basefold Optimization

Yu Guo <yu.guo@secbit.io>

Last updated: 2025-06-10

## Protocol Review

For any multilinear polynomial $\tilde{f}(X_0, X_1,\ldots, X_{n-1})\in F^{\leq 1}[X_0, X_1,\ldots, X_{n-1}]$ with n variables (indeterminates), if we want to prove that its evaluation at an arbitrary point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$ is correct, the Basefold protocol [ZCF23] provides an elegant solution. Its core idea is to use the Sumcheck protocol to prove $\tilde{f}(u_0, u_1, \ldots, u_{n-1})$, and then in the last step of the Sumcheck protocol, the Verifier needs to verify the evaluation of $\tilde{f}(r_0, r_1, \ldots, r_{n-1})$. Basefold does not rely on another MLE PCS to complete this final step of proof, but instead uses a FRI protocol to assist. The original purpose of the FRI protocol is to prove the proximity of a codeword, i.e., that its distance from the correct codeword does not exceed a security parameter $\delta$. However, in the last step of the FRI protocol, the Prover sends the message corresponding to the folded codeword. If folded sufficiently, the final message is a constant (polynomial). If the Prover is honest, this value happens to be equal to the value of $\tilde{f}(r_0, r_1, \ldots, r_{n-1})$, which perfectly complements the Sumcheck situation.

Let's go through the protocol details. First, $\tilde{f}(\vec{X})$ can be rewritten as the following equation:

$$
\tilde{f}(\vec{X}) = \sum_{\vec{b}\in\{0,1\}^n} \tilde{f}(\vec{b}) \cdot eq(\vec{X}, \vec{b})
$$

We can see that the right side of the equation is a sum, which meets the requirements of the Sumcheck protocol. The Sumcheck protocol can prove the following inner product equation:

$$
v = \sum_{\vec{b}\in\{0,1\}^n} \tilde{f}(\vec{b}) \cdot \tilde{g}(\vec{b})
$$

### Inner Product Proof Based on Sumcheck Protocol

Let's review how to use the Sumcheck protocol to prove inner products. We assume that two vectors $\vec{f}$ and $\vec{g}$ of length $2^n$ correspond to two n-variable multilinear polynomials, $\tilde{f}$ and $\tilde{g}$. Next, we explain how the Prover and Verifier prove the following goal:

$$
s = \sum_{\vec{b}\in\{0,1\}^n} \tilde{f}(b_0, b_1, \ldots, b_{n-1}) \cdot \tilde{g}(b_0, b_1, \ldots, b_{n-1})
$$

Round 1: The Prover constructs a degree-2 univariate polynomial $h^{(0)}(X)$ and sends its evaluations at $X=0,1,2$, i.e., $(h^{(0)}(0), h^{(0)}(1), h^{(0)}(2))$.

$$
h^{(0)}(X) = \sum_{\vec{b}\in\{0,1\}^{n-1}} \tilde{f}(X, b_1, b_2, \ldots, b_{n-1}) \cdot \tilde{g}(X, b_1, b_2, \ldots, b_{n-1})
$$

The Verifier checks if $h^{(0)}(0)+h^{(0)}(1)\overset{?}{=}v$. If true, it responds with a random challenge $r_0\in\mathbb{F}_q$, and the proof goal is transformed into a new goal:

$$
h^{(0)}(r_0) = \sum_{\vec{b}\in\{0,1\}^{n-1}} \tilde{f}(r_0, b_1, b_2, \ldots, b_{n-1}) \cdot \tilde{g}(r_0, b_1, b_2, \ldots, b_{n-1})
$$

Note that $\tilde{f}(r_0, X_1, \ldots, X_{n-1})$ and $\tilde{g}(r_0, X_1, \ldots, X_{n-1})$ are still multilinear polynomials. We denote them as $\tilde{f}^{(1)}(X_1, \ldots, X_{n-1})$ and $\tilde{g}^{(1)}(X_1, \ldots, X_{n-1})$:

$$
\begin{aligned}
\tilde{f}^{(1)}(X_1, \ldots, X_{n-1}) &= \tilde{f}(r_0, X_1, \ldots, X_{n-1}) \\
\tilde{g}^{(1)}(X_1, \ldots, X_{n-1}) &= \tilde{g}(r_0, X_1, \ldots, X_{n-1})
\end{aligned}
$$

So the new proof goal can be written as:

$$
h^{(0)}(r_0) = v^{(1)} \overset{?}{=} \sum_{\vec{b}\in\{0,1\}^{n-1}} \tilde{f}^{(1)}(b_1, \ldots, b_{n-1}) \cdot \tilde{g}^{(1)}(b_1, \ldots, b_{n-1})
$$

This way, Sumcheck can be seen as a recursive protocol, with each call halving the length of the sum.
The Prover and Verifier repeat this process until the proof length of Sumcheck becomes 1.

In round n, the Prover constructs $h^{(n-1)}(X)$ and sends $(h^{(n-1)}(0), h^{(n-1)}(1), h^{(n-1)}(2))$:

$$
h^{(n-1)}(X) = \tilde{f}^{(n-1)}(X) \cdot \tilde{g}^{(n-1)}(X)
$$

The Verifier checks if $h^{(n-1)}(0)+h^{(n-1)}(1)\overset{?}{=}v^{(n-1)}$. If true, it responds with a random challenge $r_{n-1}\in\mathbb{F}_q$, and the proof goal is transformed into a new goal:

$$
h^{(n-1)}(r_{n-1}) \overset{?}{=} \tilde{f}^{(n-1)}(r_{n-1}) \cdot \tilde{g}^{(n-1)}(r_{n-1})
$$

Then the Prover doesn't need to send any more messages. The Verifier directly calculates the value of $h^{(n-1)}(r_{n-1})$, then calls the oracles of $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ and $\tilde{g}(X_0, X_1, \ldots, X_{n-1})$ to get the values of $\tilde{f}^{(n-1)}(r_{n-1})$ and $\tilde{g}^{(n-1)}(r_{n-1})$, and then verifies if the equation holds:

$$
\begin{aligned}
f^{(n-1)}(r_{n-1}) &= \tilde{f}(r_0, r_1, \ldots, r_{n-1}) \\
g^{(n-1)}(r_{n-1}) &= \tilde{g}(r_0, r_1, \ldots, r_{n-1}) \\
\end{aligned}
$$

Typically, in the last step of Sumcheck, the oracles of $\tilde{f}$ and $\tilde{g}$ that the Verifier relies on are implemented using Polynomial Commitment. That is, before Sumcheck begins, the Prover first sends their commitments, and then in the last step of Sumcheck, the Prover sends the values of $\tilde{f}(r_0, r_1, \ldots, r_{n-1})$ and $\tilde{g}(r_0, r_1, \ldots, r_{n-1})$, along with the corresponding proofs of Multilinear Polynomial Evaluation.

### Proximity Proof Based on FRI Protocol

> TODO

### Basefold Proof Process Based on Multilinear Basis

Let's go through the Prover's proof process from an implementation perspective. To help readers understand, we assume $\tilde{f}$ is a three-variable multilinear polynomial, and the protocol has a total of $n=3$ rounds. The Prover first does one round of Sumcheck, then reuses the random numbers from Sumcheck to do one round of FRI protocol, which is equivalent to completing one round of the Basefold protocol; then continues until the proof length of Sumcheck becomes 1.

$$
\begin{aligned}
 v &= \sum_{(b_0,b_1,b_2)\in\{0,1\}^3} \tilde{f}(b_0, b_1, b_2) \cdot eq((u_0, u_1, u_2), (b_0, b_1, b_2)) \\
 &= \sum_{i=0}^{7} a_i\cdot w_i
\end{aligned}
$$

Here $v= \tilde{f}(u_0, u_1, u_2)$, vector $\vec{a}=(a_0, a_1, \cdots, a_{7})$ is the evaluation of $\tilde{f}(\vec{X})$ on the Boolean Hypercube, and $\vec{w}=(w_0, w_1, \cdots, w_{7})$ is the evaluation of $eq(\vec{u}, \vec{X})$ on the Boolean Hypercube:

$$
\begin{aligned}
w_0 &= (1-u_0)(1-u_1)(1-u_2) \\
w_1 &= u_0(1-u_1)(1-u_2) \\
w_2 &= (1-u_0)u_1(1-u_2) \\
w_3 &= u_0u_1(1-u_2) \\
w_4 &= (1-u_0)(1-u_1)u_2 \\
w_5 &= u_0(1-u_1)u_2 \\
w_6 &= (1-u_0)u_1u_2 \\
w_7 &= u_0u_1u_2 \\
\end{aligned}
$$

The Prover needs to prove the correctness of this inner product calculation. That is:

$$
v = a_0w_0 + a_1w_1 + a_2w_2 + a_3w_3 + a_4w_4 + a_5w_5 + a_6w_6 + a_7w_7
$$

The Prover maintains two arrays of length $2^n$, storing $\vec{a}$ and $\vec{w}$ respectively, corresponding to the Evaluations representations of $\tilde{f}$ and $eq$.

$$
\begin{aligned}
a_i &= \tilde{f}(i_0, i_1, i_2) \\
w_i &= eq((u_0, u_1, u_2), (i_0, i_1, i_2))
\end{aligned}
$$

In the first round of the Sumcheck protocol, the Prover calculates $h^{(0)}(X)$. This is a degree-2 univariate polynomial. We only need to get its evaluations at at least three different points to uniquely represent this polynomial. To optimize computation, we specifically choose the points $X=0,1,2$.

$$
h^{(0)}(X) = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{g}(X, b_1, b_2)
$$

And $h^{(0)}(0)$ happens to be equal to the sum of the terms at even positions in the inner product sum, while $h^{(0)}(1)$ happens to be equal to the sum of the terms at odd positions in the inner product sum, represented as follows:

$$
\begin{aligned}
h^{(0)}(0) &= a_0w_0 + a_2w_2 + a_4w_4 + a_6w_6  \\
h^{(0)}(1) &= a_1w_1 + a_3w_3 + a_5w_5 + a_7w_7 \\
\end{aligned}
$$

Therefore, the Prover only needs two passes of $2^{n-1}$ multiplications and $2^{n-1}$ additions (a total of $2^n$ multiplications and $2^{n}$ additions) to calculate $h^{(0)}(0)$ and $h^{(0)}(1)$. But how to calculate $h^{(0)}(2)$? Let's first prove the following equation, which we will use repeatedly:

$$
\tilde{f}(X_0+1, X_1, X_2) = \tilde{f}(X_0, X_1, X_2) + 
\tilde{f}(1, X_1, X_2) - \tilde{f}(0, X_1, X_2)
$$

Generalizing this, we can get the following expression:

$$
\tilde{f}(\vec{Y}, X_k+1, \vec{Z}) = \tilde{f}(\vec{Y}, X_k, \vec{Z}) + 
\tilde{f}(\vec{Y}, 1, \vec{Z}) - \tilde{f}(\vec{Y}, 0, \vec{Z})
$$

Then, according to the properties of Multilinear Polynomials, we can calculate the value of $h^{(0)}(2)$:

$$
\begin{aligned}
h^{(0)}(2) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(2, b_1, b_2) \cdot \tilde{w}(2, b_1, b_2)  \\
&=  \sum_{b_1,b_2\in\{0,1\}^{2}} \Big( 2\cdot\tilde{f}(1, b_1, b_2) - \tilde{f}(0, b_1, b_2) \Big)\cdot \Big( 2\cdot\tilde{w}(1, b_1, b_2)  - \tilde{w}(0, b_1, b_2) \Big)
\end{aligned}
$$

This requires the Prover to perform $2^{n-1}$ multiplications and $5\cdot 2^{n-1}$ additions. Then the Prover sends $h^{(0)}(0), h^{(0)}(1), h^{(0)}(2)$ to the Verifier, and the Verifier checks if the following equation holds:

$$
h^{(0)}(0)+h^{(0)}(1) \overset{?}{=} v
$$

If it holds, the Verifier replies with a random number $r_0\in\mathbb{F}_q$, and the proof goal is reduced to a new proof goal:

$$
\begin{aligned}
h^{(0)}(r_0) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(r_0, b_1, b_2) \cdot \tilde{w}(r_0, b_1, b_2) \\
& = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}^{(1)}(b_1,b_2) \cdot \tilde{w}^{(1)}(b_1,b_2)
\end{aligned}
$$

Here, the Evaluations representations of $f^{(1)}(X_1, X_2)$ and $w^{(1)}(X_1, X_2)$ on the two-dimensional Boolean Hypercube can actually be calculated directly from the Evaluations of $\tilde{f}$ and $\tilde{w}$:

$$
\begin{aligned}
a^{(1)}_0 &= \tilde{f}^{(1)}(0, 0) = (1-r_0)\cdot\tilde{f}(0, 0, 0) + r_0\cdot\tilde{f}(1, 0, 0) \\
a^{(1)}_1 &= \tilde{f}^{(1)}(0, 1) = (1-r_0)\cdot\tilde{f}(0, 0, 1) + r_0\cdot\tilde{f}(1, 0, 1) \\
a^{(1)}_2 &= \tilde{f}^{(1)}(1, 0) = (1-r_0)\cdot\tilde{f}(0, 1, 0) + r_0\cdot\tilde{f}(1, 1, 0) \\
a^{(1)}_3 &= \tilde{f}^{(1)}(1, 1) = (1-r_0)\cdot\tilde{f}(0, 1, 1) + r_0\cdot\tilde{f}(1, 1, 1) \\
\end{aligned}
$$

So this requires the Prover to perform $2^{n-1}$ multiplications and $2^n$ additions to get the Evaluations representation of $f^{(1)}(X_1, X_2)$, recorded in $(a^{(1)}_0, a^{(1)}_1, a^{(1)}_2, a^{(1)}_3)$:

$$
\begin{aligned}
a^{(1)}_0 &= (1-r_0)\cdot a_0 + r_0\cdot a_1 \\
a^{(1)}_1 &= (1-r_0)\cdot a_2 + r_0\cdot a_3 \\
a^{(1)}_2 &= (1-r_0)\cdot a_4 + r_0\cdot a_5 \\
a^{(1)}_3 &= (1-r_0)\cdot a_6 + r_0\cdot a_7 \\
\end{aligned}
$$

In addition, the Prover also needs to calculate the Evaluations representation of $\tilde{w}^{(1)}(X_1,X_2)$ in the same way ($2^{n-1}$ multiplications and $2^n$ additions):

$$
\begin{aligned}
w^{(1)}_0 &= \tilde{w}^{(1)}(0, 0) = (1-r_0)\cdot\tilde{w}(0, 0, 0) + r_0\cdot\tilde{w}(1, 0, 0) \\
w^{(1)}_1 &= \tilde{w}^{(1)}(0, 1) = (1-r_0)\cdot\tilde{w}(0, 0, 1) + r_0\cdot\tilde{w}(1, 0, 1) \\
w^{(1)}_2 &= \tilde{w}^{(1)}(1, 0) = (1-r_0)\cdot\tilde{w}(0, 1, 0) + r_0\cdot\tilde{w}(1, 1, 0) \\
w^{(1)}_3 &= \tilde{w}^{(1)}(1, 1) = (1-r_0)\cdot\tilde{w}(0, 1, 1) + r_0\cdot\tilde{w}(1, 1, 1) \\
\end{aligned}
$$

These two parts of folding calculations for Multilinear Polynomials together require a total of $2^n$ multiplications and $2\cdot 2^n$ additions. The calculation results are stored in two arrays $\vec{a}^{(1)}$ and $\vec{w}^{(1)}$ of length $2^{n-1}$.

Next, the Prover and Verifier complete the first round of the FRI protocol (Commit-phase), which is to calculate the RS Code of the folded univariate polynomial. Below is the univariate polynomial $\hat{f}(X)$ corresponding to $\tilde{f}(X_0, X_1, X_2)$. Please note that its coefficient form corresponds to the Evaluations representation of $\tilde{f}(X)$, which is different from the form in the Basefold paper [ZCF23]:

$$
\hat{f}(X) = a_0 + a_1X + a_2X^2 + a_3X^3 + a_4X^4 + a_5X^5 + a_6X^6 + a_7X^7
$$

The Prover has already calculated the Evaluations representation of the folded $\tilde{f}^{(1)}(X_1, X_2)$, i.e., $\vec{a}^{(1)}$, in the first round of Sumcheck. It also corresponds to a univariate polynomial $\hat{f}^{(1)}(X)$, whose coefficient form is:

$$
\begin{aligned}
\hat{f}^{(1)}(X) &= a^{(1)}_0 + a^{(1)}_1X + a^{(1)}_2X^2 + a^{(1)}_3X^3
\end{aligned}
$$

Next, the Prover needs to calculate the RS Code of $\tilde{f}^{(1)}(X)$. If calculated directly, this would require the Prover to perform $(n2^{n-1})$ multiplications. Fortunately, since RS Code is a "linear code", the Prover can directly fold on the RS Code of $\hat{f}(X)$ using $(1-r_0, r_0)$ to obtain the RS Code of $\hat{f}^{(1)}(X)$.

Let's first review the familiar polynomial decomposition of $\hat{f}(X)$:

$$
\begin{aligned}
\hat{f}(X) &= f_e(X^2) + X\cdot f_o(X^2) \\
\hat{f}(-X) &= f_e(X^2) - X\cdot f_o(X^2)
\end{aligned}
$$

Where $f_e(X)$ is the polynomial composed of even terms, and $f_o(X)$ is the polynomial composed of odd terms:

$$
\begin{aligned}
f_e(X) &= a_0 + a_2X + a_4X^2 + a_6X^3 \\
f_o(X) &= a_1 + a_3X + a_5X^2 + a_7X^3
\end{aligned}
$$

Also because

$$
\begin{aligned}
\hat{f}^{(1)}(X^2) &= (1-r_0)\cdot f_e(X^2) + r_0\cdot f_o(X^2) \\
& = (1-r_0)\cdot\frac{\hat{f}(X)+\hat{f}(-X)}{2} + r_0\cdot\frac{\hat{f}(X)-\hat{f}(-X)}{2}
\end{aligned}
$$

Therefore, the Prover only needs to perform the same folding operation on the RS Code of $\hat{f}(X)$ to obtain the RS Code of $\hat{f}^{(1)}(X)$:

$$
\mathsf{encode}(\hat{f}^{(1)})_i = (1-r_0)\cdot\mathsf{encode}(\hat{f})_i + r_0\cdot\mathsf{encode}(\hat{f})_{(i+N/2)}, \quad i\in[0, N)
$$

Here, $N$ is the length after encoding a message of length $2^n$, where $\rho=2^n/N$ is the code rate.

At this point, the Prover sends the Merkle Root of $\mathsf{encode}(\hat{f}^{(1)})$ as a commitment, then the Prover and Verifier proceed to the second round of Sumcheck, repeating the above process until the sum length of the Sumcheck protocol becomes 1. At this time, the accompanying FRI protocol has also folded the polynomial to a constant polynomial $\hat{f}^{(3)}(X)$. If the Prover is honest, then the constant term of $\hat{f}^{(3)}(X)$ happens to be $\tilde{f}(r_0, r_1, r_2)$:

$$
\hat{f}^{(3)}(X) = \tilde{f}(r_0, r_1, r_2)
$$

This value can be used by the Verifier for verification:

$$
v^{(3)} \overset{?}{=} \hat{f}^{(3)}(0)\cdot \tilde{eq}((u_0, u_1, u_2), (r_0, r_1, r_2))
$$

At this point, the Verifier needs to calculate $\tilde{eq}((u_0, u_1, u_2), (r_0, r_1, r_2))$ to complete the final verification step, which requires $2n$ multiplications:

$$
\begin{aligned}
\tilde{eq}((u_0, u_1, u_2), (r_0, r_1, r_2)) &= \prod_{i=0}^{2} \Big( (1-r_i)\cdot(1-u_i) + r_i\cdot u_i \Big) \\
&= \prod_{i=0}^{2} \Big( 1 + 2r_i\cdot u_i - r_i -u_i \Big)
\end{aligned}
$$

For the Query-phase part of FRI, we omit it here.

### Sumcheck Performance Analysis

In the Sumcheck protocol part, the Prover's total computation is:

- Calculate $\vec{w}$: $2^n$ multiplications
- Calculate $h^{i}(0)$: $2^n$ multiplications, $2\cdot 2^n$ additions
- Calculate $h^{i}(1)$: $2^n$ multiplications, $2\cdot 2^n$ additions
- Calculate $h^{i}(2)$: $2^{n}$ multiplications and $5\cdot 2^{n}$ additions
- Folding calculation of $\vec{a}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Folding calculation of $\vec{w}$: $2^n$ multiplications and $2\cdot 2^n$ additions

Verifier's computation:

- Verify $h^{(i)}(0)+h^{(i)}(1)\overset{?}{=}h^{(i-1)}(r_{i-1})$: $n$ additions
- Interpolate to calculate $h^{(i)}(r_i)$: $4n$ divisions, $3n$ multiplications and $9n$ additions
- Calculate $\tilde{eq}(r_0, r_1, \cdots, r_{n-1})$: $n$ multiplications, $4n$ additions
- Final verification: 1 multiplication

## Sumcheck Optimization 

In the above protocol, the Prover needs to send three degree-2 polynomials $h^{(0)}(X), h^{(1)}(X), h^{(2)}(X)$. The most straightforward implementation is for the Prover to send the evaluations of these polynomials at $X=0,1,2$. The Verifier checks the first two values, then uses the third value to calculate Lagrange Interpolation to get $h^{(0)}(r_0)$.

We can slightly modify the above protocol to allow the Prover to only send linear polynomials of degree 1. Then the Prover only needs to send the evaluations at two points, and the Verifier only needs to do linear interpolation to calculate the next sum value.

Habock gave an optimized version of the Basefold protocol in [Hab24], which can make $h(X)$ a linear polynomial of degree 1. This optimization technique first appeared in [Gruen24]. Let's briefly describe this optimization technique.

According to the definition of $\tilde{eq}(\vec{X}, \vec{Y})$, it can be decomposed as:

$$
\tilde{eq}(\vec{X}_0\parallel\vec{X}_1, \vec{Y}_0\parallel\vec{Y}_1) = eq(\vec{X}_0, \vec{Y}_0) \cdot eq(\vec{X}_1, \vec{Y}_1)
$$

Let's first observe the definition of $h^{(0)}(X)$:

$$
h^{(0)}(X) = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{eq}((u_0, u_1, u_2), (X, b_1, b_2))
$$

The right side of its equation can be rewritten as:

$$
\begin{aligned}
h^{(0)}(X) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{eq}((u_0, u_1, u_2), (X, b_1, b_2)) \\
&= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot eq(u_0, X) \cdot eq((u_1, u_2), (b_1, b_2)) \\
&= eq(u_0, X) \cdot \sum_{(b_1,b_2)\in\{0,1\}^2`}  \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big) \\
\end{aligned}
$$

We introduce the notation $g^{(0)}(X)$ to represent the linear polynomial on the right side of the equation except for $eq(u_0, X)$, then $h^{(0)}(X)$ can be represented as the product of two linear polynomials:

$$
h^{(0)}(X) = eq(u_0, X) \cdot g^{(0)}(X)
$$

We modify the protocol as follows: let the Prover not directly send $h_0(X)$, but send the linear polynomial $g_0(X)$, i.e., $g^{(0)}(0), g^{(0)}(1)$,

$$
g^{(0)}(X) = \sum_{(b_1,b_2)\in\{0,1\}^2} \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big)
$$

After receiving the polynomial $g^{(0)}(0), g^{(0)}(1)$, the Verifier can calculate the values of $h^{(0)}(0), h^{(0)}(1)$ on its own, because:

$$
\begin{aligned}
h^{(0)}(0) &= (1-u_0)\cdot g^{(0)}(0) \\
h^{(0)}(1) &= u_0 \cdot g^{(0)}(1) \\
\end{aligned}
$$

Then the Verifier can verify $h^{(0)}(0)+h^{(0)}(1)\overset{?}{=}v$. If the verification passes, the Verifier can calculate $h^{(0)}(r_0)$:

$$
h^{(0)}(r_0) = \Big((1-u_0)(1-r_0)+u_0r_0\Big) \cdot g^{(0)}(r_0)
$$

Here $g^{(0)}(r_0)$ can also be calculated from $g^{(0)}(0), g^{(0)}(1)$:

$$
g^{(0)}(r_0) = g^{(0)}(0) + \Big(g^{(0)}(1)-g^{(0)}(0)\Big)\cdot r_0
$$

Finally, calculate $h_0(r_0)$. In summary, the Verifier needs one multiplication to verify $v$, and three multiplications to calculate $h^{(0)}(r_0)$.

### Performance Analysis

The Prover's total computation is:

- Calculate $g^{i}(0)$: $2^n$ multiplications, $2\cdot 2^n$ additions
- Calculate $g^{i}(1)$: $2^n$ multiplications
- Folding calculation of $\vec{a}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Folding calculation of $\vec{w}$: $2^n$ multiplications and $2\cdot 2^n$ additions

Verifier's computation:

- Calculate $h^{(i)}(0)$: $n$ multiplications, $n$ additions
- Calculate $h^{(i)}(1)$: $n$ multiplications, $n$ additions
- Verify $h^{(i)}(0)+h^{(i)}(1)$: $n$ additions
- Calculate $h^{(i)}(r_i)$: $3n$ multiplications, $6n$ additions
- Calculate $\tilde{eq}(r_0, r_1, \cdots, r_{n-1})$: $n$ multiplications, $4n$ additions
- Final verification: 1 multiplication

## Further Optimization of the Verifier

Let's observe the definition of $g^{(0)}(X)$ again:

$$
g^{(0)}(X) = \sum_{(b_1,b_2)\in\{0,1\}^2} \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big)
$$

This sum happens to be equal to $\tilde{f}(X, u_1, u_2)$, so we can review the above optimization protocol from another perspective:

In the first step, the Prover sends $g^{(0)}(0), g^{(0)}(1)$, which is actually sending:

$$
\begin{aligned}
g^{(0)}(0) &= \tilde{f}(0, u_1, u_2) \\
g^{(0)}(1) &= \tilde{f}(1, u_1, u_2) \\
\end{aligned}
$$

The Verifier checks the correctness of $h^{(0)}(X)$, which is equivalent to verifying the correctness of $g^{(0)}(X)$:

$$
h^{(0)}(u_0) = eq(u_0, u_0) \cdot g^{(0)}(u_0) = g^{(0)}(u_0) = g^{(0)}(0) + \Big(g^{(0)}(1)-g^{(0)}(0)\Big)\cdot u_0 \overset{?}{=} v
$$

Then the Verifier calculates $g^{(0)}(r_0)$ as the sum value for the next round of Sumcheck.

$$
g^{(0)}(r_0) = g^{(0)}(0) + \Big(g^{(0)}(1)-g^{(0)}(0)\Big)\cdot r_0
$$

Therefore, it seems we no longer need to introduce $h^{(i)}(X)$, but can directly use $g^{(i)}(X)$. This way, in each round of the Sumcheck protocol, the Prover needs to send $g^{(i)}(0), g^{(i)}(1)$, and the Verifier only needs to perform two multiplications, one to calculate $g^{(i)}(u_i)$, and one to calculate $g^{(i)}(r_i)$. And in the last step of Sumcheck, the Verifier only needs to verify:

$$
g^{(n-1)}(r_{n-1}) \overset{?}{=} \tilde{f}(r_0, r_1, \cdots, r_{n-1})
$$

It's not hard to see that in the $i$-th round, if the Prover is honest, $g^{(i)}(X)$ should be exactly equal to $\tilde{f}^{(i)}(r_0, r_1, \cdots, r_{i-1}, X, u_{i+1}, \cdots, u_{n-1})$. Let's rewrite the transformed Sumcheck protocol:

Round 1: The Prover sends $\tilde{f}(0, u_1, u_2), \tilde{f}(1, u_1, u_2)$, the Verifier verifies:

$$
(1-u_0)\cdot \tilde{f}(0, u_1, u_2) + u_0\cdot \tilde{f}(1, u_1, u_2) \overset{?}{=} \tilde{f}(u_0, u_1, u_2) = v
$$

The Verifier responds with $r_0\in F$, and calculates $g^{(0)}(r_0) = \tilde{f}(r_0, u_1, u_2)$ as the new sum value $v^{(1)}$:

$$
\tilde{f}(r_0, u_1, u_2) = (1-r_0)\cdot \tilde{f}(0, u_1, u_2) + r_0\cdot \tilde{f}(1, u_1, u_2)
$$

Round 2: The Prover sends $\tilde{f}(r_0, 0, u_2), \tilde{f}(r_0, 1, u_2)$, the Verifier verifies:

$$
(1-u_1)\cdot \tilde{f}(r_0, 0, u_2) + u_1\cdot \tilde{f}(r_0, 1, u_2) \overset{?}{=} \tilde{f}(r_0, u_1, u_2) = v^{(1)}
$$

The Verifier responds with $r_1\in F$, and calculates $g^{(1)}(r_1) = \tilde{f}(r_0, r_1, u_2)$ as the new sum value:

$$
\tilde{f}(r_0, r_1, u_2) = (1-r_1)\cdot \tilde{f}(r_0, 0, u_2) + r_1\cdot \tilde{f}(r_0, 1, u_2)
$$

Round 3: The Prover sends $\tilde{f}(r_0, r_1, 0), \tilde{f}(r_0, r_1, 1)$, the Verifier verifies:

$$
(1-u_2)\cdot \tilde{f}(r_0, r_1, 0) + u_2\cdot \tilde{f}(r_0, r_1, 1) \overset{?}{=} \tilde{f}(r_0, r_1, u_2) = v^{(2)}
$$

The Verifier responds with $r_2\in F$, and calculates $g^{(2)}(r_2) = \tilde{f}(r_0, r_1, r_2)$ as the new sum value:

$$
\tilde{f}(r_0, r_1, r_2) = (1-r_2)\cdot \tilde{f}(r_0, r_1, 0) + r_2\cdot \tilde{f}(r_0, r_1, 1)
$$

Verification step: The Verifier verifies the following equation through the $\tilde{f}(X_0, X_1, X_2)$ Oracle:

$$
g^{(2)}(r_2) \overset{?}{=} \tilde{f}(r_0, r_1, r_2)
$$

This way, the Verifier only needs to perform two multiplications in each round. The first multiplication is to verify the correctness of the sum value $v^{(i)}$, and the second multiplication is to calculate $g^{(i)}(r_i)$, totaling $2n$ multiplications.

## Prover's Computation Optimization

In the three rounds, the Prover needs to send $g^{(0)}(0)$ and $g^{(0)}(1)$, $g^{(1)}(0)$ and $g^{(1)}(1)$, $g^{(2)}(0)$ and $g^{(2)}(1)$ in turn.

$$
\begin{aligned}
g^{(0)}(0) &= \tilde{f}(0, u_1, u_2) \\
g^{(0)}(1) &= \tilde{f}(1, u_1, u_2) \\
g^{(1)}(0) &= \tilde{f}(r_0, 0, u_2) \\
g^{(1)}(1) &= \tilde{f}(r_0, 1, u_2) \\
g^{(2)}(0) &= \tilde{f}(r_0, r_1, 0) \\
g^{(2)}(1) &= \tilde{f}(r_0, r_1, 1) \\
\end{aligned}
$$

In this section, we'll look at how the Prover can efficiently calculate $g^{(i)}(0), g^{(i)}(1)$.

As mentioned earlier, the Prover maintains an array $\vec{a}$ of length $2^n$:

$$
\begin{aligned}
a_0 &= \tilde{f}(0, 0, 0) \\
a_1 &= \tilde{f}(1, 0, 0) \\
a_2 &= \tilde{f}(0, 1, 0) \\
a_3 &= \tilde{f}(1, 1, 0) \\
a_4 &= \tilde{f}(0, 0, 1) \\
a_5 &= \tilde{f}(1, 0, 1) \\
a_6 &= \tilde{f}(0, 1, 1) \\
a_7 &= \tilde{f}(1, 1, 1) \\
\end{aligned}
$$

It's folded in each round of Sumcheck. For example, after the first round of folding (with $r_0$ as the folding factor), the Prover gets:

$$
\begin{aligned}
a^{(1)}_0 &= \tilde{f}^{(1)}(0, 0) = (1-r_0)\cdot\tilde{f}(0, 0, 0) + r_0\cdot\tilde{f}(1, 0, 0) \\
a^{(1)}_1 &= \tilde{f}^{(1)}(0, 1) = (1-r_0)\cdot\tilde{f}(0, 0, 1) + r_0\cdot\tilde{f}(1, 0, 1) \\
a^{(1)}_2 &= \tilde{f}^{(1)}(1, 0) = (1-r_0)\cdot\tilde{f}(0, 1, 0) + r_0\cdot\tilde{f}(1, 1, 0) \\
a^{(1)}_3 &= \tilde{f}^{(1)}(1, 1) = (1-r_0)\cdot\tilde{f}(0, 1, 1) + r_0\cdot\tilde{f}(1, 1, 1) \\
\end{aligned}
$$

To efficiently calculate $g^{(i)}(0), g^{(i)}(1)$, we let the Prover do some pre-computation before the Sumcheck protocol starts, obtaining a vector $\vec{d}$ of length $2^n-1$.

This vector is the result of folding the vector $\vec{a}$ (with $u_2, u_1, u_0$ as folding factors). We first fold the vector $\vec{a}$ using $u_2$ to get $d_0, d_1, d_2, d_3$:

$$
\begin{aligned}
d_0 &= (1-u_2)\cdot a_0 + u_2\cdot a_4 = \tilde{f}(0, 0, u_2)\\
d_1 &= (1-u_2)\cdot a_1 + u_2\cdot a_5 = \tilde{f}(1, 0, u_2)\\
d_2 &= (1-u_2)\cdot a_2 + u_2\cdot a_6 = \tilde{f}(0, 1, u_2)\\
d_3 &= (1-u_2)\cdot a_3 + u_2\cdot a_7 = \tilde{f}(1, 1, u_2)\\
\end{aligned}
$$

Then the Prover performs folding again on $d_0, d_1, d_2, d_3$ using $u_1$ as the folding factor to get $d_4, d_5$:

$$
\begin{aligned}
d_4 &= (1-u_1)\cdot d_0 + u_1\cdot d_2 = \tilde{f}(0, u_1, u_2)\\
d_5 &= (1-u_1)\cdot d_1 + u_1\cdot d_3 = \tilde{f}(1, u_1, u_2)\\
\end{aligned}
$$

Finally, the Prover performs folding on $d_4, d_5$ using $u_0$ as the folding factor to get $d_6$:

$$
d_6 = (1-u_0)\cdot d_4 + u_0\cdot d_5 = \tilde{f}(u_0, u_1, u_2)
$$

Observe that the end value $d_6$ of the vector $(d_0, d_1, d_2, d_3, d_4, d_5, d_6)$ happens to be $\tilde{f}(u_0, u_1, u_2)$, and the second-to-last and third-to-last elements happen to be $g^{(0)}(0), g^{(0)}(1)$:

$$
g^{(0)}(0) = d_4 \\
g^{(0)}(1) = d_5 \\
$$

If the Prover removes $d_6$ and folds the remaining vector $(d_0, d_1, d_2, d_3, d_4, d_5)$ along with $\vec{a}$ (using $r_0$ as the folding factor), we can get:

$$
\begin{aligned}
d'_0 &= (1-r_0)\cdot d_0 + r_0\cdot d_1 = \tilde{f}(r_0, 0, u_2) \\
d'_1 &= (1-r_0)\cdot d_2 + r_0\cdot d_3 = \tilde{f}(r_0, 1, u_2) \\
d'_2 &= (1-r_0)\cdot d_4 + r_0\cdot d_5 = \tilde{f}(r_0, u_1, u_2) \\
\end{aligned}
$$

We surprisingly find that $d'_2$ happens to be the value of $g^{(0)}(r_0)$, and $d'_0, d'_1$ happen to be the values of $g^{(1)}(0), g^{(1)}(1)$.

Next, in the second round of Sumcheck, the Prover folds $(d'_0, d'_1)$ along with $\vec{a}'$ using $r_1$ to get the value of $d''_0$:

$$
d''_0 = (1-r_1)\cdot d'_0 + r_1\cdot d'_1 = \tilde{f}(r_0, r_1, u_2)
$$

This happens to be the value of $g^{(1)}(r_1)$.

Then in the third round of Sumcheck, the Prover needs to send the values of $g^{(2)}(0), g^{(2)}(1)$, but the vector $\vec{d}$ has already been folded and disappeared. However, at this time, the Prover has the folded vector $\vec{a}$:

$$
\begin{aligned}
a^{(2)}_0 &= \tilde{f}^{(2)}(0) = \tilde{f}(r_0, r_1, 0) \\
a^{(2)}_1 &= \tilde{f}^{(2)}(1) = \tilde{f}(r_0, r_1, 1) \\
\end{aligned}
$$

These two values happen to be equal to the values of $g^{(2)}(0), g^{(2)}(1)$.

### Performance Analysis

To summarize, we only need to let the Prover pre-compute the vector $\vec{d}$ before Sumcheck starts. It stores all the intermediate results of $\tilde{f}(X_0, X_1, X_2)$ after Partial Evaluation by substituting $X_2=u_2, X_1=u_1, X_0=u_0$ in turn. And this vector is folded along with the vector $\vec{a}$ using the same random challenge numbers, so the values of $g^{(i)}(0), g^{(i)}(1), g^{(i)}(r_i)$ can be efficiently calculated. The pre-computation requires $2^n-1$ multiplications, and the folding requires a total of $2^n-2$ multiplications.

Prover's computation:

- Pre-compute $\vec{d}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Fold $\vec{a}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Fold $\vec{d}$: $2^n$ multiplications and $2\cdot 2^n$ additions

Verifier's computation:

- Verify $g^{(i)}(0), g^{(i)}(1)$: $n$ multiplications and $2n$ additions
- Calculate $g^{(i)}(r_i)$: $n$ multiplications and $2n$ additions

## Further Optimization of the Verifier 

In the above protocol, the Prover needs to send $g^{(i)}(0), g^{(i)}(1)$, then the Verifier verifies:

$$
g^{(i)}(0) +  (g^{(i)}(1) - g^{(i)}(0))\cdot u_i \overset{?}{=} g^{(i-1)}(r_{i-1}) = g^{(i)}(u_i)
$$

So actually, the Prover only needs to send one value $g^{(i)}(0)$ in each round of Sumcheck, then the Verifier can calculate $g^{(i)}(1)$ backwards based on the "verification equation":

$$
g^{(i)}(1) = \frac{g^{(i-1)}(r_{i-1}) - g^{(i)}(0)}{u_i} + g^{(i)}(0)
$$

This way, the Verifier uses one division calculation to exchange for a reduction in communication (by half). But note that the computational cost of finite field division (finding inverse) is significantly higher than multiplication, with a complexity of at least $o(\log{q})$. But anyway, we can further reduce the communication, i.e., the Proof size, through this method.

In fact, it's not hard to see that this relatively costly division can be optimized away. This idea comes from Deepfold []. We let the Prover send $g^{(i)}(u_i+1)$ instead of $g_i(0)$ or $g_i(1)$ in each round of Sumcheck:

$$
g^{(i)}(u_i+1) = g^{(i)}(u_i) + g^{(i)}(1) - g^{(i)}(0)
$$

Again, $g^{(i)}(u_i)$ is the tail element after each folding of the vector $\vec{d}$, so its computation cost is already included in the folding calculation of $\vec{d}$. Therefore, the Prover's cost is just two additional additions in each round.

Then, because the Verifier already has $g^{(i)}(u_{i})=g^{(i-1)}(r_{i-1})$ at this time, the Verifier can get $g^{(i)}(r_i)$ without division:

$$
g^{(i)}(r_i) = g^{(i)}(u_i) + \Big(g^{(i)}(u_i+1)-g^{(i)}(u_i)\Big)\cdot (r_i - u_i)
$$

The computational cost is only three additions and one multiplication.

### Performance Analysis

Prover's computation:

- Pre-compute $\vec{d}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Fold $\vec{a}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Fold $\vec{d}$: $2^n$ multiplications and $2\cdot 2^n$ additions
- Calculate $g^{(i)}(u_i+1)$: $2n$ additions

Verifier's computation:

- Calculate $g^{(i)}(r_i)$: $n$ multiplications and $3n$ additions

## Understanding Sumcheck Optimization from Another Perspective

After multiple steps of optimization above, we have reached a relatively ideal state. Let's see if we can understand this concise protocol more easily.

We can view the above optimized protocol as a Recursive Split-and-fold style sum proof. Because $\tilde{f}(u_0, u_1, u_2)$ itself is a sum of 8 terms:

$$
\begin{aligned}
\tilde{f}(u_0, u_1, u_2) &= a_0(1-u_0)(1-u_1)(1-u_2) + a_1u_0(1-u_1)(1-u_2) \\
&+ a_2(1-u_0)u_1(1-u_2) + a_3u_0u_1(1-u_2) \\
&+ a_4(1-u_0)u_1u_2 + a_5u_0(1-u_1)u_2 \\
&+ a_6u_0u_1(1-u_2) + a_7u_0u_1u_2  \\
& = (1-u_0)\cdot \Big(a_0(1-u_1)(1-u_2) + a_2u_1(1-u_2) + a_4(1-u_1)u_2 + a_6u_1u_2 \Big) \\
&+ u_0\cdot \Big(a_1(1-u_1)(1-u_2) + a_3u_1(1-u_2) + a_5(1-u_1)u_2 + a_7u_1u_2 \Big) \\
\end{aligned}
$$

In the first round, the Prover sends the sum of 4 terms in the left bracket and the sum of 4 terms in the right bracket, recorded as $g_0(0)$ and $g_0(1)$, and sends them to the Verifier:

$$
\begin{aligned}
g_0(0) &= a_0(1-u_1)(1-u_2) + a_2u_1(1-u_2) + a_4(1-u_1)u_2 + a_6u_1u_2 \\
g_0(1) &= a_1(1-u_1)(1-u_2) + a_3u_1(1-u_2) + a_5(1-u_1)u_2 + a_7u_1u_2 \\
\end{aligned}
$$

Or

$$
\begin{aligned}
g_0(0) &= \tilde{f}(0, u_1, u_2) \\
g_0(1) &= \tilde{f}(1, u_1, u_2) \\
\end{aligned}
$$

Then the Verifier first verifies whether the result of the inner product of $(g_0(0), g_0(1))$ and $(1-u_0, u_0)$ is equal to the sum $v$ to be proved,

$$
(1-u_0)\cdot g_0(0) + u_0\cdot g_0(1) \overset{?}{=} \tilde{f}(u_0, u_1, u_2)
$$

This way, the Prover and Verifier have reduced the proof of a sum of length 8 to two proofs of sums of length 4. And because these two new sums actually have the same structure, that is, they are both the result of the inner product of the odd and even term coefficients of the polynomial with the same vector $(1-u_1,u_1)\otimes(1-u_2,u_2)$,

$$
\begin{aligned}
g^{(0)}(0) &= \langle(a_0, a_2, a_4, a_6), (1-u_1, u_1)\otimes(1-u_2, u_2)\rangle \\
g^{(0)}(1) &= \langle(a_1, a_3, a_5, a_7), (1-u_1, u_1)\otimes(1-u_2, u_2)\rangle \\
\end{aligned}
$$

So the Verifier can give a random number $r_0$, using it to merge (Batching) these two new sum proofs together. Coincidentally, the merged sum value of length 4 happens to be $g^{(0)}(r_0)$, and it equals $\tilde{f}(r_0, u_1, u_2)$. Of course, this is not a coincidence, because we deliberately use $(1-r_0, r_0)$ this Multilinear Basis to fold $g^{(0)}(0), g^{(0)}(1)$, with the purpose of keeping it equal to $g^{(0)}(r_0)$:

$$
(1-r_0)\cdot g_0(0) + r_0\cdot g_0(1) = \tilde{f}(r_0, u_1, u_2)
$$

This way, the Prover and Verifier next prove that the sum value of the merged vector of length 4 equals $\tilde{f}(r_0, u_1, u_2)$, that is

$$
(1-r_0)\cdot g^{(0)}(0) + r_0\cdot g^{(0)}(1) \overset{?}{=} a'_0w'_0 + a'_1w'_1 + a'_2w'_2 + a'_3w'_3
$$

And so on, this protocol is consistent with the idea of the Sumcheck protocol, which is to split a sum equation into sums of different parts, and then use random numbers to merge these different sum segments together to prove. Until the last round, the sum proof is Reduced to the polynomial evaluation proof, and the Prover and Verifier use other tools to supplement the last part of the proof.

The original Sumcheck in Basefold protocol did not utilize the internal structure of the sum, but adopted a more general proof of inner product sum. Therefore, the concise protocol introduced in this article fully utilizes the internal structure of the sum terms.

## References 

- [GLH+24] Yanpei Guo, Xuanming Liu, Kexi Huang, Wenjie Qu, Tianyang Tao, and Jiaheng Zhang. "DeepFold: Efficient Multilinear Polynomial Commitment from Reed-Solomon Code and Its Application to Zero-knowledge Proofs." _Cryptology ePrint Archive_ (2024).
- [ACFY24] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "WHIR: Reed–Solomon Proximity Testing with Super-Fast Verification." _Cryptology ePrint Archive_ (2024).
- [ZCF23] Hadas Zeilberger, Binyi Chen, and Ben Fisch. "BaseFold: efficient field-agnostic polynomial commitment schemes from foldable codes." Annual International Cryptology Conference. Cham: Springer Nature Switzerland, 2024.
- [Hab24] Ulrich Haböck. "Basefold in the List Decoding Regime." _Cryptology ePrint Archive_(2024).