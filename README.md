# MLE-PCS: Comparison of Multilinear Polynomial Commitment Schemes

*This README is a living document and will be updated as the project progresses through its milestones.*

## Table of Contents

- [Background](#background)
- [Project Purpose](#project-purpose)
- [Project Structure](#project-structure)
- [Implementation Details](#implementation-details)
  - [Reference Implementations](#reference-implementations)
  - [Jupyter Notebooks](#jupyter-notebooks)
  - [Research Notes](#research-notes)
- [Features](#features)
- [Important Notices](#important-notices)
- [Future Work](#future-work)
- [Contributors](#contributors)
- [References](#references)
- [Acknowledgments](#acknowledgments)

## Background

Multilinear Polynomial Commitment Schemes (MLE PCS) are fundamental building blocks in the field of cryptography, particularly within zero-knowledge proofs. These schemes enable the commitment to a multilinear polynomial in such a way that the prover can later reveal evaluations of the polynomial at specific points without revealing the entire polynomial. Efficient and secure MLE PCS schemes are crucial for the development of scalable and practical zero-knowledge proof systems.

This repository, **mle-pcs**, is a research-driven project focused on the Comparison of Multilinear Polynomial Commitment Schemes. The research is supported by the Ethereum Foundation and aims to provide a comprehensive analysis of different schemes, their design philosophies, security properties, and performance metrics.

## Project Purpose

The primary objective of this project is to conduct a comprehensive comparison of various MLE PCS schemes. By implementing reference codes and analyzing their protocol designs, security parameters, and performance metrics, we aim to identify the strengths and weaknesses of each scheme.

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

TODO: add links to the notebooks

- **Basefold.ipynb**: Tutorial and experiments related to the BaseFold PCS scheme.
- **bcho_pcs.ipynb**: Tutorial and experiments related to the BCHO PCS scheme.
- **kzg10.ipynb**: Implementation and analysis of the KZG10 PCS scheme.
- **zeromorph.ipynb**: Tutorial and experiments related to the Zeromorph PCS scheme.
- **zeromorph_mapping_tutorial.ipynb**: Step-by-step guide to the Zeromorph PCS mapping process.

### Research Notes

Comprehensive research notes are available within each relevant folder, provided in both English and Chinese. These notes document our understanding, analysis, and insights into each PCS scheme.

TODO: add links to the notes

- **basefold/**: Detailed notes on the BaseFold scheme.
- **fri/**: Insights and analysis on the FRI scheme.
- **fri-binius/**: Comprehensive exploration of the Binius-PCS scheme.
- **zeromorph/**: Tutorials and notes on Zeromorph PCS.

📌 **Request for Feedback**: These notes are open for proofreading and reviewing. We welcome any advice, corrections, or suggestions to improve the content. Your contributions are highly appreciated!

📅 **Upcoming Blog Posts**: In the future, we plan to polish and publish these notes as blog posts to reach a wider audience and share our findings more broadly.

## Features

- **Reference Implementations**: Python-based implementations of various MLE PCS schemes to deepen understanding.
- **Interactive Tutorials**: Jupyter notebooks serve as interactive playgrounds for experimenting with different schemes.
- **Comprehensive Notes**: Detailed research notes available in each folder, provided in both English and Chinese.
- **Future Blog Posts**: Planned blog posts will elaborate on the research findings and comparisons.

## Important Notices

- **Research and Experimental Purpose Only**: This project is intended solely for research and experimental purposes.
- **Not for Production Use**: **Do not use this code in any production environment.** The implementations are reference codes aimed at understanding concepts better.
- **Educational Value**: The Python implementations provided are designed to be flexible and easy to understand, facilitating learning and further experimentation.

## PCS List 

### On-going

- Basefold 
    - [BaseFold: Efficient Field-Agnostic Polynomial Commitment Schemes from Foldable Codes
](https://eprint.iacr.org/2023/1705)
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


### More PCS (Future work)

- Brakedown-PCS 
    - [Brakedown: Linear-time and field-agnostic SNARKs for R1CS](https://eprint.iacr.org/2021/1043)
- Orion-PCS
    - [Orion: Zero Knowledge Proof with Linear Prover Time](https://eprint.iacr.org/2022/1010)
    - [A Crack in the Firmament: Restoring Soundness of the Orion Proof System and More](https://eprint.iacr.org/2024/1164)
- PH23(Logup)-PCS 
    - [Improving logarithmic derivative lookups using GKR](https://eprint.iacr.org/2023/1284)
- BCHO22(Gemini)-PCS 
    - [Gemini: Elastic SNARKs for Diverse Environments](https://eprint.iacr.org/2022/420)
- Hyrax-PCS 
    - [Doubly-efficient zkSNARKs without trusted setup](https://eprint.iacr.org/2017/1132)
- Libra-PCS 
    - [Libra: Succinct Zero-Knowledge Proofs with Optimal Prover Computation](https://eprint.iacr.org/2019/317)
- Virgo-PCS
    - [Transparent Polynomial Delegation and Its Applications to Zero Knowledge Proof](https://eprint.iacr.org/2019/1482)


## Contributors

We encourage contributions from the community to enhance this project. If you would like to contribute, please fork the repository and submit a pull request or open an issue for discussion.

TODO: list current contributors

## References

- [DP23] Diamond, Benjamin E., and Jim Posen. "Succinct arguments over towers of binary fields." Cryptology ePrint Archive (2023).
- [KT23] Kohrita, Tohru, and Patrick Towa. "Zeromorph: Zero-knowledge multilinear-evaluation proofs from homomorphic univariate commitments." Cryptology ePrint Archive (2023).
- [BBHR18] Eli Ben-Sasson, Iddo Bentov, Ynon Horesh, and Michael Riabzev. Fast Reed-Solomon Interactive Oracle Proofs of Proximity. In Proceedings of the 45th International Colloquium on Automata, Languages, and Programming (ICALP), 2018. Available online as Report 134-17 on Electronic Colloquium on Computational Complexity.
- [ZCF23] Hadas Zeilberger, Binyi Chen, and Ben Fisch. "BaseFold: efficient field-agnostic polynomial commitment schemes from foldable codes." In *Annual International Cryptology Conference*, pp. 138-169. Cham: Springer Nature Switzerland, 2024.
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.
- [DP24] Diamond, Benjamin E., and Jim Posen. "Polylogarithmic Proofs for Multilinears over Binary Towers." Cryptology ePrint Archive (2024).

More are listed in the research notes.

## Acknowledgments

We extend our gratitude to the **Ethereum Foundation** for funding this research. Special thanks to all the contributors and the cryptographic community for their continuous support and valuable insights.

---

**Disclaimer**: This project is for research and experimental purposes only. Please do not use this code in any production environment.

