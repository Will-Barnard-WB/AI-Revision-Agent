# Jordan Normal Form Summary

## Definition
The Jordan normal form (JNF) of a linear operator is a canonical form that represents the operator as a direct sum of Jordan blocks. Each Jordan block corresponds to an eigenvalue and captures the structure of the operator in relation to its eigenvalues and generalized eigenvectors.

## Theorem 4.21
Let \( \phi \in L(V) \) be a linear operator on a finite-dimensional vector space \( V \) over the complex numbers \( \mathbb{C} \). Then:
- There exists a basis of \( V \) such that \( \phi \) can be represented as a direct sum of Jordan blocks.
- This basis is called a **Jordan basis**.
- The direct sum of these Jordan blocks is referred to as the **Jordan normal form (JNF)** of \( \phi \).

## Structure of Jordan Blocks
- Let \( \lambda_1, \ldots, \lambda_k \) be the distinct eigenvalues of \( \phi \).
- The space \( V \) can be decomposed as \( V = \bigoplus V_i \), where \( V_i = G_{\phi}(\lambda_i) \) is the generalized eigenspace corresponding to \( \lambda_i \).
- The operator \( \phi_i := \phi|_{V_i} \) can be expressed as:
  \[ \phi_i = \lambda_i \text{id}_{V_i} + N_i, \]  
  where \( N_i \) is a nilpotent operator.
- By applying the appropriate theorems, we can find a basis for \( V_i \) such that \( N_i \) has a matrix representation of the form \( J_{n_1} \oplus \cdots \oplus J_{n_\ell} \).

## Uniqueness
- The sizes of the Jordan blocks, denoted as \( n_1, \ldots, n_\ell \), are unique up to order, meaning that while the arrangement of blocks may vary, their sizes remain consistent across different Jordan bases.