import os
import pandas
import numpy as np
from scipy import stats
from itertools import product
from sklearn.linear_model import LassoCV, ElasticNetCV, LogisticRegressionCV
from sklearn.svm import SVR, SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split, KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectPercentile, f_regression, f_classif, SelectFdr
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score, recall_score
from xgboost import XGBRFRegressor, XGBRFClassifier
from pennlinckit.utils import get_sge_task_id


GMVS = pandas.read_csv('/Users/jacobv/Science/ROSMAP/ResilSig/GM_ML/GMVS.csv',index_col=0)
regr = pandas.read_csv('/Users/jacobv/Science/ROSMAP/ResilSig/GM_ML/regr.csv',index_col=0)
featdict = pandas.read_pickle('/Users/jacobv/Science/ROSMAP/ResilSig/GM_ML/featnames.pk')
outdir = ''


modkind = 'reg'

# param grids
SVR_PG = {'C': [0.1, 1, 10, 100, 1000], 'gamma':[0.1, 1, 10,]}
RFR_PG = {'max_depth': [3, 5, 7, 10, 15, 20, 40, 50, None]}
EN_PG = {'l1_ratio': [.1, .5, .7, .9, .95, .99, 1]}

if modkind = 'reg':
    
    # models
    models = {'reg-Lasso': LassoCV(random_state=123, n_jobs=2,max_iter=1000),
              'reg-EN': GridSearchCV(ElasticNetCV(random_state=123),EN_PG,n_jobs=2),
             'reg-SVR': GridSearchCV(SVR(kernel='linear'),SVR_PG,n_jobs=3),
             'reg-RFR': GridSearchCV(RandomForestRegressor(random_state=123,
                                                      oob_score=True),
                                 RFR_PG,n_jobs=3),
             'reg-XGB': GridSearchCV(XGBRFRegressor(n_estimators=100,random_state=123),RFR_PG,n_jobs=3)}

    # paramaters
    options = [['all','ROSMAP'],
              ['unregr','regr'],
              ['zI-II','zI-IV','zInfTemp'],
               ['classic','multises'],
               ['None','SelPerc','SelFDR','PCA'],
               ['reg-Lasso','reg-EN','reg-SVR','reg-RFR','reg-XGB']]

elif modkind == 'clf':

    # models
    models = {'clf-LR': LogisticRegressionCV(random_state=123, penalty='elasticnet', n_jobs=2,max_iter=1000,
                                             scoring='average_precision'),
             'clf-SVC': GridSearchCV(SVC(kernel='linear',random_state=123),SVR_PG,n_jobs=3, scoring='average_precision'),
             'clf-RFC': GridSearchCV(RandomForestClassifier(random_state=123,
                                                      oob_score=True),
                                 RFR_PG,n_jobs=3,scoring='average_precision'),
             'clf-XGBC': GridSearchCV(XGBRFClassifier(n_estimators=100,random_state=123),RFR_PG,n_jobs=3,
                                      scoring='average_precision')}

    # paramaters
    options = [['all','ROSMAP'],
              ['unregr','regr'],
              ['I-IIpos','I-IVpos','InfTemppos'],
               ['classic','multises'],
               ['None','SelPerc','SelFDR','PCA'],
               ['clf-LR','clf-SVC','clf-RFC','clf-XGB']]

def build_namestring(options):
    iterations = list(product(*options))
    out_strings = []
    for it in iterations:
        string = ''
        for i,item in enumerate(it):
            if i == (len(it)-1):
                string+=item
            else:
                string+='%s_'%item
        out_strings.append(string)
        
    return out_strings

def inputs_builder(namestring,unregdf,regrdf,feat_input,model_input,modkind):
    
    jnk = namestring.split('_')
    xcols = feat_input[jnk[0]]
    if jnk[1] == 'regr':
        df = regrdf
    else:
        df = unregdf
    ycols = jnk[2]
    kfold = jnk[3]
    
    if modkind == 'clf':
        selector = f_classif
    else:
        selector = f_regression
    if jnk[4] == 'None': 
        dr = None
    elif jnk[4] == 'SelPerc':
        dr = SelectPercentile(selector,percentile=10)
    elif jnk[4] == 'SelFDR':
        dr = SelectFdr(selector)
    elif jnk[4] == 'PCA':
        pca = PCA(n_components=20,random_state=123)
    
    if jnk[4] == 'None':
        model =  Pipeline([('scale',StandardScaler()),
                           (jnk[5],model_input[jnk[5]])])
    else:
        model =  Pipeline([('scale',StandardScaler()),
                           (jnk[4],dr),
                           (jnk[5],model_input[jnk[5]])])
    
    return df,xcols,ycols,model,kfold,modkind,namestring


def unique_id_kfold(fid_df, full_df, ref_df, cv_object, groups, 
                    split_col='Family_ID'):
    
    ref_df = pandas.DataFrame(ref_df,copy=True)
    ref_df.loc[:,'row_num'] = range(len(ref_df))
    
    train_test_tuple_list = []
    for train_idx, test_idx in cv_object.split(fid_df,groups=groups):
        train_i = fid_df.iloc[train_idx]
        train_fid = train_i[split_col].values
        train_full = full_df[full_df[split_col].isin(train_fid)]
        all_train = train_i.index.tolist() + train_full.index.tolist()
        final_tr_idx = ref_df.loc[all_train,'row_num'].tolist()
        
        test_i = fid_df.iloc[test_idx]
        test_fid = test_i[split_col].values
        test_full = full_df[full_df[split_col].isin(test_fid)]
        all_test = test_i.index.tolist() + test_full.index.tolist()
        final_te_idx = ref_df.loc[all_test,'row_num'].tolist()
        
        train_test_tuple_list.append((final_tr_idx,final_te_idx))

    return train_test_tuple_list

def ML_Pipeline(outdir,df,xcols,ycols,model,kfold,modkind,namestring,
                n_iter=100,scancol='asegscan',scanval=1,cv_nsplits=5):
    
    results = pandas.DataFrame()
    if kfold == 'classic':
        df = df[df[scancol]==scanval]
    goodind = df[xcols+[ycols]].dropna().index
    df = df.loc[goodind]
    X = df.loc[goodind,xcols]
    y = df.loc[goodind,ycols]
    ind = 0
    for i in range(n_iter):
        in_sids = X.index
        preds = []
        trues = []
        done = False
        kf = KFold(n_splits=cv_nsplits,shuffle=True,random_state=123+i)
        if kfold == 'classic':
            for tr_ind,te_ind in kf.split(in_sids):
                Xtr = X.loc[in_sids[tr_ind]]
                Xte = X.loc[in_sids[te_ind]]
                ytr = y.loc[in_sids[tr_ind]]
                yte = y.loc[in_sids[te_ind]]
                model.fit(Xtr,ytr) 
                pred = model.predict(Xte).tolist()
                preds += pred
                trues += yte.values.tolist()
        elif kfold == 'multises':
            uidf = pandas.DataFrame(df[df[scancol]==scanval],copy=True)
            oidf = pandas.DataFrame(df[df[scancol]!=scanval],copy=True)
            kf = unique_id_kfold(uidf, oidf,pandas.DataFrame(df,copy=True),
                                    kf, None, split_col=scancol)
            for tr_ind,te_ind in kf:
                Xtr = X.loc[in_sids[tr_ind]]
                Xte = X.loc[in_sids[te_ind]]
                ytr = y.loc[in_sids[tr_ind]]
                yte = y.loc[in_sids[te_ind]]
                model.fit(Xtr,ytr) 
                pred = model.predict(Xte).tolist()
                preds += pred
                trues += yte.values.tolist()
        else:
            raise ValueError('kfold must be set to "classic" or "multises"')
        results.loc[ind,'iteration'] = i
        if modkind == 'reg':
            results.loc[ind,'r2'] = r2_score(trues,preds)
            results.loc[ind,'r'] = stats.pearsonr(trues,preds)[0]
            results.loc[ind,'mse'] = mean_squared_error(trues,preds)
        elif modkind == 'clf':
            results.loc[ind,'acc'] = accuracy_score(trues,preds)
            results.loc[ind,'bacc'] = balanced_accuracy_score(trues,preds)
            results.loc[ind,'prec'] = precision_score(trues,preds)
            results.loc[ind,'recall'] = recall_score(trues,preds)
        else:
            raise ValueError('modkind must be set to "clf" or "regr"')
        jnk = namestring.split('_')
        results.loc[ind,'features'] = jnk[0]
        results.loc[ind,'regr'] = jnk[1]
        results.loc[ind,'dv'] = jnk[2]
        results.loc[ind,'subjects'] = jnk[3]
        results.loc[ind,'dr'] = jnk[4]
        results.loc[ind,'model'] = jnk[5]
        flnm = os.path.join(outdir,'%s.csv'%namestring)
        results.to_csv(flnm)
        ind += 1

##### script
i = get_sge_task_id()
strings = build_namestring(options)
df,xcols,ycols,model,kfold,modkind,namestring = inputs_builder(c_strings[i],
                                                               GMVS,regr,featdict,models,modkind)
ML_Pipeline(outdir,df,xcols,ycols,model,kfold,modkind,namestring,
                n_iter=100,scancol='asegscan',scanval=1,cv_nsplits=5)
