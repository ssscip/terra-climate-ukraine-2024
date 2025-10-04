# Deployment Notes (TerraTales)

## Local Dev (Docker Compose)
```
cd infrastructure
docker compose -f docker-compose.dev.yml up --build
```
API: http://localhost:8000/api/events
Web: http://localhost:5173

## Production Sketch
1. Build images:
   - `docker build -t terratales-api -f infrastructure/Dockerfile.api .`
   - `docker build -t terratales-web -f infrastructure/Dockerfile.web .`
2. Push to registry.
3. Run behind reverse proxy (nginx / Traefik) with TLS.
4. Configure CDN/cache for `/assets` (static globe_assets).
5. (Optional) Add PMTiles server or static hosting for `events.pmtiles`.

## Scaling
- API is stateless, horizontally scalable.
- Static globe layers (PNG/PMTiles) served via CDN.
- Add caching headers (Cache-Control) for assets.

## Observability
- Add `/health` endpoint (TODO).
- Structured logging (uvicorn --log-config) (TODO).

## Security
- Read-only catalog (no auth needed initially).
- Add rate limiting if public.

## Roadmap
- Add real COG tile generation and vector tile pipeline.
- Integrate more Terra instruments (ASTER, MISR, MOPITT, CERES).
- Pre-compute time-series sparkline JSON per metric.
