# Coding Theory Learning 

This section is a comprehensive exploration of error-correcting codes! It contains a structured learning path that helps you understand the fundamental concepts of coding theory all the way up to  list decoding algorithms. Each file builds upon the previous ones, creating a cohesive understanding of how we can reliably transmit information through noisy channels.

##  Overview

The materials are progress from basic concepts to advanced algorithms. Here's the recommended reading order:

### 1. **Foundation** 

**Start Here:** [`An Introduction to Error-Correcting Codes.md`](An%20Introduction%20to%20Error-Correcting%20Codes.md)

This  blog post introduces the core problem of reliable communication over noisy channels:

- The fundamental trade-off between redundancy and error correction capability
- Formal definitions of codes, rates, distances, and error correction
- Simple examples like repetition codes and parity codes
- The concept of unique decoding and its limitations

**Key Concepts:** Alphabet, block length, code rate, minimum distance, encoding/decoding functions, unique decoding radius

### 2. **Theoretical Limits** 

**Next:** [`Entropy Function and Code Bounds.md`](Entropy%20Function%20and%20Code%20Bounds.md)

Dive deep into the mathematical foundations that govern what's possible in coding theory:

- The q-ary entropy function and its connection to Hamming ball volumes
- Four fundamental bounds: Hamming, Gilbert-Varshamov, Singleton, and Plotkin
- The achievable region for code parameters (rate vs. distance trade-offs)
- Asymptotic analysis of code performance

**Key Concepts:** Entropy function, Hamming balls, code bounds, achievable regions, asymptotic analysis

### 3. **Practical Implementation** 

**Then:** [`Reed-Solomon-Codes.ipynb`](Reed-Solomon-Codes.ipynb)

Explore one of the most famous and practical error-correcting codes:

- Polynomials over finite fields and field extensions
- Construction of Reed-Solomon codes using polynomial evaluation
- Encoding and decoding procedures
- Implementation details and examples

**Key Concepts:** Finite fields, polynomial evaluation, RS code construction, encoding/decoding

### 4. **Beyond Worst-Case: Probabilistic Models** 

**Continue:** [`Shannon-Theorem.ipynb`](Shannon-Theorem.ipynb)

Shannon Theorem for understanding the communication by modeling noise probabilistically:

- Shannon's communication model and channel capacity
- Binary Symmetric Channel (BSC) and other stochastic channels
- The gap between Hamming (worst-case) and Shannon (probabilistic) approaches
- Why unique decoding falls short of Shannon's limits

**Key Concepts:** Channel capacity, stochastic noise models, Shannon's theorem, BSC, qSC

### 5. **Unique Decoding Algorithms** 

**Next:** [`Unique-Decoding-Algorithm.ipynb`](Unique-Decoding-Algorithm.ipynb)

Learn the first practical decoding algorithm for Reed-Solomon codes:

- The Welch-Berlekamp algorithm for unique decoding
- Geometric interpretation of the decoding problem
- Error-locator polynomials and their properties
- Complete implementation with examples

**Key Concepts:** Welch-Berlekamp algorithm, error-locator polynomials, geometric decoding, unique decoding implementation

### 6. **Breaking the Unique Decoding Barrier** 

**Then:** [`List-Decoding.ipynb`](List-Decoding.ipynb)

Discover how to go beyond the limitations of unique decoding:

- The motivation for list decoding
- Visualizing the "bad examples" that break unique decoding
- How list decoding bridges the gap between Hamming and Shannon limits
- The Johnson radius and its significance

**Key Concepts:** List decoding motivation, Johnson radius, decoding beyond half-distance, bridging Hamming-Shannon gap

### 7. **List Decoding Algorithms - Part 1** 

**Continue:** [`List-Decoding-Algorithms-(Part 1).ipynb`](List-Decoding-Algorithms-%28Part%201%29.ipynb)

Implement the Sudan algorithm, the first practical list decoding method:

- Sudan's algorithm for Reed-Solomon codes
- Interpolation and root-finding steps
- Weighted degree constraints
- Complete implementation with examples

**Key Concepts:** Sudan algorithm, interpolation, weighted degrees, root-finding

### 8. **List Decoding Algorithms - Part 2** 

**Next:** [`List-Decoding-Algorithms-(Part 2).ipynb`](List-Decoding-Algorithms-%28Part%202%29.ipynb)

Explore Algorithm 2, an improved version of Sudan's approach:

- Enhanced interpolation techniques
- Better handling of weighted degree bounds
- Improved error correction capabilities
- Practical implementation details

**Key Concepts:** Algorithm 2, enhanced interpolation, improved bounds, better error correction

### 9. **List Decoding Algorithms - Part 3** 

**Finally:** [`List-Decoding-Algorithms-(Part 3).ipynb`](List-Decoding-Algorithms-%28Part%203%29.ipynb)

The Guruswami-Sudan algorithm with multiplicities:

- Multiplicity-based interpolation
- The power of using multiplicities s > 1
- implementation using SageMath

**Key Concepts:** Guruswami-Sudan algorithm, multiplicities, advanced interpolation, algorithm comparison


## Technical Requirements

- **Python 3.x** with NumPy
- **SageMath** 
- Basic familiarity with:
  - Linear algebra
  - Polynomial arithmetic
  - Finite fields
  - Probability theory

## File Structure

```
coding-theory/
├── README.md                                    # This file
├── An Introduction to Error-Correcting Codes.md # Foundation
├── Entropy Function and Code Bounds.md          # Theoretical limits
├── Reed-Solomon-Codes.ipynb                    # RS codes implementation
├── Shannon-Theorem.ipynb                       # Probabilistic models
├── Unique-Decoding-Algorithm.ipynb             # Welch-Berlekamp
├── List-Decoding.ipynb                         # List decoding motivation
├── List-Decoding-Algorithms-(Part 1).ipynb     # Sudan algorithm
├── List-Decoding-Algorithms-(Part 2).ipynb     # Algorithm 2
├── List-Decoding-Algorithms-(Part 3).ipynb     # Guruswami-Sudan
└── imgs/                                       # Supporting images
    ├── image_bad_examples.png
    ├── image_bec.png
    ├── image_bsc.png
    ├── image_channel_diagram.png
    ├── image_hamming_bound.png
    ├── image_unique_decoding_1.png
    └── image_unique_decoding_2.png
```

## Getting Started

1. **Start with the Introduction**: Read `An Introduction to Error-Correcting Codes.md` to understand the fundamental concepts
2. **Follow the Sequence**: Work through the files in the order listed above
3. **Run the Notebooks**: Execute the Jupyter notebooks to see algorithms in action
4. **Experiment**: Modify parameters and see how they affect performance

## Key Insights 

- **The Fundamental Trade-off**: Higher error correction requires more redundancy (lower rate)
- **The Hamming-Shannon Gap**: Unique decoding can only handle half the errors that Shannon's theory suggests is possible
- **The Power of List Decoding**: By relaxing the requirement for a unique answer, we can correct many more errors
- **The Evolution of Algorithms**: From simple unique decoding to sophisticated multiplicity-based list decoding

## Contributing

This is an educational resource. If you find errors or have suggestions for improvement, please feel free to contribute!

## Additional Resources

- **Books**: "Essential Coding Theory" by Guruswami, Rudra, and Sudan
- **Papers**: Original papers by Sudan, Guruswami, and Sudan on list decoding



