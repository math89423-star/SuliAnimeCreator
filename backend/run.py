import os
from app import create_app
app = create_app()
if __name__ == "__main__":
    # cmd.bash 托管时默认关 reloader（单进程，pidfile 才杀得干净）；要热重载设 FLASK_RELOAD=1
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")),
            debug=os.getenv("FLASK_DEBUG", "0") == "1",
            use_reloader=os.getenv("FLASK_RELOAD", "0") == "1")
