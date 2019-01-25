#!/usr/bin/env python
# encoding: utf-8

import PBXProjectHelper
from PBXProjectHelper import *

class MobPodsBuildSettingHelper(object):

    def __init__(self, pbxTarget):
        super(MobPodsBuildSettingHelper, self).__init__()

        self.pbxTarget = pbxTarget


    def addFrameworkSearchPaths(self, path):

        for buildConfig in self.pbxTarget.buildConfigurationList.buildConfigurations:
            buildConfig.addFrameworkSearchPath(path)

    def addLibrarySearchPath(self, path):
        for buildConfig in self.pbxTarget.buildConfigurationList.buildConfigurations:
            buildConfig.addLibrarySearchPath(path)

    def addOtherLinkerFlag(self, path):

        for buildConfig in self.pbxTarget.buildConfigurationList.buildConfigurations:
            buildConfig.addOtherLinkerFlag(path)

    def setBitCode(self, value):

        for buildConfig in self.pbxTarget.buildConfigurationList.buildConfigurations:
            buildConfig.setBitCode(value)

    def removeFrameworkSearchPaths(self, path):

        for buildConfig in self.pbxTarget.buildConfigurationList.buildConfigurations:
            buildConfig.removeFrameworkSearchPath(path)

    def removeLibrarySearchPath(self, path):
        for buildConfig in self.pbxTarget.buildConfigurationList.buildConfigurations:
            buildConfig.removeLibrarySearchPath(path)

    def getFrameworkSearchPaths(self):
        return self.pbxTarget.buildConfigurationList.buildConfigurations[0].getFrameworkSearchPaths()