from src.database.models import User, PrivilegeStatus, PrivilegeType
import datetime

serverUser = User(id=1,steamId='server')
Users = [
    serverUser
]

ownerPrivilege = PrivilegeType(id=1,accessLevel=0,name='owner',description='One privilege to rule them all!')
PrivilegeTypes = [
    ownerPrivilege,
    PrivilegeType(id=2,accessLevel=1,name='admin',description='Server administrator, developer'),
    PrivilegeType(id=3,accessLevel=2,name='moderator',description='Server/Discord moderator')
]

Privileges = [
    PrivilegeStatus(id=1,userId=serverUser.id,privilegeId=ownerPrivilege.id,activeUntil=datetime.datetime.max)
]