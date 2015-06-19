#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import time
from datetime import datetime
import threading
import json
import subprocess
import os.path

global global_local_date
global stream_dict
global thread_list
global streams_dir

thread_list = {}
stream_dict = {}
streams_dir = ''

class recording(threading.Thread):
	def __init__(self, streaming_service, channel, game, local_time, cut_time):
		threading.Thread.__init__(self)
		self.process = None
		self.streaming_service = streaming_service
		self.channel = channel
		self.game = game
		self.local_time = local_time
		self.cut_time = cut_time


	def shellquote(self, str):
		return str.replace("\"", "\\\"")
		
	def run(self):
		global thread_list
		global streams_dir

		print("Starting %s" % (self.channel))
		filename = "%s%s %s - %s.mp4" % (streams_dir, self.channel.title(), self.game, self.local_time)
		title = "%s %s - %s" % (self.channel.title(), self.game, self.local_time)

		if self.streaming_service == 'hitbox':
			cmd = "livestreamer -f -o \"%s\" http://hitbox.tv/%s best" % (self.shellquote(filename), self.shellquote(self.channel))
		elif self.streaming_service == 'twitch':
			cmd = "livestreamer -f -o \"%s\" http://twitch.tv/%s best" % (self.shellquote(filename), self.shellquote(self.channel))
		print cmd
		self.process = subprocess.Popen(cmd, shell=True)
		self.process.wait()
		thread_list.pop("%s|%s|%s|%s|%s" % (self.streaming_service,self.channel, self.game, self.local_time, self.cut_time), None)
		
		if os.path.isfile(filename):
			print "Starting uploading to yt... %s %s %s" % (self.channel, self.game, self.local_time) 
			cmd = "trickle -s -u 2048 youtube-upload --privacy=unlisted --title=\"%s\" --category=Gaming --tags=\"%s\" \"%s\"" % (self.shellquote(title), self.shellquote(self.game), self.shellquote(filename)) 
			process_yt = subprocess.Popen(cmd, shell=True)
			process_yt.wait()
		
			print "Finished uploading... Exiting %s %s %s" % (self.name, self.channel, self.game)
			cmd = "rm \"%s\"" % (self.shellquote(filename))
			process_rm = subprocess.Popen(cmd, shell=True)
			process_rm.wait()

	def stop(self):
		print("Trying to stop thread %s: %s" % (self.channel, self.game))
		if self.process is not None:
			self.process.terminate()
			self.process = None




class stream_service_info(threading.Thread):
	def __init__(self, channels_twitch, channels_hitbox):
		threading.Thread.__init__(self)
		self.channels_twitch = channels_twitch
		self.channels_hitbox = channels_hitbox
	def run(self):
		print "(%s)----------working----------" % (global_local_date.strftime("%Y-%m-%d %H:%M:%S"))
		# Get lock to synchronize threads
		threadLock.acquire()
		self.parse_json(self.channels_twitch, 'twitch', 'https://api.twitch.tv/kraken/streams?channel=')
		self.parse_json(self.channels_hitbox, 'hitbox', 'http://api.hitbox.tv/media/live/')
		threadLock.release()

	def get_http_data(self, channel_list, link):
		try:
			request = urllib2.Request(link + "%s" % (','.join(channel_list)))
			response = urllib2.urlopen(request)
			return response
		except urllib2.HTTPError, e:
			print("HTTPError = %s" % (str(e.code)))
			return -1
		except urllib2.URLError, e:
			print("URLError = %s" % (str(e.reason)))
			return -1
		except:
			import traceback
			print "Generic exception: %s" % (traceback.format_exc())
			return -1
	
	def parse_twitch(self, info, streaming_service, local_time, time_cut):
		global stream_dict
		for k in info['streams']:
			login = str(k['channel']['name']).lower()
			print "- %s (Twitch)" % (login)
				
			try:
				if k['channel']['game'] is None:
					stream_dict["%s|%s" % (streaming_service, login)] = "not_set|%s|%s" % (local_time,  time_cut[login])
				else:
					stream_dict["%s|%s" % (streaming_service, login)] = "%s|%s|%s" % (str(k['channel']['game']), local_time,  time_cut[login])
			except:
				stream_dict["%s|%s" % (streaming_service, login)] = "not_set|%s|%s" % (local_time,  time_cut[login])

	def parse_hitbox(self, info, streaming_service, local_time, time_cut):
		global stream_dict
		for k in info['livestream']:
			if k['media_is_live'] != '0':
				login = str(k['media_name']).lower()
				print "- %s (Hitbox)" % (login)
				try:
					if k['category_name'] is None:
						stream_dict["%s|%s" % (streaming_service, login)] = "not_set|%s|%s" % (local_time,  time_cut[login])
					else:
						stream_dict["%s|%s" % (streaming_service, login)] = "%s|%s|%s" % (str(k['category_name']), local_time,  time_cut[login])						
				except:
					stream_dict["%s|%s" % (streaming_service, login)] = "not_set|%s|%s" % (local_time,  time_cut[login])

	def http_loop(self, tries, channel_list_dict, streaming_api_link):
		resp_count = 0
		response = self.get_http_data(channel_list_dict, streaming_api_link)
		while response == -1 and resp_count != tries:
			response = self.get_http_data(channel_list_dict, streaming_api_link)
			resp_count = resp_count + 1
			time.sleep(2)
		
		return response
		
	def json_loop(self, tries, response, channel_list_dict, streaming_api_link):
		resp_count = 0
		info = -1
		while resp_count != tries:
			try:
				info = json.loads(response.read().decode('utf-8'))
				break
			except:
				response = self.http_loop(10, channel_list_dict, streaming_api_link)
				resp_count = resp_count + 1
				time.sleep(2)
		return info

	def parse_json(self, channel_list, streaming_service, streaming_api_link):
		ch_dict = {}
		
		for i in channel_list:
			ch_list = i.split('|')
			ch_dict[ch_list[0]] = ch_list[1]

		channel_list_dict = list(ch_dict.keys())
		local_time = global_local_date.strftime("%Y-%m-%d %H:%M:%S")
		
		response = self.http_loop(10, channel_list_dict, streaming_api_link)

		info = self.json_loop(10, response, channel_list_dict, streaming_api_link)
		
		if info == -1:
			return
		if streaming_service == 'twitch':
			self.parse_twitch(info, streaming_service, local_time, ch_dict)
		elif streaming_service == 'hitbox':
			self.parse_hitbox(info, streaming_service, local_time, ch_dict)

def dict_check(stream_dict_before, stream_dict_after):
	global thread_list
	global global_local_date
	global_local_date = datetime.now()
	live_on_list = []
	for key in thread_list:
		split_thr = key.split('|')

		#comp_time_now = datetime.now()
		comp_time_thr = datetime.strptime(split_thr[3], "%Y-%m-%d %H:%M:%S")
		diff = global_local_date - comp_time_thr
		#diff_minutes = diff.seconds/60
		#print str(key) + 'Thr time diff ' + str(diff.seconds)
		if int(diff.seconds) >= int(split_thr[4]):
			#stop recording time elapsed
			new_thr_part = "%s|%s|%s|%s|%s" % (split_thr[0], split_thr[1], split_thr[2], global_local_date.strftime("%Y-%m-%d %H:%M:%S"), split_thr[4])
			print 'stopping recording due time and starting ' + new_thr_part
			try:
				thread_list[key].stop()
				thread_list.pop(key, None)

				thread_list[new_thr_part] = recording(split_thr[0], split_thr[1], split_thr[2], global_local_date.strftime("%Y-%m-%d %H:%M:%S"), split_thr[4])
				thread_list[new_thr_part].start()
			except:
				print('Not stopping thread not on list')
		try:
			live_on_list.append("%s|%s" % (split_thr[0], split_thr[1]))
		except:
			print('No live on list')
		

	for key in stream_dict_after:
		try:
			key_after = "%s|%s" % (key, stream_dict_after[key])
		except:
			pass
		if key not in live_on_list:
			#start recording no stream before
			print 'start recording ' + key_after
			split_key = key.split('|')
			split_val = stream_dict_after[key].split('|')
			thread_list[key_after] = recording(split_key[0], split_key[1], split_val[0], split_val[1], split_val[2])
			thread_list[key_after].start()
		else:			
			before_list = stream_dict_before[key].split('|')
			after_list = stream_dict_after[key].split('|')
			if after_list[0] != before_list[0]:
				#start recording game changed
				print("Game changed, stopping recording and starting %s" % (key_after))
				for key_thr, value in thread_list.iteritems():
					if key_thr.startswith(key):
						key_before = key_thr
				thread_list[key_before].stop()
				thread_list.pop(key_before, None)
				split_key = key.split('|')
				split_val = stream_dict_after[key].split('|')
				thread_list[key_after] = recording(split_key[0], split_key[1], split_val[0], split_val[1], split_val[2])
				thread_list[key_after].start()


def main():
	global global_local_date
	global stream_dict
	global streams_dir
	sec_counter = 0
	if streams_dir[-1:] != '/' or streams_dir[-1:] != '\\':
		streams_dir = "%s/" % (streams_dir)

	while 1:
			global_local_date = datetime.now()

#		if global_local_date.second > 10 : 
			#stream_dict_before = {}
			#stream_dict_after = {}
			#copy information about streams before cycle
			stream_dict_before = stream_dict.copy()
			#stream_dict = {}
			#start stream info thread to get info about streams
			if sec_counter == 0:
				#stream_dict_before = {}
				stream_dict_after = {}
				stream_dict = {}
				thread_service_checker = stream_service_info()
				thread_service_checker.start()
				thread_service_checker.join()


			time.sleep(1)
			#copy information about streams before cycle
			stream_dict_after = stream_dict.copy()
			#thread control function
			dict_check(stream_dict_before, stream_dict_after)
			if sec_counter == 0:

				print("Before, After %s %s" % (str(stream_dict_before), str(stream_dict_after)))
				print(thread_list)
		#else:
		#	time.sleep(5)
			if sec_counter == 59:
				sec_counter = 0
			else:
				sec_counter = sec_counter + 1
	print('Exiting Main Thread')

threadLock = threading.Lock()

main()
