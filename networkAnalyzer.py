################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         networkAnalyzer.py
# Author(s):    Matthew Kesselring
# Date:         May 2019
################################################################################

# Local files
from functions import *
# Standard libraries
import logging
from datetime import datetime
import time
import re
# installed libraries
import visa



# Installed libraries


# ==============================================================================
# Network analyzer class
#
class NetworkAnalyzer(object):

    # --------------------------------------------------------------------------
    # Initialize analyzer object
    #
    def __init__(self):
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

        # Connect to instrument
        self.vi = self.open()
        if not self.vi:
            raise IOError("Failed to open connection to network analyzer")

    #
    # End init
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Open instrument
    #
    def open(self):
        rm = visa.ResourceManager()  # Create resource manager object
        resource = None
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Enumerate resources and open GPIB instrument
        #
        self.log.info("Searching for GPIB devices")
        for r in rm.list_resources():
            if "GPIB" in r:
                resource = rm.open_resource(r)
                resource.timeout = 60000
                break
        return resource

    #
    # End open
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Close instrument
    #
    def close(self):
        if self.vi:
            self.vi.close()

    #
    # End close
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set basic parameters
    #
    def setup(self, channel, trace):
        ch = channel
        tr = trace
        self.display_channel()  # Display channel
        # Undefined header error below
        self.log.info("setting channel")
        self.set_channel(ch)  # Set active channel
        self.set_num_traces(ch, tr)  # Set number of traces
        self.set_trace(ch, tr)  # Set active trace
        self.sweep_type(ch)  # Set sweep type to linear
        self.sweep_mode(ch)  # Set sweep mode to stepped
        self.toggle_output(True)  # Turn on stimulus output
        self.set_auto_sweep(ch, True)  # Turn on auto sweep time
        self.set_band(1, 1000)  # Set IF bandwidth
        self.set_cont(ch, True)  # Set continuous initiation mode
        self.set_trig()  # Set trigger source to bus
        # Undefined header error for set_meas_format
        self.log.info("setting measurement format")
        self.set_meas_format(ch)  # Set measurement data format
        self.get_errors()
        self.set_trans_format()  # Set data transfer format to ASCII
        self.set_delay(ch, 0)  # Set 0 sweep delay time
        self.store_type()  # Set store type

    #
    # End setup
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Trigger measurement
    #
    def trigger(self):
        self.vi.write(":TRIG:SING")
        time.sleep(1)
        return self.wait()

    #
    # End trigger
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Wait for measurement to be complete
    #
    def wait(self):
        return self.vi.query("*OPC?")

    #
    # End wait
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Load instrument state
    #
    def load_state(self):
        command = 'MMEM:LOAD:STAT "STAT03.STA"'
        self.vi.write(command)
        time.sleep(1)

    #
    # End load_state
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set store type
    #
    def store_type(self):
        self.vi.write(":MMEM:STOR:SALL OFF")
        self.vi.write(":MMEM:STOR:STYP CDST")
        return self.vi.query(":MMEM:STOR:STYP?")

    #
    # End store_type
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Save instrument state to file
    #
    def save_state(self):
        self.vi.write(':MMEM:STOR "STAT03.STA"')
        time.sleep(2)  # Wait 2 seconds after sending command

    #
    # End save_state
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Auto scale display
    #
    def auto_scale(self, channel=1, trace=1):
        command = ':DISP:WIND' + str(channel) + ':TRAC' + str(trace) + ':Y:AUTO'
        self.vi.write(command)

    #
    # End auto_scale
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Perform S11 Calibration
    #
    def calibrate_s11(self, channel=1, port=2):
        command = ":SENS" + str(channel) + ":CORR:COLL:ECAL:SOLT1 " + str(port)
        self.vi.write(command)
        time.sleep(2)
        return self.wait()

    #
    # End calibrate_s11
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Display desired channel
    #
    def display_channel(self):
        command = ":DISP:SPL D1"
        self.vi.write(command)

    #
    # End display_channel
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Enable/disable display update
    #
    def enable_display(self, enable=True):
        command = ":DISP:ENAB"
        if enable:
            command = command + " ON"
        else:
            command = command + " OFF"
        self.vi.write(command)

    #
    # End enable_display
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get calibration coefficients
    #
    def get_calib_coef(self, channel=1):
        command = ":SENS" + str(channel) + ":CORR:COEF?"
        return self.vi.query(command)

    #
    # End get_calib_coef
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get corrected data array
    #
    def get_corr_data(self, channel=1):
        command = ':CALC' + str(channel) + ':DATA:SDAT?'
        return format_string(self.vi.query(command))

    #
    # End get_corr_data
    # --------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get corrected S-parameter data array
    #
    def get_corr_s_data(self, a=2, b=1):
        command = ':SENS:DATA:CORR? S' + str(a) + str(b)
        return format_string(self.vi.query(command))

    #
    # End get_corr_s_data
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get content of the error queue
    #
    def get_errors(self):
        command = ":SYST:ERR?"
        nums = []
        msgs = []
        while True:
            # Check error queue, deletes read-out value from queue
            err = self.vi.query(command)
            # Separate into error number and error message
            match = re.search("([^,]+),([^,]+)", err)
            if match:
                num = match.group(1)
                msg = match.group(2)
                if int(num) == 0:
                    # If error num = 0, queue is empty
                    break
                else:
                    # Else, add error number and message to lists
                    nums.append(num)
                    msgs.append(msg)
                    # Print error to log
                    self.log.warning("Error #" + num + ": " + msg)
            else:
                # Could not separate into error number and message
                break
        # Return list of error numbers and messages
        return nums, msgs

    #
    # End get_errors
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get formatted data array
    #
    def get_form_data(self, channel=1):
        self.set_meas_format(channel)
        command = ":CALC" + str(channel) + ":DATA:FDAT?"
        return format_string(self.vi.query(command))

    #
    # End get_form_data
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get raw data array
    #
    def get_raw_data(self, a=2, b=1):
        command = ':SENS:DATA:RAWD? S' + str(a) + str(b)
        return format_string(self.vi.query(command))

    #
    # End get_raw_data
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Get x-axis data
    def get_x(self, channel=1):
        command = ':CALC' + str(channel) + ':DATA:XAX?'
        return format_freq(self.vi.query(command))

    #
    # End get_x
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Enables or disables auto sweep time
    #
    def set_auto_sweep(self, channel=1, status=True):
        command = ":SENS" + str(channel) + ":SWE:TIME:AUTO"
        if status:
            self.vi.write(command + " ON")
        else:
            self.vi.write(command + " OFF")
        return self.vi.query(command + "?")

    #
    # End set_auto_sweep
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set the IF bandwidth of the selected channel
    #
    def set_band(self, channel=1, band=1000):
        command = ":SENS" + str(channel) + ":BAND"
        self.vi.write(command + " " + str(band))
        return self.vi.query(command + "?")

    #
    # End set_band
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep center frequency
    #
    def set_center(self, channel, center):
        command = ":SENS" + str(channel) + ":FREQ:CENT"
        self.vi.write(command + " " + str(center))
        return self.vi.query(command + "?")

    #
    # End set_center
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set the active channel
    #
    def set_channel(self, channel=1):
        command = ":DISP:WIND" + str(channel) + "ACT"
        self.vi.write(command)

    #
    # End set_channel
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set continuous initiation mode for the selected channel
    #
    def set_cont(self, channel=1, status=True):
        command = ":INIT" + str(channel) + ":CONT"
        if status:
            self.vi.write(command + " ON")
        else:
            self.vi.write(command + " OFF")

        return self.vi.query(command + "?")

    #
    # End set_cont
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Enable or disable data correction
    #
    def set_data_correction(self, channel=1, en=True):
        if en:
            state = ' ON'
        else:
            state = ' OFF'
        command = ':SENS' + str(channel) + ':CORR:STAT'
        self.vi.write(command + state)
        return self.vi.query(command + '?')

    #
    # End set_data_correction
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep delay time
    #
    def set_delay(self, channel, delay=0):
        command = ":SENS" + str(channel) + ":SWE:DEL"
        self.vi.write(command + " " + str(delay))
        return self.vi.query(command + "?")

    #
    # End set_delay
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set data measurement format
    #
    def set_meas_format(self, channel=1):
        # command = ':CALC' + str(channel) + ':SEL:FORM'
        command = ':CALC' + str(channel) + ':FORM'
        self.vi.write(command + ' POL')
        return self.vi.query(command + '?')

    #
    # End set_meas_format
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Select measurement parameter
    #
    def set_measurement(self, channel=1, trace=1, a=1, b=1):
        command = ":CALC" + str(channel) + ":PAR" + str(trace) + ":DEF"
        self.vi.write(command + " S" + str(a) + str(b))
        return self.vi.query(command + "?")

    #
    # End set_measurement
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set the number of traces
    #
    def set_num_traces(self, channel=1, traces=1):
        command = ":CALC" + str(channel) + ":PAR:COUN"
        self.vi.write(command + " " + str(int(traces)))
        return self.vi.query(command + "?")

    #
    # End set_num_traces
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set the number of points
    #
    def set_points(self, channel, points):
        command = ":SENS" + str(channel) + ":SWE:POIN"
        self.vi.write(command + " " + str(int(points)))
        return self.vi.query(command + "?")

    #
    # End set_points
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep span
    #
    def set_span(self, channel, span):
        command = ":SENS" + str(channel) + ":FREQ:SPAN"
        self.vi.write(command + " " + str(span))
        return self.vi.query(command + "?")

    #
    # End set_span
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep start frequency
    #
    def set_start(self, channel, start):
        command = ":SENS" + str(channel) + ":FREQ:STAR"
        self.vi.write(command + " " + str(start))
        return self.vi.query(command + "?")

    #
    # End set_start
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep stop frequency
    #
    def set_stop(self, channel, stop):
        command = ":SENS" + str(channel) + ":FREQ:STOP"
        self.vi.write(command + " " + str(stop))
        return self.vi.query(command + "?")

    #
    # End set_stop
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set the active trace
    #
    def set_trace(self, channel, trace):
        command = ":CALC" + str(channel) + ":PAR" + str(trace) + ":SEL"
        self.vi.write(command)

    #
    # End set_trace
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set data transfer format to ASCII
    #
    def set_trans_format(self):
        self.vi.write(':FORM:DATA ASC')
        return self.vi.query(':FORM:DATA?')

    #
    # End set_trans_format
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set trigger source to bus
    #
    def set_trig(self):
        command = ":TRIG:SOUR"
        self.vi.write(command + " BUS")
        return self.vi.query(command + "?")

    #
    # End set_trig
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep mode
    #
    def sweep_mode(self, channel=1):
        command = ":SENS" + str(channel) + ":SWE:GEN"
        self.vi.write(command + " STEP")
        return self.vi.query(command + "?")

    #
    # End sweep_mode
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Set sweep type
    #
    def sweep_type(self, channel=1):
        command = ":SENS" + str(channel) + ":SWE:TYPE"
        self.vi.write(command + " LIN")
        return self.vi.query(command + "?")

    #
    # End sweep_type
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Enable/disable stimulus output
    #
    def toggle_output(self, status=True):
        if status:
            self.vi.write(":OUTP ON")
        else:
            self.vi.write(":OUTP OFF")
        return self.vi.query(":OUTP?")

    #
    # End toggle_output
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Update display one time
    #
    def update_display(self):
        command = ":DISP:UPD"
        self.vi.write(command)

    #
    # End update_display
    # --------------------------------------------------------------------------

#
# End network analyzer class
# ==============================================================================
