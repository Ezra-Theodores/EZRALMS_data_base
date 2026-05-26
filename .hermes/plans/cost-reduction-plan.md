# Firebase Cost Reduction — Caching Implementation Plan

## Problem
Every time a user opens the EZRA LMS web UI (hosted on Netlify), the app calls Firebase Firestore directly for data. Firestore charges per document read — every `collection.stream()`, `get()`, or `get_doc()` call is a billed operation. With hundreds of students and repeated page loads, costs accumulate rapidly.

## What Already Works
- Firebase → SQLite sync exists (`/api/sync/all`) — this pulls all Firestore data into `ezralms_unified.db` locally
- The web UI serves student profiles, leaderboards, and attendance from SQLite (not Firebase directly)
- `student_tracking_bp.py`, `attendance_bp.py`, `rag_bp.py` all read from local SQLite only

## What Still Costs Money
| Endpoint | Cost driver | Frequency |
|---|---|---|
| `/api/sync/all` (POST) | `fs.collection(X).stream()` × 4 collections | Manual trigger only — OK |
| `/api/students/profile/<id>` | No caching — rebuilds all data on every request | Every page load |
| `/api/students/leaderboard` | Complex SQL with subqueries, no caching | Every page load / refresh |
| `/api/rag/search` | BM25 search over full corpus, no caching | Every search query |
| **All endpoints** | No `Cache-Control`, no `ETag` — Netlify can't cache | Every page load |

## Solution: Multi-Layer Caching

### Layer 1 — HTTP Cache Headers (zero-cost, biggest impact)
Add to **ALL** `/api/` endpoints that read from SQLite:
```
Cache-Control: public, max-age=30, stale-while-revalidate=300
ETag: "<hash-of-response>"
```
Netlify CDN honors these → serves from edge cache without hitting the origin server at all.

### Layer 2 — In-Process TTL Cache for Student Profiles
File: `blueprints/_cache.py` (new)

```
@cache(ttl=120, key="student_profile:{student_id}")
def get_cached_student_profile(student_id):
    # existing profile building logic
```

- Student profile is expensive to build (joins quiz_attempts, attendance, xp_transactions, task_assignments)
- Profile doesn't change between syncs — 2-minute TTL is fine
- Invalidation: clear on next `/api/sync/all` call

### Layer 3 — In-Process TTL Cache for Leaderboard
Same `_cache.py`:
```
@cache(ttl=60, key="leaderboard")
def get_cached_leaderboard():
    # existing leaderboard SQL
```

### Layer 4 — RAG Search Cache
```
@cache(ttl=300, key="rag_search:{hash(q)}:{k}")
def cached_rag_search(q, k):
    return dh.search(q, k=k)
```

### Layer 5 — ETag / If-None-Match Support
For student profile and leaderboard — allows browsers/CDN to send `If-None-Match: <etag>` and get `304 Not Modified` if nothing changed.

### Layer 6 — Sync Invalidation Hook
After `/api/sync/all` completes successfully, clear all TTL caches so next read gets fresh data.

## Files to Create/Modify

1. **Create** `blueprints/_cache.py` — TTL cache decorator using `cachetools`
2. **Modify** `blueprints/student_tracking_bp.py`:
   - Add `_cache.py` import
   - Wrap profile and leaderboard with TTL cache
   - Add ETag header + If-None-Match check
   - Add Cache-Control header
   - Call cache clear on `/api/sync/all` completion
3. **Modify** `blueprints/rag_bp.py`:
   - Add RAG search TTL cache
   - Add Cache-Control header
4. **Modify** `blueprints/attendance_bp.py`:
   - Add Cache-Control header to stats/search endpoints
5. **Modify** `blueprints/firebase_sync_bp.py`:
   - After successful sync, emit event to clear caches (or use a shared global dict)
6. **Modify** `blueprints/curriculum_bp.py` — check for any read endpoints and add Cache-Control
7. **Add** `blueprints/_cache_stats.py` — `/api/cache/stats` endpoint for debugging

## Implementation Notes
- Use `cachetools` (pure Python, no Redis dependency) — install if missing: `pip install cachetools`
- TTL cache: `cachetools.TTLCache(maxsize=500, ttl=120)` for profiles, `maxsize=2000, ttl=60` for leaderboard
- RAG cache: `cachetools.TTLCache(maxsize=1000, ttl=300)` with ` keyed by hash(q)+k
- Use a shared module-level cache dict so all blueprints share the same cache
- For cache invalidation on sync: use a `cache_clear()` function in `_cache.py` that all blueprints call
- Do NOT cache `/api/sync/all` itself — it's already a batch job, not a read endpoint
- The `ETag` should be a hash of the serialized response JSON — cheap to generate

## Verification Plan
1. Before changes: note response headers on `/api/students/profile/<id>` — should have no Cache-Control
2. After changes: `curl -I` should show `Cache-Control: public, max-age=30, stale-while-revalidate=300` and `ETag: "..."`
3. Cache stats endpoint `/api/cache/stats` should show hits/misses incrementing
4. After triggering `/api/sync/all`, cache should be cleared (next profile call = miss, then hit)
5. `If-None-Match` test: call with correct ETag → should get `304 Not Modified`
