# -*- coding: utf-8 -*-

import sys
import socket
import common
from .abstract import ContentProvider


class DarkSky(ContentProvider):
	LOCATION = 'https://darksky.net/geo?q=%s'
	FORECAST = 'https://api.darksky.net/forecast/%s/%s?exclude=minutely&lang=%s&units=%s'
	ART_DATA = {
		"clear-day": "Clear/Day",
		"clear-night": "Clear/Night",
		"rain": "Rain/Neutral",
		"snow": "Snow/Neutral",
		"sleet": "Rain/Showers/Neutral",
		"wind":	"Others/Windy",
		"fog": "Fog/Neutral",
		"cloudy": "Cloudy/Neutral",
		"partly-cloudy-day": "Cloudy/Partly/Day",
		"partly-cloudy-night": "Cloudy/Partly/Night",
		"hail": "Rain/Mix/Neutral",
		"thunderstorm": "Rain/Night",
		"tornado": "Others/Tornado"
		}


	def __init__(self):
		socket.setdefaulttimeout(10)


	def _fanart(self, code):
		"""Detect and return fanart code"""
		return self.ART_BASE[self.ART_DATA[code]]


	def name(self):
		return "Dark Sky"


	def code(self):
		return "darksky"


	def validate(self):
		response = common.urlcall("https://api.darksky.net/forecast/%s/37.8267,-122.4233?exclude=minutely,hourly,daily,alerts,flags" %self.apikey)
		if response is not None:
			response = self._parse(response)
			if "error" in response:
				raise RuntimeError(response["error"])
		elif response is None:
			raise RuntimeError("No content provided due to an HTTP error")


	def geoip(self):
		loc = ''
		locid = ''
		data = self.ipinfo()
		if data is not None and "city"in data:
			geoloc = data["city"]
			if "regionName"in data:
				geoloc += "," + data["regionName"]
			if "country" in data:
				geoloc += "," + data["country"]
			common.debug('Identifying GeoIP location: %s' % geoloc, self.code())
			url = self.LOCATION % ("\"" + geoloc + "\"")
			data = self._call(url)
			common.debug('Found location data: %s' % data, self.code())
			if data is not None and "latitude" in data:
				self.coordinates(data["latitude"], data["longitude"])
				loc = geoloc.replace(",", "-")
				locid = str(self.latitude) + "," + str(self.longitude)
		return loc, str(locid)


	def location(self, loc):
		locs = []
		locids = []
		common.debug('Searching for location: %s' % loc, self.code())
		url = self.LOCATION % ("\"" + loc + "\"")
		data = self._call(url)
		common.debug('Found location data: %s' % data, self.code())
		if data is not None and "latitude" in data:
			self.coordinates(data["latitude"], data["longitude"])
			location = loc
			locationid = str(self.latitude) + "," + str(self.longitude)
			locs.append(location)
			locids.append(str(locationid))
		return locs, locids


	def forecast(self, loc, locid):
		common.debug('Weather forecast for location: %s' % locid, self.code())
		url = self.FORECAST %(self.apikey, locid, self.lang, "si")
		data = self._call(url)
		# Current weather forecast
		if data is not None and "currently" in data:
			item = data['currently']
			# Current - standard
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Location', loc)
			self.skinproperty('Current.Latitude', data['latitude'])
			self.skinproperty('Current.Longitude', data['longitude'])
			self.skinproperty('Current.Condition', common.utf8(item["summary"]).capitalize())
			self.skinproperty('Current.Temperature', self._2temperature(item['temperature']))
			self.skinproperty('Current.Wind', self._2speed(item['windSpeed'], iu='mps'))
			self.skinproperty('Current.WindDirection', item['windBearing'], '°') if "windBearing" in item else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', 100*item['humidity'])
			self.skinproperty('Current.Pressure', self._2pressure(item['pressure'], um=True))
			self.skinproperty('Current.OutlookIcon', '%s.png' % self._fanart(item["icon"]))
			self.skinproperty('Current.FanartCode', self._fanart(item["icon"]))
			self.skinproperty('Current.LocalTime', self._2shtime(item['time']))
			self.skinproperty('Current.LocalDate', self._2shdate(item['time']))
			self.skinproperty('Current.FeelsLike', self._2temperature(item['apparentTemperature'], um=True))
			self.skinproperty('Current.Visibility', self._2distance(item['visibility'], um=True))
			self.skinproperty('Current.DewPoint', item['dewPoint'])
			self.skinproperty('Current.UVIndex', item['uvIndex'])
			# Forecast - extended
			self.skinproperty('Forecast.City', loc)
			self.skinproperty('Forecast.Country', '')
			self.skinproperty('Forecast.Latitude', data['latitude'])
			self.skinproperty('Forecast.Longitude', data['longitude'])
			self.skinproperty('Forecast.Updated', self._2shdatetime(item['time']))
		# Today forecast
		if data is not None and "daily" in data and "data" in data['daily'] and len(data['daily']['data']) > 0:
			item = data['daily']['data'][0]
			self.skinproperty('Today.IsFetched', 'true')
			self.skinproperty('Today.Sunrise', self._2shtime(item['sunriseTime']))
			self.skinproperty('Today.Sunset', self._2shtime(item['sunsetTime']))
			self.skinproperty('Today.HighTemperature', self._2temperature(item['temperatureHigh'], um=True))
			self.skinproperty('Today.LowTemperature', self._2temperature(item['temperatureLow'], um=True))
		# Daily weather forecast
		if data is not None and "daily" in data and "data" in data['daily'] and len(data['daily']['data']) > 1:
			count = 0
			index = 0
			self.skinproperty('Daily.IsFetched', 'true')
			for item in data['daily']['data']:
				if index >= 1:
					# Standard
					self.skinproperty('Day%i.Title' % count, self._2lnday(item['time']))
					self.skinproperty('Day%i.HighTemp' % count, self._2temperature(item['temperatureHigh'], iu='c',um=True))
					self.skinproperty('Day%i.LowTemp' % count, self._2temperature(item['temperatureLow'], iu='c',um=True))
					self.skinproperty('Day%i.Outlook' % count, common.utf8(item["summary"]).capitalize())
					self.skinproperty('Day%i.OutlookIcon' % count, '%s.png' % self._fanart(item["icon"]))
					self.skinproperty('Day%i.FanartCode' % count, self._fanart(item["icon"]))
					# Extended
					self.skinproperty('Daily.%i.ShortDay' % count, self._2shday(item['time']))
					self.skinproperty('Daily.%i.LongDay' % count, self._2lnday(item['time']))
					self.skinproperty('Daily.%i.ShortDate' % count, self._2shday(item['time']))
					self.skinproperty('Daily.%i.LongDate' % count, self._2lnday(item['time']))
					self.skinproperty('Daily.%i.Outlook' % count, common.utf8(item["summary"]).capitalize())
					self.skinproperty('Daily.%i.OutlookIcon' % count, '%s.png' % self._fanart(item["icon"]))
					self.skinproperty('Daily.%i.FanartCode' % count, self._fanart(item["icon"]))
					self.skinproperty('Daily.%i.Condition' % count, common.utf8(item["summary"]).capitalize())
					self.skinproperty('Daily.%i.Wind' % count, self._2speed(item['windSpeed']))
					self.skinproperty('Daily.%i.WindDirection' % count, item['windBearing'], '°') if "windBearing" in item else self.skinproperty('Day.%i.WindDirection' % count)
					self.skinproperty('Daily.%i.Humidity' % count, 100*item['humidity'])
					self.skinproperty('Daily.%i.Pressure' % count, self._2pressure(item['pressure'],um=True))
					self.skinproperty('Daily.%i.DewPoint' % count, item['dewPoint'])
					self.skinproperty('Daily.%i.UVIndex' % count, item['uvIndex'])
					self.skinproperty('Daily.%i.HighTemperature' % count, self._2temperature(item['temperatureHigh'], iu='c',um=True))
					self.skinproperty('Daily.%i.LowTemperature' % count, self._2temperature(item['temperatureLow'], iu='c',um=True))
					count += 1
				index += 1
		# Hourly weather forecast
		if data is not None and "hourly" in data and "data" in data['hourly'] and len(data['hourly']['data']) > 0:
			count = 0
			self.skinproperty('Hourly.IsFetched', 'true')
			for item in data['hourly']['data']:
				self.skinproperty('Hourly.%i.Time' % count, self._2shtime(item['time']))
				self.skinproperty('Hourly.%i.ShortDate' % count, self._2shdate(item['time']))
				self.skinproperty('Hourly.%i.Condition' % count, common.utf8(item["summary"]).capitalize())
				self.skinproperty('Hourly.%i.Temperature' % count, self._2temperature(item['temperature'], iu='c',um=True))
				self.skinproperty('Hourly.%i.Outlook' % count, common.utf8(item["summary"]).capitalize())
				self.skinproperty('Hourly.%i.OutlookIcon' % count, '%s.png' % self._fanart(item["icon"]))
				self.skinproperty('Hourly.%i.FanartCode' % count, self._fanart(item["icon"]))
				self.skinproperty('Hourly.%i.Wind' % count, self._2speed(item['windSpeed']))
				self.skinproperty('Hourly.%i.WindDirection' % count, item['windBearing'], '°') if "windBearing" in item else self.skinproperty('Hourly%i.WindDirection' % count)
				self.skinproperty('Hourly.%i.Humidity' % count, 100*item['humidity'])
				self.skinproperty('Hourly.%i.Pressure' % count, self._2pressure(item['pressure']),um=True)
				self.skinproperty('Hourly.%i.DewPoint' % count, item['dewPoint'])
				self.skinproperty('Hourly.%i.UVIndex' % count, item['uvIndex'])
				count += 1
		# Alerts weather forecast
		if data is not None and "alerts" in data and len(data['alerts']) > 0:
			count = 0
			text = ''
			self.skinproperty('Alerts.IsFetched', 'true')
			for item in data['alerts']:
				title = item['title'].encode('utf-8', 'ignore').replace('\n', ' ')
				description = item['description'].encode('utf-8', 'ignore').replace('\n', ' ')
				expire = self._2shdatetime(item['expires'])
				self.skinproperty('Alerts.%i.Title' % count, title)
				self.skinproperty('Alerts.%i.Description' % count, description)
				self.skinproperty('Alerts.%i.Expires' % count, expire)
				text += " • " if text != "" else ""
				text += "[B]" + title + "[/B] - " + description + " (" + expire + ")"
				count += 1
			self.skinproperty('Alerts.Text', text)
