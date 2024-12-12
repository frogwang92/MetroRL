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
from logger import logger, setup_logger

def run_with_gui(env):
    """Run simulation with GUI"""
    app = QApplication(sys.argv)
    window = MetroWindow(env)
    window.show()
    
    return app.exec()

def run_without_gui(env):
    """Run simulation without GUI"""
    env.start()
    try:
        while True:
            env.step()
            time.sleep(1)  # 1 second intervals
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user")
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
    logger.info("Starting Metro System Simulation")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"GUI: {'Disabled' if args.nogui else 'Enabled'}")
    # Create environment
    env = Environment(config=Config())
    logger.info("Environment created")

    # Add initial trains
    import testcaseutils
    platforms = testcaseutils.random_train_generator(env, 12)
    for platform in platforms:
        env.add_train(platform.id)
    logger.info("Initial trains added")
    
    # Run simulation
    if args.nogui:
        logger.info("Running simulation without GUI")
        run_without_gui(env)
    else:
        logger.info("Running simulation with GUI")
        return run_with_gui(env)

if __name__ == "__main__":
    sys.exit(main())
