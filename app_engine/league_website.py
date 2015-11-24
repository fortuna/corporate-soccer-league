import collections
import os
import re
import urllib

from datetime import datetime
from lxml import etree


class LeagueWebsite(object):
  def __init__(self, standings, matches):
    self._standings = standings
    self._matches = matches
  
  def Standings(self):
    return self._standings
    
  def Matches(self):
    return self._matches


Match = collections.namedtuple('Match',
    ['time', 'location', 'team_1', 'result_1', 'team_2', 'result_2'])


def RetrieveLeagueWebsite():
  base_url = os.environ.get("CORPORATE_LEAGUE_URL", "http://corporateleague.com/soccer")
  standings = ScrapedStandings(urllib.urlopen(base_url + "/corpstandings.html"))
  matches = ParseMatches(urllib.urlopen(base_url + "/schedwinter.html"))
  return LeagueWebsite(standings, matches)


def _GetNodeText(node):
  text = etree.tostring(node, method="text", encoding='utf-8')
  if text is not None:
    text = text.replace("\xc2\xa0", " ").strip()
  return text


def _GetCleanName(node):
  return " ".join(_GetNodeText(node).split())

_TimeText = re.compile('[0-9]{1,2}:[0-9]{2}')

ParsedTeamsNode = collections.namedtuple('ParsedTeamsNode',
   ['team_1', 'result_1', 'team_2', 'result_2'])


def ParseTeamsNode(node):
  teams_segments = []
  for segment in node.xpath(".//text()"):
    clean_segment = re.sub("\s+", " ", segment).strip()
    split_segment = re.split("(^| )([vV])( |$)", clean_segment)
    for s in split_segment:
      if s.strip(): teams_segments.append(s)
  segment = iter(teams_segments)
  team_1 = segment.next()
  result_1 = segment.next()
  if result_1 == "v" or result_1 == "V":
    result_1 = None
  else:
    segment.next()
  team_2 = segment.next()
  result_2 = next(segment, None)
  return ParsedTeamsNode(team_1, result_1, team_2, result_2)


def ParseMatches(schedule_html):
  html_parser = etree.HTMLParser()
  tree = etree.parse(schedule_html, parser=html_parser)
  matches = []
  round_date = None
  for row in tree.xpath("//div[@id = 'textbox']//table[col]/tr"):
    cells = row.xpath(".//td")
    if len(cells) == 1:
      try:
        round_date = datetime.strptime(_GetNodeText(cells[0]), "%A, %B %d").date().replace(year=datetime.now().year)
      except ValueError:
        continue
    elif len(cells) >= 3:
      location_text = _GetNodeText(cells[0])
      if not location_text: continue
      
      time_text = _GetNodeText(cells[1])
      if not time_text: continue
      clean_time_text = _TimeText.search(time_text).group(0)
      match_time = datetime.strptime(clean_time_text + "pm", "%I:%M%p").time()

      parsed_teams = ParseTeamsNode(cells[2])
      matches.append(Match(
          time=datetime.combine(round_date, match_time),
          location=location_text,
          team_1=parsed_teams.team_1,
          result_1=parsed_teams.result_1,
          team_2=parsed_teams.team_2,
          result_2=parsed_teams.result_2
      ))
  return matches


Division = collections.namedtuple('Division', ['name', 'teams'])
TeamEntry = collections.namedtuple('TeamEntry', ['name', 'wins', 'ties', 'losses', 'points'])


class ScrapedStandings(object):
  def __init__(self, page_html):
    self._last_update = None
    self._divisions = []

    html_parser = etree.HTMLParser()
    tree = etree.parse(page_html, parser=html_parser)
    current_division = None
    last_update_match = re.search("\S+ [0-9]{1,2}",
        _GetNodeText(tree.xpath("//table[col]//tr")[0]))
    if last_update_match:
      last_update_str = last_update_match.group(0)
      self._last_update = datetime.strptime(last_update_str, "%B %d").date().replace(year=datetime.now().year)
    for row in tree.xpath("//table[col]//tr")[1:]:
      cells = row.xpath(".//td")
      if len(cells) == 1:
        division_name = _GetCleanName(cells[0])
        if not division_name: continue
        current_division = Division(name=division_name, teams=[])
        self._divisions.append(current_division)
      else:
        team_name = _GetCleanName(cells[0])
        if not team_name or team_name == 'TEAM': continue
        wins = int(_GetNodeText(cells[1]))
        ties = int(_GetNodeText(cells[5]))
        losses = int(_GetNodeText(cells[3]))
        points = int(_GetNodeText(cells[6]))
        current_division.teams.append(TeamEntry(
          name=team_name, wins=wins, ties=ties, losses=losses, points=points
        ))
        
  def LastUpdate(self):
    return self._last_update

  def Divisions(self):
    return self._divisions


if __name__ == "__main__":
  website = RetrieveLeagueWebsite()
  print website.Matches()
  print website.Standings().LastUpdate()
  
