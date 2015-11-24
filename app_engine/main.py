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

import league_website

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
    divisions = league_website.RetrieveLeagueWebsite().Standings().Divisions()
    template = JINJA_ENVIRONMENT.get_template('standings.html')
    self.response.write(template.render({"divisions": divisions}))
    
    #response = {
    #  "divisions": [MakeDivisionJson(d) for d in divisions]
    #}
    #self.response.headers['Content-Type'] = 'application/json'   
    #json.dump(response, self.response.out)

class CalculatedStandingsHandler(webapp2.RequestHandler):
  def get(self):
    matches = league_website.RetrieveLeagueWebsite().Matches()
    teams = collections.defaultdict(dict)
    standings = {}
    template = JINJA_ENVIRONMENT.get_template('schedule.html')
    self.response.write(template.render({"divisions": divisions}))

def MakeMatchJson(match):
  match_dict = {
    "time": match.time.isoformat(),
    "location": match.location,
    "teams": [match.team_1, match.team_2],
    "goals": [match.result_1, match.result_2]
  }
  return match_dict


class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    matches = league_website.RetrieveLeagueWebsite().Matches()
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
