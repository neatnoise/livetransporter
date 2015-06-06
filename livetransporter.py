#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import time
from datetime import datetime
import threading
import json
import subprocess
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

	def run(self):
		global thread_list
		global streams_dir

		print "Starting " + self.channel
		
		filename = streams_dir + self.channel.title() + ' ' + self.game + ' - ' + self.local_time + '.mp4'
		title = self.channel.title() + ' ' + self.game + ' - ' + self.local_time
		if self.streaming_service == 'hitbox':
			cmd = 'livestreamer -f -o \'' + filename + '\' http://hitbox.tv/' + self.channel + ' best'
		elif self.streaming_service == 'twitch':
			cmd = 'livestreamer -f -o \'' + filename + '\' http://twitch.tv/' + self.channel + ' best'
		
		self.process = subprocess.Popen(cmd, shell=True)
		self.process.wait()

		print "Starting uploading to yt..." + self.channel + ' ' + self.game + ' ' + self.local_time 
		cmd = 'trickle -s -u 2048 youtube-upload --privacy=unlisted ' + '--title=\'' + title + '\' --category=Gaming --tags=\'' + self.game + '\' \'' + filename + '\'' 
		process_yt = subprocess.Popen(cmd, shell=True)
		process_yt.wait()
		
		print "Finished uploading... Exiting " + self.name + ' ' + self.channel + ' ' + self.game
		cmd = 'rm \'' + filename + '\''
		process_rm = subprocess.Popen(cmd, shell=True)
		process_rm.wait()

		thread_list.pop(self.streaming_service + "|" + self.channel + "|" + self.game + "|" + self.local_time + "|" + self.cut_time, None)

	def stop(self):
		print "Trying to stop thread " + self.channel + ':' + self.game
		if self.process is not None:
			self.process.terminate()
			self.process = None




class stream_service_info(threading.Thread):
	def __init__(self, channels_twitch, channels_hitbox):
		threading.Thread.__init__(self)
		self.channels_twitch = channels_twitch
		self.channels_hitbox = channels_hitbox
	def run(self):
		print "(%s)----------working----------" % (global_local_date.strftime("%Y-%m-%d %H:%M"))
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
			print 'HTTPError = ' + str(e.code)
			time.sleep(2)
			return '-1'
		except urllib2.URLError, e:
			print 'URLError = ' + str(e.reason)
			time.sleep(2)
			return '-1'
		except:
			import traceback
			print 'generic exception: ' + traceback.format_exc()
			time.sleep(2)
			return '-1'
	
	def parse_twitch(self, info, streaming_service, local_time, time_cut):
		global stream_dict
		for k in info['streams']:
			login = str(k['channel']['name']).lower()
			print "- %s (Twitch)" % (login)
				
			try:
				if k['channel']['game'] is None:
					stream_dict[streaming_service + "|" + login] = 'not_set' + "|" + local_time + "|" + time_cut[login]
				else:
					stream_dict[streaming_service + "|" + login] = str(k['channel']['game']) + "|" + local_time + "|" + time_cut[login]
			except:
				stream_dict[streaming_service + "|" + login] = 'not_set' + "|" + local_time + "|" + time_cut[login]

	def parse_hitbox(self, info, streaming_service, local_time, time_cut):
		global stream_dict
		for k in info['livestream']:
			if k['media_is_live'] != '0':
				login = str(k['media_name']).lower()
				print "- %s (Hitbox)" % (login)
				try:
					if k['category_name'] is None:
						stream_dict[streaming_service + "|" + login] = 'not_set' + "|" + local_time + "|" + time_cut[login]
					else:
						stream_dict[streaming_service + "|" + login] =  str(k['category_name']) + "|" + local_time + "|" + time_cut[login]
				except:
					stream_dict[streaming_service + "|" + login] = 'not_set' + local_time + "|" + time_cut[login]

	def parse_json(self, channel_list, streaming_service, streaming_api_link):
		ch_dict = {}
		
		for i in channel_list:
			ch_list = i.split('|')
			ch_dict[ch_list[0]] = ch_list[1]

		channel_list_dict = list(ch_dict.keys())
		local_time = global_local_date.strftime("%Y-%m-%d %H:%M")

		response = self.get_http_data(channel_list_dict, streaming_api_link)
		while response == '-1':
			response = self.get_http_data(channel_list_dict, streaming_api_link)
		info = json.loads(response.read().decode('utf-8'))
		
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
		comp_time_thr = datetime.strptime(split_thr[3], "%Y-%m-%d %H:%M")
		diff = global_local_date - comp_time_thr
		diff_minutes = diff.seconds/60
		print str(key) + 'Thr time diff ' + str(diff_minutes)
		if int(diff_minutes) > int(split_thr[4]):
			#stop recording time elapsed
			new_thr_part = split_thr[0] + '|' + split_thr[1] + '|' + split_thr[2] + '|' + global_local_date.strftime("%Y-%m-%d %H:%M") + '|' + split_thr[4]
			print 'stopping recording due time and starting ' + new_thr_part
			thread_list[key].stop()
			thread_list.pop(key, None)

			thread_list[new_thr_part] = recording(split_thr[0], split_thr[1], split_thr[2], global_local_date.strftime("%Y-%m-%d %H:%M"), split_thr[4])
			thread_list[new_thr_part].start()
		try:
			live_on_list.append(split_thr[0] + '|' + split_thr[1])
		except:
			print 'no live on list'
		

	for key in stream_dict_after:
		try:
			key_after = key + '|' + stream_dict_after[key]
			key_before = key + '|' + stream_dict_before[key]
		except:
			pass
		if key not in stream_dict_before and key not in live_on_list:
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
				print 'game changed, stopping recording and starting ' + key_after
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

	if streams_dir[-1:] != '/' or streams_dir[-1:] != '\\':
		streams_dir = streams_dir + '/'

	while 1:
		global_local_date = datetime.now()

		if global_local_date.second > 10 : 
			stream_dict_before = {}
			stream_dict_after = {}
			#copy information about streams before cycle
			stream_dict_before = stream_dict.copy()
			stream_dict = {}
			#start stream info thread to get info about streams
			thread_service_checker = stream_service_info([], [])
			thread_service_checker.start()
			thread_service_checker.join()

			time.sleep(55)
			#copy information about streams before cycle
			stream_dict_after = stream_dict.copy()
			#thread control function
			dict_check(stream_dict_before, stream_dict_after)
			
			print 'before, after ' + str(stream_dict_before) + ' ' + str(stream_dict_after)
			print thread_list
		else:
			time.sleep(5)

	print "Exiting Main Thread"

threadLock = threading.Lock()

main()
