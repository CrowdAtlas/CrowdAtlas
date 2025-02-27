import numpy as np
import pandas as pd
import os
import sys
import datetime
from sklearn import linear_model
sys.path.append('./')
import data_inference

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
np.set_printoptions(threshold=np.inf)

def get_stn_index(station):
    if station == 'EW24' or station == 'NS1':
        station = 'NS1&EW24'
    if station == 'EW13' or station == 'NS25':
        station = 'NS25&EW13'
    if station == 'EW14' or station == 'NS26':
        station = 'NS26&EW14'

    if station == 'NS1&EW24':
        return 0
    if station == 'NS25&EW13':
        return 1
    if station == 'NS26&EW14':
        return 2

    ret = -1
    line = station[:2]
    num = int(station[2:])
    if line == 'EW':
        if num in range(1,13):
            ret = num + 2
        if num in range(15,24):
            ret = num
        if num in range(25,30):
            ret = num - 1
    else:
        if num in range(2,6):
            ret = num + 27
        if num in range(7,12):
            ret = num + 26
        if num in range(13,25):
            ret = num + 25
        if num in range(27,29):
            ret = num + 23

    return ret

stations = range(0,52)
station_list = ['NS1&EW24', 'NS25&EW13', 'NS26&EW14'] + ['EW'+str(q) for q in range(1,13)] \
               + ['EW'+str(q) for q in range(15,24)] + ['EW'+str(q) for q in range(25,30)] \
               + ['NS'+str(q) for q in range(2,6)] + ['NS'+str(q) for q in range(7,12)] \
                + ['NS'+str(q) for q in range(13,25)] + ['NS'+str(q) for q in range(27,29)]

station_groups = [['EW1', 'EW8', 'EW15', 'EW22'], ['EW2', 'EW9', 'EW16', 'EW23'], ['EW3', 'EW10', 'EW17', 'NS1&EW24'],
    ['EW4', 'EW11', 'EW18', 'EW25'], ['EW5', 'EW12', 'EW19', 'EW26'], ['EW6', 'NS25&EW13', 'EW20', 'EW27'],
    ['EW7', 'NS26&EW14', 'EW21', 'EW28'], ['NS2', 'NS9', 'NS16', 'NS22'], ['NS3', 'NS10', 'NS17', 'NS23'], ['NS4', 'NS11', 'NS18', 'NS24'],
    ['NS5', 'NS13', 'NS19', 'NS27'], ['NS7', 'NS14', 'NS20', 'NS28'], ['NS8', 'NS15', 'NS21', 'EW29']]


def LR_approach(date, station, hour):
    dates_ori = pd.bdate_range(end=date, periods=60)
    dates = [datetime.datetime.strftime(dates_ori[i], '%Y-%m-%d') for i in range(len(dates_ori) - 1)]

    c_value = 10
    n_classes = 52
    column_name_list1 = []
    column_name_list1.append('start_time')
    column_name_list1.append('delta_time')
    column_name_list1.append('crowd_num')
    for q in range(0, 52):
        column_name_list1.append('p_' + station_list[q])

    contain = [False for q in range(52)]
    x_train, y_temp = data_inference.data_inference(dates[0], station, hour)
    y_train = []
    for i in range(len(y_temp)):
        for j in range(n_classes):
            if y_temp[i][j] == 1:
                y_train.append(j)
                if contain[j] is False:
                    contain[j] = True
                break

    for k in range(1, len(dates)): # ref_dates:
        xs, y_temp = data_inference.data_inference(dates[k], station, hour)
        # ys = [0 for i in range(len(y_temp))]
        for i in range(len(y_temp)):
            for j in range(n_classes):
                if y_temp[i][j] == 1:
                    y_train.append(j)
                    if contain[j] is False:
                        contain[j] = True
                    break
        x_train = np.vstack((x_train, xs))
        # y_train = np.vstack((y_train, ys))

    sup_num = 0
    for q in range(len(contain)):
        if contain[q] is False:
            y_train.append(q)
            sup_num += 1

    if sup_num > 0:
        xs = np.zeros((sup_num, 192))
        x_train = np.vstack((x_train, xs))
    y_train = np.array(y_train)

    clf = linear_model.LogisticRegression(multi_class="multinomial", penalty='l1', solver="saga", C=c_value, max_iter=200)
    clf.fit(x_train, y_train)
    print('Training finished~' + station)
    # print(clf.coef_)

    column_name_list = []
    column_name_list.append('origin_station')
    column_name_list.append('start_time')
    column_name_list.append('end_time')
    column_name_list.append('people_num')
    column_name_list.append('rel_entropy')
    column_name_list.append('error')
    for q in range(0, 52):
        column_name_list.append('p_' + station_list[q])
    for q in range(0, 52):
        column_name_list.append('r_' + station_list[q])
    df_record = pd.DataFrame(columns=column_name_list)
    record_num = 0

    xs_test, ys_test = data_inference.data_inference(date, station, hour, True)
    # pred_res_list = clf.predict(xs_test)
    pred_res_list = clf.predict_proba(xs_test)

    # print("Test: " + str(len(pred_res_list)))


    for i in range(len(xs_test)):
        record = []
        sta_time = 0
        for j in range(140, 192):
            if xs_test[i][j] == 1:
                record.append(station_list[j - 140])
                break

        for j in range(0, 60):
            if xs_test[i][j] == 1:
                record.append(j + hour * 60)
                sta_time = j + hour * 60
                break

        for j in range(60, 140):
            if xs_test[i][j] == 1:
                record.append(j - 60 + 1 + sta_time)
                break

        record.append(1.)
        record.append(0.)
        record.append(0.)
        for p in range(n_classes):
            record.append(pred_res_list[i][p])
        for p in range(n_classes):
            record.append(float(ys_test[i][p]))

        if len(record) != len(column_name_list):
            print(record)
        df_record.loc[record_num] = record
        record_num += 1

    df_group = df_record.groupby(by=['origin_station', 'start_time', 'end_time']).sum().reset_index()
    for i in range(0, df_group.shape[0]):
        start_time = int(df_group.iloc[i, 1]) - hour * 60
        delta_time = int(df_group.iloc[i, 2]) - int(df_group.iloc[i, 1]) - 1
        pred_dist = [0.] * 52
        ys_dist = [0.] * 52
        for j in range(52):
            # df_group.iloc[i, j + 6] = df_group.iloc[i, 3] * lookup_table[start_time][delta_time][j]

            ratio = float(df_group.iloc[i, j + 6] / df_group.iloc[i, 3])
            if ratio <= 0:
                pred_dist[j] = 1e-10
            else:
                pred_dist[j] = ratio

            ratio2 = float(df_group.iloc[i, j + 58] / df_group.iloc[i, 3])
            if ratio2 <= 0:
                ys_dist[j] = 1e-10
            else:
                ys_dist[j] = ratio2

        df_group.iloc[i, 4] = np.sum(ys_dist * (np.log(ys_dist) - np.log(pred_dist)))
        df_group.iloc[i, 5] = np.mean((np.array(ys_dist) - np.array(pred_dist)) ** 2) ** 0.5

    df_record_opt = df_group.sort_values(by=['start_time', 'end_time'])
    dir = 'sta_results/' + date + '/' + str(hour)
    if not os.path.exists('sta_results'):
        os.mkdir('sta_results')
    if not os.path.exists('sta_results/' + date):
        os.mkdir('sta_results/' + date)
    if not os.path.exists(dir):
        os.mkdir(dir)
    df_record_opt.to_csv(dir + '/' + station + '_num_dist_lr.csv', index=None)

    print('Testing finished~' + station)
    print('Relative entropy:', np.mean(df_record_opt['rel_entropy']))
    print('RMSE:', np.mean(df_record_opt['error']))


if __name__ == '__main__':
    argv = sys.argv
    start_hour = int(argv[1])
    duration = int(argv[2])

    date_str = argv[3]  # Format: '1/1/2016' or '20160101'
    dates_ori = pd.bdate_range(date_str, date_str)
    date = dates_ori[0]

    for q in range(52):
        for h in range(start_hour, start_hour + duration):
            LR_approach(date, station_list[q], h)

    dir = 'arv_results'
    if not os.path.exists(dir):
        os.mkdir(dir)

    column_list = ['Station'] + [str(p) for p in range(start_hour*2, (start_hour + duration)*2)]
    df_mape = pd.DataFrame(columns=column_list)

    for k in range(52):
        yp_list = [0.0 for i in range(duration*12)]
        yt_list = [0.0 for i in range(duration*12)]

        for q in range(0,52):
            df = pd.read_csv('sta_results/' + date + '/' + str(start_hour) + '/' + station_list[q] + '_num_dist_lr.csv')
            for h in range(start_hour + 1, start_hour + duration):
                # Lasso_approach(date,station_list[q],h,alpha)
                df_temp = pd.read_csv('sta_results/' + date + '/' + str(h) + '/' + station_list[q] + '_num_dist_lr.csv')
                df = df.append(df_temp, ignore_index=True)
            df_opt = df[(df['end_time'] >= start_hour * 60) & (df['end_time'] <= (start_hour + duration) * 60)]
            df_group = df_opt.groupby(by=['end_time']).sum().reset_index()
            # print(df_group.shape[0])

            for i in range(0,df_group.shape[0]):
                index = int((df_group.iloc[i, 0] - 1 - start_hour * 60)/5)
                yp_list[index] += df_group.iloc[i, 5 + k - 1]
                yt_list[index] += df_group.iloc[i, 57 + k - 1]

        for x in range(duration * 12):
            yp_list[x] /= 5
            yt_list[x] /= 5

        df_record = pd.DataFrame(columns=['Time', 'Ground_Truth', 'Estimation', 'Deviation', 'Accuracy'])
        record_num = 0
        mape_list = [0.0 for u in range(duration * 2)]

        for j in range(len(yp_list)):
            accuracy = 1 - float(abs(yp_list[j] - yt_list[j]) / yt_list[j])
            deviation = yp_list[j] - yt_list[j]
            record = [start_hour * 60 + (j + 1) * 5, yt_list[j], yp_list[j], deviation, accuracy]
            df_record.loc[record_num] = record

            record_num += 1
            mape_list[int(j/12)] += abs(yp_list[j] - yt_list[j]) / yt_list[j]

        for u in range(duration ):
            mape_list[u] *= 100/12
        rec = [station_list[k]] + [str(u) for u in mape_list]
        df_mape.loc[k] = rec

        if not os.path.exists(dir + '/' + date):
            os.mkdir(dir + '/' + date)
        df_record.to_csv(dir + '/' + date + '/' + station_list[k] + '_num_comp_lr.csv', index=None)

    df_mape.to_csv(dir + '/' + date + '/MAPE_across_time_station_lr.csv', index=None)

    column_list = ['Time (min)']
    for k in range(len(stations)):
        column_list += [station_list[k] + '_gt', station_list[k] + '_est']
    df_merge = pd.DataFrame(columns=column_list)

    for i in range(duration * 12):
        record = [start_hour * 60 + (i + 1) * 5]
        for k in range(0, len(stations)):
            df = pd.read_csv(dir + '/' + date + '/' + station_list[k] + '_num_comp_lr.csv')
            record += [int(df.iloc[i, 1]), int(df.iloc[i, 2])]

        df_merge.loc[i] = record

    df_merge.to_csv(dir + '/' + date + '/merged_arv_comp_lr.csv', index=None)