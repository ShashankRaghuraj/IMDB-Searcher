import requests
from collections import deque
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w300"  # image width 300px

def search_person(name):
    url = f"{BASE_URL}/search/person"
    params = {"api_key": API_KEY, "query": name}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None
    data = res.json()
    if 'results' in data and data['results']:
        return data['results'][0]
    return None

def search_movie(title):
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": title}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None
    data = res.json()
    if 'results' in data and data['results']:
        return data['results'][0]
    return None

def get_person_movie_credits(person_id):
    url = f"{BASE_URL}/person/{person_id}/movie_credits"
    params = {"api_key": API_KEY}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return {"cast": [], "crew": []}
    return res.json()

def get_movie_cast(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": API_KEY}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return {"cast": []}
    return res.json()

def node_with_image(node_type, data):
    if node_type == "person":
        image_url = IMAGE_BASE_URL + data['profile_path'] if data.get('profile_path') else None
        return {"type": "person", "id": data['id'], "name": data['name'], "image_url": image_url}
    else:
        image_url = IMAGE_BASE_URL + data['poster_path'] if data.get('poster_path') else None
        return {"type": "movie", "id": data['id'], "title": data['title'], "image_url": image_url}

def reconstruct_path(meet_node, parents_start, parents_end):
    path_start = []
    cur = meet_node
    while cur is not None:
        path_start.append(cur)
        cur = parents_start.get(cur)
    path_start.reverse()

    path_end = []
    cur = parents_end.get(meet_node)
    while cur is not None:
        path_end.append(cur)
        cur = parents_end.get(cur)

    return path_start + path_end

def _expand_frontier(queue, visited_this_side, visited_other_side, parents_this_side, parents_other_side):
    if not queue:
        return None

    current = queue.popleft()

    neighbors = []
    if current['type'] == "person":
        credits = get_person_movie_credits(current['id'])
        movies = credits.get('cast', [])[:20]
        for movie in movies:
            neighbors.append(node_with_image("movie", movie))
    else:
        cast = get_movie_cast(current['id']).get('cast', [])[:20]
        for person in cast:
            neighbors.append(node_with_image("person", person))

    for neighbor in neighbors:
        neighbor_key = (neighbor['type'], neighbor['id'])

        if neighbor_key in visited_other_side:
            if neighbor_key not in parents_this_side:
                parents_this_side[neighbor_key] = (current['type'], current['id'])
            return neighbor_key

        if neighbor_key not in visited_this_side:
            visited_this_side.add(neighbor_key)
            parents_this_side[neighbor_key] = (current['type'], current['id'])
            queue.append(neighbor)

    return None

def tmdb_bidirectional_racer(start_person_name, target_movie_title, max_depth=6):
    start_person = search_person(start_person_name)
    if not start_person:
        return {"error": f"Start person '{start_person_name}' not found."}

    target_movie = search_movie(target_movie_title)
    if not target_movie:
        return {"error": f"Target movie '{target_movie_title}' not found."}

    start_node = node_with_image("person", start_person)
    target_node = node_with_image("movie", target_movie)

    queue_start = deque([start_node])
    queue_end = deque([target_node])

    visited_start = {(start_node['type'], start_node['id'])}
    visited_end = {(target_node['type'], target_node['id'])}

    parents_start = {(start_node['type'], start_node['id']): None}
    parents_end = {(target_node['type'], target_node['id']): None}

    depth = 0
    while queue_start and queue_end and depth <= max_depth:
        meet_node_key = _expand_frontier(queue_start, visited_start, visited_end, parents_start, parents_end)
        if meet_node_key:
            path = _build_path(meet_node_key, parents_start, parents_end)
            return {"path": path}

        meet_node_key = _expand_frontier(queue_end, visited_end, visited_start, parents_end, parents_start)
        if meet_node_key:
            path = _build_path(meet_node_key, parents_start, parents_end)
            return {"path": path}

        depth += 1

    return {"error": "No path found within max depth."}

def _build_path(meet_node_key, parents_start, parents_end):
    # Build path from start to meeting node
    path_start = []
    cur = meet_node_key
    while cur is not None:
        path_start.append(cur)
        cur = parents_start.get(cur)
    path_start.reverse()

    # Build path from meeting node to target
    path_end = []
    cur = parents_end.get(meet_node_key)
    while cur is not None:
        path_end.append(cur)
        cur = parents_end.get(cur)

    combined_keys = path_start + path_end

    # For simplicity, just return list of dicts with type and id; you can extend to full details
    # Try to get full details for each node
    result = []
    for t, i in combined_keys:
        if t == "person":
            # Search for person name
            url = f"{BASE_URL}/person/{i}"
            params = {"api_key": API_KEY}
            res = requests.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                result.append({"type": t, "id": i, "name": data.get("name", str(i))})
            else:
                result.append({"type": t, "id": i, "name": str(i)})
        elif t == "movie":
            url = f"{BASE_URL}/movie/{i}"
            params = {"api_key": API_KEY}
            res = requests.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                result.append({"type": t, "id": i, "title": data.get("title", str(i))})
            else:
                result.append({"type": t, "id": i, "title": str(i)})
        else:
            result.append({"type": t, "id": i})
    return result

@app.route('/race')
def race():
    start = request.args.get('start')
    target = request.args.get('target')
    if not start or not target:
        return jsonify({"error": "Please provide 'start' and 'target' query parameters."}), 400

    result = tmdb_bidirectional_racer(start, target)
    return jsonify(result)

@app.route('/autocomplete/person')
def autocomplete_person():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    url = f"{BASE_URL}/search/person"
    params = {"api_key": API_KEY, "query": query}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return jsonify([])
    data = res.json()
    results = data.get('results', [])
    suggestions = [{"id": p['id'], "name": p['name']} for p in results[:10]]
    return jsonify(suggestions)

@app.route('/autocomplete/movie')
def autocomplete_movie():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": query}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return jsonify([])
    data = res.json()
    results = data.get('results', [])
    suggestions = [{"id": m['id'], "title": m['title']} for m in results[:10]]
    return jsonify(suggestions)

if __name__ == "__main__":
    app.run(debug=True)
