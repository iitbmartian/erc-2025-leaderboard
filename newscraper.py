import requests
import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import process, fuzz
from io import StringIO


def extract_markdown_table(md_text, team_col, score_col):
    lines = md_text.strip().splitlines()
    table_started = False
    table_lines = []

    for line in lines:
        if team_col.lower() in line.lower() and score_col.lower() in line.lower():
            table_started = True
            table_lines.append(line)
        elif table_started and line.strip().startswith("|"):
            table_lines.append(line)
        elif table_started and not line.strip():
            break  # blank line = end of table

    if len(table_lines) < 2:
        print("⚠ Table not found or malformed")
        return None

    # Build list of rows
    data = []
    headers = [h.strip() for h in table_lines[0].split("|") if h.strip()]
    for row in table_lines[1:]:
        values = [v.strip() for v in row.split("|") if v.strip()]
        if len(values) == len(headers):
            data.append(values)

    if not data:
        print("⚠ Table rows not extracted properly")
        return None

    try:
        df = pd.DataFrame(data, columns=headers)
        return df
    except Exception as e:
        print(f"⚠ Failed to create DataFrame: {e}")
        return None


def normalize_team_names(team_list, threshold=90):
    canonical = []
    mapping = {}

    for team in team_list:
        if not canonical:  # If canonical list is empty, add the first team
            canonical.append(team)
            mapping[team] = team
        else:
            result = process.extractOne(team, canonical, scorer=fuzz.token_sort_ratio)
            if result is not None:
                match, score, _ = result
                if match and score >= threshold:
                    mapping[team] = match
                else:
                    canonical.append(team)
                    mapping[team] = team
            else:
                canonical.append(team)
                mapping[team] = team
    return mapping


def get_leaderboard_dataframe():
    urls = [
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_1/qualification_results.md", "Team name", "Sum"),
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_2/connectivity_test_1_results.md", "Team name", "Connectivity Test score"),
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_6/jury_points.md", "Team name", "Point count"),
        ("https://raw.githubusercontent.com/husarion/erc2025/refs/heads/main/phase_6/social_excellence.md", "Team name", "Point count"),
    ]

    round_dfs = []
    all_teams = set()

    for idx, (url, team_col, score_col) in enumerate(urls, 1):
        print(f"Fetching round {idx} from: {url}")
        try:
            md_text = requests.get(url).text
            df = extract_markdown_table(md_text, team_col, score_col)  # Fixed: Added missing arguments
            if df is None or team_col not in df.columns or score_col not in df.columns:
                print(f"Warning: Could not find valid table with {team_col} and {score_col}")
                continue

            df = df[[team_col, score_col]].copy()
            df.columns = ["Team", f"Round {idx}"]
            df[f"Round {idx}"] = pd.to_numeric(df[f"Round {idx}"], errors="coerce").fillna(0)
            round_dfs.append(df)
            all_teams.update(df["Team"].tolist())
        except Exception as e:
            print(f"Error in round {idx}: {e}")
            continue

    if not round_dfs:
        print("❌ No valid data found across all rounds.")
        return pd.DataFrame(columns=["Team", "Total"])

    all_names = [name for df in round_dfs for name in df["Team"]]
    name_map = normalize_team_names(all_names)

    for df in round_dfs:
        df["Team"] = df["Team"].map(lambda name: name_map.get(name, name))

    master_df = pd.DataFrame({"Team": sorted(set(name_map.values()))})
    for i in range(1, 8):  # Always 7 rounds
        col = f"Round {i}"
        df = next((d for d in round_dfs if col in d.columns), None)
        if df is not None:
            master_df = master_df.merge(df, on="Team", how="left")
        else:
            master_df[col] = 0

    master_df.fillna(0, inplace=True)
    for col in [f"Round {i}" for i in range(1, 8)]:
        master_df[col] = master_df[col].astype(int)

    master_df["Total"] = master_df[[f"Round {i}" for i in range(1, 8)]].sum(axis=1)

    return master_df