import requests
import pandas as pd
import io
import re

def normalize_team_name(name):
    if not isinstance(name, str):
        return name
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '', name)  # remove non-alphanumeric characters
    name = re.sub(r'^(team|the)', '', name)  # remove common prefixes
    return name

def extract_markdown_table(text, team_col, score_col):
    lines = text.splitlines()
    header_idx = None

    # Find the start of the table
    for i, line in enumerate(lines):
        if '|' in line and team_col in line and score_col in line:
            header_idx = i
            break

    if header_idx is None or header_idx + 2 > len(lines):
        return None

    # Extract lines that form the table
    table_lines = [lines[header_idx]]
    i = header_idx + 1
    while i < len(lines) and '|' in lines[i]:
        table_lines.append(lines[i])
        i += 1

    table_text = '\n'.join(table_lines)
    try:
        df = pd.read_csv(io.StringIO(table_text), sep='\|', engine='python')
        df = df.dropna(axis=1, how='all')  # Drop empty cols from parsing pipe edges
        df.columns = [c.strip() for c in df.columns]
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Normalize team names
        df[team_col] = df[team_col].apply(normalize_team_name)

        # Convert score column to numeric
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce').fillna(0)

        # Group by normalized team names in case duplicates exist in same table
        df = df.groupby(team_col, as_index=False)[score_col].sum()

        return df
    except Exception as e:
        print(f"Failed to parse table: {e}")
        return None

def get_leaderboard_dataframe():
    # Example input: list of (url, team_column, score_column) tuples (raw GitHub Markdown URLs)
    urls = [
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_1/qualification_results.md", "Team name", "Sum"),
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_2/connectivity_test_1_results.md", "Team name", "Connectivity Test score"),
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_6/jury_points.md", "Team name", "Point count"),
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_6/social_excellence.md", "Team name", "Point count")
    ]

    all_teams = set()
    round_dfs = []
    team_name_map = {}

    for idx, (url, team_col, score_col) in enumerate(urls, 1):
        print(f"Fetching round {idx} from: {url}")
        try:
            md_text = requests.get(url).text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        df = extract_markdown_table(md_text, team_col, score_col)
        if df is None or df.empty:
            print(f"Warning: Could not find valid table with specified columns in {url}")
            continue

        # Track the original display name
        display_names = {}
        for team in df[team_col]:
            norm = normalize_team_name(team)
            if norm not in team_name_map:
                team_name_map[norm] = team
            display_names[norm] = team_name_map[norm]

        df["Team"] = df[team_col].apply(lambda x: team_name_map.get(x, x))
        df = df[["Team", score_col]]
        df.columns = ["Team", f"Round {idx}"]
        df[f"Round {idx}"] = pd.to_numeric(df[f"Round {idx}"] , errors="coerce").fillna(0)

        round_dfs.append(df)
        all_teams.update(df["Team"].tolist())

    # Create a master DataFrame with all teams
    master_df = pd.DataFrame({"Team": sorted(all_teams)})

    # Merge round scores into the master DataFrame, filling missing scores with 0
    for round_df in round_dfs:
        master_df = master_df.merge(round_df, on="Team", how="left")

    master_df.fillna(0, inplace=True)

    # Add a Total column and sort
    round_columns = [col for col in master_df.columns if col.startswith("Round")]
    master_df["Total"] = master_df[round_columns].sum(axis=1)
    master_df.sort_values(by="Total", ascending=False, inplace=True)

    return master_df

if __name__ == "__main__":
    df = get_leaderboard_dataframe()
    print(df)
    # Optionally save to CSV
    # df.to_csv("final_scores.csv", index=False)