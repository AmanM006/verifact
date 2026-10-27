import json
import subprocess
import time
import base64
import sys
import urllib.request
import urllib.error

def get_gh_token():
    try:
        res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        print(f"Notice: gh token not found via cli ({e}), continuing with public rate limit or env token.")
        return None

token = get_gh_token()
print(f"GitHub Token available: {'Yes' if token else 'No'}")

headers = {
    "User-Agent": "Open-Agent-Hackathon-Collector-2026",
    "Accept": "application/vnd.github.v3+json",
}
if token:
    headers["Authorization"] = f"Bearer {token}"

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            reset_time = int(e.headers.get("x-ratelimit-reset", time.time() + 60))
            sleep_sec = max(5, reset_time - int(time.time()) + 2)
            print(f"Rate limited (403). Sleeping {sleep_sec}s...")
            time.sleep(sleep_sec)
            return fetch_json(url)
        print(f"HTTP error {e.code} for {url}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_readme(full_name):
    url = f"https://api.github.com/repos/{full_name}/readme"
    data = fetch_json(url)
    if data and "content" in data:
        try:
            content_b64 = data["content"]
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception as e:
            return f"(Error decoding README: {e})"
    return "*(No README found or accessible)*"

# Query for Open Agent Hackathon 2026
search_query = "Open+Agent+Hackathon+2026"
all_repos = []
seen_ids = set()
page = 1

print(f"Initiating repository search for: '{search_query.replace('+', ' ')}'...")

while True:
    print(f"Fetching search page {page}...")
    url = f"https://api.github.com/search/repositories?q={search_query}&sort=updated&order=desc&per_page=100&page={page}"
    data = fetch_json(url)
    if not data or "items" not in data:
        print("No data or items returned.")
        break
    items = data["items"]
    if not items:
        break

    for item in items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            all_repos.append(item)

    total_count = data.get("total_count", 0)
    print(f"Total collected so far: {len(all_repos)} / {total_count}")
    if len(all_repos) >= total_count or page * 100 >= 1000:
        break
    page += 1
    time.sleep(1)

print(f"\nTotal unique repositories collected: {len(all_repos)}")

output_file = "open_agent_hackathon_2026_repos.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Open Agent Hackathon 2026 - Repositories & README Intelligence Dossier\n\n")
    f.write(f"- **Total Repositories Indexed**: {len(all_repos)}\n")
    f.write(f"- **Captured At**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
    f.write(f"- **Sponsor Technologies**: Zetaris (Federated Data Lakehouse), Meterless (H-MEM / Nightshift), NVIDIA Nemotron\n\n")
    f.write("---\n\n## Table of Contents\n\n")
    for idx, repo in enumerate(all_repos, 1):
        name = repo["full_name"]
        slug = name.lower().replace("/", "").replace("-", "").replace("_", "").replace(".", "")
        desc = (repo.get("description") or "No description").replace("\n", " ")
        f.write(f"{idx}. [{name}](#{idx}-{slug}) - *{desc}*\n")
    f.write("\n---\n\n")

    for idx, repo in enumerate(all_repos, 1):
        name = repo["full_name"]
        slug = name.lower().replace("/", "").replace("-", "").replace("_", "").replace(".", "")
        html_url = repo["html_url"]
        desc = repo.get("description") or "No description provided."
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        lang = repo.get("language") or "N/A"
        topics = repo.get("topics", [])
        updated_at = repo.get("updated_at", "")
        created_at = repo.get("created_at", "")
        homepage = repo.get("homepage") or "None"
        open_issues = repo.get("open_issues_count", 0)

        print(f"[{idx}/{len(all_repos)}] Fetching README for {name}...")
        readme = fetch_readme(name)

        f.write(f"<a id=\"{idx}-{slug}\"></a>\n")
        f.write(f"## {idx}. [{name}]({html_url})\n\n")
        f.write(f"- **Description**: {desc}\n")
        f.write(f"- **Language**: {lang}\n")
        f.write(f"- **Stars**: {stars} | **Forks**: {forks} | **Open Issues**: {open_issues}\n")
        f.write(f"- **Topics**: {', '.join(topics) if topics else 'None'}\n")
        f.write(f"- **Homepage/Demo**: {homepage}\n")
        f.write(f"- **Created**: {created_at} | **Last Updated**: {updated_at}\n\n")
        f.write("### README Content:\n\n")
        f.write("````markdown\n")
        f.write(readme.strip() + "\n")
        f.write("````\n\n")
        f.write("---\n\n")
        f.flush()
        time.sleep(0.2)

print(f"\nDone! All repo metadata and READMEs saved to {output_file}")
