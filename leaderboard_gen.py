import os
import json
from datetime import datetime
from collections import defaultdict
from jinja2 import Template

def generate_leaderboard(data_dir="data"):
    scores = defaultdict(lambda: defaultdict(int))
    teams = set()

    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            team = data.get("team_name")
            if not team:
                continue
            teams.add(team)
            for task, score in data.get("scores", {}).items():
                scores[team][task] = score

    all_tasks = set()
    for team_scores in scores.values():
        all_tasks.update(team_scores.keys())
    all_tasks = sorted(list(all_tasks))

    team_rows = []
    for team in teams:
        team_score = scores[team]
        total = sum(team_score.get(task, 0) for task in all_tasks)
        row = {
            "team": team,
            "scores": [team_score.get(task, None) for task in all_tasks],
            "total": total
        }
        team_rows.append(row)

    team_rows.sort(key=lambda x: x["total"], reverse=True)
    for idx, row in enumerate(team_rows):
        row["rank"] = idx + 1

    with open("templates/index.html") as f:
        template = Template(f.read())


    mars_header = """
    <div class="text-center mb-6">
        <img src="https://mars.nasa.gov/system/news_items/main_images/10512_PIA25284-Rover-stretch-final_800.jpg" alt="Mars Rover" class="mars-deco mb-2" />
        <h1 class="text-3xl font-bold glow">🚀 Mars Robotics Leaderboard</h1>
        <p class="text-sm text-slate-400 italic mt-1">Tracking the best teams on the red planet!</p>
    </div>
    <div class="overflow-x-auto rounded-lg shadow-md">
    """

    rendered = template.render(
        tasks=all_tasks,
        team_rows=team_rows,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        mars_header=mars_header
    )

    with open("docs/index.html", "w") as f:
        f.write(rendered)

if __name__ == "__main__":
    generate_leaderboard()
