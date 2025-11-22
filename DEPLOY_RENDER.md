# Deploying to Render.com

This guide shows you how to deploy the MCU Green Agent A2A server to Render.com.

## Prerequisites

- A Render.com account (free tier available)
- A GitHub account (to connect your repository)
- Your OpenAI API key

## Step 1: Push to GitHub

If you haven't already, push your code to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: MCU Green Agent A2A Server"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 2: Create Render Service

### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create the service
5. Set the `OPENAI_API_KEY` environment variable in the dashboard

### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `mcu-green-agent`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python a2a_server.py --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

## Step 3: Set Environment Variables

In the Render dashboard, go to your service → Environment:

1. Add `OPENAI_API_KEY`:
   - Key: `OPENAI_API_KEY`
   - Value: Your OpenAI API key (starts with `sk-`)
   - Mark as "Secret"

## Step 4: Deploy

Render will automatically:
1. Build your application
2. Install dependencies
3. Start the server
4. Provide a public URL (e.g., `https://mcu-green-agent.onrender.com`)

## Step 5: Test Your Deployment

Once deployed, test your endpoints:

```bash
# Replace with your Render URL
RENDER_URL="https://mcu-green-agent.onrender.com"

# Health check
curl $RENDER_URL/health

# Agent card
curl $RENDER_URL/.well-known/agent.json

# List tasks
curl $RENDER_URL/a2a/tasks

# Generate a task (requires OPENAI_API_KEY)
curl -X POST $RENDER_URL/a2a/task/generate \
  -H "Content-Type: application/json" \
  -d '{"task_type": "atomic", "difficulty": "simple"}'
```

## Step 6: Register with AgentBeats

1. Copy your Render URL (e.g., `https://mcu-green-agent.onrender.com`)
2. Go to [AgentBeats](https://v2.agentbeats.org/main)
3. Login with GitHub
4. Register your green agent with the Render URL

## Configuration Details

### render.yaml

The `render.yaml` file configures:
- Service type: Web service
- Build command: Installs Python dependencies
- Start command: Runs the FastAPI server
- Health check: Uses `/health` endpoint
- Environment variables: `OPENAI_API_KEY` (set in dashboard)

### Port Configuration

The server automatically uses:
1. `PORT` environment variable (set by Render)
2. Falls back to port 8000 for local development

### Free Tier Limitations

Render's free tier:
- Services spin down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- 750 hours/month free
- For production, consider upgrading to a paid plan

## Troubleshooting

### Service won't start

1. Check build logs in Render dashboard
2. Verify all dependencies are in `requirements.txt`
3. Check that `OPENAI_API_KEY` is set
4. Review server logs for errors

### Health check failing

- Verify `/health` endpoint works locally
- Check that the server is binding to `0.0.0.0`
- Ensure port is using `$PORT` environment variable

### Task generation not working

- Verify `OPENAI_API_KEY` is set correctly in Render dashboard
- Check API key has credits/quota
- Review server logs for OpenAI API errors

### Slow first request

- This is normal on free tier (cold start)
- Consider upgrading to paid plan for always-on service
- Or use a service like UptimeRobot to ping your service periodically

## Updating Your Deployment

Render automatically deploys when you push to your main branch:

```bash
git add .
git commit -m "Update deployment"
git push
```

Render will:
1. Detect the push
2. Rebuild the service
3. Deploy the new version
4. Keep the same URL

## Environment Variables

Set these in Render dashboard → Environment:

- `OPENAI_API_KEY` (required): Your OpenAI API key for task generation and evaluation
- `PORT` (automatic): Set by Render, don't override

## Custom Domain (Optional)

1. Go to your service → Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed by Render
4. Update AgentBeats with your custom domain

## Monitoring

Render provides:
- Build logs
- Runtime logs
- Metrics (CPU, memory, requests)
- Automatic HTTPS

Access these in your Render dashboard.

