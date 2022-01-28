#encoding:utf-8
from urllib import request
import json
import subprocess,shlex
import os

old_git_url = "https://gitlab.aaa.com/api/v4"
old_git_token = "xxx"
new_git_url = "https://gitlab.bbb.com/api/v4"
new_git_token = "yyy"
new_groups = []
new_groups_paths = []
# 获取当前文件路径
parentPath = os.getcwd()
# print("parentPath=" + parentPath)

# 获取所有分组
def queryGroups(git_url, git_token):
    #获取所有group,其中private_token就是access_token
    allgroups = request.urlopen(git_url + "/groups?per_page=100&private_token=" + git_token)
    allgroupsDict = json.loads(allgroups.read().decode())
    return allgroupsDict

# 获取所有分组路径
def queryGroupsPaths(groups):
    paths = []
    for group in groups:
        # print (groups)
        paths.append(group['full_path'])
    return paths

# 新建分组
def createGroup(group):
    if group["parent_id"]:
        parent_group_path = group['full_path'].rsplit('/',1)[0]
        # print ('parent_group_id=%s >>>>> parent_group_path=%s >>> current_group_path=%s' % (str(group["parent_id"]), parent_group_path, group['full_path']))
        group['parent_id'] = queryGroupIds(parent_group_path)
        # for gp in new_groups:
            # print (gp)
            # print ('parent_group_path=%s >>> current_group_path=%s' % (parent_group_path, gp['full_path']))
            # if parent_group_path == gp['full_path']:
            #     group['parent_id'] = gp['id']
            #     break

    # print (group)
    #json串数据使用
    textmod = json.dumps(group).encode(encoding='utf-8')
    header_dict = {"PRIVATE-TOKEN": new_git_token, 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
    url = new_git_url + "/groups"
    req = request.Request(url=url, data=textmod, headers=header_dict)
    res = request.urlopen(req)
    res = res.read()
    new_group = json.loads(res.decode(encoding='utf-8'))
    # print (new_group)
    return new_group

def queryGroupIds(groupPath):
    for gp in new_groups:
        # print (gp)
        # print ('parent_group_path=%s >>> current_group_path=%s' % (parent_group_path, gp['full_path']))
        if groupPath == gp['full_path']:
            return gp['id']
    return None

# 检查分组，没有就创建
def checkGroup(group):
    global new_groups, new_groups_paths, parentPath

    groupFullPath = group['full_path']
    # 查看本地对应的分组目录是否存在，没有就创建
    existsDir = os.path.exists(parentPath+"/"+groupFullPath)
    if not existsDir:
        os.makedirs(parentPath+"/"+groupFullPath)

    # 遍历新gitlab查看分组是否存在，不存在就创建
    # groupPaths = groupFullPath.split('/')
    # current_gp = ''
    # for gpIndex in range(len(groupPaths)):
    #     if gpIndex == 0:
    #         current_gp = groupPaths[gpIndex]
    #     else:
    #         current_gp += '/' + groupPaths[gpIndex]
    #     if current_gp not in groupsPaths:
    #         createGroup(group)
    if groupFullPath not in new_groups_paths:
        new_group = createGroup(group)
        # print ('before >>> group length=%d, groups paths=%d' % (len(new_groups), len(new_groups_paths)))
        # 创建成功的分组加入到 new_groups
        new_groups.append(new_group)
        # 更新 new_groups
        new_groups_paths = queryGroupsPaths(new_groups)
        # print ('end <<< group length=%d, groups paths=%d' % (len(new_groups), len(new_groups_paths)))

# 获取分组下的所有项目
def queryProjectsByGid(groupId):
    projects = request.urlopen(old_git_url + "/groups/"+groupId+"/projects?per_page=1&private_token=e7c48jG5p8xyoGq8T-mx")
    projectsDict = json.loads(projects.read().decode())
    return projectsDict

# 新建项目
def createProject(project):
    #json串数据使用
    project['namespace_id'] = queryGroupIds(project['namespace']['full_path'])
    textmod = json.dumps(project).encode(encoding='utf-8')
    header_dict = {"PRIVATE-TOKEN": new_git_token, 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
    post_url = new_git_url + "/projects"
    # print ('create project url=%s' % post_url)
    # print (project)
    req = request.Request(url=post_url, data=textmod, headers=header_dict)
    res = request.urlopen(req)
    res = res.read()
    new_project = json.loads(res.decode(encoding='utf-8'))
    # print (new_project)
    return new_project

# 拉取代码
def cloneProject(project):
    # 先 clone 旧 gitlab 项目
    path = project['http_url_to_repo']
    command = shlex.split('git clone --mirror %s %s' % (path, project['path']))
    reresultCode = subprocess.Popen(command)
    print("project url=%s, result=%s" % (path, reresultCode))

    # 进入新 clone 下来的项目目录里
    # os.chdir(parentPath+"/"+project['namespace']['full_path']+"/"+project['path'])

    # 在新 gitlab 创建新的项目
    # new_project = createProject(project)
    # 把项目上传到新 gitlab
    # pushProject(new_project['http_url_to_repo'])

# 提交代码
def pushProject(path):
    command = shlex.split('git remote set-url origin %s' % path)
    reresultCode = subprocess.Popen(command)
    command = shlex.split('git push -f origin')
    reresultCode = subprocess.Popen(command)
    print("push project url=%s, result=%s" % (path, reresultCode))

groups = queryGroups(old_git_url, old_git_token)
groups.sort(key = lambda x:x["full_path"])
groups = groups[0:1:1]
new_groups = queryGroups(new_git_url, new_git_token)
new_groups_paths = queryGroupsPaths(new_groups)

for group in groups:

    try:
        groupFullPath = group['full_path']
        groupId = group['id']
        # print("group full path=%s, groupId=%s" % (groupFullPath, groupId))

        # 这里我只clone AAAA这个group下的仓库
        # if "AAAA" in groupFullPath:

        # 遍历查看新gitlab分组和本地目录是否存在，不存在就创建
        checkGroup(group)

        # 保持文件目录与远程仓库一直，并切换到目录
        os.chdir(parentPath+"/"+groupFullPath)

        # 获取当前group下的所有仓库
        projects = queryProjectsByGid(str(groupId))
        for project in projects:
            try:
                projectUrl = project['http_url_to_repo']
                # print (project)
                # try:
                    # 因为我本地git clone 配置的是http格式的，所以我选择了http_url_to_repo, 如果你是用的git@格式，你就选择ssh_url_to_repo
                # cloneProject(project)
                # except Exception as e:
                    # print("Error on copy %s: %s" % (projectUrl, e.strerror))

                # 在新 gitlab 创建新的项目
                # new_project = createProject(project)

                # print ('----------------------------------')
                # 进入项目目录
                os.chdir(parentPath+"/"+groupFullPath+"/"+project['path'])
                # print ('----------------------------------')
                # 把项目上传到新 gitlab
                # pushProject(projectUrl.replace("https://gitlab.aaa.com", "https://root@gitlab.bbb.com"))
                pushProject(project['ssh_url_to_repo'].replace("git@gitlab.aaa.com", "git@gitlab.bbb.com:root"))
                # os.rmdir(parentPath+"/"+groupFullPath+project['path'])
    
            except Exception as e:
                print("Error on %s: %s: %s" % (parentPath+"/"+groupFullPath+"/"+project['path'], projectUrl, e.strerror))
        
    except Exception as e:
        print("Error on %s: %s" % (groupFullPath, e.strerror))
