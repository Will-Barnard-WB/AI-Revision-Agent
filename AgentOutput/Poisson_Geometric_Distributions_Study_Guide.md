# Poisson & Geometric Distributions — Study Guide

## Learning Objectives
By the end of this guide, you should be able to:
- [ ] State the PMF, mean, and variance of both distributions from memory
- [ ] Prove E[X] and Var(X) for both distributions from first principles
- [ ] Derive and use the MGF and PGF for both distributions
- [ ] State and prove the memoryless property of the Geometric distribution
- [ ] Explain why the Geometric is the *only* discrete memoryless distribution
- [ ] Prove the Poisson as a limit of the Binomial (Poisson Limit Theorem)
- [ ] Prove the additive property of independent Poisson random variables
- [ ] Identify when to use each distribution and apply them to real problems
- [ ] Relate both distributions to their continuous analogues (Exponential, Gamma)

---

## Prerequisite Knowledge
- Discrete random variables and probability mass functions (PMFs)
- Geometric series: `Σ rᵏ = 1/(1−r)` for `|r| < 1`
- Taylor series for `eˣ = Σ xᵏ/k!`
- Moment generating functions (MGFs): `M(t) = E[eᵗˣ]`
- Probability generating functions (PGFs): `G(z) = E[zˣ]`
- Basic combinatorics and the Binomial distribution

---

---

# PART I: THE POISSON DISTRIBUTION

---

## 1. Definition & Setup

The **Poisson distribution** models the **number of events** occurring in a fixed interval of time, space, or volume, under the following conditions:

1. Events occur **independently** of one another.
2. Events occur at a **constant average rate** λ.
3. Two events **cannot occur simultaneously**.
4. The probability of an event in a tiny interval is proportional to the interval's length.

**Notation:** `X ~ Poi(λ)`

**Support:** `k ∈ {0, 1, 2, 3, …}`

**Real-world examples:**
- Phone calls arriving at a call centre per hour
- Radioactive decay events per second
- Typos per page of a book
- Emails received per day
- Road accidents at an intersection per month

---

## 2. Probability Mass Function (PMF)

```
P(X = k) = (λᵏ · e^{−λ}) / k!,    k = 0, 1, 2, …
```

**Verification (sums to 1):** Using the Taylor series `eˣ = Σ xᵏ/k!`:
```
Σ P(X=k) = e^{−λ} · Σ λᵏ/k! = e^{−λ} · e^λ = 1  ✓
```

**Shape:**
- Small λ (< 1): heavily right-skewed, mode at k = 0
- Larger λ: more symmetric, approaches Normal distribution
- **Mode:** ⌊λ⌋ (if λ is an integer, both λ and λ−1 are modes)

---

## 3. Parameter λ

- **λ (lambda)** = mean number of events in the interval; λ > 0
- λ is **scale-dependent**: if the rate is μ per unit time, use `λ = μ · t` for an interval of length t
- λ is simultaneously the **mean** and the **variance** — a defining characteristic

---

## 4. Derivation: Poisson as a Limit of the Binomial

> **Poisson Limit Theorem.** If `X ~ Bin(n, p)` and we let `n → ∞`, `p → 0` with `np = λ` fixed, then `P(X = k) → λᵏ e^{−λ} / k!`.

**Proof:**
```
P(X = k) = C(n,k) · pᵏ · (1−p)^{n−k}
          = [n(n−1)···(n−k+1) / k!] · (λ/n)ᵏ · (1 − λ/n)^{n−k}
          = (λᵏ/k!) · [n(n−1)···(n−k+1)/nᵏ] · (1 − λ/n)ⁿ · (1 − λ/n)^{−k}
```
As n → ∞:
- `n(n−1)···(n−k+1)/nᵏ → 1`
- `(1 − λ/n)ⁿ → e^{−λ}`
- `(1 − λ/n)^{−k} → 1`

Therefore: `P(X = k) → λᵏ e^{−λ} / k!`  ∎

**Rule of thumb for approximation:** Use Poi(λ) ≈ Bin(n, p) when n ≥ 20 and p ≤ 0.05.

---

## 5. Mean: E[X] = λ

**Proof:**
```
E[X] = Σ_{k=0}^∞  k · λᵏ e^{−λ} / k!
```
The k = 0 term vanishes. Factor out λ and re-index with j = k − 1:
```
     = e^{−λ} · Σ_{k=1}^∞  λᵏ / (k−1)!
     = λ e^{−λ} · Σ_{j=0}^∞  λʲ / j!
     = λ e^{−λ} · e^λ
     = λ  ∎
```

---

## 6. Variance: Var(X) = λ

**Strategy:** Use `Var(X) = E[X(X−1)] + E[X] − (E[X])²`.

**Step 1 — Compute E[X(X−1)]:**
```
E[X(X−1)] = Σ_{k=2}^∞  k(k−1) · λᵏ e^{−λ} / k!
           = λ² e^{−λ} · Σ_{j=0}^∞  λʲ / j!
           = λ²
```

**Step 2 — Compute E[X²]:**
```
E[X²] = E[X(X−1)] + E[X] = λ² + λ
```

**Step 3:**
```
Var(X) = E[X²] − (E[X])² = (λ² + λ) − λ² = λ  ∎
```

> **Key insight:** Mean = Variance = λ is a hallmark of the Poisson. If observed variance >> mean (overdispersion), a Poisson model may be inappropriate.

---

## 7. Moment Generating Function (MGF)

```
M_X(t) = E[eᵗˣ] = exp(λ(eᵗ − 1)),    t ∈ ℝ
```

**Derivation:**
```
M_X(t) = Σ eᵗᵏ · λᵏ e^{−λ} / k!
        = e^{−λ} · Σ (λeᵗ)ᵏ / k!
        = e^{−λ} · e^{λeᵗ}
        = exp(λ(eᵗ − 1))  ∎
```

**Recovering moments:**
- `M'(0) = λ` → E[X] = λ ✓
- `M''(0) = λ² + λ` → Var(X) = λ ✓

**Cumulant Generating Function:** `K(t) = ln M(t) = λ(eᵗ − 1)`

All cumulants equal λ: `κ₁ = κ₂ = κ₃ = … = λ`.

---

## 8. Probability Generating Function (PGF)

```
G_X(z) = E[zˣ] = exp(λ(z − 1)),    |z| ≤ 1
```

**Derivation:**
```
G_X(z) = e^{−λ} · Σ (λz)ᵏ / k! = e^{−λ} · e^{λz} = exp(λ(z−1))
```

**Note:** `M_X(t) = G_X(eᵗ)`.

**Factorial moments:** `G^{(n)}(1) = λⁿ`, so the n-th factorial moment is `E[X(X−1)···(X−n+1)] = λⁿ`.

---

## 9. Additive Property

> **Theorem.** If `X ~ Poi(λ₁)` and `Y ~ Poi(λ₂)` are **independent**, then `X + Y ~ Poi(λ₁ + λ₂)`.

**Proof via MGFs:**
```
M_{X+Y}(t) = M_X(t) · M_Y(t)
            = exp(λ₁(eᵗ−1)) · exp(λ₂(eᵗ−1))
            = exp((λ₁+λ₂)(eᵗ−1))
```
This is the MGF of `Poi(λ₁ + λ₂)`. Since MGFs uniquely determine distributions: `X + Y ~ Poi(λ₁ + λ₂)`.  ∎

**Generalisation:** `X₁ + … + Xₙ ~ Poi(λ₁ + … + λₙ)` for independent Poissons.

---

## 10. Connection to the Poisson Process

A **Poisson process** with rate μ is a continuous-time process `{N(t), t ≥ 0}` where:
1. `N(0) = 0`
2. **Independent increments** (non-overlapping intervals are independent)
3. **Stationary increments** (distribution depends only on interval length)
4. `N(t) ~ Poi(μt)` for any interval of length t
5. No simultaneous events

**Inter-arrival times:** `T₁, T₂, … ~ i.i.d. Exp(μ)` with mean `1/μ`

**Waiting time to k-th event:** `Sₖ = T₁ + … + Tₖ ~ Gamma(k, μ)`

**Key link:** `{N(t) ≥ k} ⟺ {Sₖ ≤ t}`

> **Note on memorylessness:** The Poisson distribution itself does NOT have the memoryless property (it is a count, not a waiting time). However, the *inter-arrival times* of a Poisson process are Exponential, which IS memoryless.

---

## 11. Relationships to Other Distributions

| Distribution | Relationship to Poisson |
|---|---|
| **Binomial(n, p)** | Poi(λ) is the limit as n→∞, p→0, np=λ |
| **Exponential(μ)** | Inter-arrival times of a Poi(μ) process |
| **Gamma(k, μ)** | Waiting time to k-th event in a Poi(μ) process |
| **Normal(λ, λ)** | Approximation for large λ (≥ 10–20) |
| **Negative Binomial** | Used when Var(X) > E[X] (overdispersion) |

**Normal approximation:** For large λ, `(X − λ)/√λ →^d N(0,1)`. Apply continuity correction: `P(X ≤ k) ≈ P(Z ≤ (k + 0.5 − λ)/√λ)`.

---

## 12. Worked Examples

### Example 1 — Call Centre
> A call centre receives **8 calls/hour**. Find P(X = 5) and P(X < 3).

`X ~ Poi(8)`

```
P(X = 5) = 8⁵ · e^{−8} / 5! = 32768 · e^{−8} / 120 ≈ 0.0916

P(X < 3) = P(X=0) + P(X=1) + P(X=2)
          = e^{−8}(1 + 8 + 32) ≈ 0.000335 × 41 ≈ 0.0138
```

### Example 2 — Radioactive Decay
> A source emits **3 particles/second**. Find P(X ≥ 2).

`X ~ Poi(3)`
```
P(X ≥ 2) = 1 − P(X=0) − P(X=1)
          = 1 − e^{−3} − 3e^{−3}
          = 1 − 4e^{−3} ≈ 1 − 0.1991 ≈ 0.8009
```

### Example 3 — Rescaling the Interval
> Emails arrive at **2/minute**. Find P(X = 7) in a **3-minute** window.

`λ = 2 × 3 = 6`, so `X ~ Poi(6)`
```
P(X = 7) = 6⁷ · e^{−6} / 7! = 279936 · e^{−6} / 5040 ≈ 0.1377
```

### Example 4 — Superposition
> Server A: λ₁ = 4/min, Server B: λ₂ = 6/min. Find P(total = 12 in 1 min).

`X + Y ~ Poi(10)`
```
P(X+Y = 12) = 10¹² · e^{−10} / 12! ≈ 0.0948
```

---

## 13. Common Mistakes — Poisson

| ❌ Mistake | ✅ Correction |
|---|---|
| Using per-hour rate for a 10-minute problem without rescaling | Always compute `λ = rate × interval length` |
| Confusing Poisson (count) with Exponential (waiting time) | Poisson counts events; Exponential models time *between* events |
| Claiming Poisson is memoryless | It is not — the inter-arrival times (Exponential) are memoryless |
| P(X ≥ 1) = 1 − P(X = 1) | P(X ≥ 1) = 1 − P(X = **0**) = 1 − e^{−λ} |
| Assuming mode = λ always | Mode = ⌊λ⌋; if λ ∈ ℤ, both λ and λ−1 are modes |
| Applying Poisson when events are not independent | Check independence; consider Negative Binomial for clustered data |
| Using Poisson approximation when p is not small | Only valid when n large AND p small (np = λ moderate) |

---

---

# PART II: THE GEOMETRIC DISTRIBUTION

---

## 14. Definition & The Two Conventions

> ⚠️ **Critical:** There are two standard conventions. Always state which you are using.

### Convention 1 — "Trials until first success"
```
X = number of trials needed to get the first success
Support: X ∈ {1, 2, 3, …}
PMF:     P(X = k) = (1−p)^{k−1} · p,    k = 1, 2, 3, …
```

### Convention 2 — "Failures before first success"
```
Y = number of failures before the first success
Support: Y ∈ {0, 1, 2, …}
PMF:     P(Y = k) = (1−p)^k · p,    k = 0, 1, 2, …
```

**Relationship:** `Y = X − 1`, so `P(Y = k) = P(X = k+1)`.

**Notation:** `X ~ Geo(p)` (convention 1 is more common in UK university courses)

**Parameter:** `p ∈ (0, 1)` = probability of success on each trial. Write `q = 1 − p`.

**Real-world examples:**
- Number of rolls of a die until a six appears
- Number of components tested until a defective one is found
- Number of job applications until the first offer

---

## 15. Verification: PMF Sums to 1

**Convention 1:**
```
Σ_{k=1}^∞ q^{k−1} · p = p · Σ_{j=0}^∞ qʲ = p · 1/(1−q) = p · 1/p = 1  ✓
```

**Convention 2:**
```
Σ_{k=0}^∞ qᵏ · p = p · 1/(1−q) = 1  ✓
```

Both use the geometric series `Σ qᵏ = 1/(1−q)` for `|q| < 1`.

---

## 16. Mean

### Convention 1: E[X] = 1/p

**Proof (derivative trick):**
```
E[X] = Σ_{k=1}^∞ k · q^{k−1} · p = p · Σ_{k=1}^∞ k · q^{k−1}
```
Recall that `d/dq [Σ qᵏ] = Σ k q^{k−1} = 1/(1−q)²`. Therefore:
```
E[X] = p · 1/(1−q)² = p · 1/p² = 1/p  ∎
```

### Convention 2: E[Y] = q/p = (1−p)/p

Since `Y = X − 1`:
```
E[Y] = E[X] − 1 = 1/p − 1 = (1−p)/p  ∎
```

**Intuition:** If each trial has probability p of success, you expect to need 1/p trials on average.

---

## 17. Variance: Var(X) = (1−p)/p² = q/p²

**Proof (using the falling moment):**

**Step 1 — Compute E[X(X−1)]:**
```
E[X(X−1)] = Σ_{k=1}^∞ k(k−1) · q^{k−1} · p
           = pq · Σ_{k=2}^∞ k(k−1) · q^{k−2}
```
Note `d²/dq² [Σ qᵏ] = Σ k(k−1) q^{k−2} = 2/(1−q)³`. Therefore:
```
E[X(X−1)] = pq · 2/p³ = 2q/p²
```

**Step 2 — Compute E[X²]:**
```
E[X²] = E[X(X−1)] + E[X] = 2q/p² + 1/p
```

**Step 3:**
```
Var(X) = E[X²] − (E[X])²
       = 2q/p² + 1/p − 1/p²
       = (2q + p − 1)/p²
       = (2q − q)/p²          [since p = 1−q, so p−1 = −q]
       = q/p²
       = (1−p)/p²  ∎
```

> **Note:** `Var(Y) = Var(X) = (1−p)/p²` since Y = X − 1 (shifting doesn't change variance).

---

## 18. Moment Generating Functions

### Convention 1 (X ∈ {1, 2, …}):
```
M_X(t) = E[eᵗˣ] = p·eᵗ / (1 − q·eᵗ),    valid for t < −ln(q)
```

**Derivation:**
```
M_X(t) = Σ_{k=1}^∞ eᵗᵏ · q^{k−1} · p
        = p·eᵗ · Σ_{k=1}^∞ (qeᵗ)^{k−1}
        = p·eᵗ · 1/(1 − qeᵗ)   [geometric series, valid when qeᵗ < 1]
```

### Convention 2 (Y ∈ {0, 1, 2, …}):
```
M_Y(t) = p / (1 − q·eᵗ),    valid for t < −ln(q)
```

**Relationship:** `M_X(t) = eᵗ · M_Y(t)` (consistent with Y = X − 1).

---

## 19. The Memoryless Property ⭐

> **Theorem.** If `X ~ Geo(p)` (Convention 1), then for all `m, n ≥ 1`:
> ```
> P(X > m + n | X > m) = P(X > n)
> ```

**Interpretation:** Given that the first success has not occurred in the first m trials, the probability of needing more than n additional trials is the same as if you were starting fresh. The past gives no information about the future.

**Proof:**

First, compute the survival function:
```
P(X > k) = Σ_{j=k+1}^∞ q^{j−1} · p = p · q^k / (1−q) = q^k
```

Now apply the conditional probability definition:
```
P(X > m+n | X > m) = P(X > m+n AND X > m) / P(X > m)
                   = P(X > m+n) / P(X > m)
                   = q^{m+n} / q^m
                   = q^n
                   = P(X > n)  ∎
```

---

## 20. Uniqueness of the Memoryless Property

> **Theorem.** The Geometric distribution is the **only** discrete distribution with the memoryless property.

**Proof sketch.** Suppose `P(X > m+n) = P(X > m) · P(X > n)` for all `m, n ≥ 0`. Let `f(k) = P(X > k)`. Then:
```
f(m + n) = f(m) · f(n)   for all m, n ∈ ℕ₀
```
This is Cauchy's functional equation on the integers. The only solution with `f(0) = 1` and `0 < f(k) < 1` is `f(k) = qᵏ` for some `q ∈ (0,1)`. This gives `P(X = k) = f(k−1) − f(k) = q^{k−1}(1−q)`, which is exactly the Geometric PMF with `p = 1 − q`.  ∎

**Continuous analogue:** The Exponential distribution is the *only* continuous memoryless distribution.

---

## 21. Cumulative Distribution Function (CDF)

### Convention 1:
```
P(X ≤ k) = 1 − q^k = 1 − (1−p)^k,    k = 1, 2, 3, …
```

**Proof:**
```
P(X ≤ k) = Σ_{j=1}^k q^{j−1} · p = p · (1 − qᵏ)/(1−q) = 1 − qᵏ
```

### Convention 2:
```
P(Y ≤ k) = 1 − q^{k+1} = 1 − (1−p)^{k+1},    k = 0, 1, 2, …
```

> ⚠️ **Off-by-one warning:** `P(X ≤ k) = 1 − qᵏ` but `P(Y ≤ k) = 1 − q^{k+1}`. Always check which convention you are using before applying the CDF.

---

## 22. Relationship to the Negative Binomial

The **Negative Binomial** distribution `NB(r, p)` counts the number of trials until the r-th success.

- `Geo(p)` is the special case `NB(1, p)`.
- If `X₁, …, Xᵣ ~ i.i.d. Geo(p)` (Convention 1), then `X₁ + … + Xᵣ ~ NB(r, p)`.

| Distribution | Trials until... | PMF |
|---|---|---|
| Geo(p) | 1st success | `q^{k−1} p` |
| NB(r, p) | r-th success | `C(k−1, r−1) q^{k−r} pʳ` |

---

## 23. Relationship to the Exponential Distribution

The Geometric and Exponential distributions are **discrete/continuous analogues**:

| Property | Geometric (discrete) | Exponential (continuous) |
|---|---|---|
| Models | Trials until first success | Time until first event |
| Support | {1, 2, 3, …} | (0, ∞) |
| PMF/PDF | `(1−p)^{k−1} p` | `μ e^{−μt}` |
| Mean | `1/p` | `1/μ` |
| Variance | `(1−p)/p²` | `1/μ²` |
| Memoryless | ✓ (unique discrete) | ✓ (unique continuous) |
| CDF | `1 − (1−p)^k` | `1 − e^{−μt}` |

**Connection via Poisson process:** In a Poisson process with rate μ, the number of events in a unit interval is `Poi(μ)`, and the waiting time until the first event is `Exp(μ)`. The Geometric arises when you discretise: if each time slot has probability `p = 1 − e^{−μ}` of containing an event, the slot of the first event is `Geo(p)`.

---

## 24. Worked Examples

### Example 1 — Rolling a Die
> A fair die is rolled repeatedly. Find the probability that the **first six** appears on the **4th roll**.

`X ~ Geo(1/6)`, `q = 5/6`
```
P(X = 4) = (5/6)³ · (1/6) = 125/1296 ≈ 0.0965
```

### Example 2 — Expected Rolls
> How many rolls do you expect to need to get the first six?

```
E[X] = 1/p = 1/(1/6) = 6 rolls
```

### Example 3 — CDF Application
> What is the probability that the first six appears **within the first 4 rolls**?

```
P(X ≤ 4) = 1 − (5/6)⁴ = 1 − 625/1296 = 671/1296 ≈ 0.5177
```

### Example 4 — Memoryless Property in Action
> You have already rolled the die 10 times without a six. What is the probability you need **more than 3 additional rolls**?

By the memoryless property:
```
P(X > 13 | X > 10) = P(X > 3) = q³ = (5/6)³ = 125/216 ≈ 0.5787
```
The 10 failed rolls are completely irrelevant!

### Example 5 — Quality Control
> A factory produces items, each independently defective with probability 0.1. Items are tested one by one. Find the probability that the **first defective item is found among the first 5 tested**.

`X ~ Geo(0.1)`, `q = 0.9`
```
P(X ≤ 5) = 1 − (0.9)⁵ = 1 − 0.59049 ≈ 0.4095
```

---

## 25. Common Mistakes — Geometric

| ❌ Mistake | ✅ Correction |
|---|---|
| Mixing up the two conventions | Always state: "X = number of *trials*" (support {1,2,…}) or "Y = number of *failures*" (support {0,1,…}) |
| **Gambler's Fallacy** — "I've had 10 failures, so success is more likely now" | The memoryless property says the past is irrelevant; each trial is independent |
| CDF off-by-one: using `1 − qᵏ` for Convention 2 | Convention 2 CDF is `1 − q^{k+1}`, not `1 − qᵏ` |
| MGF domain error: using M(t) for all t | MGF only valid for `t < −ln(q)`; diverges otherwise |
| Using Var(X) = 1/p² | Var(X) = **(1−p)/p²**, not 1/p² |
| Forgetting that Geometric is the *only* discrete memoryless distribution | This is a theorem, not just a property — it uniquely characterises the Geometric |

---

---

# PART III: COMPARISON & CONNECTIONS

---

## 26. Side-by-Side Summary

| Property | Poisson(λ) | Geometric(p) — Conv. 1 |
|---|---|---|
| **Type** | Count of events | Trials until first success |
| **Support** | {0, 1, 2, …} | {1, 2, 3, …} |
| **PMF** | `λᵏ e^{−λ} / k!` | `(1−p)^{k−1} p` |
| **Mean** | λ | 1/p |
| **Variance** | λ | (1−p)/p² |
| **MGF** | `exp(λ(eᵗ−1))` | `peᵗ / (1−qeᵗ)` |
| **PGF** | `exp(λ(z−1))` | `pz / (1−qz)` |
| **Memoryless?** | ✗ | ✓ |
| **Continuous analogue** | Poisson process / Gamma | Exponential |
| **Additive property** | Poi(λ₁)+Poi(λ₂) = Poi(λ₁+λ₂) | Sum of r Geo(p) = NB(r,p) |

---

## 27. When to Use Each Distribution

| Scenario | Distribution |
|---|---|
| Counting rare events in a fixed interval | Poisson |
| Number of trials until first success | Geometric |
| Modelling overdispersed count data | Negative Binomial |
| Waiting time between Poisson events | Exponential |
| Waiting time until k-th Poisson event | Gamma |
| Large n, small p, fixed np | Poisson ≈ Binomial |

---

## 28. Self-Assessment Checklist

- [ ] I can write down the PMF of Poi(λ) and Geo(p) from memory
- [ ] I can prove E[X] = λ for Poisson using the series re-indexing trick
- [ ] I can prove Var(X) = λ for Poisson using E[X(X−1)]
- [ ] I can derive the Poisson as a limit of the Binomial
- [ ] I can prove the additive property of Poisson using MGFs
- [ ] I can state both conventions for the Geometric and relate them
- [ ] I can prove E[X] = 1/p for Geometric using the derivative trick
- [ ] I can prove Var(X) = (1−p)/p² for Geometric
- [ ] I can state and prove the memoryless property of the Geometric
- [ ] I can explain why Geometric is the *only* discrete memoryless distribution
- [ ] I can correctly apply the CDF for both conventions without off-by-one errors
- [ ] I can identify the continuous analogues of both distributions

---

## 29. Learning Path

### Phase 1: Foundations (Day 1)
- Learn both PMFs and verify they sum to 1
- Compute means and variances for simple examples
- Practice: tabulate P(X = k) for Poi(3) and Geo(0.25) for k = 0, …, 6

### Phase 2: Proofs (Days 2–3)
- Prove E[X] and Var(X) for both distributions from scratch
- Derive both MGFs
- Prove the Poisson Limit Theorem
- Prove the memoryless property and its uniqueness

### Phase 3: Applications & Connections (Days 4–5)
- Practice rescaling λ for different intervals (Poisson)
- Apply the memoryless property to conditional probability problems
- Use Cayley–Hamilton to compute matrix inverses (cross-topic!)
- Solve past exam problems on both distributions

---

*Sources: Standard university probability theory; web research (no lecture notes available for this topic in the current collection).*
