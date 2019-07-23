################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         plotting.py
# Author(s):    Mitchell Costa
# Date:         May 2019
################################################################################

from tkinter import *
from functions import *
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
import smithplot
import logging
from smithplot import SmithAxes


#def Plotting(S11filename,S21filename,frequencyInput,chartType):
def Plotting(fstart,fstop,numpts,rstart,rincr,rstop,experiment_id,user_id,frequencyInput,chartType1,chartType2,chartType3,quickLook=None):
# ==============================================================================
# Housekeeping steps
#
#Create string for the plot type from the input args chartType1,chartType2,chartType3
    logging.basicConfig(filename="logfilename.log", level=logging.INFO)
    skipS21 = 0
    chartType=''

    if(chartType1)==1:
        chartType = 'p'
    else:
        chartType = 'r'

    if(chartType2)==1:
        chartType = chartType+'m'
    else:
        chartType = chartType+'p'

    if(chartType3)==1:
        chartType = chartType+'p'
    else:
        chartType = chartType+'r'

    #Special Case plots for the calibration process
    if(quickLook=='maxGain'):
        S21filename = 'S21.csv'
        S11filename = 'S21.csv'
        plotfilename = 'Gain.png'
        chartType = 'maxGain'
        csvPath = TMP_PATH+'\\'
        savePath = TMP_PATH+'\\PNG\\'
        skipS21 = 1

    elif(quickLook=='s11'):
        S21filename = 'S21.csv'
        S11filename = 'S11.csv'
        plotfilename = 'S11.png'
        chartType = 's11'
        csvPath = TMP_PATH+'\\'
        savePath = TMP_PATH+'\\PNG\\'
        skipS21 = 1

    else:
        #create the filename and path for the S21 and S11 data
        S21filename = '\\data_S21.csv'
        S11filename = '\\data_S11.csv'
        printfreq = frequencyInput/1e9 if ((frequencyInput/1e9)%1)!=0 else int(frequencyInput/1e9)
        plotfilename = chartType+'-'+str(printfreq)+'.png'
        csvPath = RESULTS_PATH+'\\'+str(user_id)+'\\'+str(experiment_id)+'\\'
        savePath = TMP_PATH+'\\'
    textFilePath = TMP_PATH +'\\'

    #Check to see if the PNG folder is there. If not, this creates it
    #PNG_PATH = os.path.join(DATA_PATH, "PNG")
    #if not os.path.isfolder(PNG_PATH):
    #   os.mkdir(PNG_PATH)

# ==============================================================================
# Begin S21 data manipulation
#
    if (skipS21==0):    #Skip S21 process if Special Case plot
        df2 = S21orCFcsv_to_dataframe(csvPath + S21filename)  #load the s21 csv file into dataframe
        df2.iloc[:,0] = df2.iloc[:,0].astype(int)
        df2 = df2.sort_values(df2.columns[0])
        anglesRAW = df2.iloc[:,0].as_matrix()   #Pull the angle data from the first column of the dataframe
        angles = np.asarray([[float(i) for i in anglesRAW]])  #interpret the angles as floats and create a 2D array of the angle data so it can be concatinated later on

        s21FrequencyRAW = np.asarray(list(df2))     #Get the column headers (frequency) of the dataframe
        s21FrequencyRAW[0] = 0                      #Set the 'Angle' column header to 0 TMPorarily so the rest of the column headers can be formatted
        s21FrequencyFixed2 = [float(i) for i in s21FrequencyRAW]    #Interpret the headers as floats to get rid of the leading '+' and the scientific notation at the end
        s21Headers = [int(i) for i in s21FrequencyFixed2]       #convert the floats to ints to get rid of decimals

       #If the frequency input is 0, set it to some arbitrary frequency value from the test
        if(frequencyInput==0):
            frequencyInput=s21Headers[2]

        frequencyInput = find_nearest(s21Headers, frequencyInput)

        s21Headers[0] = 'Angle'  # put 'Angle' column header back in the header list
        # Update Column Headers with corrected names
        df2.columns = s21Headers

        #Extract s21 values at the user entered frequency from the array
        numpy_data_vals = np.asarray(df2[[frequencyInput]])
        angles = angles.transpose()         #Transpose the angle array so it can be concatenated
        numpy_data = np.concatenate((angles, numpy_data_vals), 1) #concatenate the angle array with the S21 values from the user selected frequency
        Angle_Deg = numpy_data[:,0]         #extract the angle data from the array for plotting
        Val = numpy_data[:,1]               #extract the s21 data
        Angle = Angle_Deg * 2 * math.pi / 360       #convert degrees to rads for plotting

        #The following for statement gets rid of any spaces within S21 data and replaces all the 'i's with 'j's so the 'complex' data type in python can interpret the values
        Val_Fixed = [];
        for s in Val:
            Val_Fixed.append(str(s).replace(' ', ''))
        Val_Complex = [(complex(str(s).replace('i', 'j'))) for s in Val_Fixed]

        Mag = [20 * math.log10(abs(complex(s.replace('i', 'j')))) for s in Val_Fixed]   #calculate the magnitude from the S21 complex numbers
        if chartType =='pmp':
           Maximum = np.amax(Mag)      #get the maximum magnitude to scale the plot correctly
           Mag = Mag - Maximum         #Normalize the data
        Phase = np.angle(Val_Complex, deg=True) #Get the phase data from the complex S21 value
#
# End S21 data manipulation
# ==============================================================================

# ==============================================================================
# Begin S11 data manipulation
#
    df4 = S11csv_to_dataframe(csvPath + S11filename)  #load the s11 csv file into a dataframe
    S11_data = df4.as_matrix()              #convert dataframe to numpy array
    FrequencyRAW, S11_Val = S11_data        #Split the array into two seperate arrays containing the frequency data and the s11 data

    #Convert Frequency Values from Scientific Notation to Integers
    FrequencyFixed2 = [float(i) for i in FrequencyRAW]      #Get rid of the scientific notation in the frequency data
    Frequency = [int(i)/1000000000 for i in FrequencyFixed2]           #Get rid of the trailing decimal point in the frequency data, convert 1000000000 to 1.0 GHz

    S11Val_Fixed = [s.replace(' ', '') for s in S11_Val]    #Strip any spaces out of the s11 data
    S11Val_Complex = [(complex(s.replace('i', 'j'))) for s in S11Val_Fixed] #replace i with j in the complex S11 complex number

    S11Mag = [20 * math.log10(abs(complex(s.replace('i', 'j')))) for s in S11Val_Fixed] #calculate the magnitude from the s11 data
    Min = np.amin(S11Mag)           #extract the minimum magnitude to scale the plot correctly
    S11Phase = np.angle(S11Val_Complex, deg=True)   #convert the phase from rads to degrees

#
# End S21 data manipulation
# ==============================================================================

# ==============================================================================
# Begin plotting Sequence
#
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # PMP = S21 Magnitude Polar Plot
    #
    dpiScale = 200 #set the resolution of the plots
    if chartType =='pmp':
        fig_plot = plt.figure(figsize=(12, 9))
        ax = plt.subplot(111, projection='polar')
        ax.plot(Angle, Mag)
        title='S21 Gain Antenna Pattern @ '+ str(frequencyInput/1000000000)+' Ghz'
        plt.title(title, fontsize=18)
        plt.rcParams['grid.linestyle'] = ':'
        plt.axis()
        plt.grid(linestyle='dashed')
        ax.set_theta_direction(-1)
        major_Yticks = np.arange(math.ceil((np.amax(Mag)-20)/5)*5, math.ceil(((np.amax(Mag))/5)), 10)
        ax.set_yticks(major_Yticks, minor=TRUE)
        major_Xticks = np.arange(0 * math.pi / 180, 360 * math.pi / 180, 30 * math.pi / 180)
        plt.setp(ax.get_yticklabels(), rotation='horizontal', fontsize=11)
        plt.setp(ax.get_xticklabels(), rotation='horizontal', fontsize=13)
        plt.ylabel('(dB)',fontsize=14, rotation='horizontal')
        plt.xlabel('Angle (Degrees)',fontsize=14, rotation ='horizontal')
        ax.set_xticks(major_Xticks)
        ax.set_theta_zero_location("N")
        ax.yaxis.set_label_coords(-0.019, 0.35)
        ax.set_ylim(-40, 0)
        ax.set_rlabel_position(-106)  # get radial labels away from plotted line
        #plt.show()
        fig_plot.savefig(savePath+plotfilename,dpi=dpiScale)
        file = open(textFilePath+"plotfilename.txt","w") #write filename of plot to text file
        file.write(plotfilename)
        file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # PPR = S21 Phase Rectangluar Plot
    #
    elif chartType =='ppr':
        fig_plot2 = plt.figure(figsize=(12, 9))
        ax2 = plt.subplot(1, 1, 1)
        ax2.set_title('S21 Phase Antenna Pattern @ '+ str(frequencyInput/1000000000)+' Ghz',fontsize=18)
        plt.plot(Angle_Deg, Phase)
        major_Yticks = [-90,-150,-120,-90,-60,-30,0,30,60,90,120,150,90]
        ax2.set_yticks(major_Yticks, minor=FALSE)
        plt.axis([-200, 200, (np.amin(Phase)-10), (np.amax(Phase)+10)])
        plt.xlabel('Rotation Angle (Degrees)',fontsize=14)
        plt.ylabel('Phase (Degrees)',fontsize=14)
        plt.grid(True)
        plt.setp(ax2.get_yticklabels(), fontsize=13)
        plt.setp(ax2.get_xticklabels(), fontsize=13)
        #plt.show()
        fig_plot2.savefig(savePath+plotfilename,dpi=dpiScale)
        file = open(textFilePath+"plotfilename.txt","w") #write filename of plot to text file
        file.write(plotfilename)
        file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # RMR = S11 Magnitude Rectangular Plot
    #
    elif chartType =='rmr':
        fig_plot3 = plt.figure(figsize=(12, 9))
        ax3 = plt.subplot(1, 1, 1)
        ax3.set_title('S11 Antenna Pattern @ '+ str(np.amin(Frequency)) +'-'+ str(np.amax(Frequency)) + ' Ghz', fontsize=18)
        ax3.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
        plt.plot(Frequency, S11Mag)
        plt.axis([np.amin(Frequency), np.amax(Frequency), np.amin(S11Mag)-2, np.amax(S11Mag)+2])
        plt.xlabel('Frequency (GHz)',fontsize=14)
        plt.ylabel('S11 (dB)',fontsize=14)
        plt.setp(ax3.get_yticklabels(), fontsize=13)
        plt.setp(ax3.get_xticklabels(), fontsize=13)
        #ax3.set_title("S11")
        plt.grid(True)
        #plt.show()
        fig_plot3.savefig(savePath+plotfilename, dpi=dpiScale)
        file = open(textFilePath+"plotfilename.txt","w") #write filename of plot to text file
        file.write(plotfilename)
        file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # RPR = S11 Smith Plot
    #
    elif chartType =='rpr':
        fig_plot4 = plt.figure(figsize=(12, 9))
        ax4 = plt.subplot(111, projection = 'smith')
        ax4.set_title('S11 Antenna Pattern From '+ str(np.amin(Frequency)) +'-'+ str(np.amax(Frequency)) + ' Ghz',fontsize=18)
        ax4.plot(S11Val_Complex)
        #plt.show()
        fig_plot4.savefig(savePath+plotfilename, dpi=dpiScale)
        file = open(textFilePath+"plotfilename.txt","w") #write filename of plot to text file
        file.write(plotfilename)
        file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # PMR = S21 Magnitude Rectangular Plot
    #
    elif chartType =='pmr':
        fig_plot5 = plt.figure(figsize=(12, 9))
        ax5 = plt.subplot(111)
        ax5.set_title('S21 Gain Antenna Pattern @ '+ str(frequencyInput/1000000000)+' Ghz',fontsize=18)
        ax5.plot(Angle*180/math.pi, Mag)
        plt.xlabel('Angle (Degrees)',fontsize=14)
        plt.ylabel('Gain (dBi)',fontsize=14)
        plt.setp(ax5.get_yticklabels(), fontsize=13)
        plt.setp(ax5.get_xticklabels(), fontsize=13)
        plt.grid(True)
        #plt.show()
        fig_plot5.savefig(savePath+plotfilename,dpi=dpiScale)
        file = open(textFilePath+"plotfilename.txt","w") #write filename of plot to text file
        file.write(plotfilename)
        file.close()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # maxGain = S21 Magnitude @ 0 degrees Rectangular Plot
    #
    elif chartType =='maxGain':
        fig_plot6 = plt.figure(figsize=(12, 9))
        ax6 = plt.subplot(1, 1, 1)
        ax6.set_title('Test Antenna Gain',fontsize=18)
        ax6.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
        plt.plot(Frequency, S11Mag)
        plt.axis([np.amin(Frequency), np.amax(Frequency), np.amin(S11Mag)-2, np.amax(S11Mag)+2])
        plt.xlabel('Frequency (GHz)',fontsize=14)
        plt.ylabel('Gain (dB)',fontsize=14)
        plt.setp(ax6.get_yticklabels(), fontsize=13)
        plt.setp(ax6.get_xticklabels(), fontsize=13)
        plt.grid(True)
        #plt.show()
        fig_plot6.savefig(savePath+plotfilename,dpi=dpiScale)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # s11 = S11 Magnitude Rectangular Plot
    #
    elif chartType =='s11':
        fig_plot7 = plt.figure(figsize=(12, 9))
        ax7 = plt.subplot(1, 1, 1)
        ax7.set_title('S11',fontsize=18)
        ax7.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
        plt.plot(Frequency, S11Mag)
        plt.axis([np.amin(Frequency), np.amax(Frequency), np.amin(S11Mag)-2, np.amax(S11Mag)+2])
        plt.xlabel('Frequency (GHz)',fontsize=14)
        plt.ylabel('S11 (dB)',fontsize=14)
        plt.setp(ax7.get_yticklabels(), fontsize=13)
        plt.setp(ax7.get_xticklabels(), fontsize=13)
        plt.grid(True)
        #plt.show()
        fig_plot7.savefig(savePath+plotfilename,dpi=dpiScale)

    # ==============================================================================
    # Begin exit Sequence
    #

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("plotting")  # Get local logger
    # Create and format handler to write to file "log_[MONTH]_[YEAR].log"
    handler = logging.FileHandler('plotlog.log')
    handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    # Add handler to logger and specify properties
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    try:
        args = sys.argv
        log.info(args)
        Plotting(args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], int(float(args[9])*1e9), int(args[10]), int(args[11]), int(args[12]))
        status = 0
    except BaseException as e:
        log.exception(e)
        status = 1
    finally:
        log.info("Finished")
        sys.exit(status)
