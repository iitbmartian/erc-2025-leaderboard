This is the repository of the leaderboard website for the European Rover Challenge - 2025.

You can head on over the website by clicking [here](https://iitbmartian.github.io/erc-website/)
### Updating the leaderboard:

When the results for a round are announced, all you have to do is add the url and relevant column headings in this part of the leaderboard_gen.py code:

```
rounds = [
  
(1, "Qualification",  "https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_1/qualification_results.md",  "Team name", "Sum"),
..........

]
```

The webscraper has the following functionalities:
* Checks for duplicate team names and alternate, subtle difference in team names (Think Team A, A or A team).
* Maintains a canonical list of teams to tally all points across rounds.
* Handles cases where a team has been mentioned twice and appropriately adds points to their tally.