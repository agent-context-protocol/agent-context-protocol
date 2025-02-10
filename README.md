# Interpreter-Translator
---

## Steps to Run

1. **Set Up a Conda Environment (Optional)**  
   ```bash
   conda create -n translator_env python=3.9
   conda activate translator_env

    You can install your dependencies this yml file: https://drive.google.com/file/d/1LjAuhmhmudMFDmMmM8EwnybqYmt2I-2o/view?usp=sharing.
   
2.	Set Up Your API Keys
   Export these environment variables:
    ```bash
    export OPENAI_API_KEY=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
    export OPEN_AI_BASE=https://api.openai.com/v1/chat/completions
    export BING_API_KEY=af34c800d72846c5a1c89c19f5fffe4b
    export SERPAPI_API_KEY=34f3923cee2b5285cf77ba6054489d1a345e1b2a6c2097ae912c1d0b76841b7c
    export HUGGINGFACEHUB_API_TOKEN=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


3.	Run the App:
   Open the link provided by Streamlit in your browser or it will automatically open, enter your query, and click Run Workflow.
   ```bash
   streamlit run app.py




