import os
import traceback
import app

print('api key present', bool(os.getenv('OPENAI_API_KEY')))
try:
    app.build_ai_response('Say hello')
except Exception:
    traceback.print_exc()
