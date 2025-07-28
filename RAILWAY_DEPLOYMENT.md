# Railway Deployment Guide

## Prerequisites

1. Railway account
2. MongoDB Atlas database
3. OpenAI API key

## Environment Variables Setup

Set these environment variables in your Railway project:

### Required Variables

```bash
# OpenAI API Key
OPENAI_API_KEY=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

# MongoDB Configuration
MONGO_USER=your_mongo_username
MONGO_PWD=your_mongo_password
MONGO_HOST=cluster0.wj29w.mongodb.net
MONGO_DATABASE=cluvoai

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth Configuration (if using Google auth)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-railway-app.railway.app/api/v1/auth/oauth/google/callback
```

### Optional Variables

```bash
# RapidAPI Key (for additional data sources)
RAPIDAPI_KEY=your_rapidapi_key

# Reddit API (optional)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# LLM Configuration
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
MAX_TOKENS=2000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

## Deployment Steps

1. **Connect your GitHub repository to Railway**
2. **Set environment variables** in Railway dashboard
3. **Deploy** - Railway will automatically build and deploy your app
4. **Check health** - Visit your app URL to verify it's running

## Health Check

The app includes a health check endpoint at `/` that returns:

```json
{
  "service": "Cluvo.ai AI Business Intelligence API",
  "version": "1.0.0",
  "status": "healthy",
  "database": "connected"
}
```

## Troubleshooting

### Database Connection Issues

1. **Check MongoDB credentials** - Ensure MONGO_USER, MONGO_PWD, and MONGO_HOST are correct
2. **Verify MongoDB Atlas** - Make sure your MongoDB Atlas cluster is running
3. **Network access** - Ensure your MongoDB Atlas allows connections from Railway's IP ranges

### API Key Issues

1. **OpenAI API Key** - Verify the API key is valid and has sufficient credits
2. **RapidAPI Key** - Check if RapidAPI key is required for your use case

### Common Errors

- **"Database not connected"** - Check MongoDB environment variables
- **"OpenAI API key not set"** - Verify OPENAI_API_KEY is set in Railway
- **"Port already in use"** - Railway handles this automatically

## Monitoring

- Check Railway logs for detailed error messages
- Monitor the health check endpoint
- Use Railway's built-in monitoring tools

## Security Notes

- Never commit `.env` files to your repository
- Use strong JWT secrets in production
- Regularly rotate API keys
- Enable MongoDB Atlas security features 