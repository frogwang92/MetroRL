"""
Metro System Simulation

This program simulates a metro system with two operation modes:
- Self-rolling mode: Trains operate on fixed schedules
- Delegated mode: Train operations are controlled by a central dispatcher

The simulation can run with or without a GUI interface.

Command line arguments:
    --nogui: Run without GUI (default: False)
    --mode: Operation mode, either 'self_rolling' or 'delegated' (default: 'self_rolling')

Example usage:
    python main.py  # Run with GUI in self-rolling mode
    python main.py --nogui  # Run without GUI
    python main.py --mode delegated  # Run in delegated mode
"""

import sys
from environment import Environment, Mode
from gui import MetroWindow, QApplication
import time
from PyQt6.QtCore import QTimer
from config import Config

def run_with_gui(env):
    """Run simulation with GUI"""
    app = QApplication(sys.argv)
    window = MetroWindow(env)
    window.show()
    
    # Start simulation loop
    timer = QTimer()
    timer.timeout.connect(env.step)
    timer.start(1000)  # 1 second intervals
    
    return app.exec()

def run_without_gui(env):
    """Run simulation without GUI"""
    env.start()
    try:
        while True:
            env.step()
            time.sleep(1)  # 1 second intervals
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    finally:
        env.reset()

def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Metro System Simulation')
    parser.add_argument('--nogui', action='store_true', help='Run without GUI')
    parser.add_argument('--mode', choices=['self_rolling', 'delegated'], 
                       default='self_rolling', help='Operation mode')
    args = parser.parse_args()
    
    # Create environment
    env = Environment(config=Config())
    env.mode = Mode.SELFROLLING if args.mode == 'self_rolling' else Mode.DELEGATED
    
    # Add initial trains
    env.add_train(1)  # Add train at node 1 (d1)
    env.add_train(8)  # Add train at node 8 (d2)
    
    # Run simulation
    if args.nogui:
        run_without_gui(env)
    else:
        return run_with_gui(env)

if __name__ == "__main__":
    sys.exit(main())
