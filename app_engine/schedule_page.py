import collections
import re
from datetime import datetime
from lxml import etree

# DATA MODEL

class Team(object):
  def __init__(self, team_id):
    self._id = team_id
    self._aliases = collections.Counter()
  
  def Name(self):
    return self._aliases.most_common(1)[0][0]

  def Id(self):
    return self._id
    
  def Aliases(self):
    return self._aliases


class TeamRepository(object):
  def __init__(self):
    self._teams = {}
    self._redirects = {}
  
  def GetCanonicalId(self, team_id):
    next_id = self._redirects.get(team_id, team_id)
    if next_id == team_id:
      return team_id
    canonical_id = self.GetCanonicalId(next_id)
    if canonical_id != next_id:
      self._redirects[team_id] = canonical_id
    return canonical_id

  def GetTeam(self, team_id):
    team = self._teams.get(self.GetCanonicalId(team_id))
    if not team:
      team = Team(team_id)
      self._teams[team_id] = team
    return team
  
  def MergeTeams(self, source_id, target_id):
    source = self.GetTeam(source_id)
    target = self.GetTeam(target_id)
    target.Aliases().update(source.Aliases())
    self._redirects[source_id] = target_id
    del(self._teams[source.Id()])
    
  def NumTeams(self):
    return len(self._teams)
  
  def Teams(self):
    return self._teams.values()

MatchEntry = collections.namedtuple('MatchEntry', ['time', 'location', 'teams', 'goals'])

def MakeTeamId(name):
  return re.sub("\s", "", name).lower()


def IdsHaveSameDigits(id1, id2):
  return collections.Counter(id1) == collections.Counter(id2)

def GetBestMatch(source_id, target_ids):
  best_id = None
  best_score = -1.0
  for target_id in target_ids:
    if target_id == source_id: continue
    target_counter = collections.Counter(target_id)
    source_counter = collections.Counter(source_id)
    score = (float(sum((target_counter & source_counter).values())) /
             sum((target_counter | source_counter).values()))
    if score > best_score:
      best_id = target_id
      best_score = score
  return best_id

# PARSING

def _GetNodeText(node):
  text = etree.tostring(node, method="text", encoding='utf-8')
  if text is not None:
    text = text.replace("\xc2\xa0", " ").strip()
  return text

_TimeText = re.compile('[0-9]{1,2}:[0-9]{2}')

ParsedTeamsNode = collections.namedtuple('ParsedTeamsNode',
   ['team_1', 'result_1', 'team_2', 'result_2'])
ParsedMatch = collections.namedtuple('ParsedMatch',
    ['time', 'location', 'team_id_1', 'result_1', 'team_id_2', 'result_2'])

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


class ScrapedSchedule(object):
  def __init__(self, page_html):
    html_parser = etree.HTMLParser()
    tree = etree.parse(page_html, parser=html_parser)
    parsed_matches = []
    round_date = None
    teams = TeamRepository()
    for row in tree.xpath("//div[@id = 'textbox']//table[col]/tr"):
      cells = row.xpath(".//td")
      if len(cells) == 1:
        round_date = datetime.strptime(_GetNodeText(cells[0]), "%A, %B %d").date().replace(year=datetime.now().year)
      elif len(cells) >= 3:
        location_text = _GetNodeText(cells[0])
        if not location_text: continue
        
        time_text = _GetNodeText(cells[1])
        if not time_text: continue

        parsed_teams = ParseTeamsNode(cells[2])
        team_1 = teams.GetTeam(MakeTeamId(parsed_teams.team_1))
        team_1.Aliases()[parsed_teams.team_1] += 1
        
        team_2 = teams.GetTeam(MakeTeamId(parsed_teams.team_2))
        team_2.Aliases()[parsed_teams.team_2] += 1

        clean_time_text = _TimeText.search(time_text).group(0)
        match_time = datetime.strptime(clean_time_text + "pm", "%I:%M%p").time()
        parsed_matches.append(ParsedMatch(
            time=datetime.combine(round_date, match_time),
            location=location_text,
            team_id_1=team_1.Id(),
            result_1=parsed_teams.result_1,
            team_id_2=team_2.Id(),
            result_2=parsed_teams.result_2
        ))
    
    average_matches_per_team = 2.0 * len(parsed_matches) / teams.NumTeams()
    for team in list(teams.Teams()):
      num_matches = sum(team.Aliases().values())
      if num_matches >= average_matches_per_team - 1:
        continue
      target_id = GetBestMatch(team.Id(), [t.Id() for t in teams.Teams()])
      teams.MergeTeams(team.Id(), target_id)    

    self._matches = []
    for parsed_match in parsed_matches:
      goals = None
      if parsed_match.result_1 is not None or parsed_match.result_2 is not None:
        goals = [parsed_match.result_1, parsed_match.result_2]
      self._matches.append(MatchEntry(
        time=parsed_match.time,
        location=parsed_match.location,
        teams=[teams.GetTeam(parsed_match.team_id_1).Name(), teams.GetTeam(parsed_match.team_id_2).Name()],
        goals=goals))

  def MatchEntries(self):
    return self._matches


if __name__ == "__main__":
  import urllib
  # page_html = urllib.urlopen("http://corporateleague.com/soccer/schedwinter.html")
  page_html = open("../testdata/schedwinter.html")
  matches = ScrapedSchedule(page_html).MatchEntries()
  print matches
  
