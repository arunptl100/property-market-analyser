from flask import Flask, render_template, request
import pmarket
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
scheduler = BackgroundScheduler()

@app.route("/")
def index():
    return render_template("index.html")


def run(area, beds, baths, budget, type, dist_train, interval):
    pmarket.do_work(area, beds, baths, budget, type, dist_train, interval)
    # setup the background scheduler to auto scan every interval
    global scheduler
    # problem, we get new instances of this file and lose the reference to the last
    # scheduler making it impossible to shutdownt the last scheduler
    scheduler.add_job(pmarket.do_work, 'interval', args=(area, beds, baths, budget, type, dist_train, interval), seconds=30, id="prop_job")
    scheduler.start()
    print("starting background scheduler")
    return pmarket.see_results()


@app.route('/scan', methods=['POST'])
def result():
    params = request.form
    if params.get('action') == "See results":
        properties = pmarket.see_results()
        return render_template("results.html", result=properties)
    else:
        # setup a scheduler
        run(params.get('location'), params.get('beds'), params.get('baths'), params.get('budget'), params.get('type'), params.get('dist_train'), params.get('interval'))
        properties = pmarket.see_results()
        return render_template("results.html", result=properties)


if __name__ == '__main__':
    app.run(debug=True)
