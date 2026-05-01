import math
import heapq
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix

INPUT_FILE = '附件1.xlsx'  # 建议先将 附件1.xls 另存为 .xlsx；也可改成你的绝对路径
OUTPUT_FILE = '排班优化求解结果.xlsx'
TIME_LIMIT = 300


def read_demand(path):
    path = Path(path)
    if path.suffix.lower() in ['.xlsx', '.xlsm']:
        df = pd.read_excel(path, engine='openpyxl', header=1)
    elif path.suffix.lower() == '.xls':
        try:
            df = pd.read_excel(path, engine='calamine', header=1)
        except Exception:
            try:
                df = pd.read_excel(path, engine='xlrd', header=1)
            except Exception as e:
                raise RuntimeError('无法直接读取 .xls。请将附件1.xls用 Excel/WPS 另存为 附件1.xlsx，或安装 python-calamine 后再运行。') from e
    elif path.suffix.lower() == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError('只支持 .xlsx/.xls/.csv')
    df = df.dropna(how='all')
    df.columns = [str(c).strip() for c in df.columns]
    day_col = next(c for c in df.columns if c == '天' or '天' in c)
    hour_col = next(c for c in df.columns if c == '小时' or '时' in c)
    group_cols = [c for c in df.columns if c.startswith('小组')]
    if len(group_cols) != 10:
        raise ValueError(f'未识别到10个小组列，当前识别到: {group_cols}')
    df[day_col] = pd.to_numeric(df[day_col], errors='coerce').astype(int)
    for c in group_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    days = sorted(df[day_col].unique())
    hours = list(df[df[day_col] == days[0]][hour_col])
    D, G, H = len(days), len(group_cols), len(hours)
    demand = np.zeros((D, G, H), dtype=int)
    for di, d in enumerate(days):
        sub = df[df[day_col] == d]
        if len(sub) != H:
            raise ValueError(f'第{d}天小时数不是{H}行')
        for gi, c in enumerate(group_cols):
            demand[di, gi, :] = sub[c].to_numpy(dtype=int)
    return demand, days, hours, group_cols


def build_shift_pairs(min_break=0):
    pairs = []
    cover = []
    labels = []
    for s1 in range(0, 8):
        for s2 in range(s1 + 4 + min_break, 8):
            v = np.zeros(11, dtype=int)
            v[s1:s1+4] = 1
            v[s2:s2+4] = 1
            pairs.append((s1, s2))
            cover.append(v)
            labels.append((s1, s1+4, s2, s2+4))
    return pairs, np.array(cover, dtype=int), labels


def time_label(hours, shift_tuple):
    s1, e1, s2, e2 = shift_tuple
    return f'{hours[s1].split("-")[0]}-{hours[e1-1].split("-")[1]} + {hours[s2].split("-")[0]}-{hours[e2-1].split("-")[1]}'


def solve_problem1_one_group(req_g, shift_cover):
    D, H = req_g.shape
    K = shift_cover.shape[0]
    nvars = D * K + 1
    n_constraints = D * H + D + 1
    A = lil_matrix((n_constraints, nvars), dtype=float)
    lb = np.full(n_constraints, -np.inf)
    ub = np.full(n_constraints, np.inf)
    row = 0
    for d in range(D):
        for h in range(H):
            for k in range(K):
                if shift_cover[k, h]:
                    A[row, d*K+k] = 1
            lb[row] = req_g[d, h]
            row += 1
    N_idx = D * K
    for d in range(D):
        for k in range(K):
            A[row, d*K+k] = 1
        A[row, N_idx] = -1
        ub[row] = 0
        row += 1
    for d in range(D):
        for k in range(K):
            A[row, d*K+k] = 1
    A[row, N_idx] = -8
    lb[row] = 0
    ub[row] = 0
    c = np.zeros(nvars)
    c[N_idx] = 1
    res = milp(c=c, integrality=np.ones(nvars), bounds=Bounds(np.zeros(nvars), np.full(nvars, np.inf)), constraints=LinearConstraint(csr_matrix(A), lb, ub), options={'time_limit': TIME_LIMIT, 'mip_rel_gap': 0})
    if not res.success:
        raise RuntimeError(f'问题1单组求解失败: {res.message}')
    x = np.rint(res.x[:D*K]).astype(int).reshape(D, K)
    N = int(round(res.x[N_idx]))
    return N, x, res


def solve_daily_problem2(req_day, shift_cover):
    G, H = req_day.shape
    K = shift_cover.shape[0]
    nvars = G * K
    A = lil_matrix((G*H, nvars), dtype=float)
    lb = np.zeros(G*H)
    ub = np.full(G*H, np.inf)
    row = 0
    for g in range(G):
        for h in range(H):
            for k in range(K):
                if shift_cover[k, h]:
                    A[row, g*K+k] = 1
            lb[row] = req_day[g, h]
            row += 1
    c = np.ones(nvars)
    res = milp(c=c, integrality=np.ones(nvars), bounds=Bounds(np.zeros(nvars), np.full(nvars, np.inf)), constraints=LinearConstraint(csr_matrix(A), lb, ub), options={'time_limit': TIME_LIMIT, 'mip_rel_gap': 0})
    if not res.success:
        raise RuntimeError(f'问题2单日求解失败: {res.message}')
    x = np.rint(res.x).astype(int).reshape(G, K)
    return int(x.sum()), x, res


def build_problem3_patterns(G, H, shift_cover_same, shift_labels_same, shift_cover_cross, shift_labels_cross):
    patterns = []
    covers = []
    for g in range(G):
        for k, cov in enumerate(shift_cover_same):
            mat = np.zeros((G, H), dtype=int)
            mat[g, :] = cov
            patterns.append({'type': 'same_group', 'g1': g, 'g2': g, 'shift': shift_labels_same[k]})
            covers.append(mat)
    for g1 in range(G):
        for g2 in range(G):
            if g1 == g2:
                continue
            for k, (s1, e1, s2, e2) in enumerate(shift_labels_cross):
                mat = np.zeros((G, H), dtype=int)
                mat[g1, s1:e1] = 1
                mat[g2, s2:e2] = 1
                patterns.append({'type': 'cross_group', 'g1': g1, 'g2': g2, 'shift': (s1, e1, s2, e2)})
                covers.append(mat)
    return patterns, np.array(covers, dtype=int)


def solve_daily_problem3(req_day, pattern_cover):
    P, G, H = pattern_cover.shape
    A = lil_matrix((G*H, P), dtype=float)
    lb = np.zeros(G*H)
    ub = np.full(G*H, np.inf)
    row = 0
    for g in range(G):
        for h in range(H):
            for p in range(P):
                if pattern_cover[p, g, h]:
                    A[row, p] = 1
            lb[row] = req_day[g, h]
            row += 1
    c = np.ones(P)
    res = milp(c=c, integrality=np.ones(P), bounds=Bounds(np.zeros(P), np.full(P, np.inf)), constraints=LinearConstraint(csr_matrix(A), lb, ub), options={'time_limit': TIME_LIMIT, 'mip_rel_gap': 0})
    if not res.success:
        raise RuntimeError(f'问题3单日求解失败: {res.message}')
    x = np.rint(res.x).astype(int)
    return int(x.sum()), x, res


def choose_daily_work_counts(day_min):
    day_min = np.array(day_min, dtype=int)
    W = max(int(day_min.max()), int(math.ceil(day_min.sum() / 8)))
    y = day_min.copy()
    extra = 8 * W - int(y.sum())
    d = 0
    while extra > 0:
        add = min(extra, W - y[d])
        if add > 0:
            y[d] += add
            extra -= add
        d = (d + 1) % len(y)
    if y.max() > W or y.sum() != 8 * W:
        raise RuntimeError('全局工作日分配失败')
    return W, y


def assign_workers_by_work_counts(W, y):
    rest_counts = [W - int(v) for v in y]
    if sum(rest_counts) != 2 * W:
        raise ValueError('休息日总数不等于2W')
    heap = [(-cnt, d) for d, cnt in enumerate(rest_counts) if cnt > 0]
    heapq.heapify(heap)
    rests = []
    for _ in range(W):
        if len(heap) < 2:
            raise RuntimeError('休息日构造失败，请检查日出勤人数')
        c1, d1 = heapq.heappop(heap)
        c2, d2 = heapq.heappop(heap)
        rests.append({d1, d2})
        c1 += 1
        c2 += 1
        if c1 < 0:
            heapq.heappush(heap, (c1, d1))
        if c2 < 0:
            heapq.heappush(heap, (c2, d2))
    schedule = np.ones((W, len(y)), dtype=int)
    for i, rs in enumerate(rests):
        for d in rs:
            schedule[i, d] = 0
    if not np.all(schedule.sum(axis=1) == 8):
        raise RuntimeError('存在工人工作天数不是8天')
    if not np.all(schedule.sum(axis=0) == y):
        raise RuntimeError('每日出勤人数不匹配')
    return schedule


def expand_problem1_worker_schedule(group_id, N, x, days, hours, group_cols, shift_labels):
    y = x.sum(axis=1)
    work = assign_workers_by_work_counts(N, y)
    rows = []
    worker_names = [f'G{group_id+1:02d}-{i+1:03d}' for i in range(N)]
    day_shift_lists = []
    for d in range(len(days)):
        arr = []
        for k, cnt in enumerate(x[d]):
            arr += [time_label(hours, shift_labels[k])] * int(cnt)
        day_shift_lists.append(arr)
    ptr = [0] * len(days)
    for i, name in enumerate(worker_names):
        row = {'工人编号': name, '固定小组': group_cols[group_id]}
        for d, day in enumerate(days):
            if work[i, d] == 0:
                row[f'第{day}天'] = '休息'
            else:
                row[f'第{day}天'] = day_shift_lists[d][ptr[d]]
                ptr[d] += 1
        rows.append(row)
    return pd.DataFrame(rows)


def expand_global_worker_schedule(prefix, W, y, daily_plan_lists, days):
    work = assign_workers_by_work_counts(W, y)
    ptr = [0] * len(days)
    rows = []
    for i in range(W):
        row = {'工人编号': f'{prefix}-{i+1:03d}'}
        for d, day in enumerate(days):
            if work[i, d] == 0:
                row[f'第{day}天'] = '休息'
            else:
                row[f'第{day}天'] = daily_plan_lists[d][ptr[d]]
                ptr[d] += 1
        rows.append(row)
    return pd.DataFrame(rows)


def plan_list_problem2(x_day, hours, group_cols, shift_labels):
    arr = []
    G, K = x_day.shape
    for g in range(G):
        for k in range(K):
            arr += [f'{group_cols[g]}：{time_label(hours, shift_labels[k])}'] * int(x_day[g, k])
    return arr


def plan_list_problem3(x_day, patterns, hours, group_cols):
    arr = []
    for p, cnt in enumerate(x_day):
        if cnt <= 0:
            continue
        pat = patterns[p]
        s1, e1, s2, e2 = pat['shift']
        if pat['type'] == 'same_group':
            text = f'{group_cols[pat["g1"]]}：{hours[s1].split("-")[0]}-{hours[e1-1].split("-")[1]} + {hours[s2].split("-")[0]}-{hours[e2-1].split("-")[1]}'
        else:
            text = f'{group_cols[pat["g1"]]} {hours[s1].split("-")[0]}-{hours[e1-1].split("-")[1]}；{group_cols[pat["g2"]]} {hours[s2].split("-")[0]}-{hours[e2-1].split("-")[1]}'
        arr += [text] * int(cnt)
    return arr


def add_extra_plans(plan_lists, y):
    out = []
    for d, arr in enumerate(plan_lists):
        arr = list(arr)
        while len(arr) < y[d]:
            arr.append(arr[0] if arr else '小组1：8:00-12:00 + 12:00-16:00')
        out.append(arr)
    return out


def main():
    demand, days, hours, group_cols = read_demand(INPUT_FILE)
    D, G, H = demand.shape
    shift_pairs0, shift_cover0, shift_labels0 = build_shift_pairs(min_break=0)
    shift_pairs2, shift_cover2, shift_labels2 = build_shift_pairs(min_break=2)

    q1_N = []
    q1_x = []
    q1_status = []
    for g in range(G):
        N, x, res = solve_problem1_one_group(demand[:, g, :], shift_cover0)
        q1_N.append(N)
        q1_x.append(x)
        q1_status.append(res.message)
        print('Q1', group_cols[g], N)
    print('Q1 total', sum(q1_N))

    q2_day_min = []
    q2_x_days = []
    for d in range(D):
        n, x, res = solve_daily_problem2(demand[d], shift_cover0)
        q2_day_min.append(n)
        q2_x_days.append(x)
        print('Q2 day', days[d], n)
    q2_W, q2_y = choose_daily_work_counts(q2_day_min)
    print('Q2 W', q2_W, 'y', q2_y.tolist(), 'mins', q2_day_min)

    patterns3, cover3 = build_problem3_patterns(G, H, shift_cover0, shift_labels0, shift_cover2, shift_labels2)
    q3_day_min = []
    q3_x_days = []
    for d in range(D):
        n, x, res = solve_daily_problem3(demand[d], cover3)
        q3_day_min.append(n)
        q3_x_days.append(x)
        print('Q3 day', days[d], n)
    q3_W, q3_y = choose_daily_work_counts(q3_day_min)
    print('Q3 W', q3_W, 'y', q3_y.tolist(), 'mins', q3_day_min)

    summary = pd.DataFrame({
        '项目': ['问题1总人数', '问题2总人数', '问题3总人数'],
        '最少招聘人数': [sum(q1_N), q2_W, q3_W]
    })
    q1_group_df = pd.DataFrame({'小组': group_cols, '最少人数': q1_N})
    q2_day_df = pd.DataFrame({'天': days, '单日最少出勤人数': q2_day_min, '考虑每人工作8天后的安排出勤人数': q2_y})
    q3_day_df = pd.DataFrame({'天': days, '单日最少出勤人数': q3_day_min, '考虑每人工作8天后的安排出勤人数': q3_y})

    q1_shift_rows = []
    for g in range(G):
        for d in range(D):
            row = {'小组': group_cols[g], '天': days[d]}
            for k, lab in enumerate(shift_labels0):
                row[time_label(hours, lab)] = int(q1_x[g][d, k])
            q1_shift_rows.append(row)
    q1_shift_df = pd.DataFrame(q1_shift_rows)

    q2_shift_rows = []
    for d in range(D):
        for g in range(G):
            row = {'天': days[d], '小组': group_cols[g]}
            for k, lab in enumerate(shift_labels0):
                row[time_label(hours, lab)] = int(q2_x_days[d][g, k])
            q2_shift_rows.append(row)
    q2_shift_df = pd.DataFrame(q2_shift_rows)

    q3_rows = []
    for d in range(D):
        for p, cnt in enumerate(q3_x_days[d]):
            if cnt > 0:
                pat = patterns3[p]
                s1, e1, s2, e2 = pat['shift']
                if pat['type'] == 'same_group':
                    desc = f'{group_cols[pat["g1"]]}：{hours[s1].split("-")[0]}-{hours[e1-1].split("-")[1]} + {hours[s2].split("-")[0]}-{hours[e2-1].split("-")[1]}'
                else:
                    desc = f'{group_cols[pat["g1"]]} {hours[s1].split("-")[0]}-{hours[e1-1].split("-")[1]}；{group_cols[pat["g2"]]} {hours[s2].split("-")[0]}-{hours[e2-1].split("-")[1]}'
                q3_rows.append({'天': days[d], '模式类型': pat['type'], '模式说明': desc, '人数': int(cnt)})
    q3_plan_df = pd.DataFrame(q3_rows)

    q1_worker_df = pd.concat([expand_problem1_worker_schedule(g, q1_N[g], q1_x[g], days, hours, group_cols, shift_labels0) for g in range(G)], ignore_index=True)

    q2_plans = [plan_list_problem2(q2_x_days[d], hours, group_cols, shift_labels0) for d in range(D)]
    q2_plans = add_extra_plans(q2_plans, q2_y)
    q2_worker_df = expand_global_worker_schedule('Q2', q2_W, q2_y, q2_plans, days)

    q3_plans = [plan_list_problem3(q3_x_days[d], patterns3, hours, group_cols) for d in range(D)]
    q3_plans = add_extra_plans(q3_plans, q3_y)
    q3_worker_df = expand_global_worker_schedule('Q3', q3_W, q3_y, q3_plans, days)

    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        summary.to_excel(writer, sheet_name='Summary', index=False)
        q1_group_df.to_excel(writer, sheet_name='Q1_GroupTotals', index=False)
        q1_shift_df.to_excel(writer, sheet_name='Q1_ShiftCounts', index=False)
        q2_day_df.to_excel(writer, sheet_name='Q2_DaySummary', index=False)
        q2_shift_df.to_excel(writer, sheet_name='Q2_ShiftCounts', index=False)
        q3_day_df.to_excel(writer, sheet_name='Q3_DaySummary', index=False)
        q3_plan_df.to_excel(writer, sheet_name='Q3_PatternCounts', index=False)
        q1_worker_df.to_excel(writer, sheet_name='Q1_WorkerSchedule', index=False)
        q2_worker_df.to_excel(writer, sheet_name='Q2_WorkerSchedule', index=False)
        q3_worker_df.to_excel(writer, sheet_name='Q3_WorkerSchedule', index=False)
    print(f'结果已保存：{OUTPUT_FILE}')

if __name__ == '__main__':
    main()
