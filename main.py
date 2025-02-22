import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI()

# Configure CORS:
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "*")

ALLOWED_ORIGINS = (
    ["*"]
    if ALLOWED_ORIGINS_ENV == "*"
    else [url.strip() for url in ALLOWED_ORIGINS_ENV.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


@app.api_route("/", methods=ALLOWED_METHODS)
async def proxy(request: Request):
    # Extract the target URL from the query parameter
    target_url = request.query_params.get("url")
    if not target_url:
        raise HTTPException(
            status_code=400,
            detail="Missing 'url' query parameter",
        )

    # Get any additional query parameters passed to the proxy (excluding 'url')
    forwarded_params = [
        (k, v) for k, v in request.query_params.multi_items() if k != "url"
    ]

    # Parse the target URL to extract its own query parameters
    parsed_url = urlsplit(target_url)
    existing_params = parse_qsl(parsed_url.query)

    # Merge the original target URL parameters with the forwarded ones.
    merged_params = existing_params + forwarded_params
    new_query = urlencode(merged_params, doseq=True)

    # Rebuild the target URL with the merged query string
    target_url = urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            new_query,
            parsed_url.fragment,
        )
    )

    # Remove the "host" header to allow httpx to set it appropriately.
    headers = dict(request.headers)
    headers.pop("host", None)

    # Get the raw body (if any) from the incoming request
    body = await request.body()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=30.0,
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error forwarding request: {e}",
        )

    # Filter out hop-by-hop headers from the response
    response_headers = {
        k: v
        for k, v in response.headers.items()
        if k.lower()
        not in [
            "content-encoding",
            "transfer-encoding",
            "connection",
        ]
    }

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
    )


if __name__ == "__main__":
    uvicorn.run(app)
