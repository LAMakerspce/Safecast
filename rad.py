#How to calculate and interpolate daily averages for a given location using Safecast data
#1. Query the Safecast API
#2. Use a set of GPS coordinates and select Safecast measurements within 100m of that location.
#3. Append the string &format=csv&options=with-headings to the end of the url after performing the query in order to download the data in csv format.
#4. Calculate the average and standard deviation on the measurements per selection area per day.
#5. Assume an exponential decay in radioactivity to interpolate Safecast readings at the times and places of your measurements.

import csv
import math
import time
import datetime
import numpy
import webbrowser
import os, sys
import operator

i=0
print "Make sure your browser downloads files to the directory this script is working in."
print "You will also need the file with the Fukushima sites."
print "Please make sure that FukushimaCensus.csv lives in the same directory as the script."
id=int(raw_input('Enter site ID'))
census_file = csv.DictReader(open("FukushimaCensus.csv"))
for row in census_file:
	site=int(row["ID"])
	if site==id:
		i=i+1
		if i==1:
			lat=float(row["Latitude"])
			lon=float(row["Longitude"])
			print site,lat,lon
#This loop takes user input on a particular site by ID, then grabs the location information from the FukushimaCensus.csv file.

url='https://api.safecast.org/en-US/measurements?utf8=%E2%9C%93&latitude={lat}&longitude={lon}&distance=100&captured_after=&captured_before=&since=&until=&commit=Filter&format=csv&options=with-headings'.format(lat=lat, lon=lon)
print "Downloading all Safecast data within 100m of {lat}, {lon}".format(lat=lat, lon=lon)
webbrowser.open(url)
#Use the latitude and longitude values to download all of the Safecast data within 100m of the site latitude and longitude.

path = os.getcwd()
#Get current path
#Make sure your browser downloads files to the directory this script is working in.

downloadFile='{path}/measurements.csv'.format(path=path)
while os.path.isfile(downloadFile)==False:
	time.sleep(5)
	print 'Downloading'
else:
	print 'Safecast data downloaded'
	downloadFile='measurementsSite{id}.csv'.format(id=id)
	os.rename('measurements.csv',downloadFile)
#Wait while the data is being downloaded from Safecast.
#When the file is finished downloading make sure to rename it to the site ID for future reference.

dataSorter = csv.reader(open(downloadFile),delimiter=',')
sortedlist = sorted(dataSorter, key=operator.itemgetter(0))
header=["Captured Time", "Latitude", "Longitude", "Value", "Unit", "Location Name", "Device ID", "MD5Sum", "Height", "Surface", "Radiation", "Uploaded Time", "Loader ID"]
with open("measurements.csv", "wb") as f:
	fileWriter = csv.writer(f, delimiter=',')
	fileWriter.writerow(header)
	for row in sortedlist:
		if row!=header: fileWriter.writerow(row)
os.rename('measurements.csv',downloadFile)
#This loop sorts the data downloaded from Safecast by collection time before analysis work is done.

input_file = csv.DictReader(open(downloadFile))
#Designate the input file and run analysis to determine the average and standard deviation on the radioactivity
#levels for a given selection area, in this case a circle of 100m radius around the site, and day in duration.
#The average radioactivity per site per day will be used to fit a contamination decay curve using an exponential decay model.

i=0
j=0
k=0
#i,j,k are indices

radAve=0
#average radiation value for a given day

rad=0
#radiation reading in cpm at a given GPS coordinate

radSum=0
#sum of the radiation readings within a selection area

radDiff=0
#difference between radiation readings and the mean for a day and selection area

radStDev=0
#standard deviation on the mean for radiation readings

dateList=[]
#list which stores the dates from the download file

radList=[]
#list which stores the radiation readings from the download file

for row in input_file:
	date=row["Captured Time"][:10]
	rad=float(row["Value"])
	dateList.append(date)
	radList.append(rad)
#This loop readings in all of the dates and radiation readings into two lists.

averageData='radAveragesSite{id}.csv'.format(id=id)
fileWriter = open(averageData,'wb')
wr = csv.writer(fileWriter)
label = ["date","Unix clock(s)","Average radiation (cpm)","STDEV on radiation (cpm)"]
wr.writerow(label)
#Open up an output file for the average and standard deviation on radiation value in an area.

unixClock=[]
radReadings=[]
#Initializing x (unixClock) and y (radReadings) for fitting an exponential decay curve to the fallout data.

for i in range(0, len(dateList)):
	j=dateList.count(dateList[i])
	if dateList[i]!=dateList[i-1]:
		for k in range(i, i+j):
			radSum=radSum+radList[k]
		radAve=radSum/j
		for k in range(i, i+j):
			radDiff=radDiff+(radList[k]-radAve)**2
		radStDev = (radDiff/(j-1))**0.5
		formattedDate = "/".join((dateList[i][5:7],dateList[i][8:10],dateList[i][:4]))
		clock=time.mktime(datetime.datetime.strptime(formattedDate, "%m/%d/%Y").timetuple())
		data=formattedDate,clock,radAve, radStDev
		wr.writerow(data)
		unixClock.append(clock)
		radReadings.append(math.log(radAve))
		radSum=0
		radDiff=0
		radStDev=0
#This loop finds the average and standard deviation of the radiation readings within a selection area.
#This loop calculates the averages by day for a given area.
#The formattedDate is just to convert the input date into mm/dd/yyyy format.

x=numpy.array(unixClock)
y=numpy.array(radReadings)
coefficients=numpy.polyfit(x,y,1)
print "The contamination decay curve is R(t)=exp({a}*t + {b})".format(a=coefficients[0],b=coefficients[1])
print "R(t) is in counts per minute and t is in Unix clock seconds"
#Fit a linear function to the natural log of radioactivity versus time.
#This can then be used to interpolate average radioactivity for the selection area for a given date.

census_file = csv.DictReader(open("FukushimaCensus.csv"))
interpolated_file=csv.writer(open("radInterpolatedSite{id}.csv".format(id=id),"wb"))
interpolated_file.writerow(["Site ID","Latitude","Longitude","Date","Unix clock (s)","Interpolated radioactivity (cpm)"])
print "Site ID, Latitude, Longitude, Date, Unix clock (s), Interpolated radioactivity (cpm)"

for row in census_file:
	site=int(row["ID"])	
	if site==id:
		t=float(row["Unix Clock (s)"])
		radInterpolated=math.exp(coefficients[0]*t+coefficients[1])
		formattedDate = "/".join((dateList[i][5:7],dateList[i][8:10],dateList[i][:4]))
		data=site,row["Latitude"],row["Longitude"],row["Date"],t,radInterpolated
		interpolated_file.writerow(data)
		print data
#This loop opens up a list of sites around which selection area are taken.
#Interpolated values are calculated from the different times at which a site has data.
#The interpolation model uses an exponential best-fit based on the averaged radiation level for a selection area on a day-by-day basis.
