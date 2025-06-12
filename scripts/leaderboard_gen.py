import pandas as pd
from newscraper import get_leaderboard_dataframe
from datetime import datetime, timezone


def generate_leaderboard(rounds_config=None):
    df = get_leaderboard_dataframe(rounds_config)
    df["Total"] = df[[col for col in df.columns if col.startswith("Round") or col not in ["Team", "Total"]]].sum(axis=1)

    # Rank with ties (same score = same rank)
    df["Position"] = df["Total"].rank(method="min", ascending=False).astype(int)
    df = df.sort_values(by=["Total", "Team"], ascending=[False, True])
    

    print(df.head())
    print("Shape:", df.shape)

    round_columns = [col for col in df.columns if col not in ["Team", "Total", "Position"]]


    rows_html = ""
    for _, row in df.iterrows():
        rank = row["Position"]
        team = row["Team"]
        total = int(row["Total"])
        round_scores = [
            f'<td>{int(row[col])}</td>' if row[col] != 0 else '<td class="empty-cell">-</td>'
            for col in round_columns
        ]
        rank_class = f"rank-{rank}" if rank <= 3 else "rank"
        row_html = f"""
        <tr class="hover:bg-slate-700 transition-all duration-150">
          <td><div class="rank {rank_class}">{rank}</div></td>
          <td>{team}</td>
          {''.join(round_scores)}
          <td><span class="total-score">{total}</span></td>
        </tr>
        """
        rows_html += row_html

    round_headers = ''.join([f'<th class="px-4 py-3">{col}</th>' for col in round_columns])

    # The final HTML output
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ERC-2025 Leaderboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
        body {{
          font-family: 'Inter', sans-serif;
          color: #e2e8f0;
          background: url('assets/mars.jpg') no-repeat center center fixed;
          background-size: cover;
        }}

    .rank {{
      font-weight: bold;
      font-size: 1rem;
      background-color: #334155;
      border-radius: 9999px;
      width: 35px;
      height: 35px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: auto;
    }}

    .rank-1 {{
      background: linear-gradient(135deg, #fde047, #f59e0b);
      box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
    }}

    .rank-2 {{
      background: linear-gradient(135deg, #e5e7eb, #9ca3af);
      box-shadow: 0 0 10px rgba(156, 163, 175, 0.5);
    }}

    .rank-3 {{
      background: linear-gradient(135deg, #f97316, #b45309);
      box-shadow: 0 0 10px rgba(180, 83, 9, 0.5);
    }}
    
  </style>
</head>
<body style="background-color: #FF7F50;">
  <div class="overlay">
    <div class="max-w-7xl mx-auto">
        <div class="flex flex-col items-center mb-6">
          <img src="assets/logo.png" alt="ERC Logo" class="w-80 h-auto mb-4" />
          <h1 class="text-5xl font-bold glow text-center">Live Leaderboard</h1>
        </div>

      <div class="overflow-x-auto rounded-lg shadow-md">
        <table class="min-w-full divide-y divide-slate-700 bg-slate-800 text-sm text-center">
          <thead class="bg-slate-900 text-slate-300 uppercase tracking-wider text-xs">
            <tr>
              <th class="px-4 py-3">Position</th>
              <th class="px-4 py-3">Team</th>
              {round_headers}
              <th class="px-4 py-3">Total</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700">
            {rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </div>


<!-- Animated Footer -->
<footer style="font-family: inherit; font-size: 1.1em; text-align: center; margin-top: 1em;">
        <div class="text-center text-white-400 text-l mt-6">
          Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
  Made with 
  <span class="inline-block animate-bounce mx-1">❤️</span>
  by IITB Mars Rover Team
</footer>

</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    # Example usage with custom rounds configuration
    # You can pass rounds_config to customize which rounds to include
    # Format: (round_number, round_name, url, team_col, score_col)

    # Default behavior (if you don't pass rounds_config):
    rounds = [
            (1, "Qualification",
             "https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_1/qualification_results.md",
             "Team name", "Sum"),
            (2, "Connectivity Test",
             "https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_2/connectivity_test_1_results.md",
             "Team name", "Connectivity Test score"),
            (6, "Jury Points",
             "https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_6/jury_points.md", "Team name",
             "Point count"),
            (7, "Social Excellence",
             "https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_6/social_excellence.md",
             "Team name", "Point count"),
        ]
    generate_leaderboard(rounds)

    # Or customize like this:
    # custom_rounds = [
    #     (1, "Qualification Round", "https://example.com/round1.md", "Team name", "Sum"),
    #     (2, "Technical Challenge", "https://example.com/round2.md", "Team name", "Score"),
    # ]
    # generate_leaderboard(custom_rounds)
