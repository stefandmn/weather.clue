# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import base64
import socket
import unicodedata
from utilities import *
from datetime import date
import Commons as commons
from abstract import DataProvider

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcaddon"):
	xbmcaddon = sys.modules["__main__"].xbmcaddon
else:
	import xbmcaddon

if hasattr(sys.modules["__main__"], "xbmcvfs"):
	xbmcvfs = sys.modules["__main__"].xbmcvfs
else:
	import xbmcvfs


class Wunderground(DataProvider):
	WUNDERGROUND_LOC = 'http://autocomplete.wunderground.com/aq?query=%s&format=JSON'
	WEATHER_FEATURES = 'hourly/conditions/forecast10day/astronomy/almanac/alerts/satellite'

	def __init__(self):
		socket.setdefaulttimeout(10)

	def code(self):
		return "wunderground"

	def _toint(self, s):
		s = s.strip()
		return int(s) if s else 0

	# wunderground provides a corrupt alerts message
	def _recode(self, alert):
		try:
			alert = alert.encode("latin-1").rstrip('&nbsp)').decode("utf-8")
		except:
			pass
		return alert

	def _find(self, loc):
		url = self.WUNDERGROUND_LOC % urllib2.quote(loc)
		try:
			req = urllib2.urlopen(url)
			response = req.read()
			req.close()
		except:
			response = ''
		return response

	def location(self, string):
		locs = []
		locids = []
		commons.debug('Location: %s' % string)
		loc = unicodedata.normalize('NFKD', unicode(string, 'utf-8')).encode('ascii', 'ignore')
		commons.debug('Searching for location: %s' % loc)
		query = self._find(loc)
		commons.debug('Location data: %s' % query)
		data = self._parse(query)
		if data is not None and data.has_key("RESULTS"):
			for item in data["RESULTS"]:
				location = item["name"]
				locationid = item["l"][3:]
				locs.append(location)
				locids.append(locationid)
		return locs, locids

	def geoip(self):
		retry = 0
		query = ''
		while (retry < 6) and (not xbmc.abortRequested):
			query = self.call('geolookup', 'lang:EN', 'autoip', self.FORMAT)
			if query != '':
				retry = 6
			else:
				retry += 1
				xbmc.sleep(10000)
				commons.debug('GeoIP download failed')
		commons.debug('GeoIP data: %s' % query)
		data = self._parse(query)
		if data is not None and data.has_key('location'):
			location = data['location']['city']
			locationid = data['location']['l'][3:]
			xbmcaddon.Addon().setSetting('Location1', location)
			xbmcaddon.Addon().setSetting('Location1id', locationid)
			commons.debug('GeoIP location: %s' % location)
		else:
			location = ''
			locationid = ''
		return location, locationid

	def forecast(self, loc, locid):
		try:
			lang = LANG[self.LANG]
		except:
			lang = 'EN'
		opt = 'lang:' + lang
		commons.debug('Weather location: %s' % locid)
		retry = 0
		query = ''
		while (retry < 6) and (not xbmc.abortRequested):
			query = self.call(self.WEATHER_FEATURES, opt, locid, self.FORMAT)
			if query != '':
				retry = 6
			else:
				retry += 1
				xbmc.sleep(10000)
				commons.debug('Weather download failed')
		commons.trace('Forecast data: %s' % query)
		data = self._parse(query)
		if data is not None and data.has_key('response') and not data['response'].has_key('error'):
			self.properties(data, loc, locid)
		else:
			self.clear()

	def _parse(self, content):
		try:
			raw = content.replace('<br>', ' ').replace('&auml;', 'ä') # wu api bugs
			raw = raw.replace('"-999%"', '""').replace('"-9999.00"', '""').replace('"-9998"', '""').replace('"NA"', '""') # wu will change these to null responses in the future
			output = json.loads(raw)
		except:
			commons.debug('Failed to parse weather data')
			output = None
		return output

	def properties(self, data, loc, locid):
		# standard properties
		weathercode = WEATHER_CODES[os.path.splitext(os.path.basename(data['current_observation']['icon_url']))[0]]
		self.property('Current.Location', loc)
		self.property('Current.Condition', data['current_observation']['weather'])
		self.property('Current.Temperature', str(data['current_observation']['temp_c']))
		self.property('Current.Wind', str(data['current_observation']['wind_kph']))
		self.property('Current.WindDirection', data['current_observation']['wind_dir'])
		self.property('Current.Humidity', data['current_observation']['relative_humidity'].rstrip('%'))
		self.property('Current.FeelsLike', data['current_observation']['feelslike_c'])
		self.property('Current.UVIndex', data['current_observation']['UV'])
		self.property('Current.DewPoint', str(data['current_observation']['dewpoint_c']))
		self.property('Current.OutlookIcon', '%s.png' % weathercode) # xbmc translates it to Current.ConditionIcon
		self.property('Current.FanartCode', weathercode)
		for count, item in enumerate(data['forecast']['simpleforecast']['forecastday']):
			weathercode = WEATHER_CODES[os.path.splitext(os.path.basename(item['icon_url']))[0]]
			self.property('Day%i.Title' % count, item['date']['weekday'])
			self.property('Day%i.HighTemp' % count, str(item['high']['celsius']))
			self.property('Day%i.LowTemp' % count, str(item['low']['celsius']))
			self.property('Day%i.Outlook' % count, item['conditions'])
			self.property('Day%i.OutlookIcon' % count, '%s.png' % weathercode)
			self.property('Day%i.FanartCode' % count, weathercode)
			if count == self.NODAYS:
				break
		# forecast properties
		self.property('Forecast.IsFetched', 'true')
		self.property('Forecast.City', data['current_observation']['display_location']['city'])
		self.property('Forecast.State', data['current_observation']['display_location']['state_name'])
		self.property('Forecast.Country', data['current_observation']['display_location']['country'])
		update = time.localtime(float(data['current_observation']['observation_epoch']))
		local = time.localtime(float(data['current_observation']['local_epoch']))
		if self.FDATE[1] == 'd':
			updatedate = WEEKDAY[update[6]] + ' ' + str(update[2]) + ' ' + MONTH[update[1]] + ' ' + str(update[0])
			localdate = WEEKDAY[local[6]] + ' ' + str(local[2]) + ' ' + MONTH[local[1]] + ' ' + str(local[0])
		elif self.FDATE[1] == 'm':
			updatedate = WEEKDAY[update[6]] + ' ' + MONTH[update[1]] + ' ' + str(update[2]) + ', ' + str(update[0])
			localdate = WEEKDAY[local[6]] + ' ' + str(local[2]) + ' ' + MONTH[local[1]] + ' ' + str(local[0])
		else:
			updatedate = WEEKDAY[update[6]] + ' ' + str(update[0]) + ' ' + MONTH[update[1]] + ' ' + str(update[2])
			localdate = WEEKDAY[local[6]] + ' ' + str(local[0]) + ' ' + MONTH[local[1]] + ' ' + str(local[2])
		if self.FTIME != '/':
			updatetime = time.strftime('%I:%M%p', update)
			localtime = time.strftime('%I:%M%p', local)
		else:
			updatetime = time.strftime('%H:%M', update)
			localtime = time.strftime('%H:%M', local)
		self.property('Forecast.Updated', updatedate + ' - ' + updatetime)
		# current properties
		self.property('Current.IsFetched', 'true')
		self.property('Current.LocalTime', localtime)
		self.property('Current.LocalDate', localdate)
		self.property('Current.WindDegree', str(data['current_observation']['wind_degrees']) + u'°')
		self.property('Current.SolarRadiation', str(data['current_observation']['solarradiation']))

		if 'F' in self.UTMPRT:
			self.property('Current.Pressure', data['current_observation']['pressure_in'] + ' inHg')
			self.property('Current.Precipitation', data['current_observation']['precip_1hr_in'] + ' in')
			self.property('Current.HeatIndex', str(data['current_observation']['heat_index_f']) + self.UTMPRT)
			self.property('Current.WindChill', str(data['current_observation']['windchill_f']) + self.UTMPRT)
		else:
			self.property('Current.Pressure', data['current_observation']['pressure_mb'] + ' mb')
			self.property('Current.Precipitation', data['current_observation']['precip_1hr_metric'] + ' mm')
			self.property('Current.HeatIndex', str(data['current_observation']['heat_index_c']) + self.UTMPRT)
			self.property('Current.WindChill', str(data['current_observation']['windchill_c']) + self.UTMPRT)

		if  self.USPEED == 'mph':
			self.property('Current.Visibility', data['current_observation']['visibility_mi'] + ' mi')
			self.property('Current.WindGust', str(data['current_observation']['wind_gust_mph']) + ' ' +  self.USPEED)
		else:
			self.property('Current.Visibility', data['current_observation']['visibility_km'] + ' km')
			self.property('Current.WindGust', str(data['current_observation']['wind_gust_kph']) + ' ' +  self.USPEED)
		# today properties
		self.property('Today.IsFetched', 'true')
		if self.FTIME != '/':
			AM = unicode(self.FTIME.split('/')[0], encoding='utf-8')
			PM = unicode(self.FTIME.split('/')[1], encoding='utf-8')
			hour = int(data['moon_phase']['sunrise']['hour']) % 24
			isam = (hour >= 0) and (hour < 12)
			if isam:
				hour = ('12' if (hour == 0) else '%02d' % (hour))
				self.property('Today.Sunrise', hour.lstrip('0') + ':' + data['moon_phase']['sunrise']['minute'] + ' ' + AM)
			else:
				hour = ('12' if (hour == 12) else '%02d' % (hour - 12))
				self.property('Today.Sunrise', hour.lstrip('0') + ':' + data['moon_phase']['sunrise']['minute'] + ' ' + PM)
			hour = int(data['moon_phase']['sunset']['hour']) % 24
			isam = (hour >= 0) and (hour < 12)
			if isam:
				hour = ('12' if (hour == 0) else '%02d' % (hour))
				self.property('Today.Sunset', hour.lstrip('0') + ':' + data['moon_phase']['sunset']['minute'] + ' ' + AM)
			else:
				hour = ('12' if (hour == 12) else '%02d' % (hour - 12))
				self.property('Today.Sunset', hour.lstrip('0') + ':' + data['moon_phase']['sunset']['minute'] + ' ' + PM)
		else:
			self.property('Today.Sunrise', data['moon_phase']['sunrise']['hour'] + ':' + data['moon_phase']['sunrise']['minute'])
			self.property('Today.Sunset', data['moon_phase']['sunset']['hour'] + ':' + data['moon_phase']['sunset']['minute'])
		self.property('Today.moonphase', MOONPHASE(self._toint(data['moon_phase']['ageOfMoon']), self._toint(data['moon_phase']['percentIlluminated'])))
		if 'F' in self.UTMPRT:
			self.property('Today.AvgHighTemperature', data['almanac']['temp_high']['normal']['F'] + self.UTMPRT)
			self.property('Today.AvgLowTemperature', data['almanac']['temp_low']['normal']['F'] + self.UTMPRT)
			try:
				self.property('Today.RecordHighTemperature', data['almanac']['temp_high']['record']['F'] + self.UTMPRT)
				self.property('Today.RecordLowTemperature', data['almanac']['temp_low']['record']['F'] + self.UTMPRT)
			except:
				self.property('Today.RecordHighTemperature', '')
				self.property('Today.RecordLowTemperature', '')
		else:
			self.property('Today.AvgHighTemperature', data['almanac']['temp_high']['normal']['C'] + self.UTMPRT)
			self.property('Today.AvgLowTemperature', data['almanac']['temp_low']['normal']['C'] + self.UTMPRT)
			try:
				self.property('Today.RecordHighTemperature', data['almanac']['temp_high']['record']['C'] + self.UTMPRT)
				self.property('Today.RecordLowTemperature', data['almanac']['temp_low']['record']['C'] + self.UTMPRT)
			except:
				self.property('Today.RecordHighTemperature', '')
				self.property('Today.RecordLowTemperature', '')
		try:
			self.property('Today.RecordHighYear', data['almanac']['temp_high']['recordyear'])
			self.property('Today.RecordLowYear', data['almanac']['temp_low']['recordyear'])
		except:
			self.property('Today.RecordHighYear', '')
			self.property('Today.RecordLowYear', '')
		# daily properties
		self.property('Daily.IsFetched', 'true')
		for count, item in enumerate(data['forecast']['simpleforecast']['forecastday']):
			weathercode = WEATHER_CODES[os.path.splitext(os.path.basename(item['icon_url']))[0]]
			self.property('Daily.%i.LongDay' % (count + 1), item['date']['weekday'])
			self.property('Daily.%i.ShortDay' % (count + 1), item['date']['weekday_short'])
			if self.FDATE[1] == 'd':
				self.property('Daily.%i.LongDate' % (count + 1), str(item['date']['day']) + ' ' + item['date']['monthname'])
				self.property('Daily.%i.ShortDate' % (count + 1), str(item['date']['day']) + ' ' + MONTH[item['date']['month']])
			else:
				self.property('Daily.%i.LongDate' % (count + 1), item['date']['monthname'] + ' ' + str(item['date']['day']))
				self.property('Daily.%i.ShortDate' % (count + 1), MONTH[item['date']['month']] + ' ' + str(item['date']['day']))
			self.property('Daily.%i.Outlook' % (count + 1), item['conditions'])
			self.property('Daily.%i.OutlookIcon' % (count + 1), self.ICON % weathercode)
			self.property('Daily.%i.FanartCode' % (count + 1), weathercode)
			if  self.USPEED == 'mph':
				self.property('Daily.%i.WindSpeed' % (count + 1), str(item['avewind']['mph']) + ' ' +  self.USPEED)
				self.property('Daily.%i.MaxWind' % (count + 1), str(item['maxwind']['mph']) + ' ' +  self.USPEED)
			elif  self.USPEED == 'Beaufort':
				self.property('Daily.%i.WindSpeed' % (count + 1), KPHTOBFT(item['avewind']['kph']))
				self.property('Daily.%i.MaxWind' % (count + 1), KPHTOBFT(item['maxwind']['kph']))
			else:
				self.property('Daily.%i.WindSpeed' % (count + 1), str(item['avewind']['kph']) + ' ' +  self.USPEED)
				self.property('Daily.%i.MaxWind' % (count + 1), str(item['maxwind']['kph']) + ' ' +  self.USPEED)
			self.property('Daily.%i.WindDirection' % (count + 1), item['avewind']['dir'])
			self.property('Daily.%i.ShortWindDirection' % (count + 1), item['avewind']['dir'])
			self.property('Daily.%i.WindDegree' % (count + 1), str(item['avewind']['degrees']) + u'°')
			self.property('Daily.%i.Humidity' % (count + 1), str(item['avehumidity']) + '%')
			self.property('Daily.%i.MinHumidity' % (count + 1), str(item['minhumidity']) + '%')
			self.property('Daily.%i.MaxHumidity' % (count + 1), str(item['maxhumidity']) + '%')
			if 'F' in self.UTMPRT:
				self.property('Daily.%i.HighTemperature' % (count + 1), str(item['high']['fahrenheit']) + self.UTMPRT)
				self.property('Daily.%i.LowTemperature' % (count + 1), str(item['low']['fahrenheit']) + self.UTMPRT)
				self.property('Daily.%i.LongOutlookDay' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count]['fcttext'])
				self.property('Daily.%i.LongOutlookNight' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count + 1]['fcttext'])
				self.property('Daily.%i.Precipitation' % (count + 1), str(item['qpf_day']['in']) + ' in')
				self.property('Daily.%i.Snow' % (count + 1), str(item['snow_day']['in']) + ' in')
			else:
				self.property('Daily.%i.HighTemperature' % (count + 1), str(item['high']['celsius']) + self.UTMPRT)
				self.property('Daily.%i.LowTemperature' % (count + 1), str(item['low']['celsius']) + self.UTMPRT)
				self.property('Daily.%i.LongOutlookDay' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count]['fcttext_metric'])
				self.property('Daily.%i.LongOutlookNight' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count + 1]['fcttext_metric'])
				self.property('Daily.%i.Precipitation' % (count + 1), str(item['qpf_day']['mm']) + ' mm')
				self.property('Daily.%i.Snow' % (count + 1), str(item['snow_day']['cm']) + ' mm')
			self.property('Daily.%i.ChancePrecipitation' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count]['pop'] + '%')
		# weekend properties
		self.property('Weekend.IsFetched', 'true')
		if commons.setting('Weekend') == 2:
			weekend = [4, 5]
		elif commons.setting('Weekend') == 1:
			weekend = [5, 6]
		else:
			weekend = [6, 7]
		count = 0
		for item in data['forecast']['simpleforecast']['forecastday']:
			if date(item['date']['year'], item['date']['month'], item['date']['day']).isoweekday() in weekend:
				weathercode = WEATHER_CODES[os.path.splitext(os.path.basename(item['icon_url']))[0]]
				self.property('Weekend.%i.LongDay' % (count + 1), item['date']['weekday'])
				self.property('Weekend.%i.ShortDay' % (count + 1), item['date']['weekday_short'])
				if self.FDATE[1] == 'd':
					self.property('Weekend.%i.LongDate' % (count + 1), str(item['date']['day']) + ' ' + item['date']['monthname'])
					self.property('Weekend.%i.ShortDate' % (count + 1), str(item['date']['day']) + ' ' + MONTH[item['date']['month']])
				else:
					self.property('Weekend.%i.LongDate' % (count + 1), item['date']['monthname'] + ' ' + str(item['date']['day']))
					self.property('Weekend.%i.ShortDate' % (count + 1), MONTH[item['date']['month']] + ' ' + str(item['date']['day']))
				self.property('Weekend.%i.Outlook' % (count + 1), item['conditions'])
				self.property('Weekend.%i.OutlookIcon' % (count + 1), self.ICON % weathercode)
				self.property('Weekend.%i.FanartCode' % (count + 1), weathercode)
				if  self.USPEED == 'mph':
					self.property('Weekend.%i.WindSpeed' % (count + 1), str(item['avewind']['mph']) + ' ' +  self.USPEED)
					self.property('Weekend.%i.MaxWind' % (count + 1), str(item['maxwind']['mph']) + ' ' +  self.USPEED)
				elif  self.USPEED == 'Beaufort':
					self.property('Weekend.%i.WindSpeed' % (count + 1), KPHTOBFT(item['avewind']['kph']))
					self.property('Weekend.%i.MaxWind' % (count + 1), KPHTOBFT(item['maxwind']['kph']))
				else:
					self.property('Weekend.%i.WindSpeed' % (count + 1), str(item['avewind']['kph']) + ' ' +  self.USPEED)
					self.property('Weekend.%i.MaxWind' % (count + 1), str(item['maxwind']['kph']) + ' ' +  self.USPEED)
				self.property('Weekend.%i.WindDirection' % (count + 1), item['avewind']['dir'])
				self.property('Weekend.%i.ShortWindDirection' % (count + 1), item['avewind']['dir'])
				self.property('Weekend.%i.WindDegree' % (count + 1), str(item['avewind']['degrees']) + u'°')
				self.property('Weekend.%i.Humidity' % (count + 1), str(item['avehumidity']) + '%')
				self.property('Weekend.%i.MinHumidity' % (count + 1), str(item['minhumidity']) + '%')
				self.property('Weekend.%i.MaxHumidity' % (count + 1), str(item['maxhumidity']) + '%')
				self.property('Weekend.%i.ChancePrecipitation' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count]['pop'] + '%')
				if 'F' in self.UTMPRT:
					self.property('Weekend.%i.HighTemperature' % (count + 1), str(item['high']['fahrenheit']) + self.UTMPRT)
					self.property('Weekend.%i.LowTemperature' % (count + 1), str(item['low']['fahrenheit']) + self.UTMPRT)
					self.property('Weekend.%i.Precipitation' % (count + 1), str(item['qpf_day']['in']) + ' in')
					self.property('Weekend.%i.Snow' % (count + 1), str(item['snow_day']['in']) + ' in')
					self.property('Weekend.%i.LongOutlookDay' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count]['fcttext'])
					self.property('Weekend.%i.LongOutlookNight' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count + 1]['fcttext'])
				else:
					self.property('Weekend.%i.HighTemperature' % (count + 1), str(item['high']['celsius']) + self.UTMPRT)
					self.property('Weekend.%i.LowTemperature' % (count + 1), str(item['low']['celsius']) + self.UTMPRT)
					self.property('Weekend.%i.Precipitation' % (count + 1), str(item['qpf_day']['mm']) + ' mm')
					self.property('Weekend.%i.Snow' % (count + 1), str(item['snow_day']['cm']) + ' mm')
					if data['current_observation']['display_location']['country'] == 'UK': # for the brits
						dfcast_e = data['forecast']['txt_forecast']['forecastday'][2 * count]['fcttext'].split('.')
						dfcast_m = data['forecast']['txt_forecast']['forecastday'][2 * count]['fcttext_metric'].split('.')
						nfcast_e = data['forecast']['txt_forecast']['forecastday'][2 * count + 1]['fcttext'].split('.')
						nfcast_m = data['forecast']['txt_forecast']['forecastday'][2 * count + 1]['fcttext_metric'].split('.')
						for field in dfcast_e:
							wind = ''
							if field.endswith('mph'): # find windspeed in mph
								wind = field
								break
						for field in dfcast_m:
							if field.endswith('km/h'): # find windspeed in km/h
								dfcast_m[dfcast_m.index(field)] = wind # replace windspeed in km/h with windspeed in mph
								break
						for field in nfcast_e:
							wind = ''
							if field.endswith('mph'): # find windspeed in mph
								wind = field
								break
						for field in nfcast_m:
							if field.endswith('km/h'): # find windspeed in km/h
								nfcast_m[nfcast_m.index(field)] = wind # replace windspeed in km/h with windspeed in mph
								break
						self.property('Weekend.%i.LongOutlookDay' % (count + 1), '. '.join(dfcast_m))
						self.property('Weekend.%i.LongOutlookNight' % (count + 1), '. '.join(nfcast_m))
					else:
						self.property('Weekend.%i.LongOutlookDay' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count]['fcttext_metric'])
						self.property('Weekend.%i.LongOutlookNight' % (count + 1), data['forecast']['txt_forecast']['forecastday'][2 * count + 1]['fcttext_metric'])
				count += 1
				if count == 2:
					break
		# 36 hour properties
		self.property('36Hour.IsFetched', 'true')
		for count, item in enumerate(data['forecast']['txt_forecast']['forecastday']):
			weathercode = WEATHER_CODES[os.path.splitext(os.path.basename(item['icon_url']))[0]]
			if 'F' in self.UTMPRT:
				try:
					fcast = item['fcttext'].split('.')
					for line in fcast:
						if line.endswith('F'):
							self.property('36Hour.%i.TemperatureHeading' % (count + 1), line.rsplit(' ', 1)[0])
							self.property('36Hour.%i.Temperature' % (count + 1), line.rsplit(' ', 1)[1])
							break
				except:
					self.property('36Hour.%i.TemperatureHeading' % (count + 1), '')
					self.property('36Hour.%i.Temperature' % (count + 1), '')
				self.property('36Hour.%i.Forecast' % (count + 1), item['fcttext'])
			else:
				try:
					fcast = item['fcttext_metric'].split('.')
					for line in fcast:
						if line.endswith('C'):
							self.property('36Hour.%i.TemperatureHeading' % (count + 1), line.rsplit(' ', 1)[0])
							self.property('36Hour.%i.Temperature' % (count + 1), line.rsplit(' ', 1)[1])
							break
				except:
					self.property('36Hour.%i.TemperatureHeading' % (count + 1), '')
					self.property('36Hour.%i.Temperature' % (count + 1), '')
				if data['current_observation']['display_location']['country'] == 'UK': # for the brits
					fcast_e = item['fcttext'].split('.')
					for field in fcast_e:
						if field.endswith('mph'): # find windspeed in mph
							wind = field
							break
					for field in fcast:
						if field.endswith('km/h'): # find windspeed in km/h
							fcast[fcast.index(field)] = wind # replace windspeed in km/h with windspeed in mph
							break
					self.property('36Hour.%i.Forecast' % (count + 1), '. '.join(fcast))
				else:
					self.property('36Hour.%i.Forecast' % (count + 1), item['fcttext_metric'])
			self.property('36Hour.%i.Heading' % (count + 1), item['title'])
			self.property('36Hour.%i.ChancePrecipitation' % (count + 1), item['pop'] + '%')
			self.property('36Hour.%i.OutlookIcon' % (count + 1), self.ICON % weathercode)
			self.property('36Hour.%i.FanartCode' % (count + 1), weathercode)
			if count == 2:
				break
		# hourly properties
		self.property('Hourly.IsFetched', 'true')
		for count, item in enumerate(data['hourly_forecast']):
			weathercode = WEATHER_CODES[os.path.splitext(os.path.basename(item['icon_url']))[0]]
			if self.FTIME != '/':
				self.property('Hourly.%i.Time' % (count + 1), item['FCTTIME']['civil'])
			else:
				self.property('Hourly.%i.Time' % (count + 1), item['FCTTIME']['hour_padded'] + ':' + item['FCTTIME']['min'])
			if self.FDATE[1] == 'd':
				self.property('Hourly.%i.ShortDate' % (count + 1), item['FCTTIME']['mday_padded'] + ' ' + item['FCTTIME']['month_name_abbrev'])
				self.property('Hourly.%i.LongDate' % (count + 1), item['FCTTIME']['mday_padded'] + ' ' + item['FCTTIME']['month_name'])
			else:
				self.property('Hourly.%i.ShortDate' % (count + 1), item['FCTTIME']['month_name_abbrev'] + ' ' + item['FCTTIME']['mday_padded'])
				self.property('Hourly.%i.LongDate' % (count + 1), item['FCTTIME']['month_name'] + ' ' + item['FCTTIME']['mday_padded'])
			if 'F' in self.UTMPRT:
				self.property('Hourly.%i.Temperature' % (count + 1), item['temp']['english'] + self.UTMPRT)
				self.property('Hourly.%i.DewPoint' % (count + 1), item['dewpoint']['english'] + self.UTMPRT)
				self.property('Hourly.%i.FeelsLike' % (count + 1), item['feelslike']['english'] + self.UTMPRT)
				self.property('Hourly.%i.Precipitation' % (count + 1), item['qpf']['english'] + ' in')
				self.property('Hourly.%i.Snow' % (count + 1), item['snow']['english'] + ' in')
				self.property('Hourly.%i.HeatIndex' % (count + 1), item['heatindex']['english'] + self.UTMPRT)
				self.property('Hourly.%i.WindChill' % (count + 1), item['windchill']['english'] + self.UTMPRT)
				self.property('Hourly.%i.Mslp' % (count + 1), item['mslp']['english'] + ' inHg')
			else:
				self.property('Hourly.%i.Temperature' % (count + 1), item['temp']['metric'] + self.UTMPRT)
				self.property('Hourly.%i.DewPoint' % (count + 1), item['dewpoint']['metric'] + self.UTMPRT)
				self.property('Hourly.%i.FeelsLike' % (count + 1), item['feelslike']['metric'] + self.UTMPRT)
				self.property('Hourly.%i.Precipitation' % (count + 1), item['qpf']['metric'] + ' mm')
				self.property('Hourly.%i.Snow' % (count + 1), item['snow']['metric'] + ' mm')
				self.property('Hourly.%i.HeatIndex' % (count + 1), item['heatindex']['metric'] + self.UTMPRT)
				self.property('Hourly.%i.WindChill' % (count + 1), item['windchill']['metric'] + self.UTMPRT)
				self.property('Hourly.%i.Mslp' % (count + 1), item['mslp']['metric'] + ' inHg')
			if  self.USPEED == 'mph':
				self.property('Hourly.%i.WindSpeed' % (count + 1), item['wspd']['english'] + ' ' +  self.USPEED)
			elif  self.USPEED == 'Beaufort':
				self.property('Hourly.%i.WindSpeed' % (count + 1), KPHTOBFT(int(item['wspd']['metric'])))
			else:
				self.property('Hourly.%i.WindSpeed' % (count + 1), item['wspd']['metric'] + ' ' +  self.USPEED)
			self.property('Hourly.%i.WindDirection' % (count + 1), item['wdir']['dir'])
			self.property('Hourly.%i.ShortWindDirection' % (count + 1), item['wdir']['dir'])
			self.property('Hourly.%i.WindDegree' % (count + 1), item['wdir']['degrees'] + u'°')
			self.property('Hourly.%i.Humidity' % (count + 1), item['humidity'] + '%')
			self.property('Hourly.%i.UVIndex' % (count + 1), item['uvi'])
			self.property('Hourly.%i.ChancePrecipitation' % (count + 1), item['pop'] + '%')
			self.property('Hourly.%i.Outlook' % (count + 1), item['condition'])
			self.property('Hourly.%i.OutlookIcon' % (count + 1), self.ICON % weathercode)
			self.property('Hourly.%i.FanartCode' % (count + 1), weathercode)
		# alert properties
		self.property('Alerts.IsFetched', 'true')
		if str(data['alerts']) != '[]':
			rss = ''
			alerts = ''
			for count, item in enumerate(data['alerts']):
				description = self._recode(item['description']) # workaround: wunderground provides a corrupt alerts message
				message = self._recode(item['message']) # workaround: wunderground provides a corrupt alerts message
				self.property('Alerts.%i.Description' % (count + 1), description)
				self.property('Alerts.%i.Message' % (count + 1), message)
				self.property('Alerts.%i.StartDate' % (count + 1), item['date'])
				self.property('Alerts.%i.EndDate' % (count + 1), item['expires'])
				self.property('Alerts.%i.Significance' % (count + 1), SEVERITY[item['significance']])
				rss = rss + description.replace('\n', '') + ' - '
				alerts = alerts + message + '[CR][CR]'
			self.property('Alerts.RSS', rss.rstrip(' - '))
			self.property('Alerts', alerts.rstrip('[CR][CR]'))
			self.property('Alerts.Count', str(count + 1))
		else:
			self.property('Alerts.RSS', '')
			self.property('Alerts', '')
			self.property('Alerts.Count', '0')
		# map properties
		self.property('Map.IsFetched', 'true')
		filelist = []
		locid = base64.b16encode(locid)
		addondir = os.path.join(commons.AddonPath().decode("utf-8"))
		mapdir = xbmc.translatePath('special://profile/addon_data/%s/map' % commons.AddonId())
		self.property('MapPath', addondir)
		if not xbmcvfs.exists(mapdir):
			xbmcvfs.mkdir(mapdir)
		dirs, filelist = xbmcvfs.listdir(mapdir)
		animate = commons.setting('Animate')
		for img in filelist:
			item = xbmc.translatePath('special://profile/addon_data/%s/map/%s' % (commons.AddonId(), img)).decode("utf-8")
			if animate:
				if (time.time() - os.path.getmtime(item) > 14400) or (not locid in item):
					xbmcvfs.delete(item)
			else:
				xbmcvfs.delete(item)
		zoom = commons.setting('Zoom')
		url = data['satellite']['image_url_ir4'].replace('width=300&height=300', 'width=640&height=360').replace('radius=75', 'radius=%i' % int(1000/zoom))
		commons.debug('Map url: %s' % url)
		try:
			req = urllib2.Request(url)
			req.add_header('Accept-encoding', 'gzip')
			response = urllib2.urlopen(req)
			if response.info().get('Content-Encoding') == 'gzip':
				buf = StringIO(response.read())
				compr = gzip.GzipFile(fileobj=buf)
				data = compr.read()
			else:
				data = response.read()
			response.close()
			commons.debug('Satellite image downloaded')
		except:
			data = ''
			commons.debug('Satellite image downloaded failed')
		if data != '':
			timestamp = time.strftime('%Y%m%d%H%M%S')
			mapfile = xbmc.translatePath('special://profile/addon_data/%s/map/%s-%s.png' % (commons.AddonId(), locid, timestamp)).decode("utf-8")
			try:
				tmpmap = open(mapfile, 'wb')
				tmpmap.write(data)
				tmpmap.close()
				self.property('MapPath', mapdir)
			except:
				commons.debug('Failed to save satellite image')

	def call(self, features, settings, query, fmt):
		url = 'http://api.wunderground.com/api/%s/%s/%s/q/%s.%s' % (commons.setting("License")[::-1], features, settings, query, fmt)
		try:
			req = urllib2.Request(url)
			req.add_header('Accept-encoding', 'gzip')
			response = urllib2.urlopen(req)
			if response.info().get('Content-Encoding') == 'gzip':
				buf = StringIO(response.read())
				compr = gzip.GzipFile(fileobj=buf)
				data = compr.read()
			else:
				data = response.read()
			response.close()
		except:
			data = ''
		return data
