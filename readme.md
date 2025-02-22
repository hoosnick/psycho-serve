# FastAPI Proxy Server

This is a FastAPI-powered proxy server that doesn't give a damn about your feelings.

## Quick Start

```bash
# Get this bad boy running
pip install fastapi httpx uvicorn

# Fire it up
python main.py
```

## Environment Variables

```shell
ALLOWED_HOSTS=http://localhost:3000,https://ur.domain.com
```

## Usage

```bash
# Hit it like this
http://your-server/?url=https://target-url.com
```

## Warning

This proxy is so permissive it'll forward anything. If you deploy this in prod without proper security, you deserve what's coming to you.

## That's it

Now get back to work, you absolute psychopath.
