from src.database.models import User, PrivilegeStatus, PrivilegeType, AuthToken
import datetime
import os

FarTime = datetime.datetime(2100, 1, 1, 1, 1, 1)

Users = {
    'server':User(id=1,steamId='server'),
    'Y4r0z':User(id=2, steamId='76561198086700922')
}

PrivilegeTypes = {
    'owner': PrivilegeType(id=1,accessLevel=0,name='owner',description='One privilege to rule them all!'),
    'admin': PrivilegeType(id=2,accessLevel=1,name='admin',description='Server administrator, developer'),
    'moderator': PrivilegeType(id=3,accessLevel=2,name='moderator',description='Server/Discord moderator'),
    'soundpad': PrivilegeType(id=4, accessLevel=5, name='soundpad', description='Ability to use SoundPad'),
    'media_player': PrivilegeType(id=5, accessLevel=5, name='media_player', description='Ability to use media player'),
    'vip': PrivilegeType(id=6, accessLevel=4, name='vip', description='VIP features'),
    'premium': PrivilegeType(id=7, accessLevel=4, name='premium', description='Premium features'),
    'legend': PrivilegeType(id=8, accessLevel=4, name='legend', description='Legend features'),
    'customPrefix': PrivilegeType(id=9, accessLevel=5, name='custom_prefix', description='Custom chat prefix'),
    'welcomePhrase': PrivilegeType(id=10, accessLevel=5, name='welcome_phrase', description='Welcome phrase on join')
    
}

Privileges = {
    'server': PrivilegeStatus(id=1,userId=Users['server'].id,privilegeId=PrivilegeTypes['owner'].id,activeUntil=FarTime),
    'Y4r0z_admin': PrivilegeStatus(id=2, userId=Users['Y4r0z'].id, privilegeId=PrivilegeTypes['admin'].id, activeUntil=FarTime)
}

AuthTokens = {
    'server': AuthToken(id=1,userId=Users['server'].id,token=os.environ.get('SERVER_TOKEN'))
}