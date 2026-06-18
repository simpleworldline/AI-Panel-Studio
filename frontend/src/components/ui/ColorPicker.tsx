import { EXPERT_COLORS } from '../../utils/color';

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
}

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-medium text-[var(--color-studio-fg-muted)]">颜色</span>
      <div className="flex flex-wrap gap-2">
        {EXPERT_COLORS.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => onChange(c)}
            className={`w-8 h-8 rounded-full border-2 transition-all duration-150 cursor-pointer
              ${value === c ? 'border-white scale-110 ring-2 ring-white/30' : 'border-transparent hover:scale-105'}`}
            style={{ backgroundColor: c }}
            aria-label={`选择颜色 ${c}`}
          />
        ))}
      </div>
    </div>
  );
}
