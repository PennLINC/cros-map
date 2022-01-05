from pennlinckit.utils import submit_array_job
from itertools import product

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


options = [['all','ROSMAP'],
              ['unregr','regr'],
              ['I-IIpos','I-IVpos','InfTemppos'],
               ['classic','multises'],
               ['None','SelPerc','SelFDR','PCA'],
               ['clf-LR','clf-SVC','clf-RFC','clf-XGB']]

strings = build_namestring(options)

first_subset = 1
last_subset = len(strings) + 1
submit_array_job('/cbica/projects/NACC_APM_structural/BF2_ML/code/ML_pipeline_clf.py',first_subset,last_subset,RAM=8)
