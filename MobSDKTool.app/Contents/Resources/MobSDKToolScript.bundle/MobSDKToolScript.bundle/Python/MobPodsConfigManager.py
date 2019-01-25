# encoding: utf-8

import os
import sys
import json
import codecs

reload(sys)
sys.setdefaultencoding('utf-8')

class MobPodsConfigManager(object):
    """docstring for MobPodsConfigManager"""
    def __init__(self, configPath):
        super(MobPodsConfigManager, self).__init__()
        self.configPath = configPath
        
        # 所有的系统依赖库列表
        self.libs = []
        
        # 所有要添加的文件
        self.add = []
        
        # 编译配置文件
        self.build = []
        
        # 添加的子工程
        self.addSubproject = {}

        # 第三方依赖库
        self.dependency = []

        # setting 配置
        self.settings = []
        
        self.identifier = ""


        if os.path.exists(self.configPath) :

            fo = codecs.open(self.configPath, 'r', 'utf-8')
            
            # fo = open(self.configPath, "r")
                
            string = fo.read()

            self.__parseJsonString(string)
            
            fo.close()
    
        else :
            print self.configPath
            print "无效的配置文件路径"
    
    def __parseJsonString(self, jsonString):

        dictionary = json.loads(jsonString)

        if dictionary:
            if dictionary.has_key("id"):
                identifier = dictionary["id"]
                if identifier:
                    self.__idHandler(identifier)
            
            if dictionary.has_key("install"):
                install = dictionary["install"]
                if install:
                    self.__installHandler(install)
            
            if dictionary.has_key("config"):
                config = dictionary["config"]
                if config:
                    self.__configHandler(config)
    
            if dictionary.has_key("user_config"):
                userConfig = dictionary["user_config"]
                if userConfig:
                    self.__userConfigHandler(userConfig)
        else:
            print "dictionary 为空"
    
    def __idHandler(self, identifier):
        self.identifier = identifier
        pass
        
    def __installHandler(self, install):
        if install.has_key("build"):
            self.build = install["build"]
            
        if install.has_key("copy_files"):
            copyFiles = install["copy_files"]
    
    def __configHandler(self, config):
        if config.has_key("libs"):
            self.libs = config["libs"]
            
        if config.has_key("add"):
            self.add = config["add"]
        
        if config.has_key("add_subproject"):
            self.addSubproject = config["add_subproject"]

        if config.has_key("dependency"):
            self.dependency = config["dependency"]

        if config.has_key("settings"):
            self.settings = config["settings"]

    def __userConfigHandler(self, userConfig):
        # 暂时不记录userConfig信息
        pass

# python MobPodsConfigManager.py /Users/admin/Desktop/GitOSC/Python-MobPods/__MobPods/config.mobpods
# if __name__ == '__main__':
# 	argv = sys.argv

# 	if len(argv) > 1 :
# 		configPath = argv[1]
# 		print MobPodsConfigManager(configPath)
