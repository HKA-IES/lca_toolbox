# Analysis of computation speed
speed.py profiles the function run_monte_carlo.

## Results

- speed.py x1 : 104833 / 6 ms
  - run_monte_carlo x1 : 70970 / 1173 ms
    - calculate_scores x10 : 69637 / 206 ms
      - recalculate_exchanges x22 : 14759 / 38 ms
        - Note: appears to be run twice, one directly and one per recalculate.
      - recalculate x10 : 9295 / 5 ms
      - peewee.get x3938 : 6821 / 51 ms
      - lcia x10 : 11983 / 0 ms
      - lci x10 : 32684 / 0 ms