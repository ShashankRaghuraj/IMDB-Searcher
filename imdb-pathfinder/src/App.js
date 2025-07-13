import React, { useState, useRef } from "react";

const BACKEND_URL = "http://localhost:5000/race";
const AUTOCOMPLETE_PERSON_URL = "http://localhost:5000/autocomplete/person";
const AUTOCOMPLETE_MOVIE_URL = "http://localhost:5000/autocomplete/movie";

function App() {
  const [start, setStart] = useState("");
  const [target, setTarget] = useState("");
  const [path, setPath] = useState([]);
  const [error, setError] = useState("");
  const [personSuggestions, setPersonSuggestions] = useState([]);
  const [movieSuggestions, setMovieSuggestions] = useState([]);
  const [showPersonSuggestions, setShowPersonSuggestions] = useState(false);
  const [showMovieSuggestions, setShowMovieSuggestions] = useState(false);
  const personInputRef = useRef();
  const movieInputRef = useRef();

  async function fetchPath() {
    setError("");
    setPath([]);
    if (!start || !target) {
      setError("Please fill both fields.");
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL}?start=${encodeURIComponent(start)}&target=${encodeURIComponent(target)}`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else if (data.path) {
        setPath(data.path);
      }
    } catch (e) {
      setError("Failed to fetch path.");
    }
  }

  async function fetchPersonSuggestions(query) {
    if (!query || query.length < 3) {
      setPersonSuggestions([]);
      return;
    }
    try {
      const res = await fetch(`${AUTOCOMPLETE_PERSON_URL}?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      // Filter: only show names that start with the query (case-insensitive)
      let filtered = data.filter(p => p.name.toLowerCase().startsWith(query.toLowerCase()));
      // Remove duplicates by name
      const seen = new Set();
      filtered = filtered.filter(p => {
        if (seen.has(p.name.toLowerCase())) return false;
        seen.add(p.name.toLowerCase());
        return true;
      });
      setPersonSuggestions(filtered.slice(0, 5));
    } catch {
      setPersonSuggestions([]);
    }
  }

  async function fetchMovieSuggestions(query) {
    if (!query || query.length < 3) {
      setMovieSuggestions([]);
      return;
    }
    try {
      const res = await fetch(`${AUTOCOMPLETE_MOVIE_URL}?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      // Filter: only show titles that start with the query (case-insensitive)
      const filtered = data.filter(m => m.title.toLowerCase().startsWith(query.toLowerCase()));
      setMovieSuggestions(filtered.slice(0, 5));
    } catch {
      setMovieSuggestions([]);
    }
  }

  function getDisplayName(type, id, path, idx) {
    // Try to get name/title from previous node in path
    const node = path[idx];
    if (type === "person" && node.name) return node.name;
    if (type === "movie" && node.title) return node.title;
    // fallback to id if not available
    return id;
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>IMDb Path Finder</h1>
      <div style={{ position: "relative", marginBottom: 16 }}>
        <input
          ref={personInputRef}
          placeholder="Start Person"
          value={start}
          onChange={e => {
            setStart(e.target.value);
            fetchPersonSuggestions(e.target.value);
            setShowPersonSuggestions(true);
          }}
          onBlur={() => setTimeout(() => setShowPersonSuggestions(false), 100)}
          onFocus={() => start && setShowPersonSuggestions(true)}
          autoComplete="off"
        />
        {showPersonSuggestions && personSuggestions.length > 0 && (
          <ul style={{ position: "absolute", left: 0, right: 0, top: "100%", background: "#fff", border: "1px solid #ccc", zIndex: 10, listStyle: "none", margin: 0, padding: 0 }}>
            {personSuggestions.map(s => (
              <li
                key={s.id}
                style={{ padding: "4px 8px", cursor: "pointer" }}
                onMouseDown={() => {
                  setStart(s.name);
                  setShowPersonSuggestions(false);
                  setPersonSuggestions([]);
                  personInputRef.current.blur();
                }}
              >
                {s.name}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div style={{ position: "relative", marginBottom: 16 }}>
        <input
          ref={movieInputRef}
          placeholder="Target Movie"
          value={target}
          onChange={e => {
            setTarget(e.target.value);
            fetchMovieSuggestions(e.target.value);
            setShowMovieSuggestions(true);
          }}
          onBlur={() => setTimeout(() => setShowMovieSuggestions(false), 100)}
          onFocus={() => target && setShowMovieSuggestions(true)}
          autoComplete="off"
        />
        {showMovieSuggestions && movieSuggestions.length > 0 && (
          <ul style={{ position: "absolute", left: 0, right: 0, top: "100%", background: "#fff", border: "1px solid #ccc", zIndex: 10, listStyle: "none", margin: 0, padding: 0 }}>
            {movieSuggestions.map(s => (
              <li
                key={s.id}
                style={{ padding: "4px 8px", cursor: "pointer" }}
                onMouseDown={() => {
                  setTarget(s.title);
                  setShowMovieSuggestions(false);
                  setMovieSuggestions([]);
                  movieInputRef.current.blur();
                }}
              >
                {s.title}
              </li>
            ))}
          </ul>
        )}
      </div>
      <button onClick={fetchPath}>Find Path</button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ marginTop: 20 }}>
        {path.length > 0 && (
          <ol>
            {path.map(({ type, id }, idx) => (
              <li key={`${type}-${id}`}>
                <strong>{type}</strong> — {getDisplayName(type, id, path, idx)}
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

export default App;
