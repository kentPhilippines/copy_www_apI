from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core import deps
from app.crud.crud_rule import rule
from app.schemas.crawler import RuleCreate, RuleUpdate, RuleInDB
from app.services.crawler_service import CrawlerService

router = APIRouter()

@router.get("/rules/", response_model=List[RuleInDB])
def list_rules(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_user)
):
    """获取采集规则列表"""
    rules = rule.get_multi(db, skip=skip, limit=limit)
    return rules

@router.post("/rules/", response_model=RuleInDB)
def create_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: RuleCreate,
    current_user = Depends(deps.get_current_user)
):
    """创建采集规则"""
    db_rule = rule.create(db, obj_in=rule_in)
    return db_rule

@router.put("/rules/{rule_id}", response_model=RuleInDB)
def update_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    rule_in: RuleUpdate,
    current_user = Depends(deps.get_current_user)
):
    """更新采集规则"""
    db_rule = rule.get(db, id=rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db_rule = rule.update(db, db_obj=db_rule, obj_in=rule_in)
    return db_rule 