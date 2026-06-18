// ============================================================
// snake_case ↔ camelCase 双向转换
// 前端 camelCase → 后端 snake_case (请求)
// 后端 snake_case → 前端 camelCase (响应/WS事件)
// ============================================================

type AnyObject = Record<string, any>;

function toCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function toSnake(str: string): string {
  return str.replace(/[A-Z]/g, (c) => '_' + c.toLowerCase());
}

/** snake_case → camelCase (响应解包用) */
export function keysToCamel<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(keysToCamel) as unknown as T;
  if (typeof obj !== 'object' || obj instanceof Date) return obj as T;
  if (obj instanceof FormData || obj instanceof Blob) return obj as T;

  const result: AnyObject = {};
  for (const key of Object.keys(obj)) {
    const camelKey = toCamel(key);
    const value = obj[key];
    result[camelKey] = value !== null && typeof value === 'object' ? keysToCamel(value) : value;
  }
  return result as T;
}

/** camelCase → snake_case (请求打包用) */
export function keysToSnake<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(keysToSnake) as unknown as T;
  if (typeof obj !== 'object' || obj instanceof Date) return obj as T;
  if (obj instanceof FormData || obj instanceof Blob) return obj as T;

  const result: AnyObject = {};
  for (const key of Object.keys(obj)) {
    const snakeKey = toSnake(key);
    const value = obj[key];
    result[snakeKey] = value !== null && typeof value === 'object' ? keysToSnake(value) : value;
  }
  return result as T;
}
