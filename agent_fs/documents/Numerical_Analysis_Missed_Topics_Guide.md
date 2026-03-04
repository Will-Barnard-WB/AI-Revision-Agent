# Numerical Analysis — Missed Topics Study Guide

Topics covered: **Secant Method · Absolute Error · Relative Error · Convergence**

---

## 1. Secant Method

### Definition
The **Secant Method** is a root-finding method that uses **secant lines** (lines through two points on the curve) instead of tangent lines, requiring **two initial guesses** to find successively better approximations to a root.

### How it works
It is essentially Newton's Method, but avoids computing the derivative by approximating it using two previous iterates:

$$x_{n+1} = x_n - f(x_n) \cdot \frac{x_n - x_{n-1}}{f(x_n) - f(x_{n-1})}$$

Instead of needing $f'(x_n)$ (as Newton's Method does), it estimates the slope using the **secant line** between $(x_{n-1}, f(x_{n-1}))$ and $(x_n, f(x_n))$.

### Key comparison with Newton's Method

| Feature | Newton's Method | Secant Method |
|---|---|---|
| Uses derivative? | ✅ Yes | ❌ No |
| Initial guesses needed | 1 | **2** |
| Order of convergence | Quadratic (~2) | Superlinear (~1.618) |
| When to use | Derivative easy to compute | Derivative hard/expensive to compute |

### Key things to remember
- Uses **secant lines**, not tangents
- Needs **two** starting points $x_0$ and $x_1$
- Useful when $f'(x)$ is hard to compute
- Slightly slower convergence than Newton's Method, but more practical

---

## 2. Absolute Error

### Definition
**Absolute Error** is the difference between the **true value** and the **approximate (computed) value**:

$$\text{Absolute Error} = |x - x_c|$$

where $x$ is the true value and $x_c$ is the computed approximation.

### Example (from lecture notes)
For a root $x_+ = -10^{-9}$ with computed value $x_c^+ = 0$:

$$\text{Absolute Error} = |x_+ - x_c^+| \approx 10^{-9}$$

This is a very small absolute error — but don't be fooled! See Relative Error below.

### Key things to remember
- It is always **non-negative** (take the absolute value)
- It is a **simple difference** — no division involved
- A small absolute error doesn't always mean a good approximation (depends on the scale of the true value)

---

## 3. Relative Error

### Definition
**Relative Error** is the absolute error **divided by the true value**, often expressed as a percentage:

$$\text{Relative Error} = \frac{|x - x_c|}{|x|}$$

### Why it matters
Relative error gives a sense of the error **in proportion to the size of the true value**.

### Example (from lecture notes)
Continuing the example above, with $x_+ = -10^{-9}$ and $x_c^+ = 0$:

$$\text{Relative Error} = \frac{10^{-9}}{10^{-9}} = 1$$

A relative error of **1** means **100% error** — the approximation has **no correct digits**, even though the absolute error was tiny ($10^{-9}$)! This shows why relative error is often more informative.

### Key things to remember
- Relative Error = Absolute Error ÷ |True Value|
- Captures how significant the error is **relative to the scale** of the answer
- Often more meaningful than absolute error alone

### Side-by-side summary

| | Formula | Measures |
|---|---|---|
| **Absolute Error** | $\|x - x_c\|$ | Raw size of the error |
| **Relative Error** | $\|x - x_c\| / \|x\|$ | Error as a fraction of the true value |

---

## 4. Convergence

### Definition
**Convergence** is the property of a numerical method to produce results that **approach the exact solution** as the **number of iterations increases**.

Let $e_n = |x_n - x|$ be the error at step $n$. We say the method converges with **order $r$** if:

- **Linear convergence** ($r = 1$): $e_{n+1} \leq K e_n$ for some $K < 1$
- **Quadratic convergence** ($r = 2$): $e_{n+1} \leq K e_n^2$ for some $K > 0$
- **Superlinear convergence** ($1 < r < 2$): between the two above

### Convergence orders of common methods

| Method | Order of Convergence |
|---|---|
| Bisection Method | Linear ($r = 1$) |
| Secant Method | Superlinear ($r \approx 1.618$) |
| Newton's Method | Quadratic ($r = 2$) |

### Intuition for quadratic convergence
With quadratic convergence, the number of **correct digits roughly doubles** each iteration. From the lecture notes example of Newton's Method finding $\pi$:
- $x_1$: 3 correct digits
- $x_2$: 10 correct digits
- $x_3$: 11 correct digits (limited by rounding)

### Key things to remember
- Convergence is about behaviour **over iterations**, not machine precision
- Higher order = faster convergence
- A method can converge but still be slow (linear convergence with $K$ close to 1)
- Newton's Method converges **quadratically** if started close enough to the root

---

## Quick-Reference Summary

| Topic | One-line definition |
|---|---|
| **Secant Method** | Root-finding using secant lines; needs 2 initial guesses; avoids computing derivatives |
| **Absolute Error** | $\|$true − approximate$\|$ |
| **Relative Error** | Absolute error ÷ $\|$true value$\|$ |
| **Convergence** | Results approach the exact solution as iterations increase |
