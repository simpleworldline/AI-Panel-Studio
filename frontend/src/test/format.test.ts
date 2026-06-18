import { describe, it, expect } from 'vitest';
import {
  formatTime,
  formatDate,
  formatRelative,
  truncateText,
  statusLabel,
  utteranceTypeLabel,
  expertStatusLabel,
} from '../utils/format';

describe('format — 格式化工具', () => {
  describe('formatTime', () => {
    it('ISO → HH:mm', () => {
      expect(formatTime('2026-06-17T10:05:01Z')).toBe('18:05'); // UTC+8
    });

    it('空字符串返回空', () => {
      expect(formatTime('')).toBe('');
    });
  });

  describe('formatDate', () => {
    it('ISO → YYYY-MM-DD', () => {
      expect(formatDate('2026-06-17T10:00:00Z')).toBe('2026-06-17');
    });

    it('空字符串返回空', () => {
      expect(formatDate('')).toBe('');
    });
  });

  describe('formatRelative', () => {
    it('刚刚 — 60秒内', () => {
      const now = new Date();
      const iso = new Date(now.getTime() - 30000).toISOString();
      expect(formatRelative(iso)).toBe('刚刚');
    });

    it('N 分钟前', () => {
      const now = new Date();
      const iso = new Date(now.getTime() - 5 * 60 * 1000).toISOString();
      expect(formatRelative(iso)).toBe('5 分钟前');
    });

    it('N 小时前', () => {
      const now = new Date();
      const iso = new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString();
      expect(formatRelative(iso)).toBe('3 小时前');
    });

    it('空字符串返回空', () => {
      expect(formatRelative('')).toBe('');
    });
  });

  describe('truncateText', () => {
    it('不超出限制原样返回', () => {
      expect(truncateText('hello', 10)).toBe('hello');
    });

    it('超出限制截断加 …', () => {
      expect(truncateText('hello world test', 10)).toBe('hello worl…');
    });
  });

  describe('statusLabel', () => {
    it.each([
      ['pending', '待开始'],
      ['live', '进行中'],
      ['paused', '已暂停'],
      ['ended', '已结束'],
    ])('%s → %s', (input, expected) => {
      expect(statusLabel(input)).toBe(expected);
    });
  });

  describe('utteranceTypeLabel', () => {
    it.each([
      ['opening', '开场'],
      ['statement', '发言'],
      ['question', '提问'],
      ['reply', '回应'],
      ['summary', '总结'],
    ])('%s → %s', (input, expected) => {
      expect(utteranceTypeLabel(input)).toBe(expected);
    });
  });

  describe('expertStatusLabel', () => {
    it.each([
      ['idle', '待机'],
      ['preparing', '准备中'],
      ['speaking', '发言中'],
    ])('%s → %s', (input, expected) => {
      expect(expertStatusLabel(input)).toBe(expected);
    });
  });
});
