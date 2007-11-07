# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  functions for creating cron entries
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys, string

def month_map(month):
	month_list=['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August' 'September', 'October', 'November', 'December']
	if month == '*':
		return '*'
	if month in month_list:
		return month_list.index(month)

def weekday_map(weekday):
	weekday_list=['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	if weekday == '*':
		return '*'
	if weekday in weekday_list:
		return weekday_list.index(weekday)

def month_reverse_map(month):
	month_list=['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
	if month == '*':
		return '*'
	if int(month) < len(month_list):
		return month_list[int(month)]

def weekday_reverse_map(weekday):
	weekday_list=['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	if weekday == '*':
		return '*'
	if int(weekday) < len(weekday_list):
		return weekday_list[int(weekday)]

def cron_create(cronlist):

	keys=['minute', 'hour', 'day', 'month', 'weekday']
	string=''
	for key in keys:
		if cronlist.has_key(key):
			if len(cronlist[key]) == 0:
				if key == 'minute':
					string+='00 '
				else:
					string+='* '
				continue
			for i in range(len(cronlist[key])):
				if i > 0:
					string+=','
				if key == 'month':
					if cronlist[key][i] == 'all':
						string+='1,2,3,4,5,6,7,8,9,10,11,12 '
					else:
						string+='%s ' % month_map(cronlist[key][i])
				elif key == 'weekday':
					if cronlist[key][i] == 'all':
						string+='1,2,3,4,5,6,7 '
					else:
						string+='%s ' % weekday_map(cronlist[key][i])
				elif key == 'day':
					if cronlist[key][i] == '00':
						string+='0 '
					elif cronlist[key][i] == 'all':
						string+='1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31 '
					else:
						string+='%s ' % cronlist[key][i]
				else:
					if cronlist[key][i] == '00':
						string+='0 '
					elif cronlist[key][i] == 'all':
						if key == 'hour':
							string+='0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 '
						else:
							string+='0,5,10,15,20,25,30,35,40,45,50,55 '
					else:
						string+='%s ' % cronlist[key][i]
	return string

def cron_split(cronlist):
	cron=cronlist.split(' ')
	res={}
	keys=['minute', 'hour', 'day', 'month', 'weekday']
	pos=0
	for entry in cron:
		if not entry:
			continue
		if keys[pos] == 'month':
			res[keys[pos]]=[]
			for i in entry.split(','):
				try:
					res[keys[pos]].append(month_reverse_map(i))
				except:
					res[keys[pos]].append(i)
		elif keys[pos] == 'weekday':
			res[keys[pos]]=[]
			for i in entry.split(','):
				try:
					res[keys[pos]].append(weekday_reverse_map(i))
				except:
					res[keys[pos]].append(i)
		elif keys[pos] == 'day' and "55" in entry.split(','):
			res[keys[pos]]=['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
		else:
			res[keys[pos]]=entry.split(',')

		pos+=1
	return res

