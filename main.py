#coding=gbk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='ticks')

from scipy import stats
from sklearn.decomposition import PCA
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, GridSearchCV, learning_curve, RepeatedKFold

from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV
from sklearn.svm import SVR
from xgboost import XGBRegressor

import warnings
warnings.filterwarnings('ignore')


dtrain = pd.read_csv('zhengqi_train.txt', sep='\t')
dtest = pd.read_csv('zhengqi_test.txt', sep='\t')
dfull = pd.concat([dtrain, dtest], ignore_index=True, sort=False)
print('ѵ������С: ', np.shape(dtrain))
print('���Լ���С: ', np.shape(dtest))

print('ȱʧֵͳ�ƣ�')
print(dfull.apply(lambda x: sum(x.isnull())))

# �۲����ݻ����ֲ����
plt.figure(figsize=(18, 8), dpi=100)
dfull.boxplot(sym='r^', patch_artist=True, notch=True)
plt.title('DATA-FULL')


# �����������������ͼ���鿴������������
def heatmap(df):
    plt.figure(figsize=(20, 16), dpi=100)
    cols = df.columns.tolist()
    mcorr = df[cols].corr(method='spearman')
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    mask = np.zeros_like(mcorr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True  # �Ƿ����Ҳ�ΪTrue
    g = sns.heatmap(mcorr, mask=mask, cmap=cmap, square=True, annot=True, fmt='0.2f')
    plt.xticks(rotation=45)
    return mcorr
dtrain_mcorr = heatmap(dtrain)

# ɾ��dfull����ָ������
def drop_var(var_lst):
    dfull.drop(var_lst, axis=1, inplace=True)


# ��dfull���·ָ�Ϊdtrain��dtest
def split_dfull():
    dtrain = dfull[dfull['target'].notnull()]
    dtest = dfull[dfull['target'].isnull()]
    dtest.drop('target', axis=1, inplace=True)
    return dtrain, dtest

# �޳�ѵ��������Լ��ֲ������ȵ���������
plt.figure(figsize=(20,50),dpi=100)
for i in range(38):
    plt.subplot(10,4,i+1)
    sns.distplot(dtrain.iloc[:,i], color='green')
    sns.distplot(dtest.iloc[:,i], color='red')
    plt.legend(['Train', 'Test'])

# �Ӹ��������ݷֲ�ֱ��ͼ���֣�
# V5��V9��V11��V17��V20��V21��V22��V27��V28 ����ѵ�����Ͳ��Լ��ֲ��������
# ���Ϊ�˼�С���ݷֲ�������Ԥ������Ӱ�죬Ӧ���������������޳�
plt.tight_layout()
drop_var(['V5','V9','V11','V17','V20','V21','V22','V27','V28'])
dtrain, dtest = split_dfull()

# ɾ���޹ر���
drop_var(['V14','V25','V26','V32','V33','V34','V35'])
dtrain, dtest = split_dfull()

# ��ƫ̬���ݽ�����̬��ת��
# �ֲ���������ƫ������
piantai = ['V0','V1','V6','V7','V8','V12','V16','V31']

# �������������ҵ���ƫ̬ϵ������ֵ��С�Ķ���ת���ĵ�
def find_min_skew(data):
    subs = list(np.arange(1.01,2,0.01))
    skews = []
    for x in subs:
        skew = abs(stats.skew(np.power(x,data)))
        skews.append(skew)
    min_skew = min(skews)
    i = skews.index(min_skew)
    return subs[i], min_skew

# ��ѵ�����Ͳ��Լ�ƫ̬����ͬʱ���ж���ת��
for col in piantai:
    sub = find_min_skew(dfull[col])[0]
    dfull[col] = np.power(sub, dfull[col])
dtrain, dtest = split_dfull()

# ���� z-score��׼�� ����
dfull.iloc[:,:-1] = dfull.iloc[:,:-1].apply(lambda x: (x-x.mean())/x.std())
dtrain, dtest = split_dfull()

# ѵ��ģ��

# ��ѵ�����ݷָ�Ϊѵ��������֤��

X = np.array(dtrain.iloc[:,:-1])
y = np.array(dtrain['target'])

X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=0)

# ����ģ�����ֺ���

def score(y, y_pred):
    # ���������� MSE
    print('MSE = {0}'.format(mean_squared_error(y, y_pred)))
    # ����ģ�;���ϵ�� R2
    print('R2 = {0}'.format(r2_score(y, y_pred)))

    # ����Ԥ��в���쳣��
    y = pd.Series(y)
    y_pred = pd.Series(y_pred, index=y.index)
    resid = y - y_pred
    mean_resid = resid.mean()
    std_resid = resid.std()
    z = (resid - mean_resid) / std_resid
    n_outliers = sum(abs(z) > 3)

    # ͼһ����ʵֵvsԤ��ֵ
    plt.figure(figsize=(18, 5), dpi=80)
    plt.subplot(131)
    plt.plot(y, y_pred, '.')
    plt.xlabel('y')
    plt.ylabel('y_pred')
    plt.title('corr = {:.3f}'.format(np.corrcoef(y, y_pred)[0][1]))

    # ͼ�����в�ֲ�ɢ��ͼ
    plt.subplot(132)
    plt.plot(y, y - y_pred, '.')
    plt.xlabel('y')
    plt.ylabel('resid')
    plt.ylim([-3, 3])
    plt.title('std_resid = {:.3f}'.format(std_resid))

    # ͼ�����в�z�÷�ֱ��ͼ
    plt.subplot(133)
    sns.distplot(z, bins=50)
    plt.xlabel('z')
    plt.title('{:.0f} samples with z>3'.format(n_outliers))
    plt.tight_layout()

# ����RidgeCV�����Զ�Ѱ�����Ų���
ridge = RidgeCV()
ridge.fit(X_train, y_train)
print('best_alpha = {0}'.format(ridge.alpha_))

# ��ʼģ��ѵ��ǰ��������ع�ģ��Ԥ�⣬�޳��쳣����
y_pred = ridge.predict(X_train)
score(y_train, y_pred)

# �ҳ��쳣�����㲢�޳�
resid = y_train - y_pred
resid = pd.Series(resid, index=range(len(y_train)))
resid_z = (resid-resid.mean()) / resid.std()
outliers = resid_z[abs(resid_z)>3].index
print(f'{len(outliers)} Outliers:')
print(outliers.tolist())

plt.figure(figsize=(14,6),dpi=60)

plt.subplot(121)
plt.plot(y_train, y_pred, '.')
plt.plot(y_train[outliers], y_pred[outliers], 'ro')
plt.title(f'MSE = {mean_squared_error(y_train,y_pred)}')
plt.legend(['Accepted', 'Outliers'])
plt.xlabel('y_train')
plt.ylabel('y_pred')

plt.subplot(122)
sns.distplot(resid_z, bins = 50)
sns.distplot(resid_z.loc[outliers], bins = 50, color = 'r')
plt.legend(['Accepted', 'Outliers'])
plt.xlabel('z')
plt.tight_layout()

# ��ʼ����ģ��ѵ��

# ����LassoCV�Զ�ѡ��������򻯲���
lasso = LassoCV(cv=5)
lasso.fit(X_train, y_train)
print('best_alpha = {0}'.format(lasso.alpha_))

pred_lasso = lasso.predict(X_valid)
score(y_valid, pred_lasso)

# ʹ��sklearn�е������������� GridSearchCV Ѱ��SVR����ģ�Ͳ���
# ����GridSearchCV���������Ѱ���������۱�׼Ϊ��С����������K�۽�����֤�ļ��鷽��
def gsearch(model, param_grid, scoring='neg_mean_squared_error', splits=5, repeats=1, n_jobs=-1):
    # p��k�۽�����֤
    rkfold = RepeatedKFold(n_splits=splits, n_repeats=repeats, random_state=0)
    model_gs = GridSearchCV(model, param_grid=param_grid, scoring=scoring, cv=rkfold, verbose=1, n_jobs=-1)
    model_gs.fit(X_train, y_train)
    print('�������ȡֵ: {0}'.format(model_gs.best_params_))
    print('��С�������: {0}'.format(abs(model_gs.best_score_)))
    return model_gs

# ��С������Χ����ϸ��
svr = SVR()
cv_params = {'C': [1,2,5,10,15,20,30,50,80,100,150,200], 'gamma': [0.0001,0.0005,0.0008,0.001,0.002,0.003,0.005]}
svr = gsearch(svr, cv_params)

# ��֤��Ԥ��
pred_svr = svr.predict(X_valid)
score(y_valid, pred_svr)

# XGBRegressor��������

# ��ʼ����ֵ
params = {'learning_rate': 0.1, 'n_estimators': 500, 'max_depth': 5, 'min_child_weight': 1, 'seed': 0,
          'subsample': 0.8, 'colsample_bytree': 0.8, 'gamma': 0, 'reg_alpha': 0, 'reg_lambda': 1}

# ��ѵ���������n_estimators �ó���ѽ��Ϊ500
cv_params = {'n_estimators': [100,200,300,400,500,600,700,800,900,1000,1100,1200]}
xgb = XGBRegressor(**params)
xgb = gsearch(xgb, cv_params)
# ���²���
params['n_estimators'] = 500

# min_child_weight  �Լ� max_depth ���Ϊ4 ��4
cv_params = {'max_depth': [3,4,5,6,7,8,9],
            'min_child_weight': [1,2,3,4,5,6,7]}
xgb = XGBRegressor(**params)
xgb = gsearch(xgb, cv_params)
params['max_depth'] = 4
params['min_child_weight'] = 7

# ���֦���� gamma ���Ϊ0
cv_params = {'gamma': [0,0.01,0.05,0.1,0.2,0.3,0.4,0.5,0.6]}
xgb = XGBRegressor(**params)
xgb = gsearch(xgb, cv_params)
params['gamma'] = 0

# ��������subsample �� �в���colsample_bytree ���Ϊ 0.8 0.8
cv_params = {'subsample': [0.6,0.7,0.8,0.9],
            'colsample_bytree': [0.6,0.7,0.8,0.9]}
xgb = XGBRegressor(**params)
xgb = gsearch(xgb, cv_params)
params['subsample'] = 0.8
params['colsample_bytree'] = 0.8

# L1���������reg_alpha �� L2���������reg_lambda ���Ϊ0 1
cv_params = {'reg_alpha': [0,0.02,0.05,0.1,1,2,3],
             'reg_lambda': [0,0.02,0.05,0.1,1,2,3]}
xgb = XGBRegressor(**params)
xgb = gsearch(xgb, cv_params)
params['reg_alpha'] = 0
params['reg_lambda'] = 1

# �����learning_rate ���Ϊ 0.04
cv_params = {'learning_rate': [0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.1, 0.2]}
xgb = XGBRegressor(**params)
xgb = gsearch(xgb, cv_params)
params['learning_rate'] = 0.04

# ����������ɣ�����֤������ģ�������֤
pred_xgb = xgb.predict(X_valid)
score(y_valid, pred_xgb)

# ģ������

# ѵ��������֤����׼ȷ�ʵı仯����
models = [lasso, svr, xgb]
model_names = ['Lasso', 'SVR', 'XGB']
plt.figure(figsize=(20, 5))

for i, m in enumerate(models):
    train_sizes, train_scores, test_scores = learning_curve(m, X, y, cv=5, scoring='neg_mean_squared_error',
                                                            train_sizes=np.linspace(0.1, 1.0, 5), n_jobs=-1)
    train_scores_mean = -train_scores.mean(axis=1)
    test_scores_mean = -test_scores.mean(axis=1)

    plt.subplot(1, 3, i + 1)
    plt.plot(train_sizes, train_scores_mean, 'o-', label='Train')
    plt.plot(train_sizes, test_scores_mean, '^-', label='Test')
    plt.xlabel('Train_size')
    plt.ylabel('Score')
    plt.ylim([0, 0.35])
    plt.title(model_names[i], fontsize=16)
    plt.legend()
    plt.grid()

plt.tight_layout()

# ģ�ͼ�Ȩ�ں�
def model_mix(pred_1, pred_2, pred_3):
    result = pd.DataFrame(columns=['Lasso','SVR','XGB','Combine'])
    for a in range(5):
        for b in range(1,6):
            for c in range(5):
                y_pred = (a*pred_1 + b*pred_2 + c*pred_3) / (a+b+c)
                mse = mean_squared_error(y_valid, y_pred)
                result = result.append([{'Lasso':a, 'SVR':b, 'XGB':c, 'Combine':mse}], ignore_index=True)
    return result

model_combine = model_mix(pred_lasso, pred_svr, pred_xgb)
model_combine.sort_values(by='Combine', inplace=True)
model_combine.head()

# ģ��Ԥ��
X_test = np.array(dtest)
ans_lasso = lasso.predict(X_test)
ans_svr = svr.predict(X_test)
ans_xgb = xgb.predict(X_test)
ans_mix = (ans_lasso + 5 * ans_svr + 2 * ans_xgb) / 8
pd.Series(ans_mix).to_csv('��̬+��׼��.txt', sep='\t', index=False)
print('Finished!')
