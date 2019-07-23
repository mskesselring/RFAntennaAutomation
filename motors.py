################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         motors.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files
from serverInfo import *
# Standard libraries
import numpy
import logging
from datetime import datetime


# Installed libraries


# ==============================================================================
# Motor class
#
class Motor(object):

    # --------------------------------------------------------------------------
    # Initialize object
    #
    def __init__(self, mc, port_num, model, increment, advance):
        if (port_num < 1) or (port_num > 4):
            raise ValueError
        self.mc = mc
        self.portNum = port_num
        self.model = model
        self.increment = increment  # degrees per step
        self.advance = advance  # degrees per turn
        # Set up error log
        logging.basicConfig(level=logging.DEBUG)
        self.log = logging.getLogger(__name__)
        if not self.log.handlers:
            handler = logging.FileHandler(
                    'log_' + datetime.today().strftime('%m_%Y') + '.log')
            handler.setLevel(LOG_LEVEL)
            formatter = logging.Formatter(
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
            self.log.setLevel(LOG_LEVEL)
            self.requestsLog = logging.getLogger('pyvisa')
            self.requestsLog.setLevel(IMPORT_LOG_LEVEL)
            self.requestsLog.addHandler(handler)

    #
    # End init
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Send a command that requires the receipt of a "^" before proceeding
    #
    def send_complex_command(self, command):
        self.log.debug("Sending " + command + " to motor " + str(self.portNum))

        # Change read termination character to '^'
        self.mc.read_termination = '^'
        # Send command and wait for "^" character
        self.mc.query(command)
        # Change read termination character back to carriage return
        self.mc.read_termination = '\r'

        # Clear program
        self.mc.write("C")

    #
    # End send_complex_command
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Send a simple operation command (run immediately when received)
    #
    def send_simple_command(self, command):
        self.log.debug("Sending " + command + " to motor " + str(self.portNum))
        self.mc.write(command)

    #
    # End send_simple_command
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Send a command to get the location of one or more motors
    # Receives motor index from the controller
    #
    def send_location_command(self, command):
        self.log.debug("Sending " + command + " to motor " + str(self.portNum))

        # Read location and convert index to angle
        location = float(self.mc.query(command)) * (-self.increment)

        return location

    #
    # End send_location_command
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Verify controller status
    #
    def verify_status(self):
        self.log.debug("V")
        # Read status
        status = self.mc.query("V")
        return status

    #
    # End verify_status
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Start On-Line mode
    #
    def start_online(self):
        self.send_simple_command("F")

    #
    # End start_online
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Stop On-Line mode
    #
    def quit_online(self):
        self.send_simple_command("Q")

    #
    # End quit_online
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Clear commands
    #
    def clear_cmd(self):
        self.send_simple_command("C")

    #
    # End clear_cmd
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set absolute zero position of all motors
    #
    def set_all_zero(self):
        self.send_simple_command("N")

    #
    # End set_all_zero
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get current position of motor
    #
    def get_position(self):
        if self.portNum == 1:
            command = "X"
        elif self.portNum == 2:
            command = "Y"
        elif self.portNum == 3:
            command = "Z"
        elif self.portNum == 4:
            command = "T"
        else:
            raise ValueError()

        return self.send_location_command(command)

    #
    # End get_position
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set speed of motor (steps/sec)
    #
    def set_speed(self, speed=2500):
        if (speed < 1) or (speed > 6000):
            raise ValueError()

        command = "S" + str(self.portNum) + "M" + str(int(speed))
        self.send_simple_command(command)

    #
    # End set_speed
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set acceleration of motor (steps/sec)
    #
    def set_acceleration(self, acceleration=1):
        if (acceleration < 1) or (acceleration > 127):
            raise ValueError()

        command = "A" + str(self.portNum) + "M" + str(int(acceleration))
        self.send_simple_command(command)

    #
    # End set_acceleration
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set absolute zero for selected motor
    #
    def set_zero(self):
        command = "IA" + str(self.portNum) + "M-0"
        self.send_simple_command(command)

    #
    # End set_zero
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Move motor to absolute zero index
    #
    def goto_zero(self):
        command = "IA" + str(self.portNum) + "M0,R"
        self.send_complex_command(command)

    #
    # End goto_zero
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Move motor to positive limit switch
    #
    def goto_positive(self):
        command = "I" + str(self.portNum) + "M0,R"
        self.send_complex_command(command)

    #
    # End goto_positive
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Move motor to negative limit switch
    #
    def goto_negative(self):
        command = "I" + str(self.portNum) + "M-0,R"
        self.send_complex_command(command)

    #
    # End goto_negative
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Rotate the specified number of degrees
    #
    def rot_deg(self, degrees):
        # steps = negative (degrees) divided by (degrees per step)
        steps = -numpy.round(degrees / self.increment)
        self.rot_steps(steps)

    #
    # End rot_deg
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Rotate the specified number of steps
    #
    def rot_steps(self, steps):
        # If number of steps is too large
        if abs(steps) > 16777215:
            raise ValueError()
        # If number of steps is non-zero
        if steps != 0:
            command = "I" + str(self.portNum) + "M" + str(int(steps)) + ",R"
            self.send_complex_command(command)

    #
    # End rot_steps
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # String representation of motor class
    #
    def __str__(self):
        return "%s on port %d with degree increment per step %f and advance " \
               "per turn %f" % (
                   self.model, self.portNum, self.increment, self.advance)
    #
    # End str
    # --------------------------------------------------------------------------


#
# End Motor
# ==============================================================================


# ==============================================================================
# B5990 Motor subclass
#
class B5990(Motor):
    increment = 0.01
    advance = 4
    model = "B5990"

    # --------------------------------------------------------------------------
    # Initialize b5990 motor object
    #
    def __init__(self, ser, port_num):
        Motor.__init__(self, ser, port_num, self.model, self.increment,
                       self.advance)
    #
    # End init
    # --------------------------------------------------------------------------


#
# End B5990
# ==============================================================================


# ==============================================================================
# B4836 Motor subclass
#
class B4836(Motor):
    increment = 0.025
    advance = 10
    model = "B4836"

    # --------------------------------------------------------------------------
    # Initialize b4836 motor object
    #
    def __init__(self, ser, port_num):
        Motor.__init__(self, ser, port_num, self.model, self.increment,
                       self.advance)
    #
    # End init
    # --------------------------------------------------------------------------
#
# End B4836
# ==============================================================================
