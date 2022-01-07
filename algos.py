def getAlgo(algoNum):
	# apply algo https://scsynth.org/t/coding-fm-synthesis-algorithms/1381
	# numbers 1-indexed as written. they will be converted to 0-index later
	# 8 means no fmSrc
	# 7 means feedback recipient
	NOFM = 8
	FB   = 7
	
	#random dt01 params
	SUM_5_6   = 9 
	SUM_4_5   = 10
	SUM_4_5_6 = 11
	SUM_2_3_5 = 12
	SUM_2_3_4 = 13
	
		
	############################################
	if algoNum == 1:
		fmAlgo = [2, NOFM, 4, 5, 6, FB]
		fbSrc  = 6
		sounding = [1, 3]
	elif algoNum == 2:
		fmAlgo = [2, FB, 4, 5, 6, NOFM]
		fbSrc  = 2
		sounding = [1, 3]
		
	############################################
	elif algoNum == 3:
		fmAlgo = [2, 3, NOFM, 5, 6, FB]
		fbSrc  = 6
		sounding = [1, 4]
	elif algoNum == 4:
		fmAlgo = [2, 3, NOFM, 5, 6, FB]
		fbSrc  = 4
		sounding = [1, 4]
		
	############################################
	elif algoNum == 5:
		fmAlgo = [2, NOFM, 4, NOFM, 6, FB]
		fbSrc  = 6
		sounding = [1, 3, 5]
	elif algoNum == 6:
		fmAlgo = [2, NOFM, 4, NOFM, 6, FB]
		fbSrc  = 5
		sounding = [1, 3, 5]
		
	############################################
	elif algoNum == 7:
		fmAlgo = [2, NOFM, 4, NOFM, 6, FB]
		fbSrc  = 5
		sounding = [1, 3]
	elif algoNum == 8:
		fmAlgo = [2, NOFM, 4, FB, 6, NOFM]
		fbSrc  = 4
		sounding = [1, 3]
	elif algoNum == 9:
		fmAlgo = [2, FB, 4, NOFM, 6, NOFM]
		fbSrc  = 2
		sounding = [1, 3]
		
	############################################
	elif algoNum == 10:
		fmAlgo = [2, 3, FB, SUM_5_6, NOFM, NOFM]
		fbSrc  = 2
		sounding = [1, 4]
	elif algoNum == 11:
		fmAlgo = [2, 3, NOFM, SUM_5_6, NOFM, FB]
		fbSrc  = 6
		sounding = [1, 4]
		
	############################################
	elif algoNum == 12:
		fmAlgo = [2, FB, SUM_4_5_6, NOFM, NOFM, NOFM]
		fbSrc  = 2
		sounding = [1, 3]
	elif algoNum == 13:
		fmAlgo = [2, NOFM, SUM_4_5_6, NOFM, NOFM, FB]
		fbSrc  = 6
		sounding = [1, 3]
		
	############################################
	elif algoNum == 14:
		fmAlgo = [2, NOFM, 4, SUM_5_6, NOFM, FB]
		fbSrc  = 6
		sounding = [1, 3]
	elif algoNum == 15:
		fmAlgo = [2, FB, 4, SUM_5_6, NOFM, NOFM]
		fbSrc  = 2
		sounding = [1, 3]
		
	############################################
	elif algoNum == 16:
		fmAlgo = [SUM_2_3_5, NOFM, 4, NOFM, 6, FB]
		fbSrc  = 6
		sounding = [1]
	elif algoNum == 17:
		fmAlgo = [SUM_2_3_5, FB, 4, NOFM, 6, NOFM]
		fbSrc  = 2
		sounding = [1]
	elif algoNum == 18:
		fmAlgo = [SUM_2_3_5, NOFM, FB, 5, 6, NOFM]
		fbSrc  = 3
		sounding = [1]
		
	############################################
	elif algoNum == 19:
		fmAlgo = [2, 3, NOFM, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 4, 5]
	elif algoNum == 20:
		fmAlgo = [3, 3, FB, SUM_5_6, NOFM, NOFM]
		fbSrc  = 3
		sounding = [1, 2, 4]
	elif algoNum == 21:
		fmAlgo = [3, 3, FB, 6, 6, NOFM]
		fbSrc  = 3
		sounding = [1, 2, 4, 5]
	elif algoNum == 22:
		fmAlgo = [2, NOFM, 6, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 3, 4, 5]
	elif algoNum == 23:
		fmAlgo = [NOFM, 3, NOFM, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 4, 5]
	elif algoNum == 24:
		fmAlgo = [NOFM, NOFM, 6, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5]
	elif algoNum == 25:
		fmAlgo = [NOFM, NOFM, NOFM, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5]
		
	############################################
	elif algoNum == 26:
		fmAlgo = [NOFM, 3, NOFM, SUM_5_6, NOFM, FB]
		fbSrc  = 6
		sounding = [1, 2, 4]
	elif algoNum == 27:
		fmAlgo = [NOFM, 3, FB, SUM_5_6, NOFM, NOFM]
		fbSrc  = 3
		sounding = [1, 2, 4]
		
	############################################
	elif algoNum == 28:
		fmAlgo = [2, NOFM, 4, 5, FB, NOFM]
		fbSrc  = 5
		sounding = [1, 3, 6]
		
	############################################
	elif algoNum == 29:
		fmAlgo = [NOFM, NOFM, 4, NOFM, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 5]
	elif algoNum == 30:
		fmAlgo = [NOFM, NOFM, 4, 5, FB, NOFM]
		fbSrc  = 5
		sounding = [1, 2, 3, 6]
		
	############################################
	elif algoNum == 31:
		fmAlgo = [NOFM, NOFM, NOFM, NOFM, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5]
	elif algoNum == 32:
		fmAlgo = [NOFM, NOFM, NOFM, NOFM, NOFM, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5, 6]
	
	return fmAlgo, fbSrc, sounding
	