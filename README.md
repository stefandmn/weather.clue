# Clue Weather for Kodi

**Clue Weather** package is designed to become main weather plugin for 
_Kodi_ within **Clue** system or an alternative weather add-on for any _Kodi_ 
instance. The package comes with three content providers the default one being 
**Yahoo**, alternatively might be used **OpenWeatherMap** and the last one is
**Dark Sky** weather provider. Additionally, can be developed and plugged 
other sources using built-in plugin object model (see `ContentProvider` class
definition).

Development, testing and deployment activities are driven by CCM process (Clue 
Configuration Management), built over GNU `make` utility. To see all make rules
try `make help`.

_Enjoy!_


## Details for Skinners or Plugin Developers

Below are described the main skin properties published by the content provides
through the addon execution flow. All values returned by the addon will include 
their units.


### Weather Labels

#### Current

* Current.IsFetched
* Current.Location
* Current.Latitude
* Current.Longitude
* Current.Condition
* Current.Temperature
* Current.Wind
* Current.WindDirection
* Current.Humidity
* Current.FeelsLike
* Current.DewPoint
* Current.UVIndex
* Current.FanartCode
* Current.LowTemperature
* Current.HighTemperature
* Current.Pressure
* Current.OutlookIcon
* Current.Visibility

* Forecast.City
* Forecast.Country
* Forecast.Latitude
* Forecast.Longitude
* Forecast.Updated

#### Today

* Today.IsFetched
* Today.Sunrise
* Today.Sunset
* Today.HighTemperature
* Today.LowTemperature

#### Day [0-6]

* Day%i.Title
* Day%i.HighTemp
* Day%i.LowTemp
* Day%i.Outlook
* Day%i.OutlookIcon
* Day%i.FanartCode

* Daily.%i.IsFetched
* Daily.%i.Title
* Daily.%i.HighTemp
* Daily.%i.LowTemp
* Daily.%i.Outlook
* Daily.%i.OutlookIcon
* Daily.%i.FanartCode
* Daily.%i.WindSpeed
* Daily.%i.WindDirection
* Daily.%i.Humidity
* Daily.%i.DewPoint
* Daily.%i.UVIndex
* Daily.%i.Visibility
* Daily.%i.HighTemperature
* Daily.%i.LowTemperature


#### Hourly[0-16] 

* Hourly.IsFetched
* Hourly.%i.Time
* Hourly.%i.LongDate
* Hourly.%i.ShortDate
* Hourly.%i.Outlook
* Hourly.%i.OutlookIcon
* Hourly.%i.FanartCode
* Hourly.%i.WindSpeed
* Hourly.%i.WindDirection
* Hourly.%i.Humidity
* Hourly.%i.Pressure
* Hourly.%i.FeelsLike
* Hourly.%i.Temperature
* Hourly.%i.DewPoint
* Hourly.%i.UVIndex
* Hourly.%i.Visibility

#### Alerts [1-5]

* Alerts.IsFetched
* Alerts.Text
* Alerts.%i.Title
* Alerts.%i.Description
* Alerts.%i.Expires

#### Weather provider

* WeatherProvider
* WeatherProviderLogo
