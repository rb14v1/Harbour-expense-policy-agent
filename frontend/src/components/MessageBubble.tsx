import { escapeHtml } from '../utils/formatting';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
}

export default function MessageBubble({ role, content }: MessageBubbleProps) {
  return (
    <div className={`message ${role}`}>
      <div className="message-bubble">{content}</div>
    </div>
  );
}
