import json
import subprocess
from pathlib import Path

def main():
    repo_file = Path("maps_repo.json")
    
    # 1. Read current themes
    current_data = {}
    if repo_file.exists():
        try:
            current_data = json.loads(repo_file.read_text(encoding="utf-8"), strict=False)
            print(f"Current maps_repo.json has {len(current_data)} themes.")
        except Exception as e:
            print(f"Error reading current maps_repo.json: {e}")
            
    # 2. Read past themes from commit 34a99bb
    past_data = {}
    try:
        past_content = subprocess.check_output(["git", "show", "34a99bb:maps_repo.json"])
        past_data = json.loads(past_content.decode("utf-8"), strict=False)
        print(f"Past commit 34a99bb has {len(past_data)} themes.")
    except Exception as e:
        print(f"Error reading past maps_repo.json from git: {e}")

    # 3. Merge them (current overwrites past if conflict)
    merged_data = {}
    # Load past themes first
    for k, v in past_data.items():
        merged_data[k] = v
        
    # Overwrite/Add current themes
    for k, v in current_data.items():
        merged_data[k] = v
        
    print(f"Merged total themes: {len(merged_data)}")
    
    # 4. Save back to maps_repo.json
    repo_file.write_text(json.dumps(merged_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Successfully merged and written back to maps_repo.json!")

if __name__ == "__main__":
    main()
