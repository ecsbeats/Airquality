from airquality import app
from colorama import init
init()
if __name__ == '__main__':
    app.run(port = 8000, debug=True)
    print(app.host)
