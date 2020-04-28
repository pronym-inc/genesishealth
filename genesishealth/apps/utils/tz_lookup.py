import pytz

import googlemaps

from django.conf import settings


def timezone_from_location_string(location_str):
    client = googlemaps.Client(settings.GOOGLE_MAPS_TIMEZONE_API_KEY)
    geocoded = client.geocode(location_str)
    if len(geocoded) == 0:
        return
    location_data = geocoded[0]['geometry']['location']
    coord_str = "{lat},{lng}".format(**location_data)
    google_tz_info = googlemaps.timezone.timezone(client, coord_str)
    if google_tz_info and 'timeZoneId' in google_tz_info:
        return pytz.timezone(google_tz_info['timeZoneId'])
