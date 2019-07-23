################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         calibrateS21.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files
from networkAnalyzer import NetworkAnalyzer
from functions import *
from process import CalCalFactor
# Standard libraries
import sys
import logging
from datetime import datetime

# Installed libraries

# Global variables
db = None
mycursor = None
analyzer = None


# ==============================================================================
# S11 calibration routine
#
def run_s21_calibration(log, f1, f2, nums):
    log.info("Starting S21 calibration")

    # --------------------------------------------------------------------------
    # Load state
    #
    log.info("Loading state")
    analyzer.load_state()
    #
    # End load state
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set parameters
    #
    channel = 1
    trace = 1
    log.info("Setting parameters")
    analyzer.setup(channel, trace)
    analyzer.get_errors()

    # Set start frequency
    start = float(analyzer.set_start(channel, f1))
    if f1 != start:
        msg = "WARNING: Invalid start frequency, using " + str(start)
        print(msg)
        log.warning(msg)
        # f1_old = f1
        f1 = start

    # Set stop frequency
    stop = float(analyzer.set_stop(channel, f2))
    if f2 != stop:
        msg = "WARNING: Invalid stop frequency, using " + str(stop)
        print(msg)
        log.warning(msg)
        # f2_old = f2
        f2 = stop

    # Set number of points
    points = int(analyzer.set_points(channel, nums))
    if nums != points:
        msg = "WARNING: Invalid number of steps, using " + str(points)
        print(msg)
        log.warning(msg)
        # nums_old = nums
        nums = points

    # Update SQL database
    if db.is_connected():
        fstart = f1 / 1e9
        fstop = f2 / 1e9
        rowcount = mycursor.rowcount

        log.info("Updating fstart, fstop, and nums in sql database")
        update_config_db(log, mycursor, fstart, "'frequency_start'")
        update_config_db(log, mycursor, fstop, "'frequency_stop'")
        update_config_db(log, mycursor, nums, "'num_steps'")

        log.info("Committing changes")
        db.commit()
        if rowcount == mycursor.rowcount:
            log.warning("Failed to store updated data")
    #
    # End set parameters
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for network analyzer errors
    log.info("Checking network analyzer error queue")
    err_nums, err_msgs = analyzer.get_errors()
    if len(err_nums) > 0:
        msg = "Error in setting network analyzer parameters"
        print(msg)
        log.warning(msg)
    else:
        # No errors
        log.info("No network analyzer errors detected")
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Calibrate
    #
    log.info("Measuring S21")
    print("Starting S21 Calibration")
    print("Start Frequency: " + str(f1/1e9) + " GHz")
    print("Stop Frequency: " + str(f2/1e9) + " GHz")
    print("Number of Points: " + str(nums))
    a = 2
    b = 1
    analyzer.set_measurement(channel, trace, a, b)
    analyzer.trigger()
    analyzer.auto_scale(channel, trace)
    freq = analyzer.get_x(channel)
    s21Data = analyzer.get_corr_data(channel)
    # s21Data = analyzer.get_form_data(channel)
    filename = os.path.join(DATA_PATH, "s21Calibration.csv")
    s21File = open(filename, "w")
    s21File.write(freq)
    s21File.write(s21Data)
    s21File.close()

    CalCalFactor()
    log.info("S21 calibration complete")
    #
    # End calibrate
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for network analyzer errors
    log.info("Checking network analyzer error queue")
    err_nums, err_msgs = analyzer.get_errors()
    if len(err_nums) > 0:
        msg = "Error calibrating network analyzer s21"
        print(msg)
        log.warning(msg)
    else:
        # No errors
        msg = "S21 Calibration Successful"
        print(msg)
        log.info(msg)
    #
    # --------------------------------------------------------------------------


#
# End calibration routine
# ==============================================================================


# ==============================================================================
# Main function
#
def calibrate_s21(args):
    # --------------------------------------------------------------------------
    # Initialize parameters
    #
    rv = 0  # Error flag
    #
    # End initialize parameters
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set up log file
    #
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("calibrateS21")  # Get local logger
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
    visa_log = logging.getLogger('pyvisa')
    visa_log.setLevel(IMPORT_LOG_LEVEL)
    visa_log.addHandler(handler)
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
        if len(args) < 3:
            nums = int(801)
        else:
            nums = int(args[2])
    except ValueError:
        msg = "Error: Could not parse command line arguments " + str(args)
        print(msg)
        log.exception(msg)
        return 1
    except IndexError:
        msg = "Error: Invalid number of command line arguments. " \
              + "Expected 3, received " + str(len(args))
        print(msg)
        log.exception(msg)
        return 1
    #
    # End parse CL arguments
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Attempt calibration
    #
    try:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Open network analyzer
        #
        global analyzer
        log.info("Attempting connection to network analyzer")
        analyzer = NetworkAnalyzer()
        log.info("Successfully connected to network analyzer")

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
        # Run calibration routine
        #
        run_s21_calibration(log, f1, f2, nums)
        log.info("S21 calibration complete")

    except BaseException as e:
        # print("Error calibrating S21. Check log file for details.")
        print(e)
        log.exception("Error from calibrateS21:")
        rv = 1
    finally:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close vna connection
        #
        if analyzer:
            log.info("Closing network analyzer")
            analyzer.close()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close database connection
        #
        if db:
            if db.is_connected():
                log.info("Closing database connection")
                db.close()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Return error flag (0 if no error, 1 if error)
        #
        return rv
    #
    # End calibration
    # --------------------------------------------------------------------------


#
# End main
# ==============================================================================


# ==============================================================================
# Enter from command line
#
if __name__ == "__main__":
    argv = sys.argv  # Store command line arguments
    argv.pop(0)  # Remove file name
    # Call main function and pass return status to system
    sys.exit(calibrate_s21(argv))
#
# End enter from command line
# ==============================================================================
