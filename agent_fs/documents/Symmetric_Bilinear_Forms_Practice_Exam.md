# Symmetric Bilinear Forms - Practice Exam

## Section A: Definitions (5 points each)
1. Define a symmetric bilinear form. 
   
   **Answer:**  
   
2. What is the rank of a symmetric bilinear form?  
   
   **Answer:**  

## Section B: Multiple Choice (5 points each)
3. Which of the following statements is true about a symmetric bilinear form B on a vector space V?  
   - A) B(v, w) = B(w, v) for all v, w in V  
   - B) B(v, w) = -B(w, v) for all v, w in V  
   - C) B(v, w) = 0 for all v, w in V  
   - D) B(v, w) is always positive  
   
   **Answer:**  

4. According to Sylvester’s Theorem, a symmetric bilinear form can be represented by which of the following?  
   - A) A triangular matrix  
   - B) A diagonal matrix  
   - C) A zero matrix  
   - D) An identity matrix  
   
   **Answer:**  

## Section C: Short Answer (10 points each)
5. Explain the concept of the radical of a symmetric bilinear form.  
   
   **Answer:**  

6. Describe the Diagonalisation Theorem in the context of symmetric bilinear forms.  
   
   **Answer:**  

## Section D: Long Answer (20 points each)
7. Given a symmetric matrix A, explain how the bilinear form B(v, w) = v^T A w is a symmetric bilinear form. Provide a brief example to illustrate your explanation.  
   
   **Answer:**  

8. Consider a symmetric bilinear form B on a finite-dimensional vector space. If the rank of B is 3, what can you say about the dimension of the radical? Justify your answer.  
   
   **Answer:**  

## Answer Key

### A. Definitions
1. A symmetric bilinear form is a function B: V × V → F such that B(v, w) = B(w, v) for all v, w in V.
2. The rank of a symmetric bilinear form is the dimension of the image of the associated linear map.

### B. Multiple Choice
3. A) B(v, w) = B(w, v) for all v, w in V
4. B) A diagonal matrix

### C. Short Answer
5. The radical of a symmetric bilinear form is the set of vectors v such that B(v, w) = 0 for all w in V.
6. The Diagonalisation Theorem states that for a symmetric bilinear form B on a finite-dimensional vector space over a field F, there exists a basis v1,...,vn such that B(vi, vj) = 0 for all i ≠ j.

### D. Long Answer
7. B(v, w) = v^T A w is a symmetric bilinear form because A is symmetric, meaning that A^T = A, which ensures that B(v, w) = B(w, v).
   Example: Let A = \[ \begin{pmatrix} 1 & 2 \\ 2 & 3 \end{pmatrix} \]. Then B(v, w) = v^T A w is symmetric.
8. If the rank of B is 3, then the dimension of the radical is at least the dimension of the vector space minus the rank, which indicates that there are vectors in the radical that are orthogonal to the image of B.