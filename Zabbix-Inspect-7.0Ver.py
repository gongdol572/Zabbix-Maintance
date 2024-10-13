#!/bin/python

import requests
import json
import argparse
from datetime import datetime
import time
import pandas as pd
# 전역변수 설정

BaseURL = 'http://10.220.0.55/zabbix'
api_url= f'{BaseURL}/api_jsonrpc.php'
zbx_session=''
headers = {'Content-Type': 'application/json-rpc'}

# Zabbix에서 해결된 장애 정보의 장애 지속 시간 계산용 함수
def CalDuration(occured_time, recovery_time):
    duration = recovery_time - occured_time

    # 차이를 일, 시간, 분, 초로 분해
    day = duration.days
    seconds = duration.seconds
    hour = seconds // 3600
    seconds %= 3600
    minute = seconds // 60
    seconds %= 60

    # 각 단위를 조건에 따라 문자열로 추가
    time_str = ''
    if day > 0:
        time_str += f'{day}일 '
    if hour > 0:
        time_str += f'{hour}시간 '
    if minute > 0:
        time_str += f'{minute}분 '
    if seconds > 0 or time_str == '':  # 초는 항상 표시되도록
        time_str += f'{seconds}초'

    return time_str.strip()


def Get_Host_HealthCheck(HostInfo,proxy_mapping,proxy_group_mapping):
    host_information = []

    for host in HostInfo:
        interfaces = host["interfaces"]
        # active_available = host["active_available"]

        for interface in interfaces:
            # Proxy 체크
            # proxy_host = proxy_mapping.get(host["proxyid"], "Direct to Server")


        
            if int(host["proxyid"]) > 0 and int(host["assigned_proxyid"]) == 0:
                proxy_host = proxy_mapping.get(host["proxyid"])
            elif int(host["proxyid"]) == 0 and int(host["assigned_proxyid"]) > 0:
                proxy_host = proxy_mapping.get(host["assigned_proxyid"])
                
            else :
                proxy_host = None

            proxy_group_host =proxy_group_mapping.get(host["proxy_groupid"])

            type_map = {'1': 'Agent', '2': 'SNMP', '3': 'IPMI', '4': 'JMX'}
            agent_type = type_map.get(interface["type"], "Unknown")
            print("agent type =", agent_type)

            available_status = {'0': 'Unknown', '1': 'Available', '2': 'Unavailable'}
            host_available = available_status.get(interface["available"], "Unknown")

            if not interface["error"] and host["status"] == "0" and host_available == "Available":
                host_information.append({'hostids': host["hostid"], 'host': host["name"], 'ip': interface["ip"], 'port': interface["port"], 'type': agent_type,
                                        'error_message' : interface["error"], 'proxygroup' : proxy_group_host, 'proxy' : proxy_host, 'availability' : host_available})
            elif host["status"] == "1":
                host_information.append({'hostids': host["hostid"], 'host': host["name"], 'ip': interface["ip"], 'port': interface["port"], 'type': agent_type,
                                        'error_message' : 'This host is disabled', 'proxygroup' : proxy_group_host, 'proxy': proxy_host, 'availability' : host_available})
            else:
                host_information.append({'hostids': host["hostid"], 'host': host["name"], 'ip': interface["ip"], 'port': interface["port"], 'type': agent_type,
                                        'error_message' : interface["error"], 'proxygroup' : proxy_group_host, 'proxy' : proxy_host, 'availability' : host_available})

       # print('최종 생성된 호스트 데이터는 다음과 같습니다 : ', host_information, '\n')
    
    return host_information

def Get_Problem_Data(Host_Data,token,method):

    problem_data=[]
    
    for host in Host_Data:
        host_name=host['host']
        hostid=host['hostids']
        print(f'host : {host_name} , hostid={hostid}')

        problemparameter = {'output': ["name", "severity", "clock"], 'time_from': 1709254800, 'hostids': hostid}

        probleminfo = RestInfo(token, method, problemparameter)
        print('data :', probleminfo)

        if probleminfo:
            for data in probleminfo:
                severity_info = {'0': 'Undefined', '1': 'Information', '2': 'Average', '3': 'Low', '4': 'High','5': 'Disaster'}
                severity = severity_info.get(data['severity'], "Unknown")
                detail = data['name']

                ProblemTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data['clock'])))

                print('severity : ', severity)
                print('Problem Time :', ProblemTime)

                problem_data.append({'hostname': host_name, 'severity': severity, 'ProblemTime ': ProblemTime, 'Detail': detail})
        else:
            print('장애 리스트가 없습니다', '\n')
    return problem_data
            


def RestInfo(token,method, information):
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': information,
            'auth': token,
            'id': 1
        }
        try:
            rest_response = requests.get(url, json=payload, headers=headers)
            rest_response_json = rest_response.json()
            print("Get information success!\n Rest Information =" + json.dumps(rest_response_json, indent=4))

            restresult = rest_response.json()['result']
            return restresult
        except Exception as e:
            print("Failed to get host information. Error:", str(e))
            exit()


def save_to_excel(host_data, unsup_item_data, problem_data, event_data, trend_data, filename):
    # 데이터프레임 생성
    host_df = pd.DataFrame(host_data)
    unsup_item_df = pd.DataFrame(unsup_item_data)
    problem_df = pd.DataFrame(problem_data)
    event_df = pd.DataFrame(event_data)
    trend_df = pd.DataFrame(trend_data)
    
    # ExcelWriter 객체 생성
    with pd.ExcelWriter(filename) as writer:
        # 각각의 데이터프레임을 시트로 저장
        host_df.to_excel(writer, sheet_name='Host Data', index=False)
        unsup_item_df.to_excel(writer, sheet_name='Unsupport Item Data', index=False)
        problem_df.to_excel(writer, sheet_name='Problem Data', index=False)
        event_df.to_excel(writer, sheet_name='Event Data', index=False)
        trend_df.to_excel(writer, sheet_name='Zabbix Utilization', index=False)

def main():
    # 최초 선언 
    
    parser = argparse.ArgumentParser(description='Get Zabbix Inspection Info')
    parser.add_argument('--token', type=str, help='Please Insert Zabbix Super Admin access token')
    parser.add_argument('--date', type=str, help='Please Insert from date value to check import problem and event. ex) 2024-09-30 ')
    config = parser.parse_args()
    
    
    token = config.token
    date = config.date
    timestamp = int(time.mktime(datetime.strptime(date,'%Y-%m-%d').timetuple()))

    print(f'timestamp = {timestamp}')
    
    # 데이터 수집을 위한 리스트 선언
    Host_Data=[]
    Problem_Data=[]
    Event_Data=[]
    Unsup_Item_Data = []
    Trend_Data = []
   

    # Proxy 체크 
    ProxyParameter = {'output': ['name','proxyid'] }
    ProxyInfo =  RestInfo(token,'proxy.get',ProxyParameter)

    proxy_mapping = {proxy['proxyid']: proxy['name'] for proxy in ProxyInfo}
    print(f'Proxy List : {proxy_mapping}')

    ProxyGroupParameter = {'output' : ['proxy_groupid','name']}
    ProxyGroupInfo = RestInfo(token,'proxygroup.get',ProxyGroupParameter)

    proxy_group_mapping = {proxygroup['proxy_groupid']: proxygroup['name'] for proxygroup in ProxyGroupInfo}
    print(f'Proxy Group list : {proxy_group_mapping}')

        
    # 호스트 Health Check , 7.0 버전에서는 Proxyid로 설정
    Host_Parameter = {'output': ["hostid", "name", "status", "active_available", 'proxyid','proxy_groupid','assigned_proxyid'],
                 'selectInterfaces': ["available", "ip", "type", "port", "error"] }
    
    HostInfo = RestInfo(token,'host.get',Host_Parameter)
    Host_Data = Get_Host_HealthCheck(HostInfo,proxy_mapping, proxy_group_mapping)
    print(f'Host_Data = {Host_Data}')


    # Problem Health Check 
    Problem_Data=Get_Problem_Data(Host_Data,token,'problem.get')
    print(f'Problem_Data = {Problem_Data}')


    History_Data=[]
    History_Data=Get_Problem_Data(Host_Data,token,'event.get')
    print(f'History_Data = {History_Data}')

    save_to_excel(Host_Data, Problem_Data, History_Data, './zabbix_inspection-result.xlsx')
    print('Data saved to zabbix_data.xlsx')
    
    
    
    ItemParameter = {'output': ['itemid'] ,
                     "hostids" : "10084",
                     "tags": [
                         {
                             "tag" : "component",
                             "value" : "internal-process",
                             "operator" : "1"
                          
                         }
                     ]
                     
                    }
    Item_Data=RestInfo(token,'item.get',ItemParameter)

    Itemid = [item["itemid"] for item in Item_Data]
    print (f"itemid : {Itemid}")

    
    # Utilization Image Download
    Zabbix_ChartURL = "http://10.220.0.58/zabbix/chart.php?action=batchgraph"
    params = "&".join([f"itemids%5B{id}%5D={id}" for id in Itemid])
    Zabbix_ChartURL = f"{Zabbix_ChartURL}&{params}&graphtype=0"
    print(Zabbix_ChartURL)

    # Login 후 SessionID 값 가저오기
    USERNAME = 'Admin'
    PASSWORD = 'zabbix'
    headers = {"Content-Type": "application/json"}
    Login_Parameter = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "username": USERNAME,
                "password": PASSWORD,
                "userData": True
             
            },
            "id": 1
        }
            

    response = requests.post(url,headers=headers,json=Login_Parameter)
    result = response.json()
    print(result)

   #  zbx_sessionid = 'eyJzZXNzaW9uaWQiOiIzZWFmNjZiYTc4MDJjY2U1MmZhZDE4ZTYxYzA1ODVlNCIsInNlcnZlckNoZWNrUmVzdWx0Ijp0cnVlLCJzZXJ2ZXJDaGVja1RpbWUiOjE3MjA5NjA1NTYsInNpZ24iOiIzMjM1MTIxN2ZmZjNiZDg1NWU0OGNhNTQyM2UwNGU2N2U1NDc3OGU4ODljZGJhZGZkZTgyMmZlYWRiMTc5ZTNmIn0%3D'
    
    headers = { 
        "Authorization" : f'Basic {token}',
        'Content-Type' : 'image/png'
       
        }
    
    ChartRequest = requests.request("POST", Zabbix_ChartURL, headers=headers, stream=True)

    with open ("./utilization.png", 'wb') as out_file:
        shutil.copyfileobj(ChartRequest.raw, out_file)
        

    



if __name__ == "__main__":
    main()
    
