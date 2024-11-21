from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.database import Base

class Member(Base):
    """会员表模型"""
    __tablename__ = 'ot_member'
    
    # 基础信息
    uid = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    nickname = Column(String(16), nullable=False, default='', comment='昵称')
    sex = Column(Integer, nullable=False, default=0, comment='性别')
    birthday = Column(DateTime, nullable=False, comment='生日')
    qq = Column(String(10), nullable=False, default='', comment='qq号')
    
    # 积分与统计
    score = Column(Integer, nullable=False, default=0, comment='用户积分')
    login = Column(Integer, nullable=False, default=0, comment='登录次数')
    
    # 注册信息
    reg_ip = Column(String(15), nullable=False, default='', comment='注册IP')
    reg_time = Column(Integer, nullable=False, default=0, comment='注册时间')
    
    # 登录信息
    last_login_ip = Column(String(15), nullable=False, default='', comment='最后登录IP')
    last_login_time = Column(Integer, nullable=False, default=0, comment='最后登录时间')
    status = Column(Integer, nullable=False, default=0, comment='会员状态')

    def to_dict(self):
        """转换为字典格式"""
        return {
            'uid': self.uid,
            'nickname': self.nickname,
            'sex': self.sex,
            'birthday': self.birthday.strftime('%Y-%m-%d') if self.birthday else None,
            'qq': self.qq,
            'score': self.score,
            'login': self.login,
            'reg_time': self.reg_time,
            'last_login_time': self.last_login_time,
            'status': self.status
        } 