import asyncio
import calendar
import csv
import os
from collections import defaultdict
from datetime import datetime, time

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import requests
from django.shortcuts import render

from .forms import IdDateForm


def prepare_data(user_id, ts):
    """Func to prepare required params - list for statistics
    containment and a path to directory with static files"""
    path_to_static_dir = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'static')
    path_to_csv = os.path.join(
        path_to_static_dir, f"id_{user_id}_start_{ts}.csv")
    with open(path_to_csv, mode="w", encoding='utf-8') as w_file:
        file_writer = csv.writer(w_file, delimiter=",")
        file_writer.writerow([
            'post id', 'text', 'attachments', 'attachments amount',
            'comments amount', 'likes amount', 'reposts amount'])
    stats = [defaultdict(lambda: {
        'amount': 0, 'likes': 0, 'comments': 0, 'reposts': 0
    }) for _ in range(4)]
    return stats, path_to_static_dir


def posts_amount(user_id, vk_app_token):
    """Func that returns user's or group's amount of posts"""
    wall_get_url = 'https://api.vk.com/method/wall.get'
    params = {'owner_id': user_id,
              'offset': 0,
              'count': 1,
              'access_token': vk_app_token,
              'v': 5.131}
    return requests.get(
        wall_get_url, params=params
    ).json()['response']['count']


def first_post_ts(user_id, vk_app_token):
    """Func that returns timestamp for user's or group's first post"""
    offset = posts_amount(user_id, vk_app_token)
    wall_get_url = 'https://api.vk.com/method/wall.get'
    params = {'owner_id': user_id,
              'offset': offset-1,
              'count': 1,
              'access_token': vk_app_token,
              'v': 5.131}
    ts = requests.get(
        wall_get_url,
        params=params
    ).json()['response']['items'][0]['date']
    return ts


async def get_all_posts(user_id, all_posts, vk_app_token, ts_for_vk):
    """Async eventloop that gathers required amount of coroutines,
    creates task triplet for every three of them, runs every triplet
    and adds the resuls to 'all_posts' list"""
    posts_count = posts_amount(user_id, vk_app_token)
    groups_count = (posts_count//1500+1 if posts_count % 1500 != 0
                    else posts_count//1500)
    offsets = [1500*i for i in range(groups_count)]
    for i in range(0, len(offsets), 3):
        tasks = [asyncio.create_task(
            vk_posts_to_json(user_id, offset, vk_app_token, ts_for_vk)
        )for offset in offsets[i:i + 3]]
        loop = asyncio.gather(*tasks)
        await loop
        for task in tasks:
            for post_group in task.result()['response']:
                all_posts.extend(post_group)


async def vk_posts_to_json(user_id, offset, vk_app_token, ts_for_vk):
    """Async coroutine that makes request to execute method of VK api.
    Code parameter of this method is simplified JS func that calls wall.
    get method of VK api up to 15 times and returns list with 1500(or less)
    post-data objects. Coroutine returns json object with this list under
    'response' header"""
    async with aiohttp.ClientSession() as session:
        execute_url = 'https://api.vk.com/method/execute'
        code = f'''var offset = {offset};
                   var counter = 0;
                   var all_posts = [];
                   var posts = API.wall.get({{'owner_id': {user_id},
                   'offset': offset, 'count': 100}});
                   all_posts.push(posts.items);
                   offset = offset + 100;
                   while ((posts.items[99].date > {ts_for_vk}) &&
                    (counter < 14)) {{
                       posts = API.wall.get({{'owner_id': {user_id},
                        'offset': offset, 'count': 100}});
                       all_posts.push(posts.items);
                       offset = offset + 100;
                       counter = counter + 1;
                   }};
                   return all_posts;'''
        params = {'access_token': vk_app_token, 'code': code, 'v': 5.131}
        async with session.get(execute_url, params=params) as response:
            return await response.json()


def post_to_csv(post, path_to_csv):
    """Func that from post-data dict creates list with:
         -post id;
         -post text;
         -attachments ids(or urls);
         -amount of attachments;
         -amount of comments;
         -amount of likes;
         -amount of reposts
    and adds this list to CSV-file with all posts statistics"""
    post_id = str(post['id'])
    text = post['text']
    if 'attachments' in post.keys():
        att_amount = str(len(post['attachments']))
        att_ids = ' '.join(
            [str(att[att['type']]['id']) if 'id' in att[att['type']].keys()
             else att[att['type']]['url'] for att in post['attachments']])
    else:
        att_ids = 'None'
        att_amount = '0'
    comments_amount = str(post['comments']['count'])
    likes_amount = str(post['likes']['count'])
    reposts_amount = str(post['reposts']['count'])
    with open(path_to_csv, mode="a", encoding='utf-8') as w_file:
        file_writer = csv.writer(w_file, delimiter=",")
        file_writer.writerow([
            post_id, text, att_ids, att_amount, comments_amount,
            likes_amount, reposts_amount])


def add_post_to_stats(post, stats):
    """Func that from post-data dict takes:
         -amount of posts;
         -amount of likes;
         -amount of comments;
         -amount of reposts
    and adds those to corresponding column in every of four
    statistic defaultdicts(for hours, days of the week, months
    and years) in stats list"""
    post_hour = datetime.utcfromtimestamp(post['date']).hour
    post_week_day = datetime.utcfromtimestamp(post['date']).weekday()
    post_month = datetime.utcfromtimestamp(post['date']).month
    post_year = datetime.utcfromtimestamp(post['date']).year
    post_data = [post_hour, post_week_day, post_month, post_year]
    for p_d, s in zip(post_data, stats):
        s[p_d]['amount'] += 1
        s[p_d]['likes'] += post['likes']['count']
        s[p_d]['comments'] += post['comments']['count']
        s[p_d]['reposts'] += post['reposts']['count']


def stat_to_graph(stat, name, user_id, ts, path_to_dir):
    """Func that creates and saves(under generated name)
     4-bar-graph for given statistic"""
    index = np.arange(len(stat))
    amounts = [stat[element]['amount'] for element in stat]
    av_likes = [
        round(stat[element]['likes']/stat[element]['amount'], 2)
        for element in stat]
    av_comments = [
        round(stat[element]['comments']/stat[element]['amount'], 2)
        for element in stat]
    av_reposts = [
        round(stat[element]['reposts']/stat[element]['amount'], 2)
        for element in stat]
    bw = 0.2
    plt.figure(figsize=(len(stat)*2.5, 5))
    plt.title(f'VK post statistics for {name}', fontsize=20)
    plt.minorticks_on()
    plt.grid(which='major', alpha=0.5, axis="y")
    plt.grid(which='minor', alpha=0.3, linestyle=':', axis="y")
    plt.bar(index, amounts, bw, color='b',
            label='Amount of posts')
    plt.bar(
        index+bw, av_likes, bw, color='g',
        label='Average likes amount')
    plt.bar(
        index+2*bw, av_comments, bw, color='r',
        label='Average comments amount')
    plt.bar(
        index+3*bw, av_reposts, bw, color='y',
        label='Average reposts amount')
    plt.xticks(index+1.5*bw, [key for key in stat])
    plt.legend(loc=0)
    plt.autoscale()
    bars = [amounts, av_likes, av_comments, av_reposts]
    offsets = [offset*bw for offset in range(4)]
    for o, bar in zip(offsets, bars):
        for x, y in zip(index, bar):
            plt.text(x+o, y + 0.05, f'{y}', ha='center', va='bottom')
    plt.savefig(
        os.path.join(path_to_dir, f"{name}_stat_id_{user_id}_start_{ts}.png"))
    plt.close()


def main_for_async_execute(user_id, ts, vk_app_token):
    """Main func that contains four parts:
        -preparation(calls 'prepare_data' func and creates a 'ts_for_vk' var;
        -VK api part(runs async eventlop - 'get_all_posts' func);
        -counting(for every suitable post calls 'post_to_csv'
                  and 'add_post_to_stats' funcs);
        -graphs creation(sorts data in every stat, renames some params and
                         runs 'stat_to_graph' func for every stat)"""
    # Preparations part
    stats, path_to_static_dir = prepare_data(user_id, ts)
    ts_for_vk = max(ts, first_post_ts(user_id, vk_app_token))
    all_posts = []

    # VK api part
    if os.name == 'nt':
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_all_posts(user_id, all_posts, vk_app_token, ts_for_vk))

    # Counting part
    for post in filter(
            lambda post_json: post_json['date'] > ts_for_vk, all_posts):
        post_to_csv(
            post, os.path.join(
                path_to_static_dir,  f"id_{user_id}_start_{ts}.csv"))
        add_post_to_stats(post, stats)

    # Graphs part
    sorted_renamed_stats = [
        {f"{key}:00-{key + 1}:00": stats[0][key] for key in sorted(stats[0])},
        {calendar.day_name[key]: stats[1][key] for key in sorted(stats[1])},
        {calendar.month_name[key]: stats[2][key] for key in sorted(stats[2])},
        {str(key): stats[3][key] for key in sorted(stats[3])}]
    names = ['hours', 'days', 'months', 'years']
    for stat, name in zip(sorted_renamed_stats, names):
        stat_to_graph(stat, name, user_id, ts, path_to_static_dir)


def start(request):
    """View func that renders start.html or if form on start
    page was filled with valid params - result.html"""
    vk_app_token = 'TOKEN'
    if request.GET:
        form = IdDateForm(request.GET)
        if form.is_valid():
            data_id = form.cleaned_data['user_page_id']
            ts = datetime.combine(form.cleaned_data['start_date'],
                                  time()).timestamp()
            main_for_async_execute(data_id, ts, vk_app_token)
            filename = f"id_{data_id}_start_{ts}"
            return render(request, 'result.html',
                          context={'stat_csv':  filename+'.csv',
                                   'h_png': 'hours_stat_'+filename+'.png',
                                   'd_png': 'days_stat_'+filename+'.png',
                                   'm_png': 'months_stat_'+filename+'.png',
                                   'y_png': 'years_stat_'+filename+'.png'}, )
    else:
        form = IdDateForm()
    return render(request, 'start.html', {'form': form})
