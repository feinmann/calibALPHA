#!/usr/bin/env python
# -*- coding: utf-8 -*-

# slice_to_coordlist.py
# last edited 2012-02-06 by MB

''' 
determines local maxima in calibration-slides (fluorescent beads),
retuns txt-file with x- and y-coordinates of 'donor'- and 'acceptor' beads
and their relative distances for IGOR-import
'''

import os
#from PIL import Image 								# to open the png-files
import numpy as np 									# for array-operations
from scipy.ndimage.filters import maximum_filter, minimum_filter 	# to obtain local maxima within the png-images
import TIFFfile

# to import all the png-files in the current working directory
# returns a list with all PNGs in current working directory
def importPNG():
	filesPNG = []
	for files in os.listdir('.'):
		if files.endswith('.png'):
			filesPNG.append(files)
	return filesPNG


# input slice-image-name in local directory, returns a array with 
# x- and y-coords of local maxima on slice-image
def localMaxima(data):

	
     data_max = maximum_filter(data, 5)
     maxima = (data == data_max)
     data_min = minimum_filter(data, 5)
     diff = ((data_max - data_min) > 1000)
     maxima[diff == 0] = 0	
     myArray = np.column_stack(np.where(maxima)) # one array with first column x-coords and second column y-coords of local maxima
     myArray[:,[0, 1]] = myArray[:,[1, 0]]
     return myArray


# input coords of local maxima, returns a dict containing maxima from
# 'orange' side and from 'red' side sorted by y-coord
def orangeRed(data):
		
	# need data to be sorted according to y-value
	data = data[data[:,1].argsort(),]
	
	datanameOrange = data[data[:,0] < 128]
	datanameRed = data[data[:,0] > 127]
	
	return {'orange':datanameOrange, 'red':datanameRed}


# input a dict callable by 'orange' and 'red' with maxima-coords
# checks if maxima correspond to each other and returns an array with
# corresponding maxima-coordinates in columns (x_orange, y_orange, x_red, y_red, difx, dify)
def createCorrespondList(orangeRedData):

	correspondCoords = []	# empty list to hold maxima coords
	
	pixels = 7				# defines neighborhood for the check if 
							# maxima corresponds to each other
	
	for red_xy in orangeRedData['red']: # go thru points of the red side
		for orange_xy in orangeRedData['orange']: # check against every point of the orange side if it's close enough (within circle with radius pixels)
			if np.sqrt(np.square(red_xy[0] - orange_xy[0] - 128) + np.square(red_xy[1] - orange_xy[1])) < pixels:
				correspondCoords.append([orange_xy[0], orange_xy[1], red_xy[0]-128, red_xy[1], red_xy[0]-128-orange_xy[0], red_xy[1]-orange_xy[1]]) # and in case, append to list
				
	return np.array([correspondCoords])
	

# input array (x_orange, y_orange, x_red, y_red, difx, dify) and
# return same array with red_xy Maxima existing more than once removed!
# (will remove every red points being coupled to more than one orange point)
def cleanUpRed(orangeRedMaximaArray):
	d = {}
	for a in orangeRedMaximaArray:
		d.setdefault(tuple(a[:2]), []).append(a)

	return np.array([v for v in d.itervalues() if len(v) == 1])


# main-program using the declared functions:
if __name__ == '__main__':	
	listForIgor = np.zeros([1,6], dtype=int)										# creates an empty array in which we will put our resulting data
	
	# generate a list of numpy arrays containing tif-file each																# get all the PNG names in the current working directory
	PNGs = []
	for files in os.listdir('.'):
	    if files.endswith('.tif'):
             if TIFFfile.imread(files).shape == (256,256):
                 PNGs.append(TIFFfile.imread(files))
 
	for PNGname in PNGs:															# cycles tru every image from calibration
		orangeRedMaxima = localMaxima(PNGname)										# determines the overall local maxima
		orangeRedDict = orangeRed(orangeRedMaxima)									# seperates the local maxima into orange and red ones
		correspondingMaxima = createCorrespondList(orangeRedDict)					# couples corresponding maxima orange <-> red
		for element in correspondingMaxima:											# cycles thru all couples and appends to result-list
			listForIgor = np.append(listForIgor, element, axis=0)	
	
	listForIgor = cleanUpRed(listForIgor)											# removes duplicates
	
	listForIgor = listForIgor.reshape(listForIgor.shape[0],6)						# cosmetica for printing
		
	np.savetxt('calib20120814_result.txt', np.array(['posx_o\tposy_o\tposx\tposy\tdifx\tdify'], dtype=np.object), fmt='%s')	# add header for columns
	dataFile = open('calib20120814_result.txt', 'a')								# append data
	np.savetxt(dataFile, listForIgor, fmt='%d', delimiter='\t')						# save results for Igor-Import
	print '-> OPEN IGOR'


