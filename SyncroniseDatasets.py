#-------------------------------------------------------------
# Name:       Syncronise Datasets 
# Purpose:    Runs the syncronise changes gp tool to update dataset changes from one geodatabase to another.      
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    12/06/2014
# Last Updated:    15/07/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import string

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "false" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = os.path.join(os.path.dirname(__file__), r"") # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(sourceGeodatabase,replicatedGeodatabase,replicaName,featureClasses,tables): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # Split the replicas string in case there are more than one
        replica = string.split(replicaName, ",")

        # For each replica
        for replica in replica: 
            arcpy.AddMessage("Syncing changes for " + replica + " replica...")
            # Logging
            if (enableLogging == "true"):
                logger.info("Syncing changes for " + replica + " replica...")
            # Sync changes between databases for the replica
            arcpy.SynchronizeChanges_management(sourceGeodatabase, replica, replicatedGeodatabase, "FROM_GEODATABASE1_TO_2", "IN_FAVOR_OF_GDB1", "BY_OBJECT", "DO_NOT_RECONCILE")

        # Copy over views and custom tables - Copy used, will fail if locks present on FGDB.
        if (len(tables) > 0):
            # Remove out apostrophes
            tableList = string.split(str(tables).replace("'", ""), ";")       
            # Copy over tables
            for table in tableList:
                # Logging
                if (enableLogging == "true"):
                    logger.info("Copying Over Table " + table + "...")                                
                arcpy.AddMessage("Copying Over Table " + table + "...")               
                tableName = arcpy.Describe(table)

                # Change dataset name to be just name (remove user and schema if SDE database)
                splitDataset = tableName.name.split('.')
                dataset = splitDataset[-1]
                
                arcpy.CopyRows_management(table, os.path.join(replicatedGeodatabase, dataset), "")
                
        if (len(featureClasses) > 0):        
            # Remove out apostrophes
            featureClassList = string.split(str(featureClasses).replace("'", ""), ";")           
            # Copy over feature classes
            for featureClass in featureClassList:
                # Logging
                if (enableLogging == "true"):
                    logger.info("Copying Over Feature Class " + featureClass + "...")                                
                arcpy.AddMessage("Copying Over Feature Class " + featureClass + "...")            
                featureClassName = arcpy.Describe(featureClass)

                # Change dataset name to be just name (remove user and schema if SDE database)
                splitDataset = featureClassName.name.split('.')
                dataset = splitDataset[-1]

                arcpy.CopyFeatures_management(featureClass, os.path.join(replicatedGeodatabase, dataset), "", "0", "0", "0")

        # --------------------------------------- End of code --------------------------------------- #  
            
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                arcpy.SetParameterAsText(1, output)
        # Otherwise return the result          
        else:
            # Return the output if there is any
            if output:
                return output      
        # Logging
        if (enableLogging == "true"):
            # Log end of process
            logger.info("Process ended.")
            # Remove file handler and close log file            
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        pass
    # If arcpy error
    except arcpy.ExecuteError:           
        # Build and show the error message
        errorMessage = arcpy.GetMessages(2)   
        arcpy.AddError(errorMessage)           
        # Logging
        if (enableLogging == "true"):
            # Log error          
            logger.error(errorMessage)                 
            # Remove file handler and close log file
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)
    # If python error
    except Exception as e:
        errorMessage = ""
        # Build and show the error message
        for i in range(len(e.args)):
            if (i == 0):
                errorMessage = str(e.args[i])
            else:
                errorMessage = errorMessage + " " + str(e.args[i])
        arcpy.AddError(errorMessage)              
        # Logging
        if (enableLogging == "true"):
            # Log error            
            logger.error(errorMessage)               
            # Remove file handler and close log file
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)            
# End of main function


# Start of set logging function
def setLogging(logFile):
    # Create a logger
    logger = logging.getLogger(os.path.basename(__file__))
    logger.setLevel(logging.DEBUG)
    # Setup log message handler
    logMessage = logging.FileHandler(logFile)
    # Setup the log formatting
    logFormat = logging.Formatter("%(asctime)s: %(levelname)s - %(message)s", "%d/%m/%Y - %H:%M:%S")
    # Add formatter to log message handler
    logMessage.setFormatter(logFormat)
    # Add log message handler to logger
    logger.addHandler(logMessage) 

    return logger, logMessage               
# End of set logging function


# Start of send email function
def sendEmail(message):
    # Send an email
    arcpy.AddMessage("Sending email...")
    # Server and port information
    smtpServer = smtplib.SMTP("smtp.gmail.com",587) 
    smtpServer.ehlo()
    smtpServer.starttls() 
    smtpServer.ehlo
    # Login with sender email address and password
    smtpServer.login(emailUser, emailPassword)
    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
    body = header + '\n' + emailMessage + '\n' + '\n' + message
    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, body)    
# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Arguments are optional - If running from ArcGIS Desktop tool, parameters will be loaded into *argv
    argv = tuple(arcpy.GetParameterAsText(i)
        for i in range(arcpy.GetArgumentCount()))
    mainFunction(*argv)
    
