import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

from croniter import croniter

from core.bridge import send_message
from core.config import load_config
from core.queue import ProcessLock

logger = logging.getLogger(__name__)


class ScheduledTask:
    def __init__(self, name: str, cron: str, prompt: str, chat_id: int):
        self.name = name
        self.cron = cron
        self.prompt = prompt
        self.chat_id = chat_id
        self._iter = croniter(cron, datetime.now())
        self.next_run: float = self._iter.get_next(float)

    def advance(self):
        self.next_run = self._iter.get_next(float)

    def is_due(self) -> bool:
        return time.time() >= self.next_run


def load_tasks(config: dict) -> list[ScheduledTask]:
    scheduler_cfg = config.get("scheduler", {})
    tasks_cfg = scheduler_cfg.get("tasks", [])
    tasks = []
    for t in tasks_cfg:
        try:
            tasks.append(ScheduledTask(
                name=t["name"],
                cron=t["cron"],
                prompt=t["prompt"],
                chat_id=t["chat_id"],
            ))
            logger.info("Loaded task: %s (next: %s)", t["name"],
                       datetime.fromtimestamp(tasks[-1].next_run))
        except (KeyError, ValueError) as e:
            logger.error("Invalid task config: %s — %s", t, e)
    return tasks


async def run_task(
    task: ScheduledTask,
    bot_token: str,
    project_dir: str,
    lock: ProcessLock,
) -> None:
    logger.info("Running scheduled task: %s", task.name)
    try:
        async with lock:
            response = await send_message(
                task.prompt,
                project_dir=project_dir,
            )

        if response.is_error:
            logger.error("Task %s failed: %s", task.name, response.text)
            return

        # Send message via Telegram Bot API
        import httpx
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": task.chat_id,
                "text": response.text,
            })
        logger.info("Task %s completed", task.name)
    except Exception:
        logger.exception("Task %s failed", task.name)


async def run_scheduler(config: dict | None = None):
    if config is None:
        config = load_config()

    project_dir = str(Path(__file__).resolve().parent.parent)
    lock = ProcessLock(Path(project_dir) / ".claude_lock")
    bot_token = config["telegram"]["token"]
    tasks = load_tasks(config)

    if not tasks:
        logger.warning("No scheduled tasks configured")
        return

    logger.info("Scheduler started with %d tasks", len(tasks))

    while True:
        for task in tasks:
            if task.is_due():
                await run_task(task, bot_token, project_dir, lock)
                task.advance()

        await asyncio.sleep(30)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
