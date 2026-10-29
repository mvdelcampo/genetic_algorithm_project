# Genetic Algorithm Project
Command-line tool that solves OneMax and Traveling Salesman (TSP) problems with a genetic algorithm. Problems are described in JSON files, expanded into independent runs (including hyperparameter grids), and solved in parallel across several CPU cores.

Capstone project (Advanced track) for the course *Programming Tools for Data Science and Artificial Intelligence*, 

## Requirements
```bash
pip install -r requirements.txt
```

##  Repository organization
The repository follows this structure:

```text
├── README.md
├── cli.py
├── json_loader.py
├── functions.py
├── utils.py
├── input/
└── output/
```

#### File roles
- `cli.py` — menu and the six options
- `json_loader.py` — reads, validates and expands the JSON file into runs
- `utils.py` — input validation helpers, file writing and plotting
- `functions.py`- genetic algorithm engine and worker for parallel runs


## How it works
The session state (runs, number of cores, output settings, total time) is a single dictionary created in `cli_menu` and passed to every menu option so no global variables are used. 

The menu has six options to choose from: load a problem, adjust the number of cores, run the algorithm, check status, export results and quit the program.


## Novel features
 - **Elitism**: Copies the best individuals of each generation unchanged into the next one so the best solution is never lost.

 - **Two-opt**: For TSP, reverses a segment of a route when that makes it shorter, removing crossing paths