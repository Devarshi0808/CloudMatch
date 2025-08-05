# CloudMatch Vercel Deployment Guide

## Overview

This project has been configured for deployment on Vercel with the following components:

- **API Backend**: Python serverless functions in `/api/index.py`
- **Frontend**: Static HTML interface in `/public/index.html`
- **Configuration**: Vercel settings in `vercel.json`

## Deployment Structure

```
CloudMatch/
├── api/
│   └── index.py              # Serverless API functions
├── public/
│   └── index.html            # Static frontend
├── src/                      # Core application logic
├── data/                     # Data files
├── vercel.json              # Vercel configuration
└── requirements-vercel.txt   # Python dependencies
```

## API Endpoints

- `GET /` - Frontend interface
- `GET /api/health` - Health check
- `GET /api/search?vendor=<vendor>&solution=<solution>` - Search via GET
- `POST /api/search` - Search via POST with JSON body

## Environment Variables

No environment variables are required for basic functionality.

## Dependencies

The following Python packages are required (see `requirements-vercel.txt`):

- requests==2.31.0
- pandas==2.1.4
- scikit-learn==1.3.2
- fuzzywuzzy==0.18.0
- rapidfuzz==3.13.0
- beautifulsoup4==4.12.2
- openpyxl==3.1.2

## Deployment Steps

1. **Connect Repository**: Link your GitHub repository to Vercel
2. **Auto-Deploy**: Vercel will automatically deploy on push to main branch
3. **Environment**: Vercel will use the Python runtime and install dependencies
4. **Domain**: Your app will be available at `your-project.vercel.app`

## Testing the Deployment

1. Visit your Vercel domain
2. Try searching for vendors like "Red Hat" or "Adobe"
3. Test the API directly: `https://your-domain.vercel.app/api/health`

## Troubleshooting

### Common Issues

1. **Import Errors**: Check that all dependencies are in `requirements-vercel.txt`
2. **File Not Found**: Ensure data files are in the correct location
3. **Timeout**: API functions have 30-second timeout limit

### Debugging

- Check Vercel function logs in the dashboard
- Test API endpoints directly
- Verify file paths are correct for serverless environment

## Local Development

To test locally before deploying:

```bash
# Install dependencies
pip install -r requirements-vercel.txt

# Test API locally
python -m http.server 8000
# Then visit http://localhost:8000/public/index.html
```

## Performance Notes

- API functions have 30-second timeout
- Static files are served from CDN
- Database operations use SQLite (read-only in serverless)
- Caching is implemented for search results

## Security

- CORS is enabled for all origins
- Input validation is implemented
- Error handling prevents information leakage
- No sensitive data in environment variables 