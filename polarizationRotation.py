################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         polarizationRotation.py
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
# Test routine
#
def sweep(log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar):
    # --------------------------------------------------------------------------
    # Reset motor positions
    #
    print("Motor Setup Complete")
    print("Test Antenna Polarization: " + str(tpolar))
    print("Chamber Antenna Polarization: " + str(cpolar))
    motorSet[STAND_ROTATION].goto_zero()
    # if spos: # Stand translation
    #     motorSet[S_TRANSLATION].rot_deg(STAND_OFFSET)
    set_polarization(log, motorSet, tpolar, cpolar, mycursor)
    #
    # End reset motor positions
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Update database
    #
    if db.is_connected():
        rowcount = mycursor.rowcount

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Antenna polarization
        #
        log.info("Updating tpolar and cpolar in sql database")
        update_config_db(log, mycursor, tpolar, "'antenna_polarization'")
        update_config_db(log, mycursor, cpolar, "'chamber_polarization'")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Commit changes
        log.info("Committing changes")
        db.commit()
        if rowcount == mycursor.rowcount:
            log.warning("Failed to store updated antenna polarization data")
            print("Failed to record new polarization positions")
        else:
            print("Recorded new polarization positions")

    #
    # End update database
    # --------------------------------------------------------------------------


#
# End test routine
# ==============================================================================


# ==============================================================================
# Main function
#
def polarization_rotation(args):
    rv = 0  # Initialize return value

    # --------------------------------------------------------------------------
    # Set up log file
    #
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("polarizationRotation")  # Get local logger
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
    sql_log = logging.getLogger('mysql.connector')
    sql_log.setLevel(IMPORT_LOG_LEVEL)
    sql_log.addHandler(handler)
    log.info("")
    log.info("")
    #
    # End log setup
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Parse CL arguments
    #
    try:
        f1 = float(args[0]) * 1e9
        f2 = float(args[1]) * 1e9
        nums = int(args[2])
        rstart = float(args[3])
        angle = float(args[4])
        rstop = float(args[5])
        tpolar = float(args[6])
        cpolar = float(args[7])
    except ValueError:
        msg = "ERROR: Could not parse command line arguments " + str(args)
        print(msg)
        log.exception(msg)
        return 1
    except IndexError:
        log.exception(
                "ERROR: Invalid number of command line arguments. "
                "Expected 8, Received " + str(len(args)))
        return 1
    #
    # End parse CL arguments
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Validate parameters
    #
    (f1, f2, nums, rstart, angle, rstop, tpolar, cpolar) = validate_parameters(
            log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar)
    #
    # End validate parameters
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Attempt test
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
        # Run test routine
        #
        sweep(log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar)

    #
    # End attempt alignment
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Handle exceptions/errors
    #
    except BaseException as e:
        # log exception
        print(e)
        log.exception('Error from runTest.main():')
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
    argv = sys.argv  # Store command line arguments
    argv.pop(0)  # Remove file name
    # Call main function and pass return status to system
    sys.exit(polarization_rotation(argv))
#
# End enter from command line
# ==============================================================================
