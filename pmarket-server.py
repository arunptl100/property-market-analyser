from flask import Flask, render_template, request, g
import pmarket
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
scheduler = BackgroundScheduler()

@app.route("/")
def index():
    return render_template("index.html")


def run(area, beds, baths, budget, type, dist_train, interval):
    # setup the background scheduler to auto scan every interval
    # print("num jobs = ", len(scheduler.get_jobs()))
    # the below check is for if the scheduler is already running and a search
    # is made
    # In this case we should remove the current job and append the new one
    if scheduler.running:
        if scheduler.get_jobs():
            job = scheduler.get_jobs()[0]
            print(job.next_run_time)
            scheduler.remove_job("prop_job")
    else:
        # on the very first scan just start the scheduler
        scheduler.start()
    scheduler.add_job(pmarket.do_work, 'interval', args=(area, beds, baths, budget, type, dist_train, interval), hours=int(interval), id="prop_job")
    print("starting background scheduler with interval ", interval, " hour(s)")
    pmarket.do_work(area, beds, baths, budget, type, dist_train, interval)
    print("returning for => ", area)
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
        # get the next scheduler running time *INOP*
        if scheduler.running:
            if scheduler.get_jobs():
                job = scheduler.get_jobs()[0]
                print(job.next_run_time)
        return render_template("results.html", result=properties)


if __name__ == '__main__':
    app.run(debug=True)
