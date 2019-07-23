################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         serverinfo.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files

# Standard libraries
import logging
import os

# Installed libraries

# Database constants
DB = "update_config"

# Server path
SERVER_PATH = "REDACTED_FOR_PRIVACY"

# DB config file
DB_CONFIG_FILE = os.path.join(SERVER_PATH, "REDACTED_FOR_PRIVACY")

# Temp directory
TMP_PATH = os.path.join(SERVER_PATH, "REDACTED_FOR_PRIVACY")

# Source directory
SRC_PATH = os.path.dirname(os.path.realpath(__file__))

# Data directory (data is moved from here to results directory after test
#   normalization, calfactor, and quick-look plots happen here
DATA_PATH = TMP_PATH if os.path.isdir(TMP_PATH) else "REDACTED_FOR_PRIVACY"
# Directory containing user folders which contain result folders which contain
#   data and plots
RESULTS_PATH = os.path.join(SERVER_PATH, "REDACTED_FOR_PRIVACY")

# Logging constants
LOG_LEVEL = logging.INFO
IMPORT_LOG_LEVEL = logging.WARNING

# Motor controller constants
STAND_SPEED = 1500 # steps/second
POLARIZATION_SPEED = 2500 # steps/second
TRANSLATION_SPEED = 5000 # steps/second
MOTOR_ACCELERATION = 1 # Proportional to steps/(second^2)
STAND_OFFSET = -650 # degrees
M1 = 0
M2 = 1
M3 = 2
M4 = 3
STAND_ROTATION = M1
S_TRANSLATION = M2
T_POLARIZATION = M3
C_POLARIZATION = M4
