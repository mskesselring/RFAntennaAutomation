################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         functions.py
# Author(s):    Matthew Kesselring
#               Mitchell Costa
# Date:         May 2019
################################################################################

# Local files
import motors
from serverInfo import *
# Standard libraries
import re
from math import floor
from zipfile import ZipFile
import json
# Installed libraries
import mysql.connector
import visa
import pandas as pd
import numpy as np


# ==============================================================================
# Create zip file
#
def create_zip(archive_name, file_list):
    # Write file name to FileName.txt
    filename_txt = open(TMP_PATH + "\FileName.txt", "w")
    filename_txt.write(os.path.basename(archive_name))
    filename_txt.close()
    # Create zip
    with ZipFile(archive_name + '.zip', 'w') as data_zip:
        for file in file_list:
            data_zip.write(file, os.path.basename(file))
#
# End write zip file
# ==============================================================================


# ==============================================================================
# Validate parameters
#
def validate_parameters(log, f1, f2, nums, rstart, angle, rstop,
                        tpolar, cpolar):
    if rstart < 0:
        log.warning("Start angle must be greater than or equal to zero degrees."
                    + " Using 0 degree start angle")
        rstart = 0
    if rstart > 360:
        log.warning("Start angle must be less than or equal to 360 degrees."
                    + " Using 360 degree start angle")
        rstart = 360

    # Angle
    if angle < 1:
        log.warning("Angle increment must be greater than 1 degree."
                    + " Using 1 degree increment")
        angle = 1
    if angle > 180:
        log.warning("Angle increment must be less than 180 degrees."
                    + " Using 180 degree increment")
        angle = 180

    # Rstop
    if rstop > 360:
        log.warning("Stop angle must be less than or equal to 360 degrees."
                    + " Using 360 degree stop angle")
        rstop = 360
    if rstop < rstart:
        log.warning("Stop angle must be greater than or equal to start angle."
                    + " Using " + str(rstart) + " degree stop angle")
        rstop = rstart

    # Tpolar
    if tpolar < 0:
        log.warning("Test antenna polarization must be greater than or equal "
                    + "to 0 degrees. Using 0 degree test antenna polarization")
        tpolar = 0
    if tpolar > 180:
        log.warning("Test antenna polarization must be less than or equal "
                    + "to 180 degrees. Using 180 degree test antenna "
                    + "polarization")
        tpolar = 180

    # Cpolar
    if cpolar < 0:
        log.warning("Chamber antenna polarization must be greater than or "
                    + "equal to 0 degrees. Using 0 degree chamber antenna "
                    + "polarization")
        cpolar = 0
    if cpolar > 180:
        log.warning("Chamber antenna polarization must be less than or equal "
                    + "to 180 degrees. Using 180 degree chamber antenna "
                    + "polarization")
        cpolar = 180

    return f1, f2, nums, rstart, angle, rstop, tpolar, cpolar

#
# End validate parameters
# ==============================================================================


# ==============================================================================
# Initialize motors
#
def motors_init(mc):
    motorSet = list([])

    # --------------------------------------------------------------------------
    # Create motor objects
    #
    motorSet.append(motors.B4836(mc, 1))  # Test antenna stand
    motorSet.append(motors.B4836(mc, 2))  # Translation, not currently used
    motorSet.append(motors.B5990(mc, 3))  # Test antenna polarization
    motorSet.append(motors.B4836(mc, 4))  # Chamber antenna polarization
    #
    # End create motor objects
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Prepare to send commands
    #
    # Start interactive mode (motor number does not matter)
    motorSet[0].start_online()
    # Clear stored commands (motor number does not matter)
    motorSet[0].clear_cmd()
    #
    # End prepare to send commands
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set initial default values
    #
    for m in motorSet:
        m.set_acceleration(MOTOR_ACCELERATION)
    motorSet[STAND_ROTATION].set_speed(STAND_SPEED)
    motorSet[S_TRANSLATION].set_speed(TRANSLATION_SPEED)
    for m in (motorSet[T_POLARIZATION], motorSet[C_POLARIZATION]):
        m.set_speed(POLARIZATION_SPEED)
    #
    # End set initial default values
    # --------------------------------------------------------------------------

    return motorSet


#
# End motor initialization
# ==============================================================================


# ==============================================================================
# Set polarization
#
def set_polarization(log, motorSet, tpolar, cpolar, mycursor):
    try:
        tpolar_old = get_config_option(log, mycursor, "'antenna_polarization'")
        cpolar_old = get_config_option(log, mycursor, "'chamber_polarization'")

        motorSet[T_POLARIZATION].rot_deg(tpolar - tpolar_old)
        motorSet[C_POLARIZATION].rot_deg(cpolar - cpolar_old)

    except BaseException:
        motorSet[T_POLARIZATION].goto_zero()
        motorSet[C_POLARIZATION].goto_zero()
        motorSet[T_POLARIZATION].rot_deg(tpolar)
        motorSet[C_POLARIZATION].rot_deg(cpolar)

#
# End set polarization
# ==============================================================================


# ==============================================================================
# Convert scientific notation to float
#
def convert_float(match):
    group = match.group(1)
    val = float(group)
    # Force no scientific notation
    if val >= 1e-4:
        # Automatically prints without scientific notation
        num = str(val)
    elif val >= 1e-7:
        # If between (1e-4) and (1e-7), print with 18 decimal places
        num = "%.18f" % val
    else:
        # If smaller than 1e-7, print with 20 decimal places
        num = "%.20f" % val

    if group.startswith("+"):
        return "+" + num + ","
    else:
        return num + ","


#
# End convert scientific notation to float
# ==============================================================================


# ==============================================================================
# Convert scientific notation to integer
#
def convert_int(match):
    group = match.group(1)
    return str(int(floor(float(group))))


#
# End convert scientific notation to int
# ==============================================================================


# ==============================================================================
# Format frequency data string
#
def format_freq(data):
    data = re.sub("([+\-][0-9]+\.*[0-9]*[eE][+\-][0-9]+)", convert_int, data)

    data = data.replace('\n', '')
    data = data.replace('\r', '')
    data = data + '\n'

    return data


#
# End format frequency data
# ==============================================================================


# ==============================================================================
# Format data array string for export
#
def format_string(data):
    # Add extra comma at very end
    data = data + ","

    # Replace scientific notation with decimal
    data = re.sub("([^,]+),", convert_float, data)

    # Insert "i" before every second comma
    data = re.sub(",([^,]+),", r",\1i,", data)

    # Remove extra comma from very end
    data = data[:-1]

    # Remove comma separating real and imaginary parts
    data = re.sub("([0-9]),", r"\1", data)

    # Remove newline characters
    data = data.replace('\n', '')
    data = data.replace('\r', '')

    # Add one newline character
    data = data + '\n'

    return data


#
# End format data array
# ==============================================================================


# ==============================================================================
# Initialize motor controller
#
def motor_control_init(log):
    rm = visa.ResourceManager()  # Create resource manager object

    log.info("Attempting connection to motor controller")
    controller = rm.open_resource("Com3")
    controller.write_termination = '\r'
    controller.read_termination = '\r'
    controller.timeout = 30000  # 30 second timeout
    return controller  # If loop finds valid object, return object


#
# End motor controller initialization
# ==============================================================================


# ==============================================================================
# Initialize database
#
def db_init():
    config = open(DB_CONFIG_FILE)
    data = config.read()
    config.close()
    data = data.replace("<?php", "").replace("?>", "").replace("$", "").replace(
            " ", "").replace("=>", ":").replace("=array(", "{").replace(
            "array(", "{").replace(")", "}").replace("'", '"').replace(
            "connectionSettings", "").replace("};", "}")
    db_info = json.loads(data)

    db = mysql.connector.connect(host=db_info[DB]["host"],
                                 user=db_info[DB]["user"],
                                 password=db_info[DB]["password"],
                                 database=db_info[DB]["db"])
    mycursor = db.cursor()
    return db, mycursor


#
# End initialize database
# ==============================================================================


# ==============================================================================
# Update sql database
#
def update_config_db(log, mycursor, val, name):
    sql = "UPDATE config_options SET value = {0:.2f} WHERE name = {1}"
    log.debug("Executing query: " + sql.format(val, name))
    mycursor.execute(sql.format(val, name))


#
# End update sql database
# ==============================================================================


# ==============================================================================
# Get config option
#
def get_config_option(log, mycursor, name):
    sql = "SELECT value FROM config_options WHERE name = {1}"
    log.debug("Executing query: " + sql.format(name))
    for val in mycursor.execute(sql.format(name)):
        return float(val[0])
#
# End get config option
# ==============================================================================


# ==============================================================================
# Convert S11 CSV to Dataframe
#
def S11csv_to_dataframe(filename):
    df1 = pd.read_csv(filename, sep=',', header=None)
    S11_data = df1.as_matrix()
    count_row = df1.shape[0]

    return df1


#
# End Convert S11 CSV to Dataframe
# ==============================================================================


# ==============================================================================
# Convert S21 CSV to Dataframe
#
def S21orCFcsv_to_dataframe(filename):
    df1 = pd.read_csv(filename, sep=',',index_col = False)
    S21_data = df1.as_matrix()
    count_row = df1.shape[0]

    return df1
#
# End Convert S11 CSV to Dataframe
# ==============================================================================


# ==============================================================================
# Find nearest value in an array
#
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
# ==============================================================================


# ==============================================================================
# Manual input of parameters
#
def manual_input(log):
    skip = True

    while not skip:
        try:
            f1 = float(input("Start Frequency (GHz)(float): ")) * 1e9
            f2 = float(input("Stop frequency (GHz)(float): ")) * 1e9
            nums = int(input("Number of frequency steps (integer): "))
            rstart = float(input("Start angle (0-360 degrees)(float): "))
            angle = float(input("Angle increment (0-360 degrees)(float): "))
            rstop = float(input("Stop angle (0-360 degrees)(float): "))
            if rstop < rstart:
                raise ValueError("Stop angle must be greater than"
                                 + " or equal to start angle")
            tpolar = float(input("Test antenna polarization, 0 = vertical,"
                                 + " 90 = horizontal (degrees)(integer): "))
            cpolar = float(input("Chamber antenna polarization, 0 = vertical,"
                                 + " 90 = horizontal (degrees)(integer): "))
            return [f1, f2, nums, rstart, angle, rstop, tpolar, cpolar]
        except ValueError as e:
            log.error(e)
    if skip:
        raise ValueError()

#
# End manual input
# ==============================================================================
