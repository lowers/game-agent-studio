"""游戏设计文档 Schema — 对话采集的目标输出。"""
from pydantic import BaseModel, Field


class GameDesignDoc(BaseModel):
    """标准化游戏设计文档，由对话采集生成。"""
    game_type: str = Field(default="", description="游戏类型，如 平台跳跃、RPG、射击")
    protagonist: str = Field(default="", description="主角描述")
    core_gameplay: str = Field(default="", description="核心玩法描述")
    enemies_collectibles: str = Field(default="", description="敌人和收集物")
    win_condition: str = Field(default="", description="目标和胜利条件")

    def is_complete(self) -> bool:
        return all([
            self.game_type,
            self.protagonist,
            self.core_gameplay,
            self.win_condition,
        ])

    def missing_fields(self) -> list[str]:
        fields = []
        if not self.game_type:
            fields.append("游戏类型")
        if not self.protagonist:
            fields.append("主角描述")
        if not self.core_gameplay:
            fields.append("核心玩法")
        if not self.enemies_collectibles:
            fields.append("敌人/收集物")
        if not self.win_condition:
            fields.append("胜利条件")
        return fields
