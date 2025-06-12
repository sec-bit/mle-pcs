# Greyhound Commitment



Greyhound is a lattice-based polynomial commitment scheme (PCS). For polynomials of degree $N$, the evaluation proof size is $poly\log(N)$, and the verification time is $O(\sqrt{N})$. The main purpose of this article is to help readers understand the Greyhound polynomial commitment method, how evaluation proofs work, and how to use Greyhound to prove the evaluation of a polynomial over $\mathbb{F}_q$.

### 1. Notation and Background

Before introducing the design principles of Greyhound, let's establish some notation.

Let $d$ be a power of 2, $\mathcal{R} = \mathbb{Z}[X]/(X^d + 1)$ be the ring of integers in the $2d$-th cyclotomic field. Define the ring $\mathcal{R}_q = \mathbb{Z}_q[X]/(X^d + 1)$ using an odd prime $q$, and define $\delta = \lfloor \log q \rfloor$. To avoid confusion, we will consistently use "vector" to refer to polynomial column vectors over $\mathcal{R}$ or $\mathcal{R}_q$.

For an integer $n \geq 1$, define a tool matrix for binary-to-decimal conversion $\mathbf{G}_n = \mathbf{I} \otimes [1 ~2~ 4~ \cdots~ 2^\delta] \in \mathcal{R}_q^{n \times n\delta}$. Correspondingly, binary decomposition is denoted by $\mathbf{G}_n^{-1} : \mathcal{R}_q^n \to \mathcal{R}_q^{\delta n}$.

For example, given a vector $\mathbf{t} \in \mathcal{R}_q^n$, the notation $\mathbf{G}_n^{-1}(\mathbf{t})$ represents the process of decomposing all coefficients of $\mathbf{t}$ into binary and then filling them into a vector.
$\mathbf{G}_n$ and $\mathbf{G}_n^{-1}$ are inverse operations, with $\mathbf{G}_n \mathbf{G}_n^{-1}(\mathbf{t}) = \mathbf{t}$.

> For example, in $\mathcal{R}_{10} = \mathbb{Z}_{10} [X]/(X^3+1)$, let $\mathbf{t} = (t_1, t_2) = (6+2X+5X^2, 4+X+9X^2) \in \mathcal{R}_{10}^2$, and $\delta = \lceil \log 10 \rceil = 4$.
> Then $\mathbf{G}_3^{-1}(\mathbf{t})$ first converts $(6,5,1),(4,9,2)$ into binary numbers $(0110,0010,0101,0100,1001,0010)$, then fills them into a vector over $\mathcal{R}_q$ as $\hat{\mathbf{t}} = (0+X+X^2, 0+0X+0X^2, 1+0X+0X^2, 1+0X+1X^2, 0+X+0X^2, 0+X+0X^2, 0+X+0X^2, 0+X+0X^2)\in \mathcal{R}^{2 \delta}$, so $\mathbf{G}_3^{-1}(\mathbf{t}) = \hat{\mathbf{t}}$. 
> Correspondingly, the matrix $$\mathbf{G}_3 = \begin{bmatrix} 1 & 2  & 2^3 & 2^4 & 0 &&&&&&\cdots&0\\ 0 & & \cdots &0 & 1 & 2  & 2^3 & 2^4 &0 && \cdots & 0\\ 0 & &\cdots & & & &  &0 & 1 & 2  & 2^3 & 2^4 \end{bmatrix}$$
> represents the inverse operation, i.e., $\mathbf{G}_3 \hat{\mathbf{t}} = \mathbf{t} = (6+2X+5X^2, 4+X+9X^2) \in \mathcal{R}_{10}^2$.

#### Ajtai Commitment
Next, we introduce the definition of the SIS problem and Ajtai commitment.

The SIS problem is defined as follows: given a public matrix $\mathbf{A} \in \mathcal{R}_q^{n \times m}$, find a non-zero short vector $\mathbf{z} \in \mathcal{R}_q^m$ satisfying $\mathbf{A}\mathbf{z}=\mathbf{0}, |\mathbf{z}|\leq B$.

For a binary message, after filling the coefficients into a vector $\mathbf{m} \in \mathcal{R}^n$ over $\mathcal{R}$, the Ajtai commitment process is as follows:
- KeyGen: Input security parameter $\lambda$, generate commitment key $\mathbf{A} \in \mathcal{R}_q^{n\times m}$
- Com: Input commitment key $\mathbf{A} \in \mathcal{R}_q^{n\times m}$ and binary message $\mathbf{m} \in \mathcal{R}^m$, compute commitment $\mathbf{t} = \mathbf{Am}$.

Regarding the Ajtai commitment, three points can be further discussed: 1. Security of the commitment, 2. Norm of the commitment message, and 3. Compressibility of the commitment value.

1. The binding property of the commitment is based on the SIS problem. If a malicious attacker wants to change the commitment value $\mathbf{t}$ to another message's commitment $\mathbf{t} = \mathbf{Am}'$, it's equivalent to finding a solution to the SIS problem $\mathbf{m-m'}$ that satisfies $\mathbf{0} = \mathbf{A(m-m)'}, |\mathbf{m-m}'|_\infty \leq 2$.

2. Note that we can find a solution to the SIS problem satisfying $|\mathbf{m-m}'|_\infty \leq 2$ because we've required the committed messages to be binary. This requirement that messages be binary is actually constraining the norm of $\mathbf{m}$ to be small. In other cases, it could be that the norm of $\mathbf{m}$ is less than some bound $B$, then the binding property of the commitment would reduce to finding a solution with bound $B$: $|\mathbf{m-m}'|_\infty \leq 2B$.

3. The compressibility of the commitment value is reflected in the fact that the commitment value $\mathbf{t} \in \mathcal{R}_q^n$ is an $n$-dimensional vector over $\mathcal{R}_q$, independent of the committed message length (an $m$-dimensional vector over $\mathcal{R}_q$), and under the security definition of the SIS problem, the length of the commitment value $n < m$.


### 2. Greyhound Commitment Scheme

Greyhound commitment can be understood as a two-layer Ajtai commitment.

Suppose we want to commit to a group (e.g., $r$) of arbitrary vectors $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$. Note that each $\mathbf{f}_i$ is an $m$-dimensional vector over $\mathcal{R}_q$, with each component being an element of $\mathcal{R}_q$.

The commitment key consists of the inner public matrix $\mathbf{A}\in \mathcal{R}_q^{n\times m\delta}$ and the outer public matrix $\mathbf{B} \in \mathcal{R}_q^{n \times r n \delta}$.

- Inner commitment: As mentioned in the previous section, Ajtai commitment messages should be binary strings. Therefore, to use Ajtai commitment for $\mathbf{f}_1, \dots, \mathbf{f}_r$, we first need to use the base conversion tool matrix $\mathbf{G}^{-1}$ to convert this group of vectors into binary vectors $\mathbf{s}_i \in \mathcal{R}_q^{m \delta}$, i.e., $\mathbf{s}_i = \mathbf{G}_m^{-1}(\mathbf{f}_i)$. Now, we can make an Ajtai commitment to the message $\mathbf{s}_i$: $$\mathbf{t}_i := \mathbf{As}_i = \mathbf{AG}^{-1}_m(\mathbf{f}_i)$$
This gives us commitment values $\mathbf{t}_1, ..., \mathbf{t}_r \in \mathcal{R}_q^n$ for the $r$ messages $\mathbf{f}_1, ..., \mathbf{f}_r$.

- Outer commitment: After completing the inner commitment, we have $r$ vectors $\mathbf{t}_1, ..., \mathbf{t}_r \in \mathcal{R}_q^n$. Currently, the commitment value has a sublinear relationship $\mathcal{O}(mr)$ with the message length ($r$ groups of vectors of length $m$). To achieve a more compressed commitment value, i.e., $\mathcal{O}(1)$, we want to make another Ajtai commitment to the inner commitment values $\mathbf{t}_1, ..., \mathbf{t}_r$. This can be done by viewing $\mathbf{t}_1, ..., \mathbf{t}_r$ as commitment messages and repeating the above process. First, use $\mathbf{G}^{-1}$ to convert $\mathbf{t}_1, ..., \mathbf{t}_r$ into vectors with binary coefficients $\hat{\mathbf{t}}_i = \mathbf{G}^{-1}(\mathbf{t}_i)$, then compute the outer commitment value: $$\mathbf{u} := \mathbf{B}\begin{bmatrix} \hat{\mathbf{t}}_1 \\ \vdots \\ \hat{\mathbf{t}}_r \end{bmatrix} \in \mathcal{R}_q^n$$
Finally, the commitment to the group of vectors $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$ is the vector $\mathbf{u} \in \mathcal{R}_q^n$.


### 3. Polynomial Evaluation in Greyhound Commitment

In the previous section, we only discussed how to commit to a group of vectors $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$, but our goal is to construct a PCS, so we need to discuss the relationship between this group of vectors and a polynomial $f(\mathsf{X}) = \sum_{i=0}^{N-1} f_i \mathsf{X}^i \in \mathcal{R}_q^{<N}[\mathsf{X}]$ for which we want to perform evaluation.

Note that $\mathsf{X}$ is the variable of polynomial $f$ and has no relation to $X$ in $\mathcal{R} = \mathbb{Z}[X]/(X^d + 1)$.

Assume $N=m \cdot r$. We want to prove that the evaluation of polynomial $f$ at point $x \in \mathcal{R}_q$ is $y$, i.e., $f(x) = \sum_{i=0}^{N-1} f_i x^i = y$.

Similar to Mercury, we can represent the above evaluation process using matrix-vector multiplication:
$$f(x) = [1~x~x^2~\cdots~x^{m-1}] \begin{bmatrix} f_0 & f_m & \cdots & f_{(r-1)m} \\ f_{1} & f_{m+1} &\cdots & f_{(r-1)m+1} \\ f_{2} & f_{m+2} &\cdots & f_{(r-1)m+2} \\ &&\cdots& \\ f_{m-1} & f_{2m-1} &\cdots & f_{rm-1} \end{bmatrix} \begin{bmatrix} 1 \\ x^m \\ (x^m)^2\\ \vdots \\ (x^m)^r \end{bmatrix}.$$


Therefore, if we define vectors $\mathbf{f}_i = [ f_{(i-1)m}, f_{(i-1)m+1}, ... , f_{im-1}] \in \mathcal{R}_q^m$, consisting of the coefficients of polynomial $f$, then the commitment to $\mathbf{f}_1, \dots, \mathbf{f}_r \in \mathcal{R}_q^m$ is the commitment to polynomial $f$.

Now, we define vectors $\mathbf{a}^\top = [1~x~x^2~\cdots~x^{m-1}]$ and $\mathbf{b}^\top = \begin{bmatrix} 1 ~ x^m ~\dots ~ (x^m)^r \end{bmatrix}$, then the polynomial evaluation can be represented as $$f(x) = \mathbf{a}^\top [\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{b}.$$

### 4. Proof of Polynomial Evaluation

The proof of polynomial evaluation includes two points: 1. The polynomial commitment is correctly computed; 2. The polynomial evaluation operation is correct.

1. First, a prover needs to commit to polynomial $f$ according to the method in section 1.1. Then proving the correctness of the commitment computation means proving:
$$\begin{align*} \mathbf{s}_i &= \mathbf{G}^{-1}_m(\mathbf{f}_i), \\ \mathbf{t}_i &= \mathbf{G}_n\hat{\mathbf{t}}_i = \mathbf{As}_i,  \\ \mathbf{u} &= \mathbf{B}\begin{bmatrix} \hat{\mathbf{t}}_1 \\ \vdots \\ \hat{\mathbf{t}}_r \end{bmatrix}. \end{align*} $$

Since the transformation $\mathbf{G}$ is reversible, the first equation can also be written as $\mathbf{f}_i = \mathbf{G}_m \mathbf{s}_i$.

2. Proving the correctness of polynomial evaluation means proving: $$f(x) = \mathbf{a}^\top [\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{b}.$$

Greyhound's approach to proving the above four equations is to have the prover compute parts directly related to polynomial $\mathbf{f}_i$, and the verifier compute the remaining parts. We'll first show the proof process and then discuss this approach.

Assume the public parameters of the protocol are commitment keys $\mathbf{A,B}$, commitment $u$, and polynomial $f$. The entire protocol consists of 2 rounds of interaction:

1. The prover first calculates the first half of $f(x)$ and sends $\mathbf{w}$ to the verifier:
$$ \mathbf{w}^\top := \mathbf{a}^\top[\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r]. $$

2. The verifier selects a random challenge vector $\mathbf{c} = (c_1, ..., c_r) \in \mathcal{R}_q^r$ and sends it to the prover.

3. The prover sends intermediate commitments $(\hat{\mathbf{t}}_1, ...,\hat{\mathbf{t}}_r)$ and uses $\mathbf{c}$ to make a linear combination of $\mathbf{s}_i$: $\mathbf{z} := [\mathbf{s}_1 ~ \cdots~ \mathbf{s}_r] \mathbf{c} = \mathbf{s}_1c_1 + ... +\mathbf{s}_r c_r\in \mathcal{R}_q^m$.

Finally, the verifier uses all the information sent by the prover $\mathbf{w}, \hat{\mathbf{t}}_i, \mathbf{z}$ to verify whether the following equations hold:

$$
\begin{align}
\mathbf{w}^\top \mathbf{b} &= y, \\
\mathbf{w}^\top \mathbf{c} &= \mathbf{a}^\top \mathbf{G}_m \mathbf{z},\\
\mathbf{Az} & = c_1\mathbf{G}_n \hat{\mathbf{t}}_1 + \cdots + c_r \mathbf{G}_n \hat{\mathbf{t}}_r,\\
\mathbf{u} &= \mathbf{B}\begin{bmatrix} \hat{\mathbf{t}}_1 \\ \vdots \\ \hat{\mathbf{t}}_r \end{bmatrix}.
\end{align}
$$

The first equation actually verifies the second half of the polynomial $f(x)$ evaluation operation, because if $\mathbf{w}$ is correct (which is guaranteed by the second equation), then $$f(x) = \mathbf{a}^\top[\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{b} = \mathbf{w}^\top \mathbf{b} = y.$$

The second equation, with the participation of the challenge vector $\mathbf{c}$, verifies the correctness of the first half of the $f(x)$ evaluation operation:

$$
\begin{align*} \mathbf{w}^\top \mathbf{c} &= \mathbf{a}^\top [\mathbf{f}_1 ~ \cdots ~\mathbf{f}_r] \mathbf{c} \\ & = \mathbf{a}^\top \mathbf{G}_m [\mathbf{s}_1~ \cdots ~\mathbf{s}_r] \mathbf{c} \\
& = \mathbf{a}^\top \mathbf{G}_m \mathbf{z}
\end{align*}.
$$

The third equation verifies the correctness of the inner commitment of the PCS:

$$
\begin{align*} \mathbf{Az} & = \mathbf{A s}_1 c_1 + ... + \mathbf{A s}_r c_r\\ &= c_1\mathbf{G}_n \hat{\mathbf{t}}_1 + \cdots + c_r \mathbf{G}_n \hat{\mathbf{t}}_r. \\
\end{align*}
$$

The fourth equation verifies the outer commitment of the PCS.

This proof can be further optimized using Labrador's recursive proof to reduce the proof size by rewriting the equations in (1) into the standard form of Labrador proof. For specific details, please refer to the Greyhound documentation.

### 5. Using $\mathcal{R}_q$ to Prove Polynomial Evaluation over $\mathbb{F}_q$

In the previous introduction, we ignored an important issue: all operations and proofs are performed over $\mathcal{R}_q$, while most practical applications use polynomials over $\mathbb{F}_q$. This section discusses how to equivalently represent polynomials over $\mathbb{F}_q$ as polynomials over $\mathcal{R}_q$, thereby using the proof methods from the previous sections.

The transformation from $\mathbb{F}_q$ to $\mathcal{R}_q$ requires filling vectors over $\mathbb{F}_q$ into $\mathcal{R}_q$ through coefficient filling, and then using operations over $\mathcal{R}_q$ to represent operations over $\mathbb{F}_q$.

Define an automorphism $\sigma: \mathcal{R}_q \to \mathcal{R}_q$ that maps elements in $\mathcal{R}_q$ to negative powers, $\sigma(X) = X^{-1}$. For example, if $a = a_0 + \sum_{i=1}^{d-1} a_i X^i \in \mathcal{R}_q$, then $\sigma(a) = a_0 +\sum_{i=1}^{d-1} a_i X^{-i} \in \mathcal{R}_q$.
In $\mathcal{R}_q$, the constant term of $a\sigma(a)$ is: $a_0 a_0 + \sum_{i=1}^{d-1} a_i a_i = \sum_{i=0}^{d-1} a_i a_i$, which is the sum of all terms where the product of a term in $a$ and a term in $\sigma(a)$ does not involve $X$.

Let's clarify the notation: a polynomial over $\mathbb{F}_q$ is denoted as $F(U) = \sum_{i=0}^{N'-1} F_i U^i = V \in \mathbb{F}_q$, and a polynomial over $\mathcal{R}_q$ is denoted as $f(x) = \sum_{i=0}^{N-1} f_i x^i = y \in \mathcal{R}_q$. We use $f$ to represent the polynomial obtained by filling the coefficients of $F$ into $\mathcal{R}_q$. To distinguish, we use $N-1$ to represent the degree of polynomial $f$ and $N'-1$ for the degree of $F$. After coefficient filling, $N$ and $N'$ are not equal.

- When $N' \leq d$, without loss of generality, we discuss $N'=d$. When $N' < d$, we can pad $F$ with zeros to make $N'=d$. In this case, only one element in $\mathcal{R}_q$ is needed to store all coefficients of $F$, so $N = 1$.

We define the evaluation after filling the coefficients of $F$ as $f(x) = f_0 \sigma(x)$.
Here, $f_0 = \sum_{i=0}^{d-1} F_i X^i \in \mathcal{R}_q$ is obtained by filling all the coefficients of $F$ $(F_0, ..., F_{N'-1})$, and $\sigma(x)$ is obtained by first filling all powers of the evaluation point $U$ of $F$ $(1, U, ..., U^{N'-1})$ into $x = \sum_{i=0}^{d-1} U^i X^i\in \mathcal{R}_q$, and then applying the $\sigma$ mapping to get $\sigma(x) = 1+ \sum_{i=1}^{d-1} U^i X^i \in \mathcal{R}_q$.
It should be reminded again that $X$ here is a symbol in $\mathcal{R}_q$ and has no actual meaning.

Using the $\sigma$ mapping discussed above, the constant term of $f(x) = f_1 \sigma(x)$ is $$\sum_{i=0}^{N'-1} F_i U^{i} = V.$$ This means that a Greyhound verifier can check if $F(U) = V$ holds by checking if the constant term of $f(x)$ is $V$.

- When $N' > d$, we discuss $N' = Nd$. In this case, the coefficients of $F$ $(F_0, ..., F_{N'-1})$ will be filled into $N$ elements in $\mathcal{R}_q$ $f_0, f_1 ..., f_{N-1} \in \mathcal{R}_q$, but the operation method of polynomial $f(x)$ is similar to when $N'=d$.

We just need to fill the coefficients of $F$ sequentially into $(f_0, f_1 ..., f_{N-1})$, then fill $(1, U, ..., U^{N'-1})$ sequentially into $x_1, x_2, ..., x_N \in \mathcal{R}_q$, and then define $$f(x) = \sum_{i=0}^{N} f_i x_i.$$

Then, the multiplication operation between $f_i$ and $x_i$ in $f(x)$ will segment-wise store $\sum_{j=0}^{d} F_{id+j}{U^{id+j}}$ in the constant term of $f_i x_i$, similar to our previous discussion.
Since addition in $\mathcal{R}_q$ adds corresponding coefficients, the outer addition operation $\sum_{i=0}^{N-1} f_i x_i$ from $i=0$ to $N$ will further combine the $\sum_{j=0}^{d} F_{id+j}{U^{id+j}}$ in each constant term, i.e., the constant term of $f(x)$ is $$\sum_{i=0}^{N-1} \sum_{j=0}^{d} F_{id+j}{U^{id+j}} = \sum_{i=0} ^{N'-1} F_i U^i = V.$$

Now, we are able to use Greyhound to commit to any polynomial over $\mathbb{F}_q$ and prove their evaluations. Thank you for reading to this point.


---
References:
[1] Ngoc Khanh Nguyen, Gregor Seiler: Greyhound: Fast Polynomial Commitments from Lattices. CRYPTO (10) 2024: 243-275.