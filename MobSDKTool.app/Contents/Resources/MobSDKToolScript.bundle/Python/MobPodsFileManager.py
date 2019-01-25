#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import shutil
import unicodedata
import re
import PBXProjectHelper
from MobPodsConfigManager import *
from PBXProjectHelper import *
from MobPodsSQLHelper import *
from MobPodsBuildSettingHelper import *

reload(sys)

sys.setdefaultencoding('utf8')

class MobPodsFileManager(object):
    """docstring for MobPodsFileManager"""

    def __init__(self, projectPath, xcodeprojPath, selectedRespository, target=None):
        super(MobPodsFileManager, self).__init__()

        print "init File Manager"

        print "over"

        self.projectPath = projectPath

        self.repositoryPath = selectedRespository["localPath"]

        self.targetName = selectedRespository["target"]

        print(self.targetName.encode('utf8'))

        self.filePathInfo = []

        projectName = os.path.basename(self.projectPath)

        # project.pbxproj 文件路径
        pbxPath = xcodeprojPath + "/project.pbxproj"

        print pbxPath.encode('utf8')

        # 初始化PBXProject
        self.pbxProjHelper = PBXProjectHelper(pbxPath)

        dbPath = "%s/__MobTool/mobpods.db" % os.path.dirname(projectPath + "/" + projectName)

        if os.path.exists(dbPath):
            MobPodsSQLHelper().connect(dbPath)

            selectTableSql = "SELECT count(*) FROM sqlite_master WHERE type=\"table\" AND name = \"SysLibs\""
            resultTable = MobPodsSQLHelper().fetchAll(selectTableSql)
            if resultTable[0][0] > 0:
                # 判断SysLibs里是否有name 为 originalLibs，没有就设置下值
                originalLibs = MobPodsSQLHelper().fetchAll("SELECT * FROM SysLibs WHERE name = 'original'")
                if not originalLibs:
                    frameworkGroup = self.pbxProjHelper.project.mainGroup.find("/Frameworks")
                    print "查看下frameworks下的libs"
                    items = []
                    if frameworkGroup:
                        for item in frameworkGroup.children:
                            if item.getName():
                                items.append(item.getName())
                    itemsStr = ','.join(items)
                    insertSql = "INSERT INTO 'SysLibs' (name, libs) VALUES (?, ?)"
                    insertData = [
                        (
                            'original',
                            itemsStr
                        )
                    ]
                    print "导入SysLibs完成记录的数据: " + str(insertData)
                    MobPodsSQLHelper().insert(insertSql, insertData)


        self.targetIndex = 0
        self.repositoryName = selectedRespository["respositoryName"]
        self.baseGroup = "MobTool"

        # 获取name和version的组合
        self.nameVersion = selectedRespository["respositoryName"]
        if selectedRespository.has_key("remoteVersion"):
            self.nameVersion = self.nameVersion + "_" + selectedRespository["remoteVersion"]

        for index in xrange(0, len(self.pbxProjHelper.project.targets)):
            target = self.pbxProjHelper.project.targets[index]
            targetName = target.getName()
            if targetName == self.targetName:
                self.targetIndex = index



    # 检查配置文件验证本地文件
    # @configPath 配置文件路径
    # @localFilePath 本地文件路径
    def checkingConfigToVerifyLocalFile(self, configPath, localFilePath):

        result = {"warning": [], "info": [], "error": ""}

        if os.path.exists(configPath) and os.path.exists(localFilePath):

            configManager = MobPodsConfigManager(configPath)

            if len(configManager.add) > 0:

                for path in configManager.add:

                    # 本地文件路径 + 配置文件路径
                    repositoryFilePath = localFilePath + "/" + path

                    # 查看是否存在该路径
                    if os.path.exists(repositoryFilePath):
                        pass
                    # print "path : %s " % repositoryFilePath
                    else:
                        # print "no path : %s" % repositoryFilePath
                        warning = "path :%s %s" % (repositoryFilePath, "配置有误.".decode('utf-8'))

                        fileType = os.path.basename(path).split(".")[-1]

                        if fileType == "framework":
                            result["warning"].append(warning)

                        elif fileType == "bundle":
                            result["info"].append(warning)

                        elif fileType == "a":
                            result["warning"].append(warning)

                        elif fileType == "h" or fileType == "m" or fileType == "{h,m}" or fileType == "swift":

                            if not os.path.exists(os.path.dirname(repositoryFilePath)):
                                result["warning"].append(warning)

                        else:
                            pass

            else:
                print "配置文件 add 字段为空."
                result["error"] = "add is null"

        else:
            print "配置文件路径或者本地文件路径不存在."
            result["error"] = "configPath or localFilePath is null"

        return result

    # 检查配置里面是否有 isBuild 参数，查看是否需要编译 framework 或 .a
    # @configPath 配置文件路径
    def checkingConfigIsBuild(self, configPath):

        result = False

        if os.path.exists(configPath):

            configManager = MobPodsConfigManager(configPath)

            build = configManager.build

            if build.has_key("is_build") and build["is_build"]:

                if build["is_build"] == "Yes" or build["is_build"] == "YES":
                    result = True
                else:
                    print "is_build 字段设置不正确."

            else:
                print "is_build 字段不存在."

        else:
            print "配置文件路径不存在."

        return result

    # 检查配置里面是否有 依赖其它库文件
    # @configPath 配置文件路径
    def checkingConfigIsDependency(self, configPath):
        print " " + str(configPath)
        result = []

        if os.path.exists(configPath):

            configManager = MobPodsConfigManager(configPath)

            dependency = configManager.dependency
            print "aaabbbccc：" + str(configManager.dependency)
            if len(dependency) > 0:
                print "依赖的框架：" + str(dependency)
            else:
                print "dependency 为空."

            return dependency

        else:
            print "依赖库配置文件路径不存在."

        return result

    def copyFilesToProject(self, configPath, localPath, dstPath):

        if os.path.exists(configPath):
            configManager = MobPodsConfigManager(configPath)

            if configManager.add:
                for addFiles in configManager.add:
                    srcPath = localPath + "/" + addFiles
                    if os.path.dirname(addFiles):
                        endPath = dstPath + "/" + os.path.dirname(addFiles)
                    else:
                        endPath = dstPath
                    self.copySrcFilesToDstPath(srcPath,endPath)


    # copy 源文件夹到目标文件夹
    # @srcPath 源文件路径
    # @dstPath 目标路径
    def copySrcFilesToDstPath(self, srcPath, dstPath):

        if os.path.exists(srcPath):

            srcBasename = os.path.basename(srcPath)

            if not os.path.exists(dstPath):
                os.makedirs(dstPath)

            dirs = os.listdir(dstPath)

            dstFilesPath = dstPath + "/" + srcBasename

            for fileName in dirs:

                if fileName is srcBasename:

                    if os.path.isdir(dstFilesPath):

                        # 如果已经存在该目录，先删除掉
                        shutil.rmtree(dstFilesPath)
                    else:
                        # 如果已经存在该文件，先删除掉
                        os.remove(dstFilesPath)

            if os.path.isdir(srcPath):

                if os.path.exists(dstFilesPath):
                    shutil.rmtree(dstFilesPath)

                # 拷贝源目录到目标目录
                shutil.copytree(srcPath, dstFilesPath)
            else:
                # 拷贝源文件到目标目录
                shutil.copy(srcPath, dstFilesPath)

        elif "*" in srcPath:
            #简单拷贝
            str = srcPath.split("/*", 1)[0]

            endstr = os.path.dirname(dstPath)

            self.copySrcFilesToDstPath(str, endstr)
        else:
            print "srcPath 或 dstPath 路径不存在 ！"

    # todo 导入第三方库，并写到 PBXProject 文件
    # @projectPath 工程路径
    # @localRespository 局部仓库库信息
    def importLibrarysByProjectPath(self, projectPath, localRespository):
        if os.path.exists(projectPath):

            try:

                configPath = localRespository["configPath"]

                # 根据配置文件创建一个configManager，相当于一个model，解析了配置文件中所有字段并保存在其属性中
                configManager = MobPodsConfigManager(configPath)

                # 1、libs 导入的系统依赖库列表
                if configManager.libs:
                    # todo 添加数据库记录 name为id
                    configLibs = []
                    for name in configManager.libs:
                        configLibs.append(name)


                    configLibsStr = ','.join(configLibs)

                    projectName = os.path.basename(projectPath)
                    MobPodsSQLHelper().connect("%s/__MobTool/mobpods.db" % os.path.dirname(projectPath + "/" + projectName))

                    # 检查数据库中是否有这个id
                    selectSql = "SELECT name FROM SysLibs WHERE name = %s" % (configManager.identifier)

                    results = MobPodsSQLHelper().fetchAll(selectSql)

                    if len(results) > 0:
                        deleteSql = "DELETE FROM SysLibs WHERE name = %s" % (configManager.identifier)
                        MobPodsSQLHelper().delete(deleteSql)

                    insertSql = "INSERT INTO 'SysLibs' (name, libs) VALUES (?, ?)"
                    insertData = [
                        (
                            configManager.identifier,
                            configLibsStr
                        )
                    ]
                    MobPodsSQLHelper().insert(insertSql, insertData)

                    self.__importLibsByConfig(configManager)

                # 2、add 导入其它文件
                if configManager.add:
                    self.__importAddByConfig(configManager, localRespository)

                # 3、添加编译配置
                if configManager.build:
                  self.__addBuildConfig(configManager)

                # 4、settings配置(这里使用了之前build的代码《》)
                # if configManager.settings:
                #     self.__addBuildConfig(configManager)

                # 5、添加子工程
                if configManager.addSubproject:
                    self.__importSubProjectByConfig(configManager, localRespository)

                # 6、依赖其它库
                if configManager.dependency:

                    # 其他依赖库未作处理
                    pass

                # 保存pbxproject
                self.pbxProjHelper.save()


            except Exception, e:
                print "导入第三方库异常：" + str(e)

        else:
            print "工程路径不存在 ！"
            return "工程路径不存在 ！"

    # todo 导入系统库
    # @config 配置文件对象
    def __importLibsByConfig(self, config):
        try:
            group = self.__getGroupOfFrameWork()

            for libFileName in config.libs:

                libFileSuffix = libFileName.split(".")[-1]

                if libFileSuffix == "framework":
                    group.addSystemFramework(libFileName, self.pbxProjHelper.project.targets[self.targetIndex])

                elif libFileSuffix == "dylib" or libFileSuffix == "tbd":
                    group.addSystemDylib(libFileName, self.pbxProjHelper.project.targets[self.targetIndex])

        except Exception, e:
            print str(e)

    # todo 导入 add 字段文件，framework、bundle、.a 、h 、{h,m} 等文件
    # @config 配置文件对象
    def __importAddByConfig(self, config, localRespository):
        tempAdd = []
        tempAdd.extend(config.add)
        print len(tempAdd)

        # 获取name和version的组合
        nameVersion = localRespository["respositoryName"]
        if localRespository.has_key("remoteVersion"):
            nameVersion = nameVersion + "_" + localRespository["remoteVersion"]

        # 修复 Config Add 的路径问题
        self.__fixConfigAddPath2(tempAdd, localRespository)

        # add 需要导入的其它框架
        for index in range(len(tempAdd)):

            addFilePath = tempAdd[index]

            # addFilePath = config.add[0]
            # addFilePath = unicode(addFilePath)

            fullFilePath = self.projectPath + "/__MobTool/" + nameVersion + "/" + addFilePath


            if not (os.path.exists(fullFilePath) or os.path.isdir(fullFilePath)):
                print "将要写入的文件路径不存在或不是字典"
                continue

            # 检查是否已添加
            # fileReference = self.pbxProjHelper.project.mainGroup.find("/%s/%s/%s/%s" % (self.baseGroup, self.targetName, self.repositoryName, addFilePath))
            # if fileReference:
            #     continue

            # 文件后缀
            addFileSuffix = addFilePath.split(".")[-1]
            # 父级目录
            parentPath = os.path.dirname(addFilePath)

            if not parentPath:
                parentPath = localRespository["respositoryName"]

            # 获取group
            fileGroup = self.__getGroup(parentPath)

            localFilePath = "__MobTool" + "/" + self.nameVersion + "/" + addFilePath

            if type(fileGroup) == PBXFileReference:
                continue

            fileGroup.addFile(localFilePath, self.pbxProjHelper.project.targets[self.targetIndex])

            if addFileSuffix == "framework":
                # 添加frameworkSearchPath
                self.__addframeworkPath(addFilePath)

            elif addFileSuffix == "a":
                #添加librarySearchPath
                self.__addLibraryPath(addFilePath)

        # self.pbxProjHelper.save()

    def __addLibraryPath(self, addFilePath):
        pbxTarget = self.pbxProjHelper.project.targets[self.targetIndex]

        buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

        filePathList = addFilePath.rsplit("/", 1)
        if len(filePathList) > 1:
            addLibraryPath = "/__MobTool/" + self.nameVersion + "/" + filePathList[0]
        else:
            addLibraryPath = "/__MobTool/" + self.nameVersion

        buildSettingHelper.addLibrarySearchPath("\"$(PROJECT_DIR)" + addLibraryPath + "\"")

    def __addframeworkPath(self, addFilePath):

        pbxTarget = self.pbxProjHelper.project.targets[self.targetIndex]

        buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

        filePathList = addFilePath.rsplit("/", 1)
        if len(filePathList) > 1:
            addSearchPath = "/__MobTool/" + self.nameVersion + "/" + filePathList[0]
        else:
            addSearchPath = "/__MobTool/" + self.nameVersion

        buildSettingHelper.addFrameworkSearchPaths("\"$(PROJECT_DIR)" + addSearchPath + "\"")

    def __removeFrameworkPath(self, removeFilePath):

        pbxTarget = self.pbxProjHelper.project.targets[self.targetIndex]

        buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

        filePathList = removeFilePath.rsplit("/", 1)
        if len(filePathList) > 1:
            removeSearchPath = "/__MobTool/" + self.nameVersion + "/" + filePathList[0]
        else:
            removeSearchPath = "/__MobTool/" + self.nameVersion

        buildSettingHelper.removeFrameworkSearchPaths("\"$(PROJECT_DIR)" + removeSearchPath + "\"")

    def __removeLibraryPath(self, removeFilePath):
        pbxTarget = self.pbxProjHelper.project.targets[self.targetIndex]

        buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

        filePathList = removeFilePath.rsplit("/", 1)
        if len(filePathList) > 1:
            removeLibraryPath = "/__MobTool/" + self.nameVersion + "/" + filePathList[0]
        else:
            removeLibraryPath = "/__MobTool/" + self.nameVersion

        buildSettingHelper.removeLibrarySearchPath("\"$(PROJECT_DIR)" + removeLibraryPath + "\"")

    # 修复 config add 中的路径
    def __fixConfigAddPath(self, config, localRespository):
        # 修改配置文件中的 add 路径中的问题
        tempAdd = []
        tempAdd.extend(config.add)
        # 获得的libpath诸如： u'MJRefresh/Base/MJRefreshAutoFooter.h'
        libPaths = []
        tempIndex = []

        # 获取name
        resName = localRespository["respositoryName"]

        # 获取flelPath
        projFilePath = self.projectPath + "/__MobTool/" + resName + "/"
        self.__parseDirByPath(projFilePath, projFilePath)


        fileArray = self.filePathInfo
        files = []

        for index in range(len(tempAdd)):
            tempIndex.append(index)

            addFilePath = tempAdd[index]

            addFilePath = addFilePath.replace("{", "(")
            addFilePath = addFilePath.replace("}", ")")
            addFilePath = addFilePath.replace(",", "|")
            addFilePath = addFilePath.replace("+", "\+")


            if os.path.isdir(projFilePath + addFilePath):
                if  addFilePath.endswith("/"):
                    addFilePath = addFilePath + ".*"
                else:
                    addFilePath = addFilePath + "/.*"

            elif "**/" in addFilePath:
                addFilePath = addFilePath.replace("**/", "")
            elif "**" in addFilePath:
                addFilePath = addFilePath.replace("**", ".*")
            elif "*." in addFilePath:
                addFilePath = addFilePath.replace("*.", ".*\.")

            for fileP in fileArray:

                # addFilePath = "25519.podspec"
                # addFilePath = addFilePath.encode('utf-8')\
                print "fileP " + fileP
                if "UIKit+AFNetworking" in fileP:
                    aaa = None
                matchs = re.match(addFilePath.decode('utf-8'), fileP)
                if matchs:
                    files = matchs.group()
                    libPaths.append(files)

            continue


        # 从后往前面删除已经匹配的路径
        tempIndex.reverse()
        for index in tempIndex:
            config.add.pop(index)
        # 添加匹配符号下面的所有路径
        config.add.extend(libPaths)

        # 移除相同路径的多余的
        config.add = list(set(config.add))

    def __fixConfigAddPath2(self, config, localRespository):
        # 修改配置文件中的 add 路径中的问题
        tempAdd = []
        tempAdd.extend(config)
        # 获得的libpath诸如： u'MJRefresh/Base/MJRefreshAutoFooter.h'
        libPaths = []
        tempIndex = []
        for index in range(len(tempAdd)):
            addFilePath = tempAdd[index]

            # 获取name和version的组合
            nameVersion = localRespository["respositoryName"]
            if localRespository.has_key("remoteVersion"):
                nameVersion = nameVersion + "_" + localRespository["remoteVersion"]

            # 获取flelPath
            projFilePath = self.projectPath + "/__MobTool/" + nameVersion + "/"

            # 检查路径中带有 ** 的
            if "**" in addFilePath:
                
                tempIndex.append(index)
                filePath = os.path.dirname(os.path.dirname(addFilePath))

                projFilePath = projFilePath + filePath

                self.__parseDir(projFilePath)
                for info in self.filePathInfo:
                    if info["isDir"] == False:
                        absPath = info["absPath"]
                        libPath = (absPath.split('__MobTool/' + nameVersion + "/")).pop(1)

                        # 由于**类型的很有可能也是"*.{h,m}"类型，比如"Common/Source/**/*.{h,m}"
                        # 所以这里要进行判断
                        if "*.{h,m}" in addFilePath or "*.{h}" in addFilePath or "*.{m}" in addFilePath or "*.{c,h}" in addFilePath:
                            if libPath.endswith(".h") or libPath.endswith(".m") or libPath.endswith(".c"):
                                libPaths.append(libPath)

                        elif "*.framework" in addFilePath or "*.bundle" in addFilePath or "*.plist" in addFilePath or "*.h" in addFilePath or "*.m" in addFilePath or "*.swift" in addFilePath or "*.xib" in addFilePath:
                            if libPath.endswith(".framework") or libPath.endswith(".bundle") or libPath.endswith(
                                    ".plist") or libPath.endswith(".h") or libPath.endswith(".m") or libPath.endswith(
                                ".swift") or libPath.endswith(".xib"):
                                libPaths.append(libPath)

                        else:
                            libPaths.append(libPath)


            # 检查路径中以 /* 结尾的
            elif addFilePath.endswith("/*"):
                tempIndex.append(index)
                filePath = os.path.dirname(addFilePath)
                
                projFilePath = projFilePath + filePath
                
                self.__parseDir(projFilePath)


                for info in self.filePathInfo:
                    if info["isDir"] == False:
                        absPath = info["absPath"]
                        libPath = (absPath.split('__MobPods/' + nameVersion + "/")).pop(1)
                        libPaths.append(libPath)


            # 检查路径中以 *.{h,m} 开头的
            elif "*.{h,m}" in addFilePath or "*.{h}" in addFilePath or "*.{m}" in addFilePath or "*.{c,h}" in addFilePath:
                print "检查路径中以 *.{h,m} 开头的"
                tempIndex.append(index)

                parentPath = addFilePath.split("*.")[0]
                dicPath = projFilePath + parentPath
                dirs = os.listdir(dicPath)
                for libPath in dirs:
                    # 这里不管是{h,m}还是{h}还是{m}，都看做{h,m}操作，忽略存在h,m却只添加h或m的奇葩情况
                    if libPath.endswith(".h") or libPath.endswith(".m") or libPath.endswith(".c"):
                        libPaths.append(parentPath + libPath)

            # 检查路径中带有 *. 的
            elif "*." in addFilePath:

                if addFilePath.endswith("*.framework") or addFilePath.endswith("*.bundle") or addFilePath.endswith(
                        "*.plist") or addFilePath.endswith("*.h") or addFilePath.endswith(
                    "*.m") or addFilePath.endswith("*.swift") or addFilePath.endswith("*.a"):
                    tempIndex.append(index)

                    suffix = '.' + addFilePath.split("*.")[-1]
                    parentPath = addFilePath.split("*.")[0]
                    dicPath = projFilePath + parentPath
                    dirs = os.listdir(dicPath)

                    for libPath in dirs:
                        if libPath.endswith(suffix):
                            libPaths.append(parentPath + libPath)

            # 检查路径中只设置了根目录的
            elif len(addFilePath.split("/")) == 1:
                print "检查路径中只设置了根目录的"
                # if addFilePath.endswith("framework") or addFilePath.endswith("a") or addFilePath.endswith(
                #         "bundle") or addFilePath.startswith("*"):
                #     pass
                # else:
                #     tempIndex.append(index)
                #     projFilePath = projFilePath + addFilePath
                #     self.__parseDir(projFilePath)
                #     for info in self.filePathInfo:
                #         print "检查路径中只设置了根目录的22222"
                #         if info["isDir"] == False:
                #             tempIndex.remove(index)
                #             print "检查路径中只设置了根目录的33333"
                            # absPath = info["absPath"]
                            # libPath = (absPath.split('__MobPods/' + nameVersion + "/")).pop(1)
                            # print libPath
                            # libPaths.append(libPath)



            # 检查路径中是实际文件名的（用于MobPods）
            elif len(addFilePath.split(".")) == 2:

                if addFilePath.endswith("framework") or addFilePath.endswith("bundle"):
                    tempIndex.append(index)
                    filePath = os.path.basename(addFilePath)

                    projFilePath = projFilePath + addFilePath

                    info = self.__getFileInfo(projFilePath, isDir=False)
                    if info["isDir"] == False:
                        # absPath = info["absPath"]
                        # libPath = (absPath.split('__MobPods/')).pop(1)
                        libPaths.append(addFilePath)

                        # todo <待改进> 检查路径中是实际文件名的(用于SDKTool，到时候要把这个方法和上一个合并)
                        # elif len(addFilePath.split(".")) == 2:
                        #
                        # if addFilePath.endswith("framework") or addFilePath.endswith("bundle"):
                        #     tempIndex.append(index)
                        #     filePath = os.path.basename(addFilePath)
                        #     print "zzzzzz"
                        #
                        #     projFilePath = self.projectPath + "/__MobPods/" + localRespository[
                        #         "respositoryName"] + "/" + filePath
                        #
                        #     print str(projFilePath)
                        #
                        #     self.filePathInfo.append(self.__getFileInfo(projFilePath, isDir=False))
                        #
                        #     for info in self.filePathInfo:
                        #         if info["isDir"] == False:
                        #             absPath = info["absPath"]
                        #             libPath = (
                        #             absPath.split('__MobPods/' + localRespository["respositoryName"] + "/")).pop(1)
                        #             libPaths.append(libPath)

        # 从后往前面删除已经匹配的路径
        tempIndex.reverse()
        print tempIndex
        for index in tempIndex:
            config.pop(index)
        # 添加匹配符号下面的所有路径
        config.extend(libPaths)

        # 移除相同路径的多余的
        config = list(set(config))

    # 分析路径并解析
    def __parseDirByPath(self, filePath, parentPath):

        if os.path.isdir(filePath):
            dirs = os.listdir(filePath)
            os.chdir(filePath)

            for fileName in dirs:
                if os.path.isdir(fileName):
                    # print "fileName :" + fileName
                    if fileName.endswith("bundle") or fileName.endswith("framework") or fileName.endswith(
                            "a") or fileName.endswith("lproj") or fileName.endswith("strings"):
                        dic = self.__getFileInfo(fileName, isDir=False)
                        self.filePathInfo.append((dic["absPath"]).replace(parentPath, ""))
                    else:
                        self.__parseDirByPath(fileName, parentPath)
                else:
                    dic = self.__getFileInfo(fileName, isDir=False)
                    self.filePathInfo.append((dic["absPath"]).replace(parentPath, ""))

            os.chdir("../")


    # 分析路径并解析
    def __parseDir(self, target):
        if os.path.isdir(target):
            dirs = os.listdir(target)
            os.chdir(target)

            for fileName in dirs:
                if os.path.isdir(fileName):
                    # print "fileName :" + fileName
                    if fileName.endswith("bundle") or fileName.endswith("framework") or fileName.endswith(
                            "a") or fileName.endswith("lproj") or fileName.endswith("strings"):
                        self.filePathInfo.append(self.__getFileInfo(fileName, isDir=False))
                    else:
                        self.__parseDir(fileName)
                else:
                    self.filePathInfo.append(self.__getFileInfo(fileName, isDir=False))

            os.chdir("../")

    def __getFileInfo(self, fileName, isDir=False):

        suffix = 'dir'
        if not isDir:
            suffix = fileName.split(".")[-1]

        absPath = os.path.abspath(fileName)
        dirName = os.path.dirname(absPath)
        parentDir = os.path.basename(dirName)

        # print "开始了uuuuuuuuuuuuuuuuu"
        # print "absPath = " + absPath
        # print "dirName = " + dirName
        # print "parentDir = " + parentDir
        # print "完成了uuuuuuuuuuuuuuuuu"

        return dict(
            fileName=fileName,
            absPath=absPath,
            parentDir=parentDir,
            fileType=suffix,
            isDir=isDir
        )

    def removeManualLib(self, absolutePath, baseGroup, searchPath):

        targetGroup = self.pbxProjHelper.project.mainGroup.find(os.path.dirname(baseGroup))
        respositoryGroup = self.pbxProjHelper.project.mainGroup.find(baseGroup)

        if respositoryGroup:
            print("删除group~~~~~`")
            targetGroup.removeChild(respositoryGroup)
            #删除framework和phase
            pbxTarget = self.pbxProjHelper.project.targets[self.targetIndex]

            buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

            buildSettingHelper.removeFrameworkSearchPaths(searchPath)

            self.pbxProjHelper.save()

        if os.path.exists(absolutePath):
            print("删除文件~~~~")
            shutil.rmtree(absolutePath)
            return json.dumps({"success": "yes", "msg": "删除成功."})
        else:
            return json.dumps({"success": "no", "msg": "删除失败，文件不存在"})


    # 删除三方库
    def removeLibrarys(self, configPath):
        try:
            projDbPath = self.projectPath + "/__MobTool/mobpods.db"
            MobPodsSQLHelper().connect(projDbPath)
            MobPodsSQLHelper().createTable("CREATE TABLE IF NOT EXISTS 'SysLibs' ('name' TEXT, 'libs' TEXT)")
            MobPodsSQLHelper().createTable(
                "CREATE TABLE IF NOT EXISTS 'Project' ('id' TEXT, 'respositoryName' TEXT, 'target' TEXT, 'localVersion' TEXT, 'dependency' TEXT)")
            # 删除build settings 和 build phase中的配置
            configManager = MobPodsConfigManager(configPath)

            if configManager.libs:
                # 遍历original
                selectTableSql = "SELECT count(*) FROM sqlite_master WHERE type=\"table\" AND name = \"SysLibs\""
                resultTable = MobPodsSQLHelper().fetchAll(selectTableSql)
                originalLibs = []
                if resultTable[0][0] > 0:
                    originalLibs = MobPodsSQLHelper().fetchAll("SELECT libs FROM SysLibs WHERE name = 'original'")
                if originalLibs:

                    for lib in configManager.libs:

                        if lib not in list(originalLibs[0])[0]:

                            # 遍历所有的libs,如果lib的个数大于0,不删
                            flag = 0
                            selectTableSql = "SELECT count(*) FROM sqlite_master WHERE type=\"table\" AND name = \"SysLibs\""
                            resultTable = MobPodsSQLHelper().fetchAll(selectTableSql)
                            allLibs = []
                            if resultTable[0][0] > 0:
                                allLibs = MobPodsSQLHelper().fetchAll("SELECT libs FROM SysLibs WHERE name != '%s'" % (configManager.identifier))

                            for libs in allLibs:
                                existedLibs = list(libs)[0].split(',')

                                for existedLib in existedLibs:
                                    if lib == existedLib:
                                        flag += 1

                            if flag == 0:
                                self.__removeLibsByConfig(lib)

                    # 数据库中删掉id对应的libs
                    selectTableSql = "SELECT count(*) FROM sqlite_master WHERE type=\"table\" AND name = \"SysLibs\""
                    resultTable = MobPodsSQLHelper().fetchAll(selectTableSql)
                    if resultTable[0][0] > 0:
                        deleteSql = "DELETE FROM SysLibs WHERE name = '%s'" % (configManager.identifier)
                        MobPodsSQLHelper().delete(deleteSql)

            if configManager.add:
                # 根据配置里的add删掉__MOBTool下的文件
                # self.__removeAddFiles(configManager)

                self.__removeSearchPath(configManager)

            # sql 删除project里对应的库
            deleteSql = "DELETE FROM 'Project' WHERE target = %s AND id = %s " % (
                "\'" + self.targetName + "\'", "\'" + configManager.identifier + "\'")

            selectSql = "SELECT id FROM Project"
            resultSelect = MobPodsSQLHelper().fetchAll(selectSql)

            if resultSelect:
                for ids in resultSelect:
                    if configManager.identifier == list(ids)[0]:
                        # 如果Project数据库中没有数据，删掉__MOBTool文件夹和MOBTool文件夹
                        MobPodsSQLHelper().delete(deleteSql)

            if len(resultSelect) < 2:

                print "删掉__MOBTool文件夹和MOBTool文件夹"

                if os.path.exists(projDbPath):
                    deleteQ = "DELETE FROM Project"
                    MobPodsSQLHelper().delete(deleteQ)
                    deleteS = "DELETE FROM SysLibs"
                    MobPodsSQLHelper().delete(deleteS)
                    print("清空数据库")

                mobPodsGroup = self.pbxProjHelper.project.mainGroup.find("/%s" % self.baseGroup)
                if mobPodsGroup:
                    self.pbxProjHelper.project.mainGroup.removeChild(mobPodsGroup)

                frameworkGroup = self.pbxProjHelper.project.mainGroup.find("/Frameworks")
                if frameworkGroup:
                    if len(frameworkGroup.children) < 1:
                        self.pbxProjHelper.project.mainGroup.removeChild(frameworkGroup)

                filesDir = self.projectPath + "/__MobTool/"
                #projSqlHelper.closeAll()

                if os.path.isdir(filesDir):
                    shutil.rmtree(filesDir)

            targetGroup = self.__getGroupOfTarget()
            respositoryGroup = self.__getGroupOfRepository()

            # --
            if not respositoryGroup:
                self.pbxProjHelper.save()
                return json.dumps({"success": "yes", "msg": "lib not exist, no need to delete."})

            else:
                targetGroup.removeChild(respositoryGroup)
                self.pbxProjHelper.save()
                filesDir = self.projectPath + "/__MobTool/" + self.repositoryName
                if os.path.exists(filesDir):
                    shutil.rmtree(filesDir)


            return json.dumps({"success": "yes", "msg": "删除成功."})

        except Exception, e:
            return json.dumps({"success": "no", "msg": str(e)})


    def __removeAddFiles(self,config):

        dstPath = self.projectPath + "/__MobTool/" + self.repositoryName

        for addFiles in config.add:
            srcPath = self.repositoryPath + "/" + addFiles
            if os.path.dirname(addFiles):
                endPath = dstPath + "/" + os.path.dirname(addFiles)
            else:
                endPath = dstPath

            print "endPath"
            print addFiles
            print endPath


            srcBasename = os.path.basename(srcPath)

            if not os.path.exists(endPath):
                continue

            dirs = os.listdir(endPath)

            dstFilesPath = endPath + "/" + srcBasename

            print dstFilesPath

            for fileName in dirs:

                if fileName == srcBasename:

                    if os.path.isdir(dstFilesPath):
                        # 如果已经存在该目录，先删除掉
                        shutil.rmtree(dstFilesPath)
                    else:
                        # 如果已经存在该文件，先删除掉
                        os.remove(dstFilesPath)



    def __removeSearchPath(self, config):

        tempAdd = []
        tempAdd.extend(config.add)

        for index in range(len(tempAdd)):
            
            addFilePath = tempAdd[index]

            addFileSuffix = addFilePath.split(".")[-1]

            if addFileSuffix == "framework":

                self.__removeFrameworkPath(addFilePath)

                # self.pbxProjHelper.save()

            elif addFileSuffix == "a":
                self.__removeLibraryPath(addFilePath)

                # self.pbxProjHelper.save()


    def __removeLibsByConfig(self, lib):
        try:
            group = self.__getGroupOfFrameWork()

            libzFile = self.pbxProjHelper.project.mainGroup.find("/Frameworks/%s" % (lib))
            if libzFile:
                group.removeChild(libzFile)
                # self.pbxProjHelper.save()
            # for libFileName in config.libs:
            #     libzFile = self.pbxProjHelper.project.mainGroup.find("/Frameworks/%s" % (libFileName))
            #
            #     if libzFile:
            #         group.removeChild(libzFile)
            #         self.pbxProjHelper.save()

        except Exception, e:
            print str(e)

    # 添加并获取group
    # param filePath file父路径
    def __getGroup(self, filePath):
        # 判断是否有MobPods目录
        mobPodsGroup = self.pbxProjHelper.project.mainGroup.find("/%s" % self.baseGroup)
        if not mobPodsGroup:
            self.pbxProjHelper.project.mainGroup.addGroup("%s" % self.baseGroup)
            mobPodsGroup = self.pbxProjHelper.project.mainGroup.find("/%s" % self.baseGroup)

        # 判断是否有Target对应的目录
        targetGroup= self.pbxProjHelper.project.mainGroup.find("/%s/%s" % (self.baseGroup, self.targetName))
        if not targetGroup:
            mobPodsGroup.addGroup(self.targetName)
            targetGroup = self.pbxProjHelper.project.mainGroup.find("/%s/%s" % (self.baseGroup, self.targetName))

        # 判断是否存在对应的三方库目录
        respositoryGroup = self.pbxProjHelper.project.mainGroup.find("/%s/%s/%s" % (self.baseGroup, self.targetName, self.repositoryName))
        if not respositoryGroup:
            targetGroup.addGroup(self.repositoryName)
            respositoryGroup = self.pbxProjHelper.project.mainGroup.find("/%s/%s/%s" % (self.baseGroup, self.targetName, self.repositoryName))

        # 分割目录
        groupList = filePath.split("/")

        path = "/%s/%s/%s" % (self.baseGroup, self.targetName, self.repositoryName)
        fileGroup = respositoryGroup

        for index in xrange(0, len(groupList)):
            fileName = groupList[index]
            if index == 0 and fileName == self.repositoryName:
                continue

            else:
                path = path + "/" + fileName
                group = self.pbxProjHelper.project.mainGroup.find(path)
                if not group:
                    fileGroup.addGroup(fileName)
                    fileGroup = self.pbxProjHelper.project.mainGroup.find(path)
                else:
                    fileGroup = group

        return  fileGroup

    # 获取Frameworks文件夹的group，没有则创建并获取
    def __getGroupOfFrameWork(self):
        frameWorkGroup = self.pbxProjHelper.project.mainGroup.find("/Frameworks")
        if not frameWorkGroup:
            self.pbxProjHelper.project.mainGroup.addGroup("Frameworks")
            frameWorkGroup = self.pbxProjHelper.project.mainGroup.find("/Frameworks")

        return frameWorkGroup

    # 获取target所在的group
    # 获取不到返回None
    def __getGroupOfTarget(self):
        targetGroup = self.pbxProjHelper.project.mainGroup.find("/%s/%s" % (self.baseGroup, self.targetName))
        if not targetGroup:
            return None
        else:
            return targetGroup

    # 获取要删除的group
    # 获取不到返回None
    def __getGroupOfRepository(self):
        # /MobTool/TestSDKTool/SMSSDK
        respositoryGroup = self.pbxProjHelper.project.mainGroup.find("/%s/%s/%s" % (self.baseGroup, self.targetName, self.repositoryName))
        if not respositoryGroup:
            return None
        else:
            return respositoryGroup

    # 获取到Recovered References的group
    # 由于xcode9 删除时会自动加上这个group，要把它删除掉
    # def __removeRecoveredReferencesGroup(self):
    #     recoveredGroup = self.pbxProjHelper.project.mainGroup.find("/Recovered References")
    #     if recoveredGroup:
    #         self.pbxProjHelper.project.mainGroup.removeChild(recoveredGroup)
    #         self.pbxProjHelper.save()

    # 添加工程配置项
    # @config 配置文件对象
    def __addBuildConfig(self, config):

        # print "aaaaaa mobpodsFilemanger 445 " + str(self.pbxProjHelper.getBuildSettings(None, "Debug"))

        pbxTarget = self.pbxProjHelper.project.targets[self.targetIndex]
        buildSettingHelper = MobPodsBuildSettingHelper(pbxTarget)

        build = config.build
        # 获取工程 target
        # target = config.build["target"]
        # if not target:
        #     target = None
        #     print "no target key"


        # 添加 Other Link 标识
        if build.has_key("other_link"):
            if build["other_link"] is not None:
                key = "OTHER_LDFLAGS"
                buildSettingHelper.addOtherLinkerFlag(build["other_link"])

        else:
            pass

        # 添加 bitcode 标识
        if build.has_key("bitcode"):
            if build["bitcode"]:
                key = "ENABLE_BITCODE"
                buildSettingHelper.setBitCode(build["bitcode"])
        else:
            pass


