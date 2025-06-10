from newscraper import get_all_team_data  # Ensure this function exists in newscraper.py
from datetime import datetime
from jinja2 import Template

def generate_leaderboard():
    data = get_all_team_data()

    if not data:
        print("No data found.")
        return

    all_tasks = sorted({task for team in data for task in team['scores'].keys()})

    for team in data:
        team['score_list'] = [team['scores'].get(task) for task in all_tasks]
        team['total'] = sum(score for score in team['score_list'] if score is not None)

    data.sort(key=lambda x: x['total'], reverse=True)
    for i, team in enumerate(data):
        team['rank'] = i + 1

    mars_header = """
    <div class="text-center mb-6">
        <img src="https://mars.nasa.gov/system/news_items/main_images/10512_PIA25284-Rover-stretch-final_800.jpg" alt="Mars Rover" class="mars-deco mb-2" />
        <h1 class="text-3xl font-bold glow">🚀 Mars Robotics Leaderboard</h1>
        <p class="text-sm text-slate-400 italic mt-1">Tracking the best teams on the red planet!</p>
    </div>
    <div class="overflow-x-auto rounded-lg shadow-md">
    """

    with open("templates/index.html") as f:
        template = Template(f.read())

    rendered = template.render(
        tasks=all_tasks,
        team_rows=data,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        mars_header=mars_header
    )

    with open("docs/index.html", "w") as f:
        f.write(rendered)

if __name__ == "__main__":
    generate_leaderboard()
