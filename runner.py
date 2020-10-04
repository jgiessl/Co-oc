
from program_gui import *
import time


def main():
    gui = GUI()
    while gui.loop_flag:
        gui.changed_update()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
