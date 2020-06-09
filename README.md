# Growth rate and growth acceleration COVID-19

## Description

Growth rate and growth acceleration calculation using COVID-19 data.

## Prerequisites
- [python](https://www.python.org/) >= 3.6
- [numpy](https://www.numpy.org/)
- [matplotlib](https://matplotlib.org/)
- [pandas](https://pandas.pydata.org/)
- [requests](https://pypi.org/project/requests/)
- [argparse](https://docs.python.org/3/howto/argparse.html)
- [os](https://docs.python.org/3/library/os.html)

Typically, [Anaconda](https://www.anaconda.com/distribution/) distribution for Python >= 3.6 is enough. 

## Usage

### Notebooks

The notebooks present in iterative and detailed calculation of growth rate, growth acceleration and growth acceleration rate for COVID-19 cases evolution.

- `growth_BR_states.ipynb`: Brazilian states
- `growth_BR_cities.ipynb`: Brazilian cities
- `growth_US_states.ipynb`: US states
- `growth_world.ipynb`: World countries.

Results: CSV files in `results_dfs`


### Script

Script `growth.py`.


## Data sources: 
- [Brasil.IO](https://brasil.io/dataset/covid19/caso).
- [Our World in Data](https://ourworldindata.org/coronavirus).
- [The New York Times](https://github.com/nytimes/covid-19-data).

Directory: `data`.

## References:
- [Growth Rate and Acceleration Analysis of the COVID-19 Pandemic Reveals the Effect of Public Health Measures in Real Time](https://www.frontiersin.org/articles/10.3389/fmed.2020.00247/full#h6).
