import React from 'react';

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
}

const PRESETS = [
  '#6366F1', '#EF4444', '#3B82F6', '#F59E0B', '#10B981',
  '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#14B8A6',
  '#E11D48', '#2563EB', '#EAB308', '#22C55E', '#A855F7',
];

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-full border-2 border-[var(--color-studio-border)]"
          style={{ backgroundColor: value }}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 px-3 py-1.5 bg-[var(--color-studio-card)] border border-[var(--color-studio-border)] rounded-[var(--radius-sm)] text-sm text-[var(--color-studio-fg)] font-[var(--font-heading)] outline-none focus:border-[var(--color-studio-accent)]"
          placeholder="#RRGGBB"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((c) => (
          <button
            key={c}
            type="button"
            className={`w-7 h-7 rounded-full border-2 transition-transform hover:scale-110 ${c === value ? 'border-[var(--color-studio-fg)] scale-110' : 'border-transparent'}`}
            style={{ backgroundColor: c }}
            onClick={() => onChange(c)}
          />
        ))}
      </div>
    </div>
  );
}
