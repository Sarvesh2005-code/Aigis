# Aigis - AI Video Clipping & Generation Platform

A full-featured video clipping and generation platform inspired by ClipForge and Opus Clip. Generate viral YouTube Shorts from topics or intelligently clip existing videos with AI-powered features.

## Features

### 🎬 Video Clipping
- **Intelligent Clip Detection**: Automatically finds the best moments from long videos
- **AI Auto-Framing**: Dynamically tracks speakers and adjusts camera focus
- **Virality Prediction**: Scores clips 0-100 based on viral potential
- **Animated Captions**: Word-level animated subtitles with customizable styles
- **Multi-Clip Generation**: Generate multiple clips from a single video

### ✨ AI Video Generation
- **Topic-Based Generation**: Create videos from any topic using AI
- **Script Generation**: Powered by Google Gemini
- **Stock Footage Integration**: Automatically fetches relevant videos from Pexels
- **Text-to-Speech**: Natural voice synthesis using Edge TTS
- **Auto-Assembly**: Combines visuals, audio, and captions automatically

### 🚀 Production Ready
- **Database Persistence**: Jobs persist across restarts using SQLite
- **Keep-Alive Service**: Prevents sleep mode on Render free tier (pings every 14 minutes)
- **Error Handling**: Comprehensive error handling and validation
- **Health Checks**: Monitor service status, disk space, and API keys
- **Rate Limiting**: Built-in rate limiting for API endpoints

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 15 (React, TypeScript)
- **Database**: SQLite (SQLModel)
- **Video Processing**: MoviePy, OpenCV, MediaPipe
- **AI/ML**: Faster Whisper, Google Gemini, Edge TTS
- **Deployment**: Render.com (Free Tier Compatible)

## Setup

### Prerequisites

- Python 3.10+
- Node.js 20+
- Google API Key (for Gemini)
- Pexels API Key (for stock footage)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd aigis
   ```

2. **Install Python dependencies**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

3. **Install Node dependencies**
   ```bash
   cd ../client
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Create data directories**
   ```bash
   mkdir -p server/data/outputs
   mkdir -p server/data/temp
   ```

6. **Run development servers**
   ```bash
   # From root directory
   npm run dev
   ```

   This starts:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000

## Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here  # Optional
ALLOWED_ORIGINS=http://localhost:3000
RENDER_URL=https://your-app.onrender.com  # For keep-alive
```

### Getting API Keys

- **Google API Key**: https://makersuite.google.com/app/apikey
- **Pexels API Key**: https://www.pexels.com/api/
- **YouTube API Key**: https://console.cloud.google.com/apis/credentials (optional)

## Deployment on Render

### Free Tier Setup

1. **Connect GitHub Repository**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select the `aigis` repository

2. **Configure Service**
   - **Name**: `aigis-core`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `.`
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `cd server && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

3. **Environment Variables**
   Add these in Render dashboard:
   - `GOOGLE_API_KEY`: Your Google API key
   - `PEXELS_API_KEY`: Your Pexels API key
   - `RENDER_URL`: Will be auto-set, but you can manually set it
   - `NEXT_PUBLIC_API_URL`: Your Render app URL (e.g., `https://aigis-core.onrender.com/api`)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete
   - Your app will be live!

### Keep-Alive Service

The app includes an automatic keep-alive service that pings the health endpoint every 14 minutes to prevent Render's free tier from sleeping. This ensures 24/7 operation.

## API Endpoints

### Clipping Jobs

- `POST /api/jobs` - Create a new clipping job
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/jobs` - List all jobs
- `POST /api/jobs/detect-clips` - Detect best clips from a video

### Generation Jobs

- `POST /api/generate` - Create a new generation job
- `GET /api/generate/{job_id}` - Get generation job status
- `GET /api/generate/jobs` - List all generation jobs

### Health

- `GET /api/health` - Comprehensive health check
- `GET /` - Simple health check

## Project Structure

```
aigis/
├── server/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core processing logic
│   │   ├── db/           # Database models and engine
│   │   └── main.py        # FastAPI app
│   ├── data/             # Outputs and temp files
│   └── requirements.txt
├── client/
│   ├── src/
│   │   ├── app/          # Next.js app
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── package.json
├── build.sh              # Build script
├── render.yaml           # Render configuration
└── README.md
```

## Features in Detail

### Virality Prediction

The virality scorer analyzes:
- **Hook Quality**: First 3 seconds engagement
- **Pacing**: Words per second (optimal: 2-4 WPS)
- **Length**: Optimal 15-60 seconds for shorts
- **Captions**: Presence of subtitles
- **Visual Quality**: Resolution and clarity

### Intelligent Clip Detection

Automatically finds the best moments by analyzing:
- Speaker changes
- Emotional peaks
- Engagement words
- Question/exclamation patterns
- Optimal segment lengths

### Animated Captions

- Word-level timestamps from Whisper
- Customizable styles (font, color, position)
- Automatic subtitle generation
- SRT file export

## Troubleshooting

### Build Failures
- Ensure all dependencies are in `requirements.txt`
- Check Python version (3.10+)
- Verify Node.js version (20+)

### API Key Errors
- Verify keys are set in environment variables
- Check key permissions
- Check API quotas

### Video Processing Issues
- Ensure sufficient disk space
- Check video format compatibility
- Verify MoviePy dependencies

### Keep-Alive Not Working
- Check `RENDER_URL` is set correctly
- Verify health endpoint is accessible
- Check logs for keep-alive errors

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Inspired by:
- [Opus Clip](https://opus.pro) - AI video clipping
- [ClipForge](https://getclipforge.com) - Video repurposing

Built with:
- FastAPI
- Next.js
- MoviePy
- MediaPipe
- Faster Whisper

