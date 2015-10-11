#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import collections
import jinja2
import json
import os
import urllib
import webapp2

import schedule_page
import standings_page

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def MakeDivisionJson(division):
  def MakeTeamJson(team):
    return {
      "name": team.name,
      "wins": team.wins,
      "ties": team.ties,
      "losses": team.losses,
      "games_played": team.wins + team.ties + team.losses,
      "points_retrieved": team.points,
      "points_calculated": 3 * team.wins + team.ties
    }
  return {
    "name": division.name,
    "teams": [MakeTeamJson(t) for t in division.teams]
  }

class StandingsHandler(webapp2.RequestHandler):
  def get(self):
    divisions = standings_page.ScrapedStandings(
        urllib.urlopen("http://corporateleague.com/soccer/corpstandings.html")).Divisions()
    template = JINJA_ENVIRONMENT.get_template('standings.html')
    self.response.write(template.render({"divisions": divisions}))
    
    #response = {
    #  "divisions": [MakeDivisionJson(d) for d in divisions]
    #}
    #self.response.headers['Content-Type'] = 'application/json'   
    #json.dump(response, self.response.out)

class CalculatedStandingsHandler(webapp2.RequestHandler):
  def get(self):
    matches = schedule_page.ScrapedSchedule(
      urllib.urlopen('http://corporateleague.com/soccer/schedwinter.html')).MatchEntries()
    teams = collections.defaultdict(dict)
    standings = {}
    template = JINJA_ENVIRONMENT.get_template('schedule.html')
    self.response.write(template.render({"divisions": divisions}))

def MakeMatchJson(match):
  match_dict = {
    "time": match.time.isoformat(),
    "location": match.location,
    "teams": match.teams,
  }
  if match.goals:
    match_dict["goals"] = match.goals
  return match_dict

class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    matches = schedule_page.ScrapedSchedule(
      urllib.urlopen('http://corporateleague.com/soccer/schedwinter.html')).MatchEntries()
    response = {
      "matches": [MakeMatchJson(m) for m in matches]
    }
    self.response.headers['Content-Type'] = 'application/json'
    json.dump(response, self.response.out)
    


app = webapp2.WSGIApplication([
  ('/', StandingsHandler),
  ('/standings', StandingsHandler),  
  ('/calculated_standings', CalculatedStandingsHandler),  
  ('/schedule', ScheduleHandler),  
], debug=True)
