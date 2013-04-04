#!/usr/bin/env python

import webapp2, jinja2, os, logging
from datetime import datetime

from tz import Eastern
from data import DataHandler, WarmupHandler
from lib import Status, Key, cache

from google.appengine.api import memcache

j = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainHandler(webapp2.RequestHandler):
  """Handles web requests for the main page of the application"""
  def get(self):
    try:
      self.response.out.write(self.get_content())
    except:
      logging.exception('Error occurred while processing the request')
      from google.appengine.api import mail
      import sys, traceback
      et, ev, etb = sys.exc_info()
      mail.send_mail(sender="James River Monitor App <tonygambone@gmail.com>",
        to="Tony Gambone <tonygambone@gmail.com>",
        subject="Application Error",
        body=''.join(traceback.format_exception(et, ev, etb)))
      self.response.out.write(
        """Something went wrong, sorry. Check the
        <a href="http://water.weather.gov/ahps2/hydrograph.php?wfo=akq&gage=rmdv2">river levels</a>
        and bring a vest if the water is higher than 5 feet. If it's over 9, you can't go without a
        permit.
        """)

  @cache(Key.MainOutput, 1800)
  def get_content(self):
    """Get the HTML output for the main page."""
    result = memcache.get(Key.WaterLevelStatus)
    if result is None:
      DataHandler().fetch_and_cache()
      result = memcache.get(Key.WaterLevelStatus)
    status = result['status']
    if status == Status.Permit:
      logging.info("Status is Permit")
      text = "not without a permit"
    elif status == Status.Vest:
      logging.info("Status is Vest")
      text = "yes, but bring a vest"
    else:
      logging.info("Status is OK")
      text = "sure, go for it"
    v = {
      'text': text,
      'class': 'status'+str(status),
      'time': result['time'].strftime('%B %d at %I:%M %p %Z')
    }
    t = j.get_template('main.html')
    return t.render(v)

app = webapp2.WSGIApplication([
  ('/', MainHandler),
  ('/fetch', DataHandler),
  ('/_ah/warmup', WarmupHandler)
  ], debug=True)
