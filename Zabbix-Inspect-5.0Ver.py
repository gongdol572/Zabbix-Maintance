#!/bin/python

import requests
import json
import argparse
from datetime import datetime
import time
import pandas as pd


# 전역변수 설정

# BaseURL = 'Zabbix Base URL 입력'
BaseURL = 'http://test-zabbix.com:81'
api_url= f'{BaseURL}/api_jsonrpc.php'
zbx_session=''
headers = {'Content-Type': 'application/json-rpc'}

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
    



def Get_Host_HealthCheck(HostInfo,proxy_mapping):
    host_information = []

    for host in HostInfo:
        interfaces = host['interfaces']
        # active_available = host['active_available']

        available_status = {'0': 'Unknown', '1': 'Available', '2': 'Unavailable'}
        host_available = available_status.get(host['available'])
        
       

        for interface in interfaces:
            # Proxy 체크
            proxy_host = proxy_mapping.get(host['proxy_hostid'], 'Direct to Server')

            type_map = {'1': 'Agent', '2': 'SNMP', '3': 'IPMI', '4': 'JMX'}
            agent_type = type_map.get(interface['type'], 'Unknown')
            print('agent type =', agent_type)



            if not host['error'] and host['status'] == '0' and host_available == 'Available':
                host_information.append({'hostids': host['hostid'], 'host': host['name'], 'ip': interface['ip'], 'port': interface['port'], 'type': agent_type,
                                        'error_message' : host['error'], 'proxyid' : proxy_host, 'availability' : host_available})
            elif host['status'] == '1':
                host_information.append({'hostids': host['hostid'], 'host': host['name'], 'ip': interface['ip'], 'port': interface['port'], 'type': agent_type,
                                        'error_message' : 'This host is disabled', 'proxyid': proxy_host, 'availability' : host_available})
            else:
                host_information.append({'hostids': host['hostid'], 'host': host['name'], 'ip': interface['ip'], 'port': interface['port'], 'type': agent_type,
                                        'error_message' : host['error'], 'proxyid' : proxy_host, 'availability' : host_available})

       # print('최종 생성된 호스트 데이터는 다음과 같습니다 : ', host_information, '\n')
    
    return host_information


def Get_API(token,method, information):
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': information,
            'auth': token,
            'id': 1
        }
        try:
            rest_response = requests.get(api_url, json=payload, headers=headers)
            rest_response_json = rest_response.json()
            print('Get information success!\n Rest Information =' + json.dumps(rest_response_json, indent=4))

            restresult = rest_response.json()['result']
            return restresult
        except Exception as e:
            print('Failed to get host information. Error:', str(e))
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
    # Parser 등록 후 토큰 값과 장애 정보 확인을 위한 날짜 입력 받기
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
    

    # 프록시 정보를 Extend로 받음.
    ProxyParameter = {
        'output': 'extend'              
                      }
    print(ProxyParameter)
    ProxyInfo =  Get_API(token,'proxy.get',ProxyParameter)
    proxy_mapping = {proxy['proxyid']: proxy['host'] for proxy in ProxyInfo}
    print(f'Proxy List : {proxy_mapping}')


    
    # 호스트 Parameter 선언
    Host_Parameter={'output': ['hostid', 'name', 'status', 'available', 'proxy_hostid','error'],
                 'selectInterfaces': [ 'ip', 'type', 'port'] }
    
    HostInfo=Get_API(token,'host.get',Host_Parameter)
    
    Host_Data=Get_Host_HealthCheck(HostInfo,proxy_mapping)
    print(f'Host_Data = {Host_Data}')

   
    # 받아온 호스트 정보에 대한 장애 정보 호출
    for Host in range (len(Host_Data)):
        HostName=Host_Data[Host]['host']
        Hostid=Host_Data[Host]['hostids']
        Hostip=Host_Data[Host]['ip']
        Hostport = Host_Data[Host]['port']
        Severity_info = {'0': 'Undefined', '1': 'Information', '2': 'Average', '3': 'Low', '4': 'High','5': 'Disaster'}

        print(f'Hostname : {HostName}, Hostip : {Hostip}, Hostid: {Hostid} ')

        ################################################ 수집 되지 않은 아이템 리스트 확인 ##############################################
        
        item_get_parameter = {
            'output' : ['name','key','state','error'],
            'hostids' : Hostid,
            # STATE 0 -> 수집 가능, 1 -> 수집 불가
            'filter' : { 
                'state' : '1'
            },
            'sortfield' : 'key_',
            'sortorder' : 'ASC',
            
        }

        # 호출한 아이템 데이터를 리스트로 저장
        Item_Value = Get_API(token,'item.get',item_get_parameter)
        for item in range(len(Item_Value)):
            itemid = Item_Value[item]['itemid']
            itemname = Item_Value[item]['name']
            item_key = Item_Value[item]['key_']
            error = Item_Value[item]['error']
            Unsup_Item_Data.append({'hostname': HostName , 'hostip': Hostip, 'port': Hostport ,'itemid' : itemid,'item': itemname, 'item_key' : item_key, 'error_message': error})



        ####################################### 한달 간 장애 이벤트(미해결) 가져오기 #################################################
        Problemparameter = {'output': ['name', 'severity', 'clock'], 'time_from': timestamp, 'hostids': Hostid, 'recent': 'true'}
        Probleminfo = Get_API(token, 'problem.get', Problemparameter)
        
        if Probleminfo:
            for problem in Probleminfo:
                severity = Severity_info.get(problem['severity'],'Unknown')
                problem_detail = problem['name']
                occured_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(problem['clock'])))
                print(f'severity : {severity}, occured time : {occured_time}, detail : {problem_detail}')
                Problem_Data.append({'Hostid': Hostid, 'Hostname': HostName, 'Hostip': Hostip, 'Problem Name': problem_detail, 'Severity': severity, 'Occured Time': occured_time })
                

        # 한달동안 발생했던 장애 이벤트 가져오기
        
        Eventparameter = {
            'output': ['name', 'severity', 'r_eventid', 'clock'], 
            'time_from': timestamp,
            'hostids': Hostid
        }

        EventInfo = Get_API(token, 'event.get', Eventparameter)
        for event in range(len(EventInfo)):
            event_id = EventInfo[event]['eventid']
            recovery_eventid = EventInfo[event]['r_eventid']
            event_name = EventInfo[event]['name']
            occured_time = datetime.fromtimestamp(int(EventInfo[event]['clock'])) 

            # 장애 해결 여부 확인을 위한 변수 선언  
            recovery_time=0
            recovery_state=0

        
            print(f'eventid: {event_id}, eventname: {event_name}, occrued_time: {occured_time} recovery_eventid = {recovery_eventid}')
            
            # 장애 해결에 대한 EVENTID가 있을 경우 이벤트를 불러와 Recovery_time 값 확인
            if recovery_eventid != '0':
                
                Recovery_Event_Parameter = {
                    'output': ['name', 'severity' , 'clock'], 
                    'eventids' : recovery_eventid	
                }
                Recovery_Item = Get_API(token,'event.get',Recovery_Event_Parameter)
                recovery_time = datetime.fromtimestamp(int(Recovery_Item[0]['clock']))
                print(f'recovery_time : {recovery_time}')
                recovery_state = '해결'

            else :
                print('check')
                recovery_time = datetime.now()
                recovery_state = '미해결'
            
            # 장애 발생 후 해결 까지 걸린 시간을 확인하기 위한 함수 호출
            duration =  CalDuration(occured_time,recovery_time)
            print(f'duration : {duration}')
            Event_Data.append({'Eventid': event_id, 'Hostname': HostName, 'Hostip': Hostip, 'Problem Name': event_name, 'Severity': severity, 'Problem Resolved State' : recovery_state, 'Occured Time': occured_time, 'Recovery_Time' : recovery_time, 'Duration' : duration  })
            
    print(f'EventData : {Event_Data}')

   ####################################### 한달동안 발생했던 장애 이벤트 가져오기 (END) ##########################################

   ##########################################################################################################################

   ####################################### Zabbix Server 프로세스 사용현황 이미지 추출 ###########################################


    # Zabbix Server Utilization Chart Export
    
    Utilization_Parameter = {
        'output' : ['itemid','name'],
        'search':{
                'name': ['Zabbix server: utilization']   
        },
        'startSearch': True,
        'serachByAny' : True,
        'hostids' : '10084'
    }

    Zabbix_Server_Utilization = Get_API(token,'item.get',Utilization_Parameter)
    Utilizationlist = ''

    for utilization in range (len(Zabbix_Server_Utilization)):
        Utilizationlist += f'&itemids%5B{Zabbix_Server_Utilization[utilization]['itemid']}%5D={Zabbix_Server_Utilization[utilization]['itemid']}'
        Trend_Item = Zabbix_Server_Utilization[utilization]['itemid']
        Trend_Parameter = {
            'output' : ['value_avg','itemid','clock'],
            'time_from' : timestamp,
            'itemids' : [Trend_Item]
        }

        
        # Trend Data
        
        Trend_Result = Get_API(token,'trend.get',Trend_Parameter)
        for trend in Trend_Result:
            trend_value = trend['value_avg']
            trend_time = trend['clock']

            if float(trend_value) > 75:
               
                trend_time = datetime.fromtimestamp(int(trend_time))
                trend_time = trend_time.strftime('%Y-%m-%d %H:%M:%S')
                Trend_Data.append({'Trend_Name' : Zabbix_Server_Utilization[utilization]['name'], 'Value': trend_value, 'Time': trend_time})

    
    
    
    Zabbix_Utilization_Chart_api_url=f"{BaseURL}/chart.php?from=now%2FM&to=now%2FM{Utilizationlist}&type=0&profileIdx=web.item.graph.filter&profileIdx2=0&batch=1&width=1607&height=200&_=wu3dbkvn"
    print(Zabbix_Utilization_Chart_api_url)
    
    with open('./zabbix_utilization.jpg', 'wb') as file:
        response = requests.get(Zabbix_Utilization_Chart_api_url, cookies={'zbx_session': token})
        file.write(response.content)
        file.close()
    
    ####################################### Zabbix Server 프로세스 사용현황 이미지 추출(END) ###########################################

    save_to_excel(Host_Data, Unsup_Item_Data, Problem_Data, Event_Data, Trend_Data, './zabbix_inspection-result.xlsx')
    print('Data saved to zabbix_data.xlsx')
    
    
if __name__ == '__main__':
    main()
    
