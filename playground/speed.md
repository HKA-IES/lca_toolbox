# Analysis of computation speed
speed.py profiles the function run_monte_carlo.

## Results

- speed.py x1 : 89827 / 8 ms
  - run_monte_carlo x1 : 84463 / 1793 ms
    - calculate_scores x10 : 82454 / 503 ms
      - recalculate x10 : 12004 / 8 ms / 15 %
      - lcia x10 : 18075 / 0 ms / 22 %
      - lci x10 : 40491 / 0 ms / 48%
        - load_lci_data x10 : 8431 / 23 ms
        - lci_calculation x10 : 31702 / 11 ms
          - spsolve x10 : 22378 / 0 ms
          - __matmul__ x10 : 16948 / 0 ms