# KZG-Soundness-zh-1

- Tianyu ZHENG <tian-yu.zheng@connect.polyu.hk>

KZG多项式承诺方案因其简洁的证明长度、高效的验证算法以及可更新的参考字符串（SRS）等优点，被广泛应用于 zk-SNARKs 系统、区块链扩容方案（如 Verkle 树）以及数据可用性解决方案中。然而，不同的应用场景对 KZG 的安全性有着不同的要求。从 KZG10 论文开始，研究者们对 KZG 的安全性进行了深入研究。以下是与 zk-SNARKs 相关的主要研究：

- **KZG10:** KZG 多项式承诺方案的第一篇论文，仅证明了方案满足 evaluation binding 性质；
- **Sonic:** 将 KZG 用于构造 zk-SNARK，并首次给出了在 AGM 中的 KZG extractability 证明；
- **Plonk:** 同样给出了 AGM 中的 KZG extractability 证明，但其定义存在一些缺陷；
- **Marlin:** 给出了形式化的定义，并同时在标准模型和 AGM 中给出 extractability 证明；
- **AGMOS:** 提出了AGMOS 假设，并基于一个 falsifiable 假设证明 KZG extractability；
- **LPS24:** 仅在 ROM 中基于 falsifiable 假设证明 KZG extractability。

在这篇文章中，我们首先回顾一下 KZG10 论文中对 evaluation binding 性质的讨论。

接下来，我们介绍 KZG extractability 性质的必要性，并给出该性质在 AGM 中的证明。

最后我们简单提及 AGMOS 中的一些结论。

# Soundness in KZG10

**【KZG10 协议】**

- **Setup:** 给定 $\mathbb{G}_1, \mathbb{G}_2, \mathbb{G}_T, e:\mathbb{G}_1\times \mathbb{G}_2 \mapsto \mathbb{G}_T$ ，随机选取 $\tau \in \mathbb{F}$ 并计算

$$
SRS = ([1]_1,[\tau]_1,[\tau^2]_1,\ldots,[\tau^{D}]_1, [1]_2, [\tau]_2)
$$

- **Commit:** 证明者计算 $d$ 阶一元多项式 $f(X) \in \mathbb{F}[X]$ 生成承诺的承诺满足 $C_f = [f(\tau)]$

$$
C_f = \mathsf{Commit}(f(X)) = f_0\cdot[1]_1+f_1\cdot[\tau]_1+ \cdots + f_d\cdot[\tau^d]_1   
$$

- **Open:** 证明者在 $z$ 点上公开多项式的值为 $f(z)=v$，并生成商多项式

$$
q(X) = \frac{f(X)-f(z)}{X-z}
$$

- 生成证明 $\pi = [q(\tau)]_1$

$$
\pi = q_0\cdot[1]_1 + q_1\cdot[\tau]_1+\cdots+q_d\cdot[\tau^d]_1 
$$

- **Check:** 验证者检查求值证明

$$
e([f(\tau)]_1-f(z)\cdot[1]_1, [1]_2) = e([q(\tau)]_1, [\tau -z]_2) 
$$

**【Evaluation Binding】**

给定一个 $SRS$，如果对于任意敌手 $\mathcal{A}$，找到一个多项式承诺值 $C_f$ 和点 $z$，生成两个分别关于 $f(z) = v, f(z) = v'$ 的合法证明 $\pi, \pi'$ 的概率都是可以忽略的，那么我们认为上述多项式承诺算法满足 evaluation binding 性质。

证明这一结论需要用到 **t-Strong Diffie-Hellman Assumption** 这个困难问题假设：

令 $\alpha \in \mathbb{F}$ 为随机值，给定输入 $([1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^t]_1, [\alpha]_2)$，对任意敌手 $\mathcal{A}$，找到一个 $\mathbb{G}_1$ 上元素 $[\frac{1}{\alpha+c}]_1$ 是困难的，其中值 $c$ 可以是  $\mathbb{F}/\{-\alpha\}$  中的任意值。

**【安全证明】**

假设存在一个敌手 $\mathcal{A}$ 能够破解 KZG10 多项式承诺方案的 evaluation binding 性质：即给定输入 $SRS$， $\mathcal{A}$ 计算出一个承诺值 $C_f$ 及两个元组 $(z, v, \pi), (z, v', \pi')$，分别能够通过验证者执行的 **Check** 算法。那么我们可以基于 $\mathcal{A}$ 构造一个高效算法 $\mathcal{B}$，$\mathcal{B}$ 能够破解 t-SDH 假设。

简单来说，我们证明，如果存在 $\mathcal{A}$，那么我们可以构造 $\mathcal{B}$。逆否命题同样成立： 如果我们不能构造 $\mathcal{B}$，那么 $\mathcal{A}$ 不存在。实际上，由于算法 $\mathcal{B}$（即破解 t-SDH 假设的算法）被公认为难以构造的，我们可以得到结论，攻击 KZG10 的  
$\mathcal{A}$ 同样不存在。

接下来，我们只需要给出 $\mathcal{B}$ 的构造算法即可： 

1.  $\mathcal{B}$ 将一个待破解的 t-SDH 实例 $(\mathbb{G}_1, [1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^t]_1, [\alpha]_2)$ 作为 $SRS$ 发送给  
$\mathcal{A}$
2. 根据假设， 
$\mathcal{A}$ 可以在多项式时间内以不可忽略的概率输出 $C_f, (z, v, \pi), (z, v', \pi')$ 满足

$$
e([C_f-v\cdot[1]_1, [1]_2) = e(\pi, [\alpha-z]_2)\\ e([C_f-v'\cdot[1]_1, [1]_2) = e(\pi', [\alpha-z]_2)
$$

1.  不妨假设 $\pi = [q(\alpha)]_1, \pi' = [q'(\alpha)]_1$，它们满足 

$$
q(\alpha) \cdot (\alpha-z) + v= f(\alpha) = q'(\alpha) \cdot (\alpha-z) + v' \\ \frac{q(\alpha)/q'(\alpha)}{v'-v} = \frac{1}{\alpha-z} 
$$

注意到右式即为我们的目标关系式，因此 $\mathcal{B}$ 只需要计算下式便能够破解 t-SDH 假设 

$$
\frac{(\pi-\pi')}{v'-v} = [\frac{1}{\alpha-z}]_1
$$

# Extractable KZG

**【为什么需要 Extractability?】**

上述 evaluation binding 性质只是保证了证明者没法在同一个点上打开两个不同的值，该性质的确能够满足某一些应用场景的要求，例如成员证明。但随着 SNARK 的发展，KZG10 等多项式承诺证明被用于构造 SNARK，将一个 IOP（Interactive Oracle Proof）中的多项式 Oracle 实例化。而 IOP 所需要的安全性质对 KZG 提出了新的要求。

如果只针对一个理想的 IOP 协议，其 Knowledge Soundness 是十分容易保证的。根据 HypePlonk 中的结论，当一个 IOP 满足soundness 性质，那么它同样满足 Knowledge Soundness 性质：存在一个提取器，它只需要向一个多项式 oracle 问询 $d+1$ 次，便能够自己计算出整个多项式。

然而，当我们考虑将 IOP 中的多项式 Oracles 用 PCS 实例化之后，要保证实例化的 SNARK 满足 Knowledge Soundness 性质就没有那么容易了。

相比较于 IOP 中证明者发送包含一整个多项式的 oracle（在 IOP 模型中，oracle 的长度和多项式是相同的，只不过验证者没有完全读取它），SNARK 中证明者只发送了多项式的承诺，该承诺只包含很少一部分信息：仅仅是多项式在几个点上的取值。

因此，我们只有保证多项式承诺本身是**“可提取的“（Extractable）**，才能够保证 SNARK 的 Knowledge Soundness。（详细论证可以参考 Interactive Oracle Proofs by Eli Ben-Sasson et al. 以及 DARK）

Sonic，Plonk，Marlin 等基于多项式承诺的 SNARK 对这一问题都进行了先后讨论。下面我们主要参考 Sonic 中的描述，介绍基于 AGM 模型的 KZG10 Extractability 证明。

**【Algebraic Group Model】**

AGM（Algebraic Group Model）是一种理想化的安全模型，它的假设强于标准模型（Standard Model），但弱于 GGM（Generic Group Model）。

在 AGM 中，我们假设敌手算法 $\mathcal{A}_{alg}$ 是 ”algebraic“ 的：即，任何时候 $\mathcal{A}_{alg}$ 输出一个群元素 $Z$，它会同时输出对 $Z$ 的一个表示（representation ），该表示包含了一个域元素向量 $(z_1,...,z_t) \in F^t$ 来描述群元素 $Z$ 是如何被计算出来的，即 $Z = \prod_{i=1}^t g_i^{z_i}$，其中 $*\{ g_1,...,g_t\}$* 是 $\mathcal{A}_{alg}$ 从协议开始到现在所收到的所有的群元素列表。

与标准模型相同，AGM 下我们同样使用归约来证明安全关系。

# **Extractability** under AGM

【**Extractability 定义**】

对于任何代数敌手  $\mathcal{A}_{alg}$，如果它能够输出一个合法的 KZG 求值证明，那么一定存在另一个高效的算法  $\mathcal{B}_{alg}$，能够提取出承诺 $C_f$ 的公开值 $f(X)$，满足 $f(z) = v$

【**q-DLOG 假设**】

令 $\alpha \in \mathbb{F}$ 为随机值，给定输入 $([1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^t]_1, [1]_2,[\alpha]_2)$，对任意敌手 $\mathcal{A}$，计算出 $\alpha$ 是困难的。

**【安全证明】**

**目标：**$Adv_{\mathcal{A}_{alg}}^{Extract} \leq Adv_{\mathcal{B}_{alg}}^{qDL}$，即， $\mathcal{A}_{alg}$ 破解 KZG 的 extractability 可以被归约到  $\mathcal{B}_{alg}$ 破解 q-DLOG 困难问题。

**证明：**假设存在敌手算法  $\mathcal{A}_{alg}$，能够在不知道正确 $f(X)$ 的情况下给出合法的证明。那么我们可以构造一个算法  $\mathcal{B}_{alg}$，根据其输入的 q-DLOG 问题实例 $([1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^D]_1, [1]_2,[\alpha]_2)$ 来和  $\mathcal{A}_{alg}$ 模拟一个 extractability game:

- $\mathcal{B}_{alg}$ 将 q-DLOG 实例作为 $SRS$ 发送给  $\mathcal{A}_{alg}$

$$
SRS = ([1]_1,[\alpha]_1,[\alpha^2]_1,\ldots,[\alpha^{D}]_1, [1]_2, [\alpha]_2)
$$

- 根据假设， $\mathcal{A}_{alg}$ 可以在多项式时间内以不可忽略的概率输出消息 $C_f, (z, v, \pi)$ 通过验证
- 又由于  $\mathcal{A}_{alg}$ 是 algebraic 算法，它会同时输出群元素 $C_f, \pi$ 对应的 representations，记作 $f'(X), q'(X)$，满足

$$
C_f = [f'(\alpha)]_1, \pi = [q'(\alpha)]_1
$$

- 同时，由于证明通过验证，$C_f, \pi$ 满足

$$
e(C_f-v\cdot[1]_1, [1]_2) = e(\pi, [\alpha -z]_2) 
$$

- 根据验证等式中指数满足的关系， $\mathcal{B}_{alg}$ 可以用  $f'(X), q'(X)$ 来构造一个多项式 $Q(X)$

$$
Q(X) = f'(X) - v - (X-z)q'(X)
$$

- 如果 $Q(X) = 0$，那么  $\mathcal{B}_{alg}$ 中止算法。
- 如果 $Q(X) \neq 0$，  $\mathcal{B}_{alg}$ 对该多项式进行因式分解，并得到其全部的根。
- 依次测试每个根是否满足给定的 q-DLOG 实例，如果某个 $x$ 满足，则输出 $x$ 作为 q-DLOG 困难问题的解。

我们论证在上述归约中，如果  $\mathcal{A}_{alg}$ 成功的概率是一个不可忽略的 $\epsilon$，那么  $\mathcal{B}_{alg}$ 成功的概率为 $\epsilon+\mathsf{negl}(\lambda)$。显然  $\mathcal{B}_{alg}$ 不能输出一个 q-DLOG 问题的解这一事件可能在两个地方发生：

1.  $Q(X) = 0$，那么  $\mathcal{B}_{alg}$ 中止算法。由 $Q(X) = 0$ 可以推出 $f'(X) - v = (X-z)q'(X)$，即一定有 $f'(z) = v$，该结论与前提假设相矛盾。
2.   $\mathcal{B}_{alg}$ 因式分解得到的根均不满足 q-DLOG 实例。因为  $\mathcal{B}_{alg}$ 没有在上一步中止算法，可知 $Q(X) \neq 0$，同时  $\mathcal{A}_{alg}$ 输出的证明又能够通过验证，即 $[f'(\alpha)-v]_T = [(\alpha-z)q'(\alpha)]_T$。除非  $\mathcal{A}_{alg}$ 破解了 $G_T$ 上的DL问题，否则 $\alpha$ 一定是 $Q(X)$ 的一个根。

# AGMOS

Lipmaa等人最近提出了AGMOS（Algebraic Group Model with Oblivious Sampling）。AGMOS是AGM的一种更现实的变体，它赋予对手在不知道离散对数的情况下模糊采样群元素的额外能力（例如实际中的 hash-to-group）。

此外，Lipmaa 还指出在实际协议设计中存在着两种不同的 KZG extractability 定义

- 提取器算法在 **Commit** 和 **Open** 阶段之后提取多项式，如 Marlin 和 Sonic
- 提取器算法仅在 **Commit** 阶段之后提取多项式，如 Plonk 和 Lunar

Lipmaa 在文章中指出，后者会导致一种在 AGM 下安全但是在标准模型下不安全的 spurious knowledge assumption。

[KZG10] Kate, Aniket, Gregory M. Zaverucha, and Ian Goldberg. "Constant-size commitments to polynomials and their applications." *International conference on the theory and application of cryptology and information security*. Berlin, Heidelberg: Springer Berlin Heidelberg, 2010.

[Sonic] Maller, Mary, et al. "Sonic: Zero-knowledge SNARKs from linear-size universal and updatable structured reference strings." *Proceedings of the 2019 ACM SIGSAC conference on computer and communications security*. 2019.

[Plonk] Gabizon, Ariel, Zachary J. Williamson, and Oana Ciobotaru. "Plonk: Permutations over lagrange-bases for oecumenical noninteractive arguments of knowledge." *Cryptology ePrint Archive* (2019).

[Marlin] Chiesa, Alessandro, et al. "Marlin: Preprocessing zkSNARKs with universal and updatable SRS." *Advances in Cryptology–EUROCRYPT 2020: 39th Annual International Conference on the Theory and Applications of Cryptographic Techniques, Zagreb, Croatia, May 10–14, 2020, Proceedings, Part I 39*. Springer International Publishing, 2020.

[AGMOS] Lipmaa, Helger, Roberto Parisella, and Janno Siim. "Algebraic group model with oblivious sampling." *Theory of Cryptography Conference*. Cham: Springer Nature Switzerland, 2023.

[LPS24] Lipmaa, Helger, Roberto Parisella, and Janno Siim. "Constant-size zk-SNARKs in ROM from falsifiable assumptions." *Annual International Conference on the Theory and Applications of Cryptographic Techniques*. Cham: Springer Nature Switzerland, 2024.