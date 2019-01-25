#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import os

import PBXProjectHelper
import MobPodsFileManager

import operation
import json

from PBXProjectHelper import *
from MobPodsFileManager import *
from MobPodsSQLHelper import *

reload(sys)
sys.setdefaultencoding("utf-8")

class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

class MobPods(Singleton):

    def __unicode__(self):
        return unicode(self.projPath) or u''

    def __loadProject(self, projPath):

        print "__loadProject" + str(projPath)

        if os.path.exists(projPath):
            self.projectPath = projPath
            self.target = None

            operation.getCurrentProjectPath(projPath)

            # projSqlHelper = MobPodsSQLHelper("%s/__MobTool/mobpods.db" % os.path.dirname(projPath))
            # # 初始化记录导库情况的数据库
            # projSqlHelper.createTable(
            #     "CREATE TABLE IF NOT EXISTS 'Project' ('id' TEXT, 'respositoryName' TEXT, 'target' TEXT, 'localVersion' TEXT, 'dependency' TEXT)")
            # # 将原工程的libs保存到一个新的数据库里
            # projSqlHelper.createTable("CREATE TABLE IF NOT EXISTS 'SysLibs' ('name' TEXT, 'libs' TEXT)")

            return True
        else:
            print "projPath 不存在!"
            return False

    def run(self, projPath):

        if self.__loadProject(projPath):
            pass

    def getTargetNames(self, currentProjectPath):

        targets = []

        pbxProjHelper = PBXProjectHelper("%s/project.pbxproj" % currentProjectPath)
        helperList = dir(pbxProjHelper)
        if "project" not in helperList:
            print "pbxproj 解析失败"

            param = json.dumps({"targets": targets})
            return param

        # 拿到targets列表
        pbxTargets = pbxProjHelper.project.targets

        for index in range(len(pbxTargets)):
            print index
            pbxTarget = pbxTargets[index]
            targetName = pbxTarget.getName()

            infoPlistPath = pbxTarget.getBuildSetting("Debug", "INFOPLIST_FILE")
            targets.append({"targetName" : targetName, "infoPlistPath": infoPlistPath})

        #已修改成targets，支持多个target
        param = json.dumps({"targets": targets})

        return param

    # 检查配置文件是否存在
    # @selectedRespository 库信息
    def __checkConfigFileIsExists(self, selectedRespository):
        configPath = selectedRespository["configPath"]

        fileType = configPath.split(".")[-1]

        isExists = False
        if fileType == "mobpods":
            isExists = True
        return isExists

    # TODO 检查库是否已经导入，已经导入返回 True
    def __checkLibsIsExists(self, selectedRespository):

        try:

            print "开始检查"
            print selectedRespository

            projectPath = selectedRespository["currentProjectPath"]
            target = selectedRespository["target"]

            #
            projDbPath = os.path.dirname(projectPath) + "/__MobTool/mobpods.db"

            # if os.path.exists(projDbPath):

            MobPodsSQLHelper().connect(projDbPath)

            # Todo sql 获取Repositories里对应target的对应库信息
            projFetchOneSql = "SELECT * FROM %s WHERE respositoryName = %s AND target = %s" % ("\"Project\"", "\"" + selectedRespository["respositoryName"] + "\"", "\"" + target + "\"")
            print "检查库是否导入，SQL=" + str(projFetchOneSql)

            projFetchOneData = 1
            # projSqlHelper.fetchOne(projFetchOneSql, projFetchOneData)
            projDbResult = MobPodsSQLHelper().fetchAll(projFetchOneSql)
            print "检查库是否导入，projDbResult=" + str(projDbResult)

            if len(projDbResult) > 0:

                return True

            else:

                return False

        except Exception, e:

            return False

    # 导入库
    def importLibs(self, selectedRespository, dependencies = []):

        try:
            manualImportedLibs = selectedRespository["manualImportedLibs"]

            respositoryName = selectedRespository["respositoryName"]

            # 检查是否已经导入存在
            if manualImportedLibs and respositoryName in manualImportedLibs:
                return json.dumps({"success": "yes", "msg": "Already import."})

            projectPath = selectedRespository["currentProjectPath"]
            projPath = os.path.dirname(projectPath)

            MobPodsSQLHelper().connect("%s/__MobTool/mobpods.db" % projPath)
            # 初始化记录导库情况的数据库
            MobPodsSQLHelper().createTable(
                "CREATE TABLE IF NOT EXISTS 'Project' ('id' TEXT, 'respositoryName' TEXT, 'target' TEXT, 'localVersion' TEXT, 'dependency' TEXT)")
            # 将原工程的libs保存到一个新的数据库里
            MobPodsSQLHelper().createTable("CREATE TABLE IF NOT EXISTS 'SysLibs' ('name' TEXT, 'libs' TEXT)")

            configPath = selectedRespository["configPath"]


            repositoryPath = selectedRespository["localPath"]

            isExists = self.__checkConfigFileIsExists(selectedRespository)

            if isExists:
                # 有配置文件
                fileManager = MobPodsFileManager(projPath, projectPath, selectedRespository, self.target)

                fileManager.copyFilesToProject(configPath, repositoryPath,
                                               projPath + "/__MobTool/" + selectedRespository["respositoryName"])
                # 写入 pbxProject 文件，导入框架
                fileManager.importLibrarysByProjectPath(projPath, selectedRespository)
            else:
                # 没有配置文件
                return json.dumps({"success": "no", "msg": "no config file."})

            print "已导入~~~~~~~~~~~~~~~~~~~~~~~~"
            print selectedRespository["respositoryName"]
            # 保存导入记录

            # Todo sql 将库信息导入project
            dependencyNames = []
            for name in dependencies:
                dependencyNames.append(name)

            dependencyStr = ','.join(dependencyNames)
            if os.path.exists(configPath):

                # 检查数据库中是否有这个id
                selectSql = "SELECT id FROM Project WHERE id = %s AND target = %s" %(selectedRespository["id"], "\'" + str(self.target) + "\'")
                results = MobPodsSQLHelper().fetchAll(selectSql)

                if len(results) > 0:
                    deleteSql = "DELETE FROM Project WHERE id = %s AND target = %s" %(selectedRespository["id"], "\'" + str(self.target) + "\'")
                    MobPodsSQLHelper().delete(deleteSql)

                # for result in results:
                #     print result[0]

                insertSql = "INSERT INTO 'Project' (id, respositoryName, localVersion, target , dependency) VALUES (?, ?, ?, ?, ?)"
                insertData = [
                    (
                        selectedRespository["id"],
                        selectedRespository["respositoryName"],
                        selectedRespository["localVersion"],
                        selectedRespository["target"],
                        dependencyStr
                    )
                ]
                MobPodsSQLHelper().insert(insertSql, insertData)

                # selectSql = "SELECT id FROM Project"
                # resultSelect = MobPodsSQLHelper().fetchAll(selectSql)

                return json.dumps({"success": "yes", "msg": "import success."})

            else:
                return json.dumps({"success": "no", "msg": "config文件不存在."})

        except Exception, e:
            print "importLibs func exception :" + str(e)
            return json.dumps({"success": "no", "msg": str(e)})


    # 删除库
    def __deleteLibs(self, selectedRespository):

        try:
            projectPath = selectedRespository["currentProjectPath"]
            projDbPath = os.path.dirname(projectPath) + "/__MobTool/mobpods.db"
            MobPodsSQLHelper().connect(projDbPath)

            # 查找数据库里，是否有多个dependency
            dependencies = []
            if os.path.exists(projDbPath):
                selectTableSql = "SELECT count(*) FROM sqlite_master WHERE type=\"table\" AND name = \"Project\""
                resultTable = MobPodsSQLHelper().fetchAll(selectTableSql)
                print(resultTable[0][0])
                if resultTable[0][0] > 0:
                    fetchSql = "SELECT dependency FROM Project"
                    dependencies = MobPodsSQLHelper().fetchAll(fetchSql)

            flag = 0
            for dependencyName in dependencies:

                if selectedRespository["respositoryName"] in dependencyName[0]:
                    flag+=1

            if 'delete' in selectedRespository and selectedRespository["delete"] == "yes":
                print("删除删除删除~~~~~~~~~~~~~~~~")
                print(selectedRespository["respositoryName"])
                pass
            elif flag >= 1:
                print("无需删除无需~~~~~~~~~~~~~~~~")
                print(selectedRespository["respositoryName"])
                print(selectedRespository)
                print flag
                return json.dumps({"success": "yes", "msg": str(selectedRespository["respositoryName"]) + " no need to delete."})

            projectPath = selectedRespository["currentProjectPath"]

            projPath = os.path.dirname(projectPath)

            configPath = selectedRespository["configPath"]
            fileManager = MobPodsFileManager(projPath, projectPath, selectedRespository)

            # 删除三方库
            res = fileManager.removeLibrarys(configPath)

            return res

        except Exception, e:
            return json.dumps({"success": "no", "msg": str(e)})

    # 更新按钮点击
    def updateBtnDidClicked(self, selectedRespository):

        if selectedRespository:

            # 检查库是否已经导入
            if not self.__checkLibsIsExists(selectedRespository):
                print "warning: 该框架尚未导入,请先导入."
                return True

            else:
                try:

                    lastRespository = {  "id":selectedRespository["id"],
                                         "configPath":selectedRespository["lastConfigPath"],
                                         "currentProjectPath":selectedRespository["currentProjectPath"],
                                         "respositoryName":selectedRespository["respositoryName"],
                                         "localPath":selectedRespository["lastLocalPath"],
                                         "target":selectedRespository["target"],
                                         "localVersion":selectedRespository["localVersion"]
                                        }

                    strResult = self.__deleteLibs(lastRespository)
                    resultDel = json.loads(strResult)


                    if resultDel["success"] == "yes":

                        strAdd = self.addBtnDidClicked(selectedRespository)

                        resultAdd = json.loads(strAdd)

                        if resultAdd["success"] == "yes":

                            print "更新的添加部分完成了"

                            return json.dumps({"success": "yes", "msg": "更新完成."})

                        else:

                            return json.dumps({"success": "no", "msg": "更新失败,添加库异常."})
                    else:

                        return json.dumps({"success": "no", "msg": "更新失败,删除库异常."})

                except Exception, e:

                    return json.dumps({"success": "no", "msg": str(e)})


    # 添加按钮点击
    def addBtnDidClicked(self, selectedRespository):

        self.target = selectedRespository["target"]

        dependencies = []
        if selectedRespository["dependency"] == "null":
            print "不存在 dependcies"
            dependencies = []
        else:
            print "存在 dependencies"
            dependencies.extend(selectedRespository["dependency"])

        return self.importLibs(selectedRespository, dependencies)

    # 删除按钮点击
    def deleteBtnDidClicked(self, selectedRespository):

        return self.__deleteLibs(selectedRespository)

    # 获取已经导入的库的列表
    # @projectPath 工程路径
    def getExistsImportLibs(self, selectedRespository):
        projectPath = selectedRespository["currentProjectPath"]
        target = selectedRespository["target"]

        projDbPath = os.path.dirname(projectPath) + "/__MobTool/mobpods.db"

        libsList = []

        if not os.path.exists(projDbPath):
            return json.dumps(libsList)

        MobPodsSQLHelper().connect(projDbPath)

        MobPodsSQLHelper().createTable(
            "CREATE TABLE IF NOT EXISTS 'Project' ('id' TEXT, 'respositoryName' TEXT, 'target' TEXT, 'localVersion' TEXT, 'dependency' TEXT)")
        # 将原工程的libs保存到一个新的数据库里
        MobPodsSQLHelper().createTable("CREATE TABLE IF NOT EXISTS 'SysLibs' ('name' TEXT, 'libs' TEXT)")

        # Todo sql 获取project对应Target的所有库信息
        fetchAllSql = "SELECT respositoryName FROM 'Project' WHERE target = %s" % ("\'" + target + "\'")
        importLibs = MobPodsSQLHelper().fetchAll(fetchAllSql)

        if len(importLibs) > 0:
            for name in importLibs:
                libsList.append(name[0])
        return json.dumps(libsList)

    def getImportedLibsId(self, selectedRespository):

        projectPath = selectedRespository["currentProjectPath"]
        target = selectedRespository["target"]

        projDbPath = os.path.dirname(projectPath) + "/__MobTool/mobpods.db"

        libsList = []

        if not os.path.exists(projDbPath):
            return json.dumps(libsList)

        MobPodsSQLHelper().connect(projDbPath)

        MobPodsSQLHelper().createTable(
            "CREATE TABLE IF NOT EXISTS 'Project' ('id' TEXT, 'respositoryName' TEXT, 'target' TEXT, 'localVersion' TEXT, 'dependency' TEXT)")
        # 将原工程的libs保存到一个新的数据库里
        MobPodsSQLHelper().createTable("CREATE TABLE IF NOT EXISTS 'SysLibs' ('name' TEXT, 'libs' TEXT)")

        # Todo sql 获取project对应Target的所有库信息
        fetchAllSql = "SELECT id FROM 'Project' WHERE target = %s" % ("\'" + target + "\'")
        importLibs = MobPodsSQLHelper().fetchAll(fetchAllSql)

        if len(importLibs) > 0:
            for name in importLibs:
                libsList.append(name[0])

        return json.dumps(libsList)

    def getOtherImportedLibList(self, selectedRespository):

        projectPath = selectedRespository["currentProjectPath"]
        compareLibs = selectedRespository["compareLibs"]

        libsList = []

        pbxProjHelper = PBXProjectHelper("%s/project.pbxproj" % projectPath)

        if compareLibs:
            for index in range(len(compareLibs)):
                resultGroup = pbxProjHelper.project.mainGroup.getChild(compareLibs[index], True)
                if resultGroup:
                    libsList.append(compareLibs[index])

        libPaths = []

        targetIndex = 0

        for index in xrange(0, len(pbxProjHelper.project.targets)):
            target = pbxProjHelper.project.targets[index]
            targetName = target.getName()
            if targetName == selectedRespository["target"]:
                targetIndex = index

        pbxTarget = pbxProjHelper.project.targets[targetIndex]
        buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

        frameworkPaths = buildSettingHelper.getFrameworkSearchPaths()

        if frameworkPaths and isinstance(frameworkPaths, list):
            for index in range(len(frameworkPaths)):
                for tag in range(len(libsList)):
                    if libsList[tag] in frameworkPaths[index]:
                        libPaths.append({libsList[tag] : frameworkPaths[index]})
        elif frameworkPaths and isinstance(frameworkPaths, str):
            for tag in range(len(libsList)):
                if libsList[tag] in frameworkPaths:
                    libPaths.append({libsList[tag]: frameworkPaths})

        return json.dumps({"libsList" : libsList, "libPaths": libPaths})

    def deleteManualImportedLib(self, selectedRespository):

        print("deleteManualImportedLib~~~~~~")

        projectPath = selectedRespository["currentProjectPath"]

        projPath = os.path.dirname(projectPath)

        fileManager = MobPodsFileManager(projPath, projectPath, selectedRespository)

        absolutePath = selectedRespository["absolutePath"]
        baseGroup = selectedRespository["baseGroup"]
        searchPath = selectedRespository["searchPath"]

        # 删除三方库
        res = fileManager.removeManualLib(absolutePath, baseGroup, searchPath)

        return res

    def getLibVersion(self, selectedRespository):

        projectPath = selectedRespository["currentProjectPath"]
        target = selectedRespository["target"]
        idStr = selectedRespository["id"]

        projDbPath = os.path.dirname(projectPath) + "/__MobTool/mobpods.db"

        libVer = ""

        if not os.path.exists(projDbPath):
            return libVer

        MobPodsSQLHelper().connect(projDbPath)

        MobPodsSQLHelper().createTable(
            "CREATE TABLE IF NOT EXISTS 'Project' ('id' TEXT, 'respositoryName' TEXT, 'target' TEXT, 'localVersion' TEXT, 'dependency' TEXT)")
        # 将原工程的libs保存到一个新的数据库里
        MobPodsSQLHelper().createTable("CREATE TABLE IF NOT EXISTS 'SysLibs' ('name' TEXT, 'libs' TEXT)")

        # Todo sql 获取project对应Target的所有库信息
        fetchAllSql = "SELECT localVersion FROM 'Project' WHERE target = %s AND id = %s" % ("\'" + target + "\'", "\'" + idStr + "\'")
        libVersions = MobPodsSQLHelper().fetchAll(fetchAllSql)

        for index in range(len(libVersions)):
            libVer = libVersions[index][0]

        return json.dumps({"version" : libVer})


# 添加按钮点击事件
# @data 点击的库的信息
def ocAddBtnDidClicked(data):

    pods = MobPods()
    return pods.addBtnDidClicked(json.loads(data))

def ocDeleteBtnDidClicked(data):

    pods = MobPods()
    return pods.deleteBtnDidClicked(json.loads(data))

def ocUpdateBtnDidClicked(data):

    pods = MobPods()
    return pods.updateBtnDidClicked(json.loads(data))


def ocGetTargetNames(data):

    pods = MobPods()
    return pods.getTargetNames(data)

# 获取工程里面已经导入的库。
def ocViewDidLoadCompleted(data):
    pods = MobPods()
    return pods.getExistsImportLibs(json.loads(data))

def ocGetLibsId(data):
    pods = MobPods()
    return pods.getImportedLibsId(json.loads(data))

def ocGetOtherImportedLibList(data):
    pods = MobPods()
    return pods.getOtherImportedLibList(json.loads(data))

def ocDeleteManualImportedLib(data):
    pods = MobPods()
    return pods.deleteManualImportedLib(json.loads(data))

def ocGetLibVersion(data):
    pods = MobPods()
    return pods.getLibVersion(json.loads(data))

