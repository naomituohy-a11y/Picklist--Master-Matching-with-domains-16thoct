import gradio as gr
import pandas as pd
import openpyxl
from rapidfuzz import fuzz

def greet(name):
    return f"Hello {name}, your app is working perfectly!"

with gr.Blocks() as demo:
    gr.Markdown("# ✅ Railway Deployment Test")
    name = gr.Textbox(label="Enter your name")
    output = gr.Textbox(label="Response")
    btn = gr.Button("Submit")
    btn.click(fn=greet, inputs=name, outputs=output)

demo.launch(server_name="0.0.0.0", server_port=8080)
