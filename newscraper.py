import requests
import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import process, fuzz
from io import StringIO

def extract_markdown_table(md_text, team_col, score_col):
    try:
        html = markdown_to_html(md_text)
        df_list = pd.read_html(StringIO(html))  # ✅ FIXED: wrap with StringIO
        for df in df_list:
            df.columns = df.columns.map(lambda x: x.strip() if isinstance(x, str) else x)
            if team_col in df.columns and score_col in df.columns:
                df = df[[team_col, score_col]]
                df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
                return df
    except Exception as e:
        print(f"Failed to parse table: {e}")
    return None

def markdown_to_html(md_text):
    soup = BeautifulSoup("", features="html.parser")
    lines = md_text.strip().splitlines()
    table_lines = [line for line in lines if "|" in line]
    html_table = "<table>\n"
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        tag = "th" if lines.index(line) == 0 else "td"
        html_table += "<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in cells) + "</tr>\n"
    html_table += "</table>"
    soup.append(BeautifulSoup(html_table, features="html.parser"))
    return str(soup)

def normalize_team_names(team_list, threshold=90):
    canonical = []
    mapping = {}

    for team in team_list:
        match, score, _ = process.extractOne(team, canonical, scorer=fuzz.token_sort_ratio)
        if match and score >= threshold:
            mapping[team] = match
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
            df = extract_markdown_table(md_text, team_col, score_col)
            if df is None or df.empty:
                print(f"Warning: Could not find valid table with {team_col} and {score_col}")
                continue

            df.columns = ["Team", f"Round {idx}"]
            df[f"Round {idx}"] = pd.to_numeric(df[f"Round {idx}"], errors="coerce").fillna(0)
            round_dfs.append(df)
            all_teams.update(df["Team"].tolist())
        except Exception as e:
            print(f"Error fetching or parsing round {idx}: {e}")

    if not round_dfs:
        print("❌ No valid data found across all rounds.")
        return pd.DataFrame(columns=["Team", "Total"])  # ✅ Prevent KeyError later

    # Fuzzy normalize team names
    all_names = [name for df in round_dfs for name in df["Team"]]
    mapping = normalize_team_names(all_names)

    for df in round_dfs:
        df["Team"] = df["Team"].map(lambda name: mapping.get(name, name))

    # Merge into master DataFrame
    master_df = pd.DataFrame({"Team": sorted(set(mapping.values()))})

    for i in range(1, 8):
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
