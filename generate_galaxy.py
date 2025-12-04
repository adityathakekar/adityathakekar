import os
import requests
import math

# CONFIGURATION
# Replace with your username if not setting env var
USERNAME = os.environ.get('GH_USERNAME', 'torvalds') 
TOKEN = os.environ.get('GH_TOKEN') # Optional: Increases API limits
OUTPUT_FILE = 'github-galaxy.svg'
MAX_REPOS = 8
WIDTH = 800
HEIGHT = 400

# Language Colors
LANG_COLORS = {
    'JavaScript': '#f1e05a', 'TypeScript': '#2b7489', 'Python': '#3572A5',
    'Java': '#b07219', 'HTML': '#e34c26', 'CSS': '#563d7c',
    'Go': '#00ADD8', 'Rust': '#dea584', 'C++': '#f34b7d',
    'C': '#555555', 'Shell': '#89e051', 'PHP': '#4F5D95'
}

def get_color(lang):
    return LANG_COLORS.get(lang, '#FFFFFF')

def fetch_github_data():
    headers = {'Authorization': f'token {TOKEN}'} if TOKEN else {}
    
    print(f"Fetching data for {USERNAME}...")
    
    # 1. Fetch User
    user_resp = requests.get(f'https://api.github.com/users/{USERNAME}', headers=headers)
    if user_resp.status_code != 200:
        raise Exception(f"Error fetching user: {user_resp.status_code}")
    user = user_resp.json()

    # 2. Fetch Repos
    repos_resp = requests.get(f'https://api.github.com/users/{USERNAME}/repos?sort=pushed&per_page=100', headers=headers)
    repos = repos_resp.json()

    if not isinstance(repos, list):
        raise Exception(f"Error fetching repos: {repos.get('message', 'Unknown error')}")

    # Filter forks and sort by stars
    top_repos = [r for r in repos if not r.get('fork', False)]
    top_repos.sort(key=lambda x: x['stargazers_count'], reverse=True)
    
    return user, top_repos[:MAX_REPOS]

def generate_svg():
    try:
        user, top_repos = fetch_github_data()
    except Exception as e:
        print(e)
        return

    print(f"Found {len(top_repos)} repos. Generating Galaxy...")

    # Math Helpers
    max_stars = max([r['stargazers_count'] for r in top_repos]) if top_repos else 1
    
    # SVG Strings
    svg_elements = []
    
    # 1. CSS Styles
    css = """
    <style>
      .orbit { fill: none; stroke: #30363d; stroke-width: 1px; }
      .planet-group { animation: rotate linear infinite; transform-box: fill-box; transform-origin: center; }
      .text-label { font-family: sans-serif; fill: #c9d1d9; font-size: 10px; opacity: 0.8; }
      .star-bg { fill: #ffffff; opacity: 0.2; }
      @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      @keyframes counter-rotate { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    </style>
    """
    svg_elements.append(css)

    # 2. Background
    svg_elements.append(f'<rect width="100%" height="100%" fill="#0d1117" rx="10" />')
    
    # 3. Center Sun (User)
    center_x, center_y = WIDTH / 2, HEIGHT / 2
    svg_elements.append(f'''
    <g transform="translate({center_x}, {center_y})">
      <circle r="40" fill="#161b22" stroke="#c9d1d9" stroke-width="2" />
      <text y="5" text-anchor="middle" fill="#c9d1d9" font-weight="bold" font-family="sans-serif">
        {user['login'].upper()}
      </text>
    </g>
    ''')

    # 4. Planets
    for i, repo in enumerate(top_repos):
        # Orbit Radius (Linear scale)
        radius = 80 + (i * (170 / MAX_REPOS))
        
        # Planet Size (Log scale)
        star_count = repo['stargazers_count']
        size = 8
        if star_count > 0:
            # Simple log scale simulation
            size = 8 + (math.log(star_count) * 2)
        size = min(max(size, 8), 25) # Clamp size
        
        color = get_color(repo['language'])
        duration = 15 + (i * 5)
        
        svg_elements.append(f'''
        <circle cx="{center_x}" cy="{center_y}" r="{radius}" class="orbit" />
        <g transform="translate({center_x}, {center_y})" style="animation-duration: {duration}s" class="planet-group">
            <g transform="translate({radius}, 0)">
                <g style="animation: counter-rotate {duration}s linear infinite; transform-box: fill-box; transform-origin: center;">
                    <circle r="{size}" fill="{color}" stroke="#0d1117" stroke-width="2" />
                    <text y="{size + 12}" text-anchor="middle" class="text-label">{repo['name']}</text>
                </g>
            </g>
        </g>
        ''')

    final_svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">' + "".join(svg_elements) + '</svg>'

    with open(OUTPUT_FILE, 'w') as f:
        f.write(final_svg)
    
    print(f"Success! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_svg()
