fn bits_le_with_width(i: u32, width: usize) -> Result<Vec<u8>, &'static str> {
    if i >= (1 << width) {
        return Err("Failed");
    }
    let mut bits = Vec::new();
    let mut num = i;
    let mut w = width;
    while w > 0 {
        bits.push((num % 2) as u8);
        num /= 2;
        w -= 1;
    }
    Ok(bits)
}

fn bits_le_to_int(bits: &Vec<u8>) -> u32 {
    let mut result = 0;
    for (i, &b) in bits.iter().enumerate() {
        result += (b as u32) << i;
    }
    result

    // alternatively,
    // bits.iter().rev().fold(0, |acc,&b| (acc<<1) + b as u32)
}

fn bit_reverse(x: u32, width: usize) -> u32 {
    if let Ok(bits) = bits_le_with_width(x, width) {
        bits_le_to_int(&bits)
    } else {
        0
    }
}

fn pow_2(n: u32) -> u32 {
    1 << n
}

fn is_power_of_two(n: u32) -> bool {
    n > 0 && (n & (n - 1)) == 0
}

fn next_power_of_two(n: u32) -> u32 {
    assert!(n >= 0, "No negative integer");
    if is_power_of_two(n) {
        return n;
    }
    let mut d = n;
    let mut k = 1;
    while d > 0 {
        d >>= 1;
        k <<= 1;
    }
    k
}

fn log_2(mut x: u32) -> Result<u32, &'static str> {
    if x <= 0 {
        return Err("x must be a positive integer");
    }
    let mut result = 0;
    while x > 1 {
        x >>= 1;
        result += 1;
    }
    Ok(result)
}

fn from_bytes(bytes: &[u8]) -> u32 {
    if bytes.len() > 4 {
        panic!("Input too large for u32");
    }
    let mut res: u32 = 0;
    for &b in bytes {
        res = (res << 8) + b as u32;
    }
    res
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bits_le_with_width() {
        assert_eq!(bits_le_with_width(5, 3).unwrap(), vec![1, 0, 1]);
        assert_eq!(bits_le_with_width(2, 2).unwrap(), vec![0, 1]);
        assert!(bits_le_with_width(8, 3).is_err());
    }

    #[test]
    fn test_bits_le_to_int() {
        assert_eq!(bits_le_to_int(&vec![1, 0, 1]), 5);
        assert_eq!(bits_le_to_int(&vec![0, 1]), 2);
    }

    #[test]
    fn test_bit_reverse() {
        assert_eq!(bit_reverse(5, 3), 5);
        assert_eq!(bit_reverse(2, 3), 2);
        assert_eq!(bit_reverse(3, 3), 3);
        assert_eq!(bit_reverse(13, 4), 13);
    }

    #[test]
    fn test_pow_2() {
        assert_eq!(pow_2(0), 1);
        assert_eq!(pow_2(4), 16);
    }

    #[test]
    fn test_is_power_of_two() {
        assert!(is_power_of_two(1));
        assert!(is_power_of_two(16));
        assert!(!is_power_of_two(18));
    }

    #[test]
    fn test_next_power_of_two() {
        assert_eq!(next_power_of_two(0), 1);
        assert_eq!(next_power_of_two(5), 8);
        assert_eq!(next_power_of_two(16), 16);
    }

    #[test]
    fn test_log_2() {
        assert_eq!(log_2(16).unwrap(), 4);
        assert_eq!(log_2(1).unwrap(), 0);
        assert!(log_2(0).is_err());
    }

    #[test]
    fn test_from_bytes() {
        assert_eq!(from_bytes(&[0x01, 0x02, 0x03]), 0x010203);
        assert_eq!(from_bytes(&[0xff]), 0xff);
    }
}