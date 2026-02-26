# Eigenvalues - Practice Exam

## Section A: Multiple Choice (5 points each)
1. What is an eigenvalue of a linear operator φ?
   - A) A scalar λ such that φ(v) = λv for some non-zero vector v.
   - B) A vector that is scaled by φ.
   - C) A matrix that represents φ.
   - D) None of the above.

2. The characteristic polynomial ∆ φ(λ) is defined as:
   - A) det(φ - λI)
   - B) det(φ + λI)
   - C) λ^n - det(φ)
   - D) None of the above.

3. If λ is an eigenvalue of φ, what can be said about the eigenspace Eφ(λ)?
   - A) It contains only the zero vector.
   - B) It contains all eigenvectors corresponding to λ.
   - C) It is always one-dimensional.
   - D) None of the above.

4. The algebraic multiplicity of an eigenvalue λ is:
   - A) The number of times λ appears as a root of the characteristic polynomial.
   - B) The dimension of the eigenspace corresponding to λ.
   - C) Always equal to the geometric multiplicity.
   - D) None of the above.

5. According to the Fundamental Theorem of Algebra, if φ is a linear operator on a finite-dimensional vector space over C, then:
   - A) φ has no eigenvalues.
   - B) φ has at least one eigenvalue.
   - C) φ has infinitely many eigenvalues.
   - D) None of the above.

## Section B: Short Answer (10 points each)

3. Explain the significance of the Fundamental Theorem of Algebra in relation to eigenvalues.  
   **Answer:**  
   
4. State Theorem 3.9 and explain its importance in the context of linear operators.  
   **Answer:**  

1. Define the term "eigenvector" in the context of linear operators.

2. Explain the relationship between the characteristic polynomial and eigenvalues.

3. What is the difference between algebraic multiplicity and geometric multiplicity?

## Section C: Problem Solving (20 points each)
1. Given the matrix A = \[ \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix} \], find the eigenvalues of A. Show your work.

2. Consider the linear operator φ on a vector space V defined by φ(v) = 3v for all v in V. Determine the eigenvalue and the corresponding eigenspace.

## Answer Key

### A. Multiple Choice
1. A
2. A
3. B
4. A
5. B

### B. Short Answer
1. An eigenvector of a linear operator φ is a non-zero vector v such that φ(v) = λv for some scalar λ, known as the eigenvalue.
2. The characteristic polynomial ∆ φ(λ) is a polynomial whose roots are the eigenvalues of the linear operator φ. It is defined as det(φ - λI).
3. The algebraic multiplicity of an eigenvalue λ is the number of times it appears as a root of the characteristic polynomial, while the geometric multiplicity is the dimension of the eigenspace corresponding to λ.

### C. Problem Solving
1. To find the eigenvalues of A, we solve the characteristic polynomial det(A - λI) = 0:
   \[ \begin{pmatrix} 2 - \lambda & 1 \\ 1 & 2 - \lambda \end{pmatrix} \]
   The determinant is (2 - λ)(2 - λ) - 1 = 0, leading to λ^2 - 4λ + 3 = 0, which factors to (λ - 3)(λ - 1) = 0. Thus, the eigenvalues are λ = 3 and λ = 1.

2. The eigenvalue is λ = 3, and the eigenspace is the entire vector space V since every vector is an eigenvector corresponding to λ = 3.