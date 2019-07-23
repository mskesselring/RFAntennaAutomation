################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         alignMotors.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files
from functions import *
# Standard libraries
import sys
import logging
from datetime import datetime

# Installed libraries

motorSet = []  # Motor controller, contains motor objects
mc = None

db = None
mycursor = None


# ==============================================================================
# Alignment
#
def run_alignment(log):
    # --------------------------------------------------------------------------
    # Reset motor positions to zero index
    #
    for m in motorSet:
        m.goto_zero()
    #
    # End reset motor positions
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Alignment loop: select motor, adjust position, repeat
    #
    while True:

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Select motor
        #
        while True:
            try:
                print("Motor Numbers:")
                print("1: Stand Rotation")
                print("2: Stand Translation")
                print("3: Test Antenna Polarization")
                print("4: Chamber Antenna Polarization")
                selected = int(input("Input motor number (x to cancel):"))

                # Check for valid range
                if (selected > 4) or (selected < 1):
                    print("Motor number must be integer in range [1 : 4]")
                else:
                    log.info("Selected motor: " + str(selected))
                    break

            # Exit if not an integer number
            except ValueError:
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # Reset motor positions to zero index
                #
                for m in motorSet:
                    m.goto_zero()

                return

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Adjust position
        #
        while True:
            try:
                # Amount to rotate
                val = int(input(
                        "Enter rotation angle as integer (x to set absolute "
                        "zero):"))

                # Validate input and move motor
                if abs(val) >= 360:
                    print("Angle must be integer in range [-359 : 359]")
                else:
                    log.info("Rotating motor " + str(selected) + " by " + str(
                            val) + " degrees")
                    motorSet[selected - 1].rot_deg(val)

            # If input was not an integer, set zero index position
            except ValueError:
                log.info("Setting absolute zero position for motor " + str(
                        selected - 1))
                motorSet[selected - 1].set_zero()
                motorSet[0].set_all_zero()
                pos = motorSet[selected - 1].get_position()
                log.info("Motor " + str(selected) + " position: " + str(pos))
                break

    #
    # End alignment loop
    # --------------------------------------------------------------------------


#
# End alignment
# ==============================================================================


# ==============================================================================
# Main function
#
def align_motors(argv):
    rv = 0  # Initialize return value

    # --------------------------------------------------------------------------
    # Set up log file
    #
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("alignMotors.py")  # Get local logger
    # Create and format handler to write to file "log_[MONTH]_[YEAR].log"
    handler = logging.FileHandler(
            'log_' + datetime.today().strftime('%m_%Y') + '.log')
    handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    # Add handler to logger and specify properties
    log.addHandler(handler)
    log.setLevel(LOG_LEVEL)
    # Get logger for pyvisa module and set level to log warnings and errors
    requests_log = logging.getLogger('pyvisa')
    requests_log.setLevel(IMPORT_LOG_LEVEL)
    requests_log.addHandler(handler)
    log.info("")
    log.info("")
    #
    # End log setup
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for command line arguments
    #
    if len(argv) > 0:
        log.warning("WARNING: Command line arguments will be ignored. "
                    + "Expected 0, received " + str(len(argv)) + ": "
                    + str(argv))
    #
    # End check for command line arguments

    # --------------------------------------------------------------------------
    # Attempt alignment
    #
    try:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Open motor controller
        global mc
        mc = motor_control_init(log)
        # If mc object is empty
        if not mc:
            raise IOError('Opening motor controller failed')
        else:
            log.info("Motor controller " + str(mc) + " opened")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Connect to database
        #
        global db, mycursor
        log.info("Attempting connection to database")
        db, mycursor = db_init()
        if db.is_connected():
            log.info("Successfully connected to database")
        else:
            raise Exception("Failed to connect to database")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Initialize motors
        #
        global motorSet
        log.info("Initializing motors")
        motorSet = motors_init(mc)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Run alignment routine
        #
        run_alignment(log)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Update database
        #
        if db.is_connected():
            rowcount = mycursor.rowcount

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Antenna polarization
            #
            log.info("Updating tpolar and cpolar in sql database")
            update_config_db(log, mycursor, 0, "'antenna_polarization'")
            update_config_db(log, mycursor, 0, "'chamber_polarization'")

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Commit changes
            db.commit()
            if rowcount == mycursor.rowcount:
                log.warning("Failed to store updated antenna polarization data")

    #
    # End attempt alignment
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Handle exceptions/errors
    #
    except BaseException:
        # log exception
        log.exception('Error from alignMotors.main():')
        # Set return value to 1 (error)
        rv = 1
    #
    # End handle exceptions/errors
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Close instruments and return (always executed with or without
    # exceptions/errors)
    #
    finally:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close motor controller
        #
        if mc:
            log.info("Closing motor controller " + str(mc))
            # stop interactive mode (motor number does not matter)
            motorSet[M1].quit_online()
            mc.close()
        #
        # End close motor controller
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close database connection
        #
        if db:
            if db.is_connected():
                log.info("Closing database connection")
                db.close()

        return rv  # Return 1 if error, 0 else
    #
    # End close instruments and return
    # --------------------------------------------------------------------------


#
# End main function
# ==============================================================================


# ==============================================================================
# Enter from command line
#
if __name__ == "__main__":
    args = sys.argv  # Store command line arguments
    args.pop(0)  # Remove file name
    # Call main function and pass return status to system
    sys.exit(align_motors(args))
#
# End enter from command line
# ==============================================================================
