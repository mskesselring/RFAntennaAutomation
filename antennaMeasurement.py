################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         antennaMeasurement.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files
from networkAnalyzer import NetworkAnalyzer
from functions import *
from process import S21Normalize
# Standard libraries
import sys
import logging
from datetime import datetime
import numpy
import time

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
def sweep(log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar,
          spos=spos_default):
    print('starting sweep')
    # --------------------------------------------------------------------------
    # Initialize values
    #
    ant_no = int(
            numpy.floor((rstop - rstart) / angle) + 1)  # Number of degree steps
    # If meas 0-360, don't take measurement at 360
    if (rstop == 360) and (rstart == 0):
        ant_no = ant_no - 1
    #
    # End initialize values
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set motor start positions
    #
    motorSet[STAND_ROTATION].goto_zero()
    if spos:  # Stand translation
        motorSet[S_TRANSLATION].rot_deg(STAND_OFFSET)
    set_polarization(log, motorSet, tpolar, cpolar, mycursor)
    #
    # End set motor start positions
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
        log.warning("WARNING: Invalid start frequency, using " + str(start))
        # f1_old = f1
        f1 = start

    # Set stop frequency
    stop = float(analyzer.set_stop(channel, f2))
    if f2 != stop:
        log.warning("WARNING: Invalid stop frequency, using " + str(stop))
        # f2_old = f2
        f2 = stop

    # Set number of points
    points = int(analyzer.set_points(channel, nums))
    if nums != points:
        log.warning(
                "WARNING: Invalid number of freq steps, using " + str(points))
        # nums_old = nums
        nums = points

    # Create csv files
    d = datetime.today()
    file_name = os.path.join(DATA_PATH, d.strftime("%Y%m%d%H%M%S"))
    s11_filename = file_name + "_s11.csv"
    s21_filename = file_name + "_s21.csv"
    s11File = open(s11_filename, "w")
    s21File = open(s21_filename, "w")
    #
    # End set network analyzer parameters
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for network analyzer errors
    log.debug("Checking network analyzer error queue")
    err_nums, err_msgs = analyzer.get_errors()
    if len(err_nums) > 0:
        log.warning("Error in setting network analyzer parameters")
    else:
        # No errors
        log.debug("No network analyzer errors detected")
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Measure S11 (actually S22)
    #
    log.info("Measuring S11")
    analyzer.set_measurement(channel, trace, 2, 2)
    analyzer.trigger()
    analyzer.update_display()
    analyzer.auto_scale(channel, trace)
    s11Freq = analyzer.get_x(channel)
    s11Data = analyzer.get_corr_data(channel)
    # s11Data = analyzer.get_form_data(channel)
    # Write to csv file
    log.debug("Writing s11 data to file")
    s11File.write(s11Freq)
    s11File.write(s11Data)
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for network analyzer errors
    log.debug("Checking network analyzer error queue")
    err_nums, err_msgs = analyzer.get_errors()
    if len(err_nums) > 0:
        log.warning("Error measuring s11")
    else:
        # No errors
        log.debug("No network analyzer errors detected")
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Test loop: take measurement, get current angle, move motor, repeat
    #
    log.debug("Number of angle steps: " + str(int(ant_no)))
    analyzer.set_measurement(channel, trace, 2, 1)
    log.info("Measuring S21")
    for k in range(1, ant_no + 1):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Get current angle
        #
        pos = motorSet[M1].get_position()
        # Convert to string to print to file
        if pos > 180:
            angles = str(pos - 360)
        else:
            angles = str(pos)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Complete frequency sweep
        #
        analyzer.trigger()
        analyzer.update_display()
        analyzer.auto_scale(channel, trace)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Retrieve and store data
        #
        # If first position, get frequency data
        if k == 1:
            s21Freq = analyzer.get_x(channel)
            s21File.write("Angle," + s21Freq)
        # Get s21 data and write to file
        s21Data = analyzer.get_corr_data(channel)
        # s21Data = analyzer.get_form_data(channel)
        s21File.write(str(angles) + "," + s21Data)
        # If position == 180, write duplicate data for +/- 180
        if pos == 180:
            s21File.write(str(-180) + "," + s21Data)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Calculate next rotation angle
        #
        if k != ant_no:  # If not the last step
            rot_angle = angle
        else:  # If the last step
            rot_angle = rstop - rstart - ((ant_no - 1) * angle)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Rotate motor
        #
        log.debug("Step %d. Current angle %.2f. Rotate %.2f degrees" % (
            k, pos, rot_angle))
        motorSet[STAND_ROTATION].rot_deg(rot_angle)
        time.sleep(0.25)

    #
    # End test loop
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Check for network analyzer errors
    log.debug("Checking network analyzer error queue")
    err_nums, err_msgs = analyzer.get_errors()
    if len(err_nums) > 0:
        log.warning("Error measuring s21")
    else:
        # No errors
        log.debug("No network analyzer errors detected")
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Reset motor positions to zero index
    #
    motorSet[STAND_ROTATION].goto_zero()
    if spos:
        motorSet[S_TRANSLATION].rot_deg(-STAND_OFFSET)
    #
    # End reset motor positions
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Close csv files
    #
    s11File.close()
    s21File.close()
    #
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Update database
    #
    if db.is_connected():
        tpolar = motorSet[T_POLARIZATION].get_position()
        cpolar = motorSet[C_POLARIZATION].get_position()
        fstart = f1 / 1e9
        fstop = f2 / 1e9
        rowcount = mycursor.rowcount

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Antenna polarization
        #
        log.debug("Updating tpolar and cpolar in sql database")
        update_config_db(log, mycursor, tpolar, "'antenna_polarization'")
        update_config_db(log, mycursor, cpolar, "'chamber_polarization'")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Network analyzer parameters
        #
        log.debug("Updating fstart, fstop, and nums in sql database")
        update_config_db(log, mycursor, fstart, "'frequency_start'")
        update_config_db(log, mycursor, fstop, "'frequency_stop'")
        update_config_db(log, mycursor, nums, "'num_steps'")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Commit changes
        log.debug("Committing changes")
        db.commit()
        if rowcount == mycursor.rowcount:
            log.warning("Failed to store updated antenna polarization data")

    #
    # End update database
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Call normalization function and write files to zip
    #
    log.info("Normalized data written to file: " + S21Normalize(
            os.path.basename(s21_filename)))
    file_paths = [s11_filename, s21_filename]
    create_zip(file_name, file_paths)
    #
    # End normalization
    # --------------------------------------------------------------------------


#
# End test routine
# ==============================================================================


# ==============================================================================
# Main function
#
def antenna_measurement(args):
    print('starting antenna measurement')
    rv = 0  # Initialize return value

    # --------------------------------------------------------------------------
    # Set up log file
    #
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("antennaMeasurement")  # Get local logger
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
        log.exception(
                "ERROR: Could not parse command line arguments " + str(args))
        return 1
    except IndexError:
        log.exception(
                "ERROR: Invalid number of command line arguments. "
                "Expected 9, Received " + str(len(args)))
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
            log.debug("Motor controller " + str(mc) + " opened")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Open network analyzer
        #
        global analyzer
        log.debug("Attempting connection to network analyzer")
        analyzer = NetworkAnalyzer()
        log.debug("Successfully connected to network analyzer")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Connect to database
        #
        global db, mycursor
        log.debug("Attempting connection to database")
        db, mycursor = db_init()
        if db.is_connected():
            log.debug("Successfully connected to database")
        else:
            raise Exception("Failed to connect to database")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Initialize motors
        #
        global motorSet
        log.debug("Initializing motors")
        motorSet = motors_init(mc)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Run test routine
        #
        sweep(log, f1, f2, nums, rstart, angle, rstop, tpolar, cpolar, spos)

    #
    # End attempt alignment
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Handle exceptions/errors
    #
    except BaseException:
        log.exception("Error from calibrateS21:")
        rv = 1

    # --------------------------------------------------------------------------
    # Close instruments and return (always executed with or without
    # exceptions/errors)
    #
    finally:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close motor controller
        #
        if mc:
            log.debug("Closing motor controller " + str(mc))
            # stop interactive mode (motor number does not matter)
            motorSet[M1].quit_online()
            mc.close()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close network analyzer
        #
        if analyzer:
            analyzer.enable_display(True)
            log.debug("Closing network analyzer")
            analyzer.close()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Close database connection
        #
        if db:
            if db.is_connected():
                log.debug("Closing database connection")
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
    print('antenna measurement')
    argv = sys.argv  # Store command line arguments
    argv.pop(0)  # Remove file name
    # Call main function and pass return status to system
    sys.exit(antenna_measurement(argv))
#
# End enter from command line
# ==============================================================================
