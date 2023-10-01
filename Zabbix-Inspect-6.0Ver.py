import requests
import json
import pandas as pd
import time
from datetime import datetime
import logging
from rest_framework import exceptions


url = 'http://10.220.0.119/zabbix/api_jsonrpc.php'
headers = {'Content-Type': 'application/json-rpc'}


UNAME = "Admin"
PWORD = "zabbix"

hostinformation=[]
exceldata=[]



class DataProcessing:
    # 호스트 정보 가공을 위한 함수 hostinfo 생성 
    def hostinfo(hostinformation):
        # 호스트 정보를 저장할 리스트 선언
        host_information = []  
       
        # 호스트 정보를 받는 for문 생성
        for host in hostinformation:
            # 호스트 정보의 interface 자료 확인을 위한 interface 변수 생성
            interfaces = host["interfaces"]
            
            # 인터페이스 길이 동안 for 문 실행
            for interface in interfaces:
                # type 유형 정의
                type={'1':'Agent','2':'SNMP','3':'IPMI','4':'JMX'}
                # interface["type"] 값에 따라 agent_type 정의 -> Rest로 받아온 interface["type"] 값이 1이면 agent_type 값은 agent로 정의
                agent_type = type.get(interface["type"])
                print("agent type = ", agent_type)
                # 호스트가 정상적으로 연결된 상태면 리스트에 데이터 삽입 
                if not interface["error"] and host["status"] == "0" :

                    host_information.append([host["name"], interface["ip"], interface["port"], agent_type, interface["error"], "정상"])
                    
                # 호스트가 연결 불가 상태이지만 호스트 상태가 정상일 때 리스트에 데이터 삽입
                elif interface["error"] and host["status"] == "0":
                    # type=agent
                    host_information.append([host["name"], interface["ip"], interface["port"], agent_type, interface["error"], "Agent 연결 불가"])
                
                else :
                    host_information.append([host["name"], interface["ip"], interface["port"], agent_type, interface["error"], "해당 호스트는 비활성화 상태입니다."])
     
        # 최종 데이터는 아래와 같은 예시와 같음 : 
        # jira-crowd	127.0.0.1	10060	JMX	Connection refused (Connection refused): service:jmx:rmi:///jndi/rmi://127.0.0.1:10060/jmxrmi	Agent 연결 불가
        print('최종 생성된 호스트 데이터는 다음과 같습니다 : ', host_information,'\n')
        return host_information
    
    def probleminfo(hostlist):
        # 장애 정보를 받아올 Hostid 값 및 hostname 정의
        hostlist= [list(item.values()) for item in hostlist]
        print('hostlist for problemcheck : ',hostlist)
        probleminformation = []
        # problemparameter={'output': ["name","severity","clock"], 'hostids': hostids, "recent": "true"}
        # host 갯수 만큼 for문 진행
        for hlist in range (len(hostlist)):
            # 각 호스트 마다 장애 정보를 받기 위해 Parameter 지정, hostlist[hlist][0] 값은 각 호스트의 hostid 값.
            # 장애 정보는 호스트에 발생한 장애 리스트와 가장 최근에 해결된 장애 리스트만 가져옴.
            # Rest에 요청한 장애 정보는 장애 이름, 장애 수준, 장애가 발생한 시간을 가져옴.
            # 정보 : https://www.zabbix.com/documentation/current/en/manual/api/reference/problem/get

            '''
            가져온 장애 정보 예시
            
            Rest Information ={
            "jsonrpc": "2.0",
            "result": [
            {
                 "eventid": "2442345",
                    "name": "High memory utilization (>90% for 5m)",
                    "severity": "3",
                    "clock": "1690867966"
             }
            ],
                    "id": 1
            }

            '''

            problemparameter={'output': ["name","severity","clock"], 'hostids': hostlist[hlist][0], "recent": "true"}
            probleminfo= Getinfo.RestInfo('problem.get',problemparameter)

            # 가져온 장애 정보 리스트화 
            probleminfo= [list(item.values()) for item in probleminfo]
            
            
        
            print('hostlist=', hostlist[hlist])
            print('probleminfo = ', probleminfo)
            
            # 장애 정보가 있을 경우,
            
            if probleminfo:

                for i in range (len(probleminfo)):
                   
                    hostid = hostlist[hlist]

                    print('hostid =', hostid)
                    hostname = [probleminfo[i][1]]

                    print('hostname = ', hostname)
                    
                    severity_info= {'0':'Undefined','1':'Information','2':'Average','3':'Low','4':'High','5':'Disaster'}
                    severity = [severity_info.get(probleminfo[i][2])]

                    ProblemTime= [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(probleminfo[i][3])))]

                    print('severity : ', severity)
                    print('Problem Time :', ProblemTime)

                    probleminformation.append(hostid+ hostname+ severity+ ProblemTime)
                 
                    
                      
            else:
                print('장애 리스트가 없습니다','\n')            

      


        # print('최종 probleminformation :', probleminformation)

        return probleminformation

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
            print("Get information success!\n Rest Information =" + json.dumps(rest_response_json, indent=4))

           # 호스트 정보를 딕셔너리로 정리
            restresult = rest_response.json()['result']
            return restresult
        
        except Exception as e:
            print("Failed to get host information. Error:", str(e))
            exit()

# 생성된 데이터를 엑셀에 삽입
def createexcel(exceldata):

        excel_data = pd.ExcelWriter('C:\\Users\\Jackson\\Desktop\\{}-Zabbix-Inspection.xlsx'.format(datetime.today().strftime('%Y-%m-%d')), engine='openpyxl')
        
        
        
        try:
            
            for i in range(len(exceldata)):
                excel_data_df = pd.DataFrame(exceldata[i]['data'], columns=exceldata[i]['column'])
                print("엑셀에 삽입할 데이터는 아래와 같습니다.\n", excel_data_df)
                excel_data_df.to_excel(excel_data, sheet_name= exceldata[i]['sheet_name'], index=False)
                print("Data written to Excel successfully.")


            
            #excel_data.to_excel('C:\\Users\\Jackson\\Desktop\\{}-Zabbix-Inspection.xlsx'.format(datetime.today().strftime('%Y-%m-%d')), sheet_name=sheet_name)
            
            excel_data.save();
        except Exception as e:
            print("Failed to write data to Excel. Error:", str(e))
  

# 로그인을 통해 Session ID 확인

    def login(UNAME,PWORD):
        # Get Authentication Session
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "username": UNAME,
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


######################################메인 함수 #########################################



# 로그인 함수를 통해 로그인 Session ID를 가져옴
AUTHTOKEN= login(UNAME,PWORD)

######################### 호스트(에이전트) 데이터를 가져오는 과정 ##########################
# 호스트 정보를 가져오기 위한 변수 리스트 선언

# 호스트 정보를 가져오기 위한 파라미터 선언
hostparameter = {'output': ["hostid", "name", "status"], 'selectInterfaces': ["ip", "type", "port","error"] }

# get_host 함수를 통해 호스트 정보를 가져옴
hostinformation=Getinfo.RestInfo('host.get',hostparameter)

# DataProcessing.hostinfo 함수를 통해 호스트 정보를 가공
hostinformation=DataProcessing.hostinfo(hostinformation)


excelcolumn= ['Host Name', 'IP', 'Port' ,'Agent Type', 'Agent Error Message', 'Agent 상태 확인']
sheet_name='Host-Check'
#createexcel(hostinformation,excelcolumn,sheet_name)
exceldata.append({'data':hostinformation,'column':excelcolumn,'sheet_name':sheet_name})

##################################################################################

######################### 호스트 별 장애 데이터를 가져오는 과정 ###########################


hostparameter= {'output': ["name", "hostid"]}

probleminformation=Getinfo.RestInfo('host.get', hostparameter)

probleminformation= DataProcessing.probleminfo(probleminformation)
print('최종 probleminformation = ', probleminformation)


excelcolumn= ['HostID', 'Hostname', 'Description','Severity','Time']
sheet_name='Problem-Check'


exceldata.append({'data':probleminformation,'column':excelcolumn,'sheet_name':sheet_name})




##################################################################################
# 최종 데이터들을 엑셀에 삽입
createexcel(exceldata)
