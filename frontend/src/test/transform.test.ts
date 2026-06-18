import { describe, it, expect } from 'vitest';
import { keysToCamel, keysToSnake } from '../utils/transform';

describe('transform — snake_case ↔ camelCase', () => {
  it('keysToCamel: 扁平对象 snake_case → camelCase', () => {
    const input = { member_id: '1', member_name: '张三', focus_summary: 'test' };
    const result = keysToCamel(input);
    expect(result).toEqual({ memberId: '1', memberName: '张三', focusSummary: 'test' });
  });

  it('keysToCamel: 嵌套对象递归转换', () => {
    const input = {
      data: {
        expert_count: 4,
        creator_session_id: 'session-1',
        panel: [
          { panel_member_id: 'pm-1', member_name: '李四' },
          { panel_member_id: 'pm-2', member_name: '王五' },
        ],
      },
    };
    const result = keysToCamel(input);
    expect(result.data.expertCount).toBe(4);
    expect(result.data.creatorSessionId).toBe('session-1');
    expect(result.data.panel[0].panelMemberId).toBe('pm-1');
    expect(result.data.panel[1].memberName).toBe('王五');
  });

  it('keysToCamel: null/undefined 原样返回', () => {
    expect(keysToCamel(null)).toBeNull();
    expect(keysToCamel(undefined)).toBeUndefined();
  });

  it('keysToCamel: 数组递归转换', () => {
    const input = [{ user_id: 1 }, { user_id: 2 }];
    const result = keysToCamel(input);
    expect(result[0].userId).toBe(1);
    expect(result[1].userId).toBe(2);
  });

  it('keysToSnake: 扁平对象 camelCase → snake_case', () => {
    const input = { memberId: '1', memberName: '张三', focusSummary: 'test' };
    const result = keysToSnake(input);
    expect(result).toEqual({ member_id: '1', member_name: '张三', focus_summary: 'test' });
  });

  it('keysToSnake: 嵌套对象递归转换', () => {
    const input = {
      data: {
        expertCount: 4,
        creatorSessionId: 'session-1',
      },
    };
    const result = keysToSnake(input);
    expect(result.data.expert_count).toBe(4);
    expect(result.data.creator_session_id).toBe('session-1');
  });

  it('keysToSnake: 数组递归转换', () => {
    const input = [{ userId: 1 }, { userId: 2 }];
    const result = keysToSnake(input);
    expect(result[0].user_id).toBe(1);
  });
});
