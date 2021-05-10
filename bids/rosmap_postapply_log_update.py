import pandas

datlog_pth = '/cbica/projects/rosmap_fmri/rosmap/BIDS_data_log.csv'
applycmd_pth = '/cbica/projects/rosmap_fmri/rosmap/code/iterations/rmb7_iter2_full_cmd.sh'
it_nm = 'rmb7_iter2'

##### Code

datlog = pandas.read_csv(datlog_pth,index_col=0)
df = pandas.read_csv(applycmd_pth) 

for i,row in df.iterrows():
    cmd = row[df.columns[0]]
    split = cmd.split(' ')
    oldpth,newpth = split[1].split('rawdata/')[1],split[2].split('rawdata/')[1]
    match = datlog[datlog.new_path==oldpth]
    datlog.loc[match.index,'newpath_%s'%it_nm] = newpth

datlog.to_csv(datlog_pth,index=False)