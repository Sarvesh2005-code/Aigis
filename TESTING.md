# Testing Guide for Aigis

## Prerequisites for Full Testing

To test video generation in both modes, you need:

1. **Google API Key** - For script generation (Gemini)
   - Get from: https://makersuite.google.com/app/apikey
   - Set as: `GOOGLE_API_KEY` in `.env`

2. **Pexels API Key** - For stock video footage
   - Get from: https://www.pexels.com/api/
   - Set as: `PEXELS_API_KEY` in `.env`

3. **YouTube URL** - For clipping mode (any public YouTube video works)

## Quick Test (Without API Keys)

The application will start and endpoints will work, but:
- Clipping mode: Will work (only needs YouTube URL)
- Generation mode: Will fail without API keys

## Running Tests

### 1. Start the Server

```bash
cd server
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Test Health Endpoint

```bash
curl http://localhost:8000/
curl http://localhost:8000/api/health
```

### 3. Test Clipping Mode

```bash
# Create a clipping job
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Get job status (replace JOB_ID)
curl http://localhost:8000/api/jobs/JOB_ID
```

### 4. Test Generation Mode (Requires API Keys)

```bash
# Create a generation job
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "The future of AI"}'

# Get job status (replace JOB_ID)
curl http://localhost:8000/api/generate/JOB_ID
```

## Expected Behavior

### Clipping Mode
1. Job created with status "pending"
2. Status changes to "downloading" → "processing" → "completed"
3. Output file available at `/outputs/clip_{job_id}.mp4`
4. Virality score calculated (0-100)

### Generation Mode
1. Job created with status "pending"
2. Status changes to "processing" with progress updates
3. Steps: Script generation → Visual fetching → Audio generation → Video assembly
4. Output file available at `/outputs/{job_id}.mp4`
5. Virality score calculated (0-100)

## Troubleshooting

### Server Won't Start
- Check Python version (3.10+)
- Install dependencies: `pip install -r requirements.txt`
- Check for port conflicts (8000)

### Jobs Fail
- Check API keys in `.env`
- Check disk space in `server/data/`
- Check logs for specific errors

### MediaPipe Warning
- This is normal if MediaPipe isn't fully installed
- Face detection will default to center framing
- Video processing will still work

## Notes

- First run will download Whisper model (~75MB)
- Video processing can take 2-10 minutes depending on length
- Generated videos are saved in `server/data/outputs/`

