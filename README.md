# lcatoolbox

![Python](https://img.shields.io/badge/python-3.12|3.13-blue.svg)

A package that builds on top of the brightway framework to perform Life Cycle Assessment. Specifically, this package 
enables taking into consideration the uncertainty of both foreground and background processes in an LCA model. These
uncertainties can be characterised using an uncertainty analysis, and the contribution of each input factor to the 
overall uncertainty can be analysed using uncertainty apportioning.

This package was introduced at Brightcon 2026.

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
pip install git+https://github.com/HKA-IES/lca_toolbox
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
