import os
import subprocess

bootstrap_dir = '/cbica/projects/rosmap_fmri/production/xcp-multises/'

#######

# go to alias dir in output_ria
alias_dir = os.path.join(bootstrap_dir,'output_ria/alias/data/')
os.chdir(alias_dir)

# get list of all jobs
output = subprocess.check_output('git branch -a',shell=True)
alljobs = output.decode().split('\n  ')

# discover duplicates
dups = []
catch = []
for job in alljobs:
    subses = job.split('sub-')[-1]
    if subses in catch:
        dups.append(job)
    else:
        catch.append(subses)

print('found %s duplicates'%len(dups))

# delete duplicate branches
for dup in dups:
    os.system('git branch -D %s'%dup)


