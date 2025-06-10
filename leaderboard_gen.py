import pandas as pd
from newscraper import get_leaderboard_dataframe
from datetime import datetime

# Fetch the leaderboard data directly from newscraper
df = get_leaderboard_dataframe()

# Output HTML file path
output_path = "index.html"

# Determine round columns
round_columns = [col for col in df.columns if col.startswith("Round")]

# Generate HTML table rows
rows_html = ""
for idx, row in df.iterrows():
    position = idx + 1
    team = row["Team"]
    total = int(row["Total"])
    round_scores = [
        f'<td class="">{int(row[col]) if row[col] != 0 else "<td class=\"empty-cell\">-</td>"}</td>'
        if row[col] != 0 else '<td class="empty-cell">-</td>'
        for col in round_columns
    ]
    rank_class = f"rank-{position}" if position <= 3 else "rank"
    row_html = f"<tr class=\"hover:bg-slate-700 transition-all duration-150\"><td><div class=\"rank {rank_class}\">{position}</div></td><td class=\"\">{team}</td>{''.join(round_scores)}<td><span class=\"total-score\">{total}</span></td></tr>"
    rows_html += row_html + "\n"

# Generate final HTML
html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>
  <title>Robotics Competition Leaderboard</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
  <style>
    body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #e2e8f0; }}
    .glow {{ text-shadow: 0 0 8px rgba(56, 189, 248, 0.6); }}
    .rank {{ font-weight: bold; font-size: 1rem; background-color: #334155; border-radius: 9999px; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; margin: auto; }}
    .rank-1 {{ background: linear-gradient(135deg, #fde047, #f59e0b); box-shadow: 0 0 10px rgba(245,158,11,0.5); }}
    .rank-2 {{ background: linear-gradient(135deg, #e5e7eb, #9ca3af); box-shadow: 0 0 10px rgba(156,163,175,0.5); }}
    .rank-3 {{ background: linear-gradient(135deg, #f97316, #b45309); box-shadow: 0 0 10px rgba(180,83,9,0.5); }}
    .total-score {{ font-weight: bold; background-color: #14b8a6; color: white; padding: 4px 12px; border-radius: 8px; display: inline-block; }}
    .empty-cell {{ color: #64748b; font-style: italic; }}
  </style>
</head>
<body class=\"p-6\">
  <div class=\"max-w-7xl mx-auto\">
    <h1 class=\"text-3xl font-bold mb-6 glow text-center\">🏆 Robotics Competition Leaderboard</h1>
    <div class=\"overflow-x-auto rounded-lg shadow-md\">
      <table class=\"min-w-full divide-y divide-slate-700 bg-slate-800 text-sm text-center\">
        <thead class=\"bg-slate-900 text-slate-300 uppercase tracking-wider text-xs\">
          <tr>
            <th class=\"px-4 py-3\">Position</th>
            <th class=\"px-4 py-3\">Team Name</th>
            {''.join([f'<th class=\"px-4 py-3\">{col}</th>' for col in round_columns])}
            <th class=\"px-4 py-3\">Total</th>
          </tr>
        </thead>
        <tbody class=\"divide-y divide-slate-700\">
          {rows_html}
        </tbody>
      </table>
      <div class=\"text-center text-slate-400 text-xs mt-6\">
        Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
      </div>
    </div>
  </div>
</body>
</html>
"""

# Write to file
with open(output_path, "w") as f:
    f.write(html)

print(f"Leaderboard HTML written to {output_path}")
