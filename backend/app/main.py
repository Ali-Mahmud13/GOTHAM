"""Main application."""

import inngest.fast_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import setup_logging
from app.inngest import inngest_client, ALL_FUNCTIONS
from app.api.chat import router as chat_router


# Setup
setup_logging()
app = FastAPI(title="GOTHAM - Medical Agent System")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Inngest
inngest.fast_api.serve(app, inngest_client, ALL_FUNCTIONS)

# Register API routes
app.include_router(chat_router, prefix="/api")




@app.get("/")
async def root():
    return {"app": "GOTHAM", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
