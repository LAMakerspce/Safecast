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

input_file = csv.DictReader(open("measurements.csv"))

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

fileWriter = open('radAnalysis.csv','wb')
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
print coefficients[0],coefficients[1]
#Fit a linear function to the natural log of radioactivity versus time.
#This can then be used to interpolate average radioactivity for the selection area for a given date.

census_file = csv.DictReader(open("FukushimaCensus.csv"))
id=int(raw_input('Enter site ID'))
for row in census_file:
	site=int(row["ID"])
	
	if site==id:
		t=float(row["Unix Clock (s)"])
		radInterpolated=math.exp(coefficients[0]*t+coefficients[1])
		print site,row["Day"],row["Year"][:3],"20%s"%row["Year"][4:],t,radInterpolated
#This loop opens up a list of sites around which selection area are taken.
#Interpolated values are calculated from the different times at which a site has data.
