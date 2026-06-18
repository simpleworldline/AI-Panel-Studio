import { describe, it, expect, vi, beforeAll } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

// jsdom polyfill
beforeAll(() => {
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = vi.fn();
  }
});

// UI components
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { ColorPicker } from '../components/ui/ColorPicker';

// Domain components
import { EmptyState } from '../components/EmptyState';
import { StreamingText } from '../components/StreamingText';
import { PanelDots } from '../components/PanelDots';
import { ErrorBoundary } from '../components/ErrorBoundary';

// ── Wrapper with Router ──
function Wrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

// ============================================================
// Button
// ============================================================
describe('Button', () => {
  it('渲染 children', () => {
    render(<Button>点击我</Button>);
    expect(screen.getByText('点击我')).toBeInTheDocument();
  });

  it('点击触发 onClick', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    await userEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('disabled 时不可点击', () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Disabled</Button>);
    fireEvent.click(screen.getByText('Disabled'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('loading 时显示 spinner', () => {
    render(<Button loading>Loading</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    expect(btn.querySelector('svg')).toBeTruthy(); // spinner SVG
  });

  it('变体样式', () => {
    render(
      <>
        <Button variant="primary">P</Button>
        <Button variant="secondary">S</Button>
        <Button variant="ghost">G</Button>
        <Button variant="danger">D</Button>
      </>,
    );
    expect(screen.getByText('P')).toBeInTheDocument();
    expect(screen.getByText('S')).toBeInTheDocument();
    expect(screen.getByText('G')).toBeInTheDocument();
    expect(screen.getByText('D')).toBeInTheDocument();
  });
});

// ============================================================
// Input
// ============================================================
describe('Input', () => {
  it('渲染 label 和 input', () => {
    render(<Input label="姓名" placeholder="输入姓名" />);
    expect(screen.getByLabelText('姓名')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入姓名')).toBeInTheDocument();
  });

  it('显示错误信息', () => {
    render(<Input label="标题" value="test" onChange={() => {}} error="必填" />);
    expect(screen.getByText('必填')).toBeInTheDocument();
  });

  it('显示 helperText', () => {
    render(<Input label="标题" helperText="最多200字" />);
    expect(screen.getByText('最多200字')).toBeInTheDocument();
  });

  it('error 存在时隐藏 helperText', () => {
    render(<Input label="标题" error="必填" helperText="提示" />);
    expect(screen.getByText('必填')).toBeInTheDocument();
    expect(screen.queryByText('提示')).toBeNull();
  });

  it('输入值变更', async () => {
    const onChange = vi.fn();
    render(<Input label="Test" value="" onChange={onChange} />);
    await userEvent.type(screen.getByLabelText('Test'), 'hello');
    expect(onChange).toHaveBeenCalledTimes(5);
  });
});

// ============================================================
// Badge
// ============================================================
describe('Badge', () => {
  it('渲染内容', () => {
    render(<Badge color="#6366F1">活跃</Badge>);
    expect(screen.getByText('活跃')).toBeInTheDocument();
  });

  it('solid 变体', () => {
    const { container } = render(<Badge color="#6366F1" variant="solid">S</Badge>);
    const span = container.firstChild as HTMLElement;
    expect(span.style.backgroundColor).toBe('rgb(99, 102, 241)');
  });

  it('outline 变体', () => {
    const { container } = render(<Badge color="#EF4444" variant="outline">O</Badge>);
    const span = container.firstChild as HTMLElement;
    expect(span.style.borderColor).toBe('rgb(239, 68, 68)');
  });

  it('dot 变体包含圆点', () => {
    render(<Badge color="#10B981" variant="dot">待机</Badge>);
    expect(screen.getByText('待机')).toBeInTheDocument();
  });
});

// ============================================================
// Spinner
// ============================================================
describe('Spinner', () => {
  it('渲染加载指示器', () => {
    const { container } = render(<Spinner />);
    expect(container.querySelector('svg')).toBeTruthy();
  });

  it('不同尺寸', () => {
    const { container: c1 } = render(<Spinner size="sm" />);
    expect(c1.querySelector('svg')?.classList.contains('w-4')).toBeTruthy();

    const { container: c2 } = render(<Spinner size="lg" />);
    expect(c2.querySelector('svg')?.classList.contains('w-12')).toBeTruthy();
  });
});

// ============================================================
// ColorPicker
// ============================================================
describe('ColorPicker', () => {
  it('渲染 8 个颜色按钮', () => {
    render(<ColorPicker value="#6366F1" onChange={() => {}} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(8);
  });

  it('选中颜色按钮高亮', async () => {
    const onChange = vi.fn();
    render(<ColorPicker value="#6366F1" onChange={onChange} />);
    const buttons = screen.getAllByRole('button');
    await userEvent.click(buttons[2]); // 第 3 个颜色
    expect(onChange).toHaveBeenCalled();
  });
});

// ============================================================
// EmptyState
// ============================================================
describe('EmptyState', () => {
  it('渲染标题和描述', () => {
    render(
      <EmptyState
        title="暂无数据"
        description="这里什么也没有"
      />,
    );
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
    expect(screen.getByText('这里什么也没有')).toBeInTheDocument();
  });

  it('渲染 action', () => {
    render(
      <EmptyState
        title="空"
        action={<Button>去创建</Button>}
      />,
    );
    expect(screen.getByText('去创建')).toBeInTheDocument();
  });

  it('渲染 icon', () => {
    const { container } = render(
      <EmptyState
        title="空"
        icon={<svg data-testid="test-icon" />}
      />,
    );
    expect(container.querySelector('[data-testid="test-icon"]')).toBeTruthy();
  });
});

// ============================================================
// StreamingText
// ============================================================
describe('StreamingText', () => {
  it('渲染文本', () => {
    render(<StreamingText text="你好世界" isStreaming={false} />);
    expect(screen.getByText('你好世界')).toBeInTheDocument();
  });

  it('isStreaming=true 显示光标', () => {
    const { container } = render(<StreamingText text="正在输入" isStreaming={true} />);
    // 光标元素有 animate-blink-cursor class
    const cursor = container.querySelector('.animate-blink-cursor');
    expect(cursor).toBeTruthy();
  });

  it('isStreaming=false 隐藏光标', () => {
    const { container } = render(<StreamingText text="完成" isStreaming={false} />);
    const cursor = container.querySelector('.animate-blink-cursor');
    expect(cursor).toBeNull();
  });
});

// ============================================================
// PanelDots
// ============================================================
describe('PanelDots', () => {
  it('渲染指定数量的圆点', () => {
    const { container } = render(<PanelDots count={4} />);
    const dots = container.querySelectorAll('.rounded-full');
    expect(dots).toHaveLength(4);
  });

  it('count=0 不渲染', () => {
    const { container } = render(<PanelDots count={0} />);
    const dots = container.querySelectorAll('.rounded-full');
    expect(dots).toHaveLength(0);
  });
});

// ============================================================
// ErrorBoundary
// ============================================================
describe('ErrorBoundary', () => {
  it('正常渲染 children', () => {
    render(
      <ErrorBoundary>
        <div>正常内容</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText('正常内容')).toBeInTheDocument();
  });

  it('捕获错误显示回退 UI', () => {
    const ThrowError = () => {
      throw new Error('测试错误');
    };
    // suppress console.error for this test
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>,
    );
    expect(screen.getByText('页面出现错误')).toBeInTheDocument();
    expect(screen.getByText('测试错误')).toBeInTheDocument();
    expect(screen.getByText('返回首页')).toBeInTheDocument();
    spy.mockRestore();
  });
});

// ============================================================
// ExpertStatusPanel (轻量 smoke)
// ============================================================
describe('ExpertStatusPanel', () => {
  it('空成员显示提示', async () => {
    const { ExpertStatusPanel } = await import('../components/ExpertStatusPanel');
    render(<ExpertStatusPanel members={[]} statuses={{}} />);
    expect(screen.getByText('暂无嘉宾')).toBeInTheDocument();
  });

  it('有成员时渲染嘉宾卡片', async () => {
    const { ExpertStatusPanel } = await import('../components/ExpertStatusPanel');
    const members = [
      { id: 'm-1', name: '张明', title: 'AI伦理学家', role: 'host' as const, stance: '中立', color: '#6366F1' },
      { id: 'm-2', name: '李四', title: '研究员', role: 'expert' as const, stance: '支持', color: '#EF4444' },
    ];
    render(<ExpertStatusPanel members={members} statuses={{}} />);
    expect(screen.getByText('张明')).toBeInTheDocument();
    expect(screen.getByText('李四')).toBeInTheDocument();
  });
});

// ============================================================
// ConsensusPanel (轻量 smoke)
// ============================================================
describe('ConsensusPanel', () => {
  it('空列表显示空状态', async () => {
    const { ConsensusPanel } = await import('../components/ConsensusPanel');
    render(<ConsensusPanel items={[]} />);
    expect(screen.getByText('暂无共识或分歧')).toBeInTheDocument();
  });

  it('有数据时渲染列表', async () => {
    const { ConsensusPanel } = await import('../components/ConsensusPanel');
    const items = [
      {
        id: 'c-1', type: 'consensus' as const, title: '共识一',
        description: '大家同意', sourceUtteranceIds: ['u-1'],
        confidence: 0.9, isResolved: false, roundNum: 2,
      },
    ];
    render(<ConsensusPanel items={items} />);
    expect(screen.getByText('共识一')).toBeInTheDocument();
    expect(screen.getByText('共识')).toBeInTheDocument();
  });
});

// ============================================================
// ControlBar
// ============================================================
describe('ControlBar', () => {
  it('创建者可见全部控制按钮', async () => {
    const { ControlBar } = await import('../components/ControlBar');
    const props = {
      status: 'live' as const,
      currentRound: 1,
      totalUtterances: 5,
      maxRounds: null,
      isCreator: true,
      onPause: vi.fn(),
      onResume: vi.fn(),
      onAdvance: vi.fn(),
      onEnd: vi.fn(),
    };
    render(<ControlBar {...props} />);
    expect(screen.getByText('暂停')).toBeInTheDocument();
    expect(screen.getByText('下一轮')).toBeInTheDocument();
    expect(screen.getByText('结束')).toBeInTheDocument();
  });

  it('非创建者显示观看模式', async () => {
    const { ControlBar } = await import('../components/ControlBar');
    const props = {
      status: 'live' as const,
      currentRound: 1,
      totalUtterances: 5,
      maxRounds: null,
      isCreator: false,
      onPause: vi.fn(),
      onResume: vi.fn(),
      onAdvance: vi.fn(),
      onEnd: vi.fn(),
    };
    render(<ControlBar {...props} />);
    expect(screen.getByText('观看模式')).toBeInTheDocument();
    expect(screen.queryByText('暂停')).toBeNull();
  });

  it('paused 状态显示继续按钮', async () => {
    const { ControlBar } = await import('../components/ControlBar');
    const props = {
      status: 'paused' as const,
      currentRound: 1,
      totalUtterances: 5,
      maxRounds: null,
      isCreator: true,
      onPause: vi.fn(),
      onResume: vi.fn(),
      onAdvance: vi.fn(),
      onEnd: vi.fn(),
    };
    render(<ControlBar {...props} />);
    expect(screen.getByText('继续')).toBeInTheDocument();
    expect(screen.queryByText('暂停')).toBeNull();
  });

  it('ended 状态不显示按钮', async () => {
    const { ControlBar } = await import('../components/ControlBar');
    const props = {
      status: 'ended' as const,
      currentRound: 5,
      totalUtterances: 20,
      maxRounds: null,
      isCreator: true,
      onPause: vi.fn(),
      onResume: vi.fn(),
      onAdvance: vi.fn(),
      onEnd: vi.fn(),
    };
    render(<ControlBar {...props} />);
    expect(screen.queryByText('暂停')).toBeNull();
    expect(screen.queryByText('结束')).toBeNull();
    expect(screen.queryByText('下一轮')).toBeNull();
  });
});

// ============================================================
// DiscussionCard
// ============================================================
describe('DiscussionCard', () => {
  it('渲染讨论信息', async () => {
    const { DiscussionCard } = await import('../components/DiscussionCard');
    const discussion = {
      id: 'd-1',
      topic: 'AI 是否具备自我意识？',
      expertCount: 4,
      status: 'live' as const,
      currentRound: 3,
      createdAt: '2026-06-17T10:00:00Z',
      memberPreview: [{ name: '张明', role: 'host' as const }, { name: '李四', role: 'expert' as const }],
    };
    render(<Wrapper><DiscussionCard discussion={discussion} /></Wrapper>);
    expect(screen.getByText('AI 是否具备自我意识？')).toBeInTheDocument();
    expect(screen.getByText('进行中')).toBeInTheDocument();
    expect(screen.getByText('4 位嘉宾')).toBeInTheDocument();
  });
});

// ============================================================
// MemberCard
// ============================================================
describe('MemberCard', () => {
  it('渲染嘉宾信息', async () => {
    const { MemberCard } = await import('../components/MemberCard');
    const member = {
      id: 'pm-1',
      name: '张明',
      title: 'AI伦理学家',
      role: 'host' as const,
      stance: '中立客观，擅长引导讨论',
      color: '#6366F1',
    };
    render(<MemberCard member={member} />);
    expect(screen.getByText('张明')).toBeInTheDocument();
    expect(screen.getByText('AI伦理学家')).toBeInTheDocument();
    expect(screen.getByText('主持人')).toBeInTheDocument();
  });

  it('showActions=false 不显示操作按钮', async () => {
    const { MemberCard } = await import('../components/MemberCard');
    const member = {
      id: 'pm-1', name: '张明', title: 'AI伦理学家',
      role: 'host' as const, stance: '中立', color: '#6366F1',
    };
    render(<MemberCard member={member} showActions={false} />);
    expect(screen.queryByText('编辑')).toBeNull();
    expect(screen.queryByText('重新生成')).toBeNull();
  });

  it('showActions=true 显示操作按钮', async () => {
    const { MemberCard } = await import('../components/MemberCard');
    const member = {
      id: 'pm-1', name: '张明', title: 'AI伦理学家',
      role: 'expert' as const, stance: '支持', color: '#EF4444',
    };
    render(
      <MemberCard
        member={member}
        showActions={true}
        onEdit={vi.fn()}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.getByText('编辑')).toBeInTheDocument();
    expect(screen.getByText('重新生成')).toBeInTheDocument();
  });
});

// ============================================================
// TranscriptView
// ============================================================
describe('TranscriptView', () => {
  it('空数据显示等待状态', async () => {
    const { TranscriptView } = await import('../components/TranscriptView');
    render(<TranscriptView utterances={[]} streaming={null} />);
    expect(screen.getByText('等待讨论开始')).toBeInTheDocument();
  });

  it('有发言时渲染列表', async () => {
    const { TranscriptView } = await import('../components/TranscriptView');
    const utterances = [{
      id: 'u-1',
      panelMemberId: 'pm-1',
      memberName: '张明',
      memberTitle: 'AI伦理学家',
      memberColor: '#6366F1',
      content: '今天我们讨论…',
      utteranceType: 'opening',
      sequenceNum: 1,
      roundNum: 0,
      createdAt: '2026-06-17T10:01:00Z',
    }];
    render(<TranscriptView utterances={utterances} streaming={null} />);
    expect(screen.getByText('今天我们讨论…')).toBeInTheDocument();
    expect(screen.getByText('张明')).toBeInTheDocument();
  });

  it('有 streaming 时渲染流式发言', async () => {
    const { TranscriptView } = await import('../components/TranscriptView');
    const streaming = {
      utteranceId: 'u-2',
      memberId: 'pm-2',
      memberName: '李四',
      memberTitle: '研究员',
      memberColor: '#EF4444',
      accumulatedText: '我认为…',
      isStreaming: true,
    };
    render(<TranscriptView utterances={[]} streaming={streaming} />);
    expect(screen.getByText('我认为…')).toBeInTheDocument();
    expect(screen.getByText('发言中')).toBeInTheDocument();
  });
});

// ============================================================
// UtteranceItem
// ============================================================
describe('UtteranceItem', () => {
  it('渲染发言内容', async () => {
    const { UtteranceItem } = await import('../components/UtteranceItem');
    const utterance = {
      id: 'u-1',
      panelMemberId: 'pm-1',
      memberName: '张明',
      memberTitle: 'AI伦理学家',
      memberColor: '#6366F1',
      content: '大家好',
      utteranceType: 'opening',
      sequenceNum: 1,
      roundNum: 0,
      createdAt: '2026-06-17T10:01:00Z',
    };
    render(<UtteranceItem utterance={utterance} />);
    expect(screen.getByText('大家好')).toBeInTheDocument();
    expect(screen.getByText('开场')).toBeInTheDocument();
  });
});

// ============================================================
// ConsensusItem
// ============================================================
describe('ConsensusItem', () => {
  it('渲染共识记录', async () => {
    const { ConsensusItem } = await import('../components/ConsensusItem');
    const item = {
      id: 'c-1', type: 'consensus' as const, title: '达成一致',
      description: '双方均认同 AI 应有边界',
      sourceUtteranceIds: ['u-1', 'u-2'], confidence: 0.95,
      isResolved: false, roundNum: 2,
    };
    render(<ConsensusItem item={item} />);
    expect(screen.getByText('达成一致')).toBeInTheDocument();
    expect(screen.getByText('共识')).toBeInTheDocument();
    expect(screen.getByText(/置信度 95%/)).toBeInTheDocument();
  });

  it('渲染分歧记录并显示已化解', async () => {
    const { ConsensusItem } = await import('../components/ConsensusItem');
    const item = {
      id: 'd-1', type: 'disagreement' as const, title: '无法调和',
      description: '双方观点相反',
      sourceUtteranceIds: ['u-3'], confidence: 0.8,
      isResolved: true, roundNum: 2,
    };
    render(<ConsensusItem item={item} />);
    expect(screen.getByText('分歧')).toBeInTheDocument();
    expect(screen.getByText('已化解')).toBeInTheDocument();
  });
});

// ============================================================
// Modal
// ============================================================
describe('Modal', () => {
  it('open=false 不渲染', async () => {
    const { Modal } = await import('../components/ui/Modal');
    render(
      <Modal open={false} onClose={vi.fn()} title="T">
        内容
      </Modal>,
    );
    expect(screen.queryByText('T')).toBeNull();
  });

  it('open=true 渲染标题和内容', async () => {
    const { Modal } = await import('../components/ui/Modal');
    render(
      <Modal open={true} onClose={vi.fn()} title="编辑">
        表单内容
      </Modal>,
    );
    expect(screen.getByText('编辑')).toBeInTheDocument();
    expect(screen.getByText('表单内容')).toBeInTheDocument();
  });

  it('渲染 footer', async () => {
    const { Modal } = await import('../components/ui/Modal');
    render(
      <Modal open={true} onClose={vi.fn()} title="T" footer={<button>保存</button>}>
        内容
      </Modal>,
    );
    expect(screen.getByText('保存')).toBeInTheDocument();
  });

  it('点击关闭按钮触发 onClose', async () => {
    const { Modal } = await import('../components/ui/Modal');
    const onClose = vi.fn();
    render(
      <Modal open={true} onClose={onClose} title="T">
        内容
      </Modal>,
    );
    // 关闭按钮是 header 区域的 button（X 图标）
    const buttons = screen.getAllByRole('button');
    // 第一个应该是关闭按钮（X）
    await userEvent.click(buttons[0]);
    expect(onClose).toHaveBeenCalled();
  });
});
