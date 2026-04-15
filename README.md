# YouTube Summarizer 4.6

## Setup

Add your OpenAI API key to `backend/.env`:

```
OPENAI_API_KEY=your_key_here
```

## Running

```bash
docker-compose up -d --build
```

Connect to the frontend at http://localhost:3002

## Working Around YouTube IP Blocks

If YouTube blocks transcript fetching from your server's IP, you can authenticate requests using cookies exported from a browser where you're logged into YouTube.

**1. Export your cookies**

Install a browser extension that exports cookies in Netscape/Mozilla format (e.g. "Get cookies.txt LOCALLY" for Chrome/Firefox). Export cookies for `youtube.com` and save the file as `cookies.txt` in the project root.

**2. Restart the backend**

```bash
docker-compose restart backend
```

The backend mounts `cookies.txt` automatically and uses it if present. If the file doesn't exist, requests fall back to unauthenticated. Cookies expire over time — re-export and restart if blocking resumes.
