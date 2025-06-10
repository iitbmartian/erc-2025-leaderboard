from newscraper import get_leaderboard_dataframe  # Make sure this is defined at module level
from datetime import datetime
from jinja2 import Template

def generate_leaderboard():
    df = get_leaderboard_dataframe().copy()

    if df.empty:
        print("No data available.")
        return

    # Group by team and sum numeric task columns to get total scores
    score_columns = [col for col in df.columns if col not in ["team", "round"]]
    team_scores = (
        df.groupby("team")[score_columns]
        .sum()
        .reset_index()
    )

    # Calculate total score and prepare rows
    team_scores["total"] = team_scores[score_columns].sum(axis=1)
    team_scores = team_scores.sort_values(by="total", ascending=False).reset_index(drop=True)
    team_scores["rank"] = team_scores.index + 1

    # Convert to dicts for templating
    team_rows = []
    for _, row in team_scores.iterrows():
        team_rows.append({
            "team": row["team"],
            "scores": [row[task] for task in score_columns],
            "total": row["total"],
            "rank": row["rank"]
        })

    # Martian visual block
    mars_header = """
    <div class="text-center mb-6">
        <img src="https://mars.nasa.gov/system/news_items/main_images/10512_PIA25284-Rover-stretch-final_800.jpg" alt="Mars Rover" class="mars-deco mb-2" />
        <h1 class="text-3xl font-bold glow">🚀 Mars Robotics Leaderboard</h1>
        <p class="text-sm text-slate-400 italic mt-1">Tracking the best teams on the red planet!</p>
    </div>
    <div class="overflow-x-auto rounded-lg shadow-md">
    """

    # Load and render HTML template
    with open("templates/index.html") as f:
        template = Template(f.read())

    rendered = template.render(
        tasks=score_columns,
        team_rows=team_rows,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        mars_header=mars_header
    )

    # Save to disk
    with open("docs/index.html", "w") as f:
        f.write(rendered)

if __name__ == "__main__":
    generate_leaderboard()
