use alloc::vec;
use alloc::vec::Vec;
use core::array;
use core::cmp::Reverse;
use core::marker::PhantomData;

use itertools::Itertools;
use p3_field::PackedValue;
use p3_matrix::Matrix;
use p3_maybe_rayon::prelude::*;
use p3_symmetric::{CryptographicHasher, Hash, PseudoCompressionFunction};
use serde::{Deserialize, Serialize};
use tracing::instrument;

/// A binary Merkle tree for packed data. It has leaves of type `F` and digests of type
/// `[W; DIGEST_ELEMS]`.
///
/// This generally shouldn't be used directly. If you're using a Merkle tree as an MMCS,
/// see `MerkleTreeMmcs`.
#[derive(Debug, Serialize, Deserialize)]
pub struct MerkleTree<F, W, M, const DIGEST_ELEMS: usize> {
    pub(crate) leaves: Vec<M>,
    // Enable serialization for this type whenever the underlying array type supports it (len 1-32).
    #[serde(bound(serialize = "[W; DIGEST_ELEMS]: Serialize"))]
    // Enable deserialization for this type whenever the underlying array type supports it (len 1-32).
    #[serde(bound(deserialize = "[W; DIGEST_ELEMS]: Deserialize<'de>"))]
    pub(crate) digest_layers: Vec<Vec<[W; DIGEST_ELEMS]>>,
    _phantom: PhantomData<F>,
}

impl<F: Clone + Send + Sync, W: Clone, M: Matrix<F>, const DIGEST_ELEMS: usize>
    MerkleTree<F, W, M, DIGEST_ELEMS>
{
    /// Matrix heights need not be powers of two. However, if the heights of two given matrices
    /// round up to the same power of two, they must be equal.
    /// Neil: construct merkle tree by leaves
    ///
    /// # Arguments
    /// * `h` - hash function for raw data
    /// * `c` - compression function for nodes
    /// * `leaves` - leaves of the merkle tree
    ///
    /// # Returns
    /// A merkle tree
    #[instrument(name = "build merkle tree", level = "debug", skip_all,
                 fields(dimensions = alloc::format!("{:?}", leaves.iter().map(|l| l.dimensions()).collect::<Vec<_>>())))]
    pub fn new<P, PW, H, C>(h: &H, c: &C, leaves: Vec<M>) -> Self
    where
        P: PackedValue<Value = F>,
        PW: PackedValue<Value = W>,
        H: CryptographicHasher<F, [W; DIGEST_ELEMS]>,
        H: CryptographicHasher<P, [PW; DIGEST_ELEMS]>,
        H: Sync,
        C: PseudoCompressionFunction<[W; DIGEST_ELEMS], 2>,
        C: PseudoCompressionFunction<[PW; DIGEST_ELEMS], 2>,
        C: Sync,
    {
        assert!(!leaves.is_empty(), "No matrices given?");

        assert_eq!(P::WIDTH, PW::WIDTH, "Packing widths must match");

        // Neil: sort the matrices by height in descending order
        let mut leaves_largest_first = leaves
            .iter()
            .sorted_by_key(|l| Reverse(l.height()))
            .peekable();

        // check height property
        assert!(
            leaves_largest_first
                .clone()
                .map(|m| m.height())
                .tuple_windows()
                .all(|(curr, next)| curr == next
                    || curr.next_power_of_two() != next.next_power_of_two()),
            "matrix heights that round up to the same power of two must be equal"
        );

        // Neil: max_height is the height of the tallest matrix
        let max_height = leaves_largest_first.peek().unwrap().height();
        // Neil: collect all the tallest matrices from 'leaves_largest_first'
        let tallest_matrices = leaves_largest_first
            .peeking_take_while(|m| m.height() == max_height)
            .collect_vec();

        // Neil: digest the first layer of the merkle tree
        let mut digest_layers = vec![first_digest_layer::<P, PW, H, M, DIGEST_ELEMS>(
            h,
            tallest_matrices,
        )];

        // Neil: digest the rest of the layers of the merkle tree
        loop {
            let prev_layer = digest_layers.last().unwrap().as_slice();
            // Neil: This indicates the last layer of the merkle tree
            if prev_layer.len() == 1 {
                break;
            }
            let next_layer_len = prev_layer.len() / 2;

            // The matrices that get injected at this layer.
            // Neil: collect all the matrices that have height equal to 'next_layer_len'
            let matrices_to_inject = leaves_largest_first
                .peeking_take_while(|m| m.height().next_power_of_two() == next_layer_len)
                .collect_vec();

            // Neil: compress the previous layer and the matrices to be injected to the next layer
            let next_digests = compress_and_inject::<P, PW, H, C, M, DIGEST_ELEMS>(
                prev_layer,
                matrices_to_inject,
                h,
                c,
            );
            digest_layers.push(next_digests);
        }

        Self {
            leaves,
            digest_layers,
            _phantom: PhantomData,
        }
    }

    /// Neil: Get the root of the merkle tree
    ///
    /// # Returns
    /// The root of the merkle tree
    #[must_use]
    pub fn root(&self) -> Hash<F, W, DIGEST_ELEMS>
    where
        W: Copy,
    {
        self.digest_layers.last().unwrap()[0].into()
    }
}

/// Neil: Digest the first layer of the merkle tree
///
/// # Arguments
/// * `h` - The cryptographic hash function
/// * `tallest_matrices` - The matrices to be hashed
///
/// # Returns
/// A vector of digests
#[instrument(name = "first digest layer", level = "debug", skip_all)]
fn first_digest_layer<P, PW, H, M, const DIGEST_ELEMS: usize>(
    h: &H,
    tallest_matrices: Vec<&M>,
) -> Vec<[PW::Value; DIGEST_ELEMS]>
where
    P: PackedValue,
    PW: PackedValue,
    H: CryptographicHasher<P::Value, [PW::Value; DIGEST_ELEMS]>,
    H: CryptographicHasher<P, [PW; DIGEST_ELEMS]>,
    H: Sync,
    M: Matrix<P::Value>,
{
    let width = PW::WIDTH;
    let max_height = tallest_matrices[0].height();
    // Neil: max_height_padded is the length of the lowest layer of the merkle tree
    let max_height_padded = max_height.next_power_of_two();

    // Neil: digests stores the nodes of the merkle tree row by row
    let default_digest: [PW::Value; DIGEST_ELEMS] = [PW::Value::default(); DIGEST_ELEMS];
    let mut digests = vec![default_digest; max_height_padded];

    // Neil: fill the digests of the merkle tree
    digests[0..max_height]
        .par_chunks_exact_mut(width)
        .enumerate()
        .for_each(|(i, digests_chunk)| {
            let first_row = i * width;
            let packed_digest: [PW; DIGEST_ELEMS] = h.hash_iter(
                tallest_matrices
                    .iter()
                    // Neil: this takes out a row of field elements from each matrix
                    .flat_map(|m| m.vertically_packed_row(first_row)),
            );
            // Neil: copy digests to dst
            for (dst, src) in digests_chunk.iter_mut().zip(unpack_array(packed_digest)) {
                *dst = src;
            }
        });

    // If our packing width did not divide max_height, fall back to single-threaded scalar code
    // for the last bit.
    #[allow(clippy::needless_range_loop)]
    for i in (max_height / width * width)..max_height {
        digests[i] = h.hash_iter(tallest_matrices.iter().flat_map(|m| m.row(i)));
    }

    // Everything has been initialized so we can safely cast.
    digests
}

/// Compress `n` digests from the previous layer into `n/2` digests, while potentially mixing in
/// some leaf data, if there are input matrices with (padded) height `n/2`.
/// Neil: compress the previous layer and potentially mixing in some leaf data
///
/// # Arguments
/// * `prev_layer` - the previous layer of the merkle tree
/// * `matrices_to_inject` - the matrices to be injected
/// * `h` - hash function for raw data
/// * `c` - compression function for nodes
///
/// # Returns
/// A vector of digests
fn compress_and_inject<P, PW, H, C, M, const DIGEST_ELEMS: usize>(
    prev_layer: &[[PW::Value; DIGEST_ELEMS]],
    matrices_to_inject: Vec<&M>,
    h: &H,
    c: &C,
) -> Vec<[PW::Value; DIGEST_ELEMS]>
where
    P: PackedValue,
    PW: PackedValue,
    H: CryptographicHasher<P::Value, [PW::Value; DIGEST_ELEMS]>,
    H: CryptographicHasher<P, [PW; DIGEST_ELEMS]>,
    H: Sync,
    C: PseudoCompressionFunction<[PW::Value; DIGEST_ELEMS], 2>,
    C: PseudoCompressionFunction<[PW; DIGEST_ELEMS], 2>,
    C: Sync,
    M: Matrix<P::Value>,
{
    // Neil: if there is no matrix to inject, then just compress the previous layer
    if matrices_to_inject.is_empty() {
        return compress::<PW, C, DIGEST_ELEMS>(prev_layer, c);
    }

    let width = PW::WIDTH;
    let next_len = matrices_to_inject[0].height();
    // Neil: next_len_padded is the height of the next layer of the merkle tree
    let next_len_padded = prev_layer.len() / 2;

    let default_digest: [PW::Value; DIGEST_ELEMS] = [PW::Value::default(); DIGEST_ELEMS];
    let mut next_digests = vec![default_digest; next_len_padded];

    // Neil: compress the previous layer and the matrices to be injected to the next layer
    next_digests[0..next_len]
        .par_chunks_exact_mut(width)
        .enumerate()
        .for_each(|(i, digests_chunk)| {
            let first_row = i * width;
            let left = array::from_fn(|j| PW::from_fn(|k| prev_layer[2 * (first_row + k)][j]));
            let right = array::from_fn(|j| PW::from_fn(|k| prev_layer[2 * (first_row + k) + 1][j]));
            // Neil: compress the previous layer
            let mut packed_digest = c.compress([left, right]);
            // Neil: hash the matrices to be injected
            let tallest_digest = h.hash_iter(
                matrices_to_inject
                    .iter()
                    // Neil: this takes out a row of field elements from each matrix
                    .flat_map(|m| m.vertically_packed_row(first_row)),
            );
            // Neil: compress the previous layer and the matrices to be injected
            packed_digest = c.compress([packed_digest, tallest_digest]);
            for (dst, src) in digests_chunk.iter_mut().zip(unpack_array(packed_digest)) {
                *dst = src;
            }
        });

    // If our packing width did not divide next_len, fall back to single-threaded scalar code
    // for the last bit.
    for i in (next_len / width * width)..next_len {
        let left = prev_layer[2 * i];
        let right = prev_layer[2 * i + 1];
        let digest = c.compress([left, right]);
        let rows_digest = h.hash_iter(matrices_to_inject.iter().flat_map(|m| m.row(i)));
        next_digests[i] = c.compress([digest, rows_digest]);
    }

    // At this point, we've exceeded the height of the matrices to inject, so we continue the
    // process above except with default_digest in place of an input digest.
    for i in next_len..next_len_padded {
        let left = prev_layer[2 * i];
        let right = prev_layer[2 * i + 1];
        let digest = c.compress([left, right]);
        next_digests[i] = c.compress([digest, default_digest]);
    }

    next_digests
}

/// Compress `n` digests from the previous layer into `n/2` digests.
///
/// Neil: if there is no matrix to inject, then just compress the previous layer
///
/// # Arguments
/// * `prev_layer` - the previous layer of the merkle tree
/// * `c` - compression function for nodes
///
/// # Returns
/// A vector of digests
fn compress<P, C, const DIGEST_ELEMS: usize>(
    prev_layer: &[[P::Value; DIGEST_ELEMS]],
    c: &C,
) -> Vec<[P::Value; DIGEST_ELEMS]>
where
    P: PackedValue,
    C: PseudoCompressionFunction<[P::Value; DIGEST_ELEMS], 2>,
    C: PseudoCompressionFunction<[P; DIGEST_ELEMS], 2>,
    C: Sync,
{
    debug_assert!(prev_layer.len().is_power_of_two());
    let width = P::WIDTH;
    let next_len = prev_layer.len() / 2;

    let default_digest: [P::Value; DIGEST_ELEMS] = [P::Value::default(); DIGEST_ELEMS];
    let mut next_digests = vec![default_digest; next_len];

    // Neil: compress the previous layer
    next_digests[0..next_len]
        .par_chunks_exact_mut(width)
        .enumerate()
        .for_each(|(i, digests_chunk)| {
            let first_row = i * width;
            // Neil: left will be the even rows of the previous layer
            let left = array::from_fn(|j| P::from_fn(|k| prev_layer[2 * (first_row + k)][j]));
            // Neil: right will be the odd rows of the previous layer
            let right = array::from_fn(|j| P::from_fn(|k| prev_layer[2 * (first_row + k) + 1][j]));
            // Neil: compress the previous layer
            let packed_digest = c.compress([left, right]);
            for (dst, src) in digests_chunk.iter_mut().zip(unpack_array(packed_digest)) {
                *dst = src;
            }
        });

    // If our packing width did not divide next_len, fall back to single-threaded scalar code
    // for the last bit.
    for i in (next_len / width * width)..next_len {
        let left = prev_layer[2 * i];
        let right = prev_layer[2 * i + 1];
        let digest = c.compress([left, right]);
        next_digests[i] = digest;
    }

    // Everything has been initialized so we can safely cast.
    next_digests
}

/// Converts a packed array `[P; N]` into its underlying `P::WIDTH` scalar arrays.
#[inline]
fn unpack_array<P: PackedValue, const N: usize>(
    packed_digest: [P; N],
) -> impl Iterator<Item = [P::Value; N]> {
    (0..P::WIDTH).map(move |j| packed_digest.map(|p| p.as_slice()[j]))
}
