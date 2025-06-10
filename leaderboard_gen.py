import pandas as pd
from newscraper import get_leaderboard_dataframe
from datetime import datetime, timezone


def generate_leaderboard():
    df = get_leaderboard_dataframe()
    df["Total"] = df[[col for col in df.columns if col.startswith("Round")]].sum(axis=1)

    # Rank with ties (same score = same rank)
    df["Position"] = df["Total"].rank(method="min", ascending=False).astype(int)
    df = df.sort_values(by=["Total", "Team"], ascending=[False, True])

    print(df.head())
    print("Shape:", df.shape)

    round_columns = [col for col in df.columns if col.startswith("Round")]
    output_path = "index.html"

    # Generate HTML table rows
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

    # Final HTML output
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Mars Robotics Leaderboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{
      font-family: 'Inter', sans-serif;
      color: #e2e8f0;
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
          <img src="logo.png" alt="ERC Logo" class="w-80 h-auto mb-4" />
          <h1 class="text-3xl font-bold glow text-center">Live (kinda) Leaderboard</h1>
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
        <div class="text-center text-slate-400 text-xs mt-6">
          Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""
    with open(output_path, "w") as f:
        f.write(html)

    print(f"✅ Leaderboard written to {output_path}")


if __name__ == "__main__":
    generate_leaderboard()