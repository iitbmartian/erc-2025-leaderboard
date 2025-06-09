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
        [6, "Makercie", 33, "", "", "", "", 3, "", 36],
        [7, "Mind Cloud", 32, 16, "", "", "", "", 15, 63],
        [8, "PSG Team Aurora", 32, 18, "", "", "", 8, "", 58],
        [9, "TerraBots", 32, 20, "", "", "", 10, "", 62],
        [10, "CSA ROBOTICS", 31, 0, "", "", "", "", "", 31],
        [11, "DJS Antariksh", 31, 20, "", "", "", 5, "", 56],
        [12, "NSpace", 31, 20, "", "", "", 5, "", 56],
        [13, "Robocon IITR", 31, 20, "", "", "", 3, "", 54],
        [14, "ARES", 29, 20, "", "", "", 5, "", 54],
        [15, "Amogh", 28, 20, "", "", "", 2, "", 50],
        [16, "Interplanetar – BUET Mars Rover Team", 25, 20, "", "", "", 5, "", 50],
        [17, "Horizon", 23, 4, "", "", "", 2, "", 29],
        [18, "PUTLunarTeam", 23, 20, "", "", "", 3, 5, 51],
        [19, "ProjectRed", 20, 20, "", "", "", 5, "", 45],
        [20, "RIVAL", 19, 20, "", "", "", 5, "", 44],
        [21, "BanglaBot Xplorer", 10, "", "", "", "", "", "", 10],
        [22, "ELTE StudentTechLab", 9, "", "", "", "", "", "", 9],
        [23, "BLAZERS", 5, "", "", "", "", "", "", 5],
        [24, "light pheniox", 4, "", "", "", "", "", "", 4],
    ]
    
    with open('leaderboard.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
    print("✅ Sample CSV created: leaderboard.csv")

def csv_to_html(csv_file="leaderboard.csv", html_file="index.html"):
    """Convert CSV to beautiful HTML leaderboard"""
    
    # Read CSV data
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    
    headers = rows[0]
    data_rows = rows[1:]
    
    # HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robotics Competition Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .table-container {{
            padding: 20px;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 18px 12px;
            text-align: center;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 12px;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        td {{
            padding: 15px 12px;
            border-bottom: 1px solid #e8f4f8;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        td:nth-child(2) {{
            text-align: left;
            font-weight: 500;
            color: #2c3e50;
        }}
        
        tr:hover {{
            background: linear-gradient(90deg, #f8fbff 0%, #e3f2fd 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .rank {{
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
            background: #ecf0f1;
            border-radius: 50%;
            width: 35px;
            height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
        }}
        
        .rank-1 {{ 
            background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(241, 196, 15, 0.4);
        }}
        
        .rank-2 {{ 
            background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(149, 165, 166, 0.4);
        }}
        
        .rank-3 {{ 
            background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(230, 126, 34, 0.4);
        }}
        
        .top-1 {{ background: linear-gradient(90deg, #fff9c4 0%, #fef3cd 100%) !important; }}
        .top-2 {{ background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%) !important; }}
        .top-3 {{ background: linear-gradient(90deg, #fef3e2 0%, #fde8cc 100%) !important; }}
        
        .total-score {{
            font-weight: bold;
            font-size: 18px;
            color: #e74c3c;
            background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
            padding: 8px 12px;
            border-radius: 8px;
            display: inline-block;
            min-width: 50px;
        }}
        
        .empty-cell {{
            color: #bdc3c7;
            font-style: italic;
            opacity: 0.6;
        }}
        
        .last-updated {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 14px;
            border-top: 1px solid #ecf0f1;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2rem; }}
            table {{ font-size: 12px; }}
            th, td {{ padding: 10px 6px; }}
            .total-score {{ font-size: 14px; padding: 6px 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 Robotics Competition</h1>
            <p>Official Leaderboard - Live Rankings</p>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>"""
    
    # Add headers
    for header in headers:
        html_template += f"\n                        <th>{header}</th>"
    
    html_template += """
                    </tr>
                </thead>
                <tbody>"""
    
    # Add data rows
    for row in data_rows:
        position = int(row[0])
        row_class = ""
        if position == 1:
            row_class = "top-1"
        elif position == 2:
            row_class = "top-2"
        elif position == 3:
            row_class = "top-3"
        
        html_template += f'\n                    <tr class="{row_class}">'
        
        for i, cell in enumerate(row):
            if i == 0:  # Position column
                rank_class = f"rank-{position}" if position <= 3 else "rank"
                html_template += f'\n                        <td><div class="rank {rank_class}">{cell}</div></td>'
            elif i == len(row) - 1:  # Total column
                html_template += f'\n                        <td><span class="total-score">{cell}</span></td>'
            else:
                if cell == "" or cell is None:
                    html_template += '\n                        <td class="empty-cell">-</td>'
                else:
                    html_template += f'\n                        <td>{cell}</td>'
        
        html_template += '\n                    </tr>'
    
    # Close HTML
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_template += f"""
                </tbody>
            </table>
        </div>
        
        <div class="last-updated">
            Last updated: {current_time} UTC
        </div>
    </div>
</body>
</html>"""
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(html_template)
    
    print(f"✅ HTML leaderboard generated: {html_file}")

def auto_deploy():
    """Auto-generate and prepare for GitHub Pages deployment"""
    print("🚀 Generating leaderboard for GitHub Pages...")
    
    # Create CSV if it doesn't exist
    if not os.path.exists('leaderboard.csv'):
        create_sample_csv()
    
    # Generate HTML
    csv_to_html('leaderboard.csv', 'index.html')
    
    print("✅ Ready for GitHub Pages deployment!")
    print("📝 To update scores: Edit leaderboard.csv and run this script again")

if __name__ == "__main__":
    auto_deploy()
    