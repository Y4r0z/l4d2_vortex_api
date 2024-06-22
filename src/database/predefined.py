from src.database.models import User, PrivilegeStatus, PrivilegeType, AuthToken
import datetime
import os


Users = {
    'server':User(id=1,steamId='server')
}

PrivilegeTypes = {
    'owner': PrivilegeType(id=1,accessLevel=0,name='owner',description='One privilege to rule them all!'),
    'admin': PrivilegeType(id=2,accessLevel=1,name='admin',description='Server administrator, developer'),
    'moderator': PrivilegeType(id=3,accessLevel=2,name='moderator',description='Server/Discord moderator')
}

Privileges = {
    'server': PrivilegeStatus(id=1,userId=Users['server'].id,privilegeId=PrivilegeTypes['owner'].id,activeUntil=datetime.datetime(2100, 1, 1, 1, 1, 1))
}

AuthTokens = {
    'server': AuthToken(id=1,userId=Users['server'].id,token=os.environ.get('SERVER_TOKEN'))
}