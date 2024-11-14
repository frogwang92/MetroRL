# MetroRL

MetroRL is a Python-based application for visualizing and simulating metro systems. It uses PyQt5 for the graphical user interface and provides tools for building and interacting with metro topologies.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/MetroRL.git
    ```
2. Navigate to the project directory:
    ```sh
    cd MetroRL
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

To run the application, execute the following command:
```sh
python gui.py
```

## Project Structure

```
MetroRL/
├── buildtopology.py
├── facility/
│   ├── platform.py
│   └── switch.py
├── gui.py
├── linedata.py
├── README.md
├── requirements.txt
├── topology/
│   ├── edge.py
│   └── node.py
└── tr/
    └── linesegment.py
```

- **buildtopology.py**: Contains functions to build the metro topology from platforms and line segments.
- **facility/**: Contains classes representing different facilities in the metro system, such as platforms and switches.
- **gui.py**: Contains the main GUI application code.
- **linedata.py**: Contains sample data for platforms and line segments.
- **topology/**: Contains classes representing the topology of the metro system, such as nodes and edges.
- **tr/**: Contains classes representing the transit routes, such as line segments.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.