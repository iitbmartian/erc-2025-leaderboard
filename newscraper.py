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
            print(f"📋 Found table header at line {i}: {line.strip()}")
        elif table_started and line.strip().startswith("|"):
            # Skip the separator line (usually contains dashes)
            if not all(c in "|-: " for c in line.strip()):
                table_lines.append(line)
        elif table_started and not line.strip():
            # Empty line might end the table, but let's be more lenient
            continue
        elif table_started and not line.strip().startswith("|"):
            # Non-table line ends the table
            break

    if len(table_lines) < 2:
        print("⚠ Table not found or malformed")
        print(f"🔍 Looking for columns: '{team_col}' and '{score_col}'")
        # Debug: show lines that contain pipe characters
        pipe_lines = [f"Line {i}: {line.strip()}" for i, line in enumerate(lines) if "|" in line]
        print(f"📋 Lines with pipes: {pipe_lines[:5]}")  # Show first 5
        return None

    print(f"📊 Extracted {len(table_lines)} table lines")

    # Build list of rows - Handle empty cells properly
    data = []
    # Parse headers - keep empty cells
    header_parts = table_lines[0].split("|")
    headers = [h.strip() for h in header_parts[1:-1]]  # Remove first and last empty parts
    print(f"📋 Headers found: {headers}")

    for row_idx, row in enumerate(table_lines[1:], 1):
        # Parse row values - keep empty cells
        row_parts = row.split("|")
        values = [v.strip() for v in row_parts[1:-1]]  # Remove first and last empty parts

        if len(values) == len(headers):
            data.append(values)
        else:
            print(f"⚠ Row {row_idx} has {len(values)} values but expected {len(headers)}")
            print(f"   Raw row: {row}")
            print(f"   Parsed values: {values}")
            # Try to pad with empty strings if we have fewer values
            while len(values) < len(headers):
                values.append("")
            data.append(values)

    if not data:
        print("⚠ Table rows not extracted properly")
        return None

    print(f"📊 Successfully extracted {len(data)} data rows")

    try:
        df = pd.DataFrame(data, columns=headers)
        print(f"✅ DataFrame created with shape: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        # Show first few rows for debugging
        print("📊 First few rows:")
        print(df.head())
        return df
    except Exception as e:
        print(f"⚠ Failed to create DataFrame: {e}")
        return None


def normalize_team_names(team_list, threshold=90):
    """
    Normalize team names using fuzzy matching with more conservative approach
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
            print(f"🏷️  Set canonical: '{team}'")
        else:
            # Use only token_sort_ratio for more precise matching
            # This handles word order differences but is less aggressive than partial matching
            result = process.extractOne(team, canonical, scorer=fuzz.token_sort_ratio)

            if result is not None:
                best_match, score, _ = result

                # Additional checks to prevent false positives
                should_merge = False

                if score >= threshold:
                    # Extra validation for high-confidence matches
                    if score >= 95:
                        should_merge = True
                    elif score >= threshold:
                        # For moderate confidence, do additional checks
                        # Check if one name is contained in the other (handles abbreviations)
                        team_lower = team.lower()
                        match_lower = best_match.lower()

                        # Allow merging if one is clearly an abbreviation/subset of the other
                        if (team_lower in match_lower or match_lower in team_lower):
                            should_merge = True
                        # Allow merging if they have significant word overlap
                        elif len(set(team_lower.split()) & set(match_lower.split())) >= 2:
                            should_merge = True

                if should_merge:
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
                        print(f"🔄 Updated canonical '{best_match}' -> '{team}' (score: {score})")
                    else:
                        mapping[team] = best_match
                        print(f"🔗 Merged '{team}' -> '{best_match}' (score: {score})")
                else:
                    # No good match found, add as new canonical
                    canonical.append(team)
                    mapping[team] = team
                    print(f"🏷️  New canonical: '{team}' (best match: '{best_match}', score: {score})")
            else:
                # No match found at all
                canonical.append(team)
                mapping[team] = team
                print(f"🏷️  New canonical: '{team}' (no matches found)")

    # Apply mapping to all original teams (including duplicates)
    final_mapping = {}
    for team in team_list:
        clean_team = str(team).strip() if team else ""
        if clean_team:
            final_mapping[team] = mapping.get(clean_team, clean_team)
        else:
            final_mapping[team] = team  # Keep empty/null values as-is

    print(f"📊 Normalization complete: {len(unique_teams)} unique -> {len(canonical)} canonical")
    return final_mapping

def get_leaderboard_dataframe(rounds_config=None):
    # Default configuration if none provided
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
            (6, "Social Excellence",
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
            print(f"✅ Successfully fetched {round_name} (Status: {response.status_code})")

            md_text = response.text
            print(f"📄 Content length: {len(md_text)} characters")

            # Debug: Show first few lines of content
            lines_preview = md_text.split('\n')[:5]
            print(f"📋 First few lines: {lines_preview}")

            df = extract_markdown_table(md_text, team_col, score_col)
            if df is None or team_col not in df.columns or score_col not in df.columns:
                print(f"Warning: Could not find valid table with {team_col} and {score_col}")
                continue

            df = df[[team_col, score_col]].copy()
            df.columns = ["Team", round_name]
            df[round_name] = pd.to_numeric(df[round_name], errors="coerce").fillna(0)
            df["_round_num"] = round_num  # Store round number for sorting
            round_dfs.append(df)
            all_teams.update(df["Team"].tolist())
        except Exception as e:
            print(f"Error in {round_name}: {e}")
            continue

    if not round_dfs:
        print("❌ No valid data found across all rounds.")
        return pd.DataFrame(columns=["Team", "Total"])

    all_names = [name for df in round_dfs for name in df["Team"]]
    name_map = normalize_team_names(all_names)

    for df in round_dfs:
        df["Team"] = df["Team"].map(lambda name: name_map.get(name, name))

    master_df = pd.DataFrame({"Team": sorted(set(name_map.values()))})

    # Create columns for all 7 rounds, but populate with actual round names
    for i in range(1, 8):  # Always 7 rounds
        matching_dfs = [df for df in round_dfs if df["_round_num"].iloc[0] == i]
        if matching_dfs:
            for df in matching_dfs:
                round_col = [col for col in df.columns if col not in ["Team", "_round_num"]][0]
                df_to_merge = df[["Team", round_col]].copy()
                master_df = master_df.merge(df_to_merge, on="Team", how="left")
        else:
            master_df[f"Round {i}"] = 0

    master_df.fillna(0, inplace=True)

    # Convert all round columns to int
    round_columns = [col for col in master_df.columns if col != "Team"]
    for col in round_columns:
        master_df[col] = master_df[col].astype(int)

    master_df["Total"] = master_df[round_columns].sum(axis=1)

    return master_df