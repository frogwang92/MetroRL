# MetroRL

MetroRL is a Python-based metro system simulation and visualization tool. It provides a platform for experimenting with different train control strategies in both autonomous and delegated operation modes.

## Features

- **Dual Operation Modes**
  - Self-rolling: Trains operate autonomously based on predefined policies
  - Delegated: Train movements are controlled by external commands

- **Interactive Visualization**
  - Real-time visualization of train movements
  - Interactive topology graph with zoom and pan capabilities
  - Timeline view for schedule visualization

- **Flexible Topology**
  - Support for complex metro network layouts
  - Customizable platform and line segment properties
  - Automatic layout calculation using NetworkX

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/frogwang92/MetroRL.git
    ```
2. Navigate to the project directory:
    ```sh
    cd MetroRL
    ```
3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

Run the simulation with GUI (default):
```sh
python main.py
```

Run without GUI in self-rolling mode:
```sh
python main.py --nogui
```

Run with delegated control mode:
```sh
python main.py --mode delegated
```

## Project Structure

```
MetroRL/
├── main.py              # Entry point and simulation runner
├── environment.py       # Core simulation environment
├── gui.py              # GUI implementation
├── buildtopology.py    # Network topology builder
├── facility/           # Metro facility components
├── topology/           # Network topology components
├── tr/                 # Transit route components
└── policies/           # Train control policies
```

### Key Components

- **Environment**: Central simulation manager handling train movements and state
- **TrainController**: Manages train creation, removal, and movement
- **GUI**: Interactive visualization using PyQt6
- **Policies**: Pluggable train control strategies

## Dependencies

- PyQt6: GUI framework
- NetworkX: Graph layout and topology management

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:

- New train control policies
- UI improvements
- Bug fixes
- Documentation improvements

## License

This project is licensed under the MIT License. See the LICENSE file for details.