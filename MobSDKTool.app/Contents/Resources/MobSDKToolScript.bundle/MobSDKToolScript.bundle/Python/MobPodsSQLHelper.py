#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import sqlite3

class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

class MobPodsSQLHelper(Singleton):
	"""docstring for MobPodsSQLHelper"""
	def __init__(self):
		super(MobPodsSQLHelper, self).__init__()
		self.dbPath = None
        #
		# dbParentPath = os.path.dirname(dbPath)
        #
		# if not os.path.exists(dbParentPath):
        #
		# 	os.mkdir(dbParentPath)
        #
		# # 打开数据库连接
		# self.conn = sqlite3.connect(dbPath)
        #
		# # 使用 cursor() 方法执行 SQL 语句
		# self.cursor = self.conn.cursor()

	def __del__(self):
		self.cursor.close()
		self.conn.close()

	def connect(self, path):
		if not self.dbPath and path != self.dbPath:
			self.dbPath = path
			dbParentPath = os.path.dirname(path)
			if not os.path.exists(dbParentPath):
				os.mkdir(dbParentPath)

			# 打开数据库连接
			self.conn = sqlite3.connect(path)

			# 使用 cursor() 方法执行 SQL 语句
			self.cursor = self.conn.cursor()
		else:
			print('数据库已连接',self.dbPath)


	# 创建数据库表
	def createTable(self, sql):

		if sql is not None and sql != "":
			# 执行
			self.cursor.execute(sql)

			# 提交到数据库执行
			self.conn.commit()
		else:
			print('the [{}] is empty or equal None!'.format(sql))
		


	# 删除数据库表
	def dropTable(self, table):
		
		if table is not None and table != "":
			
			sql = "DROP TABLE IF EXISTS " + table

			self.cursor.execute(sql)

			self.conn.commit()

			print('删除数据库表[{}]成功!'.format(table))

		else:
			print('the [{}] is empty or equal None!'.format(sql))


	# 插入数据	
	def insert(self, sql, data):
		
		if sql is not None and sql != "":
			
			if data is not None:

				for d in data:
					self.cursor.execute(sql, d)

			self.conn.commit()
		else:
			print('the [{}] is empty or equal None!'.format(sql))


	# 更新数据
	def update(self, sql, data):

		if sql is not None and sql != '':

			if data is not None:

				for d in data:

					self.cursor.execute(sql, d)

			self.conn.commit()
		else:
			print('the [{}] is empty or equal None!'.format(sql)) 


	# 删除数据
	def delete(self, sql):
		
		if sql is not None and sql != "":

			self.cursor.execute(sql)

			self.conn.commit()

		else:

			print('the [{}] is empty or equal None!'.format(sql))

	# 查询所有数据
	def fetchAll(self, sql):
		
		if sql is not None and sql != "":

			self.cursor.execute(sql)

			result = self.cursor.fetchall()

			return result
			
		else:
			print('the [{}] is empty or equal None!'.format(sql))
			return None

	# 查询一条数据
	def fetchOne(self, sql, data):
		
		if sql is not None and sql != "":
			
			if data is not None:
				
				d = (data,)

				self.cursor.execute(sql, d)

				result = self.cursor.fetchall()

				if len(result) > 0:
					
					for e in range(len(result)):
						
						print(result[e])

				return result

			else:
				print('the [{}] equal None!'.format(data))
				return None

		else:
			print('the [{}] is empty or equal None!'.format(sql))
			return None

	# 判断表是否存在	 
	def tableIsExists(self, name):

		if name is not None and name != "":

			sql = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'" % name

			result = self.cursor.execute(sql)

			return result

		return False

	# 关闭数据库连接对象和游标对象
	def closeAll(self):
		
		if self.conn is not None:
			self.cursor.close()
			self.conn.close()
			pass



# def main():

# # 	# 初始化
# 	sqlHelper = MobPodsSQLHelper("/Users/admin/Desktop/GitOSC/Python-MobPods/Hello/__MobPods/mobpods.db")

# 	# # 创建表
# 	# createSql = "CREATE TABLE IF NOT EXISTS 'PbxHistoryRecord' ('id' integer, 'libraryName' varchar, 'guid' varchar, 'version' real)"
# 	# sqlHelper.createTable(createSql)

# 	# # 插入测试
# 	# insertSql = "INSERT INTO PbxHistoryRecord values (?, ?, ?, ?)"
# 	# insertData = [
# 	# 	(1, 'ShareSDK', '1234567890', 0.5),
# 	# 	(2, 'SMSSDK', '1234567890', 1.2),
# 	# 	(3, 'ShareREC', '1234567890', 2.0),
# 	# 	(4, 'MobApi', '1234567890', 3.5)
# 	# ]

# 	# sqlHelper.insert(insertSql, insertData)

# 	# # 更新测试
# 	# updateSql = "UPDATE PbxHistoryRecord SET libraryGuid = ? WHERE id = ?"
# 	# updateData = [
# 	# 	('9876543210', 2)
# 	# ]

# 	# sqlHelper.update(updateSql, updateData)

# 	# # 删除数据测试
# 	# deleteSql = "DELETE FROM PbxHistoryRecord WHERE libraryName = ? AND id = ?"
# 	# deleteData = [
# 	# 	('MobApi', 4)
# 	# ]

# 	# sqlHelper.delete(deleteSql, deleteData)

# 	# # 查询一条数据
# 	fetchOneSql = "SELECT * FROM %s WHERE rowId = ?" % "ShareSDK"
# 	fetchOneData = 1

# 	sqlHelper.fetchOne(fetchOneSql, fetchOneData)

# 	# 查询所有数据
# 	# fetchAllSql = "SELECT * FROM respository"
# 	# print sqlHelper.fetchAll(fetchAllSql)

# 	# 删除表
# 	# sqlHelper.dropTable('PbxHistoryRecord')

# if __name__ == '__main__':
# 	sys.exit(main())





