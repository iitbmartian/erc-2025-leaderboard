import requests
import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import process, fuzz
from io import StringIO
import time


def extract_markdown_table(md_text, team_col, score_col):
    lines = md_text.strip().splitlines()
    table_started = False
    table_lines = []

    for i, line in enumerate(lines):
        # Look for table header row containing both required columns
        if not table_started and line.strip().startswith(
                "|") and team_col.lower() in line.lower() and score_col.lower() in line.lower():
            table_started = True
            table_lines.append(line)
            print(f"Found table header at line {i}: {line.strip()}")
        elif table_started and line.strip().startswith("|"):
            # Skip the separator line (usually contains dashes)
            if not all(c in "|-: " for c in line.strip()):
                table_lines.append(line)
        elif table_started and not line.strip():
            # Might be an empty line ig
            continue
        elif table_started and not line.strip().startswith("|"):
            # Non-table line ends the table
            break

    if len(table_lines) < 2:
        print(f"Looking for columns: '{team_col}' and '{score_col}'")
        # Debug: show lines that contain pipe characters
        pipe_lines = [f"Line {i}: {line.strip()}" for i, line in enumerate(lines) if "|" in line]
        print(f"Lines with pipes: {pipe_lines[:5]}")
        return None

    print(f"Extracted {len(table_lines)} table lines")

    # Build list of rows - Handle empty cells properly
    data = []
    # Parse headers - keep empty cells
    header_parts = table_lines[0].split("|")
    headers = [h.strip() for h in header_parts[1:-1]]  # Remove first and last empty parts
    print(f"Headers found: {headers}")

    for row_idx, row in enumerate(table_lines[1:], 1):
        # Parse row values - keep empty cells
        row_parts = row.split("|")
        values = [v.strip() for v in row_parts[1:-1]]  # Remove first and last empty parts

        if len(values) == len(headers):
            data.append(values)
        else:
            print(f"⚠Row {row_idx} has {len(values)} values but expected {len(headers)}")
            print(f"Raw row: {row}")
            print(f"Parsed values: {values}")
            # Try to pad with empty strings if we have fewer values
            while len(values) < len(headers):
                values.append("")
            data.append(values)

    if not data:
        print("Table rows not extracted properly")
        return None

    print(f"Successfully extracted {len(data)} data rows")

    try:
        df = pd.DataFrame(data, columns=headers)
        print(f"DataFrame created with shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        # Show first few rows for debugging
        print("First few rows:")
        print(df.head())
        return df
    except Exception as e:
        print(f"Failed to create DataFrame: {e}")
        return None


def normalize_team_names(team_list, threshold=85):
    """
    Normalize team names using smart fuzzy matching
    """
    canonical = []
    mapping = {}

    # Remove empty/null team names
    clean_teams = [team.strip() for team in team_list if team and str(team).strip()]
    unique_teams = list(set(clean_teams))

    # Sort by frequency first (most common names become canonical), then by length (longer names preferred)
    team_counts = {team: clean_teams.count(team) for team in unique_teams}
    sorted_teams = sorted(unique_teams, key=lambda x: (-team_counts[x], -len(x)))

    for team in sorted_teams:
        if not canonical:
            # First team becomes canonical
            canonical.append(team)
            mapping[team] = team
            print(f"Set canonical: '{team}'")
        else:
            best_match = None
            best_score = 0
            should_merge = False

            for canonical_name in canonical:
                team_lower = team.lower().strip()
                canonical_lower = canonical_name.lower().strip()

                # Get fuzzy match score
                score = fuzz.token_sort_ratio(team_lower, canonical_lower)

                # Check for exact subset matches (handles "Team X" vs "X" cases)
                team_words = set(team_lower.split())
                canonical_words = set(canonical_lower.split())

                # High confidence matches
                if score >= 95:
                    should_merge = True
                    best_match = canonical_name
                    best_score = score
                    break

                # Subset matching - one name contains all words of the other
                elif (team_words.issubset(canonical_words) or canonical_words.issubset(team_words)):
                    # Additional check: make sure they share significant content
                    if len(team_words & canonical_words) >= min(len(team_words), len(canonical_words)):
                        should_merge = True
                        best_match = canonical_name
                        best_score = score
                        print(
                            f"Subset match: '{team}' <-> '{canonical_name}' (words: {team_words} <-> {canonical_words})")
                        break

                # Moderate confidence with word overlap check
                elif score >= threshold:
                    common_words = team_words & canonical_words
                    # Require at least 2 common words AND those words make up most of the shorter name
                    min_words = min(len(team_words), len(canonical_words))
                    if len(common_words) >= 2 and len(common_words) >= min_words * 0.7:
                        # Extra safety: avoid merging if one name is very generic
                        generic_words = {'team', 'robotics', 'robot', 'rover', 'mars', 'club', 'group'}
                        if not (team_words.issubset(generic_words) or canonical_words.issubset(generic_words)):
                            if score > best_score:
                                should_merge = True
                                best_match = canonical_name
                                best_score = score

            if should_merge and best_match:
                # Choose the more complete/longer name as canonical
                if len(team) > len(best_match):
                    # Replace the canonical name with the longer version
                    canonical_idx = canonical.index(best_match)
                    canonical[canonical_idx] = team
                    # Update all existing mappings that pointed to the old canonical
                    for k, v in mapping.items():
                        if v == best_match:
                            mapping[k] = team
                    mapping[team] = team
                    print(f"Updated canonical '{best_match}' -> '{team}' (score: {best_score})")
                else:
                    mapping[team] = best_match
                    print(f"Merged '{team}' -> '{best_match}' (score: {best_score})")
            else:
                # No good match found, add as new canonical
                canonical.append(team)
                mapping[team] = team
                if best_match:
                    print(f" New canonical: '{team}' (rejected match: '{best_match}', score: {best_score})")
                else:
                    print(f"New canonical: '{team}' (no matches found)")

    # Apply mapping to all original teams (including duplicates)
    final_mapping = {}
    for team in team_list:
        clean_team = str(team).strip() if team else ""
        if clean_team:
            final_mapping[team] = mapping.get(clean_team, clean_team)
        else:
            final_mapping[team] = team  # Keep empty/null values as-is

    print(f"Normalization complete: {len(unique_teams)} unique -> {len(canonical)} canonical")
    return final_mapping


def get_leaderboard_dataframe(rounds_config=None):
    '''

    ROUND NUMBER + URL + COLUMN HEADINGS

    '''

    if rounds_config is None:
        rounds_config = [
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

    round_dfs = []
    all_teams = set()

    for round_num, round_name, url, team_col, score_col in rounds_config:
        print(f"Fetching {round_name} (Round {round_num}) from: {url}")
        try:
            # Add timeout and better error handling
            print(f"⏳ Making HTTP request...")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()  # Raise an exception for bad status codes
            print(f"Successfully fetched {round_name} (Status: {response.status_code})")

            md_text = response.text
            print(f"Content length: {len(md_text)} characters")

            #Show first few lines of content
            lines_preview = md_text.split('\n')[:5]
            print(f"First few lines: {lines_preview}")

            df = extract_markdown_table(md_text, team_col, score_col)
            if df is None or team_col not in df.columns or score_col not in df.columns:
                print(f"Warning: Could not find valid table with {team_col} and {score_col}")
                continue

            df = df[[team_col, score_col]].copy()
            df.columns = ["Team", round_name]
            df[round_name] = pd.to_numeric(df[round_name], errors="coerce").fillna(0)

            # Remove empty team names before processing
            df = df[df["Team"].str.strip() != ""].copy()
            print(f"{round_name}: {len(df)} teams after cleaning")

            df["_round_num"] = round_num  # Store round number for sorting
            round_dfs.append(df)
            all_teams.update(df["Team"].tolist())
        except Exception as e:
            print(f"Error in {round_name}: {e}")
            continue

    if not round_dfs:
        print("No valid data found across all rounds.")
        return pd.DataFrame(columns=["Team", "Total"])

    # Normalize team names
    all_names = [name for df in round_dfs for name in df["Team"]]
    print(f"Normalizing {len(all_names)} team name instances...")
    name_map = normalize_team_names(all_names)

    # Apply normalization to all dataframes
    for df in round_dfs:
        df["Team"] = df["Team"].map(lambda name: name_map.get(name, name))
        print(f"After normalization: {df['Team'].nunique()} unique teams in {df.columns[1]}")

    # Create master dataframe with all unique normalized team names
    all_normalized_teams = set()
    for df in round_dfs:
        all_normalized_teams.update(df["Team"].unique())

    master_df = pd.DataFrame({"Team": sorted(all_normalized_teams)})
    print(f"Master dataframe initialized with {len(master_df)} unique teams")

    # Create columns for all 7 rounds, but populate with actual round names
    for i in range(1, 8):  # Always 7 rounds
        matching_dfs = [df for df in round_dfs if df["_round_num"].iloc[0] == i]
        if matching_dfs:
            for df in matching_dfs:
                round_col = [col for col in df.columns if col not in ["Team", "_round_num"]][0]
                df_to_merge = df[["Team", round_col]].copy()

                # Handle duplicates within the same round by summing scores
                print(f"Before dedup in {round_col}: {len(df_to_merge)} rows")
                if df_to_merge["Team"].duplicated().any():
                    print(f" Found duplicates in {round_col}:")
                    duplicates = df_to_merge[df_to_merge["Team"].duplicated(keep=False)]
                    print(duplicates)

                    # Sum scores for duplicate teams
                    df_to_merge = df_to_merge.groupby("Team", as_index=False)[round_col].sum()
                    print(f"fter dedup in {round_col}: {len(df_to_merge)} rows")

                master_df = master_df.merge(df_to_merge, on="Team", how="left")
        else:
            master_df[f"Round {i}"] = 0

    master_df.fillna(0, inplace=True)

    # Convert all round columns to int
    round_columns = [col for col in master_df.columns if col != "Team"]
    for col in round_columns:
        master_df[col] = master_df[col].astype(int)

    # Final deduplication check (shouldn't be needed but just in case)
    if master_df["Team"].duplicated().any():
        print("Final deduplication check found duplicates:")
        duplicates = master_df[master_df["Team"].duplicated(keep=False)]
        print(duplicates)

        # Group by team and sum all scores
        team_col = master_df[["Team"]].copy()
        score_cols = master_df[round_columns]

        master_df = team_col.groupby("Team", as_index=False).first()
        summed_scores = score_cols.groupby(master_df["Team"]).sum().reset_index()
        master_df = master_df.merge(summed_scores, on="Team")
        print(f"Final deduplication complete: {len(master_df)} unique teams")

    master_df["Total"] = master_df[round_columns].sum(axis=1)

    print(f"Final leaderboard: {len(master_df)} teams, {len(round_columns)} round columns")
    return master_df
