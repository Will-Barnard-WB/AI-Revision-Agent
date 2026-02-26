# Minimum Polynomial & Cayley–Hamilton Theorem — Study Guide

## Learning Objectives
By the end of this guide, you should be able to:
- [ ] Define the minimum polynomial of a linear operator / matrix and prove its existence and uniqueness
- [ ] State and apply the divisibility property: every annihilating polynomial is divisible by the minimum polynomial
- [ ] State the Cayley–Hamilton theorem and explain what it means concretely
- [ ] Reproduce the adjugate-matrix proof of Cayley–Hamilton
- [ ] Identify the eigenvalues of an operator as exactly the roots of its minimum polynomial
- [ ] Use Cayley–Hamilton to compute matrix inverses and high powers of matrices
- [ ] Relate the minimum polynomial to the characteristic polynomial (divisibility, same roots)

---

## Prerequisite Knowledge
- Polynomials in a linear operator: if `p = a₀ + a₁x + … + aₙxⁿ ∈ F[x]`, then `p(φ) = a₀ id_V + a₁φ + … + aₙφⁿ`
- Determinants and the characteristic polynomial `Δ_φ(x) = det(φ − x·id_V)`
- Eigenvalues, eigenvectors, and eigenspaces
- Linear independence in the matrix space `Mₙ(F)` (dimension = n²)
- The adjugate (classical adjoint) of a matrix: `adj(B) · B = det(B) · Iₙ`

---

## 1. Polynomials in Linear Operators — Quick Recap

Let `V` be a finite-dimensional vector space over a field `F`, and `φ ∈ L(V)`.

For `p = Σ aₖxᵏ ∈ F[x]`, define:
```
p(φ) = Σ aₖ φᵏ   (where φ⁰ = id_V)
```

**Key fact:** The map `F[x] → L(V)`, `p ↦ p(φ)` is a ring homomorphism. In particular:
- `(p + q)(φ) = p(φ) + q(φ)`
- `(pq)(φ) = p(φ) ∘ q(φ) = q(φ) ∘ p(φ)`  ← commutativity is crucial!

**Eigenvector lemma:** If `φ(v) = λv` (v ≠ 0), then `p(φ)(v) = p(λ)v` for all `p ∈ F[x]`.

*Proof sketch:* By induction, `φᵏ(v) = λᵏv`, so `p(φ)(v) = Σ aₖλᵏv = p(λ)v`. ∎

---

## 2. The Minimum Polynomial

### 2.1 Existence

> **Proposition.** For any `A ∈ Mₙ(F)` (or `φ ∈ L(V)`, `dim V < ∞`), there exists a monic polynomial `p ∈ F[x]` with `p(A) = 0`.

**Proof.**
`dim Mₙ(F) = n²`, so the `n² + 1` elements `Iₙ, A, A², …, Aⁿ²` are linearly dependent. Hence there exist scalars `a₀, …, aₙ²` (not all zero) with:
```
a₀Iₙ + a₁A + … + aₙ²Aⁿ² = 0
```
Dividing by the leading coefficient gives a monic polynomial `p` with `p(A) = 0`. ∎

### 2.2 Definition

> **Definition.** The **minimum polynomial** `m_φ` of `φ ∈ L(V)` is the unique monic polynomial of **smallest degree** such that `m_φ(φ) = 0`.

Similarly, `m_A` denotes the minimum polynomial of a matrix `A ∈ Mₙ(F)`.

### 2.3 Uniqueness

**Proof of uniqueness.** Suppose `p₁, p₂` are both monic of minimal degree with `pᵢ(φ) = 0`. Set `r = p₁ − p₂`. Then:
- `deg r < deg pᵢ` (leading terms cancel)
- `r(φ) = p₁(φ) − p₂(φ) = 0`

By minimality of degree, `r = 0`, so `p₁ = p₂`. ∎

### 2.4 Simple Examples

| Operator / Matrix | Minimum Polynomial |
|---|---|
| Zero operator `0` | `x` |
| Identity `id_V` | `x − 1` |
| Scalar `λ · id_V` | `x − λ` |
| `A = diag(λ₁, λ₂)`, `λ₁ ≠ λ₂` | `(x − λ₁)(x − λ₂)` |
| `A = diag(λ, λ)` | `x − λ` |
| `A = [[0,1],[0,0]]` (nilpotent) | `x²` |

> **Remark.** `deg m_φ = 1` if and only if `φ = λ · id_V` for some `λ ∈ F`.

### 2.5 The Divisibility Property

> **Theorem.** If `p ∈ F[x]` satisfies `p(φ) = 0`, then `m_φ | p` (i.e., `m_φ` divides `p`).

**Proof.** Perform polynomial division: `p = q · m_φ + r` with `deg r < deg m_φ`. Then:
```
0 = p(φ) = q(φ) ∘ m_φ(φ) + r(φ) = 0 + r(φ)
```
So `r(φ) = 0`. Since `deg r < deg m_φ` and `m_φ` has minimal degree, we must have `r = 0`. Hence `m_φ | p`. ∎

**Consequence:** The minimum polynomial is the *generator* of the ideal `{p ∈ F[x] : p(φ) = 0}`.

---

## 3. Eigenvalues and the Minimum Polynomial

> **Corollary.** Every eigenvalue of `φ` is a root of `m_φ`.

**Proof.** If `φ(v) = λv` with `v ≠ 0`, then by the eigenvector lemma:
```
0 = m_φ(φ)(v) = m_φ(λ) · v
```
Since `v ≠ 0`, we get `m_φ(λ) = 0`. ∎

**Converse:** Every root of `m_φ` is an eigenvalue of `φ` (proved via the factored form of `m_φ`).

> **Key fact:** `m_φ` and `Δ_φ` have **exactly the same roots** (i.e., the same eigenvalues), but possibly with different multiplicities.

---

## 4. The Characteristic Polynomial

> **Definition.** The **characteristic polynomial** of `φ ∈ L(V)` is:
> ```
> Δ_φ(x) = det(φ − x · id_V)
> ```
> For a matrix `A ∈ Mₙ(F)`: `Δ_A(x) = det(A − xIₙ)`.

- `deg Δ_φ = dim V = n`
- `λ` is an eigenvalue of `φ` ⟺ `λ` is a root of `Δ_φ`

**Relationship between `m_φ` and `Δ_φ`:**

| Property | Statement |
|---|---|
| Same roots | `m_φ` and `Δ_φ` have the same irreducible factors (over `F`) |
| Divisibility | `m_φ` divides `Δ_φ` (consequence of Cayley–Hamilton) |
| Degree bound | `deg m_φ ≤ deg Δ_φ = n` |

---

## 5. The Cayley–Hamilton Theorem

> **Theorem 3.12 (Cayley–Hamilton).** Let `φ ∈ L(V)` be a linear operator on a finite-dimensional vector space over `F`. Then:
> ```
> Δ_φ(φ) = 0
> ```
> Equivalently, for any `A ∈ Mₙ(F)`:  `Δ_A(A) = 0`.

In words: **every matrix (or linear operator) satisfies its own characteristic equation.**

### 5.1 Concrete Example (2×2 case)

Let `A = [[a, b], [c, d]] ∈ M₂(F)`. Then:
```
Δ_A = x² − (a+d)x + (ad−bc)
```
Cayley–Hamilton says:
```
A² − (a+d)A + (ad−bc)I₂ = 0
```
You can verify this directly by matrix multiplication — it is true but non-obvious!

### 5.2 Proof (Adjugate Method)

**Setup.** Let `A ∈ Mₙ(F)` and write `Δ_A = a₀ + a₁x + … + aₙxⁿ`. We want to show:
```
a₀Iₙ + a₁A + … + aₙAⁿ = 0
```

**Step 1.** Consider the matrix `(xIₙ − A)` with entries in `F[x]`. Its adjugate `B(x) = adj(xIₙ − A)` has polynomial entries, and each entry has degree at most `n−1`. Write:
```
B(x) = B₀ + B₁x + … + Bₙ₋₁xⁿ⁻¹,   Bᵢ ∈ Mₙ(F)
```

**Step 2.** By the adjugate identity `adj(M) · M = det(M) · Iₙ`:
```
B(x) · (xIₙ − A) = Δ_A(x) · Iₙ = (a₀ + a₁x + … + aₙxⁿ) · Iₙ
```

**Step 3.** Expand the left side and compare coefficients of `xᵏ` for `k = 0, 1, …, n`:

| Power of x | Equation |
|---|---|
| `x⁰` | `−B₀A = a₀Iₙ` |
| `x¹` | `B₀ − B₁A = a₁Iₙ` |
| `x²` | `B₁ − B₂A = a₂Iₙ` |
| ⋮ | ⋮ |
| `xᵏ` | `Bₖ₋₁ − BₖA = aₖIₙ` |
| ⋮ | ⋮ |
| `xⁿ` | `Bₙ₋₁ = aₙIₙ` |

**Step 4.** Multiply the `xᵏ`-equation on the right by `Aᵏ` and sum over `k = 0, …, n`:

```
−B₀A⁰·A  +  (B₀ − B₁A)A  +  (B₁ − B₂A)A²  +  …  +  Bₙ₋₁Aⁿ
= a₀Iₙ + a₁A + a₂A² + … + aₙAⁿ
```

The left side telescopes to **0** (each `BₖAᵏ⁺¹` appears with opposite signs). Therefore:
```
a₀Iₙ + a₁A + … + aₙAⁿ = 0   ∎
```

> ⚠️ **Common misconception:** You cannot prove Cayley–Hamilton by "substituting `A` for `x`" in `det(A − xI)` and claiming `det(A − A) = det(0) = 0`. This is wrong because `x` is a scalar variable, not a matrix — the substitution is not valid in the determinant.

---

## 6. Consequences and Applications

### 6.1 Minimum Polynomial Divides Characteristic Polynomial

Since `Δ_φ(φ) = 0` (Cayley–Hamilton), the divisibility property gives:
```
m_φ  |  Δ_φ
```
This bounds the degree: `1 ≤ deg m_φ ≤ n`.

### 6.2 Computing the Inverse via Cayley–Hamilton

If `A` is invertible, then `a₀ = Δ_A(0) = det(A) ≠ 0`. From:
```
a₀Iₙ + a₁A + … + aₙAⁿ = 0
```
Rearrange:
```
a₀Iₙ = −(a₁A + a₂A² + … + aₙAⁿ) = −A(a₁Iₙ + a₂A + … + aₙAⁿ⁻¹)
```
Therefore:
```
A⁻¹ = −(1/a₀)(a₁Iₙ + a₂A + … + aₙAⁿ⁻¹)
```
This expresses `A⁻¹` as a polynomial in `A` — no row reduction needed!

**Example.** Let `A = [[1, 2], [3, 4]]`. Then `Δ_A = x² − 5x − 2`, so:
```
A² − 5A − 2I = 0  ⟹  A⁻¹ = −½(A − 5I) = −½[[-4,2],[3,-1]] = [[2, -1],[-3/2, 1/2]]
```

### 6.3 Reducing High Powers of Matrices

Cayley–Hamilton (or the minimum polynomial) lets you reduce `Aᵏ` for large `k` to a linear combination of `{I, A, …, Aⁿ⁻¹}`.

**Method:** Divide `xᵏ` by `m_A(x)` (or `Δ_A(x)`) to get `xᵏ = q(x)·m_A(x) + r(x)` with `deg r < deg m_A`. Then:
```
Aᵏ = q(A)·m_A(A) + r(A) = 0 + r(A) = r(A)
```

**Example.** For `A = [[0,1],[0,0]]`, `m_A = x²`, so `A² = 0`. Then `A¹⁰⁰ = 0`.

### 6.4 Diagonalisability Criterion via Minimum Polynomial

> **Theorem.** `φ` is diagonalisable over `F` if and only if `m_φ` splits into **distinct** linear factors over `F`.

That is, `m_φ = (x − λ₁)(x − λ₂)···(x − λₖ)` with `λᵢ` distinct.

| Minimum polynomial | Conclusion |
|---|---|
| `(x−λ₁)(x−λ₂)` with `λ₁ ≠ λ₂` | Diagonalisable |
| `(x−λ)²` | **Not** diagonalisable (non-trivial Jordan block) |
| `(x−λ)` | Scalar matrix `λI` |

---

## 7. Finding the Minimum Polynomial in Practice

### Method 1: From the Characteristic Polynomial

1. Compute `Δ_A(x)`.
2. The minimum polynomial `m_A` divides `Δ_A` and has the same irreducible factors.
3. Test divisors of `Δ_A` (starting from smallest degree) by checking if they annihilate `A`.

**Example.** Suppose `Δ_A = (x−2)²(x−3)`. Possible minimum polynomials:
- `(x−2)(x−3)` — test: does `(A−2I)(A−3I) = 0`?
- `(x−2)²(x−3)` — this is `Δ_A` itself, always works by Cayley–Hamilton.

### Method 2: Direct Computation

For small matrices, compute `I, A, A², …` and find the first linear dependence:
```
a₀I + a₁A + … + aₖAᵏ = 0
```
The resulting monic polynomial is `m_A`.

---

## 8. Key Theorems Summary

| Result | Statement |
|---|---|
| **Existence of min. poly.** | Every `φ ∈ L(V)` has a monic annihilating polynomial |
| **Uniqueness** | The minimum polynomial is unique |
| **Divisibility** | `p(φ)=0 ⟹ m_φ | p` |
| **Eigenvalue–root correspondence** | Eigenvalues of `φ` = roots of `m_φ` = roots of `Δ_φ` |
| **Cayley–Hamilton** | `Δ_φ(φ) = 0` |
| **m divides Δ** | `m_φ | Δ_φ` (follows from C–H + divisibility) |
| **Diagonalisability** | `φ` diagonalisable ⟺ `m_φ` has distinct linear factors |

---

## 9. Common Mistakes & Corrections

| ❌ Mistake | ✅ Correction |
|---|---|
| "Substituting `A` for `x` in `det(A − xI)` gives `det(0) = 0`, proving C–H" | This is invalid — `x` is a scalar, not a matrix. Use the adjugate proof. |
| "The minimum polynomial equals the characteristic polynomial" | Not always: e.g., `A = λI` has `m_A = x−λ` but `Δ_A = (x−λ)ⁿ` |
| "If `m_φ(λ) = 0` then `λ` might not be an eigenvalue" | Wrong — roots of `m_φ` are always eigenvalues |
| "Cayley–Hamilton only works over ℝ or ℂ" | It holds over any field `F` |
| "The minimum polynomial can have degree greater than `n`" | No — `m_φ | Δ_φ` and `deg Δ_φ = n`, so `deg m_φ ≤ n` |

---

## 10. Worked Examples

### Example 1: Find `m_A` for a 3×3 matrix

Let `A = diag(1, 1, 2)`. Then `Δ_A = (x−1)²(x−2)`.

Candidates for `m_A` (must share roots 1 and 2):
- Try `p = (x−1)(x−2)`: compute `(A−I)(A−2I) = diag(0,0,1)·diag(-1,-1,0) = diag(0,0,0) = 0`. ✓

So `m_A = (x−1)(x−2)`. Note `m_A ≠ Δ_A` here. Also, since `m_A` has distinct linear factors, `A` is diagonalisable (as expected).

### Example 2: Non-diagonalisable matrix

Let `A = [[1,1],[0,1]]`. Then `Δ_A = (x−1)²`.

Try `m_A = x−1`: `A − I = [[0,1],[0,0]] ≠ 0`. ✗

Try `m_A = (x−1)²`: `(A−I)² = [[0,1],[0,0]]² = [[0,0],[0,0]] = 0`. ✓

So `m_A = (x−1)²`. Since `m_A` has a repeated factor, `A` is **not** diagonalisable.

### Example 3: Using Cayley–Hamilton to find A⁻¹

Let `A = [[2, 1], [1, 3]]`. Then `Δ_A = x² − 5x + 5`.

By Cayley–Hamilton: `A² − 5A + 5I = 0`, so `A(A − 5I) = −5I`, giving:
```
A⁻¹ = −(1/5)(A − 5I) = (1/5)(5I − A) = (1/5)[[3,-1],[-1,2]]
```

---

## 11. Self-Assessment Checklist

- [ ] I can define the minimum polynomial and prove existence and uniqueness from scratch
- [ ] I can state the divisibility property and use it to find `m_φ`
- [ ] I can state Cayley–Hamilton and explain why the "naive" proof is wrong
- [ ] I can reproduce the adjugate proof of Cayley–Hamilton
- [ ] I can identify eigenvalues as roots of `m_φ`
- [ ] I can use Cayley–Hamilton to compute `A⁻¹` and reduce high powers of `A`
- [ ] I can determine diagonalisability from `m_φ`
- [ ] I understand the relationship `m_φ | Δ_φ` and same-roots property

---

## 12. Learning Path

### Phase 1: Foundations (Day 1)
- Review polynomials in operators and the eigenvector lemma
- Learn the definition and existence/uniqueness proof of `m_φ`
- Practice: compute `m_A` for 2×2 diagonal and Jordan-block matrices

### Phase 2: Core Theorems (Days 2–3)
- Study the divisibility property and its proof
- Learn the eigenvalue–root correspondence
- State and understand Cayley–Hamilton; work through the 2×2 example by hand
- Study the adjugate proof carefully

### Phase 3: Applications (Days 4–5)
- Practice computing `A⁻¹` via Cayley–Hamilton
- Practice reducing `Aᵏ` using the minimum polynomial
- Apply the diagonalisability criterion
- Solve past exam problems on these topics

---

*Source: Linear Algebra lecture notes (linear_algebra_notes collection), Sections 3.3–3.5*
