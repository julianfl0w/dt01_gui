def getAlgo(algoNum):
	# apply algo https://scsynth.org/t/coding-fm-synthesis-algorithms/1381
	# numbers 1-indexed as written. they will be converted to 0-index later
	# 8 means no fmSrc
	# 7 means feedback recipient
	NOFM = 8
	FB   = 7
	
	#random dt01 params
	sum_5_6 = 8
	sum_4_5 = 9
	sum_4_5_6 = 10
	sum_2_3_5 = 11
	sum_2_3_4 = 12
	
		
	############################################
	if algoNum == 1:
		fmAlgo = [2, NOFM, 4, 5, 6, FB]
		fbSrc  = 6
		sounding = [1, 3]
	elif algoNum == 2:
		fmAlgo = [1, FB, 3, 4, 5]
		fbSrc  = 2
		sounding = [1, 3]
		
	############################################
	elif algoNum == 3:
		fmAlgo = [2, 3, 4, 5, 6, FB]
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
		fmAlgo = [2, NOFM, 4, FB, 6, NOMOD]
		fbSrc  = 4
		sounding = [1, 3]
	elif algoNum == 9:
		fmAlgo = [2, FB, 4, NOMOD, 6, NOMOD]
		fbSrc  = 2
		sounding = [1, 3]
		
	############################################
	elif algoNum == 10:
		fmAlgo = [2, 3, FB, SUM_5_6, NOMOD, NOMOD]
		fbSrc  = 2
		sounding = [1, 4]
	elif algoNum == 11:
		fmAlgo = [2, 3, NOMOD, SUM_5_6, NOMOD, FB]
		fbSrc  = 6
		sounding = [1, 4]
		
	############################################
	elif algoNum == 12:
		fmAlgo = [2, FB, SUM_4_5_6, NOMOD, NOMOD, NOMOD]
		fbSrc  = 2
		sounding = [1, 3]
	elif algoNum == 13:
		fmAlgo = [2, NOMOD, SUM_4_5_6, NOMOD, NOMOD, FB]
		fbSrc  = 6
		sounding = [1, 3]
		
	############################################
	elif algoNum == 14:
		fmAlgo = [2, NOMOD, 4, SUM_5_6, NOMOD, FB]
		fbSrc  = 6
		sounding = [1, 3]
	elif algoNum == 15:
		fmAlgo = [2, FB, 4, SUM_5_6, NOMOD, NOMOD]
		fbSrc  = 2
		sounding = [1, 3]
		
	############################################
	elif algoNum == 16:
		fmAlgo = [SUM_2_3_5, NOMOD, 4, NOMOD, 6, FB]
		fbSrc  = 6
		sounding = [1]
	elif algoNum == 17:
		fmAlgo = [SUM_2_3_5, FB, 4, NOMOD, 6, NOMOD]
		fbSrc  = 2
		sounding = [1]
	elif algoNum == 18:
		fmAlgo = [SUM_2_3_5, NOMOD, FB, 5, 6, NOMOD]
		fbSrc  = 3
		sounding = [1]
		
	############################################
	elif algoNum == 19:
		fmAlgo = [2, 3, NOMOD, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 4, 5]
	elif algoNum == 20:
		fmAlgo = [3, 3, FB, SUM_5_6, NOMOD, NOMOD]
		fbSrc  = 3
		sounding = [1, 2, 4]
	elif algoNum == 21:
		fmAlgo = [3, 3, FB, 6, 6, NOMOD]
		fbSrc  = 3
		sounding = [1, 2, 4, 5]
	elif algoNum == 22:
		fmAlgo = [2, NOMOD, 6, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 3, 4, 5]
	elif algoNum == 23:
		fmAlgo = [NOMOD, 3, NOMOD, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 4, 5]
	elif algoNum == 24:
		fmAlgo = [NOMOD, NOMOD, 6, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5]
	elif algoNum == 25:
		fmAlgo = [NOMOD, NOMOD, NOMOD, 6, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5]
		
	############################################
	elif algoNum == 26:
		fmAlgo = [NOMOD, 3, NOMOD, SUM_5_6, NOMOD, FB]
		fbSrc  = 6
		sounding = [1, 2, 4]
	elif algoNum == 27:
		fmAlgo = [NOMOD, 3, FB, SUM_5_6, NOMOD, NOMOD]
		fbSrc  = 3
		sounding = [1, 2, 4]
		
	############################################
	elif algoNum == 28:
		fmAlgo = [2, NOMOD, 4, 5, FB, NOMOD]
		fbSrc  = 5
		sounding = [1, 3, 6]
		
	############################################
	elif algoNum == 29:
		fmAlgo = [NOMOD, NOMOD, 4, NOMOD, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 5]
	elif algoNum == 30:
		fmAlgo = [NOMOD, NOMOD, 4, 5, FB, NOMOD]
		fbSrc  = 5
		sounding = [1, 2, 3, 6]
		
	############################################
	elif algoNum == 31:
		fmAlgo = [NOMOD, NOMOD, NOMOD, NOMOD, 6, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5]
	elif algoNum == 32:
		fmAlgo = [NOMOD, NOMOD, NOMOD, NOMOD, NOMOD, FB]
		fbSrc  = 6
		sounding = [1, 2, 3, 4, 5, 6]
	
	return fmAlgo, fbSrc, sounding
	