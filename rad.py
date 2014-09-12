#How to calculate and interpolate daily averages for a given location using Safecast data
#1. Query the Safecast API
#2. Use a set of GPS coordinates and select Safecast measurements within 100m of that location.
#3. Append the string &format=csv&options=with-headings to the end of the url after performing the query in order to download the data in csv format.
#4. Calculate the average and standard deviation on the measurements per selection area per day.
#5. Assume an exponential decay in radioactivity to interpolate Safecast readings at the times and places of your measurements.

import csv

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
for i in range(0, len(dateList)):
	j=dateList.count(dateList[i])
	if dateList[i]!=dateList[i-1]:
		for k in range(i, i+j):
			radSum=radSum+radList[k]
		radAve=radSum/j
		for k in range(i, i+j):
			radDiff=radDiff+(radList[k]-radAve)**2
		radStDev = (radDiff/(j-1))**0.5
		print j, radAve, radStDev
		radSum=0
		radDiff=0
		radStDev=0
