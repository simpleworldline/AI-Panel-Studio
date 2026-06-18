// ── 日期 / 文本格式化 ──

export function formatTime(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  const h = d.getHours().toString().padStart(2, '0');
  const m = d.getMinutes().toString().padStart(2, '0');
  return `${h}:${m}`;
}

export function formatDate(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  const y = d.getFullYear();
  const mo = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  return `${y}-${mo}-${day}`;
}

export function formatRelative(iso: string): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return '刚刚';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hour = Math.floor(min / 60);
  if (hour < 24) return `${hour} 小时前`;
  const day = Math.floor(hour / 24);
  if (day < 30) return `${day} 天前`;
  return formatDate(iso);
}

export function truncateText(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max) + '…';
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待开始',
    live: '进行中',
    paused: '已暂停',
    ended: '已结束',
  };
  return map[status] || status;
}

export function utteranceTypeLabel(type: string): string {
  const map: Record<string, string> = {
    opening: '开场',
    statement: '发言',
    question: '提问',
    reply: '回应',
    summary: '总结',
  };
  return map[type] || type;
}

export function expertStatusLabel(status: string): string {
  const map: Record<string, string> = {
    idle: '待机',
    preparing: '准备中',
    speaking: '发言中',
  };
  return map[status] || status;
}
