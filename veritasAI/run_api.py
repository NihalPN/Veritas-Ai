# run_api.py

import threading
import time
import nest_asyncio
import uvicorn
from pyngrok import ngrok

nest_asyncio.apply()


def start_server():
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
    )


# Start FastAPI in background thread
thread = threading.Thread(target=start_server)
thread.start()

# Wait for server to fully start
time.sleep(15)  # give models time to load

# Now connect ngrok AFTER server is alive
public_url = ngrok.connect(8000)
print("🚀 Public URL:", public_url)