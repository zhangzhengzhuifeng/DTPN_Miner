def updateLog(log_xes, to_interval=True, isActivity=True, isPreTrace=True):
    log = []
    if to_interval == True:
        log_xes = interval_lifecycle.to_interval(log_xes)
    # print(log_xes)
    eventId = 0
    if isActivity == True:
        dataframe = pm4py.convert_to_dataframe(log_xes)
        act = set(dataframe['concept:name'])
    for trace in log_xes:
        preattrDict = {}
        if isActivity == True:
            for i in act:
                preattrDict[i + "活动"] = 0
        case = []
        preTrace = ""
        preEvent = ""
        preEvent_times = None
        for event in trace:
            preTrace = preTrace + preEvent
            eventId += 1
            attrDict = copy.deepcopy(preattrDict)

            if isActivity == True:
                if preEvent_times != None:
                    attrDict[preEvent_times + "活动"] += 1
            name = ""
            timestamp = None
            for k, v in event.items():
                if k == 'concept:name':
                    name = v
                    preEvent = getWords(name)
                    preEvent_times = name
                elif k == 'case:concept:name':
                    pass
                elif k == 'time:timestamp':
                    timestamp = datetime.datetime.strftime(v, '%Y-%m-%d %H:%M:%S')
                elif k == 'start_timestamp':
                    pass
                elif k == 'lifecycle:transition':
                    # name = name + "_" + v
                    pass
                elif k.lower().startswith("@@startevent"):
                    pass
                else:
                    # if isinstance(v, float) or IsFloatNum(v) is True:
                    #     v = float(v)
                    attrDict[k] = v
            # print(preTrace)

            if isPreTrace == True:
                attrDict["preTrace"] = preTrace

            preattrDict = attrDict
            event = (eventId, name, timestamp, attrDict)
            case.append(event)
        start = getEvent(case[0], "art_start")
        end = getEvent(case[-1], "art_end")
        case.insert(0, start)
        case.append(end)
        log.append(case)
    return log

def getRealplaces(hid, places, real_t, silent, placein=1):
    if placein == 1:
        if hid in silent:#初始隐变迁
            real_t.add('art_start')
            return
        for place in places:
            for outp in place[1]:
                if outp == hid:
                    if IsplaceExistHid(place[0]):
                        for t in place[0]:
                            if t == hid:
                                continue
                            elif startwithName(t):
                                getRealplaces(t, places, real_t, silent, placein)
                            else:
                                real_t.add(t)

                    else:
                        for t in place[0]:
                            real_t.add(t)
                    break
    else:
        if hid in silent:
            real_t.add('art_end')
            return
        for place in places:
            for inp in place[0]:
                if inp == hid:
                    if IsplaceExistHid(place[1]):
                        for t in place[1]:
                            if t == hid:
                                continue
                            elif startwithName(t):
                                getRealplaces(t, places, real_t, silent, placein)
                            else:
                                real_t.add(t)
                    else:
                        for t in place[1]:
                            real_t.add(t)
                    break

def DTPN_Miner(log, dplace, silent, replayed_traces, ti, yl, fitness=0.0):
    place_in = getInSilent(dplace)
    place_out = getOutSilent(dplace)
    datasets = create_deList(dplace)
    flag = 0
    start = []
    if len(ti) > 1:
        ti = getTiReal(dplace, yl, silent)
        flag = 1
    for i in range(len(replayed_traces)):
        if replayed_traces[i]['trace_fitness'] < fitness:
            continue
        front_list = []  # front_model   front_activity  front_data
        lm = 0
        case = log[i]
        activated_t = replayed_traces[i]['activated_transitions']
        if flag == 1:
            if case[1][1] in ti:
                testdata = copy.deepcopy(case[1][3])
                testdata["label"] = activated_t[0].name
                start.append(testdata)
        current_activity = case[0][1]
        current_data = case[0][3]
        next_activity = case[1][1]
        for j in range(len(activated_t) - 1):
            log_move = activated_t[j].label
            log_next = activated_t[j + 1].label
            model_move = activated_t[j].name
            next_model = activated_t[j + 1].name
            if log_move is not None:
                lm += 1
                current_activity = case[lm][1]
                current_data = case[lm][3]
                next_activity = case[lm + 1][1]
                model_move = log_move
            if log_next is not None:
                next_model = log_next
            if model_move in place_in:
                front_model = model_move
                front_activity = current_activity
                # front_data = current_data
                # front_list.append([front_model, front_activity, front_data])
                front_list.append([front_model, front_activity])
            if len(front_list) > 0 and next_model in place_out:
                for f in front_list[:: -1]:
                    front_model, front_activity = f

                    flag, dp = IsDecisionActivity(front_activity, next_activity, front_model, next_model, dplace,
                                                  silent,
                                                  yl)
                    if flag:
                        testdata = copy.deepcopy(current_data)
                        testdata["label"] = next_model
                        for k, v in dp.items():
                            datasets[k][v].append(testdata)
                        break

    return datasets, start

