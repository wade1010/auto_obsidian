"""
Git管理器模块
负责自动化Git操作：add, commit, push
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

logger = logging.getLogger(__name__)


class GitManager:
    """Git管理器"""

    def __init__(self, repo_path: str,
                 auto_commit: bool = True,
                 auto_push: bool = True,
                 commit_message_template: str = "docs: 自动生成AI学习笔记 - {date}"):
        """
        初始化Git管理器

        Args:
            repo_path: Git仓库路径
            auto_commit: 是否自动提交
            auto_push: 是否自动推送
            commit_message_template: 提交信息模板
        """
        self.repo_path = Path(repo_path).resolve()
        self.auto_commit = auto_commit
        self.auto_push = auto_push
        self.commit_message_template = commit_message_template

        if not GIT_AVAILABLE:
            logger.warning(
                "GitPython未安装，Git功能将不可用。"
                "请运行: pip install GitPython"
            )
            self.repo = None
            return

        try:
            # 向上查找Git仓库
            repo = None
            current_path = self.repo_path

            # 最多向上查找5层
            for _ in range(5):
                if (current_path / '.git').exists():
                    repo = git.Repo(str(current_path))
                    logger.info(f"找到Git仓库: {current_path}")
                    logger.info(f"配置目录: {self.repo_path}")
                    self.repo_path = current_path  # 更新为实际仓库路径
                    break

                parent = current_path.parent
                if parent == current_path:  # 到达根目录
                    break
                current_path = parent

            if repo:
                self.repo = repo
            else:
                logger.error(f"在 {self.repo_path} 及其父目录中未找到Git仓库")
                logger.info(f"请在目录下运行: git init")
                self.repo = None

        except Exception as e:
            logger.error(f"加载Git仓库失败: {self.repo_path}, 错误: {e}")
            logger.info("Git功能将被禁用，但文件仍会正常保存")
            self.repo = None

    def _format_commit_message(self, **kwargs) -> str:
        """
        格式化提交信息

        Args:
            **kwargs: 模板变量

        Returns:
            格式化后的提交信息
        """
        now = datetime.now()

        # 默认变量
        default_vars = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "count": kwargs.get("count", 1),
            "topic": kwargs.get("topic", "")
        }

        # 合并用户提供的变量
        default_vars.update(kwargs)

        try:
            return self.commit_message_template.format(**default_vars)
        except KeyError as e:
            logger.warning(f"提交信息模板变量错误: {e}")
            return f"docs: 自动生成AI学习笔记 - {default_vars['date']}"

    def add(self, filepaths: List[str]) -> bool:
        """
        添加文件到暂存区

        Args:
            filepaths: 文件路径列表

        Returns:
            是否成功
        """
        if not self.repo:
            logger.warning("Git仓库未初始化，跳过add操作")
            return False

        try:
            for filepath in filepaths:
                self.repo.index.add([filepath])
                logger.debug(f"已添加文件: {filepath}")

            logger.info(f"已添加 {len(filepaths)} 个文件到暂存区")
            return True

        except Exception as e:
            logger.error(f"Git add失败: {e}")
            return False

    def commit(self, message: Optional[str] = None,
               **template_vars) -> bool:
        """
        提交更改

        Args:
            message: 提交信息（如果不提供则使用模板）
            **template_vars: 提交信息模板变量

        Returns:
            是否成功
        """
        if not self.repo:
            logger.warning("Git仓库未初始化，跳过commit操作")
            return False

        try:
            # 检查是否有更改
            if not self.repo.index.diff("HEAD"):
                logger.info("没有需要提交的更改")
                return True

            # 生成提交信息
            if message is None:
                message = self._format_commit_message(**template_vars)

            # 执行提交
            commit = self.repo.index.commit(message)

            logger.info(f"提交成功: {commit.hexsha[:7]} - {message}")
            return True

        except Exception as e:
            logger.error(f"Git commit失败: {e}")
            return False

    def push(self, remote: str = "origin",
             branch: str = "main") -> bool:
        """
        推送到远程仓库

        Args:
            remote: 远程仓库名称
            branch: 分支名称

        Returns:
            是否成功
        """
        if not self.repo:
            logger.warning("Git仓库未初始化，跳过push操作")
            return False

        if not self.auto_push:
            logger.info("自动推送已禁用")
            return True

        try:
            # 获取远程仓库
            try:
                remote_repo = self.repo.remote(remote)
            except ValueError:
                logger.warning(
                    f"远程仓库 '{remote}' 不存在，"
                    f"跳过push操作"
                )
                return False

            # 推送
            push_info = remote_repo.push(branch)

            if push_info:
                # 检查推送是否成功
                for info in push_info:
                    if info.flags & info.ERROR:
                        logger.error(f"推送失败: {info.summary}")
                        return False
                    else:
                        # 获取当前HEAD的commit
                        try:
                            commit = self.repo.head.commit.hexsha[:7]
                            logger.info(f"推送成功: {remote}/{branch} ({commit})")
                        except:
                            logger.info(f"推送成功: {remote}/{branch}")
                        return True
            else:
                logger.warning("推送失败，没有返回信息")
                return False

        except Exception as e:
            logger.error(f"Git push失败: {e}")
            return False

    def commit_and_push(self, filepaths: List[str],
                        commit_message: Optional[str] = None,
                        **template_vars) -> Dict[str, Any]:
        """
        完整流程：add, commit, push

        Args:
            filepaths: 文件路径列表
            commit_message: 提交信息
            **template_vars: 提交信息模板变量

        Returns:
            操作结果字典
        """
        result = {
            "success": False,
            "added": False,
            "committed": False,
            "pushed": False,
            "error": None
        }

        try:
            # 强制使用系统git命令（更可靠）
            logger.info("使用系统git命令进行操作")
            return self._commit_and_push_subprocess(
                filepaths, commit_message, **template_vars
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Git操作失败: {e}")

        return result

    def _commit_and_push_subprocess(self, filepaths: List[str],
                                   commit_message: Optional[str] = None,
                                   **template_vars) -> Dict[str, Any]:
        """
        使用系统git命令进行add, commit, push操作

        Args:
            filepaths: 文件路径列表
            commit_message: 提交信息
            **template_vars: 提交信息模板变量

        Returns:
            操作结果字典
        """
        result = {
            "success": False,
            "added": False,
            "committed": False,
            "pushed": False,
            "error": None
        }

        try:
            # 生成提交信息
            if commit_message is None:
                commit_message = self._format_commit_message(**template_vars)

            # Step 1: git add
            if self.auto_commit:
                add_cmd = ["git", "add"] + filepaths
                add_result = subprocess.run(
                    add_cmd,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if add_result.returncode == 0:
                    result["added"] = True
                    logger.info(f"git add 成功: {filepaths}")
                else:
                    result["error"] = f"git add失败: {add_result.stderr}"
                    logger.error(result["error"])
                    return result

            # Step 2: git commit
            if self.auto_commit:
                commit_cmd = ["git", "commit", "-m", commit_message]
                commit_result = subprocess.run(
                    commit_cmd,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if commit_result.returncode == 0:
                    result["committed"] = True
                    logger.info(f"git commit 成功: {commit_message}")
                else:
                    # 可能是没有更改
                    if "nothing to commit" in commit_result.stderr:
                        result["committed"] = True
                        logger.info("没有新的更改需要提交")
                    else:
                        result["error"] = f"git commit失败: {commit_result.stderr}"
                        logger.error(result["error"])
                        return result

            # Step 3: git push
            if self.auto_push:
                push_cmd = ["git", "push", "-v"]  # 添加verbose选项
                push_result = subprocess.run(
                    push_cmd,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if push_result.returncode == 0:
                    result["pushed"] = True
                    logger.info("git push 成功")
                else:
                    # 合并stdout和stderr来获取完整错误信息
                    error_output = push_result.stderr + "\n" + push_result.stdout
                    result["error"] = f"git push失败: {error_output}"

                    # 检查常见错误
                    if "Authentication failed" in error_output or "Permission denied" in error_output:
                        result["error"] = "Git认证失败，请检查SSH密钥配置"
                        logger.error("Git认证失败")
                    elif "failed to push some refs" in error_output:
                        result["error"] = "远程仓库有新更新，请先执行 git pull"
                        logger.error("远程仓库冲突，需要先pull")
                    else:
                        logger.error(result["error"])

                    return result

            result["success"] = True
            logger.info("系统git命令执行完成: add → commit → push")

        except subprocess.TimeoutExpired:
            result["error"] = "Git操作超时"
            logger.error("Git操作超时")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"系统git命令执行失败: {e}")

        return result

    def get_status(self) -> Dict[str, Any]:
        """
        获取仓库状态

        Returns:
            状态信息字典
        """
        if not self.repo:
            return {
                "initialized": False,
                "branch": None,
                "untracked": 0,
                "modified": 0
            }

        try:
            branch = self.repo.active_branch.name
            untracked = len(self.repo.untracked_files)
            modified = len([item.a_path for item in self.repo.index.diff(None)])

            return {
                "initialized": True,
                "branch": branch,
                "untracked": untracked,
                "modified": modified,
                "repo_path": str(self.repo_path)
            }

        except Exception as e:
            logger.error(f"获取Git状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e)
            }

    def check_repo(self) -> bool:
        """
        检查是否为有效的Git仓库

        Returns:
            是否有效
        """
        if not GIT_AVAILABLE:
            return False

        try:
            git.Repo(self.repo_path)
            return True
        except Exception:
            return False
