# Ligerito-PCS Notes

Yu Guo <yu.guo@secbit.io>

Last updated: 2025-06-05

Ligerito [NA25] is a multilinear extension (MLE) polynomial commitment scheme built on Ligero [AHIV17], employing a recursive proof strategy similar to the FRI protocol. After understanding the Ligerito protocol, I found that its recursive approach is similar to the FRI protocol, while the incorporation of a Partial Sumcheck protocol likely draws inspiration from Basefold. During the recursive process, the Sumcheck protocol can be merged with the Partial Sumcheck protocol from the previous iteration - an approach nearly identical to the handling of Shift Queries in the Whir protocol. In the Discussion section on page 13 of the paper, the authors write:

> Remco Bloemen and Giacomo Fenzi have commented that this protocol is structurally similar to the WHIR protocol of [ACFY24], though we note that Ligerito uses general linear codes, the logarithmic randomness of [DP24], and as far as we can tell, results in concretely different (and smaller) numbers in the unique decoding regime. A natural open question is whether there is a simple generalization of both protocols that can recast them in a common framework.

This article provides an overview of Ligerito's core ideas and compares them with the Whir protocol. Ultimately, I believe there is no substantial difference between the two protocols - despite their different design paths, their core processes are almost identical. Whir additionally incorporates an Out-of-domain Query step and tends to use larger domains to compute intermediate polynomial RS Codes during iterations, aiming to improve code rate and reduce query counts.

> Approach:
> 1. Review the Ligero protocol
> 2. The crucial role of Sumcheck
> 3. Recursive implementation


## 1. Ligero

Let's work through the Ligero protocol with a simple example to help readers quickly grasp the concept. We'll consider an MLE polynomial with just four variables, defined as:

$$
f(x_0, x_1, x_2, x_3) = \sum_{i=0}^{2^4-1} a_i \cdot eq(\mathsf{bits}(i), (x_0, x_1, x_2, x_3))
$$

where the vector $\vec{a}=(a_0, a_1, \cdots, a_{15})$ represents the evaluations of polynomial $f$ on the 4-dimensional Boolean Hypercube ($\{0, 1\}^4$).

### Computing the Commitment

We can rearrange the vector $\vec{a}$ into a $4\times 4$ matrix, denoted as $A$:

$$
A=
\begin{bmatrix}
a_0 & a_1 & a_2 & a_3 \\
a_4 & a_5 & a_6 & a_7 \\
a_8 & a_9 & a_{10} & a_{11} \\
a_{12} & a_{13} & a_{14} & a_{15}
\end{bmatrix}
$$

We use a linear code, $C[\mathbb{F}, 4, 8]$, with an associated generator matrix $G\in\mathbb{F}^{4\times 8}$, to encode each row of the matrix (this encoding scheme has a rate of $1/2$):

$$
\mathsf{enc}(a_0, a_1, a_2, a_3) = 
\begin{bmatrix}
a_0 & a_1 & a_2 & a_3
\end{bmatrix}
G
$$

We can choose RS Code or any linear code defined over the finite field $\mathbb{F}_q$.
In the encoding example above, $\mathsf{enc}(a_0, a_1, a_2, a_3)$ results in a row vector of length 8, which we'll denote as $(e_0, e_1, e_2, e_3, e_4, e_5, e_6, e_7)$. Similarly, we encode all rows of A using $G$ to compute the encoded matrix $B$ of size $4\times 8$:

$$
B= AG =
\begin{bmatrix}
e_0 & e_1 & e_2 & e_3 & e_4 & e_5 & e_6 & e_7 \\
e_8 & e_9 & e_{10} & e_{11} & e_{12} & e_{13} & e_{14} & e_{15} \\
e_{16} & e_{17} & e_{18} & e_{19} & e_{20} & e_{21} & e_{22} & e_{23} \\
e_{24} & e_{25} & e_{26} & e_{27} & e_{28} & e_{29} & e_{30} & e_{31}
\end{bmatrix}
$$

Like any hash-based PCS protocol, we use a Merkle Tree to compute the commitment of $B$. Importantly, we use a column-wise approach to commit to $B$. First, we treat each column of the matrix as a leaf node of a Merkle Tree, then compute its root. This gives us 8 Merkle Tree roots for the matrix $B$:

$$
\begin{aligned}
\mathsf{t}_0 &= \mathsf{MerkleRoot}(e_0, e_8, e_{16}, e_{24}) \\
\mathsf{t}_1 &= \mathsf{MerkleRoot}(e_1, e_9, e_{17}, e_{25}) \\
\vdots \\
\mathsf{t}_7 &= \mathsf{MerkleRoot}(e_7, e_{15}, e_{23}, e_{31}) \\
\end{aligned}
$$

We then use these 8 roots as leaf nodes of a new Merkle Tree and compute their root:

$$
\mathsf{t} = \mathsf{MerkleRoot}(\mathsf{t}_0, \mathsf{t}_1, \cdots, \mathsf{t}_7)
$$

Finally, $\mathsf{t}$ is our commitment to $B$. Of course, this commitment computation method can also be viewed as flattening matrix $B$ column-by-column into a one-dimensional vector of length 32, treating these as leaf nodes of a Merkle Tree, and computing its root to obtain the same value $\mathsf{t}$.

### Proving Correctness of Evaluation at a Random Point

The Prover can commit to an MLE polynomial using the method above and send the commitment $\mathsf{t}$ to the Verifier. Then the Verifier can randomly choose a point $(r_0, r_1, r_2, r_3)$ and send it to the Prover. The Prover returns a value $v$ along with a proof $\pi_{eval}$ proving the correctness of the evaluation:

$$
\pi_{eval}: v=f(r_0, r_1, r_2, r_3)
$$

Let's quickly go through the Ligero approach:

**Step 1**: The Prover computes $B$ and its commitment $\mathsf{t}$, then sends it to the Verifier.

**Step 2**: The Verifier randomly selects a point $(r_0, r_1, r_2, r_3)\in\mathbb{F}_q^{4}$ and sends it to the Prover.

**Step 3**: The Prover uses $r_3, r_2$ to perform a "vertical folding" of all "rows" in matrix $A$, and sends the calculated folded row vector $\vec{a}'$:

$$
\vec{a}' = 
\begin{bmatrix}
(1-r_2)(1-r_3) & r_2(1-r_3) & r_3(1-r_2) & r_2r_3 \\
\end{bmatrix}
\begin{bmatrix}
a_0 & a_1 & a_2 & a_3 \\
a_4 & a_5 & a_6 & a_7 \\
a_8 & a_9 & a_{10} & a_{11} \\
a_{12} & a_{13} & a_{14} & a_{15}
\end{bmatrix}
$$

Note that while the matrix has 4 rows, the Prover only needs two random numbers to fold them. This is because we can use $k$ random numbers to construct $2^k$ linearly independent values:

$$
\bar{r} = (1-r_2, r_2) \otimes (1-r_3, r_3)
$$

We use the notation $\bar{r}$ from the Ligerito paper to represent a vector of $n$ linearly independent values constructed from $\log{n}$ random factors - an approach from [DP24]. Here, $\otimes$ represents the Kronecker product. Expanded, $\bar{r}$ can be written as:

$$
\bar{r} = 
\begin{bmatrix}
(1-r_2)(1-r_3) & 
(1-r_2)r_3 &
r_2(1-r_3) &
r_2r_3
\end{bmatrix}
$$

If the mathematical notation is difficult to understand, let me explain the calculation of $\vec{a}'$ more intuitively.

I'll introduce a new notation $\mathsf{fold}(r, \vec{c})$, which represents folding a column vector $\vec{c}$ using a random number $r$:

$$
\mathsf{fold}(r, (c_0,c_1,c_2,\ldots, c_7)^T) = 
\begin{bmatrix}
(1-r)\cdot c_0 + r\cdot c_4 \\
(1-r)\cdot c_1 + r\cdot c_5 \\
(1-r)\cdot c_2 + r\cdot c_6 \\
(1-r)\cdot c_3 + r\cdot c_7
\end{bmatrix}
=\begin{bmatrix}
c_0' \\
c_1' \\
c_2' \\
c_3'
\end{bmatrix}
=\vec{c}'
$$

This fold function can be understood as splitting the vector in half, multiplying the first half by the factor $(1-r)$, the second half by $r$, then adding the corresponding elements to obtain a column vector half as long.

If we continue folding the resulting vector $\vec{c}'=(c_0', c_1', c_2', c_3')^T$ with a new random number $r'$, we get:

$$
\mathsf{fold}(r', \vec{c}') = 
\begin{bmatrix}
(1-r')\cdot c_0' + r'\cdot c_2' \\
(1-r')\cdot c_1' + r'\cdot c_3' \\
\end{bmatrix}
= 
\begin{bmatrix}
(1-r')(1-r)\cdot c_0 + (1-r')r\cdot c_4 + r'(1-r)\cdot c_2 + r'r\cdot c_6 \\
(1-r')(1-r)\cdot c_1 + (1-r')r\cdot c_5 + r'(1-r)\cdot c_3 + r'r\cdot c_7 \\
\end{bmatrix}
= \vec{c}''
$$

If we allow $\mathsf{fold}$ to be composable, we can express composite folding as:

$$
\mathsf{fold}(r', r, \vec{a}) = \mathsf{fold}(r', \mathsf{fold}(r, \vec{a}))
= \vec{a}''
$$

Continuing our example, we can express the calculation of $\vec{a}'$ using the $\mathsf{fold}$ function:

$$
\vec{a}' = 
\begin{bmatrix}
\mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\mathsf{fold}(r_2, r_3, (a_1, a_5, a_9, a_{13})) \\
\mathsf{fold}(r_2, r_3, (a_2, a_6, a_{10}, a_{14})) \\
\mathsf{fold}(r_2, r_3, (a_3, a_7, a_{11}, a_{15}))
\end{bmatrix}
$$

**Step 4**: The Verifier samples $Q\subset\{0, 1, 2, \ldots, 7\}$ and sends it to the Prover.

$$
Q = \{q_0, q_1, \ldots, q_{l-1}\}
$$

The Verifier's random sampling aims to check whether the Prover honestly calculated $\vec{a}'$ using the $\mathsf{fold}(r2,r_3,\cdot)$ function. Due to the remarkable "Proximity Gap" property of linear coding, a folded linear code is either still a correct code or, with high probability, far from any correct code. This distance between codes is measured by the Hamming Distance. Thus, the Verifier can check the correctness of the folding process by sampling just a few positions in the codeword. Of course, more sampling is more secure, but increases the proof size. We can determine the minimum number of samples needed to ensure security using probability formulas. Let's denote the number of samples as $l$.

**Step 5**: The Prover responds to the Verifier's random sampling by sending, for each query point $q_i \in Q$, the column vector $\vec{b}_{q_i}$ of $B$, along with its corresponding Merkle Tree root $\mathsf{t}_{q_i}$, and the Merkle Path $\pi_{q_i}$ from $\mathsf{t}_{q_i}$ to $\mathsf{t}$.

For example, if $q_0=2$, the Prover would send $(e_2, e_{10}, e_{18}, e_{26})$, their Merkle Root $\mathsf{t}_{2}$, and the Merkle Path from $\mathsf{t}_{2}$ to $\mathsf{t}$.

**Verification Step**: The Verifier needs to check if the following equations hold:

1. All $\mathsf{t}_{q_i}$ are consistent with $\mathsf{t}$:
$$
\mathsf{t}_{q_i} \overset{?}{=} \mathsf{MerkleRoot}(\vec{b}_{q_i}), \quad \forall q_i\in Q
$$

2. Each $t_{q_i}$ is a leaf of $\mathsf{t}$:

$$
\mathsf{MerkleTree.verify}(\mathsf{t}, \mathsf{t}_{q_i}, \pi_{q_i}) \overset{?}{=} 1, \quad \forall q_i\in Q
$$

3. The folding of $\vec{b}_{q_i}$ is consistent with the corresponding point of encoded $\vec{a}'G$:

$$
\mathsf{fold}(r_2, r_3,\vec{b}_{q_i}) \overset{?}{=} \vec{a}'^TG_{q_i}, \quad \forall q_i\in Q
$$

where $G_{q_i}$ represents the $q_i$-th column of the generator matrix $G$.

4. Verify the vector $\vec{a}'$:

$$
\vec{a}'^T\cdot\big((1-r_0,r_0)\otimes(1-r_1,r_1)\big)\overset{?}{=}v
$$

If all four verification steps pass, the Verifier accepts the proof:

$$
\pi_{eval}:f(r_0, r_1, r_2, r_3) = v
$$

## 2. The Crucial Role of Sumcheck

The protocol in the previous section has an obvious limitation: the Verifier must provide the evaluation point only after the Prover has committed to polynomial $f$, and this point must be sufficiently random - it cannot be a predetermined public point. This means the protocol doesn't satisfy the general application scenarios of polynomial commitments, where we want to support MLE polynomial evaluation at arbitrary, even non-random points.

This is where we need to introduce the Sumcheck protocol. Specifically, by adding a **partially executed** Sumcheck sub-protocol to the Ligero protocol, we can complete an evaluation proof for an MLE polynomial at any arbitrary point. This approach actually originated from Basefold [ZCF23]. I assume readers are already familiar with the Sumcheck protocol, or please refer to our previous articles. (TODO)

We'll continue with our four-variable MLE polynomial $f$, but now we want the Prover to prove $f$'s evaluation at an arbitrary point $\vec{u}=(u_0, u_1, u_2, u_3)$. According to the definition of MLE polynomials, it can be uniquely represented as an interpolation polynomial of $(a_0, a_1, a_2, \ldots, a_{15})$ over the Boolean Hypercube:

$$
f(u_0, u_1, u_2, u_3) = \sum_{\vec{b}\in\{0,1\}^4} f(b_0,b_1,b_2,b_3) \cdot eq\big((b_0, b_1, b_2, b_3), (u_0, u_1, u_2, u_3)\big)
$$

To emphasize: $\vec{u}=(u_0, u_1, u_2, u_3)$ is an arbitrary predetermined point. The $eq(\vec{b}, \vec{u})$ in the equation above is a Lagrange polynomial, defined as:

$$
eq(\vec{b}, \vec{u}) = \prod_{i=0}^{n-1} \big((1-b_i)(1-u_i) + b_i\cdot u_i\big)
$$

where $n$ represents the dimension of the BooleanHypercube, here $n=4$. If we fix $\vec{b}\in\{0,1\}^4$, we'll introduce a notation $w_i$ to represent $eq(\mathsf{bits}(i), \vec{u})$:

$$
w_i = eq(\mathsf{bits}(i), (u_0, u_1, u_2, u_3))
$$

At this point, we can see that the following equation holds:

$$
f(u_0, u_1, u_2, u_3) = \sum_{i=0}^{2^4-1} a_i \cdot w_i
$$

As mentioned earlier, $\vec{a}=(a_0, a_1, a_2, \ldots, a_{15})$ represents $f$'s values on the 4-dimensional Boolean Hypercube:

$$
\vec{a} = \begin{bmatrix}
f(0,0,0,0) \\
f(1,0,0,0) \\
f(0,1,0,0) \\
f(1,1,0,0) \\
\vdots \\
f(1,1,1,1)
\end{bmatrix}
$$

That is:

$$
a_i=f(\mathsf{bits})
$$

Since $f(u_0, u_1, u_2, u_3)$ can be expressed as a sum, specifically the inner product of $\vec{a}$ and $\vec{w}$, we can consider using the Sumcheck protocol to prove this inner product operation:

$$
f(u_0, u_1, u_2, u_3) = \sum_{\vec{b}\in\{0,1\}^4} f(b_0, b_1, b_2, b_3) \cdot \tilde{w}(b_0, b_1, b_2, b_3)
$$

where $\tilde{w}$ is the MLE polynomial corresponding to $\vec{w}$. One round of the Sumcheck protocol can reduce the above inner product equation to an inner product equation of half the length. For example, after just one round of Sumcheck protocol between Prover and Verifier, we get a sum equation of length 8:

$$
f(u_0, u_1, u_2, {\color{red}r_3}) = \sum_{\vec{b}\in\{0,1\}^3} f(b_0, b_1, b_2, {\color{red}r_3}) \cdot \tilde{w}(b_0, b_1, b_2, {\color{red}r_3})
$$

Here $r_3$ is a challenge value randomly generated by the Verifier during the first round of Sumcheck interaction. If we go another round, the length of this sum equation will be halved again:

$$
f(u_0, u_1, {\color{red}r_2}, r_3) = \sum_{\vec{b}\in\{0,1\}^2} f(b_0, b_1, {\color{red}r_2}, r_3) \cdot \tilde{w}(b_0, b_1, {\color{red}r_2}, r_3)
$$

At this point, the $f(X_0, X_1, r_2, r_3)$ on the right side of the sum equation can be viewed as an MLE polynomial in terms of $X_0,X_1$, whose values on the Boolean Hypercube form a vector of length 4, with each element being a random linear combination of matrix $A$ based on $r_2, r_3$ (expanding by Multilinear Basis):

$$
\begin{bmatrix}
f(0,0,r_2,r_3) \\
f(0,1,r_2,r_3) \\
f(1,0,r_2,r_3) \\
f(1,1,r_2,r_3)
\end{bmatrix}
= 
\begin{bmatrix}
\mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\mathsf{fold}(r_2, r_3, (a_1, a_5, a_9, a_{13})) \\
\mathsf{fold}(r_2, r_3, (a_2, a_6, a_{10}, a_{14})) \\
\mathsf{fold}(r_2, r_3, (a_3, a_7, a_{11}, a_{15}))
\end{bmatrix}
$$

We can use the first element of the vector, $f(0,0,r_2,r_3)$, as an example to derive why the above equation holds:

$$
\begin{aligned}
f(0,0,r_2,r_3) &= \sum_{i=0}^{3} a_i \cdot eq(\mathsf{bits}(i), (0,0,r_2,r_3)) \\
&= f(0,0,0,0) \cdot eq(\mathsf{bits}(0), (0,0,r_2,r_3)) + f(0,0,1,0) \cdot eq(\mathsf{bits}(4), (0,0,r_2,r_3)) \\
& + f(0,0,0,1) \cdot eq(\mathsf{bits}(8), (0,0,r_2,r_3)) + f(0,0,1,1) \cdot eq(\mathsf{bits}(12), (0,0,r_2,r_3)) \\
&= a_0 \cdot eq(\mathsf{bits}(0), (r_2,r_3)) + a_4 \cdot eq(\mathsf{bits}(1), (r_2,r_3)) \\
& + a_8 \cdot eq(\mathsf{bits}(2), (r_2,r_3)) + a_{12} \cdot eq(\mathsf{bits}(3), (r_2,r_3)) \\
& = a_0 \cdot eq(0,r_2)eq(0,r_3) + a_4 \cdot eq(1,r_2)eq(0,r_3) + a_8 \cdot eq(0,r_2)eq(1,r_3) + a_{12} \cdot eq(1,r_2)eq(1,r_3) \\
& = eq(0,r_2)\cdot \Big(a_0 \cdot eq(0,r_3) + a_8 \cdot eq(1,r_3)\Big) + eq(1,r_2)\cdot \Big(a_4 \cdot eq(0,r_3) + a_{12} \cdot eq(1,r_3)\Big) \\
&=eq(0,r_2)\cdot \Big(\mathsf{fold}(r_3,(a_0,a_8))\Big) + eq(1,r_2)\cdot \Big(\mathsf{fold}(r_3,(a_4,a_{12}))\Big) \\
&= \mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\end{aligned}
$$

All four values together are exactly the vector $\vec{a}'$ produced by folding $A$ as described in the previous section's protocol. However, unlike the previous protocol, here $r_2, r_3$ are not directly randomly generated by the Verifier, but are generated by the Verifier during a Sumcheck protocol execution. The purpose of this Sumcheck protocol is to prove the correctness of an evaluation at an arbitrary point $f(u_0, u_1, u_2, u_3)$.

In other words, the utility of the Sumcheck protocol is that it can prove the evaluation of an MLE polynomial at any public point, transforming it into the evaluation of $f$ at a random point. The transformed proof target can then be completed using the protocol from the previous section. This random number is effectively reused twice. However, it's worth noting that we don't run all rounds of the Sumcheck protocol, but stop here, leaving the remaining unproven sum equation for the Verifier to verify directly.

At this point, the Prover only needs to send $\vec{a}'$ directly to the Verifier, who then has two verification tasks: first, check if $\vec{a}'\cdot (1-u_0,u_0)\otimes(1-u_1,u_1)$ equals $\tilde{f}(u_0, u_1, r_2, r_3)$; second, randomly check if $\vec{a}'$ is indeed the result of folding matrix $A$ using $r_2, r_3$.

Below, I provide the protocol flow, which readers can understand in conjunction with the explanation above.

### Protocol Flow

**Public Input**: $\mathsf{t}$, $\vec{u}=(u_0, u_1, u_2, u_3)$

**Witness**: $\vec{a}=(a_0, a_1, a_2, \ldots, a_{15})$

#### Commitment:

The Prover computes the encoded matrix $B=AG$:

$$
B = \begin{bmatrix}
\mathsf{enc}(a_0, a_1, a_2, a_3) \\
\mathsf{enc}(a_4, a_5, a_6, a_7) \\
\mathsf{enc}(a_8, a_9, a_{10}, a_{11}) \\
\mathsf{enc}(a_{12}, a_{13}, a_{14}, a_{15})
\end{bmatrix}
=
\begin{bmatrix}
e_0 & e_1 & e_2 & e_3 & e_4 & e_5 & e_6 & e_7 \\
e_8 & e_9 & e_{10} & e_{11} & e_{12} & e_{13} & e_{14} & e_{15} \\
e_{16} & e_{17} & e_{18} & e_{19} & e_{20} & e_{21} & e_{22} & e_{23} \\
e_{24} & e_{25} & e_{26} & e_{27} & e_{28} & e_{29} & e_{30} & e_{31}
\end{bmatrix}
$$

Then calculates the Merkle Tree root for each column of matrix $B$:
$$
\begin{aligned}
\mathsf{t}_0 &= \mathsf{MerkleRoot}(e_0, e_8, e_{16}, e_{24}) \\
\mathsf{t}_1 &= \mathsf{MerkleRoot}(e_1, e_9, e_{17}, e_{25}) \\
\vdots \\
\mathsf{t}_7 &= \mathsf{MerkleRoot}(e_7, e_{15}, e_{23}, e_{31}) \\
\end{aligned}
$$

Finally calculates a Merkle Tree from these roots to get a single root $\mathsf{t}$:

$$
\mathsf{t} = \mathsf{MerkleRoot}(\mathsf{t}_0, \mathsf{t}_1, \cdots, \mathsf{t}_7)
$$

#### Evaluation Proof

**Step 1**: The Prover and Verifier conduct the first round of the Sumcheck protocol: Prover sends $h^{(0)}(X)$

$$
h^{(0)}(X) = f(u_0, u_1, u_2, X) = \sum_{\vec{b}\in\{0,1\}^3} \tilde{a}(b_0, b_1, b_2, X) \cdot \tilde{w}(b_0, b_1, b_2, X)
$$

**Step 2**: Verifier sends a random number $r_3\in\mathbb{F}$ and checks the following equation:

$$
f(u_0, u_1, u_2, u_3)\overset{?}{=}h^{(0)}(0)+h^{(0)}(1)
$$

**Step 3**: Prover sends $h^{(1)}(X)$

$$
h^{(1)}(X) =f(u_0, u_1, X, r_3) = \sum_{\vec{b}\in\{0,1\}^2} \tilde{a}(b_0, b_1, X, r_3) \cdot \tilde{w}(b_0, b_1, X, r_3)
$$

**Step 4**: Verifier sends a random number $r_2\in\mathbb{F}_q$ and checks the following equation:

$$
h^{(0)}(r_3) = f(u_0, u_1, u_2, r_3) \overset{?}{=}h^{(1)}(0)+h^{(1)}(1)
$$

**Step 5**: Prover stops the Sumcheck protocol and sends the folded vector $\vec{a}'$:

$$
\vec{a}' = \begin{bmatrix}
\mathsf{fold}(r_2, r_3, (a_0, a_4, a_8, a_{12})) \\
\mathsf{fold}(r_2, r_3, (a_1, a_5, a_9, a_{13})) \\
\mathsf{fold}(r_2, r_3, (a_2, a_6, a_{10}, a_{14})) \\
\mathsf{fold}(r_2, r_3, (a_3, a_7, a_{11}, a_{15}))
\end{bmatrix}
$$

**Step 6**: Verifier samples $Q\subset\{0, 1, 2, \ldots, 7\}$ and sends it to the Prover, where $|Q|=l$

$$
Q = \{q_0, q_1, \ldots, q_{l-1}\}
$$

**Step 7**: Prover sends, for each query point $q_i \in Q$, the column vector $\vec{b}_{q_i}$ of encoded matrix $B$, along with its corresponding Merkle Tree root $\mathsf{t}_{q_i}$, and the Merkle Path $\pi_{q_i}$ from $\mathsf{t}_{q_i}$ to $\mathsf{t}$.

Verification Step: The Verifier checks if the following equations hold:

1. All $\mathsf{t}_{q_i}$ are consistent with $\mathsf{t}$:
$$
\mathsf{t}_{q_i} = \mathsf{MerkleRoot}(\vec{b}_{q_i}), \quad \forall q_i\in Q
$$

2. Each $t_{q_i}$ is a leaf of $\mathsf{t}$:
$$
\mathsf{MerkleTree.verify}(\mathsf{t}, \mathsf{t}_{q_i}, \pi_{q_i}) = 1, \quad \forall q_i\in Q
$$

3. The folding of $\vec{b}_{q_i}$ is consistent with the corresponding point of encoded $\vec{a}'^T G$:
$$
\mathsf{fold}(r_2, r_3,\vec{b}_{q_i}) \overset{?}{=} \vec{a}'^T G_{q_i}, \quad \forall q_i\in Q
$$
where $G_{q_i}$ is the $q_i$-th column of the generator matrix.

4. Check the inner product of vectors:
$$
\vec{a}'\cdot\tilde{w}(u_0, u_1, r_2, r_3)\overset{?}{=}h^{(1)}(r_2) = \tilde{f}(u_0, u_1, r_2, r_3)
$$

## 3. Recursive Implementation

Let's introduce a new polynomial $f'(X_0, X_1)$ to represent the polynomial of length $2^2$ obtained after partially evaluating $f(X_0, X_1, X_2, X_3)$ with $X_2=r_2, X_3=r_3$:

$$
f'(X_0, X_1) = f(X_0, X_1, r_2, r_3)
$$

Starting from **Step 5** in the previous section's protocol, the Prover and Verifier are effectively proving:

$$
f'(u_0, u_1) = h^{(1)}(r_2)
$$

And it's easy to verify that the values of $f'(X_0, X_1)$ on the 2-dimensional Boolean Hypercube are exactly $\vec{a}'=(a'_0, a'_1, a'_2, a'_3)$:

$$
\begin{aligned}
f'(X_0, X_1) &= f(X_0, X_1, r_2, r_3) \\
&= a'_0\cdot\tilde{w}(X_0, X_1, r_2, r_3) + a'_1\cdot\tilde{w}(X_0, X_1, r_2, r_3) + a'_2\cdot\tilde{w}(X_0, X_1, r_2, r_3) + a'_3\cdot\tilde{w}(X_0, X_1, r_2, r_3)
\end{aligned}
$$

However, this proof process is compressed: the Prover simply sends the polynomial representation (i.e., $\vec{a}'$ as the Evaluation Form of $f'$) directly to the Verifier, who performs the inner product calculation to complete the verification.

Note! We can approach this differently. The first half of the protocol described in the previous section effectively transforms the verification target (step 4 of the verification):

$$
f(u_0, u_1, u_2, u_3) \overset{?}{=} v
$$

into the following proof target:

$$
f'(u_0, u_1) = f(u_0, u_1, r_2, r_3) \overset{?}{=} h^{(1)}(r_2)
$$

That is, proving the correctness of evaluating the MLE polynomial $f'(X_0, X_1)$ at the point $(u_0, u_1)$. Although the new target is still an MLE evaluation proof, the polynomial length has been reduced from 16 to 4.

Therefore, we can have the Prover and Verifier recursively invoke the protocol from the previous section, continuing to reduce this MLE evaluation proof $f'(u_0, u_1)=v'$ to an even smaller proof target, until the new polynomial is short enough for the Verifier to easily verify.

Looking at the third item in the verification step, the Verifier is checking $l$ inner product calculations:
$$
\mathsf{fold}(r_2, r_3,\vec{b}_{q}) \overset{?}{=} \vec{a}'G_{q}, \quad \forall q\in Q
$$

Note that the left side of the equation can be calculated by the Verifier, and the right side is an inner product of a vector of length $N/N'$. Let's introduce the symbol $N$ to represent the length of polynomial $f$, $N=2^n$, where $n$ is the number of variables; and the symbol $N'$ to indicate that we organize $f$'s Evaluations over the boolean hypercube into an $N'\times N_1$ matrix. It's easy to verify that after one protocol call, the length of the folded vector $\vec{a}'$ sent by the Prover is $N_1=N/N'$.

The matrix multiplication on the right can be broken down into $l$ vector inner product calculations, so this process can still use the Sumcheck protocol, allowing the Prover to handle it and further reducing the Verifier's computational load.
Moreover, this Sumcheck protocol can be merged with the Sumcheck protocol in the next recursive call, further reducing the Verifier's computational burden. This idea of merging Sumcheck protocols first appeared in Whir [ACFY24], and I suspect the authors of Ligerito [NA25] likely arrived at this idea independently.

### Recursive Protocol Flow

Let's assume the initial MLE polynomial is $f^{(0)}(X_0, X_1, \cdots, X_{n-1})$ with length $N=2^n$.

The first protocol call folds the evaluation form of the polynomial into an $N'\times N_1$ matrix, denoted as $A_0$, where $N_1=2^{n_1}$, $N'=2^{n_0}$, satisfying $n_0 + n_1 = n$, i.e., $N_1\cdot N'=N$.

$$
A_0 = \begin{bmatrix}
a_0 & a_1 & \cdots & a_{N_1-1} \\
a_{N_1} & a_{N_1+1} & \cdots & a_{2N_1-1} \\
\vdots & \vdots & \ddots & \vdots \\
a_{(N_1-1)N'} & a_{(N_1-1)N'+1} & \cdots & a_{N-1}
\end{bmatrix}
$$

The commitment calculation is:

$$
B_0 = A_0G_1 = \begin{bmatrix}
b_0 & b_1 & \cdots & b_{N_1-1} \\
b_{N_1} & b_{N_1+1} & \cdots & b_{2N_1-1} \\
\vdots & \vdots & \ddots & \vdots \\
b_{N'-1} & b_{N'-1+1} & \cdots & b_{N-1}
\end{bmatrix}
$$

$$
\mathsf{t}^{(0)} = \mathsf{MerkleRoot}(\mathsf{t}_0, \mathsf{t}_1, \cdots, \mathsf{t}_{N_1-1})
$$

**Public Input**:

1. $\vec{u}=(u_0, u_1, \cdots, u_{n_1-1}, u_{n_1}, u_{n_1+1}, \cdots, u_{n-1})$
2. $\mathsf{t}^{(0)}$

**Protocol Loop**: $i=0, 1, \cdots, l-1$, where variable $i$ represents the recursion layer.
 
**Loop Step 1**: If $i=0$, the Prover skips directly to Loop Step 2;

If $i\neq 0$, Prover commits to $f^{(i)}$ by arranging it into an $N'\times N_i$ matrix, denoted as $A^{(i)}$, calculates its encoded matrix $B^{(i)}$ and the Merkle Tree root $\mathsf{t}^{(i)}$. Prover sends $\mathsf{t}^{(i)}$.

**Loop Step 2**: Prover and Verifier perform $k=\log_2(N')$ rounds of the Sumcheck protocol. During the protocol, the Verifier sequentially sends random numbers $r^{(i)}_{k-1}, r^{(i)}_{k-2}, \cdots, r^{(i)}_{0}$, and finally the Prover sends the polynomial $h^{(i)}(X)$, satisfying:
$$
h^{(i)}(X) = \tilde{f}^{(i)}(u_0, u_1, u_{n_1-1}, X, r^{(i)}_{1},\ldots, r^{(i)}_{k-1}) = \sum_{\vec{b}\in\{0,1\}^{n_1}} \tilde{a}^{(i)}(\vec{b}, X) \cdot \tilde{w}^{(i)}(\vec{b}, X)
$$

And $h^{(i)}(r^{(i)}_{0})$ is the evaluation of $\tilde{f}^{(i+1)}$ at the point $(u_0, u_1, \cdots, u_{n_i-1})$, denoted as $v^{(i+1)}$:

$$
v^{(i+1)}= h^{(i)}(r^{(i)}_{0}) = \tilde{f}^{(i+1)}(u_0, u_1, \cdots, u_{n_i-1})
$$

It's easy to derive that $v^{(i+1)}$ is the inner product of the folded vector $\vec{a}^{(i+1)}$ and $\vec{w}^*$:

$$
v^* = \vec{a}^{(i+1)}\cdot\vec{w}^*
$$

Here:
$$
\vec{a}^{(i+1)} = \mathsf{fold}((r^{(i)}_{0}, r^{(i)}_{1}, \cdots, r^{(i)}_{k-1}), \vec{a}^{(i)})
$$

$$
\vec{w}^*= \mathsf{fold}((r^{(i)}_{0}, r^{(i)}_{1}, \cdots, r^{(i)}_{k-1}), \vec{w}^{(i)})
$$

Note that we're not rushing to use the symbol $w^{(i+1)}$ here, as the vector $\vec{w}^*$ is just an intermediate result that will later be merged with other vectors.

**Loop Step 3**: Verifier samples $Q\subset\{0, 1, 2, 3\}$ and sends it to the Prover. The number $|Q|$ is predetermined by the protocol security parameter:

$$
Q = \{q_0, q_1, \ldots, q_{|Q|-1}\}
$$

**Loop Step 4**: For each query point $q\in Q$, the Prover sends the column vector $\vec{b}_{q}$ of the encoded matrix $B$, along with its corresponding Merkle Tree root $\mathsf{t}^{(i)}_{q}$, and the Merkle Path $\pi^{(i)}_{q}$ from $\mathsf{t}^{(i)}_{q}$ to $\mathsf{t}^{(i)}$.

**Loop Step 5**: The Verifier checks if the following equations hold:

1. All $\mathsf{t}^{(i)}_{q}$ are consistent with $\mathsf{t}^{(i)}$:
$$
\mathsf{t}^{(i)}_{q} = \mathsf{MerkleRoot}(\vec{b}_{q}), \quad \forall q\in Q
$$

2. Each $\mathsf{t}^{(i)}_{q}$ is a leaf of $\mathsf{t}^{(i)}$:
$$
\mathsf{MerkleTree.verify}(\mathsf{t}^{(i)}, \mathsf{t}^{(i)}_{q}, \pi^{(i)}_{q}) = 1, \quad \forall q\in Q
$$

**Loop Step 6**: For each $q\in Q$, the Prover calculates the inner product of $\vec{a}^{(i+1)}$ and vector $G^{(i)}_q$, denoted as $y^{(i)}_q$, and sends it to the Verifier:

$$
y^{(i)}_q = \vec{a}^{(i+1)}\cdot G^{(i)}_q
$$

Here, $G^{(i)}_q$ is the $q$-th column of the generator matrix $G^{(i)}$ of the linear code $C[\mathbb{F}_q,N_i, \mathcal{R}N_i]$.

**Loop Step 7**: The Verifier sends a random number $\beta^{(i)}$ to combine the $y^{(i)}_q$ with the inner product sum $v^*$ from Step 2. The new sum value is:

$$
{v}^{(i+1)} =v^* + \beta^{(i)}\cdot y^{(i)}_0 + {\beta^{(i)}}^2\cdot y^{(i)}_1 + \cdots + {\beta^{(i)}}^{|Q|}\cdot y^{(i)}_{|Q|-1}
$$

If the Prover is honest, this should be the inner product of the following two vectors:

$$
\vec{w}^{(i+1)} = \vec{w}^* + \beta^{(i)}\cdot G^{(i)}_{q_0} + {\beta^{(i)}}^2\cdot G^{(i)}_{q_1} + \cdots + {\beta^{(i)}}^{|Q|}\cdot G^{(i)}_{q_{|Q|-1}}
$$

where $G_{q_i}$ is the $q_i$-th column of the generator matrix.

**Loop Termination Step**: If $n_i \leq n'$, the Prover and Verifier end the loop; otherwise, they return to **Loop Step 1**, setting $i\leftarrow i+1$.

**Outside Loop Step 1**: The Prover directly sends $\vec{a}^{(l)}$ to the Verifier.

**Outside Loop Step 2**: The Verifier calculates $\vec{w}^{(l)}$ and checks the following equation:

$$
v^{(l)} \overset{?}{=} \vec{a}^{(l)}\cdot\vec{w}^{(l)}
$$

**Protocol Complete**.

Note that $\vec{a}^{(l)}$ and $\vec{w}^{(l)}$ are both vectors of length $N_l$.

## 4. Reducing the Verifier's Computational Load

In Step 7 of the above protocol, the complexity of calculating $\vec{w}^{(i+1)}$ is related to the length of $\vec{w}^*$. If the Verifier directly calculates according to the formula in Step 7, the computational complexity will be $O(|Q|\cdot N)$, which clearly doesn't meet the Succinctness requirement.

The paper [NA25] discusses that if the linear code is a special type where each column of the generator matrix has a Tensor Structure, then the Verifier can calculate $\vec{w}^{(l)}$ in exponential time complexity.

The main idea is that if two vectors $\vec{r}$ and $\vec{w}$ both have a Tensor Structure:

$$
\begin{aligned}
\vec{r} &= r_0 \otimes r_1 \otimes \cdots \otimes r_{k-1} \\
\vec{w} &= w_0 \otimes w_1 \otimes \cdots \otimes w_{k-1} \\
\end{aligned}
$$

Then the inner product of $\vec{r}$ and $\vec{w}$ can be expressed as:

$$
\vec{r}\cdot\vec{w} = \prod_{i=0}^{k-1} r_i \cdot w_i
$$

## References 

- [NA25] Andrija Novakovic and Guillermo Angeris. Ligerito: A Small and Concretely Fast Polynomial Commitment Scheme. 2025. https://angeris.github.io/papers/ligerito.pdf.
- [ACFY24] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi and Eylon Yogev. WHIR: Reed–Solomon Proximity Testing with Super-Fast Verification. 2024. https://eprint.iacr.org/2024/1586.pdf
- [DP23] Benjamin Diamond and Jim Posen. Proximity Testing with Logarithmic Randomness. 2023. https://eprint.iacr.org/2023/630.pdf
- [AHIV17] Scott Ames, Carmit Hazay, Yuval Ishai, and Muthuramakrishnan Venkitasubramaniam. Ligero: lightweight sublinear arguments without a trusted setup". 2022. https://eprint.iacr.org/2022/1608.pdf