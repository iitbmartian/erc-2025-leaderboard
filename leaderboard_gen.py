import csv
import os
from datetime import datetime

def create_sample_csv():
    """Create a sample CSV file with the leaderboard data"""
    csv_data = [
        ["Position", "Team Name", "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5", "Phase 6 Jury", "Social Excellence", "Total"],
        [1, "Sapienza Technology Team", 41, 20, "", "", "", 4, 15, 80],
        [2, "SHUNYA", 39, 20, "", "", "", 7, "", 66],
        [3, "IITB Mars Rover Team", 38, 20, "", "", "", 5, "", 63],
        [4, "CRISS Robotics", 37, 8, "", "", "", 15, "", 60],
        [5, "Inferno DTU", 37, 20, "", "", "", 2, "", 59],
    ]
    with open('leaderboard.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    print("✅ Sample CSV created: leaderboard.csv")

def csv_to_html(csv_file="leaderboard.csv", html_file="index.html"):
    """Convert CSV to Tailwind-styled HTML leaderboard"""
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)

    headers = rows[0]
    data_rows = rows[1:]
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Robotics Competition Leaderboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{
      font-family: 'Inter', sans-serif;
      background-color: #0f172a;
      color: #e2e8f0;
    }}
    .glow {{
      text-shadow: 0 0 8px rgba(56, 189, 248, 0.6);
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
    .rank-1 {{ background: linear-gradient(135deg, #fde047, #f59e0b); box-shadow: 0 0 10px rgba(245,158,11,0.5); }}
    .rank-2 {{ background: linear-gradient(135deg, #e5e7eb, #9ca3af); box-shadow: 0 0 10px rgba(156,163,175,0.5); }}
    .rank-3 {{ background: linear-gradient(135deg, #f97316, #b45309); box-shadow: 0 0 10px rgba(180,83,9,0.5); }}
    .total-score {{
      font-weight: bold;
      background-color: #14b8a6;
      color: white;
      padding: 4px 12px;
      border-radius: 8px;
      display: inline-block;
    }}
    .empty-cell {{
      color: #64748b;
      font-style: italic;
    }}
  </style>
</head>
<body class="p-6">
  <div class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 glow text-center">🏆 Robotics Competition Leaderboard</h1>
    <div class="overflow-x-auto rounded-lg shadow-md">
      <table class="min-w-full divide-y divide-slate-700 bg-slate-800 text-sm text-center">
        <thead class="bg-slate-900 text-slate-300 uppercase tracking-wider text-xs">
          <tr>
            {''.join(f'<th class="px-4 py-3">{h}</th>' for h in headers)}
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-700">
    """

    for row in data_rows:
        pos = int(row[0])
        row_class = ""
        rank_class = f"rank-{pos}" if pos <= 3 else "rank"
        html_template += f'<tr class="hover:bg-slate-700 transition-all duration-150">'
        for i, cell in enumerate(row):
            if i == 0:
                html_template += f'<td><div class="rank {rank_class}">{cell}</div></td>'
            elif i == len(row) - 1:
                html_template += f'<td><span class="total-score">{cell}</span></td>'
            else:
                content = '-' if cell == "" or cell is None else cell
                td_class = 'empty-cell' if content == '-' else ''
                html_template += f'<td class="{td_class}">{content}</td>'
        html_template += '</tr>'

    html_template += f"""
        </tbody>
      </table>
      <div class="text-center text-slate-400 text-xs mt-6">
        Last updated: {current_time} UTC
      </div>
    </div>
  </div>
</body>
</html>"""

    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(html_template)
    print(f"✅ HTML leaderboard generated: {html_file}")

def auto_deploy():
    print("🚀 Generating leaderboard for GitHub Pages...")
    if not os.path.exists('leaderboard.csv'):
        create_sample_csv()
    csv_to_html('leaderboard.csv', 'index.html')
    print("✅ Ready for GitHub Pages deployment!")

if __name__ == "__main__":
    auto_deploy()
