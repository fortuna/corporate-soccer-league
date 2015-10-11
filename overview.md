
get scraped standings
- create:
  division {
    participating_team {
      team { team_id, name }
      wins, losses, points, ..._
  }
- get last updated time

get scraped schedule
- recon map recon_key -> team_id
- list of matches: time, participating_team_{1,2} = {team_id, goals}, winner = team_id

ScheduledMatch
- time
- location
- Participating teams

PastMatch : ScheduledMatch
- ParticipatingTeams
  - outcome: win, tie, lose
  - goals: #, None


# Output

if errors, output message and link to page.
output last updated date
if exists past match without update
  emit warning
for each division
  for each team, in order
    output name and published stats, ...
      if stats diverge from calculated, highlight
    output past matches
      <date> vs <team> W|L|T <g>-<g>|forfeit
    output upcomming matches
      <date> vs <team> - <time> @ <location>

