"""
Hugging Face Spaces Entry Point for Modern Educational Complex SMS.
Combines FastAPI with Gradio mounting to run on port 7860 seamlessly.
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import gradio as gr
import uvicorn
from database.connection import db_manager
from database.demo_seeder import seed_demo_environment
from src.web.app import app as fastapi_app

# 1. Initialize Relational Database
db_manager.init_database()
seed_demo_environment()

# 2. Mount Gradio interface so Hugging Face Space health check passes
demo = gr.Blocks(title="Modern Educational Complex Admin System")
with demo:
    gr.Markdown("# Modern Educational Complex - SMS")
    gr.Markdown("The main administrative portal is live at the root `/` URL.")

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
