#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import time
from datetime import datetime
import threading
import json
import subprocess
global chart_date
global stream_dict
global thread_list
thread_list = {}
stream_dict = {}
global streams_path
streams_path = ''

class recording(threading.Thread):
	def __init__(self, channel, game):
		threading.Thread.__init__(self)
		self.process = None
		self.channel = channel
		self.game = game

	def run(self):
		global thread_list
		print "Starting " + self.channel
		split_ch = self.channel.split('|')
		
		local_time = split_ch[2].replace('_', ' ')
		path = streams_path + split_ch[1].title() + ' ' + self.game + ' - ' + local_time
		title = split_ch[1].title() + ' ' + self.game + ' - ' + local_time
		if split_ch[0] == 'hitbox':
			cmd = 'livestreamer -f -o \'' + path + '.mp4\' http://hitbox.tv/' + split_ch[1] + ' best'
		elif split_ch[0] == 'twitch':
			cmd = 'livestreamer -f -o \'' + path + '.mp4\' http://twitch.tv/' + split_ch[1] + ' best'
		#print cmd
		
		self.process = subprocess.Popen(cmd, shell=True)
		self.process.wait()

		print "Starting uploading to yt..." + self.channel + ' ' + self.game + ' ' + local_time 
		cmd = 'youtube-upload --privacy=unlisted ' + '--title=\'' + title + '\' --category=Gaming --tags=\'' + self.game + '\' \'' + path + '.mp4\'' 
		process_yt = subprocess.Popen(cmd, shell=True)
		process_yt.wait()
		
		print "Finished uploading... Exiting " + self.name + ' ' + self.channel + ' ' + self.game
		cmd = 'rm \'' + path + '.mp4\''
		process_rm = subprocess.Popen(cmd, shell=True)
		process_rm.wait()

		thread_list.pop(self.channel + '|' + self.game, None)

	def stop(self):
		print "Trying to stop thread " + self.channel + ':' + self.game
		if self.process is not None:
			self.process.terminate()
			self.process = None




class dataThread (threading.Thread):
	def __init__(self, channels_twitch, channels_hitbox):
		threading.Thread.__init__(self)
		self.channels_twitch = channels_twitch
		self.channels_hitbox = channels_hitbox
	def run(self):
		print "(%s)----------working----------" % (chart_date.strftime("%Y-%m-%d %H:%M"))
		# Get lock to synchronize threads
		threadLock.acquire()
		self.parse_xml_twitch(self.channels_twitch)
		self.parse_xml_hitbox(self.channels_hitbox)
		threadLock.release()

	def get_data(self, channel_tab, link):
		try:
			request = urllib2.Request(link + "%s" % (','.join(channel_tab)))
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
 
	def parse_xml_twitch(self, channel_tab):
		ch_dict = {}
		for i in channel_tab:
			chlist = i.split('|')
			ch_dict[chlist[0]] = chlist[1]

		channel_tab_dict = list(ch_dict.keys())
		local_time = chart_date.strftime("%Y-%m-%d %H:%M")
		global stream_dict
		response = self.get_data(channel_tab_dict, 'https://api.twitch.tv/kraken/streams?channel=')
		while response == '-1':
			response = self.get_data(channel_tab_dict, 'https://api.twitch.tv/kraken/streams?channel=')
		info = json.loads(response.read().decode('utf-8'))
		for k in info['streams']:
			login = str(k['channel']['name']).lower()
			print "- %s (Twitch)" % (login)
			
			try:
				if k['channel']['game'] is None:
					stream_dict["twitch|" + login + "|" + local_time + "|" + ch_dict[login]] = 'not_set'
				else:
					stream_dict["twitch|" + login + "|" + local_time + "|" + ch_dict[login]] = str(k['channel']['game'])
			except:
				stream_dict["twitch|" + login + "|" + local_time + "|" + ch_dict[login]] = 'not_set'

	def parse_xml_hitbox(self, channel_tab):
		ch_dict = {}
		for i in channel_tab:
			chlist = i.split('|')
			ch_dict[chlist[0]] = chlist[1]

		channel_tab_dict = list(ch_dict.keys())
		local_time = chart_date.strftime("%Y-%m-%d %H:%M")
		global stream_dict
		response = self.get_data(channel_tab_dict, 'http://api.hitbox.tv/media/live/')
		while response == '-1':
			response = self.get_data(channel_tab_dict, 'http://api.hitbox.tv/media/live/')
		info = json.loads(response.read().decode('utf-8'))
		for k in info['livestream']:
			if k['media_is_live'] != '0':
				login = str(k['media_name']).lower()
				print "- %s (Hitbox)" % (login)
				try:
					if k['category_name'] is None:
						stream_dict["hitbox|" + login + "|" + local_time + "|" + ch_dict[login]] = 'not_set'
					elif str(k['category_name']) == 'Live Show':
						stream_dict["hitbox|" + login + "|" + local_time + "|" + ch_dict[login]] = 'not_set'
					else:
						stream_dict["hitbox|" + login + "|" + local_time + "|" + ch_dict[login]] = str(k['category_name'])
				except:
					stream_dict["hitbox|" + login + "|" + local_time + "|" + ch_dict[login]] = 'not_set'




def dict_check(stream_dict_before, stream_dict_after):
	global thread_list
	global chart_date
	live_on_list = []
	for key in thread_list:
		split_thr = key.split('|')

		comp_time_now = datetime.now()
		comp_time_thr = datetime.strptime(split_thr[2], "%Y-%m-%d %H:%M")
		diff = comp_time_now - comp_time_thr
		diff_minutes = diff.seconds/60
		print str(key) + 'Thr time diff ' + str(diff_minutes)
		if int(diff_minutes) > int(split_thr[3]):
			print 'stopping recording due time and starting ' + key
			thread_list[key].stop()
			#thread_list[key].join()
			thread_list.pop(key, None)
			chart_date = datetime.now()
			new_thr_part = split_thr[0] + '|' + split_thr[1] + '|' + chart_date.strftime("%Y-%m-%d %H:%M") + '|' + split_thr[3]
			thread_list[new_thr_part + '|' + split_thr[4]] = recording(new_thr_part, split_thr[4])
			thread_list[new_thr_part + '|' + split_thr[4]].start()
		try:
			live_on_list.append(split_thr[1])
		except:
			pass
		
	
	for key in stream_dict_after:
		try:
			key_after = key + '|' + stream_dict_after[key]
			key_before = key + '|' + stream_dict_before[key]
		except:
			pass
		if key not in stream_dict_before:
			if key.split('|')[1] not in live_on_list:
				print 'start recording ' + key_after
				thread_list[key_after] = recording(key, stream_dict_after[key])
				thread_list[key_after].start()
		else:
			if stream_dict_after[key] != stream_dict_before[key]:
				print 'game changed, stopping recording and starting ' + key_after
				thread_list[key_before].stop()
				#thread_list[key_before].join()
				thread_list.pop(key_before, None)
				thread_list[key_after] = recording(key, stream_dict_after[key])
				thread_list[key_after].start()

		

def main():
	global chart_date	# Wait for all threads to complete
	global stream_dict

	while 1:
		chart_date = datetime.now()

		if chart_date.second > 10 : 
			stream_dict_before = {}
			stream_dict_after = {}
			# Create new threads
			stream_dict_before = stream_dict.copy()
			stream_dict = {}
			thread_service_checker = dataThread()
			# Start new Threads
			thread_service_checker.start()
			thread_service_checker.join()

			time.sleep(55)
			
			stream_dict_after = stream_dict.copy()
			dict_check(stream_dict_before, stream_dict_after)
			
			print 'before, after ' + str(stream_dict_before) + ' ' + str(stream_dict_after)
			print thread_list
		else:
			time.sleep(5)

	print "Exiting Main Thread"

threadLock = threading.Lock()

main()

