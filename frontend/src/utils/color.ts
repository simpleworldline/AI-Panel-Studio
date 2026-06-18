// ── 预设颜色板 ──

export const EXPERT_COLORS = [
  '#6366F1', '#EF4444', '#10B981', '#F59E0B',
  '#8B5CF6', '#EC4899', '#06B6D4', '#F97316',
];

export const EXPERT_COLOR_LABELS = [
  '靛蓝', '赤红', '翠绿', '琥珀',
  '紫罗', '玫粉', '青蓝', '橘橙',
];

/** hex 校验 */
export function isValidHex(color: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(color);
}

/** 获取颜色对应的 Tailwind text class (用于运行时动态颜色) */
export function getColorStyles(hex: string): { bg: string; text: string; ring: string; dot: string } {
  return {
    bg: hex,
    text: hex,
    ring: hex,
    dot: hex,
  };
}
