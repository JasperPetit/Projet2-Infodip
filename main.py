from app import app
from waitress import serve

if __name__ == '__main__':
#    app.run(host="localhost", port=8000, debug=True)
    serve(app, host='0.0.0.0', port=5000, threads=4)

