# Piecewise Linear Interpolation

## Definition
Piecewise linear interpolation is a method of constructing new data points within the range of a discrete set of known data points. It connects each pair of adjacent points with a straight line, creating a piecewise linear function.

## Formula
Given a set of points 
\[(x_0, y_0), (x_1, y_1), \ldots, (x_n, y_n)\], the linear interpolation between two points \((x_i, y_i)\) and \((x_{i+1}, y_{i+1})\) is given by:

\[y = y_i + \frac{(y_{i+1} - y_i)}{(x_{i+1} - x_i)}(x - x_i)\]

for \(x_i \leq x \leq x_{i+1}\).

## Steps for Piecewise Linear Interpolation
1. **Identify the Interval**: Determine the interval \([x_i, x_{i+1}]\) that contains the value of \(x\) for which you want to interpolate.
2. **Apply the Formula**: Use the formula to calculate the interpolated value of \(y\).
3. **Repeat**: If necessary, repeat the process for other intervals or points.

## Example
Consider the points \((1, 2), (2, 3), (3, 5)\). To find the interpolated value at \(x = 2.5\):  
- Identify the interval: \((2, 3)\)  
- Apply the formula:  
  \[y = 3 + \frac{(5 - 3)}{(3 - 2)}(2.5 - 2) = 3 + 2(0.5) = 4\]  
Thus, the interpolated value at \(x = 2.5\) is \(y = 4\).

## Applications
- **Computer Graphics**: Used for rendering curves and surfaces.
- **Data Analysis**: Filling in missing data points in datasets.
- **Engineering**: Used in various engineering fields for modeling and simulations.

## Advantages
- Simple to implement and understand.
- Provides a good approximation for linear data.

## Disadvantages
- Can produce inaccurate results for non-linear data.
- The method may not be smooth at the points of interpolation.