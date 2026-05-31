# Deployment Guide

## Local Development (Default)

```bash
cd flask_app
python app.py
# Runs on http://localhost:5000 with debug mode
```

---

## Production Deployment with Gunicorn

```bash
# Install gunicorn (included in requirements.txt)
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Or with environment file
gunicorn -w 4 -b 0.0.0.0:8000 --env-file .env app:app
```

---

## Docker Deployment

Create `Dockerfile` in `flask_app/`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_DEBUG=false

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
# Build and run
docker build -t retail-analytics .
docker run -p 5000:5000 --env-file .env retail-analytics
```

---

## Cloud Deployment (Render.com — Free Tier)

1. Push code to GitHub
2. Create account at https://render.com
3. **New → Web Service** → Connect your GitHub repo
4. Set:
   - **Build Command**: `pip install -r flask_app/requirements.txt`
   - **Start Command**: `cd flask_app && gunicorn app:app`
5. Add all environment variables from `.env`
6. Deploy!

---

## Environment Variables for Production

| Variable | Required | Notes |
|----------|----------|-------|
| `SNOWFLAKE_ACCOUNT` | Yes | Your account identifier |
| `SNOWFLAKE_USER` | Yes | Service account username |
| `SNOWFLAKE_PASSWORD` | Yes | Use secrets manager in prod |
| `SNOWFLAKE_WAREHOUSE` | No | Default: RETAIL_WH |
| `SNOWFLAKE_DATABASE` | No | Default: RETAIL_DW |
| `GEMINI_API_KEY` | Yes | Google AI Studio key |
| `FLASK_SECRET_KEY` | Yes | Random 32+ char string |
| `FLASK_DEBUG` | No | Set to `false` in prod |

---

## Security Checklist

- [ ] `FLASK_DEBUG=false` in production
- [ ] `FLASK_SECRET_KEY` is a random secret (not the default)
- [ ] `.env` file is NOT committed to Git (add to `.gitignore`)
- [ ] Snowflake role has minimum required privileges
- [ ] HTTPS is enabled (use nginx/Cloudflare in front)
- [ ] Rate limiting applied to `/api/ask` endpoint
