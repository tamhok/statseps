#!/usr/bin/python

#--------------------------------
# Written by Marzyeh Ghassemi, CSAIL, MIT 
# Sept 21, 2012
# Please contact the author with errors found. 
# mghassem {AT} mit {DOT} edu
#--------------------------------

from __future__ import with_statement
import os
import os.path
import re
import string
import sys
import time
import pdb
import csv

# PATH TO DIRECTORY WITH NOTES
NOTES_PATH = "C:\\Users\\tamhok\\mimic\\notes"

# PATH TO FILES WITH DRUGS
#   Files should have a line for each distinct drug type, 
#   and drugs shld be separated by a vertical bar '|'
DRUGS_LIST_PATH = "C:\\Users\\tamhok\\Dropbox (MIT)\\MIT\\AU2016\\HST.953\\project"
statins_file = os.path.join(DRUGS_LIST_PATH, "statin_list.txt")
statin_alts_file = os.path.join(DRUGS_LIST_PATH, "statin_alts.txt")
suppress_file = os.path.join(DRUGS_LIST_PATH, "suppress_list.txt")

# OUTPUT
SUMMARY_FILE = "notes_output_full.csv"
SQL_FILE = "notes_output.sql"


###### function addToDrugs 
#   line:    line of text to search
#	drugs:   array to modify
#	listing: list of search terms in (generic:search list) form
#   genList: list of all generic keys being searched for
#
#   Searches the provided line for drugs that are listed. Inserts 
#   the dose (next number) or 9999 if not found in the drugs array provided at the location which maps 
#   the found key to the generics list
def addToDrugs(line, drugs, listing, genList):
	genList = dict(enumerate(genList))
	genList = dict((v,k) for k, v in genList.items())
	
	res = re.search("ointment|cream|topical|creme|external|eye|ocular", line, re.I)
	if not res:
		for (generic, names) in listing.items():
			query = "(?P<drug>" + names + ")(?:.*?(?P<dose>([0-9]*[.])?[0-9]+))?"
			res = re.search(query, line, re.I)
			if res:
				resdict = res.groupdict()
				if resdict['dose']:
					drugs[genList[generic]] = float(resdict['dose'])
				else:
					drugs[genList[generic]] = 9999
	return drugs
	
###### function readDrugs 
#   f:       file
#   genList: list of search terms in (generic:search list) form
#
#   Converts lines of the form "generic|brand1|brand2" to a
#   dictionary keyed by "generic" with value "generic|brand1|brand2"
def readDrugs(f, genList):
	lines = f.read()
	lines = lines.split("\n")
	generics = [x.split("|")[0] for x in lines]
	generics = [x.lower() for x in generics]
	lines = [x.lower() for x in lines]
	genList.append(generics)
	return dict(zip(generics, lines))

def main():
	# Print the variables being used for inputs
	print("Using %s notes from %s" % ("ALL", NOTES_PATH))
	print ("Using drugs from %s" % (DRUGS_LIST_PATH))
	starttime = time.time()
	
	# Keep a list of all generics we are looking for
	genList = []

	# Get the drugs into a structure we can use
	with open(statins_file) as f:
		statins = readDrugs(f, genList)
	with open(statin_alts_file) as f:
		statin_alts = readDrugs(f, genList)
	with open(suppress_file) as f:
		suppress_list = readDrugs(f, genList)
	flatList = [item for sublist in genList for item in sublist]


	
	# Create indices for the flat list
	# This allows us to understand which "types" are being used
	lengths = [len(type) for type in genList]
	prevLeng = 0
	starts = []
	ends = []
	for leng in lengths:
		starts.append(prevLeng)
		ends.append(prevLeng + leng - 1)
		prevLeng = prevLeng + leng

	print(starts)	
	print(ends)
	
	print("Lengths: %d %d %d" % (len(statins), len(statin_alts), len(suppress_list)))
	[print(flatList[s:e+1]) for s, e in zip(starts, ends)]
	[print(genList[s:e+1]) for s, e in zip(starts, ends)]
	
	# Get the list of filenames (unqualified)
	filenames = filter(lambda x: os.path.isfile(os.path.join(NOTES_PATH, x)), 
		os.listdir(NOTES_PATH))
	
	recordsKept=0
	recordsExcluded=0
	
	has_statins = 0
	has_statins_alt = 0
	has_suppress = 0
	has_supp_statin = 0
	has_both = 0
	row_id = 0
	
	# Write heads and notes to new doc
	with open(SUMMARY_FILE, 'w') as f_out:
		f_out.write("ROW_ID,HADM_ID,SUBJECT_ID,CHARTDATE,CHARTTIME,HIST_FOUND,KIDNEY,LIVER,HEART,HYPERTENSION,DIABETES,ADMIT_FOUND,STATIN,STATIN_ALT,SUPPRESS," + ",".join(flatList) + "\n")
		

		for i, doc in enumerate(filenames):
			if i % 100 == 0:
				print("%d.. %s\n" % (i, doc))
			sys.stdout.flush()

			# Read heads and notes from doc
			with open(os.path.join(NOTES_PATH, doc)) as f:
				
				reader = csv.DictReader(f, delimiter=',', quotechar='"')
				for note in reader:
				
					if re.search('discharge.*summary', note['category'], re.I):
				
						# Reset some per-patient variables
						section = ""
						newSection = ""
						admitFound = 0

						histFound = 0
						heartHist = 0;
						kidneyHist = 0;
						liverHist = 0;
						hypertensionHist = 0;
						diabetesHist = 0;
						
						drugsAdmit = [0]*len(flatList)
						row_id = note['row_id']
						hadm_id = note['hadm_id']
						sid = note['subject_id']
						chartdate = note['chartdate']
						charttime = note['charttime']
						# Read through lines sequentially
						# If this looks like a section header, start looking for drugs
						for line in note['text'].split("\n"):	

							# Searches for a section header based on my heuristics
							m = re.search(':', line, re.I)
							if m:
								newSection = ""
								# Past Medical History Section
								if re.search('med(ical)?\s+hist(ory)?', line, re.I):
									newSection = "hist"
									histFound = 1

								# Discharge Medication Section														
								elif re.search('medication(s)|meds', line, re.I) and re.search('disch(arge)?', line, re.I):
									newSection = "discharge"
									dischargeFound = 1

								# Admitting Medication Section
								elif re.search('admission|admitting|home|nh|nmeds|pre(\-|\s)?(hosp|op)|current|previous|outpatient|outpt|outside|^[^a-zA-Z]', line, re.I) and re.search('medication|meds', line, re.I):
									newSection = "admit"
									admitFound = 1 										
									
								# Med section ended, now in non-meds section						
								if section != newSection:
									section = newSection
							
							# If in history section, search for chronic diseases
							if section == "hist":
								if re.search('chronic kidney|chronic renal', line, re.I):
									kidneyHist = 1
								
								if re.search('liver failure|hepatic failure|cirrhosis|fatty liver|liver disease|hepatic failure|hepatitis', line, re.I):
									liverHist = 1
								
								if re.search('heart disease|coronary artery|coronary disease|atherosclerotic|peripheral artery disease|peripheral vascular|carotid disease|carotid artery disease|myocardial infarction|heart attack|angina pectoris|pvd', line, re.I):
									heartHist = 1
									
								if re.search('hypertension', line, re.I):
									hypertensionHist = 1
								
								if re.search('diabetes', line, re.I):
									diabetesHist = 1

							# If in meds section, look at each line for specific drugs
							elif section == 'admit':
								drugsAdmit = addToDrugs(line, drugsAdmit, statins, flatList)
								drugsAdmit = addToDrugs(line, drugsAdmit, statin_alts, flatList)
								drugsAdmit = addToDrugs(line, drugsAdmit, suppress_list, flatList)
							elif section == 'discharge':
								pass
							# A line with information which we are uncertain about... 
							elif re.search('medication|meds', line, re.I) and re.search('admission|discharge|transfer', line, re.I):
								print('?? ' + line)
							
						
						# Count the types of each drug
						member = []
						member = [sum([x != 0 for x in drugsAdmit[s:e+1]]) for s, e in zip(starts, ends)]
						if admitFound:
							# Print items for this patient into csv
							f_out.write(str(row_id) + "," + str(hadm_id) + "," + str(sid) + "," + str(chartdate) + "," + str(charttime) + "," + str(histFound) + "," + str(kidneyHist) + "," + str(liverHist) + "," + str(heartHist) + "," + str(hypertensionHist) + "," + str(diabetesHist) + "," + str(admitFound) + ","  + ",".join(map(str, member)) + "," + ",".join(map(str, drugsAdmit)) + "\n")
							recordsKept += 1
						else:
							recordsExcluded += 1						
						
						if member[0] > 0.0001:
							has_statins += 1
							if member[1] > 0:
								has_both += 1
							if member[2] > 0:
								has_supp_statin += 1
						else:
							if member[1] > 0.0001:
								has_statins_alt += 1					
							if member[2] > 0.0001:
								has_suppress += 1
						
	# Print analysis
	stoptime = time.time()
	print("Done analyzing %d documents in %.2f seconds (%.2f docs/sec)" % (i+1, stoptime - starttime, (i+1) / (stoptime - starttime)))
	print("Summary file is in %s" % (DRUGS_LIST_PATH))
	print("Records Kept: %d, Excluded: %d" % (recordsKept, recordsExcluded))
	print("On Statins: %d, On Statins and Alts: %d, On Statins and Supps: %d, On Alts only: %d, On suppress only %d" % (has_statins, has_both, has_supp_statin, has_statins_alt, has_suppress))

	with open(SQL_FILE, 'w') as f_out:
		f_out.write("SET search_path TO mimiciii;\n")
		f_out.write("CREATE TABLE statins_all\n(\n")
		f_out.write("  row_id integer NOT NULL\n")
		f_out.write("  hadm_id integer NOT NULL\n")
		f_out.write("  subject_id integer NOT NULL\n")
		f_out.write("  chartdate timestamp(0) without time zone\n")
		f_out.write("  charttime timestamp(0) without time zone\n")
		
		fieldslist = ['hist_found', 'kidney', 'liver', 'heart', 'hypertension', 'diabetes', 'admit_found', 'statin', 'statin_alt', 'suppress'] + flatList
		[f_out.write("  %s integer\n" % (x) ) for x in fieldslist]
		
		f_out.write("CONSTRAINT statins_all_pk PRIMARY KEY (row_id)\n")
		f_out.write(")")
		
if __name__ == "__main__":
	main()