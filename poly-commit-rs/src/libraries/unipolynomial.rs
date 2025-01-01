use std::ops::{Add, Mul, Neg, Sub};

#[derive(Debug, Clone)]
struct UniPolynomial {
    coeffs: Vec<i64>, // Replace i64 with a generic scalar type if needed
    degree: usize,
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
        coeffs.iter().rev().fold(0, |result, &coeff| result * point + coeff)
    }

    /// Evaluate the polynomial at a given point
    fn evaluate(&self, point: i64) -> i64 {
        Self::evaluate_at_point(&self.coeffs, point)
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
        let divisor = vec![1, 1];        // x + 1

        match UniPolynomial::polynomial_division_with_remainder(&dividend, &divisor) {
            Ok((quotient, remainder)) => {
                assert_eq!(quotient, vec![0, 2, 1]); // Expected quotient
                assert_eq!(remainder, vec![5]);      // Expected remainder
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
        let expected_quotient = UniPolynomial::new(vec![6,4,1]); // 1x^2 + 3x + 2
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
}
