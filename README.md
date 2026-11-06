# LAGUNA: Leveraging AGgregated rankings from Uncertainty Apportioning to accelerate life cycle inventory data collection

![Python](https://img.shields.io/badge/python-3.12|3.13-blue.svg)

This package implements the LAGUNA method, which leverages uncertainty apportioning to accelerate life cycle inventory 
data collection. Specifically, a foreground database is defined in a spreadhsheet and imported using the package. Then, 
an uncertainty apportioning and a discernibility analysis are conducted to determine which input factors contribute most
to the indiscernibility of the life cycle assessment. Since input factors are ranked distinctly for each impact 
category, we aggregated the rankings based on the discernibility of each impact category. This yields a single ranking
which can be used to determine which input factors to refine in priority.

This package is introduced in a scientific article currently being reviewed.

## Requirements
- Python 3.12, 3.13
- brightway25
- numpy
- pyexcel
- pandas
- SALib
- xgboost
- shap

## Install it from the repository

```
pip install git+https://github.com/HKA-IES/laguna_lca
```

## Usage
Examples will be added shortly.

## Development
Please note that the goal of this package is not to offer a general framework 
for LCA. It was built around the needs of Jonathan Larochelle for his dissertation and is designed
for this specific use-case.

Please do not hesitate to submit issues if you have found bugs or if the
documentation is unclear.

## License
This project is licensed under the MIT License.
