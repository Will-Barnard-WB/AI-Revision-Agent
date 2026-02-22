# Symmetric Bilinear Forms - Practice Exam

## Section A: Definitions (5 points each)
1. Define a symmetric bilinear form and provide an example.

**Answer:**  

2. What is Sylvester’s Theorem and how does it relate to symmetric bilinear forms?  

**Answer:**  

## Section B: Short Answer (10 points each)
3. State and explain the Diagonalisation Theorem.

**Answer:**  

4. Describe the concepts of rank and radical in the context of symmetric bilinear forms.

**Answer:**  

5. Given a symmetric matrix, explain how to determine if it represents a symmetric bilinear form.

**Answer:**  

## Section C: Problem Solving (20 points each)
6. **Problem:** Given the symmetric matrix \( A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix} \), determine if it represents a symmetric bilinear form. If it does, find the associated bilinear form and compute its value for the vectors \( \mathbf{u} = \begin{pmatrix} 1 \\ 0 \end{pmatrix} \) and \( \mathbf{v} = \begin{pmatrix} 0 \\ 1 \end{pmatrix} \).

## Answer Key

### A. Definitions
1. **Answer:** A symmetric bilinear form is a function \( B: V \times V \to \mathbb{R} \) such that \( B(u, v) = B(v, u) \) for all vectors \( u, v \in V \). An example is \( B(x, y) = x^T A y \) where \( A \) is a symmetric matrix.

2. **Answer:** Sylvester’s Theorem states that the number of positive, negative, and zero eigenvalues of a symmetric bilinear form can be determined by the number of positive and negative pivots in its associated matrix. This relates to the classification of the form as definite, indefinite, or semi-definite.

### B. Short Answer
3. **Answer:** The Diagonalisation Theorem states that any symmetric matrix can be diagonalised by an orthogonal matrix. This means there exists an orthogonal matrix \( P \) such that \( P^T A P = D \), where \( D \) is a diagonal matrix.
4. **Answer:** The rank of a symmetric bilinear form is the dimension of the image of the associated matrix, while the radical is the kernel of the bilinear form, representing the vectors that yield a zero value when plugged into the form.
5. **Answer:** To determine if a symmetric matrix represents a symmetric bilinear form, check if the matrix is symmetric (i.e., \( A = A^T \)) and then verify that the bilinear form defined by the matrix is indeed symmetric.

### C. Problem Solving
6. **Answer:** The matrix \( A \) represents a symmetric bilinear form. The associated bilinear form is given by \( B(u, v) = u^T A v \). For the vectors \( \mathbf{u} \) and \( \mathbf{v} \), we compute:
   \[ B(\mathbf{u}, \mathbf{v}) = \begin{pmatrix} 1 & 0 \end{pmatrix} \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix} \begin{pmatrix} 0 \\ 1 \end{pmatrix} = 1. \]  
   Thus, the value is 1.