class Status:
  """Enum for river statuses"""
  OK, Vest, Permit = range(3)

class Key:
  WaterLevelStatus = 'WaterLevelStatus'
  MainOutput = 'MainOutput'

def cache(key, time=0):
    """Memcache memoization decorator"""
    from google.appengine.api import memcache
    def a(f):
      def b(*args, **kwargs):
        result = memcache.get(str(key))
        if result is None:
          result = f(*args, **kwargs)
          memcache.set(str(key), result, time=time)
        return result
      return b
    return a