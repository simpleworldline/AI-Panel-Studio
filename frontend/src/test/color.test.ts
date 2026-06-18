import { describe, it, expect } from 'vitest';
import { EXPERT_COLORS, isValidHex } from '../utils/color';

describe('color — 颜色工具', () => {
  describe('EXPERT_COLORS', () => {
    it('包含 8 种颜色', () => {
      expect(EXPERT_COLORS).toHaveLength(8);
    });

    it.each(EXPERT_COLORS)('%s 是合法 hex 颜色', (color) => {
      expect(isValidHex(color)).toBe(true);
    });
  });

  describe('isValidHex', () => {
    it('合法 hex 返回 true', () => {
      expect(isValidHex('#6366F1')).toBe(true);
      expect(isValidHex('#FFFFFF')).toBe(true);
      expect(isValidHex('#000000')).toBe(true);
      expect(isValidHex('#abcdef')).toBe(true);
    });

    it('非法格式返回 false', () => {
      expect(isValidHex('6366F1')).toBe(false);     // 缺少 #
      expect(isValidHex('#6366F')).toBe(false);     // 长度不足
      expect(isValidHex('#6366F111')).toBe(false);  // 长度超出
      expect(isValidHex('red')).toBe(false);
      expect(isValidHex('')).toBe(false);
    });
  });
});
