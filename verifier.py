#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifier takes a log file and the corresponding log-hash file and outputs
the line numbers of mutated logs.  Also provides a library for processing
log and log-hash pairs.
"""
import hashlib
import time

import submitter

def verify_log_files_sha256(path_to_log_file, path_to_hash_file):
  """
  Takes a log file and its corresponding log-hash file and verifies the log
  line by line with the log-hashes.  Outputs lines that don't match their 
  hash.
  """
  start_time = time.time()
  counter = 1
  
  log_file = open(path_to_log_file, "r").read().split('\n')
  hash_file = open(path_to_hash_file, "r").read().split('\n')
  
  # Check log file lines against log-hashes and output any differences
  for i in range(0, len(log_file)):
    log_line = log_file[i]
    if(log_line != ''):
      # change the following line to be the hashing algorithm
      log_hash = hashlib.sha256(log_line.encode('utf-8')).hexdigest()
      hash_line = hash_file[i]
      if(log_hash == hash_line):
        counter += 1
      else:
        print("----- Error on line " + str(counter) + " ------")
        print("Error output: "+log_line)
  elapsed_time = time.time() - start_time
  print(str(elapsed_time) + " seconds to process " + str(counter) + " lines")
  return

def verify_log_list_sha256(log_list, hash_list):
  """
  Takes a log list and its corresponding log-hash list and verifies them line
  by line.  Prints to terminal the lines that don't match their hash.
  """
  counter = 0

  # Check log file lines against log-hashes and output any differences
  min_list_length = min(len(log_list), len(hash_list))
  for i in range(0, min_list_length):
    log_line = log_list[i]
    if(log_line != ''):
      # change the following line to be the hashing algorithm
      log_hash = hashlib.sha256(log_line.encode('utf-8')).hexdigest()
      hash_line = hash_list[i]
      if(log_hash == hash_line):
        counter += 1
      else:
        print("Error on line " + str(i))
  return

def verify_log_line_sha256(log_line, log_hash):
  """
  Compares a log line with a log hash, outputs boolean
  """
  if(log_line != ''):
    log_hash = hashlib.sha256(log_line.encode('utf-8')).hexdigest()
    if(log_hash == hash_line):
      return 1
  return 0

def gen_hash_of_line_sha256(log_line):
  """
  Returns sha256 hash of input string, if appending to file dont forget to manually add the new line char
  """
  return hashlib.sha256(log_line.encode('utf-8')).hexdigest()

def gen_hash_file_sha256(path_to_log_file, path_to_hash_file):
  """
  Generates and outputs a log-hash file to path_to_hash_file using a log file as input.
  """
  log_file = open(path_to_log_file, "r").read().split('\n')
  hash_file = open(path_to_hash_file, "a")

  # Check log file lines against log-hashes and output any differences
  for i in range(0, len(log_file)):
    log_line = log_file[i]
    log_hash = hashlib.sha256(log_line.encode('utf-8')).hexdigest()
    hash_file.write(log_hash+"\n")
  return

def gen_large_test_file(path_to_original_file, path_to_new_large_file, size_factor):
  """
  Generates and outputs a larger file to path_to_new_large_file using a text file as input. 
  size_factor is how many times the file should be copied and appended to the new file
  """
  start_time = time.time()
  original_file = open(path_to_original_file, "r").read().split('\n')
  large_file = open(path_to_new_large_file, "w")

  for i in range(0, size_factor):
    for j in range(0, len(original_file)):
      line = original_file[j]
      large_file.write(line+"\n")
  elapsed_time = time.time() - start_time
  print(str(elapsed_time) + " seconds to generate "+str(size_factor)+"x file")
  return

def upload_hashes_from_log_file(alethia_log, path_to_log_file):
  """
  Uses the submitter append function to append log-hashes to the blockchain from a file
  """
  start_time = time.time()
  log_file = open(path_to_log_file, "r").read().split('\n')
  for i in range(0, len(log_file)):
    #print(gen_hash_of_line_sha256(log_file[i]))
    alethia_log.append(gen_hash_of_line_sha256(log_file[i]))
    time.sleep(0.1)  # need this otherwise sawtooth cant handle all the requests for some reason
  elapsed_time = time.time() - start_time
  print(str(elapsed_time) + " seconds to upload " + str(path_to_log_file))
  return elapsed_time

def download_and_verify(alethia_log, path_to_log_file, num_pages):
  """
  Gets user defined # of pages of log-hashes to verify against the logs.
  Appends any sized page, can't do re-requests on a request failure yet
  """
  bool_is_log_modified = False
  start_time = time.time()
  hash_list = []
  for idx in range(0,  num_pages):
    #print("Check " + str(idx))
    page_list = alethia_log.get_page(idx)
    if page_list == False:
      print("Error on page " + str(idx))
      bool_is_log_modified = True
      break
    hash_list.extend(page_list)
    time.sleep(0.05)
  # prints the list of log-hashes
  #print(hash_list)
  log_list = open(path_to_log_file, "r").read().split('\n')
  verify_log_list_sha256(log_list, hash_list) # verify lists
  elapsed_time = time.time() - start_time
  print(str(elapsed_time) + " seconds to verify")
  return elapsed_time, bool_is_log_modified

if __name__ == "__main__":
  # Test Setup
  # Test files located in folder test_case_logs: foo.log and bar.txt
  private_key_hex = submitter.make_private_key_hex()
  alethia = submitter.Alethia("www.website.com", private_key_hex, api_url="http://rest-api:8008")
  log = alethia.get_log_handle("syslog4") 
  
  # Test 1: Large log file with blockchain
  #
  # Generates large test file, uploads, then downloads and verifies
  # WARNING: Creates Nx large log file, uncommend below to run
  # To rerun verification, need to comment out gen_large_test_file and upload_logs_from_file
  path_to_log_file = "./test_case_logs/foo.log"
  path_to_new_large_log_file = "./test_case_logs/large_foo.log"
  # change # to other values for stress testing
  gen_large_test_file(path_to_log_file, path_to_new_large_log_file, 100)
  t1 = upload_hashes_from_log_file(log, path_to_new_large_log_file)
  t2, bool_is_log_modified = download_and_verify(log, path_to_new_large_log_file, 90)
  
  # Output results to output_stats.txt
  output_stats_file = open('./output_stats.txt', 'a')
  output_stats_file.write("Time_up\tTime_down\tbool_is_log_modified\n")
  output_stats_file.write(str(t1)+"\t"+str(t2)+"\t"+str(bool_is_log_modified))
  output_stats_file.close()
  
  # Test 2: Small log file with blockchain
  #
  # Put data onto blockchain
  #upload_hashes_from_log_file(log, path_to_log_file)
  # Get data from blockchain and verify 
  #download_and_verify(log, path_to_log_file, 2)
  
  # Test 3: Verifier by itself
  #
  """
  path_to_hash_file = "./test_case_logs/bar.txt" 
  
  # generate large 6250x log file, writes to larger log file (will delete file if already exists)
  path_to_original_log_file = "./test_case_logs/foo.log"
  path_to_new_large_log_file = "./test_case_logs/large_foo.log"
  #gen_large_test_file(path_to_original_log_file, path_to_new_large_log_file, 6250)
  
  # generate corresponding log-hash file 
  #gen_hash_file_sha256(path_to_new_large_log_file, path_to_hash_file)
  # verify test case
  verify_log_files_sha256(path_to_original_log_file, path_to_hash_file)
  #verify_log_files_sha256(path_to_new_large_log_file, path_to_hash_file)
  """
