#!/usr/bin/python
# -*- coding: utf-8 -*-
#multiple.py

import re
import sys
import time
import chardet
import urllib2,httplib
import MySQLdb as mdb

reload(sys)
sys.setdefaultencoding( "utf-8" )


url_cmp = 'http://www.google.com.hk/search?q='
nextpage = '&start='
pagenumber = 0
re_data = re.compile(r'<h3 class="r"><a href="[\s\S]*?" target="_blank">([\s\S]*?)<cite.*?>([\s\S]*?)</cite>.*?<span.*?>([\s\S]*?)</li>',re.S)



def search(table_task, table_type, keyword,engines = ['google_hk','baidu','sousou'],page = 6):
	print engines
	while len(engines)!=0:
		set_params(table_task, table_type, keyword,engines[0])
		do_search(table_task, table_type, keyword,engines[0],page)
		print engines[0]
		del engines[0]

def set_params(table_task, table_type, keyword,host):
	global url_cmp,nextpage,pagenumber,re_data
	if host == 'google_hk':
		pagenumber = 0
		nextpage = '&start='
		url_cmp = 'http://www.google.com.hk/search?q='+ keyword + nextpage 
		re_data = re.compile(r'<h3 class="r"><a href="[\s\S]*?" target="_blank">([\s\S]*?)<cite.*?>([\s\S]*?)</cite>.*?<span.*?>([\s\S]*?)</li>',re.S)
	if host == 'baidu':
		pagenumber = 0
		nextpage = '&pn='
		url_cmp = 'http://www.baidu.com/s?wd='+keyword+nextpage
		re_data = re.compile(r'<table.*?id="\d*?".*?<a.*?href="([\s\S]*?)".*?>([\s\S]*?)</a>.*?</h3>([\s\S]*?)</td>',re.S)
		#re_data = re.compile(r'<h3 class="t"><a href="([\s\S]*?)".*?>([\s\S]*?)</a>.*?</h3>([\s\S]*?)</table>',re.S)
	if host == 'sousou':
		pagenumber = 1
		nextpage = '&pg='
		url_cmp = 'http://www.soso.com/q?w=' + keyword + nextpage
		re_data = re.compile(r'<h3><a href="([\s\S]*?)".*?>([\s\S]*?)</a>([\s\S]*?)</p>',re.S)

def do_search(table_task, table_type, keyword,host,page):
	table_time = time.strftime('%Y%m%d')
#	table_task = table_task.decode("utf-8").encode("utf-8")
#	table_type = table_type.decode("utf-8").encode("utf-8")
#	keyword = keyword.decode("utf-8").encode("utf-8")
	cur_timerecord.execute("insert into `timerecord`(`keyword`,`time`,`comefrom`,`type`,`task`) values('%s','%s','%s','%s','%s')"%(str(keyword), str(table_time), str(host), str(table_type), str(table_task)))
#	print "insert into `timerecord`(`keyword`,`time`,`comefrom`,`type`,`task`) values('%s','%s','%s','%s','%s')"%(str(keyword), str(table_time), str(host), str(table_type), str(table_task))
	pagenumber = 0
	table_number = 0
	while True:
		url = url_cmp + str(pagenumber)
		print url
		if host == 'google_hk':
			data = google_data(pagenumber,keyword)
		else:
			data = get_page_data(url)

		if host == 'sousou':
			data = data.decode('gbk','ignore').encode('utf-8')
		if host == 'google_hk':
			data = data.decode('big5','ignore').encode('utf-8')

		mine_data = re_data.findall(data)
		print len(mine_data)
		if len(mine_data)==0:
			break

		if host == 'google_hk':
			while(mine_data):
				title_words = re.sub('<[\s\S]*?>','',mine_data[0][0])
				cite_words  = re.sub('<[\s\S]*?>','',mine_data[0][1])
				text_words  = re.sub('<[\s\S]*?>','',mine_data[0][2])
				
				table_number += 1
				print   title_words,'\n',cite_words,'\n\n\n'
				#fw.write(title_words+'\n'+cite_words+'\n'+text_words+'\n\n\n')
				cur_webpage.execute('insert into `webpage`(`title`,`url`,`keyword`,`time`,`comefrom`,`number`,`type`,`task`) values("%s","%s","%s","%s","%s",%d,"%s","%s")'%(str(title_words), str(cite_words), str(keyword), str(table_time), str(host), table_number, str(table_type), str(table_task) ))
#				print 'insert into `webpage`("title","url","keyword","time","comefrom","number","type","task") values("%s","%s","%s","%s","%s",%d,"%s","%s")'%(str(title_words), str(cite_words), str(keyword), str(table_time), str(host), table_number, str(table_type), str(table_task) )
				del mine_data[0]
			if pagenumber >= 100:
				return
			pagenumber = pagenumber + 10
			continue

		while (mine_data):
			head_url = mine_data[0][0]
			if host == 'google_hk':
				head_url = re.sub('<.*?>','',mine_data[0][0])

			if host == 'baidu':
				head_url_cmp = mine_data[0][0]     #http://www.baidu.com/xxx
				head_url_cmp = head_url_cmp[7:]    #www.baidu.com/xxx
				num          = head_url_cmp.find('/')    #www.baidu.com
				host_cmp     = head_url_cmp[0:num]       #www.baidu.com
				link         = head_url_cmp[num:]        #xxx....
				if host_cmp == 'www.baidu.com':
					head_url     = url_change(host_cmp,link)
			table_number += 1;
			title = mine_data[0][1]
			title = re.sub(r'<[\s\S]*?>','',title)
			
			extra_data = mine_data[0][2]
			extra_data = re.sub('<style>[\s\S]*?</style>','',extra_data)
			extra_data = re.sub('<script>[\s\S]*?</script>','',extra_data)
			extra_data = re.sub('<[\s\S]*?>','',extra_data)
			cur_webpage.execute('insert into `webpage`(`title`,`url`,`keyword`,`time`,`comefrom`,`number`,`type`,`task`) values("%s","%s","%s","%s","%s",%d,"%s","%s")'%(str(title), str(mine_data[0][0]), str(keyword), str(table_time), str(host), table_number, str(table_type), str(table_task) ))
#			print 'insert into `webpage`("title","url","keyword","time","comefrom","number","type","task") values("%s","%s","%s","%s","%s",%d,"%s","%s")'%(str(title), str(mine_data[0][0]), str(keyword), str(table_time), str(host), table_number, str(table_type), str(table_task) )
			print mine_data[0][0],'\n',title,'\n\n\n'
			#fw.write(mine_data[0][0]+ '\n'+head_url+'\n'+title+'\n'+extra_data+'\n\n\n')
			del mine_data[0]
		
		if pagenumber >= 10* page:
		 	return
		if (host == 'sousou') & (pagenumber >=page) :
			return
		if host == 'sousou':
			pagenumber = pagenumber + 1
		else:
			pagenumber = pagenumber + 10
		
def get_page_data(page):
	page_cmp = urllib2.Request(page)
	get_page = urllib2.urlopen(page_cmp)
	data     = get_page.read()
	get_page.close()
	return data

def google_data(pagenumber,keyword):
	link = '/search?&q=' + keyword + '&start=' + str(pagenumber)
	conn = httplib.HTTPConnection('www.google.com.hk')
	conn.request('GET',link)
	page = conn.getresponse()
	return page.read()
'''
def google_data(pagenumber,keyword):
	link = '/search?&q=' + keyword + '&start=' + str(pagenumber)
	conn = httplib.HTTPConnection('www.google.com.hk')
	user_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0', \
          'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0', \
          'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533+ \
          (KHTML, like Gecko) Element Browser 5.0', \
          'IBM WebExplorer /v0.94', 'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)', \
          'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)', \
          'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14', \
          'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) \
           Version/6.0 Mobile/10A5355d Safari/8536.25', \
          'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) \
           Chrome/28.0.1468.0 Safari/537.36', \
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)']
	index = 8
	user_agent = user_agents[index]
	headers = {"User-agent": user_agent,"Accept": "text/plain"}
	conn.request('GET',link,None,headers)
	page = conn.getresponse()
	return page.read()
'''
def url_change(host,link):
	conn = httplib.HTTPConnection(host)
	conn.request('GET',link)
	url_change_page = conn.getresponse()
	url_change_data = url_change_page.read()
	conn.close()
	url_change_re = re.compile(r'<a\shref="([\s\S]*?)">',re.S)
	url_change_result = url_change_re.search(url_change_data)
	return url_change_result.group(1)
	
if __name__ == '__main__':
  conn=mdb.connect(host='127.0.0.1',user='root',passwd='1234',db='inet',port=3306,use_unicode=True,charset="utf8")
  
  cur_webpage = conn.cursor()
  cur_timerecord = conn.cursor()
  r_task = raw_input("请输入任务名称：\n")
  r_type = raw_input("请输入子任务名称：\n")
  r_keyword = raw_input("请输入关键字名称：\n")
  print "开始检索。。。\n" 
  search(r_task, r_type, r_keyword,['google_hk','baidu','sousou'],6)
  
  conn.commit()
  cur_webpage.close()
  cur_timerecord.close()
  conn.close()




