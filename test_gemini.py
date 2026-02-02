import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print(f'API Key set: {bool(api_key)}')

if not api_key or api_key == 'test-key-placeholder':
    print('ERROR: No valid API key found!')
    print('Please create a .env file with: GEMINI_API_KEY=your_actual_key')
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        test_prompt = 'Return only valid JSON: {"test": "value"}'
        response = model.generate_content(test_prompt)
        print('Gemini Response:', response.text[:300])
    except Exception as e:
        print(f'Error calling Gemini: {e}')
