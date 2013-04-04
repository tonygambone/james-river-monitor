import logging, webapp2
from datetime import datetime, timedelta

from tz import Eastern
from lib import Status, Key

from google.appengine.api import memcache
from google.appengine.api import urlfetch

class DataHandler(webapp2.RequestHandler):
  """Cron job handler to fetch & cache data"""
  def get(self):
    if not self.request.headers.has_key('X-AppEngine-Cron'):
      logging.warn('Non-cron request to DataHandler')
      self.response.set_status(403)
      return      
    try:
      self.response.out.write(self.fetch_and_cache())
    except:
      logging.exception('Error occurred while fetching')
      self.response.set_status(500)

  def fetch_and_cache(self):
    """Fetch the current status and update the cache"""
    status = self.fetch_status()
    memcache.set(Key.WaterLevelStatus, {
        'status': status,
        'time': datetime.now(Eastern)
      })
    memcache.delete(Key.MainOutput)
    return status

  def fetch_status(self):
    """Determines the current status based the maximum of all data points
    from the current date."""
    import urllib2
    from xml.dom.minidom import parseString
    from decimal import Decimal
    # fetch
    result = urlfetch.fetch("http://water.weather.gov/ahps2/hydrograph_to_xml.php?gage=rmdv2&output=xml", deadline=60*10);
    # parse
    doc = parseString(result.content)
    todaystr = datetime.utcnow().date().isoformat()
    logging.info("Matching on " + todaystr)
    values = [Decimal(n.parentNode.getElementsByTagName('primary')[0].childNodes[0].nodeValue)
                for n in doc.getElementsByTagName('valid')
                if todaystr in n.childNodes[0].nodeValue]
    logging.info("Got " + str(len(values)) + " data points")
    # decide
    maximum = max(values)
    logging.info("Maximum is " + str(maximum))
    if maximum >= 9:
      return Status.Permit
    elif maximum >= 5:
      return Status.Vest
    else:
      return Status.OK

class WarmupHandler(webapp2.RequestHandler):
  """Handler to warm up initial data"""
  def get(self):
    if (memcache.get(Key.WaterLevelStatus) is None):
      logging.info("Warming up")
      DataHandler().fetch_and_cache()