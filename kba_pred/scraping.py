import requests
import re
import pandas as pd
from bs4 import BeautifulSoup


def get_dataset():
    columns = ['place', 'horse', 'waku', 'umaban', 'sex', 'age', 'weight', 'jockey', 'horse_weight', 'horse_weight_diff',
             'trainer', 'pop', 'distance', 'course', 'direction','start_h', 'start_m', 'weather', 'year', 'month', 'day', 'time']
    df_l = [[] for i in range(len(columns))]
    for y in ['2020', '2021']:
        r = requests.get('https://jra.jp/datafile/seiseki/replay/'+ y +'/jyusyo.html')
        soup = BeautifulSoup(r.content, 'html.parser')
        urls_pre = soup.find_all('td', class_='result')
        urls = []
        for url in urls_pre:
            m = re.search(r'.+href="(.+)"><i.+', str(url))
            if m is None: break
            urls.append(m.group(1))
        for epoch in range(len(urls)):
            df_r = get_dataset_r(urls[epoch])
            for i in range(len(df_l)):
                df_l[i] = df_l[i] + df_r[i]
            print('race(' + y + ') '+ urls[epoch])

    df = pd.DataFrame(df_l).T
    df.columns = columns 
    return df   

def name_modifier(name):
    name = name.strip()
    name = name.strip('\t')
    name = name.strip('\n')
    return name

def get_dataset_r(url):
    cancel = 0

    #race_num = str(epoch + 1).zfill(3)
    r = requests.get('https://jra.jp/' + url)
    soup = BeautifulSoup(r.content, 'html.parser')

    # place
    places_pre = soup.find_all('td', class_='place')
    places = []
    for p in places_pre:
        m = re.search(r'.+e">(\d+)</t.+', str(p))
        if m is None:
            print(p)
            cancel += 1
        else:
            places.append(int(m.group(1)))
    if cancel > 0:  print('cancel : '+ str(cancel))
    epochs = len(places)

    # horse name
    horses = soup.find_all('td', class_='horse')
    horses_text = [horses[i].text for i in range(epochs)]
    horses_text = list(map(name_modifier, horses_text))

    # waku
    waku = soup.find_all('td', class_='waku')
    waku_num = []
    for i in range(epochs):
        m = re.search(r'.+".(\d).".+', str(waku[i]))
        waku_num.append(m.group(1))

    # age & sex
    ages_pre = soup.find_all('td', class_='age')
    sexes, ages = [], []
    for i in range(epochs):
        m = re.search(r'.+(牡|牝|せん)(\d).+', str(ages_pre[i]))
        # male or female (male : 0, female : 1, error : -1)
        sexes.append(m.group(1))
        '''
        if m.group(1) == '牡': sexes.append('')
        elif m.group(1) == '牝': sexes.append(1)
        elif m.group(1) == 'せん': sexes.append(2)
        else: sexes.append(-1)   
        '''
        ages.append(int(m.group(2)))

    # weights
    weights_pre = soup.find_all('td', class_='weight')
    weights = []
    for i in range(epochs):
        m = re.search(r'.+t">(.+)</t.*', str(weights_pre[i]))
        weights.append(float(m.group(1)))

    # jockey
    jockeys_pre = soup.find_all('td', class_="jockey")
    jockeys = []
    for i in range(epochs):
        m = re.search(r'.+y">(.+)</t.*', str(jockeys_pre[i]))
        jockeys.append(m.group(1))

    # time
    times_pre = soup.find_all('td', class_='time')
    times = []
    for i in range(epochs):
        m = re.search(r'.+e">(\d+):(.+)</t.+', str(times_pre[i]))
        if m is None:
            time = times[-1] * 1.5
            continue
        time = float(m.group(1)) * 60 + float(m.group(2))
        times.append(time)

    # horse's weight
    h_weights_pre = soup.find_all('td', class_='h_weight')
    h_weights, h_weight_diffs = [], []
    for i in range(epochs):
        m = re.search(r'.+(\d{3})<span>\((.+)\).+', str(h_weights_pre[i]))
        if m is None: 
            #print(hw)
            #cancel += 1
            print('error(hw)')
            continue
        h_weights.append(int(m.group(1)))
        if m.group(2) == '前計不':  h_weight_diffs.append(0)
        else:   h_weight_diffs.append(int(m.group(2)))

    # trainer
    trainers_pre = soup.find_all('td', class_= 'trainer')
    trainers = []
    for i in range(epochs):
        m = re.search(r'.+r">(.+)</t.+', str(trainers_pre[i]))
        trainers.append(m.group(1))

    # pop
    pops_pre = soup.find_all('td', class_='pop')
    pops = []
    for i in range(epochs):
        m = re.search(r'.+p">(\d+)</t.+', str(pops_pre[i]))
        if m is None and cancel != 0:   
            print('error(pop)')
            continue
        pops.append(int(m.group(1)))

    # num
    nums_pre = soup.find_all('td', class_='num')
    nums = []
    for i in range(epochs):
        m = re.search(r'.+m">(\d+)</t.+', str(nums_pre[i]))
        nums.append(int(m.group(1)))

    # course 
    dist = soup.find_all('div', class_='cell course')
    #m = re.search(r'.+コース.</span>(.+)<span class="u.+l">（(.+)・(.).+', str(dist[0]))
    m = re.search(r'.+コース.</span>(.+)<span class="u.+l">（(.+)）.+', str(dist[0]))
    distance = int(m.group(1)[:1] + m.group(1)[2:])
    s = m.group(2)
    if s.find('・') != -1:
        l = s.split('・')
        course, direction = l[0], l[1]
    else:
        course, direction = s, '無'
    '''
    course = m.group(2)
    direction = m.group(3)
    '''

    # start time
    start_time_pre = soup.find_all('div', class_='cell time')
    m = re.search(r'.+ng>(\d+)時(\d+)分.+', str(start_time_pre[0]))
    start_h = int(m.group(1))
    start_m = int(m.group(2))

    # weather
    weather_pre = soup.find_all('div', class_='cell baba')
    m = re.search(r'.+天候</span><span class="txt">(.).+', str(weather_pre[0]))
    weather = m.group(1)

    # date
    date_pre = soup.find_all('div', class_='cell date')
    m = re.search(r'.+(\d{4})年(\d+)月(\d+)日.+', str(date_pre[0]))
    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))

    # dataframe
    distance_df = [distance for i in range(len(horses_text))]
    course_df = [course for i in range(len(horses_text))]
    direction_df = [direction for i in range(len(horses_text))]
    start_h_df = [start_h for i in range(len(horses_text))]
    start_m_df = [start_m for i in range(len(horses_text))]
    weather_df = [weather for i in range(len(horses_text))]
    year_df = [year for i in range(len(horses_text))]
    month_df = [month for i in range(len(horses_text))]
    day_df = [day for i in range(len(horses_text))]    

    df_r = [places, horses_text, waku_num, nums, sexes, ages, weights, jockeys, h_weights, h_weight_diffs,
          trainers, pops, distance_df, course_df, direction_df, start_h_df, start_m_df, weather_df, 
           year_df, month_df, day_df, times]

    return df_r
    
    '''
    if cancel == 0: return df_r
    else:
        f = lambda l: l[:len(l) - cancel]
        return list(map(f, df_r))
    '''