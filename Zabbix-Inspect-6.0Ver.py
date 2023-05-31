import requests
import json
import pandas as pd
import time
from datetime import datetime
import math

# Define the URL and authentication details for the Zabbix API for Zabbix 6.0

url = 'http://<zabbix URL 주소 입력 >/zabbix/api_jsonrpc.php'
headers = {'Content-Type': 'application/json-rpc'}


# 데이터 가공 클래스 생성

class DataProcessing:
    # 호스트 정보 가공을 위한 함수 hostinfo 생성 
    def hostinfo(hostinformation):
        # 호스트 리스트 초기화
        host_information = []  # New list to store additional information
        # 호스트 정보를 받는 for문 생성
        for host in hostinformation:
            # 호스트 정보의 interface 자료 확인을 위한 interface 변수 생성
            interfaces = host["interfaces"]
            
            # 인터페이스 길이 동안 for 문 실행
            for interface in interfaces:

                # 인터페이스 내 값이 없고, 호스트 상태가 정상이면 리스트에 데이터 삽입 
                if not interface["error"] and host["status"] == "0":
                    # type= agent
                    if interface["type"] == '1':
                        host_information.append([host["name"], interface["ip"], interface["port"], "Agent", interface["error"], "정상"])
                    # type=SNMP
                    elif interface["type"] == '2':
                        host_information.append([host["name"], interface["ip"], interface["port"], "SNMP", interface["error"], "정상"])
                    # type=IPMI
                    elif interface["type"] == '3':
                        host_information.append([host["name"], interface["ip"], interface["port"], "IPMI", interface["error"], "정상"])
                    # type=JMX
                    elif interface["type"] == '4':
                        host_information.append([host["name"], interface["ip"], interface["port"], "JMX", interface["error"], "정상"])
                # 인터페이스 내 값이 존재하고 호스트 상태가 정상일 때 리스트에 데이터 삽입
                elif interface["error"] and host["status"] == "0":
                    # type=agent
                    if interface["type"] == '1':
                        host_information.append([host["name"], interface["ip"], interface["port"], "Agent", interface["error"], "Agent 연결 불가"])
                    # type=SNMP
                    elif interface["type"] == '2':
                        host_information.append([host["name"], interface["ip"], interface["port"], "SNMP", interface["error"], "Agent 연결 불가"])
                    # type=IPMI
                    elif interface["type"] == '3':
                        host_information.append([host["name"], interface["ip"], interface["port"], "IPMI", interface["error"], "Agent 연결 불가"])
                    # type=JMX
                    elif interface["type"] == '4':
                        host_information.append([host["name"], interface["ip"], interface["port"], "JMX", interface["error"], "Agent 연결 불가"])
        # 리스트 삽입 구조가 데이터에 리스트를 추가하는 방식이라 기존 데이터 초기화
        hostinformation.clear()
        # 호스트 정보에 새롭게 추가된 데이터 리스트 추가 
        # 최종 데이터는 예를 들어 아래와 같음 : 
        # jira-crowd	127.0.0.1	10060	JMX	Connection refused (Connection refused): service:jmx:rmi:///jndi/rmi://127.0.0.1:10060/jmxrmi	Agent 연결 불가
        hostinformation.append(host_information)  # Append additional information to the original list
        print('최종 생성된 호스트 데이터는 다음과 같습니다 : ', hostinformation[0],'\n')
        return hostinformation[0]
    
    # 장애 정보를 받아오고 가공하는 함수
    def probleminfo(hostlist):

        # hostlist는 메인에서 host.get 에서 받아온 json 딕셔너리를 리스트로 정리함
        hostlist= [list(item.values()) for item in hostlist]

        print('hostlist for problemcheck : ',hostlist)

        # 장애정보를 받아올 리스트 선언
        probleminformation = []
        # problemparameter={'output': ["name","severity","clock"], 'hostids': hostids, "recent": "true"}
        
        # hostlist의 길이만큼 for문 진행
        for hlist in range (len(hostlist)):
            # 장애정보를 받아올 problem 파라미터 지정
            problemparameter={'output': ["name","severity","clock"], 'hostids': hostlist[hlist][0], "recent": "true"}
            # problem.get method로 장애 정보를 받아옴
            probleminfo= Getinfo.RestInfo('problem.get',problemparameter)

            # 받아온 장애정보를 리스트로 변경
            probleminfo= [list(item.values()) for item in probleminfo]
            del hostlist[hlist][0]
            print('hostlist=', hostlist[hlist])
            print('probleminfo = ', probleminfo)

            # 호스트 id 별 장애정보를 받아올 경우에 진행
            if probleminfo:
            
                for i in range (len(probleminfo)):

                    # 받아온 severity 정보는 1,2,3,4,5 순으로 받아오고 리스트의 3번째 값으로 받아옴 
                    print('severity : ', probleminfo[i][2])

                    # severity 순으로 데이터를 리스트로 저장  (hostid, hostname, problem description, severity, 장애 발생 시간으로 저장)
                    if probleminfo[i][2] == '1':
                        probleminformation.append(hostlist[hlist]+ [probleminfo[i][1]]+ ['Information']+ [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(probleminfo[i][3])))])
                        
                    elif probleminfo[i][2] == '2':
                        probleminformation.append(hostlist[hlist]+ [probleminfo[i][1]]+ ['Average']+ [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(probleminfo[i][3])))])
                        
                    elif probleminfo[i][2] == '3':
                        probleminformation.append(hostlist[hlist]+ [probleminfo[i][1]]+ ['Low']+ [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(probleminfo[i][3])))])
                        
                    elif probleminfo[i][2] == '4':
                        probleminformation.append(hostlist[hlist]+ [probleminfo[i][1]]+ ['High']+ [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(probleminfo[i][3])))])   
                     
                    elif probleminfo[i][2] == '5':
                        probleminformation.append(hostlist[hlist]+ [probleminfo[i][1]]+ ['Average']+ [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(probleminfo[i][3])))])
            #         
            else:
                print('장애 리스트가 없습니다','\n')            

      


        # print('최종 probleminformation :', probleminformation)

        return probleminformation
    
    def iteminfo(hostlist):
         
         hostlist= [list(item.values()) for item in hostlist]
         print('hostlist for itemcheck : ',hostlist)
         print('hostlist[0]',len(hostlist))
         print('template :', hostlist[0][2][1]['host'])
         print('hostlist:',hostlist[0][1])

         
         linuxitem=[]
         windowsitem=[]
         snmpitem=[]
         dbitem=[]

         for i in range (len(hostlist)):
             for j in range (len(hostlist[i][2])):
                print('template = ', hostlist[i][2][j]['host'])
                if hostlist[i][2][j]['host'] and 'Linux' in hostlist[i][2][j]['host']:
                    itemparameter = { "output": ["name","key_","lastvalue"], "hostids": hostlist[i][0], "search":{"name": "CPU utilization", "name": "Available memory"} }
                    
                    item=Getinfo.RestInfo('item.get', itemparameter)
                    item = [list(item.values()) for item in item]
                    print('item = ', item[0])
                    for itemlen in range (len(item)): 
                       
                        linuxitem.append([hostlist[i][1]]+ [hostlist[i][3][0]['ip']] + item[itemlen])
                
                elif hostlist[i][2][j]['host'] and 'Windows' in hostlist[i][2][j]['host']:
                    
                   
 
                        
                    print('itemlist : ', linuxitem)
             

         



# host, problem, item 수집을 위한 클래스 함수 구현        
class Getinfo:
    # 호스트 정보를 가져오기 위한 함수 구현 
    def RestInfo(method,information):
        # Get Host Information
        host_payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': information,
            'auth': AUTHTOKEN,
            'id': 1
        }

        try:
            rest_response = requests.post(url, json=host_payload, headers=headers)
            rest_response_json = rest_response.json()
            print("Get information success!\nhost=" + json.dumps(rest_response_json, indent=4))

           # 호스트 정보를 딕셔너리로 정리
            restresult = rest_response.json()['result']
            return restresult
        
            # enabled_hosts = sum(host['status'] == '0' for host in hosts)
            # disabled_hosts = sum(host['status'] == '1' for host in hosts)
            # print('Number of hosts (enabled/disabled):', len(hosts), enabled_hosts, '/', disabled_hosts)

        except Exception as e:
            print("Failed to get host information. Error:", str(e))
            exit()

# 생성된 데이터를 엑셀에 삽입
def createexcel(information):
    if information == hostinformation:
        excel_data = pd.DataFrame(information, columns=['Host Name', 'IP', 'Port' ,'Agent Type', 'Agent Error Message', 'Agent 상태 확인'])
        print("엑셀에 삽입할 데이터는 아래와 같습니다.\n", excel_data)
        try:
            excel_data.to_excel('/Users/gongdol/Desktop/{} Zabbix 점검 항목.xlsx'.format(datetime.today().strftime('%Y-%m-%d')), sheet_name='Host-Check')
            print("Data written to Excel successfully.")
        except Exception as e:
            print("Failed to write data to Excel. Error:", str(e))
    elif information == probleminformation:
        excel_data= pd.DataFrame(information, columns=['Hostname', 'Description','Severity','Time'])
        print("엑셀에 삽입할 데이터는 아래와 같습니다.\n", excel_data)
        try:
            excel_data.to_excel('/Users/gongdol/Desktop/{} Zabbix 점검 항목.xlsx'.format(datetime.today().strftime('%Y-%m-%d')), sheet_name='Problem-Check')
            print("Data written to Excel successfully.")
        except Exception as e:
            print("Failed to write data to Excel. Error:", str(e))
    



# 로그인을 통해 Session ID 확인

def login(UNAME,PWORD):
    # Get Authentication Session
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": UNAME,
            "password": PWORD
    },
        "id": 1
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_json = response.json()
        AUTHSESSION = response_json["result"]
        print(json.dumps(response_json, indent=4, sort_keys=True))

        # 생성된 Session 값 반환
        return AUTHSESSION
    except Exception as e:
        print("Failed to authenticate. Error:", str(e))
    exit()




##########################################################메인#################################################################
# Zabbix에 로그인할 사용자 이름과 패스워드 입력

UNAME = 'Admin'
PWORD = 'zabbix'

# 로그인 함수를 통해 로그인 Session ID를 가져옴
AUTHTOKEN= login(UNAME,PWORD)

######################### 호스트(에이전트) 데이터를 가져오는 과정 ##########################
# 호스트 정보를 가져오기 위한 변수 리스트 선언
hostinformation=[]

# 호스트 정보를 가져오기 위한 파라미터 선언
hostparameter = {'output': ["hostid", "name", "status"], 'selectInterfaces': ["ip", "type", "port","error"] }

# get_host 함수를 통해 호스트 정보를 가져옴
hostinformation=Getinfo.RestInfo('host.get',hostparameter)

# DataProcessing.hostinfo 함수를 통해 호스트 정보를 가공
hostinformation=DataProcessing.hostinfo(hostinformation)

createexcel(hostinformation)

##################################################################################

######################### 호스트 별 장애 데이터를 가져오는 과정 ###########################

# host 정보를 받아올 파라미터 생성
hostparameter= {'output': ["name", "hostid"]}

# host.get method로 네임과, 호스트 아이디를 받을 수 있도록 Rest 요청 진행
probleminformation=Getinfo.RestInfo('host.get', hostparameter)

# host.get method로 요청해 받아온 데이터를 토대로 장애 데이터 요청 및 데이터 가공
probleminformation= DataProcessing.probleminfo(probleminformation)
print('최종 probleminformation = ', probleminformation)

##################################################################################
# 최종 데이터들을 엑셀에 삽입

createexcel(probleminformation)
######################### 호스트 별 수집 데이터를 가져오는 과정 ###########################

parameter= {'output': ["name", "hostid"], 'selectInterfaces': ["ip"], 'selectParentTemplates': ["host"]}
itemhostlist=Getinfo.RestInfo('host.get',parameter)
itemlist=DataProcessing.iteminfo(itemhostlist)

##################################################################################

