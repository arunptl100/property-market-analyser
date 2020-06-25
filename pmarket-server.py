from flask import Flask, render_template, request
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/hello/<name>')
def hello_name(name):
    return 'Hello %s!' % name


@app.route('/scan', methods=['POST'])
def result():
    result = request.form
    return render_template("results.html", result=result)


if __name__ == '__main__':
    app.run(debug=True)
