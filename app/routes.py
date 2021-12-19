# -*- coding: utf-8 -*-
from app import app
from flask import render_template, redirect, url_for, request
from app.forms import ShowForm, PostForm
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import re
import time

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('base.html', title='Welcome')


@app.route('/showstat', methods=['GET', 'POST'])
def showstat():
    stat = requests.get('https://slot-ml.com/api/v1/users/1ad36c1fb80a7034c827120650895c8670f083cc/stats')
    var = stat.json()
    return render_template('showstat.html', title='Statistics', var=var)

@app.route('/start', methods=['GET', 'POST'])
def start():
    form = ShowForm()
    regex = r'"vector":\s"(?P<cd>.*)",(\n\t)?"meta3"'
    regex1 = r'"id":\s"(?P<cd>.*)"\,(\n\t)?"meta2"'
    regex2 = r'"meta5":\s"(?P<cd>.*)"\n}'
    regex3 = r'"meta6":\s"(?P<cd>.*)",(\n\t)?"meta4"'
    regex4 = r'"meta3":\s(?P<cd>.*),(\n\t)?"meta6"'

    if request.method == 'POST' and form.validate_on_submit():  
        n = format(form.n.data)
        n = int(n)
        collection = []
        
        for i in range(n):
            collection.append(requests.get('https://slot-ml.com/api/v1/users/1ad36c1fb80a7034c827120650895c8670f083cc/vectors/?random'))
        
        cols = {}
        err_count = 0

        for i in range(len(collection)):
            try: 
                vec = re.search(regex, collection[i].text).group(1) 
                ids = re.search(regex1, collection[i].text).group(1)
                res = vec + ' ' + re.search(regex2, collection[i].text).group(1)+ ' ' + re.search(regex3, collection[i].text).group(1) + ' ' + re.search(regex4, collection[i].text).group(1) 
                cols[ids] = res
            except:
                ids = re.search(regex1, collection[i].text).group(1)
                cols[ids] = 'PARSING ERROR'
                err_count += 1
            

        samples = list(cols.values())
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2))
        vectors = vectorizer.fit_transform(samples)

        eps_opt = 0.4
        n_clusters_opt = 0
        eps_ar = np.arange(0.7, 1, 0.01)

        for j in range(len(eps_ar)):
            db = DBSCAN(eps=eps_ar[j], min_samples=2).fit(vectors)
            core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
            core_samples_mask[db.core_sample_indices_] = True
            labels = db.labels_
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            if n_clusters < 49 and n_clusters > n_clusters_opt:
                n_clusters_opt = n_clusters
                eps_opt = eps_ar[j]        

        db = DBSCAN(eps=eps_opt, min_samples=2).fit(vectors)
        labels = db.labels_

        zer = len(set(labels))
        keys = list(cols.keys())
        for i in range(len(labels)):
            if int(labels[i]) == 0:
                   labels[i] = zer - 1
            requests.post('https://slot-ml.com/api/v1/users/1ad36c1fb80a7034c827120650895c8670f083cc/results/', data={"vector": keys[i], "class": labels[i]})
           #time.sleep(5)


        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        var = "Results have been successfully posted!"
        var1 = "Estimated number of clusters: " + str(n_clusters)
        var2 = 'Estimated number of noise points:' +  str(n_noise)
        return redirect(url_for('success', var=var, var1=var1, var2=var2))
    return render_template('start.html', title='Show', form=form)

@app.route('/success/<var>/<var1>/<var2>)', methods=['GET', 'POST'])
def success(var, var1, var2):
    return  render_template('success.html', title='success', var=var, var1=var1, var2=var2)
