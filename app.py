from flask import Flask
app = Flask(__name__)
@app.route("/")
def home():
  return "hello, ton application fonctionne sur render !"
if __name__=="__main__":
  app.run()
