# Interpreter-Translator
---

## Steps to Run

1. **Set Up a Conda Environment (Optional)**  
   ```bash
   conda create -n translator_env python=3.9
   conda activate translator_env

    You can install your dependencies this yml file: https://drive.google.com/file/d/1LjAuhmhmudMFDmMmM8EwnybqYmt2I-2o/view?usp=sharing.
   
2.	Set Up Your API Keys
    Export these environment variables (replace with your own keys):
    
    export OPENAI_API_KEY="sk-XXXXXXXXXXXXXXXXXXXXXXXX"
    export OPEN_AI_BASE="https://api.openai.com/v1/chat/completions"
    export BING_API_KEY="af34c800d72846c5a1c89c19f5fffe4b"
    export SERPAPI_API_KEY="34f3923cee2b5285cf77ba6054489d1a345e1b2a6c2097ae912c1d0b76841b7c"
    export HUGGINGFACEHUB_API_TOKEN="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"


3.	Run the App
   
    streamlit run app.py

    Open the link provided by Streamlit in your browser or it will automatically open, enter your query, and click Run Workflow.




