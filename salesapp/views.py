from django.shortcuts import render
from django.http import HttpResponse
import requests
import csv
import json
import xmltodict
import datetime
from math import ceil
import jxmlease
import operator
import random
from operator import itemgetter
import time
from json import loads, dumps

# Create your views here.

def auth(clientId: str, 
         clientSecret: str,
         accountId:str
    ) -> requests.Response:
    
    end_point = "https://mc4pytkknrp1gsz0v23m93b3055y.auth.marketingcloudapis.com/v2/token" 
    headers = {'Content-type': 'application/json;charset=UTF-8'}
    payload = {
        "grant_type":"client_credentials",
        "client_id": clientId,
        "client_secret": clientSecret,
        "account_id": accountId,
    }

    req = requests.post(
    end_point,
    payload,
    {"headers" : headers}
        # verify=False
    )
    # req.close()
    return req.json()

cred = auth('0uxbt59f6sju7wn305gjul2l','sXyrweNBlA0KaULSDfKC0Cue','6291063')
token = (cred["access_token"])
print("Access Token : ",token)



def index(request):
    resp = ""

    try:
        accessToken = token
        account_id = "6291063"
        de_name = "Test_HoldOut_Group"
        de_external_key = "5E4FE032-6C0E-42E8-8B81-99F167D7DFC9"
    except Exception as e:
        return "There is some problem with the Credentials Provided...",e
        
    try:
        descbody =f"""
            <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">    
            <s:Header>        
                <a:Action s:mustUnderstand="1">Retrieve</a:Action>        
                <a:To s:mustUnderstand="1">https://webservice.s6.exacttarget.com/Service.asmx</a:To>        
                <fueloauth xmlns="http://exacttarget.com">{accessToken}</fueloauth>    
            </s:Header>    
            <s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">          
                <RetrieveRequestMsg xmlns="http://exacttarget.com/wsdl/partnerAPI">
                    <RetrieveRequest>
                        <ObjectType>DataExtensionObject[{de_name}]</ObjectType>
                        <Properties>NAME</Properties>
                        <Properties>Flag</Properties>
                        <Properties>Status</Properties>
                        <Filter xsi:type="SimpleFilterPart">
                            <Property>Status</Property>
                                <SimpleOperator>equals</SimpleOperator>
                            <Value>Unprocessed</Value>
                        </Filter>
                    </RetrieveRequest>
                </RetrieveRequestMsg>  
            </s:Body>
            </s:Envelope>
        """
        url = "https://webservice.s6.exacttarget.com/Service.asmx"
        headers = {'content-type': 'text/xml'}
        body = descbody
        resp = requests.post(url, data=body, headers=headers)

        response = resp.text
        #    print(response)
        data = jxmlease.parse(response)
        status1=data["soap:Envelope"]["soap:Body"]["RetrieveResponseMsg"]["Results"]
        status2 = loads(dumps(status1))
    
    except Exception as e:
        return "There are no records for holding out...",e

    else:
        cust_list=[]
        # print(status2)
        for item in status2:
            cust_key= item["Properties"]["Property"][0]['Value']
            cust_list.append(cust_key)
    
        print("UnProcessed List",cust_list)
        n= len(cust_list)%10
        print(n)
        cust_1 = []
        for i in range(0,n):
            cust_1.append(cust_list.pop())
        
        print(cust_1)
        cust_2 = [ele for ele in cust_list if ele not in cust_1] 
        print(cust_2)

        if len(cust_2) > 9:
            # hold_list = cust_list[::10]
            hold_list = [cust_2[x*10-1] for x in range(1,len(cust_2)) if x*10<=len(cust_2)]
            print(hold_list)

            for element in hold_list:
        
                soapbody = f"""
                    <s:Envelope
                        xmlns:s="http://www.w3.org/2003/05/soap-envelope"
                        xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                        xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
                        <s:Header>
                            <a:Action s:mustUnderstand="1">Update</a:Action>
                            <a:MessageID>urn:uuid:7e0cca04-57bd-4481-864c-6ea8039d2ea0</a:MessageID>
                            <a:ReplyTo>
                            <a:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
                            </a:ReplyTo>
                            <a:To s:mustUnderstand="1">https://webservice.s6.exacttarget.com/Service.asmx</a:To>
                            <fueloauth xmlms="http://exacttarget.com">{accessToken}</fueloauth>
                        </s:Header>
                        <s:Body
                            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                            <UpdateRequest
                            xmlns="http://exacttarget.com/wsdl/partnerAPI">
                            <Objects xsi:type="DataExtensionObject">
                                <PartnerKey xsi:nil="true"/>
                                <Client>
                                <ID>{account_id}</ID>
                                </Client>
                                <ObjectID xsi:nil="true"/>
                                <CustomerKey>{de_external_key}</CustomerKey>
                                <Properties>
                                <Property>
                                    <Name>Name</Name>
                                    <Value>{element}</Value>
                                </Property>
                                <Property>
                                    <Name>Flag</Name>
                                    <Value>False</Value>
                                </Property>
                                <Property>
                                    <Name>Status</Name>
                                    <Value>Hold Out</Value>
                                </Property>
                            </Properties>
                            </Objects>
                        </UpdateRequest>
                        </s:Body>
                        </s:Envelope>
                    """
                url = "https://webservice.s6.exacttarget.com/Service.asmx"
                headers = {'content-type': 'text/xml'}
                body = soapbody
                resp = requests.post(url, data=body, headers=headers)
                print(resp.status_code)
                # print(resp.text)
 
            holdout_rec = hold_list
            # print("HoldOut Records: ", holdout_rec)

            res_list = tuple(set(holdout_rec)^set(cust_2))
            print("Without Holdout: ", res_list)

            for element in res_list:
                
                    soapbody = f"""
                        <s:Envelope
                            xmlns:s="http://www.w3.org/2003/05/soap-envelope"
                            xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                            xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
                            <s:Header>
                                <a:Action s:mustUnderstand="1">Update</a:Action>
                                <a:MessageID>urn:uuid:7e0cca04-57bd-4481-864c-6ea8039d2ea0</a:MessageID>
                                <a:ReplyTo>
                                <a:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
                                </a:ReplyTo>
                                <a:To s:mustUnderstand="1">https://webservice.s6.exacttarget.com/Service.asmx</a:To>
                                <fueloauth xmlms="http://exacttarget.com">{accessToken}</fueloauth>
                            </s:Header>
                            <s:Body
                                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                                <UpdateRequest
                                xmlns="http://exacttarget.com/wsdl/partnerAPI">
                                <Objects xsi:type="DataExtensionObject">
                                    <PartnerKey xsi:nil="true"/>
                                    <Client>
                                    <ID>{account_id}</ID>
                                    </Client>
                                    <ObjectID xsi:nil="true"/>
                                    <CustomerKey>{de_external_key}</CustomerKey>
                                    <Properties>
                                    <Property>
                                        <Name>Name</Name>
                                        <Value>{element}</Value>
                                    </Property>
                                    <Property>
                                        <Name>Flag</Name>
                                        <Value>True</Value>
                                    </Property>
                                    <Property>
                                        <Name>Status</Name>
                                        <Value>Processed</Value>
                                    </Property>
                                </Properties>
                                </Objects>
                            </UpdateRequest>
                            </s:Body>
                            </s:Envelope>
                        """
                    url = "https://webservice.s6.exacttarget.com/Service.asmx"
                    headers = {'content-type': 'text/xml'}
                    body = soapbody
                    resp = requests.post(url, data=body, headers=headers)
                    print(resp.status_code)
                    # print(resp.text)
        if len(cust_1) > 0: 
            for element in cust_1:
                
                    soapbody = f"""
                        <s:Envelope
                            xmlns:s="http://www.w3.org/2003/05/soap-envelope"
                            xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                            xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
                            <s:Header>
                                <a:Action s:mustUnderstand="1">Update</a:Action>
                                <a:MessageID>urn:uuid:7e0cca04-57bd-4481-864c-6ea8039d2ea0</a:MessageID>
                                <a:ReplyTo>
                                <a:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
                                </a:ReplyTo>
                                <a:To s:mustUnderstand="1">https://webservice.s6.exacttarget.com/Service.asmx</a:To>
                                <fueloauth xmlms="http://exacttarget.com">{accessToken}</fueloauth>
                            </s:Header>
                            <s:Body
                                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                                <UpdateRequest
                                xmlns="http://exacttarget.com/wsdl/partnerAPI">
                                <Objects xsi:type="DataExtensionObject">
                                    <PartnerKey xsi:nil="true"/>
                                    <Client>
                                    <ID>{account_id}</ID>
                                    </Client>
                                    <ObjectID xsi:nil="true"/>
                                    <CustomerKey>{de_external_key}</CustomerKey>
                                    <Properties>
                                    <Property>
                                        <Name>Name</Name>
                                        <Value>{element}</Value>
                                    </Property>
                                    <Property>
                                        <Name>Flag</Name>
                                        <Value>True</Value>
                                    </Property>
                                    <Property>
                                        <Name>Status</Name>
                                        <Value>Unprocessed</Value>
                                    </Property>
                                </Properties>
                                </Objects>
                            </UpdateRequest>
                            </s:Body>
                            </s:Envelope>
                        """
                    url = "https://webservice.s6.exacttarget.com/Service.asmx"
                    headers = {'content-type': 'text/xml'}
                    body = soapbody
                    resp = requests.post(url, data=body, headers=headers)
                    print(resp.status_code)
                    # print(resp.text)
        
        
        

    # return HttpResponse("<h1>Hello Shailesh</h1>")
    return render(request,'salesapp/index.html',context={"resp":resp.text})