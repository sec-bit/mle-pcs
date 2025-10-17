# Entropy Function and the Fundamental Limits of Codes

## Introduction

We now turn our attention to applying combinatorial techniques to one of the central questions in coding theory: what are the optimal parameters an error-correcting code can achieve? This inquiry delves into the fundamental trade-off between a code's efficiency and its robustness.

The core lies in understanding the relationship between a code's **rate**, denoted by $R$, and its **relative distance**, denoted by $\delta$. The rate, defined as $R=k/n$ for an $(n,k,d)_q$ code, measures the density of information within a codeword; a higher rate means less redundancy and more efficient transmission. The relative distance, $\delta=d/n$, measures the code's error-correcting capability; a larger relative distance allows for the correction of a greater fraction of errors. Intuitively, these two parameters are in opposition: increasing a code's resilience to errors (higher $\delta$) requires adding more redundancy, which in turn decreases its rate (lower $R$). The central challenge is to precisely quantify this trade-off.

To navigate this landscape, an important mathematical instrument is required: the **q-ary entropy function**, $H_q(x)$. This function provides the essential language for describing the combinatorial geometry of code spaces. It is deeply connected to the concept of a Hamming ball's volume, which represents the number of possible corrupted versions of a given codeword. By understanding the entropy function, we can formulate sharp bounds on the achievable pairs of $(R,\delta)$.

First, we will conduct a deep dive into the q-ary entropy function, defining it formally and exploring its connection to the volume of Hamming balls. Second, we will chart the limits of what is possible and impossible in code design by examining four foundational bounds: the *Asymptotic Hamming Bound*, the *Gilbert-Varshamov Bound*, the *Singleton Bound*, and the *Plotkin Bound*. These bounds collectively define the achievable region for code parameters. Finally, for the readers seeking complete mathematical rigor, a detailed appendix provides the full, step-by-step derivations of the key propositions and theorems discussed.


## The q-ary Entropy Function

At the heart of combinatorial coding theory lies the problem of counting. Specifically, we need to count how many possible vectors exist within a certain distance of a given codeword. The q-ary entropy function emerges as the natural mathematical language to describe the size of these sets, especially in the asymptotic limit of large block lengths.

### Definition and Intuition

The q-ary entropy function is a fundamental quantity that plays a central role in analyzing the limits of codes.

> **Definition (q-ary Entropy Function):** Let $q$ be an integer such that $q \ge 2$, and let $x$ be a real number such that $0 \le x \le 1$. The q-ary entropy function is defined as:
> $$ H_q(x) = x\log_q(q-1) - x\log_q(x) - (1-x)\log_q(1-x) $$

For the special binary case where $q=2$, the subscript is typically dropped, and the function simplifies to the well-known Shannon entropy function, where logarithms are base 2:
$$ H(x) = H_2(x) = -x\log_2(x) - (1-x)\log_2(1-x) $$
In the context of information theory, $H(x)$ represents the entropy, or uncertainty, of a binary random variable that takes the value 1 with probability $x$ and 0 with probability $1-x$. It quantifies the average number of bits of information gained from observing the outcome of such a random event.

For $q > 2$, the q-ary entropy function does not have a direct analogue to the entropy of a single random variable. Its structure is tailored to combinatorial counting problems in q-ary spaces. The key distinction is the presence of the $x\log_q(q-1)$ term. This term arises from the fact that in a q-ary alphabet, if a symbol at a given position is erroneous, there are $q-1$ possible incorrect values it could assume. This term accounts for the "richness" of error possibilities in a non-binary setting, a crucial factor when counting the number of error patterns of a certain weight. The function $H_q(x)$ reaches its maximum value of 1 at $x=1-1/q$.

### The Volume of Hamming Balls: Connecting Entropy to Code Space

The primary reason for the centrality of the entropy function in coding theory is its connection to the volume of a Hamming ball. This connection provides the bridge between abstract combinatorial counting and the concrete analysis of code parameters like rate and distance.

> **Definition (Volume of a Hamming Ball):** Let $q \ge 2$ and $n \ge r \ge 1$ be integers. The volume of a Hamming ball of radius $r$ in the space $[q]^n$, denoted $\text{Vol}_q(r,n)$, is the number of vectors at a Hamming distance of at most $r$ from a given center point (e.g., the all-zero vector). It is given by:
> $$ \text{Vol}_q(r,n) = |B_q(0,r)| = \sum_{i=0}^{r} \binom{n}{i}(q-1)^i $$

The term $\binom{n}{i}$ counts the number of ways to choose $i$ positions to have errors, and for each of those $i$ positions, the $(q-1)^i$ term counts the number of ways to assign non-zero (erroneous) values from the alphabet of size $q$. The q-ary entropy function provides a remarkably accurate asymptotic approximation for this volume. This relationship is formalized in the following proposition.

> **Proposition:** Let $q \ge 2$ be an integer and $0 \le p \le 1 - 1/q$ be a real number. Then:
> 1.  $\text{Vol}_q(pn,n) \le q^{H_q(p)n}$
> 2.  For large enough $n$, $\text{Vol}_q(pn,n) \ge q^{H_q(p)n - o(n)}$

This proposition carries a profound implication: $H_q(p)$ can be interpreted as the *logarithmic density* of a Hamming ball. The volume of a ball whose radius is a fraction $p$ of the block length grows exponentially with $n$, and the base-q logarithm of this volume, when normalized by $n$, is precisely $H_q(p)$ in the limit. This insight is the cornerstone of asymptotic analysis in coding theory. It allows us to translate geometric properties of codes (like the non-overlapping of error balls) into algebraic statements about their rates, using the entropy function as the intermediary.

The specific mathematical form of the q-ary entropy function is not arbitrary; it is the expression that naturally emerges from the asymptotic analysis of the binomial sum that defines the volume of a Hamming ball. When tools like Stirling's approximation are applied to this sum for large $n$, the term that arises in the exponent is precisely $H_q(p)$. Thus, the entropy function is not an external construct imposed upon the problem but rather a function that the underlying combinatorics of the problem generates.

### Essential Properties and Behaviors of $H_q(x)$

To effectively apply the entropy function in deriving code bounds, it is necessary to understand its mathematical behavior under various conditions.

* **Behavior for Large Alphabet Size (q):** For a fixed error fraction $\rho$, the behavior of $H_q(\rho)$ for large $q$ is of interest. It can be shown that for very large alphabets, the rate penalty associated with a given error fraction (as captured by the entropy term in bounds) behaves almost linearly with that fraction.
* **Monotonicity with q:** For a fixed error fraction $\rho$, the q-ary entropy function $H_q(\rho)$ is a decreasing function of $q$ for sufficiently large $q$. This implies that for a fixed fractional radius, the logarithmic density of a Hamming ball decreases as the alphabet size grows. This is intuitive: with a larger alphabet, there are more "directions" for errors to occur, so a ball of a fixed relative radius constitutes a smaller fraction of the total space.
* **Behavior Near the Peak:** The function $H_q(x)$ achieves its maximum value of 1 at $x=1-1/q$. Understanding its behavior near this peak is crucial for analyzing codes that operate close to their theoretical limits. Taylor series expansion shows that the function is quadratic near its maximum, indicating a "flattening" of the curve at its peak.
* **Behavior Near Zero:** For very small error fractions, the behavior of the entropy function is also important. For a small $\epsilon > 0$, $H_q(\epsilon) = \Theta(\log_q(1/\epsilon) \cdot \epsilon\log(1/\epsilon))$. This describes the characteristic shape of the entropy curve as it rises from zero, which is relevant for analyzing codes designed to correct a very small number of errors.


## The R vs. δ Trade-off: Charting the Boundaries of Possibility

Armed with the q-ary entropy function as our primary analytical tool, we can now explore the fundamental limits of error-correcting codes. This exploration involves establishing bounds on the rate $R$ and relative distance $\delta$. These bounds fall into two categories: **upper bounds** (or impossibility results), which set a ceiling on what can be achieved, and **lower bounds** (or existence results), which provide a floor, guaranteeing that codes with certain parameters do exist.

### The Asymptotic Hamming Bound: A Sphere-Packing Limit on Rate

The Hamming bound is a classic impossibility result that provides an upper limit on the rate of any code with a given minimum distance. The underlying concept is one of sphere packing. For a code to be able to uniquely correct up to $t$ errors, the Hamming balls of radius $t$ centered at each of its codewords must be disjoint. If they were to overlap, a received word in the intersection could be decoded to two different valid codewords, creating ambiguity.

This geometric constraint leads to a simple combinatorial inequality. The total number of points in the space, $q^n$, must be at least as large as the sum of the volumes of these disjoint balls. For an $(n,k,d)_q$ code with $M=q^k$ codewords, and letting $t=\lfloor\frac{d-1}{2}\rfloor$ be the number of correctable errors, this gives:
$$ M \cdot \text{Vol}_q(t,n) \le q^n $$
Taking the base-q logarithm of both sides and dividing by $n$ yields a bound on the rate $R=k/n$:
$$ R = \frac{k}{n} \le 1 - \frac{\log_q \text{Vol}_q(\lfloor\frac{d-1}{2}\rfloor,n)}{n} $$
To find the asymptotic form of this bound, we use the connection between the volume of a Hamming ball and the entropy function. Using the lower bound from our proposition, with a relative distance $\delta=d/n$ (implying a correction radius of approximately $(\delta/2)n$), we have:
$$ \text{Vol}_q\left(\left\lfloor\frac{d-1}{2}\right\rfloor,n\right) \ge q^{H_q(\frac{\delta}{2})n - o(n)} $$
Substituting this into the rate inequality, the second term on the right-hand side is lower-bounded by $H_q(\delta/2)-o(1)$. This leads directly to the final statement of the bound.

> **Proposition (Asymptotic Hamming Bound):** Let $C$ be an infinite family of q-ary codes with rate $R$ and relative distance $\delta$. Then:
> $$ R \le 1 - H_q\left(\frac{\delta}{2}\right) $$

This bound establishes a fundamental ceiling on performance. No code, regardless of its construction, can achieve a rate higher than that permitted by the Asymptotic Hamming Bound for a given relative distance.

### The Gilbert-Varshamov (GV) Bound: A Proof of Existence for Good Codes

In contrast to the Hamming bound's impossibility statement, the Gilbert-Varshamov (GV) bound is a powerful existence result. It guarantees that "good" codes—those with a respectable rate and distance—do exist, even if it does not provide an explicit method for constructing them in all cases.

> **Theorem (Gilbert-Varshamov Bound):** Let $q \ge 2$. For every $0 \le \delta < 1 - 1/q$, there exists a family of q-ary codes $C$ with rate $R(C) \ge 1 - H_q(\delta)$ and relative distance $\delta(C) \ge \delta$. If $q$ is a prime power, then such a family of linear codes exists.

The GV bound provides a floor for what is achievable. The gap between this lower bound and the Hamming upper bound defines the primary region of uncertainty in combinatorial coding theory. The difference between the two bounds, $R_{\text{Hamming}} \approx 1 - H_q(\delta/2)$ and $R_{\text{GV}} \approx 1 - H_q(\delta)$, stems directly from the radii of the Hamming balls considered in their respective proofs. The Hamming bound's condition for unique decodability requires disjoint balls of radius $t \approx d/2$, leading to the $\delta/2$ term. The GV bound's condition for existence requires that a new codeword can be placed outside balls of radius $d-1$ from existing codewords, leading to the $\delta$ term. This difference is not a mathematical artifact but a reflection of the distinct combinatorial conditions for decodability versus separability.

Two primary methods are used to prove the GV bound, each offering a different perspective.

* **Proof Method 1: Greedy Construction**
    This method provides a constructive, albeit computationally infeasible, proof for general (not necessarily linear) codes. The algorithm proceeds as follows:
    1.  Start with an empty code $C$.
    2.  Iteratively add any vector $v$ from the space $[q]^n$ to $C$, provided that $v$ has a Hamming distance of at least $d$ from every codeword already in $C$.
    3.  Terminate when no such vector $v$ can be found.
    When the algorithm terminates, the Hamming balls of radius $d-1$ centered at each codeword in $C$ must completely cover the entire space $[q]^n$. If they did not, there would be an uncovered vector, which by definition would be at a distance of at least $d$ from all codewords and could have been added, contradicting termination. This covering property implies the inequality $|C| \cdot \text{Vol}_q(d-1,n) \ge q^n$. Applying the asymptotic upper bound for the volume, $\text{Vol}_q(d-1,n) \approx \text{Vol}_q(\delta n,n) \le q^{nH_q(\delta)}$, and solving for the rate $R=(\log_q|C|)/n$ yields the GV bound.

* **Proof Method 2: The Probabilistic Method for Linear Codes**
    For linear codes over fields where $q$ is a prime power, a more abstract and powerful argument can be made using the probabilistic method. Instead of building a code, one proves its existence by showing that a randomly chosen linear code has the desired properties with high probability. The argument proceeds in these key steps:
    1.  A random linear code is generated by choosing a $k \times n$ generator matrix $G$ with each entry selected independently and uniformly at random from $\mathbb{F}_q$.
    2.  For any non-zero message vector $m \in \mathbb{F}_q^k \setminus \{0\}$, the corresponding codeword $c=mG$ is a uniformly random vector in $\mathbb{F}_q^n$.
    3.  The probability that this random codeword has a weight less than $d$ is the ratio of the volume of the ball of radius $d-1$ to the size of the entire space:
        $$ \Pr_G[wt(mG) < d] = \frac{\text{Vol}_q(d-1,n)}{q^n} \le \frac{q^{nH_q(\delta)}}{q^n} = q^{n(H_q(\delta)-1)} $$
    4.  To ensure the minimum distance of the code is at least $d$, we must show that no non-zero message results in a low-weight codeword. The union bound is used to sum the small probability of failure over all $q^k-1$ possible non-zero messages.
    5.  By choosing the rate $R=k/n$ to be slightly less than $1-H_q(\delta)$, the total probability of failure becomes less than 1. Since the probability of failure is less than 1, there must exist at least one generator matrix $G$ that produces a code with the desired minimum distance, proving the theorem.

### The Singleton Bound: An Elegant and Universal Constraint

The Singleton bound is another upper bound on code parameters, notable for its simplicity and its independence from the alphabet size $q$. While often not as tight as the Hamming or Plotkin bounds for a fixed alphabet, its generality makes it a fundamental benchmark.

> **Theorem (Singleton Bound):** For every $(n,k,d)_q$ code:
> $$ k \le n - d + 1 $$
> In its asymptotic form, for a family of codes with rate $R$ and relative distance $\delta$, the bound is:
> $$ R \le 1 - \delta $$

The proof relies on a simple yet powerful "puncturing" argument. Consider any $(n,k,d)_q$ code $C$. If we create a new set of strings by deleting the first $d-1$ symbols from every codeword in $C$, the resulting strings, now of length $n-(d-1)=n-d+1$, must all be distinct. If any two of these shortened strings were identical, it would imply that their original full-length codewords differed in at most the $d-1$ positions that were deleted. This would mean their Hamming distance was at most $d-1$, contradicting the code's minimum distance of $d$.

Since all $M=q^k$ of these new strings are unique and have length $n-d+1$, the total number of such strings cannot exceed the total number of possible strings in that space, which is $q^{n-d+1}$. This leads directly to the inequality $q^k \le q^{n-d+1}$, which simplifies to $k \le n-d+1$. This progression from a simple combinatorial argument to a powerful bound showcases the elegance often found in coding theory.

### The Plotkin Bound: A Stronger Limit for High-Distance Codes

The Plotkin bound provides a stronger upper bound on rate, particularly for codes with a large relative distance. It definitively answers a question left open by the GV bound: can codes exist with both a positive rate ($R>0$) and a relative distance greater than the "random coding" threshold ($\delta > 1-1/q$)? The Plotkin bound proves that the answer is no. The value $\delta=1-1/q$ represents the expected fractional distance between two randomly chosen vectors. The Plotkin bound demonstrates that demanding all codewords be more separated than random vectors are on average comes at a steep cost: the code size collapses, and the asymptotic rate becomes zero. This behavior is characteristic of a phase transition in a combinatorial system.

> **Theorem (Plotkin bound):** For any code $C \subseteq [q]^n$ with distance at least $d$:
> 1.  If $d > (1-\frac{1}{q})n$, then $|C| \le \frac{qd}{qd - (q-1)n}$.
> 2.  If $d = (1-\frac{1}{q})n$, then $|C| \le 2qn$.

The first part implies that for any $\delta > 1-1/q$, the code size $|C|$ is bounded by a constant that does not grow with $n$, meaning the rate $R$ must asymptotically be zero. The bound can be extended via a "shortening" argument to cover the entire range of $\delta$.

> **Corollary:** For an infinite family of q-ary codes with rate $R$ and relative distance $0 \le \delta \le 1 - 1/q$:
> $$ R \le 1 - \left(\frac{q}{q-1}\right)\delta $$

The proof of the Plotkin bound is the most mathematically sophisticated in this chapter, showcasing a powerful technique of transforming a discrete problem into a continuous geometric one. This progression from the simple combinatorial argument of the Singleton bound to the geometric abstraction of the Plotkin bound illustrates a key pattern in modern mathematics: solving problems by mapping them to different domains where more powerful tools are available. The high-level strategy is as follows:

1.  **Transform the Problem:** A mapping lemma provides a method to map each codeword $c \in [q]^n$ to a unit vector $f(c)$ in a high-dimensional real space, $\mathbb{R}^{nq}$.
2.  **Connect Distance to Geometry:** This mapping is ingeniously constructed such that the Hamming distance $\Delta(c_1,c_2)$ is directly related to the inner product $\langle f(c_1), f(c_2) \rangle$. A large Hamming distance corresponds to a large negative inner product, meaning the vectors form an obtuse angle.
3.  **Solve the Geometric Problem:** A geometric lemma establishes a fundamental limit on how many non-zero vectors can exist in an N-dimensional real space if every pair has a non-positive inner product.
4.  **Conclude:** By applying this geometric limit to the set of vectors corresponding to the codewords, we obtain an upper bound on the number of codewords, which is precisely the Plotkin bound.


## Visualizing the Achievable Region

The interplay of these four fundamental bounds defines the landscape of what is achievable in coding theory. By plotting them on a graph of rate $R$ versus relative distance $\delta$, we can visualize the known limits of code performance. The following chart illustrates this for the important case of binary codes ($q=2$).

![Chart of Code Bounds for Binary Codes](https://i.imgur.com/83u65aP.png)

**Interpreting the Graph:**

* **The Achievable Region (Green Area):** The Gilbert-Varshamov (GV) bound forms a lower boundary. Any point $(R,\delta)$ that lies on or below the GV curve represents a code that is known to exist. This is the region of provably achievable code parameters.
* **The Forbidden Region (Above the Upper Bounds):** The Asymptotic Hamming Bound, Singleton Bound, and Plotkin Bound collectively form an upper boundary. For any given $\delta$, the tightest of these bounds dictates the maximum possible rate. No code can have parameters $(R,\delta)$ that lie in the region above this composite upper envelope.
* **The Region of Uncertainty (White Area):** The significant gap between the GV lower bound and the upper bounds represents the frontier of research in combinatorial coding theory. For any $\delta$ in this region, we know that codes with rate up to the GV bound exist, and we know that no code can have a rate above the Hamming/Plotkin bound, but the true maximum possible rate, often denoted $\alpha_q(\delta)$, remains unknown.

To synthesize this information, the following table summarizes the key characteristics of each bound. This table distills the core information of the chapter into a single, comparative artifact, facilitating a structured understanding of their roles and relationships.

| Bound Name          | Type                 | Asymptotic Formula (for q≥2)                 | Key Insight / Proof Technique          | When is it Strongest?                          |
| :------------------ | :------------------- | :------------------------------------------- | :------------------------------------- | :--------------------------------------------- |
| **Hamming** | Upper (Impossibility) | $R \le 1 - H_q(\delta/2)$                    | Sphere Packing / Volume Argument       | For small $\delta$ (high rate).                |
| **Gilbert-Varshamov** | Lower (Existence)    | $R \ge 1 - H_q(\delta)$                      | Greedy Algorithm / Probabilistic Method | The best general existence bound.              |
| **Singleton** | Upper (Impossibility) | $R \le 1 - \delta$                           | Puncturing / Pigeonhole Principle      | Simple and alphabet-independent.               |
| **Plotkin** | Upper (Impossibility) | $R \le 1 - (\frac{q}{q-1})\delta$             | Geometric Mapping / Inner Products     | For large $\delta$ (low rate), especially $\delta > 1-1/q$. |

## Conclusion

This report has traversed the foundational combinatorial landscape of coding theory. We began by defining the q-ary entropy function, establishing it not merely as a formula but as the intrinsic language of asymptotic counting in q-ary spaces, directly tied to the volume of Hamming balls. With this powerful tool, we systematically charted the critical trade-off between a code's rate $R$ and its relative distance $\delta$.

The analysis of four fundamental bounds has delineated the boundaries of our knowledge. The Gilbert-Varshamov bound provides a robust proof of existence, guaranteeing a baseline level of performance that can be achieved. Conversely, the Hamming, Singleton, and Plotkin bounds establish a firm ceiling, defining a forbidden region of parameters that no code can attain. The Hamming bound, based on sphere-packing, is strongest for high-rate codes, while the Plotkin bound, derived from an elegant geometric argument, dominates for high-distance codes, revealing a sharp "phase transition" at a relative distance of $\delta = 1 - 1/q$.

A significant gap persists between the best-known existence bounds and the tightest impossibility bounds. The precise location of the optimal trade-off curve, $\alpha_q(\delta)$, within this region of uncertainty remains one of the most important open problems in the field, driving ongoing research.

While this chapter has focused on the existence and non-existence of codes, the methods have been largely non-constructive. The probabilistic proof of the GV bound, for instance, tells us that good codes are abundant but does not tell us how to find one efficiently. The next stage of our exploration will shift focus from the combinatorial to the algebraic, examining powerful techniques that yield explicit constructions of codes. These constructions, such as the celebrated Reed-Solomon codes, not only provide practical solutions but also meet some of the fundamental bounds we have established, thereby connecting the abstract limits of possibility with concrete algorithmic reality.

---

## Appendix: Detailed Mathematical Proofs

This appendix provides the full mathematical derivations for the key results presented in the main body of the report.

### A.1. Proof of Proposition: Asymptotic Bounds on the Volume of a Hamming Ball

This proposition establishes the crucial link between the combinatorial quantity $\text{Vol}_q(pn, n)$ and the analytical function $H_q(p)$.

#### Part (i) - The Upper Bound

We want to prove $\text{Vol}_q(pn, n) \le q^{H_q(p)n}$. The proof leverages the binomial expansion. For $0 \le p \le 1 - 1/q$, we have:
$$
\begin{aligned}
1 &= (p + (1-p))^n = \sum_{i=0}^{n} \binom{n}{i} p^i (1-p)^{n-i} \\
&\ge \sum_{i=0}^{pn} \binom{n}{i} p^i (1-p)^{n-i} \\
&= \sum_{i=0}^{pn} \binom{n}{i} (q-1)^i \left(\frac{p}{q-1}\right)^i (1-p)^{n-i} \\
&= \sum_{i=0}^{pn} \binom{n}{i} (q-1)^i (1-p)^n \left(\frac{p}{(q-1)(1-p)}\right)^i
\end{aligned}
$$
Since $p \le 1-1/q$, the term $\frac{p}{(q-1)(1-p)} \le 1$. As $i \le pn$, we can weaken the inequality by replacing the exponent $i$ with $pn$:
$$
\begin{aligned}
1 &\ge \sum_{i=0}^{pn} \binom{n}{i} (q-1)^i (1-p)^n \left(\frac{p}{(q-1)(1-p)}\right)^{pn} \\
&= \left(\sum_{i=0}^{pn} \binom{n}{i} (q-1)^i\right) (1-p)^{n-pn} \left(\frac{p}{q-1}\right)^{pn} \\
&= \text{Vol}_q(pn, n) \cdot \frac{p^{pn}(1-p)^{n-pn}}{(q-1)^{pn}}
\end{aligned}
$$
The final term is $q^{-H_q(p)n}$. Thus:
$$ 1 \ge \text{Vol}_q(pn, n) \cdot q^{-H_q(p)n} $$
Rearranging gives the desired bound:
$$ \text{Vol}_q(pn, n) \le q^{H_q(p)n} $$

#### Part (ii) - The Lower Bound

We want to prove $\text{Vol}_q(pn, n) \ge q^{H_q(p)n - o(n)}$. The volume is at least its largest term, which is at $i=pn$:
$$ \text{Vol}_q(pn, n) \ge \binom{n}{pn} (q - 1)^{pn} $$
Using Stirling's approximation, $\binom{n}{k} \approx \frac{1}{\sqrt{2\pi n p (1-p)}} 2^{n H(p)}$ for the binary case, a similar analysis gives:
$$ \binom{n}{pn} \ge q^{n(-p\log_q p - (1-p)\log_q(1-p))} \cdot q^{-o(n)} $$
Substituting this back into the inequality for the volume:
$$
\begin{aligned}
\text{Vol}_q(pn, n) &\ge (q-1)^{pn} \cdot q^{n(-p\log_q p - (1-p)\log_q(1-p))} \cdot q^{-o(n)} \\
&= q^{pn \log_q(q-1)} \cdot q^{n(-p\log_q p - (1-p)\log_q(1-p))} \cdot q^{-o(n)} \\
&= q^{n(p\log_q(q-1) - p\log_q p - (1-p)\log_q(1-p))} \cdot q^{-o(n)} \\
&= q^{n H_q(p)} \cdot q^{-o(n)} = q^{H_q(p)n - o(n)}
\end{aligned}
$$
This completes the proof.

### A.2. Proof of Theorem: The Gilbert-Varshamov Bound for Linear Codes

We prove the existence of a linear $[n, k, d]_q$ code for $k \approx n(1 - H_q(\delta))$ using the probabilistic method. We must show a generator matrix $G$ exists such that for every non-zero message $m$, $wt(mG) \ge d$.

1.  **Setup:** Pick a $k \times n$ matrix $G$ uniformly at random. We bound the probability that there exists some non-zero $m$ such that $wt(mG) < d$.
2.  **Union Bound:** We sum the failure probability over all $q^k - 1$ non-zero messages:
    $$ P[\text{failure}] \le \sum_{m \neq 0} P[wt(mG) < d] $$
3.  **Probability for a Single Message:** For a fixed non-zero $m$, the codeword $c=mG$ is a uniformly random vector. The probability that its weight is less than $d$ is the ratio of the volume of the ball of radius $d-1$ to the size of the space:
    $$ P[wt(mG) < d] = \frac{\text{Vol}_q(d-1, n)}{q^n} $$
4.  **Bounding the Probability:** Using the volume upper bound with $d=\delta n$:
    $$ P[wt(mG) < d] \le \frac{q^{n H_q(\delta)}}{q^n} = q^{n(H_q(\delta) - 1)} $$
5.  **Completing the Union Bound:**
    $$ P[\text{failure}] \le (q^k - 1) \cdot q^{n(H_q(\delta) - 1)} < q^k \cdot q^{n(H_q(\delta) - 1)} $$
    By choosing $k = n(1 - H_q(\delta) - \epsilon)$:
    $$ P[\text{failure}] < q^{n(1 - H_q(\delta) - \epsilon)} \cdot q^{n(H_q(\delta) - 1)} = q^{-n\epsilon} $$
6.  **Conclusion:** For any $\epsilon > 0$, this probability is less than 1. Therefore, a "good" matrix $G$ must exist. This argument also ensures $G$ has full rank.

### A.3. Proof of Theorem: The Singleton Bound

The theorem states that for any $(n, k, d)_q$ code, $k \le n - d + 1$.

1.  **Setup:** Let $C$ be an $(n, k, d)_q$ code with $M = q^k$ codewords.
2.  **Puncturing Operation:** Create a new set of strings $C'$ by keeping only the first $n - d + 1$ symbols of each codeword in $C$.
3.  **Injectivity Argument:** All strings in $C'$ must be unique. If two distinct original codewords $c_i$ and $c_j$ became identical after puncturing, they must have agreed on their first $n-d+1$ symbols. This would mean they differed in at most the final $d-1$ symbols, so $\Delta(c_i, c_j) \le d-1$, which contradicts the code's minimum distance of $d$.
4.  **Pigeonhole Principle:** Since all $M$ strings in $C'$ are unique, $M$ cannot be larger than the total number of possible strings of length $n-d+1$.
    $$ M \le q^{n-d+1} $$
5.  **Final Step:** Taking $\log_q$ of both sides gives $k \le n-d+1$. The asymptotic version $R \le 1-\delta$ follows by dividing by $n$ and letting $n \to \infty$.

### A.4. Proof of Theorem: The Plotkin Bound

The proof uses a geometric argument.

**Stage 1: Mapping Lemma**
There exists a map $f : [q]^n \to \mathbb{R}^{nq}$ that turns codewords into unit vectors such that the inner product is related to Hamming distance:
$$ \langle f(c_1), f(c_2) \rangle = 1 - \left(\frac{q}{q - 1}\right) \frac{\Delta(c_1, c_2)}{n} $$
The proof involves constructing a local map $\phi(i) = e_i - \bar{e}$ and concatenating these vectors with a normalization factor.

**Stage 2: Geometric Lemma**
For a set of $m$ vectors $\{v_i\}$ in $\mathbb{R}^N$:
1.  If $\langle v_i, v_j \rangle \le 0$ for all $i \neq j$, then $m \le 2N$.
2.  If the vectors are unit vectors and $\langle v_i, v_j \rangle \le -\epsilon < 0$ for all $i \neq j$, then $m \le 1 + 1/\epsilon$.
The proof for (2) involves analyzing the squared norm of the sum of the vectors, $\| \sum v_i \|^2 \ge 0$.

**Stage 3: Main Proof**
1.  **Setup:** Map the $m$ codewords of $C$ to $m$ unit vectors $\{v_i\}$ in $\mathbb{R}^{nq}$ using the Mapping Lemma.
2.  **Bound the Inner Product:** Since $\Delta(c_i, c_j) \ge d$:
    $$ \langle v_i, v_j \rangle \le 1 - \left( \frac{q}{q - 1} \right) \frac{d}{n} $$
3.  **Case 1: $d > (1 - 1/q)n$.** The inner product is negative. Let $\epsilon = (\frac{q}{q-1})\frac{d}{n} - 1 > 0$. From the Geometric Lemma (Part 2), $m \le 1+1/\epsilon$, which simplifies to:
    $$ m \le \frac{qd}{qd - (q-1)n} $$
4.  **Case 2: $d = (1 - 1/q)n$.** The inner product is $\le 0$. From the Geometric Lemma (Part 1), with $N=nq$:
    $$ m \le 2N = 2nq $$
This completes the proof.