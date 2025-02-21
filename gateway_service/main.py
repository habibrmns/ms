from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

app = FastAPI()

async def forward_request(service_url: str, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=service_url,
            headers=request.headers,
            params=request.query_params,
            content=await request.body(),
        )
    return Response(content=response.content, status_code=response.status_code, headers=response.headers)

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH"])
async def auth_proxy(path: str, request: Request):
    return await forward_request(f"http://localhost:8001/{path}", request)

@app.api_route("/products/{path:path}", methods=["GET", "POST", "PUT", "PATCH"])
async def product_proxy(path: str, request: Request):
    return await forward_request(f"http://localhost:8002/{path}", request)

@app.api_route("/orders/{path:path}", methods=["GET", "POST"])
async def order_proxy(path: str, request: Request):
    return await forward_request(f"http://localhost:8003/{path}", request)