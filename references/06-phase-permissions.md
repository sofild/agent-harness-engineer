# Phase 6: 权限安全

## 目标

实现完整的权限控制和沙箱机制，确保Agent在安全边界内运行。

## 理论指导

### 应用的设计原则

1. **六层纵深防御**：权限模型、Hook系统、沙箱、审计
   - 为什么：单层防御容易被绕过
   - 怎么做：多层叠加，绕过概率指数下降

2. **deny > settings rules > hook allow**：安全不可变量
   - 为什么：确保最高优先级规则不被覆盖
   - 怎么做：硬编码拒绝规则

3. **最小权限原则**：只授予必要的权限
   - 为什么：减少攻击面
   - 怎么做：默认拒绝，显式允许

### 为什么需要权限控制？

场景：Agent需要执行命令
- 如果没有权限控制：Agent可能执行 `rm -rf /`
- 如果有权限控制：危险命令被拦截

## 实践步骤

### 步骤1：实现权限模型

文件：`src/permissions/models.py`

```python
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class PermissionMode(Enum):
    """权限模式"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"

@dataclass
class PermissionRule:
    """权限规则"""
    pattern: str
    action: str
    level: str = "read"

class PermissionManager:
    """权限管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.mode = PermissionMode(config.get("mode", "ask")) if config else PermissionMode.ASK
        self.rules: List[PermissionRule] = []
        
        if config and "rules" in config:
            for rule in config["rules"]:
                self.rules.append(PermissionRule(
                    pattern=rule["pattern"],
                    action=rule["action"],
                    level=rule.get("level", "read")
                ))
    
    def check_permission(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """检查权限"""
        import fnmatch
        
        for rule in self.rules:
            if fnmatch.fnmatch(tool_name, rule.pattern):
                if rule.action == "deny":
                    return False
                elif rule.action == "ask":
                    raise PermissionError(f"Permission required for: {tool_name}")
        
        return True
    
    def add_rule(self, pattern: str, action: str, level: str = "read"):
        """添加权限规则"""
        self.rules.append(PermissionRule(pattern, action, level))
```

### 步骤2：实现Hook系统

文件：`src/permissions/hooks.py`

```python
import os
from typing import Dict, Any, Callable, List
from pathlib import Path

class HookSystem:
    """Hook系统"""
    
    def __init__(self, hooks_dir: str = "config/hooks"):
        self.hooks_dir = Path(hooks_dir)
        self.pre_hooks: List[Callable] = []
        self.post_hooks: List[Callable] = []
        self._load_hooks()
    
    def _load_hooks(self):
        """加载Hook脚本"""
        if not self.hooks_dir.exists():
            return
        
        for hook_file in self.hooks_dir.glob("*.py"):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(hook_file.stem, hook_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "pre_tool_use"):
                    self.pre_hooks.append(module.pre_tool_use)
                if hasattr(module, "post_tool_use"):
                    self.post_hooks.append(module.post_tool_use)
            except Exception as e:
                print(f"Failed to load hook {hook_file}: {e}")
    
    def execute_pre_hooks(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行前置Hook"""
        for hook in self.pre_hooks:
            try:
                tool_input = hook(tool_name, tool_input)
            except Exception as e:
                print(f"Pre-hook failed: {e}")
        return tool_input
    
    def execute_post_hooks(self, tool_name: str, tool_input: Dict[str, Any], tool_output: str) -> str:
        """执行后置Hook"""
        for hook in self.post_hooks:
            try:
                tool_output = hook(tool_name, tool_input, tool_output)
            except Exception as e:
                print(f"Post-hook failed: {e}")
        return tool_output
```

### 步骤3：实现沙箱管理

文件：`src/permissions/sandbox.py`

```python
import os
from typing import List, Dict, Any
from pathlib import Path

class SandboxManager:
    """沙箱管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.enabled = config.get("enabled", True) if config else True
        self.allowed_directories = config.get("allowed_directories", ["workspace/"]) if config else ["workspace/"]
        self.denied_patterns = config.get("denied_patterns", []) if config else []
    
    def validate_path(self, path: str) -> bool:
        """验证路径是否在允许范围内"""
        if not self.enabled:
            return True
        
        path_obj = Path(path).resolve()
        allowed = False
        for allowed_dir in self.allowed_directories:
            allowed_path = Path(allowed_dir).resolve()
            if str(path_obj).startswith(str(allowed_path)):
                allowed = True
                break
        
        if not allowed:
            return False
        
        for pattern in self.denied_patterns:
            if pattern in str(path_obj):
                return False
        
        return True
    
    def validate_command(self, command: str) -> bool:
        """验证命令是否安全"""
        if not self.enabled:
            return True
        
        dangerous_patterns = ["rm -rf", "sudo", "dd if=", "> /dev", "mkfs"]
        for pattern in dangerous_patterns:
            if pattern in command:
                return False
        
        return True
```

## 检查清单

- [ ] 权限模型支持allow/deny/ask三种模式
- [ ] Hook系统支持pre/post-tool-use
- [ ] 沙箱限制文件系统访问范围
- [ ] 危险命令被正确拦截
- [ ] 权限规则可配置
- [ ] 审计日志记录

## 常见问题

### 问题：Hook allow绕过deny规则

**症状**：
- Hook允许执行危险操作
- 权限规则被绕过

**解决**：
- deny > settings rules > hook allow
- 这是安全不可变量

### 问题：沙箱配置被修改

**症状**：
- Agent修改settings.json关闭沙箱
- 沙箱设置被篡改

**解决**：
- 沙盒设置文件被硬编码为不可写
- 防止Agent通过修改settings.json来关闭沙盒

## 下一步

完成Phase 6后，进入 **Phase 7: 生产化**（参考 `references/07-phase-production.md`）
