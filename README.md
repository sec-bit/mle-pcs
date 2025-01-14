# MLE-PCS: Comparison of Multilinear Polynomial Commitment Schemes

*This README is a living document and will be updated as the project progresses through its milestones.*

## Table of Contents

- [MLE-PCS: Comparison of Multilinear Polynomial Commitment Schemes](#mle-pcs-comparison-of-multilinear-polynomial-commitment-schemes)
  - [Table of Contents](#table-of-contents)
  - [Background](#background)
  - [Project Purpose](#project-purpose)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Implementation Details](#implementation-details)
    - [Reference Implementations](#reference-implementations)
    - [Jupyter Notebooks](#jupyter-notebooks)
    - [Research Notes](#research-notes)
  - [Important Notices](#important-notices)
  - [PCS List](#pcs-list)
    - [On-going](#on-going)
    - [More PCS (Future work)](#more-pcs-future-work)
  - [Contributors](#contributors)
  - [References](#references)
  - [Acknowledgments](#acknowledgments)

## Background

Multilinear Polynomial Commitment Schemes (MLE PCS) are fundamental building blocks in the field of cryptography, particularly within zero-knowledge proofs. These schemes enable the commitment to a multilinear polynomial in such a way that the prover can later reveal evaluations of the polynomial at specific points without revealing the entire polynomial. Efficient and secure MLE PCS schemes are crucial for the development of scalable and practical zero-knowledge proof systems.

This repository, **mle-pcs**, is a research-driven project focused on the Comparison of Multilinear Polynomial Commitment Schemes. The research is supported by the Ethereum Foundation and aims to provide a comprehensive analysis of different schemes, their design philosophies, security properties, and performance metrics.

## Project Purpose

The primary objective of this project is to conduct a comprehensive comparison of various MLE PCS schemes. By implementing reference codes and analyzing their protocol designs, security parameters, and performance metrics, we aim to identify the strengths and weaknesses of each scheme.

## Features

- **Reference Implementations**: Python-based implementations of various MLE PCS schemes to deepen understanding.
- **Interactive Tutorials**: Jupyter notebooks serve as interactive playgrounds for experimenting with different schemes.
- **Comprehensive Notes**: Detailed research notes available in each folder, provided in both English and Chinese.
- **Future Blog Posts**: Planned blog posts will elaborate on the research findings and comparisons.

## Project Structure

The repository is organized to facilitate both research and experimental exploration:


<details>
  <summary>layout:</summary>

```
mle-pcs/
├── basefold/
│   ├── basefold-01.md
│   ├── basefold-01.zh.md
│   ├── basefold-02.md
│   ├── basefold-02.zh.md
│   └── ...
├── fri/
│   ├── BBHR18-FRI.md
│   ├── BBHR18-FRI.zh.md
│   ├── BCIKS20-proximity-gaps.md
│   ├── BCIKS20-proximity-gaps.zh.md
│   └── ...
├── fri-binius/
│   ├── binius-01.md
│   ├── binius-01.zh.md
│   ├── binius-02.md
│   ├── binius-02.zh.md
│   └── ...
├── zeromorph/
│   ├── zeromorph.md
│   ├── zeromorph.zh.md
│   ├── zeromorph_mapping_tutorial.ipynb
│   └── ...
├── src/
│   ├── Basefold.py
│   ├── Basefold.ipynb
│   ├── bcho_pcs.ipynb
│   ├── kzg10.ipynb
│   ├── zeromorph.ipynb
│   └── ... (other source files)
```

</details>

- **basefold/**: Contains research notes related to the BaseFold PCS scheme
- **fri/**: Focuses on the Fast Reed-Solomon Interactive Oracle Proofs of Proximity (FRI) scheme.
- **fri-binius/**: Explores the Binius-PCS scheme based on FRI.
- **zeromorph/**: Includes tutorials and notes on the Zeromorph PCS scheme.
- **src/**: Houses reference Python implementations and Jupyter notebooks for interactive experimentation.
- **test/**: Test cases for the implementations.
- ***.ipynb**: Jupyter notebooks for interactive playgrounds and tutorials.

## Implementation Details

### Reference Implementations

We have implemented reference code for several MLE PCS schemes using Python. Python was chosen for its flexibility and readability, facilitating a better understanding of the underlying concepts. These implementations serve as a foundation for further research and experimentation.

### Jupyter Notebooks

Interactive Jupyter Notebooks are provided to serve as playgrounds and tutorials for experimenting with different PCS schemes. These notebooks allow users to run code snippets, visualize results, and gain hands-on experience with the algorithms.

- [**Basefold.ipynb**](src/Basefold.ipynb): Tutorial and experiments related to the BaseFold PCS scheme.
- [**bcho_pcs.ipynb**](src/bcho_pcs.ipynb): Tutorial and experiments related to the BCHO PCS scheme.
- [**kzg10.ipynb**](src/kzg10.ipynb): Implementation and analysis of the KZG10 PCS scheme.
- [**zeromorph.ipynb**](src/zeromorph.ipynb): Tutorial and experiments related to the Zeromorph PCS scheme.
- [**zeromorph_mapping_tutorial.ipynb**](zeromorph/zeromorph_mapping_tutorial.ipynb): Step-by-step guide to the Zeromorph PCS mapping process.

### Research Notes

Comprehensive research notes are available within each relevant folder, provided in both English and Chinese. These notes document our understanding, analysis, and insights into each PCS scheme.

- [**basefold/**](basefold/): Detailed notes on the BaseFold scheme.
- [**fri/**](fri/): Insights and analysis on the FRI scheme.
- [**fri-binius/**](fri-binius/): Comprehensive exploration of the Binius-PCS scheme.
- [**zeromorph/**](zeromorph/): Tutorials and notes on Zeromorph PCS.

*You can also find the PDF version of the research notes at [https://sec-bit.github.io/mle-pcs/](https://sec-bit.github.io/mle-pcs/). Note PDF files may not be fully updated to the latest version.*

📌 **Request for Feedback**: These notes are open for proofreading and reviewing. We welcome any advice, corrections, or suggestions to improve the content. Your contributions are highly appreciated!

📅 **Upcoming Blog Posts**: In the future, we plan to polish and publish these notes as blog posts to reach a wider audience and share our findings more broadly.

## Important Notices

- **Research and Experimental Purpose Only**: This project is intended solely for research and experimental purposes.
- **Not for Production Use**: **Do not use this code in any production environment.** The implementations are reference codes aimed at understanding concepts better.
- **Educational Value**: The Python implementations provided are designed to be flexible and easy to understand, facilitating learning and further experimentation.

## PCS List 

### On-going

- Basefold 
    - [BaseFold: Efficient Field-Agnostic Polynomial Commitment Schemes from Foldable Codes](https://eprint.iacr.org/2023/1705)
- Binius-PCS (for binary fields)
    - [Proximity Testing with Logarithmic Randomness](https://eprint.iacr.org/2023/630)
    - [Succinct Arguments over Towers of Binary Fields](https://eprint.iacr.org/2023/1784)
    - [Polylogarithmic Proofs for Multilinears over Binary Towers](https://eprint.iacr.org/2024/504)
- FRI (for univariate polynomial only)
    - [Fast Reed-Solomon Interactive Oracle Proofs of Proximity](https://eccc.weizmann.ac.il/report/2017/134/download/)
    - [Worst-case to average case reductions for the distance to a code](https://www.math.toronto.edu/swastik/fri.pdf)
    - [DEEP-FRI: Sampling Outside the Box Improves Soundness](https://eprint.iacr.org/2019/336)
    - [Proximity Gaps for Reed-Solomon Codes](https://eprint.iacr.org/2020/654)
- Zeromorph (MLE-2-Uni adaptor)
    - [Zeromorph: Zero-Knowledge Multilinear-Evaluation Proofs from Homomorphic Univariate Commitments](https://eprint.iacr.org/2023/917)
- Virgo-PCS
    - [Transparent Polynomial Delegation and Its Applications to Zero Knowledge Proof](https://eprint.iacr.org/2019/1482)
- PH23(Logup)-PCS 
    - [Improving logarithmic derivative lookups using GKR](https://eprint.iacr.org/2023/1284)
- BCHO22(Gemini)-PCS 
    - [Gemini: Elastic SNARKs for Diverse Environments](https://eprint.iacr.org/2022/420)

### More PCS (Future work)

- Brakedown-PCS 
    - [Brakedown: Linear-time and field-agnostic SNARKs for R1CS](https://eprint.iacr.org/2021/1043)
- Orion-PCS
    - [Orion: Zero Knowledge Proof with Linear Prover Time](https://eprint.iacr.org/2022/1010)
    - [A Crack in the Firmament: Restoring Soundness of the Orion Proof System and More](https://eprint.iacr.org/2024/1164)
- Hyrax-PCS 
    - [Doubly-efficient zkSNARKs without trusted setup](https://eprint.iacr.org/2017/1132)
- Libra-PCS 
    - [Libra: Succinct Zero-Knowledge Proofs with Optimal Prover Computation](https://eprint.iacr.org/2019/317)

## Contributors

We encourage contributions from the community to enhance this project. If you would like to contribute, please fork the repository and submit a pull request or open an issue for discussion.

TODO: list current contributors

You can find guidelines for contributing to this project [here](CONTRIBUTING.md).

## References

- [ACFY24a] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "STIR: Reed-Solomon proximity testing with fewer queries." In _Annual International Cryptology Conference_, pp. 380-413. Cham: Springer Nature Switzerland, 2024.
- [ACFY24b] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "WHIR: Reed–Solomon Proximity Testing with Super-Fast Verification." _Cryptology ePrint Archive_ (2024).
- [BCH+22] Jonathan Bootle, Alessandro Chiesa, Yuncong Hu, and Michele Orru. "Gemini: Elastic SNARKs for diverse environments." In _Annual International Conference on the Theory and Applications of Cryptographic Techniques_, pp. 427-457. Cham: Springer International Publishing, 2022.
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.
- [BGKS20] Eli Ben-Sasson, Lior Goldberg, Swastik Kopparty, and Shubhangi Saraf. "DEEP-FRI: sampling outside the box improves soundness." _arXiv preprint arXiv:1903.12243_ (2019).
- [BBHR18] Eli Ben-Sasson, Iddo Bentov, Ynon Horesh, and Michael Riabzev. Fast Reed-Solomon Interactive Oracle Proofs of Proximity. In Proceedings of the 45th International Colloquium on Automata, Languages, and Programming (ICALP), 2018. Available online as Report 134-17 on Electronic Colloquium on Computational Complexity.
- [CFS17] Chiesa, Alessandro, Michael A. Forbes, and Nicholas Spooner. "A zero knowledge sumcheck and its applications." [*arXiv preprint arXiv:1704.02086* (2017)](https://eprint.iacr.org/2017/305).
- [CHMMVW19] Alessandro Chiesa, Yuncong Hu, Mary Maller, Pratyush Mishra, Psi Vesely, and Nicholas Ward. "Marlin: Preprocessing zkSNARKs with Universal and Updatable SRS." https://eprint.iacr.org/2019/1047
- [D24] Yuval Domb. "Really Complex Codes with Application to STARKs." _Cryptology ePrint Archive_ (2024). https://eprint.iacr.org/2024/1620
- [DP23] Diamond, Benjamin E., and Jim Posen. "Succinct arguments over towers of binary fields." Cryptology ePrint Archive (2023).
- [DP24] Diamond, Benjamin E., and Jim Posen. "Polylogarithmic Proofs for Multilinears over Binary Towers." Cryptology ePrint Archive (2024).
- [GLHQTZ24] Yanpei Guo, Xuanming Liu, Kexi Huang, Wenjie Qu, Tianyang Tao, and Jiaheng Zhang. "DeepFold: Efficient Multilinear Polynomial Commitment from Reed-Solomon Code and Its Application to Zero-knowledge Proofs." _Cryptology ePrint Archive_ (2024).
- [H24] Ulrich Haböck. "Basefold in the List Decoding Regime." _Cryptology ePrint Archive_(2024).
- [HLP24] Ulrich Haböck, David Levit, and Shahar Papini. "Circle STARKs." _Cryptology ePrint Archive_ (2024). https://eprint.iacr.org/2024/278
- [KT23] Kohrita, Tohru, and Patrick Towa. "Zeromorph: Zero-knowledge multilinear-evaluation proofs from homomorphic univariate commitments." Cryptology ePrint Archive (2023).
- [KZG10] Kate, Aniket, Gregory M. Zaverucha, and Ian Goldberg. "Constant-size commitments to polynomials and their applications." Advances in Cryptology-ASIACRYPT 2010: 16th International Conference on the Theory and Application of Cryptology and Information Security, Singapore, December 5-9, 2010. Proceedings 16. Springer Berlin Heidelberg, 2010.
- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/1284
- [PST13] Papamanthou, Charalampos, Elaine Shi, and Roberto Tamassia. "Signatures of correct computation." Theory of Cryptography Conference. Berlin, Heidelberg: Springer Berlin Heidelberg, 2013. https://eprint.iacr.org/2011/587
- [XZZPS19] Tiancheng Xie, Jiaheng Zhang, Yupeng Zhang, Charalampos Papamanthou, and Dawn Song. "Libra: Succinct Zero-Knowledge Proofs with Optimal Prover Computation." Cryptology ePrint Archive (2019). https://eprint.iacr.org/2019/317
- [ZCF23] Hadas Zeilberger, Binyi Chen, and Ben Fisch. "BaseFold: efficient field-agnostic polynomial commitment schemes from foldable codes." In *Annual International Cryptology Conference*, pp. 138-169. Cham: Springer Nature Switzerland, 2024.
- [ZGKPP17] Yupeng Zhang, Daniel Genkin, Jonathan Katz, Dimitrios Papadopoulos, and Charalampos Papamanthou. "A zero-knowledge version of vSQL." _Cryptology ePrint Archive_ (2017). https://eprint.iacr.org/2017/1146
- [ZXZS19] Jiaheng Zhang, Tiancheng Xie, Yupeng Zhang, and Dawn Song. "Transparent Polynomial Delegation and Its Applications to Zero Knowledge Proof". In 2020 IEEE Symposium on Security and Privacy (SP), pp. 859-876. IEEE, 2020. https://eprint.iacr.org/2019/1482.

More are listed in the research notes.

## Acknowledgments

We extend our gratitude to the **Ethereum Foundation** for funding this research. Special thanks to all the contributors and the cryptographic community for their continuous support and valuable insights.

---

**Disclaimer**: This project is for research and experimental purposes only. Please do not use this code in any production environment.

