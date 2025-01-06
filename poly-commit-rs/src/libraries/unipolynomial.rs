use std::ops::{Add, Mul, Neg, Sub};

#[derive(Debug, Clone)]
struct UniPolynomial {
    coeffs: Vec<i64>, // Replace i64 with a generic scalar type if needed
    degree: usize,
}

/// Subproduct tree structure
#[derive(Debug, PartialEq)]
struct SubproductTree {
    poly: Vec<i64>,
    children: Option<Box<(SubproductTree, SubproductTree)>>,
}

impl UniPolynomial {
    fn new(mut coeffs: Vec<i64>) -> Self {
        // Remove trailing zeros
        while coeffs.len() > 1 && *coeffs.last().unwrap() == 0 {
            coeffs.pop();
        }
        let degree = if coeffs.is_empty() {
            0
        } else {
            coeffs.len() - 1
        };
        UniPolynomial { coeffs, degree }
    }

    fn polynomial_multiplication(a: &[i64], b: &[i64]) -> Vec<i64> {
        let mut result = vec![0; a.len() + b.len() - 1];
        for (i, &coeff_a) in a.iter().enumerate() {
            for (j, &coeff_b) in b.iter().enumerate() {
                result[i + j] += coeff_a * coeff_b;
            }
        }
        result
    }

    fn polynomial_division_with_remainder(
        dividend: &[i64],
        divisor: &[i64],
    ) -> Result<(Vec<i64>, Vec<i64>), String> {
        if divisor.is_empty() || (divisor.len() == 1 && divisor[0] == 0) {
            return Err("Division by zero polynomial".to_string());
        }

        let mut dividend = dividend.to_vec();
        let divisor = divisor.to_vec();

        // Remove leading zeros
        while !dividend.is_empty() && *dividend.last().unwrap() == 0 {
            dividend.pop();
        }

        if dividend.len() < divisor.len() {
            return Ok((vec![0], dividend));
        }

        let mut quotient = vec![0; dividend.len() - divisor.len() + 1];
        let mut remainder = dividend.clone();

        for i in (0..quotient.len()).rev() {
            if remainder.len() < divisor.len() {
                break;
            }

            let quot = remainder.last().unwrap() / divisor.last().unwrap();
            quotient[i] = quot;

            for j in 0..divisor.len() {
                remainder[i + j] -= quot * divisor[j];
            }

            while !remainder.is_empty() && *remainder.last().unwrap() == 0 {
                remainder.pop();
            }
        }

        Ok((quotient, remainder))
    }

    fn division_by_linear_divisor(&self, d: i64) -> (UniPolynomial, i64) {
        let n = self.coeffs.len();
        if n == 0 {
            return (UniPolynomial::new(vec![]), 0); // Handle empty polynomial case
        }

        let mut quotient = vec![0; n - 1];
        let mut current = self.coeffs[n - 1];

        for i in (0..n - 1).rev() {
            quotient[i] = current;
            current = current * d + self.coeffs[i];
        }

        let remainder = current;
        (UniPolynomial::new(quotient), remainder)
    }

    /// Static method to evaluate a polynomial at a given point
    fn evaluate_at_point(coeffs: &[i64], point: i64) -> i64 {
        coeffs
            .iter()
            .rev()
            .fold(0, |result, &coeff| result * point + coeff)
    }

    /// Evaluate the polynomial at a given point
    fn evaluate(&self, point: i64) -> i64 {
        Self::evaluate_at_point(&self.coeffs, point)
    }

    /// Perform bit reversal on an integer
    fn bit_reverse(k: usize, k_log_size: usize) -> usize {
        let mut result = 0;
        for i in 0..k_log_size {
            result |= ((k >> i) & 1) << (k_log_size - 1 - i);
        }
        result
    }

    /// Construct subproduct tree for given domain
    fn construct_subproduct_tree(domain: &[i64]) -> SubproductTree {
        if domain.len() == 1 {
            return SubproductTree {
                poly: vec![-domain[0], 1],
                children: None,
            };
        }

        let mid = domain.len() / 2;
        let left_tree = Self::construct_subproduct_tree(&domain[..mid]);
        let right_tree = Self::construct_subproduct_tree(&domain[mid..]);

        let poly = Self::polynomial_multiplication(&left_tree.poly, &right_tree.poly);

        SubproductTree {
            poly,
            children: Some(Box::new((left_tree, right_tree))),
        }
    }

    /// Compute evaluations using subproduct tree
    fn compute_eval_fix(tree: &SubproductTree, f: &[i64], domain: &[i64]) -> Vec<i64> {
        if domain.len() == 1 {
            return vec![Self::evaluate_at_point(f, domain[0])];
        }

        let (left_tree, right_tree) = tree.children.as_ref().unwrap().as_ref();

        let (_, r0) = Self::polynomial_division_with_remainder(f, &left_tree.poly).unwrap();
        let (_, r1) = Self::polynomial_division_with_remainder(f, &right_tree.poly).unwrap();

        let mid = domain.len() / 2;

        let left_evals = Self::compute_eval_fix(left_tree, &r0, &domain[..mid]);
        let right_evals = Self::compute_eval_fix(right_tree, &r1, &domain[mid..]);

        [left_evals, right_evals].concat()
    }

    /// Core NTT operation
    fn ntt_core(coeffs: &mut Vec<i64>, omega: i64, k_log_size: usize, mod_value: i64) {
        let domain_size = 1 << k_log_size;

        // Bit reversal
        for k in 0..domain_size {
            let k_rev = Self::bit_reverse(k, k_log_size);
            if k < k_rev {
                coeffs.swap(k, k_rev);
            }
        }

        // NTT loop
        let mut sep = 1;
        while sep < domain_size {
            let mut w = 1;
            let omega_step = omega.pow((domain_size / (2 * sep)) as u32) % mod_value;
            for j in 0..sep {
                for i in (0..domain_size).step_by(2 * sep) {
                    let l = i + j;
                    let r = i + j + sep;
                    let tmp = (coeffs[r] * w) % mod_value;
                    coeffs[r] = (coeffs[l] - tmp + mod_value) % mod_value;
                    coeffs[l] = (coeffs[l] + tmp) % mod_value;
                }
                w = (w * omega_step) % mod_value;
            }
            sep *= 2;
        }
    }

    /// Compute NTT evaluations from coefficients
    fn ntt_evals_from_coeffs(
        coeffs: &Vec<i64>,
        omega: i64,
        k_log_size: usize,
        mod_value: i64,
    ) -> Vec<i64> {
        let mut coeffs = coeffs.clone();
        let domain_size = 1 << k_log_size;

        // Ensure coefficients length matches the domain size
        coeffs.resize(domain_size, 0);

        // Perform NTT
        Self::ntt_core(&mut coeffs, omega, k_log_size, mod_value);
        coeffs
    }

    /// Compute coefficients from NTT evaluations
    fn ntt_coeffs_from_evals(
        evals: &Vec<i64>,
        omega: i64,
        k_log_size: usize,
        mod_value: i64,
    ) -> Vec<i64> {
        let domain_size = 1 << k_log_size;
        let omega_inv = Self::mod_inverse(omega, mod_value); // Modular inverse of omega
        let domain_size_inv = Self::mod_inverse(domain_size as i64, mod_value);

        // Perform the inverse NTT
        let mut coeffs = evals.clone();
        Self::ntt_core(&mut coeffs, omega_inv, k_log_size, mod_value);

        // Scale the results by the domain size inverse
        coeffs
            .iter_mut()
            .for_each(|c| *c = (*c * domain_size_inv) % mod_value);

        coeffs
    }

    /// Modular inverse function
    fn mod_inverse(value: i64, mod_value: i64) -> i64 {
        // Extended Euclidean Algorithm for modular inverse
        let (mut a, mut b) = (value, mod_value);
        let (mut x0, mut x1) = (0, 1);

        while a > 1 {
            let q = a / b;
            (a, b) = (b, a % b);
            (x0, x1) = (x1 - q * x0, x0);
        }

        if x1 < 0 {
            x1 += mod_value;
        }

        x1
    }
}

impl Neg for UniPolynomial {
    type Output = UniPolynomial;

    fn neg(self) -> Self::Output {
        UniPolynomial {
            coeffs: self.coeffs.iter().map(|&c| -c).collect(),
            degree: self.degree,
        }
    }
}

impl Add for UniPolynomial {
    type Output = UniPolynomial;

    fn add(self, other: Self) -> Self::Output {
        let max_degree = std::cmp::max(self.coeffs.len(), other.coeffs.len());
        let mut new_coeffs = vec![0; max_degree];
        for i in 0..max_degree {
            if i < self.coeffs.len() {
                new_coeffs[i] += self.coeffs[i];
            }
            if i < other.coeffs.len() {
                new_coeffs[i] += other.coeffs[i];
            }
        }
        UniPolynomial::new(new_coeffs)
    }
}

// Support for scalar addition
impl Add<i64> for UniPolynomial {
    type Output = UniPolynomial;

    fn add(self, scalar: i64) -> Self::Output {
        let mut new_coeffs = self.coeffs.clone();
        if !new_coeffs.is_empty() {
            new_coeffs[0] += scalar;
        } else {
            new_coeffs.push(scalar);
        }
        UniPolynomial::new(new_coeffs)
    }
}

impl Sub for UniPolynomial {
    type Output = UniPolynomial;

    fn sub(self, other: UniPolynomial) -> Self::Output {
        let max_degree = std::cmp::max(self.coeffs.len(), other.coeffs.len());
        let mut result_coeffs = vec![0; max_degree];

        for i in 0..max_degree {
            let coeff1 = if i < self.coeffs.len() {
                self.coeffs[i]
            } else {
                0
            };
            let coeff2 = if i < other.coeffs.len() {
                other.coeffs[i]
            } else {
                0
            };
            result_coeffs[i] = coeff1 - coeff2;
        }

        UniPolynomial::new(result_coeffs)
    }
}

// Support for scalar subtraction
impl Sub<i64> for UniPolynomial {
    type Output = UniPolynomial;

    fn sub(self, scalar: i64) -> Self::Output {
        let mut result_coeffs = self.coeffs.clone();
        if !result_coeffs.is_empty() {
            result_coeffs[0] -= scalar;
        } else {
            result_coeffs.push(-scalar);
        }
        UniPolynomial::new(result_coeffs)
    }
}

impl Mul for UniPolynomial {
    type Output = UniPolynomial;

    fn mul(self, other: UniPolynomial) -> Self::Output {
        let result_coeffs = UniPolynomial::polynomial_multiplication(&self.coeffs, &other.coeffs);
        UniPolynomial::new(result_coeffs)
    }
}

// Support for scalar multiplication
impl Mul<i64> for UniPolynomial {
    type Output = UniPolynomial;

    fn mul(self, scalar: i64) -> Self::Output {
        let result_coeffs: Vec<i64> = self.coeffs.iter().map(|&c| c * scalar).collect();
        UniPolynomial::new(result_coeffs)
    }
}

// Support for right-hand scalar multiplication
impl Mul<UniPolynomial> for i64 {
    type Output = UniPolynomial;

    fn mul(self, poly: UniPolynomial) -> Self::Output {
        poly * self
    }
}

#[cfg(test)]
mod tests {
    use super::*; // Adjust this based on where `UniPolynomial` is defined

    #[test]
    fn test_polynomial_addition() {
        let poly1 = UniPolynomial::new(vec![1, 2, 3]); // 3x^2 + 2x + 1
        let poly2 = UniPolynomial::new(vec![4, 5]); // 5x + 4

        let result = poly1.clone() + poly2.clone();
        assert_eq!(result.coeffs, vec![5, 7, 3]); // Coefficients of (3x^2 + 7x + 5)
    }

    #[test]
    fn test_scalar_addition() {
        let poly1 = UniPolynomial::new(vec![1, 2, 3]); // 3x^2 + 2x + 1

        let scalar_result = poly1 + 10; // Adds 10 to the constant term
        assert_eq!(scalar_result.coeffs, vec![11, 2, 3]); // Coefficients of (3x^2 + 2x + 11)
    }

    #[test]
    fn test_polynomial_subtraction() {
        let poly1 = UniPolynomial::new(vec![1, 2, 3]); // 3x^2 + 2x + 1
        let poly2 = UniPolynomial::new(vec![4, 5]); // 5x + 4

        let result = poly1.clone() - poly2.clone();
        assert_eq!(result.coeffs, vec![-3, -3, 3]); // Coefficients of (3x^2 - 3x - 3)
    }

    #[test]
    fn test_scalar_subtraction() {
        let poly1 = UniPolynomial::new(vec![1, 2, 3]); // 3x^2 + 2x + 1

        let scalar_result = poly1 - 10; // Subtracts 10 from the constant term
        assert_eq!(scalar_result.coeffs, vec![-9, 2, 3]); // Coefficients of (3x^2 + 2x - 9)
    }

    #[test]
    fn test_polynomial_multiplication() {
        let poly1 = UniPolynomial::new(vec![1, 2, 3]); // 3x^2 + 2x + 1
        let poly2 = UniPolynomial::new(vec![4, 5]); // 5x + 4

        let result = poly1.clone() * poly2.clone();
        assert_eq!(result.coeffs, vec![4, 13, 22, 15]); // Coefficients of (15x^3 + 22x^2 + 13x + 4)
    }

    #[test]
    fn test_scalar_multiplication() {
        let poly1 = UniPolynomial::new(vec![1, 2, 3]); // 3x^2 + 2x + 1

        let scalar_result = poly1 * 3; // Multiply polynomial by scalar
        assert_eq!(scalar_result.coeffs, vec![3, 6, 9]); // Coefficients of (9x^2 + 6x + 3)
    }

    #[test]
    fn test_polynomial_division_with_remainder() {
        let dividend = vec![5, 2, 3, 1]; // 1x^3 + 3x^2 + 2x + 5
        let divisor = vec![1, 1]; // x + 1

        match UniPolynomial::polynomial_division_with_remainder(&dividend, &divisor) {
            Ok((quotient, remainder)) => {
                assert_eq!(quotient, vec![0, 2, 1]); // Expected quotient
                assert_eq!(remainder, vec![5]); // Expected remainder
            }
            Err(err) => panic!("Unexpected error: {}", err),
        }
    }

    #[test]
    fn test_division_by_linear_divisor() {
        // Test case 1: Polynomial division with a linear divisor
        let poly = UniPolynomial::new(vec![5, 2, 3, 1]); // 1x^3 + 3x^2 + 2x + 5
        let divisor = 1;

        let (quotient, remainder) = poly.division_by_linear_divisor(divisor);

        // Expected results
        let expected_quotient = UniPolynomial::new(vec![6, 4, 1]); // 1x^2 + 3x + 2
        let expected_remainder = 11;

        // Assertions
        assert_eq!(quotient.coeffs, expected_quotient.coeffs);
        assert_eq!(remainder, expected_remainder);

        // Test case 2: Empty polynomial
        let empty_poly = UniPolynomial::new(vec![]);
        let divisor = 2;

        let (quotient, remainder) = empty_poly.division_by_linear_divisor(divisor);

        // Expected results for empty polynomial
        assert_eq!(quotient.coeffs, vec![]); // Quotient should be empty
        assert_eq!(remainder, 0); // Remainder should be 0

        // Test case 3: Single coefficient polynomial
        let single_coeff_poly = UniPolynomial::new(vec![5]); // 5
        let divisor = 3;

        let (quotient, remainder) = single_coeff_poly.division_by_linear_divisor(divisor);

        // Expected results
        assert_eq!(quotient.coeffs, vec![]); // Quotient should be empty
        assert_eq!(remainder, 5); // Remainder should be the same as the polynomial
    }

    #[test]
    fn test_evaluate_at_point() {
        // Test case 1: Evaluate P(x) = 3x^2 + 2x + 1 at x = 2
        let coeffs = vec![1, 2, 3]; // P(x) = 3x^2 + 2x + 1
        let point = 2; // x = 2
        let result = UniPolynomial::evaluate_at_point(&coeffs, point);

        // Expected result: 3*(2^2) + 2*2 + 1 = 12 + 4 + 1 = 17
        assert_eq!(result, 17);

        // Test case 2: Evaluate P(x) = -x^2 + 4x - 5 at x = -1
        let coeffs = vec![-5, 4, -1]; // P(x) = -x^2 + 4x - 5
        let point = -1; // x = -1
        let result = UniPolynomial::evaluate_at_point(&coeffs, point);

        // Expected result: -(-1^2) + 4*(-1) - 5 = -1 - 4 - 5 = -10
        assert_eq!(result, -10);

        // Test case 3: Evaluate P(x) = 0 (constant zero polynomial) at any x
        let coeffs = vec![0]; // P(x) = 0
        let point = 5; // x = 5
        let result = UniPolynomial::evaluate_at_point(&coeffs, point);

        // Expected result: 0
        assert_eq!(result, 0);
    }

    #[test]
    fn test_evaluate() {
        // Test case 1: Evaluate P(x) = 3x^2 + 2x + 1 at x = 2
        let poly = UniPolynomial::new(vec![1, 2, 3]); // P(x) = 3x^2 + 2x + 1
        let point = 2; // x = 2
        let result = poly.evaluate(point);

        // Expected result: 3*(2^2) + 2*2 + 1 = 17
        assert_eq!(result, 17);

        // Test case 2: Evaluate P(x) = -x^2 + 4x - 5 at x = -1
        let poly = UniPolynomial::new(vec![-5, 4, -1]); // P(x) = -x^2 + 4x - 5
        let point = -1; // x = -1
        let result = poly.evaluate(point);

        // Expected result: -10
        assert_eq!(result, -10);

        // Test case 3: Evaluate P(x) = 0 (constant zero polynomial) at any x
        let poly = UniPolynomial::new(vec![0]); // P(x) = 0
        let point = 5; // x = 5
        let result = poly.evaluate(point);

        // Expected result: 0
        assert_eq!(result, 0);
    }

    #[test]
    fn test_bit_reverse() {
        // Test case 1: Reverse 3-bit integer
        let result = UniPolynomial::bit_reverse(3, 3); // Binary: 011 -> 110
        assert_eq!(result, 6);

        // Test case 2: Reverse 4-bit integer
        let result = UniPolynomial::bit_reverse(5, 4); // Binary: 0101 -> 1010
        assert_eq!(result, 10);

        // Test case 3: Single bit integer
        let result = UniPolynomial::bit_reverse(1, 1); // Single bit remains unchanged
        assert_eq!(result, 1);
    }

    #[test]
    fn test_construct_subproduct_tree() {
        // Test case: Domain [1, 2, 3, 4]
        let domain = vec![1, 2, 3, 4];
        let tree = UniPolynomial::construct_subproduct_tree(&domain);

        // Expected subproduct tree
        let expected_tree = SubproductTree {
            poly: vec![1, -10, 35, -50, 24], // (x - 1)(x - 2)(x - 3)(x - 4)
            children: Some(Box::new((
                SubproductTree {
                    poly: vec![1, -3, 2], // (x - 1)(x - 2)
                    children: Some(Box::new((
                        SubproductTree {
                            poly: vec![-1, 1], // x - 1
                            children: None,
                        },
                        SubproductTree {
                            poly: vec![-2, 1], // x - 2
                            children: None,
                        },
                    ))),
                },
                SubproductTree {
                    poly: vec![1, -7, 12], // (x - 3)(x - 4)
                    children: Some(Box::new((
                        SubproductTree {
                            poly: vec![-3, 1], // x - 3
                            children: None,
                        },
                        SubproductTree {
                            poly: vec![-4, 1], // x - 4
                            children: None,
                        },
                    ))),
                },
            ))),
        };

        assert_eq!(tree, expected_tree);
    }

    #[test]
    fn test_compute_eval_fix() {
        // Input domain and polynomial
        let domain = vec![1, 2, 3, 4];
        let tree = UniPolynomial::construct_subproduct_tree(&domain);
        let poly = vec![1, 0, -1]; // x^2 - 1

        // Compute evaluations
        let evals = UniPolynomial::compute_eval_fix(&tree, &poly, &domain);

        // Expected evaluations
        // P(1) = 1^2 - 1 = 0
        // P(2) = 2^2 - 1 = 3
        // P(3) = 3^2 - 1 = 8
        // P(4) = 4^2 - 1 = 15
        let expected_evals = vec![0, 3, 8, 15];

        assert_eq!(evals, expected_evals);
    }

    #[test]
    fn test_ntt_core() {
        let mut coeffs = vec![1, 2, 3, 4];
        let omega = 3;
        let k_log_size = 2; // Domain size = 2^2 = 4
        let mod_value = 17;

        UniPolynomial::ntt_core(&mut coeffs, omega, k_log_size, mod_value);

        // Expected NTT result
        let expected = vec![10, 9, 15, 4]; // This depends on your specific NTT implementation
        assert_eq!(coeffs, expected);
    }

    #[test]
    fn test_ntt_evals_from_coeffs() {
        let coeffs = vec![1, 2, 3, 4];
        let omega = 3;
        let k_log_size = 2; // Domain size = 2^2 = 4
        let mod_value = 17;

        let result = UniPolynomial::ntt_evals_from_coeffs(&coeffs, omega, k_log_size, mod_value);

        // Expected NTT evaluations
        let expected = vec![10, 9, 15, 4]; // This depends on your specific NTT implementation
        assert_eq!(result, expected);
    }

    #[test]
    fn test_ntt_coeffs_from_evals() {
        let evals = vec![10, 9, 15, 4];
        let omega = 3;
        let k_log_size = 2; // Domain size = 2^2 = 4
        let mod_value = 17;

        let result = UniPolynomial::ntt_coeffs_from_evals(&evals, omega, k_log_size, mod_value);

        // Expected coefficients after inverse NTT
        let expected = vec![1, 2, 3, 4]; // Original coefficients
        assert_eq!(result, expected);
    }

    #[test]
    fn test_ntt_round_trip() {
        let coeffs = vec![1, 2, 3, 4];
        let omega = 3;
        let k_log_size = 2; // Domain size = 2^2 = 4
        let mod_value = 17;

        // Perform forward NTT
        let evals = UniPolynomial::ntt_evals_from_coeffs(&coeffs, omega, k_log_size, mod_value);

        // Perform inverse NTT
        let reconstructed_coeffs =
            UniPolynomial::ntt_coeffs_from_evals(&evals, omega, k_log_size, mod_value);

        // Coefficients after round-trip should match original
        assert_eq!(reconstructed_coeffs, coeffs);
    }
}
