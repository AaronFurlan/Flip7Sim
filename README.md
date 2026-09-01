# Flip7Sim

A Python simulation of the card game **Flip 7** with interchangeable decision-making agents.

## Current features

- Complete Flip 7 deck and scoring
- Number, modifier, and action cards
- Freeze, Flip Three, and Second Chance
- Multi-round games with winner detection
- Algorithm-independent agent interface
- Reproducible Random-vs-Random simulations
- Automated tests with pytest

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pytest
```

## Run a simulation
```powershell
python main.py
```

## Run tests
```powershell
python -m pytest -v
```