import requests
import pandas as pd
import re
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple
import time

class GitHubRoundScraper:
    def __init__(self, team_column: str = None, score_column: str = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.team_column = team_column
        self.score_column = score_column
        self.results_df = pd.DataFrame()  # Master results table
        self.round_counter = 0
        
    def convert_github_url_to_raw(self, url: str) -> str:
        """Convert GitHub URL to raw content URL"""
        if 'raw.githubusercontent.com' in url:
            return url
        
        # Convert github.com URL to raw URL
        url = url.replace('github.com', 'raw.githubusercontent.com')
        url = url.replace('/blob/', '/')
        return url
    
    def get_markdown_files_from_repo(self, repo_url: str) -> List[str]:
        """Get all markdown files from a repository"""
        # Extract owner and repo name from URL
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        
        owner, repo = path_parts[0], path_parts[1]
        
        # Get repository contents using GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        
        try:
            response = self.session.get(api_url)
            response.raise_for_status()
            contents = response.json()
            
            md_files = []
            for item in contents:
                if item['name'].endswith('.md'):
                    md_files.append(item['download_url'])
            
            return md_files
        except Exception as e:
            print(f"Error fetching repository contents: {e}")
            return []
    
    def extract_markdown_content(self, url: str) -> Optional[str]:
        """Extract markdown content from URL"""
        try:
            raw_url = self.convert_github_url_to_raw(url)
            response = self.session.get(raw_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return None
    
    def parse_markdown_tables(self, content: str) -> List[pd.DataFrame]:
        """Parse markdown tables from content"""
        tables = []
        
        # Split content into lines and find tables
        lines = content.split('\n')
        table_lines = []
        in_table = False
        
        for line in lines:
            if '|' in line and line.strip():
                if not in_table:
                    table_lines = [line]
                    in_table = True
                else:
                    table_lines.append(line)
            else:
                if in_table and table_lines:
                    if len(table_lines) >= 3:  # Header + separator + at least one data row
                        tables.append(self._parse_single_table('\n'.join(table_lines)))
                    table_lines = []
                    in_table = False
        
        # Handle case where table is at the end of file
        if in_table and table_lines and len(table_lines) >= 3:
            tables.append(self._parse_single_table('\n'.join(table_lines)))
        
        return [t for t in tables if t is not None]
    
    def _parse_single_table(self, table_text: str) -> Optional[pd.DataFrame]:
        """Parse a single markdown table"""
        try:
            lines = [line.strip() for line in table_text.strip().split('\n') if line.strip()]
            
            if len(lines) < 3:
                return None
            
            # Extract headers
            header_line = lines[0]
            headers = [col.strip() for col in header_line.split('|')[1:-1]]  # Remove empty first/last
            
            # Skip separator line (lines[1])
            data_lines = lines[2:]
            
            # Extract data
            data = []
            for line in data_lines:
                if '|' in line:
                    row = [col.strip() for col in line.split('|')[1:-1]]
                    if len(row) == len(headers):
                        data.append(row)
            
            if data:
                df = pd.DataFrame(data, columns=headers)
                return df
            
        except Exception as e:
            print(f"Error parsing table: {e}")
        
        return None
    
    def identify_team_score_columns(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """Identify which columns contain team names and scores"""
        # If explicit column names provided, use them
        if self.team_column and self.score_column:
            # Check if columns exist in the dataframe (case-insensitive)
            team_col = None
            score_col = None
            
            for col in df.columns:
                if col.lower() == self.team_column.lower():
                    team_col = col
                if col.lower() == self.score_column.lower():
                    score_col = col
            
            if team_col and score_col:
                return team_col, score_col
            else:
                print(f"Warning: Specified columns not found. Looking for '{self.team_column}' and '{self.score_column}'")
                print(f"Available columns: {list(df.columns)}")
        
        # Fallback to automatic detection
        team_col = None
        score_col = None
        
        # Common patterns for team columns
        team_patterns = ['team', 'name', 'participant', 'player', 'group']
        score_patterns = ['score', 'points', 'total', 'result', 'mark']
        
        columns = [col.lower() for col in df.columns]
        
        # Find team column
        for col_idx, col in enumerate(columns):
            for pattern in team_patterns:
                if pattern in col:
                    team_col = df.columns[col_idx]
                    break
            if team_col:
                break
        
        # Find score column
        for col_idx, col in enumerate(columns):
            for pattern in score_patterns:
                if pattern in col:
                    score_col = df.columns[col_idx]
                    break
            if score_col:
                break
        
        # If no explicit matches, try to infer from data types
        if not team_col or not score_col:
            for col in df.columns:
                sample_values = df[col].dropna().head(3)
                if len(sample_values) > 0:
                    # Check if column contains mostly numbers (likely score)
                    numeric_count = 0
                    for val in sample_values:
                        try:
                            float(str(val).replace(',', ''))
                            numeric_count += 1
                        except:
                            pass
                    
                    if numeric_count >= len(sample_values) * 0.7:  # 70% numeric
                        if not score_col:
                            score_col = col
                    else:
                        if not team_col:
                            team_col = col
        
        return team_col, score_col
    
    def add_round(self, urls: List[str], round_name: str = None) -> pd.DataFrame:
        """Add a new round of scores from URLs"""
        self.round_counter += 1
        if round_name is None:
            round_name = f"Round_{self.round_counter}"
        
        print(f"\nProcessing {round_name}...")
        round_results = {}
        
        for url in urls:
            print(f"  Processing: {url}")
            
            # If it's a repository URL, get all markdown files
            if '/blob/' not in url and url.count('/') == 4:  # Repository root URL
                md_files = self.get_markdown_files_from_repo(url)
                urls_to_process = md_files
            else:
                urls_to_process = [url]
            
            for file_url in urls_to_process:
                content = self.extract_markdown_content(file_url)
                if not content:
                    continue
                
                tables = self.parse_markdown_tables(content)
                
                for table in tables:
                    team_col, score_col = self.identify_team_score_columns(table)
                    
                    if team_col and score_col:
                        # Extract team-score pairs
                        for _, row in table.iterrows():
                            team = str(row[team_col]).strip()
                            score = str(row[score_col]).strip()
                            
                            # Try to convert score to numeric
                            try:
                                score_numeric = float(score.replace(',', ''))
                            except:
                                score_numeric = 0  # Default to 0 if can't parse
                                print(f"Warning: Could not parse score '{score}' for team '{team}'")
                            
                            # Store the score for this team in this round
                            round_results[team] = score_numeric
            
            # Be respectful to GitHub's rate limits
            time.sleep(0.5)
        
        # Update the master results dataframe
        self._update_results(round_results, round_name)
        
        return self.results_df.copy()
    
    def _update_results(self, round_results: Dict[str, float], round_name: str):
        """Update the master results dataframe with new round data"""
        if self.results_df.empty:
            # Initialize with team names
            teams = list(round_results.keys())
            self.results_df = pd.DataFrame(index=teams)
            self.results_df.index.name = 'Team'
        
        # Add new teams if they don't exist
        for team in round_results.keys():
            if team not in self.results_df.index:
                # Add new team with 0s for all existing rounds
                new_row = pd.Series(0, index=self.results_df.columns, name=team)
                self.results_df = pd.concat([self.results_df, new_row.to_frame().T])
        
        # Add the new round column
        self.results_df[round_name] = 0  # Initialize all teams with 0
        
        # Update scores for teams that participated in this round
        for team, score in round_results.items():
            self.results_df.loc[team, round_name] = score
        
        # Update total column
        round_columns = [col for col in self.results_df.columns if col.startswith('Round_') or col == round_name]
        self.results_df['Total'] = self.results_df[round_columns].sum(axis=1)
    
    def get_results(self) -> pd.DataFrame:
        """Get the current results dataframe"""
        return self.results_df.copy()
    
    def save_results(self, filename: str = 'competition_results.csv'):
        """Save results to CSV file"""
        if not self.results_df.empty:
            # Reset index to make Team a column
            save_df = self.results_df.reset_index()
            save_df.to_csv(filename, index=False)
            print(f"Results saved to '{filename}'")
        else:
            print("No results to save")
    
    def display_results(self):
        """Display current results in a formatted way"""
        if self.results_df.empty:
            print("No results yet")
            return
        
        print("\n" + "="*60)
        print("COMPETITION RESULTS")
        print("="*60)
        
        # Sort by total score (descending)
        display_df = self.results_df.sort_values('Total', ascending=False)
        
        # Add ranking
        display_df = display_df.reset_index()
        display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
        
        print(display_df.to_string(index=False))
        print("="*60)

# Usage example
def main():
    # Initialize scraper with your column names
    scraper = GitHubRoundScraper(team_column="Team", score_column="Score")
    
    # Round 1 URLs
    round1_urls = [
        "https://github.com/husarion/erc2025/blob/main/phase_1/qualification_results.md"
    ]
    
    # Round 2 URLs  
    round2_urls = [
        "https://github.com/husarion/erc2025/blob/main/phase_2/connectivity_test_1_results.md"
    ]
    
    # Add rounds one by one
    scraper.add_round(round1_urls, "Round_1")
    scraper.display_results()
    
    scraper.add_round(round2_urls, "Round_2")
    scraper.display_results()
    
    # Save final results
    scraper.save_results()
    
    # You can also get the raw dataframe
    results = scraper.get_results()
    print(f"\nFinal shape: {results.shape}")

if __name__ == "__main__":
    main()