# Eigenvalues - Study Guide

## Learning Objectives
By the end, you should be able to:
- Define eigenvalues and their multiplicities.
- Explain the significance of the Fundamental Theorem of Algebra in relation to eigenvalues.
- Apply the properties of eigenvalues and eigenvectors with polynomials.

## Prerequisite Knowledge
- Linear operators on vector spaces.
- Basic properties of polynomials.

## Learning Path
### Phase 1: Foundations (Days 1-2)
- **Topic to learn:** Definitions of eigenvalues and their multiplicities.
  - **Practice:** Review definitions and examples of eigenvalues.
  - **Check understanding:** What is the difference between algebraic and geometric multiplicity?

### Phase 2: Core Concepts (Days 3-5)
- **Topic to learn:** Theorems related to eigenvalues.
  - **Practice:** Work through examples of applying the Fundamental Theorem of Algebra.

### Phase 3: Advanced Applications (Days 6-7)
- **Topic to learn:** Eigenvalues and eigenvectors with polynomials.
  - **Practice:** Solve problems involving polynomials and eigenvalues.

## Key Concepts
- **Eigenvalue (λ):** A scalar associated with a linear operator φ such that there exists a non-zero vector v (eigenvector) satisfying φ(v) = λv.
- **Algebraic Multiplicity (am(λ)):** The multiplicity of λ as a root of the characteristic polynomial ∆φ.
- **Geometric Multiplicity (gm(λ)):** The dimension of the eigenspace Eφ(λ), which is the set of all eigenvectors associated with λ.

## Core Content
### Definitions
1. **Eigenvalue (λ):** Let φ ∈ L(V) be a linear operator on a finite-dimensional vector space V over a field F. An eigenvalue λ of φ satisfies the equation φ(v) = λv for some non-zero vector v (eigenvector).
2. **Algebraic Multiplicity (am(λ)):** The number of times λ appears as a root of the characteristic polynomial ∆φ.
3. **Geometric Multiplicity (gm(λ)):** The dimension of the eigenspace Eφ(λ), which consists of all eigenvectors corresponding to λ.

### Theorems
- **Fundamental Theorem of Algebra:** When F = C, this theorem ensures that the characteristic polynomial has at least one root, implying that φ has at least one eigenvalue.
- **Theorem 3.9:** Let φ be a linear operator on a finite-dimensional vector space V over C. Then φ has an eigenvalue.

### Important Relationships
- Eigenvalues and eigenvectors are closely related to polynomials. If v is an eigenvector of φ with eigenvalue λ, then for any polynomial p ∈ F[x], it holds that p(φ)(v) = p(λ)v. This means that v is also an eigenvector of p(φ) with eigenvalue p(λ).

## Key Formulas/Theorems
- **Eigenvalue Equation:** φ(v) = λv
- **Characteristic Polynomial:** ∆φ(x) = det(xI - A) where A is the matrix representation of φ.

## Common Mistakes & Corrections
- **Mistake 1:** Confusing algebraic and geometric multiplicity. 
  - **Correction:** Remember that algebraic multiplicity refers to the number of times an eigenvalue appears as a root, while geometric multiplicity refers to the dimension of the eigenspace.
- **Mistake 2:** Assuming all eigenvalues are distinct. 
  - **Correction:** Eigenvalues can have multiplicities; always check the characteristic polynomial.

## Self-Assessment Checklist
- [ ] I understand the definitions of eigenvalues, algebraic multiplicity, and geometric multiplicity.
- [ ] I can explain the significance of the Fundamental Theorem of Algebra in relation to eigenvalues.
- [ ] I can apply the properties of eigenvalues and eigenvectors with polynomials.

## Resources for Practice
- **Practice problems:** Textbook exercises on eigenvalues and eigenvectors.
- **Worked examples:** Lecture notes and additional resources on linear algebra.

## Learning Objectives
By the end, you should be able to:
- Define eigenvalues and eigenvectors.
- Understand the characteristic polynomial and its significance.
- Explain the concepts of algebraic and geometric multiplicity.
- Apply theorems related to eigenvalues in linear algebra.

## Prerequisite Knowledge
- Basic understanding of vector spaces.
- Familiarity with linear transformations and matrices.

## Learning Path
### Phase 1: Foundations (Days 1-2)
- **Topic to learn:** Definitions of eigenvalues and eigenvectors.
- **Practice:** Solve problems identifying eigenvalues and eigenvectors from given matrices.
- **Check understanding:** What is the definition of an eigenvalue?

### Phase 2: Core Concepts (Days 3-5)
- **Topic to learn:** Characteristic polynomial and its role in finding eigenvalues.
- **Practice:** Calculate the characteristic polynomial for various matrices.

### Phase 3: Advanced Applications (Days 6-7)
- **Topic to learn:** Algebraic and geometric multiplicity of eigenvalues.
- **Practice:** Determine the multiplicities for given eigenvalues.

## Key Concepts
- **Eigenvalue:** A scalar \( \lambda \in F \) such that there exists a non-zero vector \( v \in V \) with \( \phi(v) = \lambda v \).
- **Eigenvector:** A vector associated with an eigenvalue, satisfying the equation above.
- **Eigenspace:** The set of all eigenvectors corresponding to an eigenvalue \( \lambda \), denoted as \( E_{\phi}(\lambda) = \text{ker}(\phi - \lambda \text{id}_V) \).

## Core Content
### Characteristic Polynomial
- The characteristic polynomial \( \Delta_{\phi}(\lambda) \) is defined as:
  \[ \Delta_{\phi}(\lambda) = \text{det}(\phi - \lambda \text{id}_V) = \text{det}(A - \lambda I) \]
  where \( A \) is the matrix representation of \( \phi \).
- **Importance:** A scalar \( \lambda \) is an eigenvalue of \( \phi \) if and only if it is a root of the characteristic polynomial.

### Multiplicities
1. **Algebraic Multiplicity (am):** The number of times an eigenvalue appears as a root of the characteristic polynomial.
2. **Geometric Multiplicity (gm):** The dimension of the eigenspace corresponding to an eigenvalue.
- **Relationship:** \( am(\lambda) \geq gm(\lambda) \)

## Important Theorems
- **Theorem 3.9:** If \( \phi \) is a linear operator on a finite-dimensional vector space \( V \) over \( \mathbb{C} \), then \( \phi \) has at least one eigenvalue.

## Examples & Applications
- **Example 1:** Given a matrix, find its eigenvalues by calculating the characteristic polynomial and identifying its roots.
- **Example 2:** Determine the eigenvectors corresponding to a specific eigenvalue.

## Common Mistakes & Corrections
- **Mistake 1:** Confusing eigenvalues with eigenvectors. Remember, eigenvalues are scalars, while eigenvectors are vectors.
- **Mistake 2:** Miscalculating the characteristic polynomial. Ensure to correctly apply the determinant formula.

## Self-Assessment Checklist
- [ ] I understand the definition of eigenvalues and eigenvectors.
- [ ] I can calculate the characteristic polynomial for a matrix.
- [ ] I can determine the algebraic and geometric multiplicities of eigenvalues.

## Resources for Practice
- Practice problems: Linear Algebra textbooks or online resources.
- Worked examples: Lecture notes or supplementary materials.