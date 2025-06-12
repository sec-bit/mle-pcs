# Montgomery Reduction

In finite field operations, we frequently need to perform mod N calculations. For exponential operations involving consecutive multiplications, Montgomery Reduction provides better performance optimization.

The core idea of Montgomery Reduction is to convert operands to a special Montgomery Form, where all division operations can be significantly simplified.

Let's understand this through a concrete example:

Given modulus N = 97, we need to calculate $(a \cdot b) \bmod N$. The traditional method requires performing a modular operation on the result of $a \cdot b$, which involves costly division operations.

### Montgomery Form Conversion
1. Choose R = 100 (usually selected as a power of 2; for demonstration purposes we use 100, which allows us to simply take the last digits or remove trailing zeros in base 10)
2. For inputs a = 15, b = 32:
   - $T_a = aR \bmod N = 45$
   - $T_b = bR \bmod N = 96$

### Montgomery Multiplication Process
1. Calculate the product in Montgomery Form:
   $T_r = T_a \cdot T_b = 45 \cdot 96 = 4320$

2. Result conversion:
   - Since we've gone through two Montgomery Form conversions, the result contains an $R^2$ term, and we need to eliminate one $R$
   - We need to adjust $T_r$ without changing its value modulo $N$, making it divisible by $R$
   - We can add multiples of $N$ to $T$ without affecting the result modulo $N$, giving us $T + xN$
   - We need a suitable $x$ that makes $T + xN$ divisible by $R$
   - Through the congruence equation $T + xN \equiv 0 \pmod{R}$, we get $x = T \cdot (-\frac{1}{N}) \bmod R$
   - We denote $-\frac{1}{N}$ as $N'$, where $N' = -\frac{1}{N} \bmod R = 67$ (pre-computed)
   - The $x$ calculated above is the $m$ in Montgomery Reduction, and $t = T + mN$

3. Specific calculations:
   First Montgomery Reduction ($aR \cdot bR/R$):

   $m = T_r \cdot N' \bmod R = 4320 \cdot 67 \bmod 100 = 289440 \bmod 100 = 40$
   (Note: mod 100 in base 10 means taking the last two digits)

   $t = (T_r + m \cdot N) / R = (4320 + 40 \cdot 97) / 100 = 8200 / 100 = 82 = abR$ 
   (Note: dividing by 100 in base 10 means removing trailing zeros)

   Second Montgomery Reduction ($abR/R$):

   $m' = t \cdot N' \bmod R = 82 \cdot 67 \bmod 100 = 94$

   $t' = (t + m' \cdot N) / R = (82 + 94 \cdot 97) / 100 = 92 = ab$

### Advantage Analysis
Although Montgomery Reduction may not save much computational resources for a single operation (conversion to Montgomery Form still requires mod N operations), its advantages become very clear in scenarios requiring continuous modular multiplication (such as modular exponentiation):

1. Modular exponentiation example: calculate $a^5 \bmod N$
   - Traditional method requires mod N operation after each multiplication
   - Using Montgomery Form:
     - Initial conversion: $T_a = aR \bmod N$
     - No division needed for intermediate operations: $T_a \cdot T_a / R = (aR \cdot aR) / R = a^2R$
     - Only need to convert back to original form at the end

2. Main advantages:
   - Avoids mod N operations in intermediate steps
   - Eliminates most division operations
   - Suitable for hardware implementation (when R is chosen as a power of 2, division and modulo can be completed using shift and bitwise AND operations)
   - Especially suitable for scenarios requiring continuous modular multiplications

### Engineering Implementation
In practical engineering, we typically encode an element a into Montgomery Form by multiplying it by $R^2$. The advantages of this approach are:

1. Montgomery Reduction and multiplication can be merged into a unified mul function:
   - $\text{mul}(a, b) = ab/R$

2. Both encode and decode can use the same mul function:
   - $\text{encode}(a) = \text{mul}(a, R^2) = aR^2/R = aR$
   - $\text{decode}(T_a) = \text{mul}(T_a, 1) = aR/R = a$

This unified implementation makes the code more concise, and when R is chosen as a power of 2, all division and modulo operations can be efficiently performed through shift and bitwise AND operations.

For modular exponentiation, we can see the advantages of Montgomery multiplication:
1. Traditional algorithm:
   $a^5 = ((((a \cdot a) \bmod N) \cdot a) \bmod N) \cdot a) \bmod N) \cdot a) \bmod N$
   Each step requires expensive division operations for modular reduction

2. Montgomery algorithm:
   - $T_a = aR \bmod N$
   - $T_a \cdot T_a / R = a^2R$
   - $(a^2R \cdot aR) / R = a^3R$
   - $(a^3R \cdot aR) / R = a^4R$
   - $(a^4R \cdot aR) / R = a^5R$
   - $\text{decode}(a^5R) = a^5$

All intermediate steps only require simple shift operations, greatly improving performance.