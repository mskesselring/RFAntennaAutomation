################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         maxGain.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files
from networkAnalyzer import NetworkAnalyzer
from functions import *
from process import S21Normalize
from plotting import Plotting
# Standard libraries
import sys
import logging
from datetime import datetime

# Installed libraries


motorSet = []  # Motor controller, contains motor objects
mc = None

db = None
mycursor = None

analyzer = None

spos_default = True


# ==============================================================================
# Test routine
#
def sweep_maxGain(log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar,
                  spos=spos_default):
    # --------------------------------------------------------------------------
    # Reset motor positions
    #
    motorSet[STAND_ROTATION].goto_zero()
    if spos: # Stand translation
        motorSet[S_TRANSLATION].rot_deg(STAND_OFFSET)
    set_polarization(log, motorSet, tpolar, cpolar, mycursor)
    #
    # End reset motor positions
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Move test antenna to start degree position
    #
    log.info("Start Position: " + str(rstart))
    motorSet[M1].rot_deg(rstart)
    log.info("Motor setup complete")
    #
    # End move test antenna to start position
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Load state
    #
    analyzer.load_state()
    #
    # End load state
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set network analyzer parameters
    #
    channel = 1
    trace = 1
    analyzer.setup(channel, trace)
    # analyzer.enable_display(False)

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

    # Create csv files
    # d = datetime.today()
    # file_name = os.path.join(DATA_PATH, d.strftime("%Y%m%d%H%M%S"))
    # s21_filename = file_name + "_s21.csv"
    s21_filename = os.path.join(DATA_PATH, "S21.csv")
    s21File = open(s21_filename, "w")
    #
    # End set network analyzer parameters
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
    # Complete frequency sweep
    #
    log.info("Measuring S21")
    print("Starting S21 Measurement")
    print("Start Frequency: " + str(f1 / 1e9) + " GHz")
    print("Stop Frequency: " + str(f2 / 1e9) + " GHz")
    print("Number of Points: " + str(nums))
    analyzer.set_measurement(channel, trace, 2, 1)
    analyzer.trigger()
    analyzer.update_display()
    analyzer.auto_scale(channel, trace)
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Retrieve and store data
    #
    # If first position, get frequency data
    s21Freq = analyzer.get_x(channel)
    s21File.write(s21Freq)
    # Get s21 data and write to file
    s21Data = analyzer.get_corr_data(channel)
    # s21Data = analyzer.get_form_data(channel)
    s21File.write(s21Data)

    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Reset motor positions to zero index
    #
    motorSet[STAND_ROTATION].goto_zero()
    if spos: # Stand translation
        motorSet[S_TRANSLATION].rot_deg(-STAND_OFFSET)
    #
    # End reset motor positions
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Close csv files
    #
    s21File.close()
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Update database
    #
    if db.is_connected():
        fstart = f1 / 1e9
        fstop = f2 / 1e9
        rowcount = mycursor.rowcount

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Antenna polarization
        #
        log.info("Updating tpolar and cpolar in sql database")
        update_config_db(log, mycursor, tpolar, "'antenna_polarization'")
        update_config_db(log, mycursor, cpolar, "'chamber_polarization'")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Network analyzer parameters
        #
        log.info("Updating fstart, fstop, and nums in sql database")
        update_config_db(log, mycursor, fstart, "'frequency_start'")
        update_config_db(log, mycursor, fstop, "'frequency_stop'")
        update_config_db(log, mycursor, nums, "'num_steps'")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Commit changes
        log.info("Committing changes")
        db.commit()
        if rowcount == mycursor.rowcount:
            log.warning("Failed to store updated antenna polarization data")

    #
    # End update database
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Call normalization function, plot data, and write zip
    #
    log.info("Normalized data written to file: " + S21Normalize(
            os.path.basename(s21_filename), maxGain=True))
    Plotting(f1, f2, nums, rstart, angle, rstop, 0, 0, 0, 0, 0, 0, "maxGain")
    #
    # End normalization
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for network analyzer errors
    log.info("Checking network analyzer error queue")
    err_nums, err_msgs = analyzer.get_errors()
    if len(err_nums) > 0:
        msg = "Error measuring S21"
        print(msg)
        log.warning(msg)
    else:
        # No errors
        msg = "S21 Measurement Successful"
        print(msg)
        log.info(msg)
    #
    # --------------------------------------------------------------------------


#
# End test routine
# ==============================================================================


# ==============================================================================
# Main function
#
def maxGain(args):
    rv = 0  # Initialize return value

    # --------------------------------------------------------------------------
    # Set up log file
    #
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("maxGain")  # Get local logger
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
        nums = int(args[2])
        rstart = float(args[3])
        angle = float(args[4])
        rstop = float(args[5])
        tpolar = float(args[6])
        cpolar = float(args[7])
        spos = bool(float(args[8])) if len(args) == 9 else spos_default
    except ValueError:
        msg = "Error: Could not parse command line arguments " + str(args)
        print(msg)
        log.exception(msg)
        return 1
    except IndexError:
        msg = "Error: Invalid number of command line arguments. " + \
              "Expected 9, received " + str(len(args))
        print(msg)
        log.exception(msg)
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
        # Initialize motors
        #
        global motorSet
        log.info("Initializing motors")
        motorSet = motors_init(mc)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Run test routine
        #
        sweep_maxGain(log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar,
                      spos)

    #
    # End attempt test
    # --------------------------------------------------------------------------

    except BaseException as e:
        # log exception
        # print("Error measuring S21. Check log file for details.")
        print(e)
        log.exception('Error in maxGain:')
        # Set return value to 1 (error)
        rv = 1
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
        # Close network analyzer
        #
        if analyzer:
            analyzer.enable_display(True)
            log.info("Closing network analyzer")
            analyzer.close()

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
    sys.exit(maxGain(argv))
#
# End enter from command line
# ==============================================================================
