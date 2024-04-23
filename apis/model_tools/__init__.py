class Tool_Property:
  def __init__(self, name, type, description):
    self.name = name
    self.type = type
    self.description = description
  
  def jasonify (self):
    return {
      self.name: {
        'type': self.type,
        'description': self.description
      }
    }

class Tool:

  def __init__(self, name, description):
    self.name = name

from .yahoo_finance import * 

# get_ticker_info, tool_def
