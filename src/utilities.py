# -*- coding: utf-8 -*-

import gzip
import urllib2
import Commons as commons
from StringIO import StringIO

#http://www.wunderground.com/weather/api/d/docs?d=language-support
LANG = {'afrikaans': 'AF',
		'albanian': 'AL',
		'amharic': 'EN', # AM is n/a, use AR or EN?
		'arabic': 'AR',
		'armenian': 'HY',
		'azerbaijani': 'AZ',
		'basque': 'EU',
		'belarusian': 'BY',
		'bosnian': 'CR', # BS is n/a, use CR or SR?
		'bulgarian': 'BU',
		'burmese': 'MY',
		'catalan': 'CA',
		'chinese (simple)': 'CN',
		'chinese (traditional)': 'TW',
		'croatian': 'CR',
		'czech': 'CZ',
		'danish': 'DK',
		'dutch': 'NL',
		'english': 'LI',
		'english (us)': 'EN',
		'english (australia)': 'LI',
		'english (new zealand)': 'LI',
		'esperanto': 'EO',
		'estonian': 'ET',
		'faroese': 'DK', # FO is n/a, use DK
		'finnish': 'FI',
		'french': 'FR',
		'galician': 'GZ',
		'german': 'DL',
		'greek': 'GR',
		'georgian': 'KA',
		'hebrew': 'IL',
		'hindi (devanagiri)': 'HI',
		'hungarian': 'HU',
		'icelandic': 'IS',
		'indonesian': 'ID',
		'italian': 'IT',
		'japanese': 'JP',
		'korean': 'KR',
		'latvian': 'LV',
		'lithuanian': 'LT',
		'macedonian': 'MK',
		'malay': 'EN', # MS is n/a, use EN
		'malayalam': 'EN', # ML is n/a, use EN
		'maltese': 'MT',
		'maori': 'MI',
		'norwegian': 'NO',
		'ossetic': 'EN', # OS is n/a, use EN
		'persian': 'FA',
		'persian (iran)': 'FA',
		'polish': 'PL',
		'portuguese': 'BR',
		'portuguese (brazil)': 'BR',
		'romanian': 'RO',
		'russian': 'RU',
		'serbian': 'SR',
		'serbian (cyrillic)': 'SR',
		'slovak': 'SK',
		'slovenian': 'SL',
		'spanish': 'SP',
		'spanish (argentina)': 'SP',
		'spanish (mexico)': 'SP',
		'swedish': 'SW',
		'tajik': 'FA', # TG is n/a, use FA or EN?
		'tamil (india)': 'EN', # TA is n/a, use EN
		'telugu': 'EN', # TE is n/a, use EN
		'thai': 'TH',
		'turkish': 'TU',
		'ukrainian': 'UA',
		'uzbek': 'UZ',
		'vietnamese': 'VU',
		'welsh': 'CY'}

WEATHER_CODES = {'chanceflurries': '41',
				 'chancerain': '39',
				 'chancesleet': '6',
				 'chancesnow': '41',
				 'chancetstorms': '38',
				 'clear': '32',
				 'cloudy': '26',
				 'flurries': '13',
				 'fog': '20',
				 'hazy': '21',
				 'mostlycloudy': '28',
				 'mostlysunny': '34',
				 'partlycloudy': '30',
				 'partlysunny': '34',
				 'sleet': '18',
				 'rain': '11',
				 'snow': '42',
				 'sunny': '32',
				 'tstorms': '38',
				 'unknown': 'na',
				 '': 'na',
				 'nt_chanceflurries': '46',
				 'nt_chancerain': '45',
				 'nt_chancesleet': '45',
				 'nt_chancesnow': '46',
				 'nt_chancetstorms': '47',
				 'nt_clear': '31',
				 'nt_cloudy': '27',
				 'nt_flurries': '46',
				 'nt_fog': '20',
				 'nt_hazy': '21',
				 'nt_mostlycloudy': '27',
				 'nt_mostlysunny': '33',
				 'nt_partlycloudy': '29',
				 'nt_partlysunny': '33',
				 'nt_sleet': '45',
				 'nt_rain': '45',
				 'nt_snow': '46',
				 'nt_sunny': '31',
				 'nt_tstorms': '47',
				 'nt_unknown': 'na',
				 'nt_': 'na'}

MONTH = {1: commons.translate(51),
		 2: commons.translate(52),
		 3: commons.translate(53),
		 4: commons.translate(54),
		 5: commons.translate(55),
		 6: commons.translate(56),
		 7: commons.translate(57),
		 8: commons.translate(58),
		 9: commons.translate(59),
		 10: commons.translate(60),
		 11: commons.translate(61),
		 12: commons.translate(62)}

WEEKDAY = {0: commons.translate(41),
		   1: commons.translate(42),
		   2: commons.translate(43),
		   3: commons.translate(44),
		   4: commons.translate(45),
		   5: commons.translate(46),
		   6: commons.translate(47)}

SEVERITY = {'W': commons.translate(32510),
			'A': commons.translate(32511),
			'Y': commons.translate(32512),
			'S': commons.translate(32513),
			'O': commons.translate(32514),
			'F': commons.translate(32515),
			'N': commons.translate(32516),
			'L': '', # no idea
			'': ''}

def MOONPHASE(age, percent):
	if (percent == 0) and (age == 0):
		phase = commons.translate(32501)
	elif (age < 17) and (age > 0) and (percent > 0) and (percent < 50):
		phase = commons.translate(32502)
	elif (age < 17) and (age > 0) and (percent == 50):
		phase = commons.translate(32503)
	elif (age < 17) and (age > 0) and (percent > 50) and (percent < 100):
		phase = commons.translate(32504)
	elif (age > 0) and (percent == 100):
		phase = commons.translate(32505)
	elif (age > 15) and (percent < 100) and (percent > 50):
		phase = commons.translate(32506)
	elif (age > 15) and (percent == 50):
		phase = commons.translate(32507)
	elif (age > 15) and (percent < 50) and (percent > 0):
		phase = commons.translate(32508)
	else:
		phase = ''
	return phase


def KPHTOBFT(spd):
	if (spd < 1.0):
		bft = '0'
	elif (spd >= 1.0) and (spd < 5.6):
		bft = '1'
	elif (spd >= 5.6) and (spd < 12.0):
		bft = '2'
	elif (spd >= 12.0) and (spd < 20.0):
		bft = '3'
	elif (spd >= 20.0) and (spd < 29.0):
		bft = '4'
	elif (spd >= 29.0) and (spd < 39.0):
		bft = '5'
	elif (spd >= 39.0) and (spd < 50.0):
		bft = '6'
	elif (spd >= 50.0) and (spd < 62.0):
		bft = '7'
	elif (spd >= 62.0) and (spd < 75.0):
		bft = '8'
	elif (spd >= 75.0) and (spd < 89.0):
		bft = '9'
	elif (spd >= 89.0) and (spd < 103.0):
		bft = '10'
	elif (spd >= 103.0) and (spd < 118.0):
		bft = '11'
	elif (spd >= 118.0):
		bft = '12'
	else:
		bft = ''
	return bft
