import pandas as pd
from newscraper import get_leaderboard_dataframe
from datetime import datetime

def generate_leaderboard():
    df = get_leaderboard_dataframe()
    df = df.sort_values(by="Total", ascending=False).reset_index(drop=True)

    output_path = "index.html"
    round_columns = [col for col in df.columns if col.startswith("Round")]

    # Generate HTML rows
    rows_html = ""
    for idx, row in df.iterrows():
        position = idx + 1
        team = row["Team"]
        total = int(row["Total"])
        round_scores = [
            f'<td>{int(row[col])}</td>' if row[col] != 0 else '<td class="empty-cell">-</td>'
            for col in round_columns
        ]
        rank_class = f"rank-{position}" if position <= 3 else "rank"
        row_html = f"""
        <tr class="hover:bg-slate-700 transition-all duration-150">
          <td><div class="rank {rank_class}">{position}</div></td>
          <td>{team}</td>
          {''.join(round_scores)}
          <td><span class="total-score">{total}</span></td>
        </tr>
        """
        rows_html += row_html

    # Generate round headers
    round_headers = ''.join([f'<th class="px-4 py-3">{col}</th>' for col in round_columns])

    # Final HTML
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
      background: url('logo.png') no-repeat center center fixed;
      background-size: cover;
      color: #e2e8f0;
    }}
    .overlay {{
      background-color: rgba(15, 23, 42, 0.7);
      min-height: 100vh;
      padding: 2rem;
    }}
    .glow {{
      text-shadow: 0 0 10px rgba(255, 100, 100, 0.6);
      animation: glowAnimation 1.5s ease-in-out infinite;
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
    .total-score {{
      font-weight: bold;
      background-color: #ef4444;
      color: white;
      padding: 4px 12px;
      border-radius: 8px;
      display: inline-block;
    }}
    .empty-cell {{
      color: #64748b;
      font-style: italic;
    }}
    .mars-deco {{
      max-width: 120px;
      margin: 0 auto;
    }}
    @keyframes glowAnimation {{
      0% {{ text-shadow: 0 0 10px rgba(255, 100, 100, 0.6); }}
      50% {{ text-shadow: 0 0 20px rgba(255, 200, 200, 1); }}
      100% {{ text-shadow: 0 0 10px rgba(255, 100, 100, 0.6); }}
    }}
  </style>
</head>
<body>
  <div class="overlay">
    <div class="max-w-7xl mx-auto">
      <div class="text-center mb-6">
        <img src="logo.png"/>
        <h1 class="text-3xl font-bold glow">🚀 Mars Robotics Leaderboard</h1>
        <p class="text-sm text-slate-400 italic mt-1">Tracking the best teams on the red planet!</p>
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
          Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
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
