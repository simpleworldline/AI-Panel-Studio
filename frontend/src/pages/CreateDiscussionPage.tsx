import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createDiscussion } from '../api/discussions';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useToastStore } from '../store/useToastStore';

export function CreateDiscussionPage() {
  const navigate = useNavigate();
  const addToast = useToastStore((s) => s.addToast);
  const [topic, setTopic] = useState('');
  const [expertCount, setExpertCount] = useState(4);
  const [maxRounds, setMaxRounds] = useState<number | null>(null);
  const [customMax, setCustomMax] = useState<string>('');
  const [useCustom, setUseCustom] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const topicLength = topic.length;
  const topicMax = 200;
  const isTopicValid = topicLength > 0 && topicLength <= topicMax;
  const finalMaxRounds = useCustom ? (Number(customMax) || null) : maxRounds;

  const handleSubmit = async () => {
    if (!isTopicValid) return;
    setSubmitting(true);
    try {
      const res = await createDiscussion({ topic, expertCount, maxRounds: finalMaxRounds });
      addToast({ type: 'success', message: '讨论创建成功' });
      navigate(`/create/${res.data.id}/panel?count=${expertCount}`);
    } catch (e: any) {
      addToast({ type: 'error', message: e.message || '创建失败' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <h1 className="text-xl font-bold text-[var(--color-studio-fg)] text-center mb-2">
          发起新讨论
        </h1>
        <p className="text-sm text-[var(--color-studio-fg-muted)] text-center mb-6">
          输入讨论话题，AI 将自动生成嘉宾阵容
        </p>

        <div className="flex flex-col gap-4">
          {/* topic */}
          <div>
            <Input
              label="讨论话题"
              placeholder="例如：AI 是否应该具备自我意识？"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              maxLength={topicMax}
              error={topicLength > topicMax ? `最多 ${topicMax} 字` : undefined}
              helperText={`${topicLength}/${topicMax}`}
            />
          </div>

          {/* expert count */}
          <div>
            <label className="text-xs font-medium text-[var(--color-studio-fg-muted)] block mb-1.5">
              嘉宾人数
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={2}
                max={8}
                value={expertCount}
                onChange={(e) => setExpertCount(Number(e.target.value))}
                className="flex-1 accent-[var(--color-studio-info)]"
              />
              <span className="text-sm font-semibold text-[var(--color-studio-fg)] min-w-[2ch] text-center">
                {expertCount}
              </span>
            </div>
          </div>

          {/* max utterances */}
          <div>
            <label className="text-xs font-medium text-[var(--color-studio-fg-muted)] block mb-1.5">
              发言上限（可选）
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {[
                { val: null, label: '不限' },
                { val: 5, label: '5 条' },
                { val: 10, label: '10 条' },
                { val: 15, label: '15 条' },
                { val: 20, label: '20 条' },
                { val: 30, label: '30 条' },
              ].map(({ val, label }) => (
                <button
                  key={String(val)}
                  onClick={() => { setMaxRounds(val); setUseCustom(false); }}
                  className={`px-3 py-1.5 text-xs rounded-md border transition-all cursor-pointer
                    ${!useCustom && maxRounds === val
                      ? 'bg-[var(--color-studio-info)]/15 border-[var(--color-studio-info)] text-[var(--color-studio-info)]'
                      : 'bg-[var(--color-studio-bg)] border-[var(--color-studio-border)] text-[var(--color-studio-fg-muted)] hover:border-[var(--color-studio-fg-subtle)]'
                    }`}
                >
                  {label}
                </button>
              ))}
              <button
                onClick={() => setUseCustom(true)}
                className={`px-3 py-1.5 text-xs rounded-md border transition-all cursor-pointer
                  ${useCustom
                    ? 'bg-[var(--color-studio-info)]/15 border-[var(--color-studio-info)] text-[var(--color-studio-info)]'
                    : 'bg-[var(--color-studio-bg)] border-[var(--color-studio-border)] text-[var(--color-studio-fg-muted)] hover:border-[var(--color-studio-fg-subtle)]'
                  }`}
              >
                自定义
              </button>
            </div>
            {useCustom && (
              <input
                type="number"
                min={1}
                max={99}
                value={customMax}
                onChange={(e) => setCustomMax(e.target.value)}
                placeholder="输入发言条数上限"
                className="w-full px-3 py-2 text-sm rounded-lg bg-[var(--color-studio-bg)]
                  border border-[var(--color-studio-info)] text-[var(--color-studio-fg)]
                  focus:ring-2 focus:ring-[var(--color-studio-info)]/20 outline-none
                  placeholder:text-[var(--color-studio-fg-subtle)]"
              />
            )}
          </div>

          {/* submit */}
          <Button
            variant="primary"
            size="lg"
            className="w-full mt-2"
            disabled={!isTopicValid}
            loading={submitting}
            onClick={handleSubmit}
          >
            生成嘉宾阵容
          </Button>
        </div>
      </div>
    </div>
  );
}
