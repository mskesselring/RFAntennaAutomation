################################################################################
# Project:      NCSU ECE PREAL 2.0 Senior Design Project
# File:         process.py
# Author(s):    Mitchell Costa
# Date:         May 2019
################################################################################

from tkinter import *
from functions import *
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import cmath
import scipy.interpolate
import matplotlib.ticker as ticker
from decimal import *
Cal_Test_filename = 's21Calibration.csv'

def CalCalFactor():
    Cal_Test_filename = 's21Calibration.csv'
    No_of_points=801
    constant = 43.5

    df1 = S11csv_to_dataframe(TMP_PATH + '\\' +Cal_Test_filename)  #load the Cal_Test_ csv file into a dataframe
    Cal_Test_data = df1.as_matrix()              #convert dataframe to numpy array
    FrequencyRAW, Cal_Test_Val = Cal_Test_data        #Split the array into two seperate arrays containing the frequency data and the Cal_Test_ data

    #Convert Frequency Values from Scientific Notation to Integers
    FrequencyFixed2 = [float(i) for i in FrequencyRAW]      #Get rid of the scientific notation in the frequency data
    Frequency = [(float(i)/1000000000) for i in FrequencyFixed2]           #Get rid of the trailing decimal point in the frequency data
    Cal_Test_Val_Fixed = [str(s).replace(' ', '') for s in Cal_Test_Val]    #Strip any spaces out of the Cal_Test_ data
    Cal_Test_Val_Complex = [(complex(s.replace('i', 'j'))) for s in Cal_Test_Val_Fixed] #replace i with j in the complex Cal_Test_ complex number

    Cal_Test_Mag = [20 * math.log10(abs(complex(s.replace('i', 'j')))) for s in Cal_Test_Val_Fixed] #calculate the magnitude from the Cal_Test_ data
    Cal_Test_Phase = np.angle(Cal_Test_Val_Complex, deg=True)   #convert the phase from rads to degrees

    freq1 = Frequency[0]
    freq2 = Frequency[No_of_points-1]

    if ((freq1>=1.7)&(freq2<=2.6)):
        std_freq= [1.7000,1.7500,1.8000,1.8500,1.9000,1.9500,2.0000,2.0500,2.1000,2.1500,2.2000,2.2500,2.3000,2.3500,2.4000,2.4500 ,2.5000,2.5500,2.6000]
        std_Gain= [13.8,13.9,14.0,13.9,14.0,14.1,14.9,14.6,14.4,14.8,14.9,15.1,15.4,15.4,15.4,15.3,16.0,16.2,16.6]
    else:
        std_freq=[0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.25,1.5,1.75,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5]
        std_Gain = [-40,-30,-20,-10,1.5,6.5,6.9,7.2,8.5,9.5,10.1,8.5,9.8,10.1,11.2,10.1,10.9,10.4,11.6,11.6,11.2]

    step  = (freq2-freq1)/(No_of_points-1)
    pchip_Std_Gain = scipy.interpolate.PchipInterpolator(std_freq,std_Gain)
    xi = np.arange(freq1,freq2+step,0.006875)
    interpMag = pchip_Std_Gain(xi)

    CalFactor = interpMag-Cal_Test_Mag;
    OutputFrequency = [(int(round((i)*1000000000))) for i in xi]

    OutputFrequency = np.asarray(OutputFrequency)
    np.asarray(CalFactor)
    calFactorDataframe = pd.DataFrame(np.reshape(CalFactor, (1,len(CalFactor))),columns=OutputFrequency)

    #Create the CalFactor Plot
    fig_plot1 = plt.figure(figsize=(14, 9))
    ax1 = plt.subplot(1, 1, 1)
    ax1.set_title('S21 Calibration Plot')
    #ax1.xaxis.set_major_locator(ticker.MultipleLocator()) #dont use unless you want to crash your computer
    plt.plot(OutputFrequency, CalFactor)
    plt.axis([np.amin(OutputFrequency), np.amax(OutputFrequency), np.amin(CalFactor)-5, np.amax(CalFactor)+5])
    plt.xlabel('Frequency (GHz)')
    plt.ylabel('S21 Calibration Factor')
    plt.grid(True)
    plotfilename = 'GainCalibration.png'
    fig_plot1.savefig(TMP_PATH+'/PNG/'+plotfilename)
    CFFilename = ('CalFactor')                     #correct filename
    calFactorDataframe.to_csv(DATA_PATH+'\\'+CFFilename+'.csv', sep=',', encoding='utf-8', index=False)   #Write to CSV
    return(1)

def S21Normalize(S21filename,maxGain=False):
    startColumn = 0 if maxGain else 1
    #Get the angle data
    print('BEGIN S21 NORM')
    calFactorFilename = ('CalFactor.csv')
    dfS21 = S21orCFcsv_to_dataframe(DATA_PATH + '\\' + S21filename)  #load the s21 csv file into dataframe
    dfCF  = S21orCFcsv_to_dataframe(DATA_PATH + '\\' + calFactorFilename)  #load the s21 csv file into dataframe

    #Format the S21 Dataframe, Extract Angle Data
    s21FrequencyRAW = np.asarray(list(dfS21))     #Get the column headers (frequency) of the dataframe
    s21FrequencyRAW[0] = 0 if not maxGain else s21FrequencyRAW[0]       #Set the 'Angle' column header to 0 temporarily so the rest of the column headers can be formatted
    s21FrequencyFixed2 = [float(i) for i in s21FrequencyRAW]    #Interpret the headers as floats to get rid of the leading '+' and the scientific notation at the end
    s21Headers = [int(i) for i in s21FrequencyFixed2]       #convert the floats to ints to get rid of decimals
    s21Headers[0] = 'Angle' if not maxGain else s21Headers[0]       #put 'Angle' column header back in the header list
    #Update S21 Column Headers with corrected names
    dfS21.columns = s21Headers
    dfS21.columns = dfS21.columns.astype(str) #convert headers to string

    #Format the CalFactor Dataframe
    dfCF.columns = dfCF.columns.astype(str)

    Columns = (dfS21.shape[1])    #get the number of columns
    Rows = (dfS21.shape[0])       #get the number of rows

    #The following loop steps though each column (frequency) and normalizes the data to the maximum value
    for y in range (startColumn,Columns):
        #Extract s21 values at the user entered frequency from the array
        currentFrequency = dfS21.columns[y] #frequency string
        S21slice = np.asarray([dfS21.iloc[:,y]])
        S21slice = S21slice.transpose()

        #The following for statement gets rid of any spaces within S21 data and replaces all the 'i's with 'j's so the 'complex' data type in python can interpret the values
        S21_Fixed = []
        S21_Complex = np.asarray([])
        newS21 = []
        newColumn = []

        for s in S21slice:
            S21_Fixed.append(str(s).replace(' ', ''))

        for s in S21_Fixed:
            #Format value for complex() cast
            s = (s).replace('i', 'j')
            s = (s).replace('[', '')
            s = (s).replace('\'', '')
            s = (s).replace(']', '')
            S21_Complex = np.append(S21_Complex,complex(s))

        dfCF.index = ['Value']
        constant = dfCF.loc['Value',currentFrequency]
        constantF = 10**(constant/20);

        newS21 = [i*constantF for i in S21_Complex]
        #the following for loop strips out the () from the complex number and adds it to the dataframe
        for n in newS21:
            fixed = str(n).replace('(', '').replace(')', '')
            newColumn.append(fixed)

        dfS21.iloc[:,y] = newColumn

    dfS21.to_csv(DATA_PATH + '\\' + S21filename, sep=',', encoding='utf-8', index=False)   #Write to CSV
    return S21filename+'.csv'
